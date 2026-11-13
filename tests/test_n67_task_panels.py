"""Source Ctrl+T/G/B cases on the one interactive input owner."""

import asyncio

from prompt_toolkit.data_structures import Size
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from ruocun.agent.input_broker import InputBroker
from ruocun.agent.tasks import BgTask


def test_source_panels_read_live_tasks_and_history_without_touching_the_draft():
    class Output(DummyOutput):
        def __init__(self):
            self.text = []

        def get_size(self):
            return Size(rows=35, columns=100)

        def write(self, data):
            self.text.append(data)

    async def scenario():
        async def until(check):
            async with asyncio.timeout(4):
                while not check():
                    await asyncio.sleep(.01)

        paused, converted = [], []

        async def pause():
            paused.append(True)

        async def convert():
            converted.append(True)
            return 2

        task = BgTask("agent-review", "run-1", "agent", "Review docs", "running")
        failed = BgTask("agent-second", "run-2", "agent", "Follow-up", "failed", error="round limit reached")
        manual = BgTask("task-manual", "run-3", "manual", "manual-only-row", "running")
        with create_pipe_input() as pipe:
            output = Output()
            broker = InputBroker(on_pause=pause, input=pipe, output=output)
            broker.configure_terminal({"RUOCUN_THEME": "dark", "NO_COLOR": "1"})
            broker.set_language("zh")
            broker.configure_panels(tasks=lambda: [task, failed, manual])
            broker.on_background = convert
            await broker.start()
            try:
                pipe.send_text("\x02")
                await asyncio.sleep(.12)
                assert not converted
                broker.set_status("running", 0)
                pipe.send_text("草稿🙂")
                await until(lambda: broker.buffer.text == "草稿🙂")
                pipe.send_text("\x14")
                await until(lambda: "子 agent 执行情况" in "".join(output.text))
                assert "agent-review" in "".join(output.text) and "manual-only-row" not in "".join(output.text)
                task.messages.append({"role": "assistant", "tool_calls": [{"function": {"name": "Read", "arguments": "README.md"}}]})
                await until(lambda: "Read README.md" in "".join(output.text))
                pipe.send_text("\x1b[B")
                await until(lambda: "round limit reached" in "".join(output.text))
                pipe.send_text("\r\x1b")
                await asyncio.sleep(.25)
                assert not paused and broker.buffer.text == "草稿🙂"
                broker.emit_event("user_message", text="Earlier question")
                broker.emit_event("assistant_done", message={"content": "Earlier answer"})
                broker.emit_event("user_message", text="Latest question")
                await broker.drain_render()
                pipe.send_text("\x07")
                await until(lambda: "❯ 2. Latest question" in "".join(output.text))
                pipe.send_text("\x1b[A\r")
                await until(lambda: "回看历史对话" in "".join(output.text))
                pipe.send_text("\x1b")
                await asyncio.sleep(.25)
                assert not paused and broker.buffer.text == "草稿🙂"
                pipe.send_text("\x02")
                await until(lambda: "已将 2 个前台调用转为后台" in "".join(output.text))
                assert len(converted) == 1
            finally:
                await broker.close()

    asyncio.run(scenario())
