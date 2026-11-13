"""冻结 DAO 首次引导的顺序、验证、信任及异常退出。"""

import asyncio

import pytest


@pytest.mark.parametrize("trust", [True, False])
def test_source_onboarding_language_provider_key_and_trust(trust):
    from ruocun.config.profiles import DEFAULTS
    from ruocun.i18n.i18n import getLang, setLang
    from ruocun.tui.onboarding.run import runOnboarding

    events = []

    class Owner:
        async def show_welcome(self, info, *, skip_footer=False):
            assert info["cwd"] == "/synthetic/project" and skip_footer
            events.append("welcome")

        async def select(self, title, items, *, initial_index=0, wrap=False):
            values = [item["value"] for item in items]
            assert wrap
            if values == ["zh", "en"]:
                assert initial_index == 1
                return "zh"
            assert values == ["deepseek", "volcengine", "qianfan", "zhipu"] and initial_index == 0
            assert getLang() == "zh" and "选择模型来源" in title
            return "volcengine"

        def set_language(self, lang):
            events.append(("language", lang))
            setLang(lang)

        async def ask_secret_validated(self, prompt, submit, *, validating):
            assert "火山方舟" in prompt and "正在校验" in validating
            assert not await submit("synthetic-invalid")
            assert await submit("synthetic-valid")
            return "synthetic-valid"

        async def ask_trust(self, prompt):
            assert "/synthetic/project" in prompt and "[y/N]" in prompt and ".ruocun/settings.json" in prompt
            events.append("trust prompt")
            return trust

        async def write(self, text):
            assert "无效" in text
            events.append("invalid notice")

    async def validate(cred):
        assert cred["provider"] == "volcengine" and cred["baseUrl"] == DEFAULTS["volcengine"]["baseUrl"]
        events.append("validate")
        return {"ok": True} if cred["key"] == "synthetic-valid" else {"ok": False, "reason": "invalid"}

    async def persist(provider, meta, key):
        assert provider == "volcengine" and meta == DEFAULTS["volcengine"] and key == "synthetic-valid"
        events.append("persist")
        return {**meta, "key": key, "provider": provider, "source": "profile:default"}

    async def write_lang(lang):
        assert lang == "zh"
        events.append("save language")

    async def trust_current():
        events.append("save trust")

    setLang("en")
    try:
        result = asyncio.run(runOnboarding(Owner(), welcome={"cwd": "/synthetic/project"}, detectedLang="en",
                                          validate=validate, persist=persist, writeLang=write_lang,
                                          trustCurrent=trust_current, workspaceRoot="/synthetic/project"))
        assert result["lang"] == "zh" and result["trusted"] is trust
        assert result["resolved"]["key"] == "synthetic-valid"
        expected = ["welcome", ("language", "zh"), "validate", "invalid notice", "validate", "persist", "trust prompt", "save language"]
        assert events == expected + (["save trust"] if trust else [])
    finally:
        setLang("en")


@pytest.mark.parametrize("stop", ["empty", "persist", "writeLang"])
def test_source_onboarding_stops_without_replaying_writes(stop):
    from ruocun.i18n.i18n import setLang
    from ruocun.tui.onboarding.run import runOnboarding

    events = []

    class Owner:
        async def show_welcome(self, info, *, skip_footer=False):
            pass

        async def select(self, title, items, *, initial_index=0, wrap=False):
            return items[initial_index]["value"]

        def set_language(self, lang):
            setLang(lang)

        async def ask_secret_validated(self, prompt, submit, *, validating):
            if stop == "empty":
                return None
            assert await submit("synthetic-valid")
            return "synthetic-valid"

        async def ask_trust(self, prompt):
            events.append("trust prompt")
            return True

        async def write(self, text):
            assert "Save failed" in text and "synthetic-valid" not in text
            events.append("safe failure")

    async def validate(cred):
        events.append("validate")
        return {"ok": True}

    async def persist(provider, meta, key):
        events.append("persist")
        if stop == "persist":
            raise OSError("synthetic write status unknown: synthetic-valid")
        return {**meta, "key": key, "provider": provider, "source": "profile:default"}

    async def write_lang(lang):
        events.append("save language")
        raise OSError("synthetic language write failed")

    async def trust_current():
        pytest.fail("trust may only be saved after language is saved")

    setLang("en")
    assert asyncio.run(runOnboarding(Owner(), welcome={}, detectedLang="en", validate=validate, persist=persist,
                                     writeLang=write_lang, trustCurrent=trust_current, workspaceRoot="/synthetic/project")) is None
    assert events == {"empty": [], "persist": ["validate", "persist", "safe failure"],
                      "writeLang": ["validate", "persist", "trust prompt", "save language", "safe failure"]}[stop]


def test_source_key_step_holds_owner_until_validation_and_save_settle():
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from ruocun.agent.input_broker import InputBroker

    class Output(DummyOutput):
        def __init__(self):
            self.writes = []

        def write(self, data):
            self.writes.append(data)

    async def scenario():
        async def pause():
            pass

        async def until(predicate):
            async with asyncio.timeout(4):
                while not predicate():
                    await asyncio.sleep(.01)

        validating, saved = asyncio.Event(), asyncio.Event()
        attempts = []

        async def submit(key):
            attempts.append(key)
            validating.set()
            await saved.wait()
            return True

        with create_pipe_input() as pipe:
            output = Output()
            broker = InputBroker(on_pause=pause, input=pipe, output=output)
            broker.configure_terminal({"RUOCUN_THEME": "dark"})
            await broker.start()
            waiting = asyncio.create_task(broker.next_submission())
            try:
                entering = asyncio.create_task(broker.ask_secret_validated("Paste your API key", submit, validating="Validating key…"))
                await until(lambda: "Paste your API key" in "".join(output.writes))
                pipe.send_text("\x1b[200~synthetic-\r\n valid\x1b[201~\r\rsynthetic-extra\r")
                async with asyncio.timeout(4):
                    await validating.wait()
                await until(lambda: "Validating key…" in "".join(output.writes))
                assert attempts == ["synthetic-valid"] and not entering.done() and not waiting.done()
                assert not broker.buffer.text and "synthetic-" not in "".join(output.writes)
                saved.set()
                assert await entering == "synthetic-valid"
                for text, decision in (("n", False), ("y\r", True)):
                    output.writes.clear()
                    asking = asyncio.create_task(broker.ask_trust("Synthetic folder [y/N]"))
                    await until(lambda: "Synthetic folder" in "".join(output.writes))
                    pipe.send_text(text)
                    async with asyncio.timeout(4):
                        assert await asking is decision
                    assert not waiting.done() and not broker.buffer.text
            finally:
                saved.set()
                await broker.close()
            assert await waiting is None

    asyncio.run(scenario())
