"""冻结 App.tsx 与 D06 输入链语义的产品迁移，受控TTY不代表实机体验。"""

import asyncio

from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from ruocun.agent import input_broker
from ruocun.agent.input_broker import InputBroker


async def until(predicate):
    async with asyncio.timeout(5):
        while not predicate():
            await asyncio.sleep(.01)


def test_paste_utf16_and_seven_line_fold_expand_only_on_enter():
    # App.tsx:1346-1357，以及D06 280/281 UTF16边界。
    async def scenario():
        async def pause():
            pass

        with create_pipe_input() as pipe:
            broker = InputBroker(on_pause=pause, input=pipe, output=DummyOutput())
            await broker.start()
            waiting = asyncio.create_task(broker.next_submission())
            pipe.send_text("\x1b[200~" + "🙂" * 140 + "\x1b[201~")
            await until(lambda: broker.buffer.text == "🙂" * 140)
            assert not waiting.done()
            pipe.send_text("\r")
            assert await waiting == "🙂" * 140
            for content in ["🙂" * 140 + "中", "一\r二\r三\r四\r五\r六\r七\r"]:
                waiting = asyncio.create_task(broker.next_submission())
                pipe.send_text("\x1b[200~" + content + "\x1b[201~")
                await until(lambda: broker.buffer.text.startswith("[粘贴#"))
                assert not waiting.done()
                pipe.send_text("\r")
                assert await waiting == content.replace("\r", "\n")
            await broker.close()
    asyncio.run(scenario())


def test_control_c_arms_two_second_exit_and_modal_escape_keeps_draft(monkeypatch):
    # App.tsx:1121-1125；D06模态优先。
    async def scenario():
        async def pause():
            raise AssertionError("Ctrl+C退出不能转成暂停")

        now = [0.0]
        monkeypatch.setattr(input_broker, "monotonic", lambda: now[0])
        with create_pipe_input() as pipe:
            broker = InputBroker(on_pause=pause, input=pipe, output=DummyOutput())
            await broker.start()
            pipe.send_text("草稿")
            await until(lambda: broker.buffer.text == "草稿")
            waiting = asyncio.create_task(broker.next_submission())
            pipe.send_text("\x03")
            await asyncio.sleep(.05)
            assert not waiting.done()
            now[0] = 2.1
            pipe.send_text("\x03")
            await asyncio.sleep(.05)
            assert not waiting.done()
            now[0] = 3.0
            pipe.send_text("\x03")
            assert await waiting is None
            assert broker.buffer.text == "草稿"
            await broker.close()
    asyncio.run(scenario())


def test_unicode_cursor_and_delete_use_complete_graphemes():
    # D10对既有Unicode平台路线的必要修正，覆盖组合字、旗帜与ZWJ。
    async def scenario():
        async def pause():
            pass

        with create_pipe_input() as pipe:
            broker = InputBroker(on_pause=pause, input=pipe, output=DummyOutput())
            await broker.start()
            pipe.send_text("é🇨🇳👨‍👩‍👧‍👦")
            await until(lambda: broker.buffer.text == "é🇨🇳👨‍👩‍👧‍👦")
            pipe.send_text("\x1b[D")
            await until(lambda: broker.buffer.cursor_position == len("é🇨🇳"))
            pipe.send_text("\x7f")
            await until(lambda: broker.buffer.text == "é👨‍👩‍👧‍👦")
            pipe.send_text("\x1b[3~")
            await until(lambda: broker.buffer.text == "é")
            pipe.send_text("\x7f")
            await until(lambda: broker.buffer.text == "")
            await broker.close()
    asyncio.run(scenario())


def test_escape_prioritizes_modal_and_keeps_draft_then_restores_last_submission():
    # App.test.tsx 中ESC先清队列、空输入回填及Down清空既有断言。
    async def scenario():
        calls = []

        async def pause():
            raise AssertionError("已配置回调时应交给调度器")

        async def escape():
            calls.append(True)
            return len(calls) > 1

        with create_pipe_input() as pipe:
            broker = InputBroker(on_pause=pause, input=pipe, output=DummyOutput())
            broker.on_escape = escape
            await broker.start()
            pipe.send_text("原指令\r")
            assert await broker.next_submission() == "原指令"
            pipe.send_text("新草稿")
            await until(lambda: broker.buffer.text == "新草稿")
            answer = asyncio.create_task(broker.ask_selection("合成模态"))
            await until(lambda: broker.app.layout.current_buffer is not broker.buffer)
            pipe.send_text("\x1b")
            assert await answer is None
            assert calls == [] and broker.buffer.text == "新草稿"
            pipe.send_text("\x1b")
            await until(lambda: len(calls) == 1)
            assert broker.buffer.text == "新草稿"
            pipe.send_text("\x15\x1b")
            await until(lambda: broker.buffer.text == "原指令")
            pipe.send_text("\x1b[B")
            await until(lambda: broker.buffer.text == "")
            await broker.close()
    asyncio.run(scenario())
