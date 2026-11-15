"""为配置的 Hook 保存执行意图和已核实的结果。

先登记意图再运行命令。已有意图而缺少可信结果时，将结果未确认交还调用方核实，避免恢复流程重新触发同一项外部操作。
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Sequence
from dataclasses import asdict
from typing import Any, Protocol

from ..session.contract import ToolResult
from .hooks import HookOutcome, HookRuntime, HookSpec, RunCtx


class HookJournal(Protocol):
    async def intent(self, call_id: str, name: str, args: str, effect: bool) -> ToolResult | None: ...
    async def result(self, call_id: str, text: str) -> None: ...


class HookOutcomeUnknown(RuntimeError):
    """无法确认 Hook 命令的执行结果或其持久化输出。"""


def hookJSON(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode(
        "utf-8", errors="backslashreplace").decode("utf-8")


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest()


def hookIntentId(event: str, identity: str) -> str:
    return f"hook-v1:{event}:{_digest(identity)}"


async def runJournaledHooks(
    runtime: HookRuntime, event: str, identity: str, context: RunCtx, signal: threading.Event,
    journal: HookJournal, *, selected: Sequence[HookSpec] | None = None,
) -> HookOutcome:
    commands = runtime.matching(event, context) if selected is None else selected
    if not commands:
        return HookOutcome()
    call_id = hookIntentId(event, identity)
    name = f"{event}:{context.tool_name}" if context.tool_name is not None else event
    fingerprint = _digest(hookJSON([asdict(spec) for spec in commands]))
    metadata = {"toolCallId": identity, "args": context.args_json, "selection": fingerprint, "cwd": context.cwd}
    if context.tool_name is None:
        metadata["payloadDigest"] = _digest(hookJSON(context.payload))
        metadata["source"] = context.source
    try:
        # 先登记事件和本次命令的身份。恢复时，可用经过校验的旧收据直接返回结果。
        cached = await journal.intent(call_id, name, hookJSON(metadata), True)
        if cached is not None:
            if not isinstance(cached, str):
                raise ValueError("Hook receipt must be text.")
            receipt = json.loads(cached)
            payload = receipt["outcome"]
            if not isinstance(payload, str) or _digest(payload) != receipt["digest"]:
                raise ValueError("Hook receipt differs from the completed output.")
            return HookOutcome(**json.loads(payload))
        # 只有记录接口允许继续且没有可复用的结果时，才实际运行 Hook。
        outcome = await runtime.run(event, context, signal, selected=commands)
        if signal.is_set():
            outcome = HookOutcome(block=True, reason="Hook 已取消，原调用已停止。")
        payload = hookJSON(asdict(outcome))
        await journal.result(call_id, hookJSON({"outcome": payload, "digest": _digest(payload)}))
        return outcome
    except Exception as error:
        raise HookOutcomeUnknown(f"{event} 执行或结果未确认，原现场保留，未重新运行 Hook。") from error
