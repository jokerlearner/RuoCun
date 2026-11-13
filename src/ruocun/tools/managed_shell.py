"""D08 independent Shell controller, adapted from frozen managed_shell.ts (MIT)."""
from __future__ import annotations

import asyncio
import codecs
import hashlib
import os
import secrets
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Protocol, TypeVar, cast

from ..platform.process_tree import ForegroundResult, OutputCallback, scrubbed_env
from ..platform.sandbox import SandboxUnavailable, sandboxExecutionPlan
from ..platform.shell_plan import ShellExecutionPlan
from ..platform.windows.durable_file import (
    PrivateDirectory,
    atomic_publish,
    ensure_private_dir,
    local_path,
    verify_private_file,
)
from ..session.contract import RunRecord, RunRef
from ..session.process_identity import identity_alive, process_identity
from ..version import __version__
from .shell_runner import (
    PROTOCOL_VERSION,
    TERMINAL,
    digest,
    identity,
    package_files,
    plan_payload,
    read_signed,
    validate_manifest,
    validate_terminal,
    write_signed,
)
from .types import ToolRejected

if TYPE_CHECKING:
    from ..agent.background_runtime import BackgroundRuntime

_T = TypeVar("_T")
_READ_LIMIT = 16000
_STREAMS: tuple[Literal["stdout", "stderr"], ...] = ("stdout", "stderr")


class ShellRunStore(Protocol):
    async def prepare(self, run_ref: RunRef, snapshot: dict[str, Any]) -> RunRecord: ...
    async def commit(self, record: RunRecord) -> None: ...
    async def recover(self) -> tuple[RunRecord, ...]: ...


@dataclass
class _Run:
    record: RunRecord
    manifest: dict[str, Any]
    capability: bytes
    stdout_cursor: int = 0
    stderr_cursor: int = 0
    terminal: dict[str, Any] | None = None
    ui_stdout: int = 0
    ui_stderr: int = 0
    poll_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    publication_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    foreground_control: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def directory(self) -> Path:
        return local_path(Path(self.record.snapshot["run_dir"]))


