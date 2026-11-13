"""冻结auth_wizard/App/multi_select的公开交互seam；仅合成凭据和ptk。"""

import asyncio

import pytest


@pytest.mark.parametrize("answers,prefer,invalid", [(["synthetic-good"], True, False), (["synthetic-bad", "synthetic-good"], False, True), ([""], True, False)])
def test_source_key_wizard(answers, prefer, invalid):
    from ruocun.config.auth_wizard import WizardDeps, runKeyWizard
    from ruocun.config.credential import MemoryKeychain
    from ruocun.config.profiles import DEFAULTS
    from ruocun.i18n.i18n import setLang
    setLang("zh")
    replies, writes, calls = iter(answers), [], []
    async def ask(prompt):
        return next(replies, "")
    async def validate(credential):
        calls.append(credential)
        return {"ok": False, "reason": "invalid"} if invalid and len(calls) == 1 else {"ok": True}
    result = asyncio.run(runKeyWizard(WizardDeps(
        cfg={"version": 2, "activeProfile": "default", "profiles": {}}, name="default",
        meta={"provider": "deepseek", **DEFAULTS["deepseek"]}, ask=ask, write=writes.append,
        validate=validate, kc=MemoryKeychain(), preferKeychain=prefer)))
    if answers == [""]:
        assert result is None and not calls
    else:
        assert result["resolved"]["key"] == "synthetic-good"
        assert ("key" not in result["cfg"]["profiles"]["default"]) is prefer
        if invalid:
            assert len(calls) == 2 and "无效" in "".join(writes)
    setLang("en")


def test_source_select_wrap_and_initial():
    from ruocun.tui.onboarding.select import Select
    view = Select([{"label": "中文", "value": "zh"}, {"label": "English", "value": "en"}], initialIndex=0)
    assert view.value == "zh"
    view.move(-1)
    assert view.value == "en"
    view.move(1)
    assert view.value == "zh"
    assert Select([{"label": "A", "value": "a"}], initialIndex=9).value == "a"


async def _with_broker(action):
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from ruocun.agent.input_broker import InputBroker
    class Output(DummyOutput):
        def __init__(self):
            self.parts = []
        def write(self, text):
            self.parts.append(text)
    async def pause():
        pass
    with create_pipe_input() as pipe:
        out = Output()
        broker = InputBroker(on_pause=pause, input=pipe, output=out)
        broker.configure_terminal({"RUOCUN_THEME": "dark"})
        broker.set_language("zh")
        await broker.start()
        async def until(predicate):
            async with asyncio.timeout(2):
                while not predicate():
                    await asyncio.sleep(.01)
        try:
            await action(broker, pipe, out, until)
        finally:
            await broker.close()


def test_source_choice_multi_fill_and_single():
    async def scenario(broker, pipe, out, until):
        multi = asyncio.create_task(broker.ask_choice("选哪些?", ["A", "B", "C"], True))
        await until(lambda: "选哪些?" in "".join(out.parts))
        pipe.send_text("\r\x1b[B ")
        await until(lambda: "[x] B" in "".join(out.parts))
        assert not multi.done()
        pipe.send_text("\x1b[B\x1b[B\r")
        assert await multi == "A, B"
        single = asyncio.create_task(broker.ask_choice("选一个", ["甲", "乙"]))
        await until(lambda: "选一个" in "".join(out.parts))
        pipe.send_text("\x1b[B\r")
        assert await single == "乙"
        fill = asyncio.create_task(broker.ask_choice("自己填写", ["甲", "乙"]))
        await until(lambda: "自己填写" in "".join(out.parts))
        pipe.send_text("\x1b[B\x1b[B我的想法\r")
        assert await fill == "我的想法"
    asyncio.run(_with_broker(scenario))


def test_source_approval_queue_dangerous_and_modal_focus():
    async def scenario(broker, pipe, out, until):
        pipe.send_text("原草稿")
        await until(lambda: broker.buffer.text == "原草稿")
        first = asyncio.create_task(broker.approval_prompt([{"id": "a", "toolName": "Write", "capability": "write", "summary": "Write a.txt"}]))
        second = asyncio.create_task(broker.approval_prompt([{"id": "b", "toolName": "Bash", "capability": "execute", "summary": "dangerous", "dangerous": True}]))
        await until(lambda: "Write a.txt" in "".join(out.parts))
        pipe.send_text("a\r")
        assert await first == {"a": "always"}
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(broker.next_submission(), .02)
        await until(lambda: "dangerous" in "".join(out.parts))
        pipe.send_text("a")
        await asyncio.sleep(.03)
        assert not second.done()
        pipe.send_text("y")
        assert await second == {"b": "once"}
        assert broker.buffer.text == "原草稿"
        third = asyncio.create_task(broker.approval_prompt([{"id": "c", "toolName": "Write", "capability": "write", "summary": "cancel-one"}]))
        fourth = asyncio.create_task(broker.approval_prompt([{"id": "d", "toolName": "Write", "capability": "write", "summary": "cancel-queued"}]))
        await until(lambda: "cancel-one" in "".join(out.parts))
        pipe.send_text("\x1b")
        assert await third == {} and await fourth == {}
        assert broker.buffer.text == "原草稿"
    asyncio.run(_with_broker(scenario))


