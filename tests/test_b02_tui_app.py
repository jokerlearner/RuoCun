"""冻结render/App/tail公开展示seam的定向来源断言。"""
import re

import pytest


def test_plain_render_source_boundaries() -> None:
    from ruocun.tui.render import plainEvents
    writes = []
    events = plainEvents(writes.append)
    events.reasoning("思考中")
    events.content("# 标题")
    events.assistantDone({"role": "assistant", "content": "# 标题"})
    output = "".join(writes)
    assert "思考中" in output and "标题" in output and "\x1b[1m" in output
    writes.clear()
    events.content("正文")
    events.toolStart({"name": "Read", "index": 0})
    events.assistantDone({"role": "assistant", "content": "正文"})
    output = re.sub(r"\x1b\[[0-9;]*m", "", "".join(writes))
    assert output.index("正文") < output.index("Read") and "→ Read" in output


def test_tail_source_visual_rows() -> None:
    from ruocun.tui.app.app import tail
    assert tail("a\nb\nc", 5, 80) == "a\nb\nc"
    assert tail("a\nb\nc\nd", 2, 80) == "…\nc\nd"
    assert tail("0" * 25, 2, 10).startswith("…\n")
    assert tail("a" * 12 + "\n" + "b" * 12, 3, 10) == "…\n" + "b" * 12
    assert tail("a" * 12 + "\n" + "b" * 12, 3, 80) == "a" * 12 + "\n" + "b" * 12
    assert tail("道" * 5 + "\n" + "道" * 5, 2, 10) == "道" * 5 + "\n" + "道" * 5
    assert tail("道" * 5 + "\n" + "道" * 5, 1, 10) == "…\n" + "道" * 5


def test_replayed_history_displays_saved_win32_surrogate_pairs_without_mutating_messages() -> None:
    from ruocun.tui.app.app import App
    from ruocun.tui.capabilities import Capabilities

    writes = []
    app = App(writes.append, caps=Capabilities("truecolor", True, 80))
    original = "验收\ud83d\ude42"
    saved = [{"role": "user", "content": original}]
    app.restore_history(saved)
    assert "验收🙂" in "".join(writes) and "验收🙂" in app.replay()
    assert saved[0]["content"] == original


def test_app_source_reasoning_tools_diff_todo_expand() -> None:
    import json

    from ruocun.i18n.i18n import setLang
    from ruocun.tui.app.app import App
    from ruocun.tui.capabilities import Capabilities
    setLang("zh")
    writes = []
    app = App(writes.append, caps=Capabilities("none", True, 80))
    assert app.live_text(80, 24) == ""
    app.reasoning("先看下结构\nThen check the response.")
    assert app.live_text(80, 24, tick=0).endswith("⠋ 正在思考…")
    assert "Then check the response." in app.live_text(80, 24)
    assert app.live_text(80, 24, tick=21).endswith("⠙ 正在思考…")
    app.content("好了")
    assert app.live_text(80, 24).endswith("⠋ 正在回复…")
    app.assistantDone({"role": "assistant", "content": "好了"})
    assert app.live_text(80, 24) == ""
    out = "".join(writes)
    assert "✻ 思考" in out and out.index("先看下结构") < out.index("Then check the response.") < out.index("好了")
    def call(name, args):
        return {"id": "c1", "function": {"name": name, "arguments": json.dumps(args)}}
    def message(content):
        return {"role": "tool", "tool_call_id": "c1", "content": content}
    app.toolResult(call("Edit", {"path": "a.ts", "old_string": "旧行", "new_string": "新行A\n新行B"}), message("已编辑 a.ts"))
    out = "".join(writes)
    assert all(value in out for value in ("a.ts", "- 旧行", "+ 新行A", "+ 新行B"))
    app.toolStart({"name": "Read", "index": 0})
    app.toolStart({"name": "Read", "index": 1})
    assert app.live_text(80, 24).endswith("⠋ 工具请求：读取")
    app.toolResult(call("Read", {"path": "b.ts"}), message("B1"))
    assert app.live_text(80, 24).endswith("⠋ 工具请求：读取")
    app.toolResult(call("Read", {"path": "a.ts"}), message("L1\nL2\nL3"))
    assert app.live_text(80, 24) == ""
    assert "L2" not in writes[-1] and "ctrl+o 展开" in writes[-1]
    app.toggle_expanded()
    assert "L2" in writes[-1]
    app.toolResult(call("Bash", {"command": "echo hi"}), message("hi\n[exit 0]"))
    assert "hi" in writes[-1] and "[exit 0]" not in writes[-1]
    app.toolResult(call("Bash", {"command": "false"}), message("[exit 1]"))
    assert "[exit 1]" in writes[-1]
    app.toolResult(call("TodoWrite", {}), message("☑ 读代码\n▶ 写实现\n☐ 测试"))
    assert all(value in writes[-1] for value in ("☑ 读代码", "▶ 写实现", "☐ 测试"))


