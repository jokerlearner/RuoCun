"""Ticket-07 synthetic local chat, durable save, process exit and restart.

This explicit engineering demo requires a new workspace and a caller-supplied
official DLL archive. It never uses real accounts or external model services.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..platform.windows.durable_file import atomic_publish, ensure_private_dir
from .contract import AcceptedInput, Checkpoint
from .runtime import verify_controlled_runtime, verify_official_archive
from .storage_worker import StorageWorker

_SESSION_ID = "synthetic-session"
_OPERATION_ID = "synthetic-chat-checkpoint-v1"


async def _phase(root: Path, archive: Path, phase: str) -> dict[str, Any]:
    runtime = verify_controlled_runtime(verify_official_archive(archive, root / "runtime"))
    chat: dict[str, Any] = {}
    if phase == "save":
        from ..chat_demo import run_chat_demo

        config = root / "config"
        ensure_private_dir(config)
        atomic_publish(config / "config.json", json.dumps({
            "version": 2, "activeProfile": "synthetic",
            "profiles": {"synthetic": {
                "provider": "deepseek", "baseUrl": "https://api.deepseek.com",
                "model": "deepseek-v4-pro", "key": "sk-synthetic-NOT-A-REAL-KEY",
            }},
        }).encode("utf-8"))
        chat = run_chat_demo(config, "保存这次对话")
        if chat["status"] != "complete" or not chat["wire_request_validated"] or not chat["server_closed"]:
            raise RuntimeError("本地对话未完整结束，不能宣称会话已保存。")

    worker = StorageWorker.open(root / "session", _SESSION_ID, root, runtime)
    try:
        initial = await worker.load_recovery_view()
        if phase == "save":
            messages = tuple(dict(item) for item in chat["request_golden"]["messages"])
            messages += ({"role": "assistant", "content": chat["answer"]},)
            checkpoint = Checkpoint(
                _SESSION_ID, messages, str(chat["model"]), "normal", "合成存储演示", 0,
                (AcceptedInput("input-1", 1, "保存这次对话", (), "consumed"),), (),
                dict(chat["usage"]), "idle", 0,
            )
            handle = worker.enqueue_checkpoint(0, checkpoint, (), operation_id=_OPERATION_ID)
            revision = await handle.wait()
            receipt = await worker.lookup_checkpoint_operation(
                _OPERATION_ID, request_digest=handle.request_digest,
            )
            if receipt is None or receipt.revision != revision:
                raise RuntimeError("提交后无法核验持久收据。")
            return {
                "revision": revision, "owner_epoch": initial.owner.owner_epoch,
                "answer": chat["answer"], "wire_request_validated": True,
                "server_closed": True, "runtime": asdict(runtime),
            }
        if phase != "recover" or initial.checkpoint is None:
            raise RuntimeError("恢复没有可信检查点。")
        receipt = await worker.lookup_checkpoint_operation(_OPERATION_ID)
        if receipt is None:
            raise RuntimeError("新进程没有读到持久操作收据。")
        return {
            "revision": initial.checkpoint.revision,
            "owner_epoch": initial.owner.owner_epoch,
            "answer": initial.checkpoint.messages[-1]["content"],
            "receipt_revision": receipt.revision,
            "accepted_state": initial.checkpoint.accepted_inputs[0].state,
            "runtime": asdict(runtime),
        }
    finally:
        await worker.close()


def run_phase(root: Path, archive: Path, phase: str) -> dict[str, Any]:
    """Internal child entry; the orchestrator owns the new synthetic root."""
    return asyncio.run(_phase(root, archive, phase))


def run_demo(workspace: Path, archive: Path) -> dict[str, Any]:
    root = workspace.resolve()
    if root.exists() or root.is_symlink():
        raise FileExistsError("演示只接受不存在的新工作区。")
    if not root.parent.is_dir():
        raise FileNotFoundError("演示工作区的父目录不存在。")
    ensure_private_dir(root)
    if any(root.iterdir()):
        raise FileExistsError("新演示工作区不是空目录。")
    child_code = (
        "import json,sys; from pathlib import Path; "
        "from ruocun.session.demo import run_phase; "
        "print(json.dumps(run_phase(Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]),ensure_ascii=False))"
    )
    results = []
    for phase in ("save", "recover"):
        child = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", "-c", child_code,
             str(root), str(archive.resolve()), phase],
            capture_output=True, text=True, encoding="utf-8", timeout=35,
        )
        if child.returncode:
            raise RuntimeError(f"合成存储子进程 {phase} 失败：{child.stderr}")
        results.append(json.loads(child.stdout))
    saved, restored = results
    if (
        saved["revision"] != restored["revision"]
        or saved["answer"] != restored["answer"]
        or restored["receipt_revision"] != saved["revision"]
        or restored["accepted_state"] != "consumed"
    ):
        raise RuntimeError("新进程恢复内容或持久收据不一致。")
    return {
        "status": "passed", "answer": restored["answer"],
        "saved_revision": saved["revision"], "restored_revision": restored["revision"],
        "saved_owner_epoch": saved["owner_epoch"], "restored_owner_epoch": restored["owner_epoch"],
        "operation_receipt_revision": restored["receipt_revision"],
        "sqlite_version": restored["runtime"]["version"], "runtime": restored["runtime"],
        "wire_request_validated": saved["wire_request_validated"],
        "server_closed": saved["server_closed"], "processes_exited": True,
        "boundary": "local synthetic HTTP; no real model; process restart, not power loss",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--archive", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = run_demo(args.workspace, args.archive)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(f"合成会话演示失败（{type(error).__name__}）：{error}", file=sys.stderr)
        return 72
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
