"""CFG-05/06：dotenv 简化方言与原生环境变量的逐项谓词。"""

from __future__ import annotations

from ruocun.config import compat, env_file

# ---------------------------------------------------------------------------
# CFG-05 · dotenv (env_file.test.ts:7-66)
# ---------------------------------------------------------------------------


def test_parse_dotenv_key_value_lines():
    # frozen env_file.test.ts:8-13
    assert env_file.parseDotenv("DEEPSEEK_API_KEY=sk-abc\nDEEPSEEK_MODEL=flash") == {
        "DEEPSEEK_API_KEY": "sk-abc", "DEEPSEEK_MODEL": "flash",
    }


def test_parse_dotenv_skips_blanks_comments_and_strips_paired_quotes():
    # frozen env_file.test.ts:14-16
    assert env_file.parseDotenv('\n# comment\nA="quoted"\nB=\'q2\'\n') == {
        "A": "quoted", "B": "q2",
    }


def test_parse_dotenv_ignores_lines_without_equals():
    # frozen env_file.test.ts:17-19
    assert env_file.parseDotenv("nonsense\nA=1") == {"A": "1"}


def test_parse_dotenv_unpaired_quotes_are_kept():
    # 简化方言：只有成对引号才剥离，不引入 export/插值/转义 (env_file.ts:13-18)
    assert env_file.parseDotenv('A="open\nB=tail"\nC="v" # not a comment') == {
        "A": '"open', "B": 'tail"', "C": '"v" # not a comment',
    }


def test_parse_dotenv_does_not_expand_export_or_variables():
    # D09:134「不引入 export、变量插值、跨品牌扫描」
    assert env_file.parseDotenv("export A=1\nB=${A}\nC=$A") == {
        "export A": "1", "B": "${A}", "C": "$A",
    }
    assert "A" not in env_file.parseDotenv("export A=1\nB=${A}\nC=$A")


def test_load_dotenv_missing_file_returns_empty(tmp_path):
    # frozen env_file.test.ts:31-33
    assert env_file.loadDotenv(tmp_path / ".env") == {}


def test_load_dotenv_reads_existing_file(tmp_path):
    # frozen env_file.test.ts:34-38
    (tmp_path / ".env").write_text("DEEPSEEK_API_KEY=sk-xyz\n", encoding="utf-8")
    assert env_file.loadDotenv(tmp_path / ".env") == {"DEEPSEEK_API_KEY": "sk-xyz"}


def test_apply_dotenv_existing_process_env_including_empty_string_wins(tmp_path):
    # frozen env_file.test.ts:52-61 + D09「已有 process env（含空串）优先」
    (tmp_path / ".env").write_text(
        "RUOCUN_ENVTEST_NEW=fromfile\nRUOCUN_ENVTEST_EXIST=fromfile\nRUOCUN_ENVTEST_EMPTY=fromfile\n",
        encoding="utf-8",
    )
    environ = {"RUOCUN_ENVTEST_EXIST": "fromenv", "RUOCUN_ENVTEST_EMPTY": ""}
    applied = env_file.applyDotenv(tmp_path / ".env", environ)
    assert environ["RUOCUN_ENVTEST_NEW"] == "fromfile"
    assert environ["RUOCUN_ENVTEST_EXIST"] == "fromenv"  # 不覆盖
    assert environ["RUOCUN_ENVTEST_EMPTY"] == ""  # 空串也算已存在，不被 .env 覆盖
    assert applied == ["RUOCUN_ENVTEST_NEW"]


def test_apply_dotenv_missing_file_is_noop(tmp_path):
    # frozen env_file.test.ts:63-65
    environ: dict[str, str] = {}
    assert env_file.applyDotenv(tmp_path / "nope.env", environ) == []
    assert environ == {}


# ---------------------------------------------------------------------------
# CFG-06 · 原生环境变量与逐项谓词 (D09:144-147)
# ---------------------------------------------------------------------------


def test_ruocun_primary_wins_over_dao_fallback():
    assert compat.resolve_env("AUTO_APPROVE", {
        "RUOCUN_AUTO_APPROVE": "1", "DAO_AUTO_APPROVE": "0",
    }) == "1"


