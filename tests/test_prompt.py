"""WIRE-01/PROMPT: 冻结提示词组装、品牌/环境差异白名单与环境快照纯函数。

预期独立来源：
- 冻结 src/prompt/system_prompt.ts:687-877 及 .test.ts:4-318
- 冻结 src/env_snapshot.ts:68-72, 163-196, 205-232, 255-290
- R-05（提示词保真、品牌身份与真实 Python/Windows 环境替换形成差异白名单）
- ADR-0001 / ADR-0005 / D09:101（RUOCUN.md / .ruocun 原生根）
"""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

from ruocun import env_snapshot
from ruocun.prompt import system_prompt


def _prompt(**kw):
    base = {"modelId": "deepseek-v4-pro", "toolSummaries": "- Read:读文件\n- Write:写文件",
            "projectInstructions": "### RUOCUN.md @ .\n这是项目指令内容"}
    return system_prompt.buildSystemPrompt({**base, **kw})


# ---------------------------------------------------------------------------
# buildSystemPrompt (system_prompt.test.ts)
# ---------------------------------------------------------------------------


def test_zh_identity_line_and_tool_summaries():
    p = _prompt()
    assert "交互式智能助手" in p
    assert "- Read:读文件" in p
    assert "- Write:写文件" in p


def test_zh_model_self_identification_and_vision():
    p = _prompt()
    assert "你当前运行的模型是 deepseek-v4-pro" in p
    assert "不支持图片输入" in p
    v = _prompt(modelId="kimi-k3")
    assert "你当前运行的模型是 kimi-k3" in v
    assert "这个模型支持图片输入" in v


def test_zh_reflect_switches_default_off():
    p = _prompt()
    assert "[审视者]" not in p
    assert "[纠偏者]" not in p
    assert "[反思]" not in p
    assert "审视与反思提醒" not in p


def test_zh_reflect_memory_only():
    p = _prompt(reflectMemoryEnabled=True)
    assert "[反思]" in p
    assert "[审视者]" not in p
    assert "[纠偏者]" not in p


def test_zh_reflect_challenger_only():
    p = _prompt(reflectChallengerEnabled=True)
    assert "[审视者]" in p
    assert "[纠偏者]" in p
    assert "[反思]" not in p


def test_zh_reflect_both():
    p = _prompt(reflectMemoryEnabled=True, reflectChallengerEnabled=True)
    assert "[审视者]" in p and "[反思]" in p and "[纠偏者]" in p


def test_project_instructions_section_and_default_none():
    assert "# 项目指令" in _prompt()
    assert "这是项目指令内容" in _prompt()
    assert "(无)" in _prompt(projectInstructions="")
    assert "见下方" not in _prompt()
    assert "{project_instruction_files}" not in _prompt()


def test_no_unfilled_placeholders():
    assert not re.search(r"\{[a-z_]+\}", _prompt())
    assert not re.search(r"\{[a-z_]+\}", _prompt(lang="en"))


def test_memories_injection_and_default():
    p = _prompt(memories="- 用户偏好 TypeScript\n- 本项目用 pytest")
    assert "用户偏好 TypeScript" in p
    assert "本项目用 pytest" in p
    assert "(暂无)" in _prompt()


def test_env_snapshot_injection_and_no_stray_placeholder():
    p = _prompt(envSnapshot="- 可用语言/工具: python 3.11.9\n- Git 分支: master (干净)")
    assert "可用语言/工具: python 3.11.9" in p
    assert "Git 分支: master (干净)" in p
    assert "{env_snapshot}" not in _prompt()


def test_interactive_default_has_no_unattended_guidance():
    assert "AskUserQuestion 不会有人来回答" not in _prompt()
    assert "AskUserQuestion 不会有人来回答" not in _prompt(interactive=True)


def test_interactive_false_injects_session_guidance_and_todowrite():
    p = _prompt(interactive=False)
    assert "会话特定指引" in p
    assert "AskUserQuestion 不会有人来回答" in p
    assert "合理默认" in p
    assert "第一步必须先调用 TodoWrite 把任务拆成具体子步骤" in p


def test_interactive_true_has_no_headless_todowrite_requirement():
    assert "第一步必须先调用 TodoWrite 把任务拆成具体子步骤" not in _prompt()
    assert "第一步必须先调用 TodoWrite 把任务拆成具体子步骤" not in _prompt(interactive=True)


def test_en_identity_headers_and_model_note():
    p = _prompt(lang="en", toolSummaries="- Read:Reads a text file")
    assert "interactive intelligent assistant" in p
    for header in ["# Who You Are", "# Authority Hierarchy", "# Honesty",
                   "# Project Instructions", "# Tools", "# Memory"]:
        assert header in p
    assert "- Read:Reads a text file" in p
    assert "You are currently running as deepseek-v4-pro" in p
    assert "does not support image input" in p


def test_default_lang_is_zh():
    p = system_prompt.buildSystemPrompt({"modelId": "x", "toolSummaries": "- a:b"})
    assert "# 你是谁" in p
    assert "# Who You Are" not in p


