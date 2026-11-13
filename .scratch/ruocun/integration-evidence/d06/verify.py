"""D06 独立集成复验；仅写本目录新运行，保留原始证据，不改产品与断言。"""
import asyncio
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import traceback
import zipfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
BASE = REPO / ".scratch/ruocun-discovery/experiments/terminal"
REF = REPO / ".scratch/ruocun-discovery/reference/dao-f17e189-7ac654a0dc06"
CANDIDATE = "ad48d6c86d5e9b1dad0961c035c9f66641ac4b63"
START = "35125492cb1b89545494b2a9ca6ba2da554cabd8"
MERGE = "9e643bff6bafaaee232c04e4788acfc2bbf63e4d"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
PACKAGES = ("prompt_toolkit", "rich", "wcwidth", "pytest", "markdown-it-py", "mdurl",
            "pygments", "pluggy", "packaging", "iniconfig", "colorama")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO, stderr=subprocess.PIPE)


def write(root, name, value):
    (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def integrity(root):
    files = git("ls-tree", "-r", "-z", "--name-only", CANDIDATE,
                BASE.relative_to(REPO).as_posix()).decode("utf-8").split("\0")
    rows = []
    for rel in filter(None, files):
        actual = (REPO / rel).read_bytes()
        expected = git("show", f"{CANDIDATE}:{rel}")
        rows.append({"path": rel, "bytes": len(actual), "sha256": sha(actual),
                     "matches_candidate_blob": actual == expected})
    write(root, "candidate-files.json", rows)
    assert rows and all(row["matches_candidate_blob"] for row in rows)

    reports = []
    for path in sorted((BASE / "evidence/automated").glob("*/report.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        bindings = []
        for name, expected in report["code_sha256"].items():
            rel = (BASE / name).relative_to(REPO).as_posix()
            recorded = subprocess.run(["git", "show", f'{report["head_before_run"]}:{rel}'],
                                      cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            snapshots = [head for head in ("7036050", "d295a15", CANDIDATE)
                         if sha(git("show", f"{head}:{rel}")) == expected]
            bindings.append({"path": name, "declared_sha256": expected,
                             "present_in_recorded_head": recorded.returncode == 0,
                             "matches_recorded_head": recorded.returncode == 0 and sha(recorded.stdout) == expected,
                             "matching_committed_snapshots": snapshots,
                             "matches_merged_code": sha((BASE / name).read_bytes()) == expected})
        item = {"report": path.relative_to(REPO).as_posix(), "report_sha256": sha(path.read_bytes()),
                "head_before_run": report["head_before_run"], "exit_code": report["exit_code"],
                "lock_matches": report["lock_sha256"] == sha((BASE / "requirements.lock").read_bytes()),
                "stdout_matches": report["stdout_sha256"] == sha((path.parent / "pytest-stdout.txt").read_bytes()),
                "stdout_tail": (path.parent / "pytest-stdout.txt").read_text(encoding="utf-8").splitlines()[-1],
                "code_bindings": bindings}
        assert item["lock_matches"] and item["stdout_matches"] and item["exit_code"] == 0
        # 首两轮是在提交前运行，运行时仓库 HEAD 不是源码快照；原声明 hash 必须能绑定后续提交。
        assert all(binding["matching_committed_snapshots"] for binding in bindings)
        reports.append(item)
    assert len(reports) == 3
    assert all(row["matches_merged_code"] for row in reports[-1]["code_bindings"])
    assert all(row["matches_recorded_head"] for row in reports[-1]["code_bindings"])
    write(root, "original-report-review.json", reports)

    tdd = []
    for path in sorted((BASE / "evidence/automated").glob("*.txt")):
        data = path.read_bytes()
        text = data.decode("utf-8", errors="replace")
        tdd.append({"path": path.relative_to(REPO).as_posix(), "sha256": sha(data),
                    "bytes": len(data), "summary": re.findall(r"(?:\d+ (?:failed|passed|error|errors)[^\r\n]*)", text)[-2:]})
    write(root, "tdd-raw-index.json", tdd)

    checksums = json.loads((REF / "checksums.json").read_text(encoding="utf-8"))
    for name, expected in checksums.items():
        assert sha((REF / name).read_bytes()) == expected, name
    manifest = {entry["path"]: entry for entry in json.loads((REF / "manifest.json").read_text(encoding="utf-8"))["files"]}
    ranges = {
        "src/tui/app/App.tsx": [(474,489), (1335,1362)],
        "src/tui/app/run.tsx": [(15,59)],
        "src/tui/terminal_reports.ts": [(24,35),(79,146),(148,206)],
        "src/tui/mascot.ts": [(36,58)],
        "src/tui/imagePaste.ts": [(1,29)],
        "src/tui/width.ts": [(1,27)],
        "src/tui/tab_attention.ts": [(30,66)],
    }
    source = {"archive_sha256": sha((REF / "source.zip").read_bytes()), "files": []}
    with zipfile.ZipFile(REF / "source.zip") as archive:
        for name, spans in ranges.items():
            data = archive.read(name)
            assert sha(data) == manifest[name]["sha256"]
            lines = data.decode("utf-8-sig").splitlines()
            source["files"].append({"path": name, "sha256": sha(data), "matches_manifest": True,
                                    "excerpts": [{"first": first, "last": min(last, len(lines)),
                                                  "lines": [f"{i}: {lines[i-1]}" for i in range(first, min(last,len(lines))+1)]}
                                                 for first,last in spans]})
    write(root, "source-contract-review.json", source)

    fixtures = json.loads((BASE / "fixtures/manifest.json").read_text(encoding="utf-8"))
    fixture_rows = []
    for name, expected in fixtures.items():
        path = BASE / "fixtures" / ("合成 image.png" if name == "image" else name + ".txt")
        data = path.read_bytes()
        assert sha(data) == expected["file_sha256"] and len(data) == expected["file_bytes"]
        if name != "image":
            text = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
            lines = len(text.rstrip("\n").split("\n")) if text.rstrip("\n") else 0
            collapsed = len(text.encode("utf-16-le")) // 2 > 280 or lines > 6
            assert sha(text.encode("utf-8")) == expected["normalized_paste"]["sha256"]
            submission = text if collapsed else text.strip()
            assert sha(submission.encode("utf-8")) == expected["source_submission"]["sha256"]
        fixture_rows.append({"file": path.name, "sha256": sha(data), "matches_manifest": True})
    write(root, "fixture-review.json", fixture_rows)


async def real_worker_trace(root):
    """同一已确认进程 seam 补 raw 清理凭据；不借用其它运行或按进程名清理。"""
    sys.path.insert(0, str(BASE))
    from workers import Workers
    events = []
    workers = Workers(root, lambda transition, **data: events.append({"transition": transition, **data}))
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME),
                                      ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
                                      ctypes.POINTER(wintypes.FILETIME)]
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE

    class ProcessEntry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260)]

    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]

    def process_binding(pid):
        handle = kernel.OpenProcess(0x00100000 | 0x1000, False, pid)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            times = [wintypes.FILETIME() for _ in range(4)]
            if not kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
                raise ctypes.WinError(ctypes.get_last_error())
            image = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(image))
            if not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)):
                raise ctypes.WinError(ctypes.get_last_error())
            return handle, {"pid": pid, "creation_filetime": str(times[0].dwHighDateTime << 32 | times[0].dwLowDateTime),
                            "image": image.value, "initial_handle_wait": kernel.WaitForSingleObject(handle, 0)}
        except BaseException:
            kernel.CloseHandle(handle)
            raise

    def parent_pid(pid):
        snapshot = kernel.CreateToolhelp32Snapshot(0x2, 0)
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            entry = ProcessEntry()
            entry.dwSize = ctypes.sizeof(entry)
            valid = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
            while valid:
                if entry.th32ProcessID == pid:
                    return entry.th32ParentProcessID
                valid = kernel.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            kernel.CloseHandle(snapshot)
        raise RuntimeError("owned worker absent from process snapshot")

    task, launcher_handle, worker_handle, receipt = None, None, None, None
    try:
        task = await workers.start(ticks=1000, delay=.01)
        await workers.wait_started(task)
        started = next(event for event in events if event["transition"] == "worker-started")
        spawned = next(event for event in events if event["transition"] == "worker-spawned")
        pid = workers.describe()[0]["pid"]
        assert spawned["pid"] == pid and started["owner"] == spawned["owner"] == workers.owner
        launcher_handle, launcher = process_binding(pid)
        worker_handle, actual = process_binding(started["pid"])
        actual["parent_pid"] = parent_pid(started["pid"])
        assert started["pid"] == pid or actual["parent_pid"] == pid
        assert launcher["initial_handle_wait"] == actual["initial_handle_wait"] == 258
        assert workers.detach(task)
        assert not await workers.cancel(task, foreground_only=True)
        assert kernel.WaitForSingleObject(launcher_handle, 0) == kernel.WaitForSingleObject(worker_handle, 0) == 258
        assert await workers.cancel(task)
        receipt = await workers.wait(task)
        assert receipt["status"] == "canceled" and receipt["returncode"] is not None
        launcher["after_close_handle_wait"] = kernel.WaitForSingleObject(launcher_handle, 2000)
        actual["after_close_handle_wait"] = kernel.WaitForSingleObject(worker_handle, 2000)
        assert launcher["after_close_handle_wait"] == actual["after_close_handle_wait"] == 0
        before = len(events)
        await asyncio.sleep(.05)
        assert len(events) == before
        return {"owner": workers.owner, "task": task, "launcher": launcher, "actual_worker": actual,
                "receipt": receipt, "late_event_count": len(events)-before,
                "process_pump_done": workers.records[task]["pump"].done()}
    finally:
        await workers.shutdown()
        for handle in (launcher_handle, worker_handle):
            if handle:
                kernel.CloseHandle(handle)
        (root / "worker-events.jsonl").write_text("".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events), encoding="utf-8")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify.py NEW_RUN_DIRECTORY_NAME")
    name = sys.argv[1]
    if not re.fullmatch(r"r\d+", name):
        raise SystemExit("run must be r<digits>")
    root = HERE / name
    # r1 只允许已有的本次 venv 安装原始材料；其它运行必须新建。
    if root.exists():
        assert name == "r1" and {p.name for p in root.iterdir()} <= {"pip-install.txt", "pip-check.txt"}
    else:
        root.mkdir()
    assert not (root / "t").exists()
    head = git("rev-parse", "HEAD").decode().strip()
    assert head == MERGE or git("merge-base", MERGE, head).decode().strip() == MERGE
    assert git("rev-list", "--parents", "-n", "1", MERGE).decode().split() == [MERGE, START, CANDIDATE]
    integrity(root)
    packages = {package: version(package) for package in PACKAGES}
    locked = {name.lower().replace("_", "-"): item for name,item in re.findall(r"^([A-Za-z0-9_-]+)==([^\s]+)", (BASE/"requirements.lock").read_text(), re.M)}
    assert all(locked[name.lower().replace("_", "-")] == item for name,item in packages.items())
    command = [sys.executable, "-m", "pytest", str(BASE/"test_terminal.py"), "-q", "--basetemp", str(root/"t")]
    completed = subprocess.run(command, cwd=REPO, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (root / "pytest-stdout.txt").write_bytes(completed.stdout)
    assert completed.returncode == 0, completed.stdout.decode("utf-8", errors="replace")
    assert re.search(rb"14 passed", completed.stdout)
    focus = []
    shutdowns = []
    for path in sorted((root/"t").rglob("events.jsonl")):
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        assert rows[-1]["transition"] == "shutdown-complete"
        assert all(row["seq"] == i for i,row in enumerate(rows,1))
        shutdowns.append({"path": path.relative_to(root).as_posix(), "seq": rows[-1]["seq"], "resources": rows[-1]["resources"]})
        if "test_focus_reporting" in str(path):
            transitions = [row["transition"] for row in rows]
            assert transitions.count("focus-reporting-enabled") == transitions.count("focus-reporting-disabled") == 1
            assert transitions.index("focus-reporting-enabled") < transitions.index("focus-reporting-disabled")
            focus.append({"path": path.relative_to(root).as_posix(), "enabled_seq": transitions.index("focus-reporting-enabled")+1,
                          "disabled_seq": transitions.index("focus-reporting-disabled")+1})
    assert len(focus) == 2 and len(shutdowns) == 5
    write(root, "focus-review.json", {"normal_and_controlled_exception": focus,
                                     "exact_raw_enable_disable_counts": "existing test assertions passed against ProtocolOutput.write_raw"})
    worker = asyncio.run(real_worker_trace(root))
    write(root, "cleanup.json", {"harness_shutdowns": shutdowns, "worker": worker,
                                  "i06_accessed_or_controlled": False, "scope": "m06 本次拥有的单级子进程和 harness"})
    report = {"evidence_kind": "independent-automated-prototype", "utc": datetime.now(timezone.utc).isoformat(),
              "candidate": CANDIDATE, "integration_start": START, "merge": MERGE, "head_before_run": head,
              "branch": git("branch", "--show-current").decode().strip(), "python": sys.version,
              "executable": sys.executable, "os": platform.platform(), "dependencies": packages,
              "command": command, "exit_code": completed.returncode, "result": "14 passed",
              "lock_sha256": sha((BASE/"requirements.lock").read_bytes()),
              "code_sha256": {p.name:sha(p.read_bytes()) for p in sorted([*BASE.glob("*.py"), *BASE.glob("*.ps1")])},
              "stdout_sha256": sha(completed.stdout), "technical_continue": True,
              "hitl": "pending (ADR-0004; only recorded first-group feedback accepted)",
              "visible_windows_terminal": "not independently operated in this review",
              "limitations": ["prototype only; no product acceptance inherited", "no real model calls",
                              "mascot/full owned viewport, persistent runner/process tree, system image clipboard not implemented here",
                              "remaining WT visual/input/mode recovery checks require final 77/78/85 acceptance"]}
    write(root, "report.json", report)
    write(root, "manifest.json", [{"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p.read_bytes())}
                                  for p in sorted(root.rglob("*")) if p.is_file() and p.name != "manifest.json"])
    print(completed.stdout.decode("utf-8"), end="")
    print(json.dumps({"run": str(root), "technical_continue": True, "focus_exit_paths": len(focus),
                      "managed_worker_handle_exit": worker["actual_worker"]["after_close_handle_wait"], "hitl": "pending"}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        if len(sys.argv) == 2 and re.fullmatch(r"r\d+", sys.argv[1]):
            root = HERE / sys.argv[1]
            if root.is_dir() and not (root/"verification-error.txt").exists():
                (root/"verification-error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
