"""冻结App.tsx（MIT）的转录/live职责；由唯一ptk输入owner执行终端I/O。"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, Protocol, cast

from prompt_toolkit.utils import get_cwidth

from ...config.profiles import Provider
from ...i18n.i18n import getLang, t
from ..capabilities import Capabilities
from ..input_text import normalizeSurrogates
from ..markdown import renderMarkdown
from ..onboarding.select import SelectItem
from ..theme import PALETTES, paint
from ..width import displayWidth, padEnd
from .format import parseTodoResult
from .types import AccountActions, LiveState, TranscriptItem

_SGR = re.compile(r"\x1b\[[0-9;]*m")
_VT = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\|$)|\x1b\[[0-?]*[ -/]*[@-~]|\x1b.")
_VERBS = {"Read": "readFile", "ListDir": "listDir", "Grep": "grepFiles", "Glob": "fileSearch", "Bash": "execShell",
          "BashOutput": "execPoll", "KillShell": "execKill", "Write": "writeFile", "Edit": "editFile", "MultiEdit": "multiEdit",
          "WebSearch": "webSearch", "WebFetch": "fetchUrl", "MemoryWrite": "memoryWrite", "TodoWrite": "todoWrite",
          "AskUserQuestion": "askUser", "agent": "agent"}
_ECHO = {"Bash", "BashOutput", "Grep", "WebSearch", "WebFetch"}


def clean_text(value: str) -> str:
    """原文不允许注入VT；此后只有渲染器能生成SGR。"""
    return "".join(char for char in _VT.sub("", normalizeSurrogates(value))
                   if char in "\n\t" or ord(char) >= 32 and ord(char) != 127)


def panel_line(text: str, columns: int) -> str:
    width = 0
    line = clean_text(text).replace("\n", " ").replace("\t", " ")
    for index, char in enumerate(line):
        width += get_cwidth(char)
        if width > max(1, columns - 4):
            return line[:index]
    return line


def tail(text: str, maximum: int, cols: int = 80) -> str:
    rows, index, lines = 0, len(text.split("\n")), text.split("\n")
    while index > 0:
        following = rows + max(1, math.ceil(displayWidth(lines[index - 1]) / max(1, cols)))
        if following > maximum:
            break
        rows = following
        index -= 1
    return text if index <= 0 else "…\n" + "\n".join(lines[index:])


def _verb(name: str) -> str:
    return t("ui.verb." + _VERBS[name]) if name in _VERBS else name


def activityLabel(name: str, raw: str) -> str:
    try:
        args = json.loads(raw)
        if not isinstance(args, dict):
            args = {}
    except (ValueError, TypeError):
        args = {}
    def text(key: str) -> str:
        value = args.get(key)
        return clean_text(value) if isinstance(value, str) else ""
    if name in {"Read", "ListDir", "Write", "Edit", "MultiEdit"}:
        extra = f" :{args['offset']}" if name == "Read" and args.get("offset") else ""
        return f"{_verb(name)} {text('path') or ('.' if name == 'ListDir' else '')}{extra}"
    if name in {"Grep", "WebSearch"}:
        value = json.dumps(text("pattern" if name == "Grep" else "query"), ensure_ascii=False)
        return f"{_verb(name)} {value}" + (f" ({text('glob')})" if name == "Grep" and text("glob") else "")
    if name == "Glob":
        return f"{_verb(name)} {text('glob')}"
    if name == "Bash":
        return "$ " + text("command").split("\n")[0][:80]
    if name in {"BashOutput", "KillShell", "TodoWrite"}:
        return t("ui.tool." + {"BashOutput": "execPoll", "KillShell": "execKill", "TodoWrite": "todoWrite"}[name])
    if name == "WebFetch":
        return f"{_verb(name)} {text('url')}"
    if name == "MemoryWrite":
        return f"{_verb(name)} {text('text')[:50]}"
    if name == "Skill":
        return f"Skill({text('name') or '?'})"
    if name == "Agent":
        return t("ui.tool.agentParallel", len(args["tasks"])) if isinstance(args.get("tasks"), list) else t("ui.tool.agentOne", text("task")[:50])
    return _verb(name)


def resultDetail(name: str, ok: bool, content: str) -> str:
    lines = content.split("\n")
    if not ok:
        return lines[0][:120]
    if name in {"Read", "Write"}:
        return t("ui.detail.lines", len(lines))
    if name in {"ListDir", "Grep", "Glob"}:
        return content if content.startswith("(") else t("ui.detail." + {"ListDir": "items", "Grep": "matches", "Glob": "found"}[name], len(lines))
    if name == "Bash":
        return next((line[:100] for line in reversed(lines) if line.strip()), "")
    if name == "WebSearch":
        return content if content.startswith("(") else t("ui.detail.results", len(content.split("\n\n")))
    if name == "WebFetch":
        return t("ui.detail.chars", len(content))
    if name == "Skill":
        if content.startswith("未找到"):
            return lines[0][:80]
        match = re.search(r"^# Skill:\s*(.+)$", content, re.M)
        return t("ui.tool.skillLoaded", " " + match[1].strip() if match else "")
    return ""


class App:
    """只持展示状态，已完成项进scrollback；模型/调度/持久化仍归原模块。"""

    def __init__(self, commit: Callable[[str], None], *, caps: Capabilities, background: str = "dark", verbose: bool = False,
                 commit_item: Callable[[TranscriptItem], None] | None = None) -> None:
        self._commit = commit
        self._commit_item = commit_item
        self.caps, self.background, self.expanded = caps, background, verbose
        self.items: list[TranscriptItem] = []
        self.live = LiveState()

    def _paint(self, text: str, semantic: str) -> str:
        return paint(text, semantic, self.caps, self.background)

    def _panel(self, text: str) -> str:
        if self.caps.tier == "none":
            return text
        rgb, ansi256, ansi16 = PALETTES[self.background]["panel"]
        prefix = (f"\x1b[48;2;{rgb[0]};{rgb[1]};{rgb[2]}m" if self.caps.tier == "truecolor" else
                  f"\x1b[48;5;{ansi256}m" if self.caps.tier == "ansi256" else f"\x1b[{ansi16}m")
        return prefix + self._paint(text, "ink") + "\x1b[49m"

    def _push(self, kind: str, **data: Any) -> None:
        item = TranscriptItem(len(self.items) + 1, kind, data)
        self.items.append(item)
        if self._commit_item is None:
            self._commit(self.render_item(item) + "\n")
        else:
            self._commit_item(item)

    def reasoning(self, chunk: str) -> None:
        self.live.reasoning += clean_text(chunk)

    def content(self, chunk: str) -> None:
        self.live.content += clean_text(chunk)

    def toolStart(self, call: dict[str, Any]) -> None:
        name = clean_text(str(call.get("name", "")))
        self.live.tools.append(name)
        self.live.toolCount += 1

    def assistantDone(self, message: dict[str, Any]) -> None:
        reasoning = self.live.reasoning or message.get("reasoning_content", "") or ""
        if isinstance(reasoning, str) and reasoning.strip():
            self._push("reasoning", text=clean_text(reasoning))
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            self._push("assistant", text=clean_text(content))
        self.live.reasoning = self.live.content = ""

    def toolResult(self, call: dict[str, Any], message: dict[str, Any]) -> None:
        function = call.get("function", {})
        name = clean_text(str(function.get("name", "")))
        raw = clean_text(str(function.get("arguments", "")))
        content = clean_text(message.get("content", "")) if isinstance(message.get("content"), str) else ""
        ok = not content.startswith("Error") and "拒绝" not in content
        try:
            args = json.loads(raw)
            if not isinstance(args, dict):
                raise ValueError("arguments")
            if ok and name in {"Edit", "MultiEdit"}:
                rows = [line for block in re.findall(r"```diff\n([\s\S]*?)\n```", content) for line in block.split("\n")]
                edits = args.get("edits", []) if name == "MultiEdit" else []
                removed = [""] * len(edits) if edits else clean_text(str(args.get("old_string", ""))).removesuffix("\n").split("\n")
                added = [""] * len(edits) if edits else clean_text(str(args.get("new_string", ""))).removesuffix("\n").split("\n")
                self._push("diff", path=clean_text(str(args.get("path", ""))), rows=rows, removed=removed, added=added)
            elif ok and name == "TodoWrite":
                self._push("todo", items=parseTodoResult(content))
            else:
                raise ValueError("ordinary tool")
        except (ValueError, TypeError):
            displayed = content.removesuffix("\n[exit 0]") if name == "Bash" and content.split("\n")[-1].strip() == "[exit 0]" else content
            self._push("tool", label=clean_text(activityLabel(name, raw)), detail=resultDetail(name, ok, displayed), ok=ok,
                       output=displayed.split("\n") if displayed.strip() else [], rawArgs=raw, echo=name in _ECHO)
        if name in self.live.tools:
            self.live.tools.remove(name)

    def notice(self, text: str) -> None:
        if text.strip():
            self._push("notice", text=clean_text(text.strip()))

    def userMessage(self, text: str) -> None:
        self._push("user", text=clean_text(text))

    def emit(self, kind: str, **payload: Any) -> None:
        if kind in {"reasoning", "content", "notice", "user_message"}:
            {"reasoning": self.reasoning, "content": self.content, "notice": self.notice,
             "user_message": self.userMessage}[kind](str(payload["text"]))
        elif kind == "assistant_done":
            self.assistantDone(payload["message"])
        elif kind == "permission_mode":
            self._push(kind, text=clean_text(str(payload["text"])))
        elif kind == "tool_start":
            self.toolStart(payload)
        elif kind == "tool_result":
            self.toolResult(payload["call"], payload["message"])
        elif kind == "flush":
            self.flush_live()
        else:
            raise ValueError("未知终端事件")

    def flush_live(self) -> None:
        # 未收到saved事件的取消/失败沿旧逐字输出保留已生成正文，只做一次边界。
        if self.live.reasoning.strip() or self.live.content.strip():
            self.assistantDone({"content": self.live.content})
        self.live = LiveState()

    def render_item(self, item: TranscriptItem, *, expanded: bool | None = None) -> str:
        data, kind = item.data, item.kind
        expanded = self.expanded if expanded is None else expanded
        if kind == "assistant":
            value = renderMarkdown(data["text"], self.caps.columns)
            return "\n" + (_SGR.sub("", value) if self.caps.tier == "none" else value)
        if kind == "user":
            return "\n" + "\n".join(self._panel("  " + padEnd(line or " ", max(1, self.caps.columns - 2))) for line in data["text"].split("\n"))
        if kind == "reasoning":
            lines = [line for line in data["text"].split("\n") if line.strip()]
            shown = lines if expanded else lines[-6:]
            label = t("ui.reasoning.label") + (t("ui.reasoning.more", len(lines)) if len(lines) > 6 and not expanded else "")
            return "\n" + self._paint("\n".join([label, *("  " + line for line in shown)]), "dim")
        if kind == "notice":
            return self._paint(data["text"], "dim")
        if kind == "permission_mode":
            return self._paint(data["text"], "jade")
        if kind == "todo":
            icons = {"pending": "☐", "in_progress": "▶", "completed": "☑"}
            return "\n" + self._paint(t("ui.row.todoTitle"), "jade") + "\n" + "\n".join(
                self._paint("  " + icons[value["status"]] + " " + value["content"],
                            "dim" if value["status"] == "completed" else "gold" if value["status"] == "in_progress" else "ink") for value in data["items"])
        if kind == "diff":
            rows = data["rows"] or [*("- " + line for line in data["removed"]), *("+ " + line for line in data["added"])]
            shown = rows if expanded else rows[:40]
            output = [self._paint(f"● {t('ui.row.edit')} {data['path']} (-{len(data['removed'])} +{len(data['added'])})", "jade")]
            output.extend(self._paint("  " + line, "jade" if line.startswith("+") else "vermilion" if line.startswith("-") else "dim") for line in shown)
            if len(rows) > len(shown):
                output.append(self._paint("  " + t("ui.row.moreLines", len(rows) - len(shown)), "dim"))
            return "\n" + "\n".join(output)
        if kind == "tool":
            output = data["output"]
            visible = (data["echo"] or expanded) and bool(output)
            header = self._paint("● ", "jade" if data["ok"] else "vermilion") + data["label"]
            if data["detail"]:
                header += "  " + self._paint(data["detail"], "dim" if data["ok"] else "vermilion")
            if output and not visible:
                header += "  " + self._paint(t("ui.row.expandHint"), "dim")
            lines = [header]
            if expanded and data["rawArgs"]:
                lines.append(self._paint("  ⎿ " + t("ui.row.args") + " " + data["rawArgs"], "dim"))
            if visible:
                shown = output if expanded else output[:8]
                lines.extend(self._paint(("  ⎿ " if index == 0 else "    ") + line, "dim") for index, line in enumerate(shown))
                if len(output) > len(shown):
                    lines.append(self._paint("  " + t("ui.row.moreLines", len(output) - len(shown)), "dim"))
            return "\n" + "\n".join(lines)
        return ""

    def toggle_expanded(self) -> None:
        self.expanded = not self.expanded
        self._commit(self._paint(t("ui.notice.expandAll" if self.expanded else "ui.notice.collapseAll"), "dim") + "\n")
        if self.expanded:
            for item in reversed(self.items):
                if item.kind in {"tool", "reasoning", "diff"}:
                    self._commit(self.render_item(item, expanded=True) + "\n")
                    break

    def live_text(self, columns: int, rows: int, tick: int = 0) -> str:
        maximum = max(4, min(12, rows - 10))
        text = self.live.content or self.live.reasoning
        parts = []
        if text:
            parts.append(tail(text, max(1, maximum - 2), columns))
        if self.live.tools:
            label = t("ui.activity.toolRequest", _verb(self.live.tools[-1]))
        elif self.live.content:
            label = t("ui.activity.replying")
        elif self.live.reasoning:
            label = t("ui.activity.thinking")
        else:
            return ""
        parts.append(self._paint("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"[tick % 10] + " " + label, "jade"))
        return "\n".join(parts)

    def replay(self) -> str:
        return "".join(self.render_item(item) + "\n" for item in self.items)

    def restore_history(self, messages: Sequence[Mapping[str, Any]]) -> None:
        calls: dict[str, dict[str, Any]] = {}
        for message in messages:
            role, content = message.get("role"), message.get("content")
            if role == "user":
                if isinstance(content, str):
                    self.userMessage(content)
                elif isinstance(content, list):
                    self.userMessage("\n".join(str(part.get("text", "[image]")) for part in content if isinstance(part, dict)))
            elif role == "assistant":
                self.assistantDone(dict(message))
                for call in message.get("tool_calls", []) or []:
                    if isinstance(call, dict) and isinstance(call.get("id"), str):
                        calls[call["id"]] = call
            elif role == "tool" and message.get("tool_call_id") in calls:
                self.toolResult(calls[message["tool_call_id"]], dict(message))

    def replace_history(self, messages: Sequence[Mapping[str, Any]]) -> None:
        self.items.clear()
        self.live = LiveState()
        commit, commit_item = self._commit, self._commit_item
        self._commit = lambda _text: None
        self._commit_item = None
        try:
            self.restore_history(messages)
        finally:
            self._commit, self._commit_item = commit, commit_item


class HistoryPanel:
    """A transient view of the user turns already present in App's transcript."""

    def __init__(self, view: App) -> None:
        self.view = view
        self.items = tuple(view.items)
        self.users = [index for index, item in enumerate(self.items) if item.kind == "user"]
        self.index = len(self.users) - 1
        self.review: tuple[TranscriptItem, ...] | None = None
        self.offset = 0
        self._columns = 0
        self._lines: list[str] = []

    def handle(self, key: str, rows: int) -> None:
        if self.review is not None:
            page = max(1, rows - 6)
            moves = {"up": -1, "down": 1, "pageup": -page, "pagedown": page}
            self.offset = max(0, min(len(self._lines) - page, self.offset + moves.get(key, 0)))
        elif key == "enter" and self.index >= 0:
            start = self.users[self.index]
            end = self.users[self.index + 1] if self.index + 1 < len(self.users) else len(self.items)
            self.review = self.items[start:end]
        elif key in {"up", "down"}:
            self.index = max(0, min(len(self.users) - 1, self.index + (1 if key == "down" else -1)))

    def render(self, columns: int, rows: int) -> str:
        zh = getLang() == "zh"
        page = max(1, rows - 6)
        if self.review is not None:
            if self._columns != columns:
                self._columns = columns
                self._lines = [line for item in self.review for line in clean_text(self.view.render_item(item)).splitlines()]
            start = min(self.offset, max(0, len(self._lines) - page))
            title = (f"↻ 回看历史对话(共 {len(self.review)} 条记录) · Esc 返回当前对话" if zh else
                     f"↻ Conversation review ({len(self.review)} entries) · Esc back")
            lines = [title, *self._lines[start:start + page]]
        else:
            title = (f"对话导航(共 {len(self.users)} 条用户消息) · ↑↓ 选择 · ⏎ 跳转 · Esc 关闭" if zh else
                     f"Conversation history ({len(self.users)} user messages) · ↑↓ select · Enter review · Esc close")
            start = max(0, min(self.index - page // 2, len(self.users) - page))
            lines = [title, *(f"{'❯ ' if i == self.index else '  '}{i + 1}. {self.items[item].data['text']}"
                              for i, item in enumerate(self.users[start:start + page], start))]
        return "\n".join(panel_line(line, columns) for line in lines)


class ModalUI(Protocol):
    async def select(self, title: str, items: Sequence[SelectItem], *, initial_index: int = 0, wrap: bool = False,
                     refresh: Callable[[], Awaitable[Sequence[SelectItem]]] | None = None) -> str | None: ...
    async def ask_text(self, prompt: str, *, secret: bool = False, cancelled: Callable[[], bool] | None = None) -> str | None: ...
    def emit_event(self, kind: str, **payload: Any) -> None: ...


async def runAccountPicker(ui: ModalUI, actions: AccountActions) -> str:
    rows = list(actions.listAccounts())
    if rows:
        deleting = False
        while True:
            items: list[SelectItem] = [{"label": ("● " if row.get("active") else "  ") + str(row["name"]) + " · " + str(row.get("detail", "")),
                                       "value": "account:" + str(index)} for index, row in enumerate(rows)]
            if not deleting:
                items.extend([{"label": t("ui.account.addNew"), "value": "add"}, {"label": t("ui.account.deleteEntry"), "value": "delete"}])
            answer = await ui.select(t("ui.account.deleteTitle" if deleting else "ui.account.switchTitle"), items)
            if answer is None:
                if deleting:
                    deleting = False
                    continue
                return ""
            if answer == "add":
                break
            if answer == "delete":
                deleting = True
                continue
            row = rows[int(answer.removeprefix("account:"))]
            name = str(row["name"])
            if deleting:
                await actions.removeAccount(name)
                return t("ui.account.removed", name)
            switched = await actions.switchAccount(name)
            return t("ui.account.switched", name) if switched else t("ui.notice.error", "Account not found")
    providers = ["deepseek", "qianfan", "volcengine", "zhipu", "custom"]
    provider = await ui.select(t("ui.account.providerPickerTitle"),
                               [{"label": t("ui.account.providerLabel." + value), "value": value} for value in providers])
    if provider is None:
        return t("ui.notice.cancelled")
    base_url: str | None = None
    if provider == "custom":
        base_url = (await ui.ask_text(t("ui.account.baseUrlPrompt")) or "").strip()
        if not base_url:
            return t("ui.notice.cancelled")
    key = (await ui.ask_text(t("ui.account.pastePrompt", t("ui.account.providerLabel." + provider)), secret=True) or "").strip()
    if not key:
        return t("ui.notice.cancelled")
    model = None
    if provider == "custom":
        assert base_url is not None
        ui.emit_event("notice", text=t("ui.account.fetchingModels"))
        models = await actions.fetchGatewayModels(base_url, key) if actions.fetchGatewayModels else []
        if models:
            model = await ui.select(t("ui.account.gatewayModelTitle"), [{"label": value, "value": value} for value in models])
        else:
            model = (await ui.ask_text(t("ui.account.modelPrompt")) or "").strip()
        if not model:
            return t("ui.notice.cancelled")
    name_answer = await ui.ask_text(t("ui.account.namePrompt"))
    if name_answer is None:
        return t("ui.notice.cancelled")
    name = name_answer.strip()
    ui.emit_event("notice", text=t("ui.account.validating"))
    result = await actions.addAccount(key, name or None, cast(Provider, "deepseek" if provider == "custom" else provider), base_url, model)
    if result.get("ok"):
        return t("ui.account.added", str(result.get("name", "")))
    reason = result.get("reason")
    reason = t("validate.reason." + str(reason)) if reason in {"invalid", "unreachable", "http"} else str(reason or "unknown")
    return t("ui.account.addFailed", reason)


async def runModelPicker(
    ui: ModalUI, listModels: Callable[[], Sequence[dict[str, Any]]],
    switchModel: Callable[[str], Awaitable[str | None]],
    listGatewayModels: Callable[[], Awaitable[list[str] | None]] | None = None,
) -> str:
    rows = list(listModels())
    if not rows:
        return t("ui.model.none")
    initial = next((index for index, row in enumerate(rows) if row.get("active")), 0)
    current = str(rows[initial]["model"])
    async def refreshed() -> Sequence[SelectItem]:
        models = await listGatewayModels() if listGatewayModels else None
        return [{"label": ("● " if value == current else "  ") + value, "value": value} for value in models] if models else []
    chosen = await ui.select(t("ui.model.pickerTitle"),
                             [{"label": ("● " if row.get("active") else "  ") + str(row["model"]), "value": str(row["model"])} for row in rows],
                             initial_index=initial, refresh=refreshed if listGatewayModels else None)
    return (await switchModel(chosen) or "") if chosen is not None else ""
