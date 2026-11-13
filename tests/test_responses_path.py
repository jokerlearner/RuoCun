"""任务05 完整产品路径：合成账户配置 → Responses 路由 → 同一对话/工具回合 → 回答。

通过真实 ``-m ruocun --responses-demo <合成配置目录> <prompt>`` 子进程验证：
合成账户配置 + 本地 loopback 合成 HTTP/SSE 服务（真实 HTTP POST，不调用真实模型、
不访问公网、不读真实用户配置/凭据）+ 注入式 transport 重写端点。
输出两轮请求 golden、Responses 原始事件 golden、统一 Chat 事件 golden 与清理回执。

预期独立来源：冻结 ``src/client/responses.test.ts:5-13`` fixture、``:30-62`` 两轮
工具回合、``:48-51`` 请求断言、``:54`` usage、``:87-96`` 路由反例；规格 R-06/R-07、
ADR-0003（不重放）、ADR-0004（HITL 未验）。既有 03/04 行为作为回归基线。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SYNTHETIC_KEY = "sk-synthetic-NOT-A-REAL-KEY"

# 冻结 responses.test.ts:6-8 / :11 的 fixture（测试预期独立来源，不读产品实现）
REASONING: dict[str, Any] = {
    "type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "ciphertext",
}
CALL_ARGUMENTS = '{"path":"中文.ts"}'
USAGE: dict[str, Any] = {
    "input_tokens": 100, "output_tokens": 10, "total_tokens": 110,
    "input_tokens_details": {"cached_tokens": 80},
}


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
    return subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-m", "ruocun", *arguments],
        cwd=tmp_path, env=env, capture_output=True, text=True,
        encoding="utf-8", timeout=30,
    )


def _config(tmp_path: Path, *, key: bool = True, bad_json: bool = False,
            model: str = "gpt-6.1-sol", with_env: bool = True) -> Path:
    cfg = tmp_path / "cfg"
    cfg.mkdir(exist_ok=True)
    profile: dict[str, Any] = {
        "provider": "openai", "baseUrl": "https://api.openai.com/v1", "model": model,
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
            "RUOCUN_MAX_OUTPUT_TOKENS=50000\nRUOCUN_REASONING_EFFORT=none\n",
            encoding="utf-8",
        )
    return cfg


def _chat_config(tmp_path: Path) -> Path:
    """04 的 --chat-demo 回归用配置（deepseek，走 Chat Completions）。"""
    cfg = tmp_path / "chatcfg"
    cfg.mkdir(exist_ok=True)
    (cfg / "config.json").write_text(json.dumps({
        "version": 2, "activeProfile": "synthetic",
        "profiles": {"synthetic": {
            "provider": "deepseek", "baseUrl": "https://api.deepseek.com",
            "model": "deepseek-v4-pro", "key": SYNTHETIC_KEY,
        }},
    }), encoding="utf-8")
    return cfg


def _report(tmp_path: Path) -> dict[str, Any]:
    cfg = _config(tmp_path)
    result = _cli(tmp_path, "--responses-demo", str(cfg), "看图并读文件")
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# 完整可运行路径与请求 / 事件 golden
# ---------------------------------------------------------------------------


def test_responses_demo_full_path_answer_and_goldens(tmp_path):
    report = _report(tmp_path)
    assert report["route"] == "responses"
    assert report["status"] == "complete"
    assert report["answer"] == "完成"
    assert report["wire_request_validated"] is True  # 真实 HTTP POST 到达合成服务且 body 一致
    assert report["server_closed"] is True
    assert report["server_socket_fileno"] == -1  # 监听 socket 已关闭
    assert report["port_not_listening"] is True  # 端口不再监听
    assert len(report["request_golden"]) == 2
    assert len(report["responses_events_golden"]) == 2
    assert len(report["event_golden"]) == 2
    assert SYNTHETIC_KEY not in json.dumps(report, ensure_ascii=False)  # 不泄漏 secret


def test_responses_demo_request_goldens(tmp_path):
    report = _report(tmp_path)
    first, second = report["request_golden"]
    # 冻结 responses.test.ts:48-51 / :64-69 的请求断言
    assert first["model"] == "gpt-6.1-sol"
    assert first["store"] is False
    assert first["include"] == ["reasoning.encrypted_content"]
    assert first["max_output_tokens"] == 50000  # dotenv + RUOCUN_ 环境别名
    assert first["reasoning"] == {"effort": "low"}  # none + 6.1-sol 映射
    assert first["tools"] == [{
        "type": "function", "name": "Read", "description": "读取",
        "parameters": {"type": "object"}, "strict": False,
    }]
    assert first["input"][1]["content"][1] == {
        "type": "input_image", "image_url": "data:image/png;base64,test",
    }
    assert "max_tokens" not in first and "messages" not in first
    # 冻结 responses.test.ts:57-59：第二轮带入 reasoning / function_call / function_call_output
    assert second["input"][2:] == [
        REASONING,
        {"type": "function_call", "call_id": "call_1",
         "name": "Read", "arguments": CALL_ARGUMENTS},
        {"type": "function_call_output", "call_id": "call_1", "output": "文件内容"},
    ]


def test_responses_demo_event_goldens(tmp_path):
    report = _report(tmp_path)
    first, second = report["event_golden"]
    # 统一事件回传：工具调用、加密推理项、usage 归一化、结束原因
    assert first["message"]["tool_calls"] == [{
        "id": "call_1", "type": "function",
        "function": {"name": "Read", "arguments": CALL_ARGUMENTS},
    }]
    assert first["message"]["responseItems"] == [REASONING]
    assert first["usage"]["prompt_cache_hit_tokens"] == 80
    assert first["usage"]["prompt_cache_miss_tokens"] == 20
    assert first["finish_reason"] == "tool_calls"
    assert second["message"]["content"] == "完成"
    assert [d["text"] for d in second["deltas"] if d["kind"] == "content"] == ["完成"]
    # Responses 原始事件 golden：末帧为 completed，usage 为冻结 fixture
    completed = report["responses_events_golden"][0][-1]
    assert completed["type"] == "response.completed"
    assert completed["response"]["usage"] == USAGE


def test_responses_demo_route_criteria_and_no_public_network(tmp_path):
    report = _report(tmp_path)
    criteria = report["route_criteria"]
    assert criteria["uses_responses"] is True
    assert criteria["base_url"] == "https://api.openai.com/v1"
    assert criteria["endpoint"] == "https://api.openai.com/v1/responses"
    assert criteria["model"] == "gpt-6.1-sol"
    # 判据成立但请求实际只到本次拥有的本地合成服务，未访问公网
    assert report["configured_base_url"] == "https://api.openai.com/v1"
    assert report["local_endpoint"].startswith("http://127.0.0.1:")
    assert report["local_endpoint"].endswith("/responses")
    assert len(report["server_captured"]) == 2
    assert all(c["path"] == "/responses" for c in report["server_captured"])


# ---------------------------------------------------------------------------
# 无效配置 / 路由不命中 / 坏参数明确失败边界
# ---------------------------------------------------------------------------


def test_responses_demo_missing_config_dir_is_explicit_failure(tmp_path):
    result = _cli(tmp_path, "--responses-demo", str(tmp_path / "absent"), "你好")
    assert result.returncode != 0
    assert "失败" in result.stderr or "缺少" in result.stderr


def test_responses_demo_bad_json_is_explicit_failure(tmp_path):
    cfg = _config(tmp_path, bad_json=True)
    result = _cli(tmp_path, "--responses-demo", str(cfg), "你好")
    assert result.returncode != 0
    assert "失败" in result.stderr or "缺少" in result.stderr


def test_responses_demo_missing_key_is_explicit_failure(tmp_path):
    cfg = _config(tmp_path, key=False)
    result = _cli(tmp_path, "--responses-demo", str(cfg), "你好",
                  extra_env={"OPENAI_API_KEY": "sk-env-NOT-REAL"})
    assert result.returncode != 0
    assert "失败" in result.stderr or "缺少" in result.stderr


def test_responses_demo_model_not_matching_route_is_explicit_failure(tmp_path):
    # R-06：不因 SDK 支持就把非 gpt-6 模型静默改成 Responses；明确失败
    cfg = _config(tmp_path)
    result = _cli(tmp_path, "--responses-demo", str(cfg), "--model", "gpt-5", "你好")
    assert result.returncode != 0
    assert "判据" in result.stderr or "失败" in result.stderr


def test_responses_demo_requires_config_dir_argument(tmp_path):
    result = _cli(tmp_path, "--responses-demo")
    assert result.returncode != 0


# ---------------------------------------------------------------------------
# 任务 03/04 既有行为回归（不得破坏）
# ---------------------------------------------------------------------------


def test_existing_version_help_agent_and_chat_demo_preserved(tmp_path):
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
    chat = _cli(tmp_path, "--chat-demo", str(_chat_config(tmp_path)), "你好")
    assert chat.returncode == 0, chat.stderr
    chat_report = json.loads(chat.stdout)
    assert chat_report["status"] == "complete"
    assert chat_report["answer"] == "你好，世界 😀"  # 04 首轮 Chat SSE 路径不被破坏
