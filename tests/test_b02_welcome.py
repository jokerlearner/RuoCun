"""冻结 Welcome/banner/maxim/taiji/mascot 的来源语义，不替代实际图形体验。"""

import asyncio
import re

import pytest


@pytest.fixture(autouse=True)
def _chinese():
    from ruocun.i18n.i18n import setLang
    setLang("zh")
    yield
    setLang("en")


def _info():
    return {"model": "deepseek-v4-pro", "thinking": "max", "cwd": "D:\\synthetic\\project",
            "version": "0.2.0", "branch": "main"}


def test_source_welcome_layout_and_real_card_anchor():
    from ruocun.tui.capabilities import Capabilities
    from ruocun.tui.welcome import Welcome, getWelcomeLayout
    assert getWelcomeLayout(209, {"columns": 26, "rows": 13}) == {
        "cardWidth": 146, "cardLeft": 31, "imageColumns": 26, "imageLeft": 34,
        "imageTop": 2, "cardHeight": 17, "imageRows": 13, "sideBySide": True}
    assert getWelcomeLayout(120, {"columns": 32, "rows": 16})["cardHeight"] == 20
    for mascot in (None, {"columns": 26, "rows": 13}, {"columns": 0, "rows": 0}, {"columns": float("nan"), "rows": 13}):
        assert not getWelcomeLayout(80, mascot)["sideBySide"]
        assert getWelcomeLayout(80, mascot)["cardHeight"] == 0
    rows = Welcome(_info(), Capabilities("none", True, 209), mascot={"columns": 26, "rows": 13}).splitlines()
    assert len(rows) == 17 and rows[0].index("╭") == 31
    assert rows[3].index("若存 Code") == 65
    assert "绵绵若存，用之不勤。" in rows[5]
    assert "deepseek-v4-pro" in rows[8] and "synthetic" in rows[9]
    assert all("main" not in row and "0.2.0" not in row for row in rows)
    assert "快速开始" in rows[13]


def test_source_footer_brand_workspace_and_light_text():
    from ruocun.i18n.i18n import setLang
    from ruocun.tui.capabilities import Capabilities
    from ruocun.tui.welcome import Welcome
    setLang("zh")
    try:
        caps = Capabilities("none", True, 80)
        out = Welcome(_info(), caps)
        assert all(x in out for x in ("快速开始", "若存 Code", "绵绵若存，用之不勤。", "synthetic"))
        assert all(x not in out for x in ("DAO CODE", "上善若水", "0.2.0", "main"))
        assert "快速开始" not in Welcome(_info(), caps, skipFooter=True)
        light = Welcome(_info(), Capabilities("none", True, 120), bg="light", mascot={"columns": 26, "rows": 13})
        assert len(light.splitlines()) < 17 and "\x1b" not in light
    finally:
        setLang("en")


def test_source_maxim_rng_and_banner_capabilities():
    from ruocun.data.laozi_maxims import MAXIMS
    from ruocun.tui.banner import buildWelcome
    from ruocun.tui.capabilities import Capabilities
    from ruocun.tui.maxim import randomMaxim
    assert randomMaxim(lambda: 0) == MAXIMS[0]
    assert randomMaxim(lambda: .999999) == MAXIMS[-1]
    assert randomMaxim() in MAXIMS
    out = buildWelcome(_info(), Capabilities("none", True, 80), lambda: 0)
    assert all(x in out for x in ("若存 Code", MAXIMS[0]["text"], "deepseek-v4-pro", "0.2.0", "1M 上下文", "main", "/help", "Esc"))
    assert "DAO CODE" not in out
    assert "老子" not in out and "\x1b" not in out
    assert "\x1b[38;2;" in buildWelcome(_info(), Capabilities("truecolor", True, 80), lambda: 0)
    assert "⎇" not in buildWelcome({k: v for k, v in _info().items() if k != "branch"}, Capabilities("none", True, 80))


def test_source_taiji_background_only_and_width():
    from ruocun.tui.capabilities import Capabilities
    from ruocun.tui.taiji import TAIJI_WIDTH, renderTaiji
    def caps(tier):
        return Capabilities(tier, True, 120)
    for tier in ("truecolor", "ansi256", "none", "ansi16"):
        lines = renderTaiji(caps(tier))
        visible = [re.sub(r"\x1b\[[0-9;]*m", "", line) for line in lines]
        assert TAIJI_WIDTH(caps(tier)) == max(map(len, visible))
        if tier in {"none", "ansi16"}:
            assert "\x1b" not in "".join(lines)
        else:
            assert len(lines) == 8 and not "".join(visible).strip()
            assert ("\x1b[48;2;" if tier == "truecolor" else "\x1b[48;5;") in "".join(lines)
            assert "\x1b[38;2;" not in "".join(lines)
    assert renderTaiji(caps("truecolor"), "dark") != renderTaiji(caps("truecolor"), "light")


