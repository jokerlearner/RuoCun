"""Hook configuration and command protocol (MIT)."""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import threading
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from ..config.compat import resolve_env
from ..permissions.engine import matchesIfClause
from ..permissions.secrets import redactSecrets
from ..platform.file_contract import AtomicFileError
from ..platform.process_tree import ForegroundResult, run_foreground_argv
from ..platform.shell_plan import buildShellPlan
from ..platform.windows.durable_file import atomic_publish, local_path

HookDecision = Literal["allow", "ask", "deny"]
_STRENGTH: dict[HookDecision, int] = {"allow": 0, "ask": 1, "deny": 2}
_MAX_OUTPUT = 4 * 1024 * 1024


@dataclass(frozen=True)
class HookFileRef:
    path: Path
    plugin_root: str | None = None


@dataclass(frozen=True)
class HookSpec:
    event: str
    matcher: str | None = None
    if_clause: str | None = None
    type: str = "command"
    command: str | None = None
    url: str | None = None
    prompt: str | None = None
    async_: bool = False
    timeout: float | None = None
    plugin_root: str | None = None


@dataclass(frozen=True)
class HookOutcome:
    block: bool = False
    reason: str = ""
    additional_context: str = ""
    permission_decision: HookDecision | None = None
    updated_input: dict[str, Any] | list[Any] | None = None


@dataclass(frozen=True)
class RunCtx:
    cwd: str
    tool_name: str | None = None
    args_json: str | None = None
    source: str | None = None
    payload: Any = None


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _invalid_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode(
        "utf-8", errors="backslashreplace")


def parseHookOutput(stdout: str, stderr: str, code: int) -> HookOutcome:
    if code == 2:
        return HookOutcome(block=True, reason=(stderr or stdout).strip())
    text = stdout.strip()
    if code != 0 or not text:
        return HookOutcome()
    try:
        raw = json.loads(text, parse_constant=_invalid_constant)
    except ValueError:
        return HookOutcome(additional_context=text)
    if raw is None:
        return HookOutcome(additional_context=text)
    if not isinstance(raw, dict):
        return HookOutcome()
    nested = raw.get("hookSpecificOutput")
    detail = nested if isinstance(nested, dict) else {}
    context = next((value for value in (detail.get("additionalContext"), raw.get("additionalContext"),
                                        raw.get("additional_context")) if value is not None), None)
    decision = detail.get("permissionDecision")
    updated = detail.get("updatedInput")
    if updated is None:
        updated = raw.get("updatedInput")
    return HookOutcome(
        additional_context=_string(context) or "",
        permission_decision=cast(HookDecision, decision) if decision in ("allow", "ask", "deny") else None,
        updated_input=updated if isinstance(updated, (dict, list)) else None,
    )


def loadHooks(refs: Sequence[HookFileRef]) -> list[HookSpec]:
    specs: list[HookSpec] = []
    for ref in refs:
        try:
            raw = json.loads(ref.path.read_text("utf-8"), parse_constant=_invalid_constant)
        except (OSError, ValueError):
            continue
        if not isinstance(raw, dict):
            continue
        events = raw["hooks"] if isinstance(raw.get("hooks"), dict) else raw
        for event, groups in events.items():
            if not isinstance(groups, list):
                continue
            for group in groups:
                if not isinstance(group, dict):
                    continue
                inner = group["hooks"] if isinstance(group.get("hooks"), list) else [group]
                for entry in inner:
                    if not isinstance(entry, dict):
                        continue
                    timeout = entry.get("timeout")
                    kind = entry.get("type")
                    specs.append(HookSpec(
                        event=event, matcher=_string(group.get("matcher")),
                        if_clause=_string(entry.get("if")) if isinstance(entry.get("if"), str) else _string(group.get("if")),
                        type="command" if kind is None else kind if isinstance(kind, str) else "unsupported",
                        command=_string(entry.get("command")), url=_string(entry.get("url")),
                        prompt=_string(entry.get("prompt")), async_=entry.get("async") is True,
                        timeout=timeout if type(timeout) in (int, float) else None, plugin_root=ref.plugin_root,
                    ))
    return specs


def selectHooks(
    specs: Sequence[HookSpec], event: str, *, tool_name: str | None = None,
    args_json: str | None = None, source: str | None = None,
) -> list[HookSpec]:
    selected = []
    target = source if event == "SessionStart" else tool_name
    for spec in specs:
        if spec.event != event:
            continue
        if spec.matcher:
            if not target:
                continue
            # JS RegExp's named captures and ASCII word/character classes.
            pattern = re.sub(r"\(\?<([A-Za-z_]\w*)>", r"(?P<\1>", spec.matcher)
            pattern = re.sub(r"\\k<([A-Za-z_]\w*)>", r"(?P=\1)", pattern)
            try:
                if re.search(pattern, target, re.ASCII) is None:
                    continue
            except re.error as error:
                raise ValueError("Hook matcher 无效或当前正则端口不支持。") from error
        if spec.if_clause and tool_name and not matchesIfClause(spec.if_clause, tool_name, args_json or "{}"):
            continue
        selected.append(spec)
    return selected