def test_source_account_switch_add_and_secret_field():
    from ruocun.tui.app.app import runAccountPicker
    from ruocun.tui.app.types import AccountActions
    async def scenario(broker, pipe, out, until):
        switched, added = [], []
        async def switch(name):
            switched.append(name)
            return True
        async def remove(name):
            pass
        async def add(key, name, provider, baseUrl, model):
            added.append((key, name, provider, baseUrl, model))
            return {"ok": True, "name": name or "default"}
        actions = AccountActions(lambda: [{"name": "personal", "active": True, "detail": "deepseek/v4"},
                                         {"name": "work", "active": False, "detail": "deepseek/v4"}], switch, remove, add)
        picking = asyncio.create_task(runAccountPicker(broker, actions))
        await until(lambda: "personal" in "".join(out.parts))
        pipe.send_text("\x1b[B\r")
        assert "work" in await picking and switched == ["work"]
        actions.listAccounts = lambda: []
        picking = asyncio.create_task(runAccountPicker(broker, actions))
        await until(lambda: "哪个 provider" in "".join(out.parts))
        pipe.send_text("2")
        await until(lambda: "粘贴 千帆 token plan" in "".join(out.parts))
        pipe.send_text("synthetic-qianfan-key\r")
        await until(lambda: "起个名" in "".join(out.parts))
        pipe.send_text("\r")
        assert "default" in await picking
        assert added == [("synthetic-qianfan-key", None, "qianfan", None, None)]
        assert "synthetic-qianfan-key" not in "".join(out.parts)
    asyncio.run(_with_broker(scenario))


@pytest.mark.parametrize("models", [["GLM-5.3-joybuilder", "DeepSeek-V4-Pro-joybuilder"], []])
def test_source_custom_account_gateway_and_manual_fallback(models):
    from ruocun.tui.app.app import runAccountPicker
    from ruocun.tui.app.types import AccountActions
    async def scenario(broker, pipe, out, until):
        added, fetched = [], []
        async def switch(name):
            return True
        async def remove(name):
            pass
        async def fetch(base, key):
            fetched.append((base, key))
            return models
        async def add(*args):
            added.append(args)
            return {"ok": True, "name": "default"}
        action = AccountActions(lambda: [], switch, remove, add, fetch)
        running = asyncio.create_task(runAccountPicker(broker, action))
        await until(lambda: "哪个 provider" in "".join(out.parts))
        pipe.send_text("5")
        await until(lambda: "输入网关地址" in "".join(out.parts))
        pipe.send_text("http://127.0.0.1:1/v1\r")
        await until(lambda: "粘贴 自定义网关" in "".join(out.parts))
        pipe.send_text("synthetic-gateway-key\r")
        if models:
            await until(lambda: "GLM-5.3-joybuilder" in "".join(out.parts))
            pipe.send_text("1")
        else:
            await until(lambda: "输入模型名" in "".join(out.parts))
            pipe.send_text("my-model\r")
        await until(lambda: "起个名" in "".join(out.parts))
        pipe.send_text("\r")
        assert "default" in await running
        assert fetched == [("http://127.0.0.1:1/v1", "synthetic-gateway-key")]
        assert added == [("synthetic-gateway-key", None, "deepseek", "http://127.0.0.1:1/v1", models[0] if models else "my-model")]
    asyncio.run(_with_broker(scenario))


def test_source_model_picker_selection_uses_backend():
    from ruocun.tui.app.app import runModelPicker
    async def scenario(broker, pipe, out, until):
        changed = []
        async def switch(model):
            changed.append(model)
            return "changed " + model
        task = asyncio.create_task(runModelPicker(broker, lambda: [{"model": "m1", "active": True}, {"model": "m2", "active": False}], switch))
        await until(lambda: "m2" in "".join(out.parts))
        pipe.send_text("\x1b[B\r")
        assert await task == "changed m2" and changed == ["m2"]
    asyncio.run(_with_broker(scenario))


def test_source_shift_tab_localized_mode_hint():
    async def scenario(broker, pipe, out, until):
        async def cycle():
            return "auto"
        broker.set_language("zh")
        broker.set_status_info({"permMode": "bypassPermissions", "model": "deepseek-ai/DeepSeek-V4.1-Flash",
                                "costCNY": 0.029, "contextUsed": 29000, "contextWindow": 1000000,
                                "branch": "main"})
        assert list(broker._status_bar()) == [
            ("class:permission-status", "全权放行 『 Shift+Tab 切换 』"),
            ("", "DeepSeek-V4.1-Flash · ￥0.029 · 上下文 29k/1000k · ⎇ main"),
        ]
        broker.on_cycle_mode = cycle
        broker.set_language("en")
        pipe.send_text("\x1b[Z")
        await until(lambda: "Switched to Smart approval" in "".join(out.parts))
    asyncio.run(_with_broker(scenario))