def test_source_motion_policy_and_anchors():
    from ruocun.tui.mascot import imageAnchor, motionPauseReason
    state = {"epoch": 0, "home": True, "inputEmpty": True, "busy": False, "modalOpen": False,
             "backgroundRunning": False, "enabled": True, "dynamicRows": 4, "extraStaticRows": 0}
    assert motionPauseReason(None, True, False) == "disabled"
    assert motionPauseReason(state, True, False) == "idle"
    for changes, expected in (({"enabled": False}, "disabled"), ({"home": False}, "history"),
                              ({"inputEmpty": False}, "input"), ({"busy": True}, "task"),
                              ({"backgroundRunning": True}, "task"), ({"modalOpen": True}, "modal")):
        assert motionPauseReason({**state, **changes}, True, False) == expected
    assert motionPauseReason(state, False, False) == "focus"
    assert motionPauseReason(state, True, True) == "resize"
    mascot = {"columns": 26, "rows": 13}
    assert imageAnchor(22, 4, 0, 120, 40, mascot) == {"row": 3, "column": 4}
    assert imageAnchor(22, 4, 0, 120, 40, mascot, require_top=True) == {"row": 3, "column": 4}
    assert imageAnchor(23, 4, 0, 120, 40, mascot, require_top=True) is None
    assert imageAnchor(26, 4, 2, 200, 40, mascot) == {"row": 5, "column": 31}
    for args in ((21, 4, 0, 120, 40), (22, 0, 0, 120, 40), (22, 4, 0, 80, 40), (40, 4, 0, 120, 30)):
        assert imageAnchor(*args, mascot) is None


def test_source_motion_single_pending_frame_pause_reset_and_disposal():
    from ruocun.tui.mascot import createWelcomeMotion
    async def scenario():
        writes, pending = [], asyncio.Event()
        class Reports:
            async def cursor(self):
                return {"row": 22, "column": 1}
            async def probe(self):
                return {"cell_width": 10, "cell_height": 20}
        async def write(text, valid):
            writes.append(text)
            await pending.wait()
            return valid()
        async def flush():
            pass
        state = {"epoch": 0, "home": True, "inputEmpty": True, "busy": False, "modalOpen": False,
                 "backgroundRunning": False, "enabled": True, "dynamicRows": 4, "extraStaticRows": 0}
        motion = createWelcomeMotion(reports=Reports(), write=write, dimensions=lambda: (120, 40),
                                     waitUntilRenderFlush=flush, cell={"cell_width": 10, "cell_height": 20})
        try:
            motion.update(state)
            await asyncio.sleep(.3)
            assert len(writes) == 1 and writes[0].startswith("\x1b7\x1b[3;4H\x1bP") and writes[0].endswith("\x1b8")
            await motion.advance()
            assert len(writes) == 1
            motion.update({**state, "busy": True})
            pending.set()
            await asyncio.sleep(.02)
            await motion.advance()
            assert len(writes) == 1
            assert await motion.reset() == {"columns": 26, "rows": 13}
            motion.update(state)
            await motion.advance()
            assert len(writes) == 1
            motion.update({**state, "epoch": 1})
            await motion.advance()
            assert len(writes) == 2
            motion.resized()
            motion.update({**state, "epoch": 1})
            await motion.advance()
            assert len(writes) == 2
        finally:
            await motion.dispose()
        motion.update({**state, "epoch": 2})
        await motion.advance()
        assert len(writes) == 2
    asyncio.run(scenario())