def test_previous_environment_prefix_is_ignored():
    assert compat.resolve_env("AUTO_APPROVE", {"DAO_AUTO_APPROVE": "1"}) is None
    assert compat.resolve_env("AUTO_APPROVE", {}) is None


def test_present_primary_blocks_fallback_even_when_value_is_empty():
    # D09:146「判断键是否存在（空值也阻止 fallback）」
    assert compat.resolve_env("TRUST", {
        "RUOCUN_TRUST": "", "DAO_TRUST": "1",
    }) == ""
    assert compat.resolve_env("AUTO_APPROVE", {
        "RUOCUN_AUTO_APPROVE": "", "DAO_AUTO_APPROVE": "1",
    }) == ""


def test_auto_approve_zero_is_still_truthy_and_empty_is_false():
    # 冻结 index.ts:942 !!process.env.DAO_AUTO_APPROVE；"0" 是非空字符串 → 真
    assert compat.auto_approve({"DAO_AUTO_APPROVE": "0"}) is False
    assert compat.auto_approve({"RUOCUN_AUTO_APPROVE": "0"}) is True
    assert compat.auto_approve({"DAO_AUTO_APPROVE": ""}) is False
    assert compat.auto_approve({}) is False


def test_trust_only_the_exact_string_one():
    # 冻结 config/trust.ts:34 process.env.RUOCUN_TRUST === "1"
    assert compat.trust({"DAO_TRUST": "1"}) is False
    assert compat.trust({"RUOCUN_TRUST": "1"}) is True
    assert compat.trust({"RUOCUN_TRUST": "0"}) is False
    assert compat.trust({"RUOCUN_TRUST": "true"}) is False
    assert compat.trust({"RUOCUN_TRUST": ""}) is False


def test_use_keychain_disabled_only_by_zero_or_off():
    # 冻结 config/keychain.ts:18
    assert compat.use_keychain_enabled({"DAO_USE_KEYCHAIN": "0"}) is True
    assert compat.use_keychain_enabled({"RUOCUN_USE_KEYCHAIN": "0"}) is False
    assert compat.use_keychain_enabled({"RUOCUN_USE_KEYCHAIN": "off"}) is False
    assert compat.use_keychain_enabled({"RUOCUN_USE_KEYCHAIN": "1"}) is True
    assert compat.use_keychain_enabled({"RUOCUN_USE_KEYCHAIN": "OFF"}) is True
    assert compat.use_keychain_enabled({}) is True


def test_auto_approve_zero_and_trust_zero_are_not_confused():
    # 任务票 CFG-06 明确要求：AUTO_APPROVE=0 与 TRUST=0 不混同
    environ = {"RUOCUN_AUTO_APPROVE": "0", "RUOCUN_TRUST": "0"}
    assert compat.auto_approve(environ) is True   # 非空真
    assert compat.trust(environ) is False          # 只 "1"


def test_numeric_env_predicates_use_number_or_default_not_bool():
    # 冻结 client.ts:104/127/390 Number(process.env.X) || default
    assert compat.max_output_tokens({"RUOCUN_MAX_OUTPUT_TOKENS": "50000"}) == 50000
    assert compat.max_output_tokens({"RUOCUN_MAX_OUTPUT_TOKENS": "0"}) == 128000
    assert compat.max_output_tokens({"RUOCUN_MAX_OUTPUT_TOKENS": "bogus"}) == 128000
    assert compat.max_output_tokens({}) == 128000
    assert compat.stream_idle_ms({"RUOCUN_STREAM_IDLE_MS": "50"}) == 50
    assert compat.stream_idle_ms({}) == 240000
    assert compat.max_continue({}) == 3
    assert compat.reasoning_effort({"RUOCUN_REASONING_EFFORT": "low"}) == "low"
    assert compat.reasoning_effort({}) == "max"


def test_third_party_standard_variable_names_are_not_renamed():
    # D09:148「第三方标准变量保留原名」
    assert compat.third_party("OPENAI_API_KEY", {"OPENAI_API_KEY": "x"}) == "x"
    assert compat.third_party("HTTP_PROXY", {"HTTP_PROXY": "http://p:8080"}) == "http://p:8080"
    assert compat.third_party("TERM", {"TERM": "xterm"}) == "xterm"
