"""Independent same-package Shell runner (frozen shell_runner.ts, MIT; D08/D09).

The runner owns its command Job and output files. Transport helpers never own
execution truth or the session database.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import signal
import threading
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, cast

from ..platform.process_tree import ForegroundResult, run_foreground_plan
from ..platform.shell_plan import ShellAnalysis, ShellExecutionPlan
from ..platform.windows.durable_file import (
    PrivateDirectory,
    atomic_publish,
    ensure_private_dir,
    local_path,
    sync_directory,
    verify_private_file,
)
from ..session.contract import ProcessIdentity
from ..session.process_identity import identity_alive, process_identity
from ..version import __version__

if TYPE_CHECKING:
    from ..platform.windows.ipc import PeerIdentity, PipeServer

PROTOCOL_VERSION = 1
TERMINAL = {"completed", "failed", "canceled"}
LOGS = ("stdout.log", "stderr.log", "stdout.txt", "stderr.txt")


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def write_signed(path: Path, payload: dict[str, Any], capability: bytes) -> None:
    mac = hmac.new(capability, canonical(payload), hashlib.sha256).hexdigest()
    atomic_publish(path, canonical({"payload": payload, "mac": mac}))


def read_signed(path: Path, capability: bytes) -> dict[str, Any]:
    verify_private_file(path)
    raw = path.read_bytes()
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("runner收据或清单超过允许大小。")
    value = json.loads(raw)
    if not isinstance(value, dict) or not isinstance(value.get("payload"), dict) or not isinstance(value.get("mac"), str):
        raise ValueError("runner收据格式无效。")
    expected = hmac.new(capability, canonical(value["payload"]), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(value["mac"], expected):
        raise ValueError("runner收据认证失败。")
    return cast(dict[str, Any], value["payload"])


def identity(value: Any) -> ProcessIdentity:
    if (not isinstance(value, dict) or set(value) != {"host", "boot", "pid", "start"}
            or not all(isinstance(value[name], str) and value[name] for name in ("host", "boot", "start"))
            or not isinstance(value.get("pid"), int) or isinstance(value["pid"], bool) or value["pid"] <= 0):
        raise ValueError("runner进程身份无效。")
    return ProcessIdentity(**value)


def package_files() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    names = ("tools/shell_runner.py", "platform/process_tree.py", "platform/windows/process_tree.py",
             "platform/windows/ipc.py", "platform/shell_output.py", "version.py")
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}


def plan_payload(plan: ShellExecutionPlan) -> dict[str, Any]:
    return asdict(plan)


def parse_plan(value: dict[str, Any]) -> ShellExecutionPlan:
    data = dict(value)
    raw_analysis = dict(data.pop("analysis"))
    for key in ("commands", "wrappers", "bashPayloads"):
        raw_analysis[key] = tuple(raw_analysis.get(key, ()))
    data["analysis"] = ShellAnalysis(**raw_analysis)
    data["argv"] = tuple(data["argv"])
    data["environment"] = tuple(tuple(pair) for pair in data["environment"])
    plan = ShellExecutionPlan(**data)
    if not Path(plan.argv[0]).is_absolute() or not Path(plan.cwd).is_absolute():
        raise ValueError("runner执行计划缺少绝对路径。")
    return plan


def validate_manifest(manifest: dict[str, Any], *, session_id: str, run_id: str, task_id: str,
                      launch_id: str, plan_digest: str) -> None:
    expected = {"version": PROTOCOL_VERSION, "session_id": session_id, "run_id": run_id,
                "task_id": task_id, "launch_id": launch_id, "plan_digest": plan_digest}
    if any(manifest.get(name) != value for name, value in expected.items()):
        raise ValueError("runner清单执行身份不匹配。")
    if digest(manifest.get("plan")) != plan_digest:
        raise ValueError("runner清单执行计划摘要不匹配。")


def log_facts(directory: Path) -> dict[str, dict[str, Any]]:
    facts: dict[str, dict[str, Any]] = {}
    for name in LOGS:
        file = directory / name
        verify_private_file(file)
        sha = hashlib.sha256()
        count = 0
        with file.open("rb") as data:
            while chunk := data.read(65536):
                sha.update(chunk)
                count += len(chunk)
        facts[name] = {"bytes": count, "sha256": sha.hexdigest()}
    return facts


def validate_terminal(receipt: dict[str, Any], manifest: dict[str, Any], directory: Path,
                      runner_identity: dict[str, Any]) -> None:
    for name in ("version", "session_id", "task_id", "run_id", "launch_id", "plan_digest"):
        if receipt.get(name) != manifest.get(name):
            raise ValueError("runner终态收据身份不匹配。")
    if receipt.get("status") not in TERMINAL or receipt.get("runner_identity") != runner_identity:
        raise ValueError("runner终态缺少原执行器身份或真实终态。")
    if receipt.get("logs") != log_facts(directory):
        raise ValueError("runner终态输出附件缺失或摘要不匹配。")
    if receipt.get("closed") is not True:
        raise ValueError("runner终态尚未确认进程树和输出关闭。")
    code = receipt.get("code")
    if not isinstance(code, int) or isinstance(code, bool):
        raise ValueError("runner终态退出码无效。")
    if (receipt["status"] == "completed" and code != 0) or (receipt["status"] == "failed" and code == 0):
        raise ValueError("runner终态与退出码冲突。")


class Runner:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        verify_private_file(directory / "capability")
        self.capability = (directory / "capability").read_bytes()
        if len(self.capability) != 32:
            raise ValueError("runner capability格式无效。")
        self.manifest = read_signed(directory / "manifest.json", self.capability)
        if self.manifest.get("version") != PROTOCOL_VERSION or self.manifest.get("package_version") != __version__:
            raise ValueError("runner协议或包版本不匹配。")
        if self.manifest.get("package_files") != package_files():
            raise ValueError("runner与controller未使用同一包代码。")
        if any((directory / name).exists() for name in ("runner-state.json", "start.claim", "terminal.json", "grant.json")):
            raise ValueError("旧runner材料已存在，拒绝再次启动执行器。")
        self.plan = parse_plan(self.manifest["plan"])
        validate_manifest(self.manifest, session_id=self.manifest["session_id"], run_id=self.manifest["run_id"],
                          task_id=self.manifest["task_id"], launch_id=self.manifest["launch_id"],
                          plan_digest=self.manifest["plan_digest"])
        current = process_identity()
        if current is None:
            raise ValueError("runner真实身份不可用。")
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.done = threading.Event()
        self.worker: threading.Thread | None = None
        self.files: list[BinaryIO] = []
        self.server: PipeServer | None = None
        self.transport_poisoned = False
        self.state: dict[str, Any] = {
            **{name: self.manifest[name] for name in ("version", "session_id", "task_id", "run_id", "launch_id", "plan_digest")},
            "runner_identity": asdict(current), "owner_identity": self.manifest["owner_identity"],
            "control_epoch": 0, "endpoint": self.manifest["endpoint"], "server_helper_identity": None,
            "phase": "bootstrap", "status": "launching", "started": False, "cancel_requested": False,
            "detached": False, "closed": False,
        }

    def persist(self) -> None:
        write_signed(self.directory / "runner-state.json", self.state, self.capability)

    def open_logs(self) -> None:
        for name in LOGS:
            file = self.directory / name
            self.files.append(file.open("xb", buffering=0))
            verify_private_file(file)

    def close_logs(self) -> None:
        errors: list[BaseException] = []
        for file in self.files:
            if file.closed:
                continue
            try:
                file.flush()
                os.fsync(file.fileno())
            except BaseException as error:
                errors.append(error)
            finally:
                file.close()
        if errors:
            raise RuntimeError("runner输出持久关闭未确认。") from errors[0]
        sync_directory(self.directory)

    def raw_output(self, index: int, chunk: bytes) -> None:
        view = memoryview(chunk)
        while view:
            count = self.files[index].write(view)
            if count is None or count <= 0:
                raise OSError("runner输出写入未完成。")
            view = view[count:]

    def text_output(self, stream: str, text: str) -> None:
        if not text:
            return
        index = 2 if stream == "stdout" else 3
        data = text.encode("utf-8", errors="backslashreplace")
        view = memoryview(data)
        while view:
            count = self.files[index].write(view)
            if count is None or count <= 0:
                raise OSError("runner解码输出写入未完成。")
            view = view[count:]

    def finish(self, result: ForegroundResult) -> None:
        self.close_logs()
        if any(note.startswith("实时输出回调不可用") for note in result.decodingDiagnostics):
            raise RuntimeError("runner解码日志未能完整保存。")
        with self.lock:
            status = "canceled" if result.aborted else "completed" if result.code == 0 else "failed"
            self.state.update(status=status, phase="terminal", closed=True, code=result.code,
                              elapsed_ms=result.elapsedMs, decoding_diagnostics=list(result.decodingDiagnostics),
                              logs=log_facts(self.directory))
            write_signed(self.directory / "terminal.json", self.state, self.capability)
            self.persist()
        self.done.set()

    def execute(self) -> None:
        try:
            result = run_foreground_plan(self.plan, self.stop, onLogOutput=self.text_output,
                                         onRawOutput=self.raw_output, captureOutput=False)
            self.finish(result)
        except BaseException as error:
            try:
                self.close_logs()
            except BaseException:
                pass
            with self.lock:
                self.state.update(status="unknown", phase="execution-unconfirmed", error_type=type(error).__name__)
                try:
                    self.persist()
                except BaseException:
                    pass
            self.done.set()

    def start(self) -> None:
        if self.state["started"] or self.done.is_set():
            return
        grant = read_signed(self.directory / "grant.json", self.capability)
        for name in ("version", "session_id", "task_id", "run_id", "launch_id", "plan_digest", "control_epoch", "owner_identity"):
            if grant.get(name) != self.state.get(name):
                raise ValueError("runner启动许可已经过期或身份不匹配。")
        claim = self.directory / "start.claim"
        with claim.open("xb") as data:
            payload = {"run_id": self.state["run_id"], "launch_id": self.state["launch_id"],
                       "plan_digest": self.state["plan_digest"], "control_epoch": self.state["control_epoch"]}
            data.write(canonical(payload))
            data.flush()
            os.fsync(data.fileno())
        verify_private_file(claim)
        sync_directory(self.directory)
        self.state.update(started=True, phase="started", status="running")
        self.persist()
        worker = threading.Thread(target=self.execute, name="ruocun-shell-executor")
        worker.start()
        self.worker = worker

    def control(self, payload: dict[str, Any], owner: ProcessIdentity) -> dict[str, Any]:
        with self.lock:
            for name in ("version", "session_id", "run_id", "launch_id", "plan_digest"):
                if payload.get(name) != self.state.get(name):
                    raise ValueError("runner控制身份不匹配。")
            claimed = identity(payload.get("owner_identity"))
            if owner != claimed:
                raise ValueError("runner控制方OS身份与声明不匹配。")
            epoch = payload.get("control_epoch")
            if not isinstance(epoch, int) or isinstance(epoch, bool) or not 0 <= epoch <= 9007199254740991:
                raise ValueError("runner控制租约无效。")
            current = self.state["control_epoch"]
            action = payload.get("action")
            if epoch < current or (epoch == current and payload["owner_identity"] != self.state["owner_identity"]):
                raise ValueError("runner控制租约已过期。")
            if epoch > current:
                if action != "adopt":
                    raise ValueError("新控制租约必须先显式接管。")
                self.state.update(control_epoch=epoch, owner_identity=payload["owner_identity"])
                self.persist()
            if action == "start":
                try:
                    self.start()
                except BaseException:
                    if self.worker is None:
                        self.state.update(status="unknown", phase="start-unconfirmed")
                        try:
                            self.close_logs()
                            self.persist()
                        finally:
                            self.done.set()
                    raise
            elif action == "cancel":
                self.state["cancel_requested"] = True
                if not self.done.is_set():
                    self.state.update(status="canceling", phase="canceling")
                    try:
                        self.persist()
                    finally:
                        self.stop.set()
                if not self.state["started"] and not self.done.is_set():
                    self.finish(ForegroundResult("", "", 1, True, 0))
            elif action == "detach":
                self.state["detached"] = True
                self.persist()
            elif action not in ("status", "adopt"):
                raise ValueError("runner控制动作无效。")
            return dict(self.state)

    def rpc(self, payload: dict[str, Any], peer: PeerIdentity) -> dict[str, Any]:
        try:
            return self.control(payload, peer.owner_identity)
        except BaseException as error:
            # A rejected stale request must not tear down an otherwise healthy transport helper.
            return {"error": type(error).__name__}

    def serve(self) -> None:
        from ..platform.windows.ipc import PipeServer
        self.server = PipeServer(self.state["endpoint"], self.capability, self.rpc,
                                 helper_command=self.manifest.get("helper_command"))
        self.server.start(time.monotonic() + 3)
        if self.server.helper_identity is None:
            raise RuntimeError("transport helper真实身份不可用。")
        with self.lock:
            self.state.pop("transport_error", None)
            self.state["server_helper_identity"] = asdict(self.server.helper_identity)
            self.state["private_sid"] = self.server.private_sid
            self.persist()

    def run(self) -> int:
        with PrivateDirectory(self.directory):
            self.open_logs()
            try:
                self.serve()
                deadline = time.monotonic() + 30
                while not self.done.wait(.05):
                    cancel = self.directory / "cancel.json"
                    if cancel.exists():
                        try:
                            value = read_signed(cancel, self.capability)
                            owner = identity(value.get("owner_identity"))
                            if identity_alive(owner):
                                if value.get("control_epoch", -1) > self.state["control_epoch"]:
                                    self.control({**value, "action": "adopt"}, owner)
                                self.control(value, owner)
                        except Exception:
                            pass
                    if not self.state["started"] and (self.stop.is_set() or time.monotonic() >= deadline):
                        self.stop.set()
                        self.finish(ForegroundResult("", "", 1, True, 0))
                        break
                    if self.server is not None and not self.server.alive and not self.transport_poisoned:
                        try:
                            self.server.close()
                            with self.lock:
                                self.state["control_epoch"] += 1
                                self.state["endpoint"] = r"\\.\pipe\ruocun-shell-" + uuid.uuid4().hex
                            self.serve()
                        except BaseException as error:
                            self.transport_poisoned = True
                            with self.lock:
                                self.state["transport_error"] = type(error).__name__
                                try:
                                    self.persist()
                                except BaseException:
                                    pass
                if self.worker is not None:
                    self.worker.join()
            finally:
                if self.server is not None:
                    self.server.close()
                self.close_logs()
        return 0 if self.state["status"] in TERMINAL else 74


def main(directory: Path) -> int:
    if os.name != "nt":
        return 78
    try:
        directory = local_path(directory)
        ensure_private_dir(directory)
        runner = Runner(directory)
        signal.signal(signal.SIGTERM, lambda *_: runner.stop.set())
        signal.signal(signal.SIGINT, lambda *_: runner.stop.set())
        return runner.run()
    except BaseException as error:
        # Never print manifest arguments, capability or raw I/O exception values.
        print(f"Shell runner停止（{type(error).__name__}），请保留运行目录核实。", flush=True)
        return 74
