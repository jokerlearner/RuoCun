"""任务04 完整产品路径：profile/dotenv/模型覆盖 → 冻结提示/参数 → Chat SSE → 回答。

通过真实 ``-m ruocun --chat-demo <合成配置目录> <prompt>`` 子进程验证：
合成账户配置 + 本地 loopback 合成 SSE 服务（真实 HTTP，不调用真实模型、不读真实
用户配置/凭据）。预期独立来源：冻结 src/index.ts:330-423（账户/模型路由）、
D09 兼容契约、client.ts 请求/流、任务票 CFG/WIRE 子案例。
既有 --version/--help/69 行为作为回归基线（任务03）。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import ruocun

SYNTHETIC_KEY = "sk-synthetic-NOT-A-REAL-KEY"


def _cli(tmp_path: Path, *arguments: str, extra_env: dict[str, str] | None = None):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {
        "SYSTEMROOT": "C:\\Windows", "WINDIR": "C:\\Windows",
        "PATH": str(Path(sys.executable).parent),
        "HOME": str(home), "USERPROFILE": str(home),
        "APPDATA": str(home / "appdata"), "LOCALAPPDATA": str(home / "localappdata"),
        "TEMP": str(home), "TMP": str(home),
        "PYTHONUTF8": "1", "PYTHONNOUSERSITE": "1",
    }
    if extra_env:
        env.update(extra_env)
    package = Path(ruocun.__file__).resolve().parent.parent
    entry = f"import runpy,sys;sys.path.insert(0,{str(package)!r});runpy.run_module('ruocun',run_name='__main__')"
    return subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", entry, *arguments],
        cwd=tmp_path, env=env, capture_output=True, text=True,
        encoding="utf-8", timeout=30,
    )


def _config(tmp_path: Path, *, key: bool = True, bad_json: bool = False,
            with_env: bool = True) -> Path:
    cfg = tmp_path / "cfg"
    cfg.mkdir(exist_ok=True)
    profile = {
        "provider": "deepseek", "baseUrl": "https://api.deepseek.com",
        "model": "deepseek-v4-pro",
    }
    if key:
        profile["key"] = SYNTHETIC_KEY
    raw = json.dumps({
        "version": 2, "activeProfile": "synthetic",
        "profiles": {"synthetic": profile}, "theme": "dark",
    })
    (cfg / "config.json").write_text("{ broken" if bad_json else raw, encoding="utf-8")
    if with_env:
        (cfg / ".env").write_text(
            "RUOCUN_MAX_OUTPUT_TOKENS=50000\nRUOCUN_REASONING_EFFORT=high\n",
            encoding="utf-8",
        )
    return cfg


# ---------------------------------------------------------------------------
# 完整可运行路径
# ---------------------------------------------------------------------------


def test_chat_demo_full_path_answer_and_request_golden(tmp_path):
    cfg = _config(tmp_path)
    result = _cli(tmp_path, "--chat-demo", str(cfg), "你好")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "complete"
    assert report["answer"] == "你好，世界 😀"  # 中文/emoji 跨 3 字节分片后完整还原
    assert report["model"] == "deepseek-v4-pro"
    assert report["provider"] == "deepseek"
    assert report["selection"] == "native"
    body = report["request_golden"]
    assert body["model"] == "deepseek-v4-pro"
    assert body["stream"] is True
    assert body["stream_options"] == {"include_usage": True}
    assert body["max_tokens"] == 50000  # dotenv + RUOCUN_ 环境别名生效
    assert body["reasoning_effort"] == "high"  # extra 覆盖
    assert body["messages"][0]["role"] == "system"
    assert body["messages"][1] == {"role": "user", "content": "你好"}
    assert "temperature" not in body and "top_p" not in body
    assert report["wire_request_validated"] is True  # 真实 HTTP POST 到达合成服务
    assert report["server_closed"] is True  # 本地服务已关闭
    assert SYNTHETIC_KEY not in result.stdout  # 请求 golden/输出不泄漏合成密钥


def test_chat_demo_system_prompt_brand_whitelist(tmp_path):
    cfg = _config(tmp_path)
    result = _cli(tmp_path, "--chat-demo", str(cfg), "品牌")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    system_text = report["request_golden"]["messages"][0]["content"]
    assert "RUOCUN.md" in system_text
    assert ".ruocun/settings.json" in system_text
    assert "DAO.md" not in system_text
    assert ".dao/settings.json" not in system_text
    assert "python/node" not in system_text
    assert "你当前运行的模型是 deepseek-v4-pro" in system_text
    assert not system_text.count("{model_id}")


def test_chat_demo_model_override(tmp_path):
    cfg = _config(tmp_path)
    result = _cli(tmp_path, "--chat-demo", str(cfg), "--model", "glm-5.3-flash", "模型")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["model"] == "glm-5.3-flash"
    assert report["request_golden"]["model"] == "glm-5.3-flash"


def test_chat_demo_does_not_load_previous_account_source(tmp_path):
    cfg = tmp_path / "cfg"
    cfg.mkdir()
    old = tmp_path / "old-config.json"
    old.write_text(json.dumps({
        "version": 2, "activeProfile": "legacy",
        "profiles": {"legacy": {"provider": "deepseek",
                                "baseUrl": "https://api.deepseek.com",
                                "model": "deepseek-v4-pro", "key": SYNTHETIC_KEY}},
    }), encoding="utf-8")
    before = old.read_bytes()
    (cfg / "compatibility.json").write_text(json.dumps({
        "version": 1,
        "sources": [{"id": "old-profile", "scope": "user",
                     "resource": "profiles", "path": str(old)}],
    }), encoding="utf-8")
    (cfg / ".env").write_text("RUOCUN_MAX_OUTPUT_TOKENS=50000\n", encoding="utf-8")
    result = _cli(tmp_path, "--chat-demo", str(cfg), "兼容账户")
    assert result.returncode != 0
    assert "缺少有效凭据" in result.stderr
    assert old.read_bytes() == before


# ---------------------------------------------------------------------------
# 无效配置 / 缺凭据 / 坏 JSON 明确失败边界
# ---------------------------------------------------------------------------


def test_chat_demo_missing_config_dir_is_explicit_failure(tmp_path):
    result = _cli(tmp_path, "--chat-demo", str(tmp_path / "absent"), "你好")
    assert result.returncode != 0
    assert "缺少有效凭据" in result.stderr or "失败" in result.stderr


def test_chat_demo_bad_json_is_explicit_failure(tmp_path):
    cfg = _config(tmp_path, bad_json=True)
    result = _cli(tmp_path, "--chat-demo", str(cfg), "你好")
    assert result.returncode != 0
    assert "缺少有效凭据" in result.stderr


def test_chat_demo_missing_key_not_picked_from_generic_env(tmp_path):
    # CFG-04：缺 key 不靠 OPENAI_API_KEY 等通用环境变量自动挑账户。
    cfg = _config(tmp_path, key=False)
    result = _cli(tmp_path, "--chat-demo", str(cfg), "你好",
                  extra_env={"OPENAI_API_KEY": "sk-env-NOT-REAL"})
    assert result.returncode != 0
    assert "缺少有效凭据" in result.stderr


def test_chat_demo_requires_config_dir_argument(tmp_path):
    result = _cli(tmp_path, "--chat-demo")
    assert result.returncode != 0


# ---------------------------------------------------------------------------
# 任务03 既有行为回归（不得破坏）
# ---------------------------------------------------------------------------


def test_existing_version_help_and_unimplemented_agent_preserved(tmp_path):
    version = _cli(tmp_path, "--version")
    assert version.returncode == 0
    assert version.stdout == "RuoCun v0.1.0.dev0\n"
    assert version.stderr == ""
    help_result = _cli(tmp_path, "--help")
    assert help_result.returncode == 0
    assert "用法：ruocun [选项] [提示词]" in help_result.stdout
    normal = _cli(tmp_path, "合成提示词")
    assert normal.returncode == 71  # ADR-0011：真实入口在合成HOME中明确缺账户
    assert "缺少可用账户" in normal.stderr
