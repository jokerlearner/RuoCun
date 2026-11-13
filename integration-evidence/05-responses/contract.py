"""独立 merger 复核：任务 05 共享 client 契约与 Responses 路由核对。

复核者自写，不修改产品代码。只用已安装分布的公开 API，并把任务 04 基线
（``git show bbf4aa9:src/ruocun/client/client.py``）的 ``buildRequestBody``
以 exec 独立加载，逐字段对比默认 Chat 路径输出是否与 04 一致。

用法（经 tools/run.py 白名单启动）：
  python -I -X utf8 contract.py --output integration-evidence/05-responses/raw/contract.json
"""

from __future__ import annotations

import argparse
import dataclasses
import inspect
import json
import pathlib
import sys
from types import ModuleType
from typing import Any

REPO = pathlib.Path("D:/java supplement/Firstcode/RuoCun/.worktrees/wb-m05")
BASELINE_CLIENT = REPO / ".cache/m05r2-baseline-client.py"  # 04 基线，复核前导出

SYNTHETIC_KEY = "sk-synthetic-NOT-A-REAL-KEY"
REASONING: dict[str, Any] = {
    "type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "ciphertext",
}
CALL_ARGUMENTS = '{"path":"中文.ts"}'
CALL: dict[str, Any] = {
    "type": "function_call", "id": "fc_1", "call_id": "call_1",
    "name": "Read", "arguments": CALL_ARGUMENTS,
}
ANSWER: dict[str, Any] = {
    "type": "message", "content": [{"type": "output_text", "text": "完成"}],
}
USAGE: dict[str, Any] = {
    "input_tokens": 100, "output_tokens": 10, "total_tokens": 110,
    "input_tokens_details": {"cached_tokens": 80},
}
TOOLS: list[dict[str, Any]] = [{
    "type": "function", "function": {
        "name": "Read", "description": "读取", "parameters": {"type": "object"},
    },
}]


def opts(**kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "baseUrl": "https://api.openai.com/v1", "apiKey": SYNTHETIC_KEY,
        "model": "gpt-6.1-sol", "messages": [{"role": "user", "content": "你好"}],
    }
    base.update(kw)
    return base


def responses_sse(events: list[Any]) -> list[bytes]:
    parts: list[str] = []
    for event in events:
        if isinstance(event, str):
            parts.append("data: " + event + "\r\n\r\n")
        else:
            parts.append("event: " + str(event["type"]) + "\r\ndata: "
                         + json.dumps(event, ensure_ascii=False) + "\r\n\r\n")
    raw = "".join(parts).encode("utf-8")
    return [raw[i:i + 17] for i in range(0, len(raw), 17)]


def chat_sse(frames: list[Any]) -> list[bytes]:
    text = "".join(
        "data: " + (f if isinstance(f, str) else json.dumps(f, ensure_ascii=False)) + "\n\n"
        for f in frames
    )
    raw = text.encode("utf-8")
    return [raw[i:i + 7] for i in range(0, len(raw), 7)]


def completed(output: list[dict[str, Any]], *extra: dict[str, Any]) -> list[Any]:
    return [*extra, {"type": "response.completed", "response": {"output": output, "usage": USAGE}}]


def load_baseline() -> ModuleType:
    """把 04 基线 client.py 的相对导入改为绝对导入后 exec 到独立模块。"""
    src = BASELINE_CLIENT.read_text(encoding="utf-8")
    src = src.replace("from ..config import compat", "from ruocun.config import compat")
    src = src.replace("from ..config.profiles import outputLimitFor",
                      "from ruocun.config.profiles import outputLimitFor")
    src = src.replace("from .sse import SSEStreamParser",
                      "from ruocun.client.sse import SSEStreamParser")
    src = src.replace("from .types import ChatMessage, StreamChatOptions, StreamDelta",
                      "from ruocun.client.types import ChatMessage, StreamChatOptions, StreamDelta")
    mod = ModuleType("m05r2_baseline_client")
    sys.modules[mod.__name__] = mod
    exec(compile(src, "m05r2_baseline_client.py", "exec"), mod.__dict__)  # noqa: S102
    return mod