def test_long_task_directives():
    assert "长任务自主模式" in system_prompt.LONG_TASK_DIRECTIVE
    assert "Long-task autonomous mode" in system_prompt.LONG_TASK_DIRECTIVE_EN


# ---------------------------------------------------------------------------
# WIRE-01 品牌/环境差异白名单（R-05 / ADR-0005 / D09:101）
# ---------------------------------------------------------------------------


def test_brand_deltas_replace_dao_identity_strings():
    p = _prompt()
    assert "DAO.md" not in p
    assert ".dao/settings.json" not in p
    assert "python/node" not in p
    assert "RUOCUN.md" in p
    assert ".ruocun/settings.json" in p


def test_packaged_system_prompt_templates_use_current_product_paths():
    templates = files("ruocun.prompt").joinpath("resources")
    for language in ("zh", "en"):
        text = templates.joinpath(f"system_prompt.{language}.txt").read_text(encoding="utf-8")
        assert ".ruocun/settings.json" in text and "RUOCUN.md" in text
        assert "dao" not in text.casefold() and "python/node" not in text


# ---------------------------------------------------------------------------
# env_snapshot 纯函数 (env_snapshot.ts)
# ---------------------------------------------------------------------------


def test_format_env_snapshot_zh_and_en():
    data = {"toolchain": ["python 3.11.9", "pip 24.0"],
            "gitBranch": "master", "gitDirtyCount": 0, "network": None}
    assert env_snapshot.formatEnvSnapshot(data, False) == (
        "- 可用语言/工具: python 3.11.9; pip 24.0\n- Git 分支: master (干净)")
    assert env_snapshot.formatEnvSnapshot(data, True) == (
        "- Available languages/tools: python 3.11.9; pip 24.0\n"
        "- Git branch: master (clean)")


def test_format_env_snapshot_dirty_and_network():
    data = {"toolchain": [], "gitBranch": "dev", "gitDirtyCount": 3,
            "network": {"reachable": {"npm registry": True, "PyPI": False},
                        "proxy": None}}
    zh = env_snapshot.formatEnvSnapshot(data, False)
    assert "3 个未提交改动" in zh
    assert "网络: 可访问 npm registry;不可访问 PyPI" in zh
    en = env_snapshot.formatEnvSnapshot(data, True)
    assert "3 uncommitted change(s)" in en
    assert "reachable npm registry; unreachable PyPI" in en


def test_format_env_snapshot_none_is_empty():
    assert env_snapshot.formatEnvSnapshot(None, False) == ""


def test_redact_proxy_credentials_idempotent():
    redacted = env_snapshot.redactProxyCredentials("http://user:pass@proxy.corp:8080")
    assert redacted == "http://***@proxy.corp:8080"
    assert "user" not in redacted and "pass" not in redacted
    assert env_snapshot.redactProxyCredentials(redacted) == redacted  # 幂等
    assert env_snapshot.redactProxyCredentials("http://proxy:8080") == "http://proxy:8080"


class _Entry:
    def __init__(self, name: str, is_dir: bool = False) -> None:
        self.name = name
        self._dir = is_dir

    def is_dir(self) -> bool:
        return self._dir


def test_probe_top_level_dir_sanitizes_and_sorts(tmp_path, monkeypatch):
    # Windows 不允许文件名含控制字符，故在系统边界注入合成条目验证清洗规则
    # （mocking.md：只在文件系统边界用替身）。
    entries = [
        _Entry("b_dir", True), _Entry("a.txt"), _Entry(".git", True),
        _Entry("a\nweird"), _Entry("z" * 100),
    ]
    monkeypatch.setattr(Path, "iterdir", lambda self: iter(entries))
    names = env_snapshot.probeTopLevelDir(tmp_path)
    assert names is not None
    assert not any(n.startswith(".git") for n in names)
    assert names[0] == "b_dir/"  # 目录优先
    assert any("\ufffd" in n for n in names)  # 控制字符压成 U+FFFD
    assert any(n.endswith("…") for n in names)  # 单条名字限长


def test_probe_top_level_dir_missing_is_none(tmp_path):
    assert env_snapshot.probeTopLevelDir(tmp_path / "missing") is None


def test_format_fast_env_fields():
    out = env_snapshot.formatFastEnvFields(
        ["src/", "tests/"], {"totalGB": 16.0, "freeGB": 8.0}, False)
    assert "顶层目录: src/, tests/" in out
    assert "系统内存: 16.0 GB 总量,8.0 GB 可用" in out


def test_wrap_delayed_env_notice():
    assert env_snapshot.wrapDelayedEnvNotice("", False) == ""
    zh = env_snapshot.wrapDelayedEnvNotice("- Git 分支: master (干净)", False)
    assert zh.startswith("<环境探测补充 ") and zh.endswith("</环境探测补充>")
    en = env_snapshot.wrapDelayedEnvNotice("- Git branch: master (clean)", True)
    assert '<environment-probe note="tool and platform details collected at startup">' in en
