"""D06单输入owner链的必要TTY产品接缝；不是真实stdin pipe/Terminal体验验收。"""

import asyncio

from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from ruocun.agent import input_broker
from ruocun.agent.input_broker import InputBroker


async def until(predicate):
    async with asyncio.timeout(5):
        while not predicate():
            await asyncio.sleep(0.01)


class RecordingOutput(DummyOutput):
    def __init__(self):
        self.parts = []

    def write(self, text):
        self.parts.append(text)


def test_actual_input_chain_paste_is_not_submission_and_output_keeps_draft():
    # 复用D06 actual_prompt_input_chain_paste_is_not_submit_and_stream_keeps_draft。
    async def scenario():
        async def pause():
            pass

        with create_pipe_input() as pipe:
            output = RecordingOutput()
            broker = InputBroker(on_pause=pause, input=pipe, output=output)
            await broker.start()
            waiting = asyncio.create_task(broker.next_submission())
            pipe.send_text("\x1b[200~第一行\r\n第二行\x1b[201~")
            await until(lambda: broker.buffer.text == "第一行\n第二行")
            assert not waiting.done()
            pipe.send_text("\r")
            assert await waiting == "第一行\n第二行"
            pipe.send_text("新草稿中🙂\x1b[D")
            await until(lambda: broker.buffer.text == "新草稿中🙂")
            cursor = broker.buffer.cursor_position
            await broker.write("合成模型输出", end="")
            assert "合成模型输出" in "".join(output.parts)
            assert broker.buffer.text == "新草稿中🙂"
            assert broker.buffer.cursor_position == cursor
            await broker.close()
            assert not broker.app.is_running and not pipe.closed
            assert await broker.next_submission() is None
    asyncio.run(scenario())


def test_pause_keeps_draft_and_close_releases_owned_input_and_pending_waiters(monkeypatch):
    # D06 Esc保草稿及退出清理职责；使用受控Input，不声称真实Windows Terminal验收。
    async def scenario():
        paused = asyncio.Event()

        async def pause():
            paused.set()

        with create_pipe_input() as pipe:
            monkeypatch.setattr(input_broker, "create_input", lambda: pipe)
            monkeypatch.setattr(input_broker, "create_output", DummyOutput)
            broker = InputBroker(on_pause=pause)
            await broker.start()
            waiting = asyncio.create_task(broker.next_submission())
            pipe.send_text("暂停时保留草稿\x1b")
            async with asyncio.timeout(5):
                await paused.wait()
            assert broker.buffer.text == "暂停时保留草稿" and not waiting.done()
            answering = asyncio.create_task(broker.ask_approval("关闭时拒绝未完成审批"))
            await until(lambda: broker.app.layout.current_buffer is not broker.buffer)
            await broker.close()
            assert await answering == "" and await waiting is None
            assert pipe.closed and not broker.app.is_running
            await broker.close()
    asyncio.run(scenario())


def test_approval_uses_same_input_owner_and_restores_main_draft_after_answer():
    # D06模态优先及独立草稿；审批原文交权限层，不能混成新用户消息。
    async def scenario():
        pauses = []

        async def pause():
            pauses.append(True)

        with create_pipe_input() as pipe:
            broker = InputBroker(on_pause=pause, input=pipe, output=DummyOutput())
            await broker.start()
            waiting = asyncio.create_task(broker.next_submission())
            pipe.send_text("正在编辑🙂\x1b[D")
            await until(lambda: broker.buffer.text == "正在编辑🙂")
            cursor = broker.buffer.cursor_position
            answering = asyncio.create_task(broker.ask_approval("合成审批 [once/session/always]"))
            await until(lambda: broker.app.layout.current_buffer is not broker.buffer)
            cancelled = asyncio.Event()
            queued = asyncio.create_task(broker.ask_approval("过期审批不应出现", cancelled=cancelled.is_set))
            await asyncio.sleep(0)
            cancelled.set()
            broker.restore_submission("持久化未接纳的原指令")
            pipe.send_text(" session \r")
            assert await answering == " session "
            await until(lambda: queued.done() or broker.app.layout.current_buffer is not broker.buffer)
            assert queued.done() and await queued == ""
            assert not waiting.done() and pauses == []
            assert broker.app.layout.current_buffer is broker.buffer
            assert broker.buffer.text == "持久化未接纳的原指令\n正在编辑🙂"
            assert broker.buffer.cursor_position == len("持久化未接纳的原指令\n") + cursor
            answering = asyncio.create_task(broker.ask_approval("第二次合成审批"))
            await until(lambda: broker.app.layout.current_buffer is not broker.buffer)
            pipe.send_text("\x03")
            assert await answering == "" and pauses == []
            assert not waiting.done()
            selecting = asyncio.create_task(broker.ask_selection("Enter保留空回答"))
            await until(lambda: broker.app.layout.current_buffer is not broker.buffer)
            pipe.send_text("\r")
            assert await selecting == ""
            selecting = asyncio.create_task(broker.ask_selection("Esc关闭选择"))
            await until(lambda: broker.app.layout.current_buffer is not broker.buffer)
            pipe.send_text("\x1b")
            assert await selecting is None
            assert not waiting.done() and pauses == []
            await broker.close()
            assert await waiting is None
    asyncio.run(scenario())
