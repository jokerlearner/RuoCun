"""冻结tab_attention/NotifyUser语义，桌面分支按W6排除。"""

import asyncio

import pytest


def test_source_tab_attention_lifecycle_and_dedup():
    from ruocun.tui.tab_attention import createTabAttention
    writes = []
    tab = createTabAttention("dao · 项目", write=writes.append, isTTY=True, env={})
    assert "".join(writes) == "\x1b[22;0t\x1b]0;dao · 项目\x1b\\\x1b[?1004h"
    writes.clear()
    tab.mark()
    tab.mark()
    assert writes == ["\x1b]0;🟡 dao · 项目\x1b\\"]
    tab.clear()
    tab.clear()
    assert writes[-1] == "\x1b]0;dao · 项目\x1b\\"
    tab.mark()
    writes.clear()
    tab.dispose()
    tab.dispose()
    tab.mark()
    tab.clear()
    assert "".join(writes) == "\x1b]0;dao · 项目\x1b\\\x1b[?1004l\x1b[23;0t"


@pytest.mark.parametrize("tty,env", [(False, {}), (True, {"TERM": "dumb"})])
def test_source_non_tty_attention_no_controls(tty, env):
    from ruocun.tui.tab_attention import createTabAttention
    writes = []
    tab = createTabAttention("dao", write=writes.append, isTTY=tty, env=env)
    tab.mark()
    tab.clear()
    tab.dispose()
    assert writes == []


def test_source_tab_title_sanitizing_and_completed_color():
    from ruocun.tui.tab_attention import createTabAttention, formatTabTitle
    writes = []
    tab = createTabAttention("dao\x07\n\x1b\x9c", write=writes.append, isTTY=True, env={})
    tab.mark()
    assert writes[-1] == "\x1b]0;🟡 dao\x1b\\"
    tab.mark("completed")
    tab.setTitle("修复登录 · 项目")
    assert writes[-1] == "\x1b]0;🟢 修复登录 · 项目\x1b\\"
    count = len(writes)
    tab.setTitle("修复登录 · 项目")
    tab.mark("completed")
    assert len(writes) == count
    tab.setTitle("\x1b\x07手动标题\n项目")
    tab.clear()
    assert writes[-1] == "\x1b]0;手动标题 项目\x1b\\"
    tab.dispose()
    writes.clear()
    tab.setTitle("退出后")
    assert writes == []
    assert formatTabTitle("/a/dao-code") == "若存 Code"
    assert formatTabTitle("/a/dao-code", "修复登录超时") == "修复登录超时 · 若存 Code"
    assert formatTabTitle("/a", "若存 Code") == "若存 Code"
    assert formatTabTitle("/a", "修复\n\t登录\x1b\x07") == "修复 登录 · 若存 Code"
    assert formatTabTitle("/a", "🟢" * 25) == "🟢" * 24 + "… · 若存 Code"


def test_source_notify_user_callback_and_w6_channel():
    from ruocun.tools.notify_user import notifyUserTool
    from ruocun.tools.types import ToolContext
    sent = []
    ctx = ToolContext("/synthetic", notifyUser=sent.append)
    result = asyncio.run(notifyUserTool.handler({"message": "需要你尽快看看"}, ctx))
    assert sent == ["需要你尽快看看"] and "终端" in result and "未发送桌面" in result
    ctx.notifyUser = None
    result = asyncio.run(notifyUserTool.handler({"message": "x"}, ctx))
    assert "不支持" in result and "未发送桌面" in result


def test_source_no_notify_and_best_effort_terminal_only():
    from ruocun.tui.notifier import notify
    sent = []
    assert not notify("t", "m", write=sent.append, env={"RUOCUN_NO_NOTIFY": "1"})
    assert sent == []
    assert notify("t\x1b[2J", "m\x07\x9b2J\x9d0;synthetic\x9c", write=sent.append, env={})
    assert not any(ord(char) < 32 and char not in "\n\t" or 127 <= ord(char) <= 159 for char in sent[-1])
    def unavailable(value):
        raise OSError("synthetic terminal unavailable")
    assert not notify("t", "m", write=unavailable, env={})


def test_source_focus_and_user_input_clear_title_same_owner_and_failure_is_secondary():
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from ruocun.agent.input_broker import InputBroker
    class Output(DummyOutput):
        def __init__(self):
            self.raw = []
            self.fail = False
        def write_raw(self, value):
            if self.fail and "\x1b]0;" in value:
                raise OSError("synthetic title sink unavailable")
            self.raw.append(value)
        def write(self, value):
            if self.fail and "synthetic notification" in value:
                raise OSError("synthetic notification sink unavailable")
    async def scenario():
        async def pause():
            pass
        async def until(check):
            async with asyncio.timeout(3):
                while not check():
                    await asyncio.sleep(.01)
        with create_pipe_input() as pipe:
            out = Output()
            broker = InputBroker(on_pause=pause, input=pipe, output=out)
            broker.configure_terminal({"RUOCUN_THEME": "dark"})
            broker.set_tab_name("合成任务")
            await broker.start()
            try:
                broker.mark_attention("completed")
                await broker.drain_render()
                assert "\x1b]0;🟢 合成任务 · 若存 Code\x1b\\" in out.raw
                pipe.send_text("\x1b[I")
                await until(lambda: out.raw[-1] == "\x1b]0;合成任务 · 若存 Code\x1b\\")
                broker.mark_attention()
                await broker.drain_render()
                pipe.send_text("保留草稿🙂")
                await until(lambda: broker.buffer.text == "保留草稿🙂")
                await broker.drain_render()
                assert out.raw[-1] == "\x1b]0;合成任务 · 若存 Code\x1b\\"
                out.fail = True
                broker.mark_attention()
                broker.post_notification("synthetic notification\x1b[2J")
                await broker.drain_render()
                assert broker.app.is_running and broker.buffer.text == "保留草稿🙂"
                assert broker._render_error is None
            finally:
                out.fail = False
                await broker.close()
            assert "\x1b[?1004l\x1b[23;0t" in out.raw
    asyncio.run(scenario())