def transport_for(batches: list[list[bytes]], captured: list[dict[str, Any]]):
    def transport(url: str, headers: dict[str, str], body: bytes):
        captured.append({
            "url": url, "headers": dict(headers),
            "body": json.loads(body.decode("utf-8")),
        })
        idx = min(len(captured) - 1, len(batches) - 1)
        from ruocun.client import client
        return client.HttpResponse(200, {}, iter(batches[idx]))
    return transport


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    from ruocun.client import client as cur, responses
    from ruocun.client import types

    checks: list[dict[str, Any]] = []

    def check(name: str, cond: Any, detail: Any = "") -> None:
        checks.append({"name": name, "pass": bool(cond), "detail": str(detail)})

    # ---- 1) 公共契约静态核对 ----
    sig = str(inspect.signature(cur.streamChat))
    check("streamChat_signature_unchanged",
          all(k in sig for k in ("opts", "transport", "env")), sig)
    fields = [f.name for f in dataclasses.fields(cur.StreamResult)]
    check("StreamResult_fields_unchanged",
          fields == ["status", "deltas", "message", "usage", "finish_reason", "request_body"],
          fields)
    opt_keys = set(types.StreamChatOptions.__annotations__)
    expected_opt = {
        "baseUrl", "apiKey", "provider", "model", "messages", "tools",
        "parallelToolCalls", "extra", "maxTokens", "idleTimeoutMs", "maxRetries",
        "retryDelayMs", "background", "onUsage", "onFinishReason", "onEmptyTruncation",
    }
    check("StreamChatOptions_keys_unchanged", expected_opt.issubset(opt_keys), sorted(opt_keys))
    br = inspect.signature(cur.buildRequestBody).parameters
    check("buildRequestBody_default_use_responses_false",
          "use_responses" in br and br["use_responses"].default is False,
          str(inspect.signature(cur.buildRequestBody)))
    bw = inspect.signature(cur.buildWireMessages).parameters
    check("buildWireMessages_default_use_responses_false",
          "use_responses" in bw and bw["use_responses"].default is False,
          str(inspect.signature(cur.buildWireMessages)))
    check("RESPONSES_ENDPOINT_value",
          responses.RESPONSES_ENDPOINT == "https://api.openai.com/v1/responses",
          responses.RESPONSES_ENDPOINT)

    # ---- 2) 与 04 基线默认 Chat 输出独立对比 ----
    base = load_baseline()
    check("baseline_loaded", hasattr(base, "buildRequestBody"))
    check("baseline_buildRequestBody_has_no_use_responses",
          "use_responses" not in inspect.signature(base.buildRequestBody).parameters,
          str(inspect.signature(base.buildRequestBody)))
    conv = [{
        "role": "assistant", "content": None, "reasoningContent": "思维链",
        "tool_calls": [{"id": "call_1", "type": "function",
                        "function": {"name": "Read", "arguments": CALL_ARGUMENTS}}],
        "responseItems": [REASONING],
    }]
    o = opts(messages=conv, tools=TOOLS,
             extra={"reasoning_effort": "none"}, maxTokens=256000)
    b_base = base.buildRequestBody(o)
    b_default = cur.buildRequestBody(o)
    b_false = cur.buildRequestBody(o, use_responses=False)
    b_true = cur.buildRequestBody(o, use_responses=True)
    check("default_chat_body_identical_to_04_baseline", b_base == b_default,
          json.dumps(b_base, ensure_ascii=False)[:300])
    check("use_responses_false_equals_default", b_default == b_false)
    check("04_baseline_chat_body_has_no_responseItems",
          "responseItems" not in json.dumps(b_base))
    check("use_responses_true_adds_responseItems",
          "responseItems" in json.dumps(b_true))
    check("04_baseline_null_content_to_empty",
          b_base["messages"][0]["content"] == "")
    check("04_baseline_tool_round_reasoning_carried_back",
          b_base["messages"][0].get("reasoning_content") == "思维链")

    # ---- 3) 路由成立/不成立时 URL 与请求体 ----
    cap: list[dict[str, Any]] = []
    t = transport_for([responses_sse(completed([ANSWER]))], cap)
    r = cur.streamChat(opts(), transport=t)
    check("route_true_url_is_responses",
          cap[0]["url"] == "https://api.openai.com/v1/responses", cap[0]["url"])
    rb = cap[0]["body"]
    check("route_true_body_is_responses_shape",
          rb.get("store") is False
          and rb.get("include") == ["reasoning.encrypted_content"]
          and rb.get("max_output_tokens") == 128000
          and rb.get("reasoning") == {"effort": "medium"}
          and "messages" not in rb and "max_tokens" not in rb
          and "max_completion_tokens" not in rb and "stream_options" not in rb,
          json.dumps(rb, ensure_ascii=False)[:300])
    check("route_true_answer", r.message.get("content") == "完成")
    check("secret_not_in_request_body", SYNTHETIC_KEY not in json.dumps(rb))
    check("secret_only_in_authorization_header",
          cap[0]["headers"].get("Authorization") == "Bearer " + SYNTHETIC_KEY)

    cap = []
    t = transport_for([chat_sse([{"choices": [{"delta": {"content": "网关回复"}}]}, "[DONE]"])], cap)
    r = cur.streamChat(opts(
        baseUrl="https://gateway.example/v1",
        messages=[{"role": "assistant", "content": "此前回答", "responseItems": [REASONING]}],
    ), transport=t)
    check("route_false_gateway_url_is_chat_completions",
          cap[0]["url"] == "https://gateway.example/v1/chat/completions", cap[0]["url"])
    cb = cap[0]["body"]
    check("route_false_gateway_body_is_chat_shape",
          "messages" in cb and "stream_options" in cb
          and ("max_tokens" in cb or "max_completion_tokens" in cb),
          json.dumps(cb, ensure_ascii=False)[:300])
    check("route_false_no_responseItems_leak", "responseItems" not in json.dumps(cb))
    check("route_false_gateway_answer", r.message.get("content") == "网关回复")

    cap = []
    t = transport_for([chat_sse([{"choices": [{"delta": {"content": "gpt5"}}]}, "[DONE]"])], cap)
    cur.streamChat(opts(model="gpt-5"), transport=t)
    check("route_false_gpt5_url_is_chat_completions",
          cap[0]["url"] == "https://api.openai.com/v1/chat/completions", cap[0]["url"])
    check("route_true_trailing_slash_and_case",
          responses.usesResponses("https://api.openai.com/v1///", "GPT-6-LUNA") is True)

    # ---- 4) 冻结 responses.test.ts:30-62 两轮工具回合 golden（独立 fixture） ----
    cap = []
    first_events = completed(
        [REASONING, CALL],
        {"type": "response.output_item.added", "output_index": 1,
         "item": {**CALL, "arguments": ""}},
        {"type": "response.function_call_arguments.delta", "output_index": 1,
         "delta": '{"path":'},
        {"type": "response.function_call_arguments.delta", "output_index": 1,
         "delta": '"中文.ts"}'},
        {"type": "response.output_item.done", "output_index": 1, "item": CALL},
    )
    second_events = completed([ANSWER], {"type": "response.output_text.delta", "delta": "完成"})
    t = transport_for([responses_sse(first_events), responses_sse(second_events)], cap)
    msgs: list[dict[str, Any]] = [
        {"role": "system", "content": "系统"},
        {"role": "user", "content": [
            {"type": "text", "text": "看图并读文件"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,test"}},
        ]},
    ]
    first = cur.streamChat(opts(messages=msgs, tools=TOOLS,
                                extra={"reasoning_effort": "none"}), transport=t)
    check("golden_first_url", cap[0]["url"] == "https://api.openai.com/v1/responses")
    check("golden_first_store_include_tools",
          cap[0]["body"].get("store") is False
          and cap[0]["body"].get("include") == ["reasoning.encrypted_content"]
          and cap[0]["body"]["tools"][0]["strict"] is False)
    check("golden_first_input_image",
          cap[0]["body"]["input"][1]["content"][1]
          == {"type": "input_image", "image_url": "data:image/png;base64,test"})
    check("golden_first_effort_low", cap[0]["body"]["reasoning"] == {"effort": "low"})
    check("golden_first_tool_calls",
          first.message.get("tool_calls") == [{
              "id": "call_1", "type": "function",
              "function": {"name": "Read", "arguments": CALL_ARGUMENTS}}])
    check("golden_first_responseItems", first.message.get("responseItems") == [REASONING])
    check("golden_first_usage_cache",
          first.usage is not None
          and first.usage.get("prompt_cache_hit_tokens") == 80
          and first.usage.get("prompt_cache_miss_tokens") == 20)
    check("golden_first_finish_reason", first.finish_reason == "tool_calls")
    second = cur.streamChat(opts(messages=[
        *msgs, first.message,
        {"role": "tool", "tool_call_id": "call_1", "content": "文件内容"},
    ]), transport=t)
    check("golden_second_input_slice2",
          cap[1]["body"]["input"][2:] == [
              REASONING,
              {"type": "function_call", "call_id": "call_1",
               "name": "Read", "arguments": CALL_ARGUMENTS},
              {"type": "function_call_output", "call_id": "call_1", "output": "文件内容"},
          ], json.dumps(cap[1]["body"]["input"][2:], ensure_ascii=False))
    check("golden_second_answer", second.message.get("content") == "完成")
    check("golden_second_single_content_delta",
          [d["text"] for d in second.deltas if d["kind"] == "content"] == ["完成"])

    summary = {
        "total": len(checks),
        "passed": sum(1 for c in checks if c["pass"]),
        "failed": [c for c in checks if not c["pass"]],
    }
    out = {
        "role": "independent merger (task 05)",
        "baseline": "bbf4aa9:src/ruocun/client/client.py (task-04 baseline, exported pre-run)",
        "checks": checks,
        "summary": summary,
    }
    pathlib.Path(args.output).write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