class ManagedShellManager:
    def __init__(
        self, session_dir: Path, session_id: str, store: ShellRunStore, *,
        runner_command: Sequence[str] | None = None, helper_command: Sequence[str] | None = None,
    ) -> None:
        self.directory, self.session_id, self.store = local_path(session_dir), session_id, store
        self.runner_command = tuple(runner_command) if runner_command is not None else (
            sys.executable, "-I", "-X", "utf8", "-m", "ruocun", "--ruocun-shell-runner")
        self.helper_command = tuple(helper_command) if helper_command is not None else None
        self._runs: dict[str, _Run] = {}
        self._launchers: dict[str, subprocess.Popen[bytes]] = {}
        self._ports: set[asyncio.Task[Any]] = set()
        self._foreground: str | None = None
        self._closed = False
        self._background: BackgroundRuntime | None = None
        self.recovery_errors: dict[str, str] = {}
        self._recovery_unconfirmed = False

    @asynccontextmanager
    async def recovery_decision_scope(self) -> AsyncIterator[None]:
        """Fence the observer while committing a user's attestation; never forge a receipt."""
        entries = tuple(self._runs.values())
        acquired: list[_Run] = []
        try:
            for entry in entries:
                await entry.publication_lock.acquire()
                acquired.append(entry)
            yield
        finally:
            try:
                by_id = {record.run_ref.run_id: record for record in await self.store.recover()}
                for entry in entries:
                    record = by_id.get(entry.record.run_ref.run_id)
                    if record is not None and record.snapshot.get("resolved_by_user"):
                        entry.record = record
            except BaseException:
                self._recovery_unconfirmed = True
                raise
            finally:
                for entry in reversed(acquired):
                    entry.publication_lock.release()

    async def _port(self, operation: Callable[..., _T], *args: Any, **kwargs: Any) -> _T:
        task = asyncio.create_task(asyncio.to_thread(operation, *args, **kwargs))
        self._ports.add(task)

        def done(future: asyncio.Task[Any]) -> None:
            self._ports.discard(future)
            if not future.cancelled():
                future.exception()

        task.add_done_callback(done)
        return await asyncio.shield(task)

    async def _commit(self, entry: _Run, *, status: str | None = None, **snapshot: Any) -> None:
        # Update before await: an accepted DB operation may outlive cancellation.
        entry.record = replace(entry.record, status=status or entry.record.status,
                               snapshot={**entry.record.snapshot, **snapshot})
        await self.store.commit(entry.record)

    def _validate_state(self, entry: _Run, state: dict[str, Any]) -> None:
        for name in ("version", "session_id", "run_id", "task_id", "launch_id", "plan_digest"):
            if state.get(name) != entry.manifest.get(name):
                raise ValueError("runner响应执行身份不匹配。")
        current = identity(state.get("runner_identity"))
        recorded = entry.record.snapshot.get("runner_identity")
        if recorded is not None and asdict(current) != recorded:
            raise ValueError("runner身份已改变，拒绝接管新进程。")
        epoch = state.get("control_epoch")
        if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < entry.record.snapshot["control_epoch"]:
            raise ValueError("runner响应控制租约已过期。")

    def _state(self, entry: _Run) -> dict[str, Any]:
        state = read_signed(entry.directory / "runner-state.json", entry.capability)
        self._validate_state(entry, state)
        return state

    def _terminal(self, entry: _Run) -> dict[str, Any] | None:
        if entry.terminal is not None:
            return entry.terminal
        file = entry.directory / "terminal.json"
        if not file.exists():
            return None
        receipt = read_signed(file, entry.capability)
        known_identity = entry.record.snapshot.get("runner_identity")
        if known_identity is None:
            known_identity = self._state(entry)["runner_identity"]
        validate_terminal(receipt, entry.manifest, entry.directory, known_identity)
        published = read_signed(entry.directory / "runner-state.json", entry.capability)
        if published.get("phase") != "terminal":
            if identity_alive(identity(receipt["runner_identity"])):
                return None
            raise RuntimeError("runner终态收据发布尚未确认。")
        if (published.get("status") != receipt.get("status")
                or published.get("logs") != receipt.get("logs") or published.get("closed") is not True):
            raise RuntimeError("runner终态收据发布确认不匹配。")
        return receipt

    async def _accept_terminal(self, entry: _Run, receipt: dict[str, Any], *, recover: bool = False) -> None:
        entry.terminal = receipt
        metadata: dict[str, Any] = {
            "phase": "terminal", "receipt_digest": hashlib.sha256((entry.directory / "terminal.json").read_bytes()).hexdigest(),
            "runner_identity": receipt["runner_identity"], "code": receipt.get("code"), "closed": True,
        }
        if recover and "tool_result" not in entry.record.snapshot:
            metadata["tool_result"] = self._recovery_ack(entry.record.run_ref.run_id)
        await self._commit(entry, status=receipt["status"], **metadata)

    @staticmethod
    def _recovery_ack(run_id: str) -> str:
        return f"原Shell执行已恢复，任务id: {run_id}。使用BashOutput读取输出；未重新执行命令。"

    async def _unknown(self, entry: _Run, error: BaseException) -> None:
        if entry.record.status in TERMINAL or entry.record.status == "failed-before-grant":
            return
        await self._commit(entry, status="unknown", phase="outcome-unconfirmed", error_type=type(error).__name__)

    async def _rpc(self, entry: _Run, action: str) -> dict[str, Any]:
        from ..platform.windows.ipc import request
        await self.store.commit(entry.record)  # Fence a stale DB owner before control.
        snapshot = entry.record.snapshot
        helper = identity(snapshot["server_helper_identity"])
        if not identity_alive(helper):
            raise RuntimeError("runner transport helper不存在，等待同run重连。")
        payload = {
            **{name: entry.manifest[name] for name in ("version", "session_id", "run_id", "launch_id", "plan_digest")},
            "action": action, "control_epoch": snapshot["control_epoch"],
            "owner_identity": snapshot["owner_identity"],
        }
        result = await self._port(request, snapshot["endpoint"], entry.capability, payload,
                                  expected_server_pid=helper.pid, deadline=time.monotonic() + 3,
                                  helper_command=self.helper_command)
        self._validate_state(entry, result)
        return result

    async def _connect(self, entry: _Run, *, adopt: bool = False) -> dict[str, Any]:
        state = await self._port(self._state, entry)
        if not identity_alive(identity(state["runner_identity"])):
            raise RuntimeError("runner不存在；已有启动许可的命令不会重新执行。")
        helper = identity(state["server_helper_identity"])
        owner = process_identity()
        if owner is None:
            raise RuntimeError("controller真实身份不可用。")
        changed = adopt or state["owner_identity"] != asdict(owner) or state["control_epoch"] > entry.record.snapshot["control_epoch"]
        epoch = max(state["control_epoch"], entry.record.snapshot["control_epoch"]) + (1 if changed else 0)
        await self._commit(entry, runner_identity=state["runner_identity"],
                           server_helper_identity=asdict(helper), endpoint=state["endpoint"],
                           control_epoch=epoch, owner_identity=asdict(owner), phase=state["phase"])
        reply = await self._rpc(entry, "adopt" if changed else "status")
        if reply["status"] in TERMINAL:
            receipt = await self._port(self._terminal, entry)
            if receipt is None:
                raise RuntimeError("runner报告终态但缺少可信收据。")
            await self._accept_terminal(entry, receipt)
        else:
            await self._commit(entry, status=reply["status"], phase=reply["phase"],
                               detached=bool(reply.get("detached", False)))
        return reply

    def _create_files(self, entry: _Run) -> None:
        runs = self.directory / "runs"
        ensure_private_dir(runs)
        if entry.directory.exists():
            raise ValueError("runner目录已存在，拒绝覆盖。")
        ensure_private_dir(entry.directory)
        with PrivateDirectory(entry.directory):
            atomic_publish(entry.directory / "capability", entry.capability)
            write_signed(entry.directory / "manifest.json", entry.manifest, entry.capability)

    async def _spawn(self, entry: _Run) -> None:
        def spawn() -> subprocess.Popen[bytes]:
            with (entry.directory / "runner.log").open("ab", buffering=0) as log:
                return subprocess.Popen(
                    [*self.runner_command, str(entry.directory)], cwd=entry.manifest["plan"]["cwd"],
                    env=scrubbed_env(), stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                    close_fds=True, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                )

        task = asyncio.create_task(asyncio.to_thread(spawn))
        self._ports.add(task)

        def bind(future: asyncio.Task[subprocess.Popen[bytes]]) -> None:
            self._ports.discard(future)
            if not future.cancelled() and future.exception() is None:
                self._launchers[entry.record.run_ref.run_id] = future.result()

        task.add_done_callback(bind)
        await asyncio.shield(task)

    async def _start(self, plan: ShellExecutionPlan, signal: threading.Event) -> _Run:
        if self._closed or os.name != "nt":
            raise ToolRejected("当前环境未提供可恢复Shell执行后端，命令未执行。")
        run_id = str(uuid.uuid4())
        reference = RunRef("proc-" + run_id[:8], run_id)
        run_dir = local_path(self.directory / "runs" / run_id)
        plan_data = plan_payload(plan)
        owner = process_identity()
        if owner is None:
            raise ToolRejected("controller真实身份不可用，命令未执行。")
        manifest = {
            "version": PROTOCOL_VERSION, "package_version": __version__, "package_files": package_files(),
            "session_id": self.session_id, "task_id": reference.task_id, "run_id": run_id,
            "launch_id": uuid.uuid4().hex, "plan_digest": digest(plan_data), "plan": plan_data,
            "endpoint": r"\\.\pipe\ruocun-shell-" + uuid.uuid4().hex, "owner_identity": asdict(owner),
        }
        if self.helper_command is not None:
            manifest["helper_command"] = list(self.helper_command)
        snapshot = {
            "version": PROTOCOL_VERSION, "phase": "intent", "launch_id": manifest["launch_id"],
            "plan_digest": manifest["plan_digest"], "run_dir": str(run_dir), "endpoint": None,
            "control_epoch": 0, "owner_identity": asdict(owner), "detached": False,
        }
        record = await self.store.prepare(reference, snapshot)
        entry = _Run(record, manifest, secrets.token_bytes(32))
        self._runs[run_id] = entry
        try:
            await self._port(self._create_files, entry)
            if signal.is_set():
                raise ToolRejected("启动前已取消，命令未执行。")
            await self._spawn(entry)
            deadline = time.monotonic() + 10
            while not (run_dir / "runner-state.json").exists():
                if signal.is_set():
                    raise ToolRejected("runner启动等待已取消，命令未执行。")
                launcher = self._launchers.get(run_id)
                if launcher is not None and launcher.poll() is not None:
                    raise RuntimeError(f"runner bootstrap退出（exit={launcher.returncode}）。")
                if time.monotonic() >= deadline:
                    raise TimeoutError("runner bootstrap超时。")
                await asyncio.sleep(.025)
            await self._connect(entry)
            if signal.is_set():
                raise ToolRejected("授予执行许可前已取消，命令未执行。")
            await self._commit(entry, phase="grant-possible")
            grant = {
                **{name: manifest[name] for name in ("version", "session_id", "task_id", "run_id", "launch_id", "plan_digest")},
                "owner_identity": entry.record.snapshot["owner_identity"],
                "control_epoch": entry.record.snapshot["control_epoch"],
            }
            await self._port(write_signed, run_dir / "grant.json", grant, entry.capability)
            response = await self._rpc(entry, "start")
            if response.get("started") is not True:
                raise RuntimeError("runner未确认启动认领，不重复执行。")
            await self._commit(entry, status="running", phase="started")
            return entry
        except BaseException as error:
            if isinstance(error, asyncio.CancelledError):
                signal.set()
            try:
                terminal = await self._port(self._terminal, entry)
            except (OSError, ValueError, RuntimeError):
                terminal = None
            if terminal is not None:
                await self._accept_terminal(entry, terminal)
                return entry
            if (entry.record.snapshot.get("phase") not in ("grant-possible", "started", "canceling", "terminal")
                    and not (run_dir / "grant.json").exists() and not (run_dir / "start.claim").exists()):
                log = run_dir / "runner.log"
                diagnostic = f"诊断位于 {log}" if log.is_file() else "runner日志尚未创建，请保留运行目录核实"
                message = f"命令未执行：runner启动失败（{type(error).__name__}）；{diagnostic}。"
                await self._commit(entry, status="failed-before-grant", phase="failed-before-grant",
                                   tool_result="Error: " + message)
                raise ToolRejected(message) from error
            await self._unknown(entry, error)
            raise RuntimeError("Shell启动结果未确认，已保留现场，拒绝重新启动。") from error

    @staticmethod
    def _read_text(entry: _Run, name: str, cursor: int) -> tuple[str, int]:
        path = entry.directory / name
        verify_private_file(path)
        with path.open("rb") as data:
            data.seek(cursor)
            raw = data.read(_READ_LIMIT)
        decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
        text = decoder.decode(raw, final=False)
        return text, cursor + len(raw) - len(decoder.getstate()[0])

    @staticmethod
    def _slice_units(text: str, budget: int, *, tail: bool = False) -> str:
        raw = text.encode("utf-16-le")
        if len(raw) <= budget * 2:
            return text
        raw = raw[-budget * 2:] if tail else raw[:budget * 2]
        if tail and 0xDC00 <= int.from_bytes(raw[:2], "little") <= 0xDFFF:
            raw = raw[2:]
        elif not tail and 0xD800 <= int.from_bytes(raw[-2:], "little") <= 0xDBFF:
            raw = raw[:-2]
        return raw.decode("utf-16-le")

    @staticmethod
    def _read_window(entry: _Run, name: str, cursor: int) -> tuple[str, int]:
        path = entry.directory / name
        verify_private_file(path)
        decoder = codecs.getincrementaldecoder("utf-8")(errors="strict")
        head = tail = small = ""
        total = 0
        with path.open("rb") as data:
            end = os.fstat(data.fileno()).st_size
            data.seek(cursor)
            while data.tell() < end:
                raw = data.read(min(65536, end - data.tell()))
                if not raw:
                    break
                text = decoder.decode(raw, final=False)
                total += len(text.encode("utf-16-le")) // 2
                head = ManagedShellManager._slice_units(head + text, 12000)
                tail = ManagedShellManager._slice_units(tail + text, 8000, tail=True)
                small = small + text if total <= 20000 else ""
            consumed = data.tell() - len(decoder.getstate()[0])
        if total <= 20000:
            return small, consumed
        omitted = total - len(head.encode("utf-16-le")) // 2 - len(tail.encode("utf-16-le")) // 2
        label = "stdout" if name.startswith("stdout") else "stderr"
        return f"{head}\n…[{label}共 {total} 字符,已截断,中间省略 {omitted} 字符]…\n{tail}", consumed

    async def poll(self, run_id: str, *, incremental: bool = False) -> dict[str, Any]:
        entry = self._runs.get(run_id)
        if entry is None:
            return {"id": run_id, "status": "not-found", "stdout": "", "stderr": ""}
        if entry.record.snapshot.get("resolved_by_user"):
            return {"id": run_id, "status": "resolved-by-user", "stdout": "[用户核实，非runner收据] " + str(entry.record.snapshot.get("user_evidence", "")), "stderr": ""}
        async with entry.poll_lock:
            return await self._poll(run_id, incremental=incremental)

    async def _refresh(self, entry: _Run, *, verify_owner: bool = True) -> None:
        receipt = await self._port(self._terminal, entry)
        if receipt is not None:
            await self._accept_terminal(entry, receipt)
        elif entry.record.status not in TERMINAL and entry.record.status != "failed-before-grant":
            last_error: BaseException | None = None
            for attempt in range(3):
                try:
                    response = await self._port(self._state, entry)
                    cached = entry.record.snapshot
                    if (response["control_epoch"] != cached["control_epoch"]
                            or response.get("server_helper_identity") != cached.get("server_helper_identity")):
                        response = await self._connect(entry)
                    elif not identity_alive(identity(response["runner_identity"])):
                        raise RuntimeError("runner执行器不存在。")
                    elif verify_owner:
                        await self.store.commit(entry.record)
                    if response.get("status") == "unknown" or response.get("transport_error"):
                        raise RuntimeError("runner执行结果未确认。")
                    last_error = None
                    break
                except (OSError, ValueError, RuntimeError) as error:
                    last_error = error
                    await asyncio.sleep(.05 * (attempt + 1))
            if last_error is not None:
                await self._unknown(entry, last_error)

    async def _poll(self, run_id: str, *, incremental: bool = False) -> dict[str, Any]:
        entry = self._runs.get(run_id)
        if entry is None:
            return {"id": run_id, "status": "not-found", "stdout": "", "stderr": ""}
        await self._refresh(entry)
        stdout = stderr = ""
        read = self._read_text if incremental else self._read_window
        if (entry.directory / "stdout.txt").exists():
            stdout, next_stdout = await self._port(read, entry, "stdout.txt", entry.ui_stdout if incremental else entry.stdout_cursor)
            if incremental:
                entry.ui_stdout = next_stdout
            else:
                entry.stdout_cursor = next_stdout
        if (entry.directory / "stderr.txt").exists():
            stderr, next_stderr = await self._port(read, entry, "stderr.txt", entry.ui_stderr if incremental else entry.stderr_cursor)
            if incremental:
                entry.ui_stderr = next_stderr
            else:
                entry.stderr_cursor = next_stderr
        return {"id": run_id, "status": entry.record.status, "stdout": stdout, "stderr": stderr,
                "exitCode": entry.record.snapshot.get("code"), "runnerDir": str(entry.directory),
                "stdout_cursor": entry.stdout_cursor, "stderr_cursor": entry.stderr_cursor}

    def bind_background(self, runtime: BackgroundRuntime) -> None:
        if runtime.sessionId != self.session_id or runtime.store is not self.store:
            raise ValueError("后台收件箱与Shell会话存储不匹配。")
        self._background = runtime

    async def _publish_background(self, entry: _Run) -> None:
        from ..agent.background_types import (
            ExecutionEvent,
            ExecutionSnapshot,
            ExecutionStatus,
        )
        runtime = self._background
        if runtime is None:
            return
        async with entry.publication_lock:
            if entry.record.snapshot.get("resolved_by_user") or self._recovery_unconfirmed:
                return
            if runtime.fault is not None:
                raise RuntimeError("后台运行登记未确认，保留原run。") from runtime.fault
            await self._refresh(entry, verify_owner=False)
            status, run_id = entry.record.status, entry.record.run_ref.run_id
            if status not in TERMINAL | {"running", "canceling", "unknown"}:
                raise RuntimeError("后台运行尚未确认可等待状态。")
            cached = runtime.snapshot(run_id)
            if cached is not None and cached.status == status:
                return
            text = None
            if status in TERMINAL:
                receipt = await self._port(self._terminal, entry)
                if receipt is None:
                    raise RuntimeError("后台完成缺少可信关闭收据。")
                for name, facts in receipt["logs"].items():
                    await runtime.attachFile(entry.directory / name, facts["sha256"])
                stdout, _ = await self._port(self._read_window, entry, "stdout.txt", 0)
                stderr, _ = await self._port(self._read_window, entry, "stderr.txt", 0)
                text = stdout + ("\n[stderr]\n" + stderr if stderr else "")
                text += f"\n[exit {receipt['code']}; 完整日志:{entry.directory}]"
            elif status == "unknown":
                text = "执行结果未确认，原run与日志保留；未重新启动命令。"
            snapshot = ExecutionSnapshot(entry.record.run_ref.task_id, run_id, "shell", True,
                str(entry.manifest.get("description") or entry.manifest["plan"]["command"]),
                cast(ExecutionStatus, status), text, "runner", str(entry.directory))
            if status in TERMINAL:
                await runtime.publish(ExecutionEvent(cast(Any, status), snapshot), entry.record, import_receipt=True)
            elif status == "unknown":
                if cached is None:
                    await runtime.publish(ExecutionEvent("started", snapshot), entry.record)
                await runtime.publish(ExecutionEvent("unknown", snapshot, requiresAttention=True,
                                                     eventId=run_id+":recovery-unknown"), entry.record)
            else:
                await runtime.publish(ExecutionEvent("progress" if cached else "started", snapshot), entry.record)
            if runtime.fault is not None:
                raise RuntimeError("后台运行登记未确认，保留原run。") from runtime.fault

    async def _confirm_background_ack(self, entry: _Run) -> None:
        await self._publish_background(entry)
        if entry.record.status not in TERMINAL | {"running", "canceling"}:
            raise RuntimeError("Shell执行结果未确认，原run与事件已保留，不生成普通成功回执。")

    async def observe_background(self, runtime: BackgroundRuntime, stop: asyncio.Event | None = None) -> None:
        self.bind_background(runtime)
        while not self._closed and (stop is None or not stop.is_set()):
            if runtime.fault is not None:
                return
            for entry in tuple(self._runs.values()):
                if not entry.record.snapshot.get("detached"):
                    continue
                try:
                    await self._publish_background(entry)
                except asyncio.CancelledError:
                    raise
                except (OSError, ValueError, RuntimeError, KeyError) as error:
                    runtime.fail(error)
                    return
            if stop is None:
                await asyncio.sleep(.25)
            else:
                try:
                    await asyncio.wait_for(stop.wait(), .25)
                except TimeoutError:
                    pass

    async def detach(self, run_id: str) -> dict[str, Any]:
        entry = self._runs[run_id]
        receipt = await self._port(self._terminal, entry)
        if receipt is not None:
            await self._accept_terminal(entry, receipt)
            await self._commit(entry, detached=True, detach_requested=True)
            return {"id": run_id, "status": entry.record.status, "detached": True}
        # A durable decision precedes loss of foreground cancellation ownership.
        await self._commit(entry, detach_requested=True)
        try:
            result = await self._rpc(entry, "detach")
        except (OSError, ValueError, RuntimeError):
            receipt = await self._port(self._terminal, entry)
            if receipt is None:
                raise
            await self._accept_terminal(entry, receipt)
            result = {"detached": True}
        if result.get("detached") is not True:
            raise RuntimeError("runner未确认保留许可。")
        await self._commit(entry, detached=True)
        return {"id": run_id, "status": entry.record.status, "detached": True}

    async def detach_foreground(self) -> bool:
        run_id = self._foreground
        if run_id is None:
            return False
        entry = self._runs[run_id]
        async with entry.foreground_control:
            if (self._foreground != run_id or entry.record.status != "running"
                    or entry.record.cancel_requested or entry.record.snapshot.get("detach_requested")):
                return False
            try:
                await self.detach(run_id)
                await self._confirm_background_ack(entry)
            except (OSError, ValueError, RuntimeError) as error:
                await self._unknown(entry, error)
                raise
            return True

    async def _cancel_foreground(self, entry: _Run) -> bool:
        async with entry.foreground_control:
            if entry.record.snapshot.get("detach_requested"):
                return False
            await self.cancel(entry.record.run_ref.run_id)
            return True

    def _authenticated_control_state(self, entry: _Run) -> dict[str, Any]:
        # Unknown recovery may carry only a DB record, never control credentials.
        if not entry.manifest or len(entry.capability) != 32:
            raise ValueError("未知执行缺少已认证控制材料。")
        verify_private_file(entry.directory / "capability")
        if not secrets.compare_digest((entry.directory / "capability").read_bytes(), entry.capability):
            raise ValueError("执行控制材料已经变化。")
        manifest = read_signed(entry.directory / "manifest.json", entry.capability)
        validate_manifest(manifest, session_id=self.session_id, run_id=entry.record.run_ref.run_id,
                          task_id=entry.record.run_ref.task_id, launch_id=entry.record.snapshot["launch_id"],
                          plan_digest=entry.record.snapshot["plan_digest"])
        if manifest != entry.manifest or entry.record.snapshot.get("runner_identity") is None:
            raise ValueError("未知执行缺少原执行器身份。")
        state = self._state(entry)
        current = process_identity()
        if current is None or not identity_alive(identity(state["runner_identity"])):
            raise RuntimeError("原执行器或当前控制器身份未确认。")
        owner = asdict(current)
        if (state["owner_identity"] != owner or entry.record.snapshot["owner_identity"] != owner
                or state["control_epoch"] != entry.record.snapshot["control_epoch"]):
            raise RuntimeError("未知执行尚未确认当前控制租约。")
        return state

    async def cancel(self, run_id: str) -> dict[str, Any]:
        entry = self._runs.get(run_id)
        if entry is None:
            return {"id": run_id, "status": "not-found"}
        if entry.record.snapshot.get("resolved_by_user"):
            return {"id": run_id, "status": "resolved-by-user", "reason": "用户已核实处理，未向原执行发送取消。"}
        if self._recovery_unconfirmed:
            return {"id": run_id, "status": "unknown", "reason": "恢复提交未确认，保留现场，未发出控制。"}
        if entry.record.status in TERMINAL | {"failed-before-grant"}:
            return {"id": run_id, "status": entry.record.status}
        try:
            if not entry.manifest or len(entry.capability) != 32:
                raise ValueError("未知执行缺少已认证控制材料。")
            receipt = await self._port(self._terminal, entry)
            if receipt is not None:
                await self._accept_terminal(entry, receipt)
                return {"id": run_id, "status": entry.record.status}
            if entry.record.status == "unknown":
                await self._port(self._authenticated_control_state, entry)
        except (OSError, ValueError, RuntimeError, KeyError) as error:
            if entry.record.status != "unknown":
                await self._unknown(entry, error)
            return {"id": run_id, "status": entry.record.status,
                    "reason": "原执行或控制材料未确认，保留现场，未发出取消控制。"}
        entry.record = replace(entry.record, cancel_requested=True)
        await self._commit(entry, status="canceling", phase="canceling")
        payload = {
            **{name: entry.manifest[name] for name in ("version", "session_id", "run_id", "launch_id", "plan_digest")},
            "action": "cancel", "control_epoch": entry.record.snapshot["control_epoch"],
            "owner_identity": entry.record.snapshot["owner_identity"],
        }
        await self._port(write_signed, entry.directory / "cancel.json", payload, entry.capability)
        try:
            await self._rpc(entry, "cancel")
        except (OSError, ValueError, RuntimeError) as error:
            receipt = await self._port(self._terminal, entry)
            if receipt is not None:
                await self._accept_terminal(entry, receipt)
            else:
                await self._unknown(entry, error)
        return {"id": run_id, "status": entry.record.status}

    async def execute(
        self, plan: ShellExecutionPlan, signal: threading.Event, *, background: bool = False,
        onOutput: OutputCallback | None = None, disableSandbox: bool = False,
    ) -> ForegroundResult | str:
        try:
            plan = sandboxExecutionPlan(plan, disableSandbox and not background)
        except SandboxUnavailable as error:
            raise ToolRejected(str(error)) from error
        entry = await self._start(plan, signal)
        run_id = entry.record.run_ref.run_id
        if background:
            await self.detach(run_id)
            await self._confirm_background_ack(entry)
            return f"后台Shell已登记，id: {run_id}。用BashOutput读取新输出，用KillShell请求停止。"
        self._foreground = run_id
        collected: list[list[str]] = [[], []]
        size = [0, 0]
        total = [0, 0]
        started = time.monotonic()
        requested = False
        observer_error: str | None = None

        def emit(stream: Literal["stdout", "stderr"], text: str) -> None:
            nonlocal onOutput, observer_error
            if onOutput is not None and not signal.is_set():
                try:
                    onOutput(stream, text)
                except Exception as error:
                    observer_error = type(error).__name__
                    onOutput = None

        try:
            while True:
                if entry.record.snapshot.get("detached"):
                    await self._confirm_background_ack(entry)
                    emit("stdout", "")
                    emit("stderr", "")
                    return f"原Shell已转后台，id: {run_id}。原运行继续；用BashOutput读取输出。"
                if signal.is_set() and not requested:
                    requested = True
                    if not await self._cancel_foreground(entry):
                        if entry.record.snapshot.get("detached"):
                            continue
                        raise RuntimeError("Shell后台交接未确认，保留原run，不发出取消控制。")
                view = await self.poll(run_id, incremental=True)
                for index, name in enumerate(_STREAMS):
                    text = view[name]
                    total[index] += len(text)
                    if size[index] < 10 * 1024 * 1024:
                        saved = text[:10 * 1024 * 1024 - size[index]]
                        collected[index].append(saved)
                        size[index] += len(saved)
                    if text:
                        emit(name, text)
                if view["status"] in TERMINAL:
                    # Drain the bounded log reader before finalising.
                    if entry.ui_stdout < (entry.directory / "stdout.txt").stat().st_size or entry.ui_stderr < (entry.directory / "stderr.txt").stat().st_size:
                        continue
                    emit("stdout", "")
                    emit("stderr", "")
                    for index, name in enumerate(_STREAMS):
                        if total[index] > size[index]:
                            collected[index].append(f"\n[前台响应只保留前 {size[index]} 字符，完整输出 {total[index]} 字符在 {entry.directory / (name + '.txt')}；可用BashOutput读取。]")
                    if observer_error is not None:
                        collected[1].append(f"\n[实时输出不可用（{observer_error}）；完整工具结果已保留。]")
                    return ForegroundResult("".join(collected[0]), "".join(collected[1]),
                                            int(view.get("exitCode") or 0), view["status"] == "canceled",
                                            round((time.monotonic() - started) * 1000))
                if view["status"] == "unknown":
                    raise RuntimeError("Shell执行结果未确认，保留原run，不自动重放。")
                await asyncio.sleep(.1)
        except asyncio.CancelledError:
            signal.set()
            if await self._cancel_foreground(entry):
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    view = await self.poll(run_id)
                    if view["status"] in TERMINAL:
                        break
                    await asyncio.sleep(.1)
            raise
        finally:
            if self._foreground == run_id:
                self._foreground = None

    async def restore(self, *, report_errors: bool = False) -> tuple[RunRecord, ...]:
        for record in await self.store.recover():
            if record.snapshot.get("storage_link_version") != 1:
                continue
            if record.snapshot.get("resolved_by_user") or (record.status in TERMINAL and record.snapshot.get("recovery_material_accepted")):
                # Explicit human disposition is not a verified runner receipt; do not reconnect/control.
                continue
            directory = local_path(Path(record.snapshot["run_dir"]))
            if record.status == "failed-before-grant":
                self._runs[record.run_ref.run_id] = _Run(record, {}, b"")
                continue
            if (record.snapshot.get("phase") in {"intent", "bootstrap"}
                    and not (directory / "grant.json").exists() and not (directory / "start.claim").exists()):
                entry = _Run(record, {}, b"")
                self._runs[record.run_ref.run_id] = entry
                await self._commit(entry, status="failed-before-grant", phase="failed-before-grant",
                                   bootstrap_cleanup_unconfirmed=True,
                                   tool_result="Error: 原Shell启动从未获得执行许可，命令未执行；未重启。")
                continue
            try:
                if local_path(directory.parent) != local_path(self.directory / "runs") or directory.name != record.run_ref.run_id:
                    raise ValueError("runner目录与会话关联不符。")
                verify_private_file(directory / "capability")
                capability = (directory / "capability").read_bytes()
                manifest = read_signed(directory / "manifest.json", capability)
                validate_manifest(manifest, session_id=self.session_id, run_id=record.run_ref.run_id,
                                  task_id=record.run_ref.task_id, launch_id=record.snapshot["launch_id"],
                                  plan_digest=record.snapshot["plan_digest"])
                entry = _Run(record, manifest, capability)
                self._runs[record.run_ref.run_id] = entry
                if record.status == "failed-before-grant":
                    continue
                receipt = await self._port(self._terminal, entry)
                if receipt is not None:
                    await self._accept_terminal(entry, receipt, recover=True)
                    continue
                state = await self._connect(entry, adopt=True)
                if not state.get("started"):
                    raise RuntimeError("runner未完成启动认领，恢复不重发start。")
                if not entry.record.snapshot.get("detached"):
                    await self.cancel(record.run_ref.run_id)
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        receipt = await self._port(self._terminal, entry)
                        if receipt is not None:
                            await self._accept_terminal(entry, receipt)
                            if "tool_result" not in entry.record.snapshot:
                                await self._commit(entry, tool_result=f"原前台Shell已停止，任务id: {record.run_ref.run_id}；输出保留，未重启命令。")
                            break
                        await asyncio.sleep(.1)
                    else:
                        raise RuntimeError("未保留前台执行的取消仍未确认。")
                    continue
                metadata: dict[str, Any] = {}
                if "tool_result" not in entry.record.snapshot:
                    metadata["tool_result"] = self._recovery_ack(record.run_ref.run_id)
                await self._commit(entry, status=state["status"], **metadata)
            except (OSError, ValueError, RuntimeError) as error:
                if record.status in TERMINAL:
                    if report_errors:
                        self.recovery_errors[record.run_ref.run_id] = type(error).__name__
                        self._runs.pop(record.run_ref.run_id, None)
                        continue
                    raise RuntimeError("已完成执行的收据或输出附件未能核验，保留现场并停止恢复。") from error
                if record.run_ref.run_id not in self._runs:
                    self._runs[record.run_ref.run_id] = _Run(record, {}, b"")
                await self._unknown(self._runs[record.run_ref.run_id], error)
        return tuple(entry.record for entry in self._runs.values())

    async def _close_bootstrap(self, entry: _Run, launcher: subprocess.Popen[bytes]) -> None:
        # Retain and settle even a bootstrap which reported ready after its caller stopped waiting.
        deadline = time.monotonic() + 35
        cancel_sent = False
        while launcher.poll() is None and time.monotonic() < deadline:
            if not cancel_sent and (entry.directory / "runner-state.json").exists():
                try:
                    state = await self._port(self._state, entry)
                    current = process_identity()
                    if current is None:
                        raise RuntimeError("清理controller身份不可用。")
                    epoch = max(state["control_epoch"], entry.record.snapshot["control_epoch"]) + 1
                    await self._commit(entry, control_epoch=epoch, endpoint=state["endpoint"],
                                       runner_identity=state["runner_identity"], server_helper_identity=state["server_helper_identity"],
                                       owner_identity=asdict(current))
                    await self._rpc(entry, "adopt")
                    await self._rpc(entry, "cancel")
                    cancel_sent = True
                except (OSError, ValueError, RuntimeError):
                    pass
            await asyncio.sleep(.05)
        if launcher.poll() is None:
            raise RuntimeError("未授权runner bootstrap退出未确认，保留实际进程句柄。")
        await self._port(launcher.wait)

    async def close(self, *, keep_background: bool = False) -> tuple[str, ...]:
        self._closed = True
        notices: list[str] = []
        for run_id, entry in tuple(self._runs.items()):
            if entry.record.snapshot.get("resolved_by_user") or self._recovery_unconfirmed:
                notices.append(f"Shell任务 {run_id} 的人工核实或恢复提交保留；未重新控制原执行。")
                continue
            if entry.record.status in TERMINAL and entry.terminal is None:
                notices.append(f"Shell任务 {run_id} 已保存终态的附件未确认；保留现场，未发出控制。")
            if entry.record.status == "unknown" and entry.record.snapshot.get("detached"):
                notices.append(f"Shell任务 {run_id} 执行未确认；保留已许可后台与现场，未发出控制。")
                continue
            if keep_background and entry.record.status not in TERMINAL | {"failed-before-grant", "unknown"}:
                await self.detach(run_id)
            if entry.record.snapshot.get("detached"):
                continue
            if entry.record.status not in TERMINAL | {"failed-before-grant"}:
                requested = await self.cancel(run_id)
                if requested.get("reason"):
                    notices.append(f"Shell任务 {run_id} 执行未确认；{requested['reason']}")
                    continue
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    try:
                        view = await self.poll(run_id)
                    except (OSError, ValueError, RuntimeError) as error:
                        await self._unknown(entry, error)
                        notices.append(f"Shell任务 {run_id} 关闭或输出附件未确认；保留现场。")
                        break
                    if view["status"] in TERMINAL:
                        break
                    await asyncio.sleep(.1)
                else:
                    await self._unknown(entry, TimeoutError("runner关闭未确认。"))
                    notices.append(f"Shell任务 {run_id} 关闭未确认；保留现场，不视为已停止。")
        if self._ports:
            await asyncio.gather(*tuple(self._ports), return_exceptions=True)
        for run_id, launcher in tuple(self._launchers.items()):
            entry = self._runs[run_id]
            if entry.record.snapshot.get("detached"):
                continue
            if entry.record.status == "failed-before-grant" and launcher.poll() is None:
                await self._close_bootstrap(entry, launcher)
            elif launcher.poll() is None and entry.record.status in TERMINAL:
                try:
                    await self._port(launcher.wait, timeout=5)
                except subprocess.TimeoutExpired as error:
                    raise RuntimeError("Shell已关闭但runner资源收尾未确认。") from error
        return tuple(notices)
