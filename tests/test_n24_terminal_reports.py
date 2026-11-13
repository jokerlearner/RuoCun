"""D06 protocol既有断言迁入产品适配。"""

import asyncio
from types import SimpleNamespace

from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from ruocun.agent.input_broker import InputBroker
from ruocun.tui import terminal_reports
from ruocun.tui.terminal_reports import END, START, ParserGate, Reports


def test_fragmented_reports_focus_and_paste_are_separated():
    events = []
    reports = Reports(lambda kind, **data: events.append((kind, data)))
    reports.begin("probe", 0)
    assert reports.feed(b"\xe9\xb2", 0) == ""
    assert reports.feed(b"\xb8\x1b", .1) == "鲸"
    assert reports.feed("[?65;4c\x1b[6;20;", .2) == ""
    assert reports.feed("10t\x1b[O\x1b[I", .3) == ""
    assert reports.result == {"cell_width": 10, "cell_height": 20}
    assert [data["focused"] for kind, data in events if kind == "focus"] == [False, True]
    assert reports.feed("\x1b[24;1R键", 1) == "键"
    assert reports.feed("\x1b[1;5R", 3) == "\x1b[1;5R"
    assert reports.feed("\x1b[200", 4) == ""
    assert reports.feed("~hello\x1b[6;20;10t\n\x1b[20", 4.1) == ""
    assert reports.feed("1~", 4.2) == "\x1b[200~hello\x1b[6;20;10t\n\x1b[201~"
    reports.feed("\x1b", 5)
    assert reports.expire(5.081) == "\x1b"
    reports.begin("probe", 6)
    reports.feed("\x1b[?65;", 6)
    assert reports.expire(8.01) == ""
    assert reports.pending == ""


def test_product_query_returns_cpr_to_ptk_without_forwarding_unsolicited_reply():
    # 产品ptk自身CPR定位必须保留，不用D06图形query取代其输入owner。
    pending = [True]
    reports = Reports(lambda *args, **kwargs: None, cpr_pending=lambda: pending[0])
    assert reports.feed("\x1b[24;1R", 0) == "\x1b[24;1R"
    pending[0] = False
    assert reports.feed("\x1b[24;1R", .1) == ""


def test_win32_surrogate_pair_reaches_parser_as_one_character_across_reads():
    forwarded = []
    parser = SimpleNamespace(feed=forwarded.append, flush=lambda: None)
    source = SimpleNamespace(vt100_parser=parser)
    gate = ParserGate(source, Reports(lambda *_args, **_kwargs: None), lambda: 0)
    gate.feed("验收\ud83d")
    gate.flush()
    assert "".join(forwarded) == "验收"
    gate.feed("\ude42\r")
    assert "".join(forwarded) == "验收🙂\r"
    gate.restore()
    assert source.vt100_parser is parser


def test_actual_product_reader_filters_reports_and_restores_original_parser():
    async def scenario():
        async def pause():
            pass

        with create_pipe_input() as pipe:
            original = pipe.vt100_parser
            broker = InputBroker(on_pause=pause, input=pipe, output=DummyOutput())
            await broker.start()
            waiting = asyncio.create_task(broker.next_submission())
            pipe.send_text("\x1b[O\x1b[I\x1b[?65;4c\x1b[6;20;10t实际输入\r")
            assert await waiting == "实际输入"
            pipe.send_text("\x1b[200~文本\x1b[6;20;10t\x1b[201~\r")
            assert await broker.next_submission() == "文本\x1b[6;20;10t"
            await broker.close()
            assert pipe.vt100_parser is original
    asyncio.run(scenario())


def test_unclosed_paste_is_bounded_and_rejected_without_replaying_control_keys():
    # D10要求18登记有界资源，并保留D06的1MiB样本可接纳。
    events = []
    reports = Reports(lambda kind, **data: events.append((kind, data)))
    megabyte = "a" * (1024 * 1024)
    assert reports.feed(START + megabyte, 0) == ""
    assert reports.feed(END, 1) == START + megabyte + END
    # 8MiB正文边界（含多字节emoji），结束标记未到时不能交ptk。
    accepted = "🙂" * (2 * 1024 * 1024)
    assert reports.feed(START + accepted, 2) == ""
    assert reports.feed(END, 3) == START + accepted + END
    # 同次feed跨限时整段拒收，随后的Enter/Esc仍属paste数据。
    assert reports.feed(START + megabyte * 8 + "🙂\r\x1b", 4) == ""
    assert events[-1] == ("paste-rejected", {"limit_bytes": 8 * 1024 * 1024})
    assert reports.feed("\r/exit\r\x1b[20", 5) == ""
    assert reports.feed("1~正常输入", 6) == "正常输入"
    assert reports.feed(START + "恢复粘贴" + END, 7) == START + "恢复粘贴" + END


def test_rejected_paste_keeps_product_draft_and_displays_reason(monkeypatch):
    # 缩小相同公开上限以定向确认真实输入owner的拒收反馈和草稿，真实8MiB边界见上例。
    monkeypatch.setattr(terminal_reports, "PASTE_LIMIT_BYTES", 32)

    class Output(DummyOutput):
        def __init__(self):
            self.parts = []

        def write(self, text):
            self.parts.append(text)

    async def scenario():
        async def pause():
            raise AssertionError("拒收paste不能执行其中的Esc")

        async def until(predicate):
            async with asyncio.timeout(5):
                while not predicate():
                    await asyncio.sleep(.01)

        with create_pipe_input() as pipe:
            output = Output()
            broker = InputBroker(on_pause=pause, input=pipe, output=output)
            await broker.start()
            waiting = asyncio.create_task(broker.next_submission())
            pipe.send_text("原草稿")
            await until(lambda: broker.buffer.text == "原草稿")
            pipe.send_text(START + "x" * 33 + "\r\x1b/exit\r")
            await until(lambda: "已整段拒收" in "".join(output.parts))
            assert broker.buffer.text == "原草稿" and not waiting.done()
            pipe.send_text(END + "\r")
            assert await waiting == "原草稿"
            await broker.close()
    asyncio.run(scenario())