@pytest.mark.parametrize("owned", [False, True])
def test_source_resize_replays_only_owned_and_keeps_draft(owned) -> None:
    import asyncio
    from types import SimpleNamespace

    from prompt_toolkit.data_structures import Size
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from ruocun.agent.input_broker import InputBroker

    class Output(DummyOutput):
        columns = 80
        def __init__(self):
            self.parts = []
            self.up = 0
            self.erasures = []
            self.cursor_x = 15  # Border, input prefix, then the 12-character draft.
        def get_size(self):
            return Size(rows=30, columns=self.columns)
        def write(self, data):
            self.parts.append(data)
        def write_raw(self, data):
            self.parts.append(data)
        def cursor_up(self, amount):
            self.up += amount
        def erase_down(self):
            self.erasures.append((self.columns, self.up))
            self.up = 0
        def get_win32_screen_buffer_info(self):
            return SimpleNamespace(dwCursorPosition=SimpleNamespace(X=self.cursor_x, Y=20),
                                   srWindow=SimpleNamespace(Top=5))

    async def scenario():
        output = Output()
        async def pause():
            pass
        with create_pipe_input() as pipe:
            broker = InputBroker(on_pause=pause, input=pipe, output=output)
            broker.configure_terminal({"WT_SESSION": "synthetic"}, owned_viewport=owned)
            draft_painted = asyncio.Event()

            def after_render(app):
                screen = app.renderer.last_rendered_screen
                if (screen is not None and broker.buffer.text == "queued draft"
                        and screen.get_cursor_position(app.layout.current_window).x == 15):
                    draft_painted.set()

            broker.app.after_render += after_render
            await broker.start()
            try:
                await broker.write("startup ", end="")
                await broker.write("display")
                broker.emit_event("assistant_done", message={"role": "assistant", "content": "completed history"})
                await broker.drain_render()
                broker.post_notification("notification between turns")
                broker.emit_event("assistant_done", message={"role": "assistant", "content": "next completed answer"})
                await broker.drain_render()
                broker.emit_event("content", text="in-flight response")
                pipe.send_text("queued draft")
                async with asyncio.timeout(3):
                    # Fake Win32 X describes the painted draft cursor, not the buffer during input processing.
                    await draft_painted.wait()
                    cursor = broker.buffer.cursor_position
                    for columns in (40, 56, 36):
                        draft_painted.clear()
                        output.up = 0
                        if columns == 36:
                            output.cursor_x = 0  # Unmatched host geometry leaves the ordinary renderer in charge.
                        output.columns = columns
                        broker.app.invalidate()
                        if owned:
                            await asyncio.sleep(.03)  # Keep the resize events in the same debounce window.
                        else:
                            await draft_painted.wait()
                if owned:
                    await asyncio.sleep(.3)
                assert broker.buffer.text == "queued draft" and broker.buffer.cursor_position == cursor
                frame = "".join(output.parts)
                assert "completed history" in frame and "in-flight response" in frame
                assert ("\x1b[3J" in frame) is owned
                if owned:
                    assert frame.count("\x1b[3J") == 1
                    rebuilt = frame.split("\x1b[3J", 1)[1]
                    expected = ("startup display", "completed history", "notification between turns", "next completed answer")
                    assert all(rebuilt.count(item) == 1 for item in expected)
                    assert [rebuilt.index(item) for item in expected] == sorted(rebuilt.index(item) for item in expected)
                    await broker.replace_history([{"role": "assistant", "content": "replacement history"}])
                    rebuilt = "".join(output.parts).rsplit("\x1b[3J", 1)[1]
                    assert "replacement history" in rebuilt and all(item not in rebuilt for item in expected)
                    assert broker.buffer.text == "queued draft" and broker.buffer.cursor_position == cursor
                else:
                    # At 40 columns the previous 80-cell frame border becomes two physical rows.
                    # Two live rows and the border precede the draft cursor, so clear from four rows above it.
                    assert next(up for columns, up in output.erasures if columns == 40) == 4
                    assert next(up for columns, up in output.erasures if columns == 36) == 3
            finally:
                await broker.close()
    asyncio.run(scenario())


def test_source_background_same_reader_and_preserved_input() -> None:
    import asyncio

    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from ruocun.agent.input_broker import InputBroker
    from ruocun.tui.background import bgFromEnv
    assert bgFromEnv({"RUOCUN_THEME": "light", "COLORFGBG": "15;0"}) == "light"
    assert bgFromEnv({"RUOCUN_THEME": "dark", "COLORFGBG": "0;15"}) == "dark"
    assert [bgFromEnv({"COLORFGBG": value}) for value in ("0;15", "0;7", "15;0")] == ["light", "light", "dark"]
    assert bgFromEnv({}) is None
    async def scenario():
        with create_pipe_input() as pipe:
            class Output(DummyOutput):
                def write_raw(self, value):
                    if "\x1b]11;?\x07" in value:
                        asyncio.get_running_loop().call_soon(pipe.send_text, "\x1b]11;rgb:ffff/ffff/")
                        asyncio.get_running_loop().call_later(.01, pipe.send_text, "ffff\x07合成草稿")
            async def pause():
                pass
            broker = InputBroker(on_pause=pause, input=pipe, output=Output())
            broker.configure_terminal({})
            await broker.start()
            try:
                assert broker.background == "light"
                async with asyncio.timeout(2):
                    while broker.buffer.text != "合成草稿":
                        await asyncio.sleep(.01)
            finally:
                await broker.close()
    asyncio.run(scenario())
