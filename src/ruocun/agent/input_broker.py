"""交互终端的输入所有者，管理草稿、模态审批和终端刷新。它在同一个终端输入源上分配键盘事件，防止确认键落入下一次提交。

重定向的 stdin 仍由原有顺序输入路径读取。
"""

from __future__ import annotations

import asyncio
import math
import os
import sys
from collections import deque
from collections.abc import Awaitable, Callable, Coroutine, Mapping, Sequence
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING, Any, Literal

from prompt_toolkit import Application
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.application.current import set_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.data_structures import Point, Size
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import ANSI, FormattedText
from prompt_toolkit.input import Input, create_input
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import ConditionalContainer, HSplit, Layout, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.processors import ConditionalProcessor, PasswordProcessor
from prompt_toolkit.layout.screen import Char
from prompt_toolkit.output import ColorDepth, Output, create_output
from prompt_toolkit.output.plain_text import PlainTextOutput
from prompt_toolkit.renderer import Renderer, print_formatted_text
from prompt_toolkit.styles import DynamicStyle, Style
from prompt_toolkit.widgets import Frame

from ..approval.types import ApprovalDecision, ApprovalRequest
from ..i18n.i18n import getLang, setLang, t
from ..platform.windows.clipboard import ClipboardPayload
from ..session.inputs import Content
from ..skills.control import SkillControls
from ..tui.app.agent_tasks_panel import AgentTasksPanel
from ..tui.app.app import App, HistoryPanel, clean_text
from ..tui.app.modals import Modal, SecretValidationModal, TrustModal
from ..tui.app.types import TranscriptItem
from ..tui.background import bgFromEnv, fromRGB, resolveBackground
from ..tui.capabilities import Capabilities, detectCapabilities
from ..tui.image_paste import getClipboardImages, imageFromPath, pastedImagePath
from ..tui.input_text import PasteStore, next_grapheme, previous_grapheme
from ..tui.mascot import WelcomeMotion, createWelcomeMotion
from ..tui.notifier import cleanNotificationText
from ..tui.onboarding.select import SelectItem
from ..tui.tab_attention import (
    TabAttention,
    TabAttentionKind,
    createTabAttention,
    formatTabTitle,
)
from ..tui.terminal_reports import ParserGate, Reports, TerminalQueries
from ..tui.theme import semHex
from ..tui.welcome import Welcome
from ..tui.width import displayWidth

if TYPE_CHECKING:
    from .tasks import BgTask

_OUTPUT_STYLE = Style([])
_RenderFormat = bool | Literal["control", "notification"]
_RenderEntry = tuple[str, _RenderFormat, asyncio.Future[None] | None, Callable[[], bool] | None, TranscriptItem | None]


def _hard_wrap_row(cells: Mapping[int, Char], end: int, columns: int) -> Point:
    x = y = 0
    for index in range(end):
        cell = cells.get(index)
        width = min(cell.width, columns) if cell is not None else 1
        if x + width > columns:
            x, y = 0, y + 1
        x += width
    return Point(x, y)


class _SharedViewportRenderer(Renderer):
    reflow_enabled = True

    def _rebase_cursor(self) -> None:
        if not self.reflow_enabled or self._last_size is None or self.last_rendered_screen is None:
            return
        columns = self.output.get_size().columns
        if not 0 < columns < self._last_size.columns:
            return
        # prompt_toolkit 3.0.52 依据旧的相对光标计算差异。
        # Windows Terminal 已按新宽度硬换行，旧帧的擦除范围须随之重算。
        rows = self.last_rendered_screen.data_buffer
        cursor = self._cursor_pos
        physical_rows = 0
        for y in range(cursor.y):
            cells: Mapping[int, Char] = rows.get(y, {})
            end = max((x + cell.width for x, cell in cells.items() if cell.char not in {"", " "}), default=0)
            physical_rows += 1 + _hard_wrap_row(cells, end, columns).y
        current: Mapping[int, Char] = rows.get(cursor.y, {})
        position = _hard_wrap_row(current, cursor.x, columns)
        cell = current.get(cursor.x)
        width = max(1, min(cell.width, columns)) if cell is not None else 1
        if position.x + width > columns:
            position = Point(0, position.y + 1)
        origin_distance = physical_rows + position.y
        console_info = getattr(self.output, "get_win32_screen_buffer_info", None)
        if callable(console_info):
            try:
                info = console_info()
            except Exception:
                return  # 拿不到宿主的终端尺寸时，无法安全定位擦除起点。
            if info.dwCursorPosition.X != position.x or origin_distance > info.dwCursorPosition.Y - info.srWindow.Top:
                return
        self._cursor_pos = Point(position.x, origin_distance)

    def render(self, app: Application[Any], layout: Layout, is_done: bool = False) -> None:
        self._rebase_cursor()
        super().render(app, layout, is_done)

    def erase(self, leave_alternate_screen: bool = True) -> None:
        self._rebase_cursor()
        super().erase(leave_alternate_screen)