def hooksReport(specs: Sequence[HookSpec]) -> str:
    if not specs:
        return ("未配置 hooks。可在用户目录的 ~/.ruocun/hooks.json 或项目的 .ruocun/hooks.json 注册处理程序。"
                "支持 PreToolUse、PostToolUse、UserPromptSubmit、SessionStart 和 SessionEnd。")
    rows = [f"  {s.event}{f'[{s.matcher}]' if s.matcher else ''}: {s.command if s.type == 'command' else s.type}"
            for s in specs]
    return redactSecrets("已配置 hooks:\n" + "\n".join(rows))


class _HookSignal(threading.Event):
    def __init__(self, parent: threading.Event, timeout: float | None) -> None:
        super().__init__()
        if timeout is not None and (not math.isfinite(timeout) or timeout < 0):
            raise ValueError("Hook timeout 必须是有限非负毫秒数。")
        self.parent = parent
        self.deadline = None if timeout == 0 else time.monotonic() + (30000 if timeout is None else timeout) / 1000

    def is_set(self) -> bool:
        return (super().is_set() or self.parent.is_set()
                or self.deadline is not None and time.monotonic() >= self.deadline)


class HookRuntime:
    def __init__(
        self, specs: Sequence[HookSpec], env: Mapping[str, str], *,
        audit_dir: Path | None = None, redact: Callable[[str], str] | None = None,
    ) -> None:
        self.specs = tuple(specs)
        self.env = env
        self._audit_dir = audit_dir if resolve_env("AUDIT", env) != "0" else None
        self._redact = redact if redact is not None else str

    def redacted(self, value: str) -> str:
        return redactSecrets(self._redact(value))

    def matching(self, event: str, ctx: RunCtx) -> tuple[HookSpec, ...]:
        return tuple(spec for spec in selectHooks(self.specs, event, tool_name=ctx.tool_name,
                                                  args_json=ctx.args_json, source=ctx.source)
                     if spec.type == "command" and spec.command)

    async def audit(self, event: str, tool: str, args: str, status: str) -> None:
        if self._audit_dir is None:
            return
        payload = {"ts": time.time_ns() // 1_000_000, "event": event, "tool": self.redacted(tool),
                   "args": self.redacted(args)[:2048], "status": status}
        directory = self._audit_dir / "hook-audit"
        file = directory / f"{time.time_ns()}-{uuid.uuid4().hex}.json"

        def write() -> None:
            data = _json_bytes(payload) + b"\n"
            if os.name == "nt":
                atomic_publish(local_path(file), data, require_durability=False)
            else:
                directory.mkdir(mode=0o700, parents=True, exist_ok=True)
                if directory.is_symlink() or directory.stat().st_mode & 0o077:
                    return
                fd = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)

        try:
            await asyncio.to_thread(write)
        except (OSError, AtomicFileError):
            pass  # An observation failure never changes the durable tool receipt.

    async def _command(self, spec: HookSpec, event: str, ctx: RunCtx, signal: threading.Event) -> ForegroundResult:
        assert spec.command is not None
        env = dict(self.env)
        env.update(RUOCUN_HOOK_EVENT=event, CLAUDE_PROJECT_DIR=ctx.cwd)
        if ctx.tool_name:
            env["RUOCUN_TOOL_NAME"] = ctx.tool_name
        else:
            env.pop("RUOCUN_TOOL_NAME", None)
        if spec.plugin_root:
            env.update(CLAUDE_PLUGIN_ROOT=spec.plugin_root, RUOCUN_PLUGIN_ROOT=spec.plugin_root)
        else:
            for name in ("CLAUDE_PLUGIN_ROOT", "RUOCUN_PLUGIN_ROOT"):
                env.pop(name, None)
        process_signal = _HookSignal(signal, spec.timeout)
        plan = buildShellPlan(spec.command, ctx.cwd, analyze=False, environ=env)
        task = asyncio.create_task(asyncio.to_thread(
            run_foreground_argv, list(plan.argv), plan.cwd, process_signal, environ=dict(plan.environment),
            commandLine=plan.commandLine, codec="utf-8", stdinData=_json_bytes(ctx.payload if ctx.payload is not None else {}),
            outputLimit=_MAX_OUTPUT,
        ))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            process_signal.set()
            await asyncio.shield(task)
            raise

    async def run(
        self, event: str, ctx: RunCtx, signal: threading.Event, *, selected: Sequence[HookSpec] | None = None,
    ) -> HookOutcome:
        reasons, contexts = [], []
        block = False
        decision: HookDecision | None = None
        updated: dict[str, Any] | list[Any] | None = None
        for spec in self.matching(event, ctx) if selected is None else selected:
            if signal.is_set():
                break
            result = await self._command(spec, event, ctx, signal)
            status = "cancelled" if signal.is_set() else "timeout" if result.aborted else (
                "output-limit" if result.outputCapped else f"exit-{result.code}")
            await self.audit(event, ctx.tool_name or "", ctx.args_json or "", status)
            if result.aborted or result.outputCapped:
                continue
            parsed = parseHookOutput(result.stdout, result.stderr, result.code)
            block |= parsed.block
            if parsed.reason:
                reasons.append(parsed.reason)
            if parsed.additional_context:
                contexts.append(parsed.additional_context)
            current = parsed.permission_decision
            if current is not None and (decision is None or _STRENGTH[current] > _STRENGTH[decision]):
                decision = current
            if parsed.updated_input is not None:
                updated = parsed.updated_input
        return HookOutcome(block, "\n".join(reasons), "\n".join(contexts), decision, updated)