def test_source_actual_owner_probe_cursor_paste_and_resize_fallback():
    from prompt_toolkit.data_structures import Size
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import ColorDepth, DummyOutput

    from ruocun.agent.input_broker import InputBroker
    from ruocun.tui.mascot_frames import MASCOT_FRAMES
    async def scenario():
        async def pause():
            pass
        async def until(check):
            async with asyncio.timeout(4):
                while not check():
                    await asyncio.sleep(.01)
        with create_pipe_input() as pipe:
            class Output(DummyOutput):
                def __init__(self):
                    self.columns, self.raw, self.text = 80, [], []
                    self.rows = 24
                    self.cursor_row = 18
                    self.output_order = []
                def get_size(self):
                    return Size(rows=self.rows, columns=self.columns)
                def get_default_color_depth(self):
                    return ColorDepth.TRUE_COLOR
                def write(self, text):
                    self.text.append(text)
                    self.output_order.append(text)
                def write_raw(self, text):
                    self.raw.append(text)
                    self.output_order.append(text)
                    if text == "\x1b[c\x1b[16t":
                        for chunk in ("\x1b[?61;", "4;6;7;14;21;22;23;24;28;32;42c", "\x1b[6;20;10t"):
                            pipe.send_text(chunk)
                    elif text == "\x1b[6n":
                        # run_in_terminal已擦动态区；17行静态卡后的实测坐标。
                        pipe.send_text(f"\x1b[{self.cursor_row};1R")
            out = Output()
            broker = InputBroker(on_pause=pause, input=pipe, output=out)
            broker.configure_terminal({"RUOCUN_THEME": "dark", "WT_SESSION": "synthetic-wt"}, owned_viewport=True)
            await broker.start()
            try:
                await broker.show_welcome(_info())
                assert any(text.startswith("\x1b7\x1b[3;4H\x1bP") for text in out.raw), (
                    "The first native frame must be visible before startup can append session output."
                )
                waiting = asyncio.create_task(broker.next_submission())
                paste = "\x1b[200~草稿\x1b[?1;4c\x1b[6;20;10t\x1b[201~"
                pipe.send_text(paste)
                await until(lambda: "草稿" in broker.buffer.text)
                assert broker.buffer.text == "草稿\x1b[?1;4c\x1b[6;20;10t" and not waiting.done()
                first_narrow_write = len(out.text)
                out.columns = 64
                broker.app.invalidate()
                await until(lambda: broker._welcome_epoch == 1)
                written = "".join(out.text[first_narrow_write:])
                assert "若存" in written and any(block in written for block in "▞▚▙▟")
                assert "\x1b[38;2;" in broker._welcome_text()
                count = len([text for text in out.raw if text.startswith("\x1b7")])
                await asyncio.sleep(.3)
                assert count == len([text for text in out.raw if text.startswith("\x1b7")])
                assert broker.buffer.text.startswith("草稿") and not waiting.done()
                broker.set_theme("light")
                await until(lambda: broker._welcome_epoch == 2)
                out.columns = 120
                broker.app.invalidate()
                await until(lambda: broker._welcome_epoch == 3)
                assert count == len([text for text in out.raw if text.startswith("\x1b7")])
                broker.set_theme("dark")
                await until(lambda: broker._welcome_epoch == 4)
                try:
                    await until(lambda: count < len([text for text in out.raw if text.startswith("\x1b7")]))
                except TimeoutError:
                    raise AssertionError({"reason": broker._motion.reason, "layout": broker._motion.layout,
                                          "state": broker._motion._state, "anchor": broker._motion._anchor,
                                          "still": broker._motion._needs_still,
                                          "controls": [text for text in out.raw if len(text) < 20]}) from None
                count = len([text for text in out.raw if text.startswith("\x1b7")])
                await asyncio.sleep(.3)
                assert count == len([text for text in out.raw if text.startswith("\x1b7")])
                assert broker.buffer.text.startswith("草稿") and not waiting.done()
                await broker.write("合成普通提示")
                out.cursor_row = 19
                out.columns = 121
                broker.app.invalidate()
                await until(lambda: broker._welcome_epoch == 5)
                await until(lambda: count < len([text for text in out.raw if text.startswith("\x1b7")]))
                assert broker.buffer.text.startswith("草稿") and not waiting.done()

                for index in range(20):
                    await broker.write(f"terminal-history-{index}")
                for epoch, (columns, rows, image_column) in enumerate(((190, 42, 26), (96, 24, 4)), start=6):
                    start = len(out.output_order)
                    out.columns, out.rows = columns, rows
                    out.cursor_row = min(rows, 39)
                    broker.app.invalidate()
                    await until(lambda: broker._welcome_epoch == epoch)
                    replay = "".join(out.output_order[start:])
                    native = f"\x1b7\x1b[3;{image_column}H{MASCOT_FRAMES[0]}\x1b8"
                    assert native in replay, "A full history must not turn the native welcome image into character art."
                    assert replay.index("\x1b[3J") < replay.index("若存 Code") < replay.index(native) < replay.index("terminal-history-0")
                    assert "terminal-history-19" in replay
                    assert broker.buffer.text.startswith("草稿") and not waiting.done()
            finally:
                await broker.close()
            assert await waiting is None
            assert broker._queries._disposed and not broker.app.is_running
    asyncio.run(scenario())


def test_static_mascot_with_no_graphics_report():
    from ruocun.tui.capabilities import Capabilities
    from ruocun.tui.welcome import Welcome

    caps = Capabilities("truecolor", True, 80)
    for theme in ("dark", "light"):
        text = Welcome(_info(), caps, bg=theme, terminalRows=24)
        visible = re.sub(r"\x1b\[[0-9;]*m", "", text)
        assert any(block in visible for block in "▞▚▙▟") and "\x1b[38;2;" in text and "\x1bP" not in text
        assert max(sum(block in "▘▝▀▖▌▞▛▗▚▐▜▄▙▟█" for block in row) for row in visible.splitlines()) > 26
        assert "若存 Code" in visible and "快速开始" in visible and len(visible.splitlines()) <= 19


def test_input_uses_contrasting_colors_on_both_owned_input_surfaces():
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from ruocun.agent.input_broker import InputBroker

    async def pause():
        pass

    with create_pipe_input() as pipe:
        broker = InputBroker(on_pause=pause, input=pipe, output=DummyOutput())
        for theme, ink, panel in (("dark", "e1e8f0", "2d3745"), ("light", "192736", "e0e9f1")):
            broker.set_theme(theme)
            for control in (broker._control, broker._answer_control):
                window = next(window for window in broker.app.layout.find_all_windows() if window.content is control)
                attrs = broker.app.style.get_attrs_for_style_str(window.style)
                assert (attrs.color, attrs.bgcolor) == (ink, panel)