class InputBroker:
    def __init__(
        self, *, on_pause: Callable[[], Awaitable[None]],
        input: Input | None = None, output: Output | None = None,
    ) -> None:
        self._on_pause = on_pause
        self._owns_input = input is None
        self._input = input if input is not None else create_input()
        self._output = output if output is not None else create_output()
        self._submissions: asyncio.Queue[Content | None] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None
        self._pause_task: asyncio.Task[None] | None = None
        self._ready: asyncio.Future[None] | None = None
        self._closed = self._closing = False
        self._error: Exception | None = None
        self._output_lock = asyncio.Lock()
        self._approval_lock = asyncio.Lock()
        self._approval: asyncio.Future[str | None] | None = None
        self._approval_prompt = ""
        self._modal: Modal | None = None
        self._approval_generation = 0
        self._secret_answer = False
        self.on_escape: Callable[[], Awaitable[bool]] | None = None
        self.on_cycle_mode: Callable[[], Awaitable[str]] | None = None
        self._mode_task: asyncio.Task[None] | None = None
        self.on_background: Callable[[], Awaitable[int]] | None = None
        self._handoff_task: asyncio.Task[None] | None = None
        self._list_agent_tasks: Callable[[], Sequence[BgTask]] | None = None
        self._panel: AgentTasksPanel | HistoryPanel | None = None
        self._state, self._queued = "idle", 0
        self._exit_armed_at: float | None = None
        self._exit_timer: asyncio.TimerHandle | None = None
        self._last_submission = ""
        self._restored_last = False
        self._input_notice = ""
        self._pastes = PasteStore()
        self._render_queue: deque[_RenderEntry] = deque()
        self._render_task: asyncio.Task[None] | None = None
        self._render_error: Exception | None = None
        self._owned_viewport = False
        self._viewport_entries: list[str | TranscriptItem] = []
        self._resize_timer: asyncio.TimerHandle | None = None
        self._resize_task: asyncio.Task[None] | None = None
        self._resize_tasks: set[asyncio.Task[None]] = set()
        self._resize_epoch = 0
        self._columns = self._output.get_size().columns
        self._rows = self._output.get_size().rows
        self._view = App(self._commit_render, caps=detectCapabilities(os.environ, True, self._columns),
                         commit_item=self._commit_item)
        self._status_info: dict[str, object] = {}
        self._background_env = dict(os.environ)
        self._background_future: asyncio.Future[str | None] | None = None
        self._background_task: asyncio.Task[None] | None = None
        self._reports: Reports | None = None
        self._queries: TerminalQueries | None = None
        self._motion: WelcomeMotion | None = None
        self._motion_state: dict[str, object] | None = None
        self._welcome_info: dict[str, str] | None = None
        self._welcome_skip_footer = False
        self._welcome_epoch = 0
        self._welcome_untracked = False
        self._welcome_still_presented = False
        self._last_dynamic_rows = 0
        self._static_rows_key: tuple[object, ...] | None = None
        self._static_rows = 0
        self._tab: TabAttention | None = None
        self._tab_name: str | None = None
        self._clipboard_port: Callable[[], ClipboardPayload] | None = None
        self._image_tasks: set[asyncio.Task[None]] = set()
        self._image_lock = asyncio.Lock()
        self._clipboard_active = False
        self.buffer = Buffer(multiline=True)
        self._control = BufferControl(self.buffer)
        self._panel_control = FormattedTextControl(self._panel_text, focusable=True)
        self._answer = Buffer()
        self._answer_control = BufferControl(self._answer, input_processors=[
            ConditionalProcessor(PasswordProcessor(char="•"), Condition(lambda: isinstance(self._modal, SecretValidationModal))),
            ConditionalProcessor(PasswordProcessor(), Condition(lambda: self._secret_answer and not isinstance(self._modal, SecretValidationModal)))])
        self.app: Application[None] = Application(
            layout=Layout(HSplit([
                ConditionalContainer(Window(FormattedTextControl(self._live_text),
                                            height=Dimension(min=0, max=12), wrap_lines=True, dont_extend_height=True),
                                     filter=Condition(lambda: not self._panel_active() and
                                         bool(self._view.live.content or self._view.live.reasoning or self._view.live.tools))),
                ConditionalContainer(
                    Frame(Window(self._control, height=Dimension(min=1, max=6), wrap_lines=True,
                                 style="class:input", get_line_prefix=lambda line, wrap: "› ", dont_extend_height=True),
                          style="class:input-frame"),
                    filter=Condition(lambda: self._approval is None and self._panel is None)),
                ConditionalContainer(Frame(Window(self._panel_control, style="class:input", dont_extend_height=True),
                                           style="class:input-frame"), filter=Condition(self._panel_active)),
                ConditionalContainer(HSplit([
                    Frame(Window(FormattedTextControl(self._dialog_text), wrap_lines=True, dont_extend_height=True), style="class:input-frame"),
                    Window(self._answer_control, height=1, style="class:input",
                           get_line_prefix=lambda line, wrap: "› "),
                ]), filter=Condition(lambda: self._approval is not None)),
                Window(FormattedTextControl(self._status_text), height=1),
                ConditionalContainer(Window(FormattedTextControl(self._status_bar), height=1),
                                     filter=Condition(lambda: bool(self._status_info))),
            ]), focused_element=self._control),
            key_bindings=self._bindings(), input=self._input, output=self._output,
            full_screen=False, mouse_support=False, erase_when_done=True,
            style=DynamicStyle(self._style), before_render=self._before_render,
            after_render=self._after_render,
            refresh_interval=.1,
        )
        self.app.ttimeoutlen = self.app.timeoutlen = 0.08
        self.app.key_processor.before_key_press += lambda _: self._user_activity()

    def _bindings(self) -> KeyBindings:
        keys = KeyBindings()
        draft = Condition(lambda: self._approval is None and self._panel is None and not self._closing)

        @keys.add("s-tab", filter=draft & Condition(lambda: self.on_cycle_mode is not None))
        def cycle_mode(event: KeyPressEvent) -> None:
            previous = self._mode_task
            async def cycle() -> None:
                try:
                    if previous is not None:
                        await previous
                    if self._closing or self.on_cycle_mode is None:
                        return
                    mode = await self.on_cycle_mode()
                    if mode in {"auto", "bypassPermissions"}:
                        self.emit_event("permission_mode", text=t("ui.modeHint", t("mode." + mode)))
                    else:
                        self.emit_event("notice", text=mode)
                except Exception as error:
                    self._error = error
                    self._request_exit()
            self._mode_task = asyncio.create_task(cycle())

        @keys.add("c-o", filter=draft)
        def expand(event: KeyPressEvent) -> None:
            self._view.toggle_expanded()
            self.app.invalidate()

        @keys.add("c-t", filter=Condition(lambda: self._approval is None and self._list_agent_tasks is not None and not self._closing))
        def task_panel(event: KeyPressEvent) -> None:
            if self._list_agent_tasks is not None:
                self._set_panel(None if isinstance(self._panel, AgentTasksPanel) else AgentTasksPanel(self._list_agent_tasks))

        @keys.add("c-g", filter=Condition(lambda: self._approval is None and not self._closing))
        def history_panel(event: KeyPressEvent) -> None:
            if isinstance(self._panel, HistoryPanel):
                self._set_panel(None)
            elif self._panel is None:
                panel = HistoryPanel(self._view)
                if panel.users:
                    self._set_panel(panel)

        @keys.add("up", filter=Condition(self._panel_active))
        @keys.add("down", filter=Condition(self._panel_active))
        @keys.add("pageup", filter=Condition(self._panel_active))
        @keys.add("pagedown", filter=Condition(self._panel_active))
        def panel_move(event: KeyPressEvent) -> None:
            key = event.key_sequence[-1].key
            self._handle_panel(key.value if isinstance(key, Keys) else key)

        @keys.add("c-b", filter=draft & Condition(lambda: self._state == "running" and self.on_background is not None))
        def transfer(event: KeyPressEvent) -> None:
            if self._handoff_task is None or self._handoff_task.done():
                self._handoff_task = asyncio.create_task(self._transfer_background())

        @keys.add("escape", "v", filter=draft)
        def attach_clipboard(event: KeyPressEvent) -> None:
            if not self._clipboard_active:
                self._clipboard_active = True
                self._start_image_task(self._attach_clipboard())

        @keys.add("enter", eager=True)
        def submit(event: KeyPressEvent) -> None:
            if self._handle_modal("enter"):
                return
            if self._approval is not None:
                self._finish_approval(self._answer.text)
                return
            if self._handle_panel("enter"):
                return
            text = self.buffer.text.strip()
            if text:
                self._restored_last = False
                self._last_submission = text
                expanded = self._pastes.expand(text)
                self.buffer.reset()
                self._submissions.put_nowait(expanded)
                self._pastes.retain(text)

        @keys.add("down", filter=draft & Condition(lambda: self._restored_last and self.buffer.text == self._last_submission))
        def clear_restored(event: KeyPressEvent) -> None:
            self.buffer.reset()
            self._restored_last = False

        @keys.add("up", filter=Condition(lambda: self._modal is not None))
        @keys.add("down", filter=Condition(lambda: self._modal is not None))
        def move_modal(event: KeyPressEvent) -> None:
            self._handle_modal("up" if event.key_sequence[-1].key == Keys.Up else "down")

        @keys.add(Keys.Any, filter=Condition(lambda: self._modal is not None))
        def modal_text(event: KeyPressEvent) -> None:
            if not self._handle_modal("text", event.data):
                if isinstance(self._modal, SecretValidationModal) and not event.data.isprintable():
                    return
                self._answer.insert_text(event.data)
                self.app.invalidate()

        @keys.add(Keys.BracketedPaste)
        def paste(event: KeyPressEvent) -> None:
            if self._closing or self._panel_active():
                return
            if self._modal is not None and not self._modal.typing:
                return
            text = event.data.replace("\r\n", "\n").replace("\r", "\n")
            if self._approval is None:
                path = pastedImagePath(text)
                if path is not None:
                    self._start_image_task(self._paste_image_path(text, path))
                elif not text and sys.platform == "darwin" and not self._clipboard_active:
                    self._clipboard_active = True
                    self._start_image_task(self._attach_clipboard())
                else:
                    event.current_buffer.insert_text(self._pastes.insert(text))
            else:
                if isinstance(self._modal, SecretValidationModal):
                    text = "".join(text.split())
                event.current_buffer.insert_text(text)

        @keys.add("left")
        @keys.add("right")
        @keys.add("backspace")
        @keys.add("delete")
        def edit_grapheme(event: KeyPressEvent) -> None:
            if self._handle_modal(str(event.key_sequence[-1].key)) or self._panel_active():
                return
            buffer = event.current_buffer
            cursor, text = buffer.cursor_position, buffer.text
            key = event.key_sequence[-1].key
            before, after = previous_grapheme(text, cursor), next_grapheme(text, cursor)
            if key == Keys.Left:
                buffer.cursor_position = before
            elif key == Keys.Right:
                buffer.cursor_position = after
            elif key == Keys.ControlH:
                buffer.delete_before_cursor(cursor - before)
            elif key == Keys.Delete:
                buffer.delete(after - cursor)

        @keys.add("escape", "enter", filter=draft)
        def newline(event: KeyPressEvent) -> None:
            if self._approval is None:
                event.current_buffer.insert_text("\n")

        @keys.add("escape")
        def interrupt(event: KeyPressEvent) -> None:
            if self._handle_modal("escape"):
                return
            if self._approval is not None:
                self._finish_approval(None)
            elif self._handle_panel("escape"):
                return
            elif self._pause_task is None or self._pause_task.done():
                self._pause_task = asyncio.create_task(self._pause())

        @keys.add("c-c")
        def control_c(event: KeyPressEvent) -> None:
            if self._modal is not None:
                self._handle_modal("ctrl-c" if isinstance(self._modal, (SecretValidationModal, TrustModal)) else "escape")
                return
            if self._approval is not None:
                self._finish_approval(None)
                return
            now = monotonic()
            if self._exit_armed_at is not None and 0 <= now - self._exit_armed_at <= 2:
                self._request_exit()
            else:
                self._exit_armed_at = now
                if self._exit_timer is not None:
                    self._exit_timer.cancel()
                self._exit_timer = asyncio.get_running_loop().call_later(2, self._disarm_exit)
                self.app.invalidate()

        @keys.add("c-d")
        def eof(event: KeyPressEvent) -> None:
            if isinstance(self._modal, (SecretValidationModal, TrustModal)):
                self._handle_modal("ctrl-d")
            elif self._approval is not None:
                self._finish_approval(None)
            elif not self._panel_active() and not self.buffer.text:
                self._request_exit()

        return keys

    def configure_panels(self, *, tasks: Callable[[], Sequence[BgTask]]) -> None:
        self._list_agent_tasks = tasks

    def _panel_active(self) -> bool:
        return self._panel is not None and self._approval is None

    def _set_panel(self, panel: AgentTasksPanel | HistoryPanel | None) -> None:
        self._panel = panel
        self.app.layout.focus(self._panel_control if panel is not None else self._control)
        self.app.invalidate()

    def _panel_text(self) -> str:
        size = self._output.get_size()
        return self._panel.render(size.columns, size.rows) if self._panel is not None else ""

    def _handle_panel(self, key: str) -> bool:
        if self._panel is None or self._approval is not None:
            return False
        if key == "escape":
            self._set_panel(None)
        else:
            self._panel.handle(key, self._output.get_size().rows)
            self.app.invalidate()
        return True

    async def _transfer_background(self) -> None:
        callback = self.on_background
        if callback is None or self._closing or self._state != "running" or self._approval is not None or self._panel is not None:
            return
        try:
            count = await callback()
        except Exception:
            self._input_notice = ("转后台结果未确认，请核对任务状态。" if getLang() == "zh" else
                                  "Background handoff was not confirmed. Check task status.")
            self.app.invalidate()
            return
        if count > 0 and not self._closing:
            self.emit_event("notice", text=t("ui.notice.convertedToBackground", count))

    async def _pause(self) -> None:
        try:
            if self.on_escape is not None:
                paused = await self.on_escape()
                if paused and not self.buffer.text.strip() and self._last_submission:
                    self.buffer.set_document(Document(self._last_submission, len(self._last_submission)))
                    self._restored_last = True
                    self.app.invalidate()
            else:
                await self._on_pause()
        except Exception as exc:
            self._error = exc
            self._request_exit()

    def _disarm_exit(self) -> None:
        self._exit_armed_at = None
        self._exit_timer = None
        self.app.invalidate()

    def set_status(self, state: str, queued: int) -> None:
        self._state, self._queued = state, queued
        self._update_motion()
        self.app.invalidate()

    def set_language(self, lang: str) -> None:
        setLang(lang)
        self.app.invalidate()

    @property
    def background(self) -> str:
        return self._view.background

    def set_theme(self, background: str) -> None:
        if background not in {"dark", "light"}:
            raise ValueError("theme must be dark or light")
        changed = self.background != background
        self._view.background = background
        if changed and self._welcome_info is not None and self._motion is not None:
            self._motion.resized()
            if self._owned_viewport and not self._closing:
                self._resize_epoch += 1
                self._start_rebuild(self._resize_epoch)
        self.app.invalidate()

    def configure_terminal(self, environ: Mapping[str, str], *, owned_viewport: bool = False) -> None:
        self._view.caps = detectCapabilities(environ, True, self._output.get_size().columns)
        self._background_env = dict(environ)
        self._view.background = bgFromEnv(environ) or "dark"
        self._owned_viewport = owned_viewport
        reflow = bool(environ.get("WT_SESSION")) and not owned_viewport and not isinstance(self._output, PlainTextOutput)
        if isinstance(self.app.renderer, _SharedViewportRenderer):
            self.app.renderer.reflow_enabled = reflow
        elif reflow and not self.app.is_running:
            self.app.renderer = _SharedViewportRenderer(self.app.renderer.style, self._output,
                                                       cpr_not_supported_callback=self.app.cpr_not_supported_callback)
        self.app.invalidate()

    def set_tab_name(self, name: str | None) -> None:
        self._tab_name = name
        if self._tab is not None:
            self._tab.setTitle(formatTabTitle("", name))

    def mark_attention(self, kind: TabAttentionKind = "attention") -> None:
        if self._tab is not None and not self._closed and not self._closing:
            self._tab.mark(kind)

    def clear_attention(self) -> None:
        if self._tab is not None:
            self._tab.clear()

    def post_notification(self, text: str) -> None:
        """向当前终端投递次要提示。提示没有用户已读确认，也不触发桌面通知。"""
        if not self._closed and not self._closing:
            self.mark_attention()
            if self._motion is not None:
                self._welcome_untracked = True
                self._motion.resized()  # 静态行数无法准确测量时，放弃按推测位置擦除。
            self._enqueue_output(cleanNotificationText(text) + "\n", "notification")

    def _attention_write(self, sequence: str) -> None:
        self._enqueue_output(sequence, "control")

    def set_status_info(self, info: Mapping[str, object]) -> None:
        self._status_info = dict(info)
        self._update_motion()
        self.app.invalidate()

    def _user_activity(self) -> None:
        self.clear_attention()
        if self._motion is not None:
            self._motion.pause()
            self._motion_state = None

    def _dynamic_rows(self) -> int:
        screen = self.app.renderer.last_rendered_screen
        if screen is None:
            return self._last_dynamic_rows
        # Screen.height 包含 HSplit 补齐剩余空间的虚拟窗口，测量时只取实际窗口。
        windows = set(self.app.layout.find_all_windows())
        self._last_dynamic_rows = max((position.ypos + position.height for window, position in screen.visible_windows_to_write_positions.items()
                                       if window in windows), default=0)
        return self._last_dynamic_rows

    def _update_motion(self) -> None:
        if self._motion is None:
            return
        size = self._output.get_size()
        owned_replay = self._owned_viewport and self._welcome_epoch > 0
        key = (id(self._view.items), len(self._view.items), self._view.expanded, size.columns, getLang(),
               self._welcome_epoch, len(self._viewport_entries))
        if key != self._static_rows_key:
            if owned_replay:
                # 历史回放须按原顺序插入普通通知和渲染后的消息。
                replay = "".join(self._view.render_item(entry) + "\n" if isinstance(entry, TranscriptItem) else entry
                                 for entry in self._viewport_entries)
            else:
                replay = self._view.replay()
            raw = clean_text(replay)
            lines = raw.removesuffix("\n").split("\n") if raw else []
            self._static_rows = sum(max(1, math.ceil(displayWidth(line) / max(1, size.columns))) for line in lines)
            self._static_rows_key = key
        extra = self._static_rows
        state: dict[str, object] = {"epoch": self._welcome_epoch, "home": not self._view.items,
                                   "inputEmpty": not self.buffer.text, "busy": self._state == "running",
                                   "modalOpen": self._approval is not None or self._panel is not None or self._exit_armed_at is not None,
                                   "backgroundRunning": self._state == "waiting" or self._queued > 0 or bool(self._status_info.get("backgroundRunning")),
                                   "enabled": self.background == "dark" and not self._closing and not self._welcome_untracked,
                                   "dynamicRows": self._dynamic_rows(), "extraStaticRows": extra,
                                   "viewportStartsAtTop": owned_replay, "stillPresented": self._welcome_still_presented}
        if state != self._motion_state:
            self._motion_state = state
            self._motion.update(state)

    async def _wait_render_flush(self) -> None:
        if self._render_task is not None:
            await self._render_task
        await asyncio.sleep(0)

    def _welcome_text(self, size: Size | None = None) -> str:
        if self._welcome_info is None:
            return ""
        if size is None:
            size = self._output.get_size()
        tier = self._view.caps.tier
        explicit_color = self._background_env.get("FORCE_COLOR") or self._background_env.get("COLORTERM")
        if (tier == "ansi16" and not explicit_color and self._background_env.get("WT_SESSION")
                and self._output.get_default_color_depth() == ColorDepth.TRUE_COLOR):
            tier = "truecolor"
        graphics = not isinstance(self._output, PlainTextOutput) and self._background_env.get("TERM") != "dumb"
        caps = Capabilities(tier, self._view.caps.isTTY, size.columns)
        return Welcome(self._welcome_info, caps, self.background, skipFooter=self._welcome_skip_footer,
                       mascot=self._motion.layout if self._motion is not None else None,
                       terminalRows=size.rows if graphics else None) + "\n"

    async def show_welcome(self, info: Mapping[str, str], *, skip_footer: bool = False) -> None:
        if self._closed or self._closing:
            return
        if self._task is None or self._reports is None:
            raise RuntimeError("请先启动输入owner。")
        if self._motion is not None:
            await self._motion.dispose()
        self._welcome_info = dict(info)
        self._welcome_skip_footer = skip_footer
        self._welcome_still_presented = False
        self._queries = TerminalQueries(self._reports, self._write_control,
                                        isTTY=(not isinstance(self._output, PlainTextOutput)
                                               and self._background_env.get("TERM") != "dumb" and self._view.caps.tier != "none"),
                                        cursor_offset=self._dynamic_rows)
        cell = await self._queries.probe() if self.background == "dark" else None
        self._motion = createWelcomeMotion(reports=self._queries, write=self._write_control,
                                           dimensions=lambda: (self._output.get_size().columns, self._output.get_size().rows),
                                           waitUntilRenderFlush=self._wait_render_flush, cell=cell)
        self._motion_state = None
        future: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._enqueue_output(self._welcome_text(), True, future)
        await future
        self._update_motion()
        self.app.invalidate()
        # 调用方可能在返回后立即追加启动文字。
        # 先画出首个原生画面，避免新增文字覆盖欢迎区的锚点。
        await self._motion.advance()

    def configure_images(self, *, clipboard: Callable[[], ClipboardPayload] | None = None) -> None:
        self._clipboard_port = clipboard

    def _start_image_task(self, action: Coroutine[Any, Any, None]) -> None:
        task = asyncio.create_task(action)
        self._image_tasks.add(task)
        def done(future: asyncio.Task[None]) -> None:
            self._image_tasks.discard(future)
            if not future.cancelled():
                error = future.exception()
                if error is not None:
                    self._error = error if isinstance(error, Exception) else RuntimeError("图片读取已中断，草稿保留。")
                    self._request_exit()
        task.add_done_callback(done)

    async def _attach_clipboard(self) -> None:
        try:
            async with self._image_lock:
                images = await getClipboardImages(self._clipboard_port)
                if self._closed or self._closing:
                    return
                if not images:
                    from ..i18n.i18n import getLang
                    self._input_notice = ("剪贴板没有可用图片或读取失败，原草稿保留。" if getLang() == "zh" else
                                          "No supported clipboard image or read failed; draft preserved.")
                else:
                    self._input_notice = ""
                    self.buffer.insert_text("".join(self._pastes.insert_image(image) for image in images))
                self.app.invalidate()
        finally:
            self._clipboard_active = False

    async def _paste_image_path(self, original: str, path: Path) -> None:
        async with self._image_lock:
            image = await asyncio.to_thread(imageFromPath, path)
            if self._closed or self._closing:
                return
            self.buffer.insert_text(self._pastes.insert_image(image) if image is not None else self._pastes.insert(original))
            self.app.invalidate()

    def emit_event(self, kind: str, **payload: Any) -> None:
        if self._closed:
            return
        self._view.emit(kind, **payload)
        self.app.invalidate()

    def restore_history(self, messages: Sequence[Mapping[str, Any]]) -> None:
        self._view.restore_history(messages)
        self.app.invalidate()

    async def replace_history(self, messages: Sequence[Mapping[str, Any]]) -> None:
        await self.drain_render()
        self._view.replace_history(messages)
        if self._owned_viewport:
            self._viewport_entries = list(self._view.items)
            self._resize_epoch += 1
            await self._rebuild_viewport(self._resize_epoch)
        self.app.invalidate()

    def _style(self) -> Style:
        background = self.background
        return Style.from_dict({"input-frame": semHex("dim" if self._state == "running" else "jade", background),
                                "input": f"{semHex('ink', background)} bg:{semHex('panel', background)}",
                                "permission-status": f"{semHex('jade', background)} bold"})

    def _live_text(self) -> ANSI:
        size = self._output.get_size()
        return ANSI(self._view.live_text(size.columns, size.rows, int(monotonic() * 10)))

    def _status_bar(self) -> FormattedText:
        info = self._status_info
        def count(name: str) -> str:
            value = info.get(name, 0)
            number = float(value) if isinstance(value, (float, int)) else 0
            return str(int(number)) if number < 1000 else f"{number / 1000:.1f}k" if number < 10000 else f"{number / 1000:.0f}k"
        mode = str(info.get("permMode", "default"))
        prefix = t("mode." + mode)
        prefix += " · " if mode == "plan" else t("ui.modeShortcut")
        text = str(info.get("model", "")).rsplit("/", 1)[-1]
        cost_value = info.get("costCNY", 0)
        cost = float(cost_value) if isinstance(cost_value, (float, int)) else 0.0
        text += f" · ￥{cost:.3f}" if cost < 1 else f" · ￥{cost:.2f}"
        text += f" · {t('ui.status.context')} {count('contextUsed')}/{count('contextWindow')}"
        if branch := info.get("branch"):
            text += " · ⎇ " + str(branch)
        return FormattedText([("class:permission-status", prefix), ("", clean_text(text))])

    def _before_render(self, app: Application[None]) -> None:
        size = self._output.get_size()
        if size.columns == self._columns and size.rows == self._rows:
            return
        if self._motion is not None:
            self._motion.resized()
        self._columns = size.columns
        self._rows = size.rows
        self._view.caps = Capabilities(self._view.caps.tier, True, size.columns)
        self._resize_epoch += 1
        if self._resize_timer is not None:
            self._resize_timer.cancel()
        if self._owned_viewport and not self._closing:
            epoch = self._resize_epoch
            self._resize_timer = asyncio.get_running_loop().call_later(.2, self._start_rebuild, epoch)

    def _after_render(self, app: Application[None]) -> None:
        self._update_motion()

    def _start_rebuild(self, epoch: int) -> None:
        if self._resize_timer is not None:
            self._resize_timer.cancel()
        self._resize_timer = None
        self._resize_task = asyncio.create_task(self._rebuild_viewport(epoch))
        self._resize_tasks.add(self._resize_task)
        self._resize_task.add_done_callback(self._resize_tasks.discard)

    async def _rebuild_viewport(self, epoch: int) -> None:
        if self._closing or self._closed or epoch != self._resize_epoch or not self._owned_viewport:
            return
        if self._motion is not None:
            await self._motion.reset()
        async with self._output_lock:
            if self._closing or self._closed or epoch != self._resize_epoch or not self._owned_viewport:
                return
            emitted = False
            still_presented = False
            def emit() -> None:
                nonlocal emitted, still_presented
                if self._closing or epoch != self._resize_epoch:
                    return
                size = self._output.get_size()
                self._output.write_raw("\x1b[0m\x1b[2J\x1b[3J\x1b[H")
                welcome = self._welcome_text(size)
                if welcome:
                    print_formatted_text(self._output, ANSI(welcome), _OUTPUT_STYLE)
                    if self.background == "dark" and self._motion is not None:
                        frame = self._motion.still_at_viewport_top(size.columns, size.rows)
                        if frame is not None:
                            try:
                                # 清屏先确立锚点，再回放会话，避免把锚点滚出屏幕。
                                self._output.write_raw(frame)
                            except Exception:
                                pass  # 文本降级已经显示，可以继续回放历史。
                            else:
                                still_presented = True
                formatted: list[str] = []
                for entry in self._viewport_entries:
                    if isinstance(entry, TranscriptItem):
                        formatted.append(self._view.render_item(entry) + "\n")
                    else:
                        if formatted:
                            print_formatted_text(self._output, ANSI("".join(formatted)), _OUTPUT_STYLE)
                            formatted.clear()
                        self._output.write(entry)
                if formatted:
                    print_formatted_text(self._output, ANSI("".join(formatted)), _OUTPUT_STYLE)
                self._output.flush()
                emitted = True
            with set_app(self.app):
                await run_in_terminal(emit)
            if emitted:
                self._welcome_epoch += 1
                self._welcome_untracked = False
                self._welcome_still_presented = still_presented
                self.app.invalidate()

    def _commit_item(self, item: TranscriptItem) -> None:
        self._commit_render(self._view.render_item(item) + "\n", item=item)

    def _commit_render(self, text: str, *, item: TranscriptItem | None = None) -> None:
        if self._motion is not None:
            self._motion.pause()
        self._enqueue_output(text, True, item=item)

    def _enqueue_output(self, text: str, formatted: _RenderFormat, future: asyncio.Future[None] | None = None,
                        guard: Callable[[], bool] | None = None, *, item: TranscriptItem | None = None) -> None:
        self._render_queue.append((text, formatted, future, guard, item))
        if self._render_task is None or self._render_task.done():
            self._render_task = asyncio.create_task(self._render_output())

    async def _render_output(self) -> None:
        async with self._output_lock:
            while self._render_queue:
                text, formatted, future, guard, item = self._render_queue.popleft()
                try:
                    def emit() -> None:
                        if guard is not None and not guard():
                            return
                        if formatted == "control":
                            self._output.write_raw(text)
                            self._output.flush()
                        elif formatted is True:
                            # 当前写入由 run_in_terminal 接管，须在这次操作返回之前完成绘制。
                            print_formatted_text(self._output, ANSI(text), _OUTPUT_STYLE)
                        else:
                            self._output.write(text)
                            self._output.flush()
                        if self._owned_viewport and (item is not None or formatted in {False, "notification"}):
                            self._viewport_entries.append(item if item is not None else text)
                    with set_app(self.app):
                        await run_in_terminal(emit)
                    if future is not None and not future.done():
                        future.set_result(None)
                except Exception as error:
                    if formatted in {"control", "notification"}:
                        if future is not None and not future.done():
                            future.set_exception(error)
                        continue  # 次要提示或标题更新失败后，后续业务输出和任务仍继续。
                    self._render_error = error
                    if future is not None and not future.done():
                        future.set_exception(error)
                    while self._render_queue:
                        _, _, pending, _, _ = self._render_queue.popleft()
                        if pending is not None and not pending.done():
                            pending.set_exception(error)
                    self._request_exit()
                    return

    async def _write_control(self, text: str, guard: Callable[[], bool]) -> bool:
        emitted = False
        def fresh() -> bool:
            nonlocal emitted
            emitted = not self._closed and not self._closing and guard()
            return emitted
        future: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._enqueue_output(text, "control", future, fresh)
        try:
            await future
            return emitted
        except Exception:
            return False

    async def drain_render(self) -> None:
        self._view.flush_live()
        if self._render_task is not None:
            await self._render_task
        if self._render_error is not None:
            raise self._render_error

    def _status_text(self) -> str:
        if self._exit_armed_at is not None and 0 <= monotonic() - self._exit_armed_at <= 2:
            return t("ui.hint.ctrlcExit")
        labels = {"idle": "就绪", "running": "运行中", "waiting": "等待中", "paused": "已暂停",
                  "recovering": "恢复中", "closed": "已结束"}
        english = {"idle": "Ready", "running": "Running", "waiting": "Waiting", "paused": "Paused",
                   "recovering": "Recovering", "closed": "Closed"}
        from ..i18n.i18n import getLang
        status = (labels if getLang() == "zh" else english).get(self._state, self._state)
        if self._input_notice:
            return self._input_notice
        return (f"{status} · 排队 {self._queued} · Esc 清队列/暂停 · Ctrl+C 退出" if getLang() == "zh" else
                f"{status} · Queued {self._queued} · Esc clear queue/pause · Ctrl+C exit")

    def _protocol_event(self, kind: str, **data: object) -> None:
        if self._queries is not None:
            self._queries.on_event(kind, **data)
        if kind == "focus" and self._motion is not None:
            self._motion.setFocused(data.get("focused") is True)
        if kind == "focus" and data.get("focused") is True:
            self.clear_attention()
        elif kind == "query-ended" and data.get("query") == "background":
            future = self._background_future
            result = data.get("result")
            if future is not None and not future.done():
                color = None
                if isinstance(result, dict) and all(isinstance(result.get(key), int) for key in ("red", "green", "blue")):
                    color = fromRGB(result["red"], result["green"], result["blue"])
                future.set_result(color)
        elif kind == "paste-rejected":
            self._input_notice = "此次粘贴超过 8 MiB，已整段拒收，原草稿保留。"
            self.app.invalidate()
        elif kind == "paste-accepted":
            self._input_notice = ""
            self.app.invalidate()

    def _request_exit(self) -> None:
        self._closing = True
        if self._motion is not None:
            self._motion.pause()
        if self._queries is not None:
            self._queries.dispose()
        self._resize_epoch += 1
        if self._resize_timer is not None:
            self._resize_timer.cancel()
            self._resize_timer = None
        if self._exit_timer is not None:
            self._exit_timer.cancel()
            self._exit_timer = None
        self._finish_approval(None)
        if self.app.is_running and not self.app.is_done:
            self.app.exit()

    def _finish_approval(self, text: str | None) -> None:
        future = self._approval
        if future is not None:
            self._approval = None
            self._approval_prompt = ""
            self._modal = None
            self._secret_answer = False
            self._answer.reset()
            self.app.layout.focus(self._panel_control if self._panel is not None else self._control)
            self.app.invalidate()
            if not future.done():
                future.set_result(text)

    def _dialog_text(self) -> str:
        return self._modal.render(self._answer.text, self._output.get_size().rows) if self._modal else clean_text(self._approval_prompt)

    def _handle_modal(self, key: str, text: str = "") -> bool:
        modal = self._modal
        if modal is None:
            return False
        if modal.finished:
            return True  # 当前这批按键由模态窗口消费，避免确认后的 Enter 又提交主草稿。
        try:
            handled = modal.handle(key, text, self._answer)
        except Exception as error:
            self._error = error
            self._request_exit()
            return True
        if modal.finished:
            if modal.cancelled and modal.kind == "approval":
                self._approval_generation += 1
                async def pause_only() -> None:
                    await self._on_pause()
                self._pause_task = asyncio.create_task(pause_only())
            if modal.kind == "choice" and modal.value is not None:
                self.emit_event("user_message", text=modal.value)
            def finish_current() -> None:
                if self._modal is modal:
                    self._finish_approval(modal.value)
            asyncio.get_running_loop().call_soon(finish_current)
        self.app.invalidate()
        return handled

    async def _open_modal(
        self, prompt: str, *, modal: Modal | None = None, secret: bool = False,
        cancelled: Callable[[], bool] | None = None,
    ) -> str | None:
        if self._closed or self._closing or (cancelled is not None and cancelled()):
            return None
        if self._task is None:
            raise RuntimeError("请先启动输入owner。")
        future: asyncio.Future[str | None] = asyncio.get_running_loop().create_future()
        self._approval, self._modal = future, modal
        self._approval_prompt = modal.render("", self._output.get_size().rows) if modal is not None else prompt
        self._secret_answer = secret
        self._answer.reset()
        self.app.layout.focus(self._answer_control)
        self.app.invalidate()
        self.mark_attention()
        async def watch_cancel() -> None:
            while not future.done():
                if cancelled is not None and cancelled():
                    if self._approval is future:
                        self._finish_approval(None)
                    return
                await asyncio.sleep(.05)
        watcher = asyncio.create_task(watch_cancel()) if cancelled is not None else None
        try:
            answer = await future
            return None if cancelled is not None and cancelled() else answer
        finally:
            if watcher is not None:
                watcher.cancel()
                try:
                    await watcher
                except asyncio.CancelledError:
                    pass
            if self._approval is future:
                self._finish_approval(None)

    async def ask_text(self, prompt: str, *, secret: bool = False, cancelled: Callable[[], bool] | None = None) -> str | None:
        async with self._approval_lock:
            return await self._open_modal(prompt, secret=secret, cancelled=cancelled)

    async def ask_secret_validated(self, prompt: str, submit: Callable[[str], Awaitable[bool]], *,
                                   validating: str) -> str | None:
        async with self._approval_lock:
            task: asyncio.Task[None] | None = None

            async def attempt(value: str) -> None:
                try:
                    accepted = await submit(value)
                except (Exception, asyncio.CancelledError):
                    if self._modal is modal:
                        self._finish_approval(None)
                    raise
                if self._modal is modal:
                    if accepted:
                        self._finish_approval(value)
                    else:
                        modal.busy = False
                        self.app.invalidate()

            def begin(value: str) -> None:
                nonlocal task
                task = asyncio.create_task(attempt(value))

            modal = SecretValidationModal(prompt, validating, begin)
            try:
                return await self._open_modal(prompt, modal=modal, secret=True)
            finally:
                if task is not None:
                    # 写入提交后可能已经落盘，先等到结果明确，
                    # 再释放当前输入所有者的审批位置或报告失败。
                    await asyncio.shield(task)

    async def ask_trust(self, prompt: str) -> bool | None:
        async with self._approval_lock:
            answer = await self._open_modal(prompt, modal=TrustModal(prompt))
            return None if answer is None else answer == "yes"

    async def select(self, title: str, items: Sequence[SelectItem], *, initial_index: int = 0, wrap: bool = False,
                     refresh: Callable[[], Awaitable[Sequence[SelectItem]]] | None = None) -> str | None:
        if not items:
            return None
        async with self._approval_lock:
            modal = Modal(title, items, initial=initial_index, wrap=wrap)
            original = modal.selection.value
            async def update() -> None:
                if refresh is None:
                    return
                try:
                    fresh = await refresh()
                except Exception:
                    return  # 模型列表读取失败时，保留当前模型。
                if fresh and self._modal is modal and not modal.finished:
                    modal.selection.items = list(fresh)
                    modal.selection.index = next((index for index, item in enumerate(fresh) if item["value"] == original), 0)
                    self.app.invalidate()
            updater = asyncio.create_task(update()) if refresh is not None else None
            try:
                return await self._open_modal(title, modal=modal)
            finally:
                if updater is not None:
                    updater.cancel()
                    try:
                        await updater
                    except asyncio.CancelledError:
                        pass

    async def ask_choice(self, question: str, options: Sequence[str], multi: bool = False,
                         *, cancelled: Callable[[], bool] | None = None) -> str | None:
        async with self._approval_lock:
            return await self._open_modal(question, modal=Modal.choice(question, options, multi), cancelled=cancelled)

    async def approval_prompt(self, requests: Sequence[ApprovalRequest], *, cancelled: Callable[[], bool] | None = None) -> dict[str, ApprovalDecision]:
        generation = self._approval_generation
        async with self._approval_lock:
            if generation != self._approval_generation:
                return {}
            result: dict[str, ApprovalDecision] = {}
            for index, request in enumerate(requests):
                answer = await self._open_modal("", modal=Modal.approval(request, index, len(requests)), cancelled=cancelled)
                if answer is None:
                    return {}  # Esc 或取消否决整个批次，包括之前临时选定但尚未执行的项。
                result[request["id"]] = "always" if answer == "always" else "once" if answer == "once" else "deny"
            return result

    async def pick_skills(self, controls: SkillControls) -> str:
        async with self._approval_lock:
            modal = Modal.skills(controls)
            await self._open_modal("", modal=modal)
            from ..i18n.i18n import getLang
            return ("技能设置已保存，重启生效。" if getLang() == "zh" else "Skill settings saved; restart to apply.") if modal.changed else ""

    async def ask_approval(self, prompt: str, *, cancelled: Callable[[], bool] | None = None) -> str:
        return await self.ask_selection(prompt, cancelled=cancelled) or ""

    async def ask_selection(self, prompt: str, *, cancelled: Callable[[], bool] | None = None) -> str | None:
        async with self._approval_lock:
            return await self._open_modal(prompt, cancelled=cancelled)

    def restore_submission(self, text: Content) -> None:
        """把未确认的提交放回草稿，并保留用户正在编辑的内容与相对光标位置。"""
        text = self._pastes.restore_content(text)
        current = self.buffer.document
        prefix = text + "\n" if current.text else text
        position = len(prefix) + current.cursor_position
        self.buffer.set_document(Document(prefix + current.text, position))
        self.app.invalidate()

    async def _run(self, ready: asyncio.Future[None]) -> None:
        def started() -> None:
            self._tab = createTabAttention(
                formatTabTitle("", self._tab_name), write=self._attention_write,
                isTTY=not isinstance(self._output, PlainTextOutput), env=self._background_env)
            self._background_task = asyncio.create_task(self._initialize_background(ready))
            if self._closing:
                self.app.exit()

        gate: ParserGate | None = None
        expiry: asyncio.Task[None] | None = None

        async def expire_reports() -> None:
            assert gate is not None
            while True:
                await asyncio.sleep(.05)
                if gate.tick():
                    self.app.key_processor.feed_multiple(self._input.flush_keys())
                    self.app.key_processor.process_keys()

        try:
            reports = Reports(self._protocol_event,
                              cpr_pending=lambda: self.app.renderer.waiting_for_cpr)
            self._reports = reports
            gate = ParserGate(self._input, reports, monotonic)
            expiry = asyncio.create_task(expire_reports())
            await self.app.run_async(pre_run=started, set_exception_handler=False,
                                     handle_sigint=False)
        except EOFError:
            pass
        except Exception as exc:
            self._error = exc
            if not ready.done():
                ready.set_exception(exc)
        finally:
            if self._queries is not None:
                self._queries.dispose()
            if self._motion is not None:
                await self._motion.dispose()
            if self._tab is not None:
                self._tab.dispose()
                if self._render_task is not None:
                    await self._render_task
            if self._background_task is not None and not self._background_task.done():
                self._background_task.cancel()
                try:
                    await self._background_task
                except asyncio.CancelledError:
                    pass
            if expiry is not None:
                expiry.cancel()
                try:
                    await expiry
                except asyncio.CancelledError:
                    pass
            if gate is not None:
                gate.restore()
            self._reports = None
            self._closed = True
            self._finish_approval(None)
            self._submissions.put_nowait(None)
            if self._owns_input:
                self._input.close()
            if not ready.done():
                ready.set_result(None)

    async def _initialize_background(self, ready: asyncio.Future[None]) -> None:
        try:
            background = await resolveBackground(self._background_env, probe=self._probe_background)
            if not self._closing:
                self.set_theme(background)
        except Exception:
            pass  # 显示探测失败时，以深色方案继续，业务循环不受影响。
        finally:
            if not ready.done():
                ready.set_result(None)

    async def _probe_background(self) -> str | None:
        reports = self._reports
        if reports is None:
            return None
        self._background_future = asyncio.get_running_loop().create_future()
        reports.begin("background", monotonic())
        reports.deadline = monotonic() + .25
        await self._write_control("\x1b]11;?\x07", lambda: reports.kind == "background")
        try:
            return await asyncio.wait_for(asyncio.shield(self._background_future), .3)
        except TimeoutError:
            if reports.kind == "background":
                reports.settle("timeout")
            return None
        finally:
            self._background_future = None

    async def start(self) -> None:
        if self._closed:
            raise RuntimeError("输入owner已关闭。")
        if self._task is None:
            self._ready = asyncio.get_running_loop().create_future()
            self._task = asyncio.create_task(self._run(self._ready))
        assert self._ready is not None
        await self._ready

    async def next_submission(self) -> Content | None:
        if self._closed and self._submissions.empty():
            if self._error is not None:
                raise self._error
            return None
        if self._task is None:
            raise RuntimeError("请先启动输入owner。")
        text = await self._submissions.get()
        if text is None and self._error is not None:
            raise self._error
        return text

    async def write(self, text: str, *, end: str = "\n") -> None:
        if self._welcome_info is not None and (text or end):
            self._welcome_untracked = True
            if self._motion is not None:
                self._motion.resized()
        future: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._enqueue_output(text + end, False, future)
        await future

    async def close(self) -> None:
        self._closing = True
        if self._handoff_task is not None and not self._handoff_task.done():
            self._finish_approval(None)
            await asyncio.shield(self._handoff_task)
        if self._mode_task is not None:
            await self._mode_task
        await self.drain_render()
        if self._image_tasks:
            await asyncio.gather(*tuple(self._image_tasks))
        if self._task is None:
            if not self._closed:
                self._closed = True
                self._submissions.put_nowait(None)
                if self._owns_input:
                    self._input.close()
            return
        self._request_exit()
        await self._task
        if self._pause_task is not None:
            await self._pause_task
        if self._resize_tasks:
            await asyncio.gather(*tuple(self._resize_tasks))
