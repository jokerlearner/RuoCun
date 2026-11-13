"""独立读取 D18 新轮归档；不改 probe、原始轮次或测试期望。"""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PROBE = ROOT / ".scratch/ruocun-discovery/experiments/durable-io"
LABEL = "m18-independent-r01"
ARCHIVE = HERE / (LABEL + ".zip")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def put(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def capture():
    source = PROBE / ".t" / LABEL
    assert source.resolve().parent == (PROBE / ".t").resolve()
    assert not ARCHIVE.exists(), "refuse to overwrite independent evidence"
    files = {p.relative_to(source).as_posix(): sha(p.read_bytes())
             for p in sorted(source.rglob("*")) if p.is_file()}
    with zipfile.ZipFile(ARCHIVE, "x", compression=zipfile.ZIP_DEFLATED) as out:
        for name in files:
            out.write(source / name, LABEL + "/" + name)
    put("round-member-sha256.json", files)
    verify = subprocess.run([sys.executable, str(PROBE / "verify.py"), "--git"],
                            cwd=ROOT, capture_output=True)
    (HERE / "candidate-verify.stdout.json").write_bytes(verify.stdout)
    (HERE / "candidate-verify.stderr.txt").write_bytes(verify.stderr)
    put("candidate-verify.exit.json", {"command": [sys.executable, str(PROBE / "verify.py"), "--git"],
                                      "returncode": verify.returncode})
    assert verify.returncode == 0


def audit(live=False):
    material_manifest = HERE / "evidence-sha256.json"
    if material_manifest.exists():
        expected = json.loads(material_manifest.read_text(encoding="utf-8"))
        assert all(sha((HERE / name).read_bytes()) == digest for name, digest in expected.items())
    manifest = json.loads((HERE / "round-member-sha256.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(ARCHIVE) as archive:
        members = {p.removeprefix(LABEL + "/"): archive.read(p) for p in archive.namelist()}
    assert set(members) == set(manifest)
    assert all(sha(data) == manifest[name] for name, data in members.items())

    def obj(name):
        return json.loads(members[name])

    environment = obj("environment.json")
    assert obj("exit.json")["returncode"] == 0
    assert b"6 passed in 5.21s" in members["stdout.txt"]
    for name, digest in environment["harness_sha256"].items():
        assert sha(members["h/" + name]) == digest
    original = json.loads((HERE / "candidate-verify.stdout.json").read_text())
    assert len(original["rounds"]) == 19
    assert all(item["harness_hashes_match"] for item in original["rounds"])
    assert original["inventory_files"] == original["git_blob_bytes_verified"] == 874
    workers = []
    for name in members:
        if not name.endswith("/process.json"):
            continue
        folder = name.removesuffix("process.json")
        process, ready, cleanup = [obj(folder + suffix) for suffix in ["process.json", "ready.json", "cleanup.json"]]
        for field in ["pid", "creation_time"]:
            assert process[field] == ready[field] == cleanup[field]
        assert cleanup["held_handle_signaled"] and cleanup["same_creation_time"] and cleanup["process_handle_closed"]
        kill = obj(folder + "kill.json") if folder + "kill.json" in members else None
        if kill:
            assert kill["pid"] == process["pid"] and kill["creation_time"] == process["creation_time"]
            assert kill["requested_on_held_handle"] and kill["wait_signaled"]
        workers.append({"folder": folder, **cleanup})
    assert len(workers) == 11
    if live:
        put("post-process-state.json", live_process_audit(workers))
    paths, refusals, pipe, crash, acl = [obj(name + "/result.json") for name in ["paths", "refusals", "pipe", "crash", "acl"]]
    summary = {
        "reviewed_merge": environment["git_head"],
        "candidate": "14fcde35586374480c8ac917a2cfb4dce638e8e3",
        "archive": ARCHIVE.name, "archive_sha256": sha(ARCHIVE.read_bytes()),
        "archive_files": len(members), "archive_harness_snapshots_verified": len(environment["harness_sha256"]),
        "original_inventory_files_verified": 874, "original_round_snapshots_verified": 19,
        "pytest": {"passed": 6, "failed": 0, "seconds": 5.21},
        "all_11_workers_pid_and_creation_matched": True, "all_11_workers_held_handle_signaled_and_closed": True,
        "publish_paths": {name: {"published": item["published"], "receipt": item["receipt"],
                                  "acl_read_back": item["published_acl"]["read_back"]}
                          for name, item in paths["paths"].items()},
        "directory_flush": paths["native_directory_flush"],
        "refusals": {name: {"published": refusals[name]["published"], "elapsed": refusals[name]["elapsed"],
                             "attempts": len(refusals[name]["attempts"]),
                             "observed_winerrors": sorted({p["winerror"] for p in refusals[name]["attempts"] if not p["success"]}),
                             "receipt": refusals[name]["receipt"],
                             "error_class": refusals[name].get("error_class")}
                     for name in ["sharing-release", "denied-release", "sharing-permanent", "denied-permanent"]},
        "pipe": {"server_events_opened": pipe["server"]["events_opened"],
                 "server_events_closed": pipe["server"]["events_closed"],
                 "server_cancelled_pending": pipe["server"]["cancelled_pending"],
                 "server_handles_ready": pipe["server"]["handles_ready"],
                 "server_handles_after": pipe["server"]["handles_after"],
                 "client_events_opened": pipe["client_io"]["events_opened"],
                 "client_events_closed": pipe["client_io"]["events_closed"],
                 "pipe_absent": pipe["pipe_absent"], "connections": pipe["server"]["connections"]},
        "cold_crash_reads": {stage: crash[stage]["cold_read"] for stage in ["before-replace", "after-replace"]},
        "concurrent_readers": {name: {"reads": item["reads"], "versions_seen": len(item["versions"]),
                                      "malformed": item["malformed"], "open_errors": item["open_errors"],
                                      "successful_publications": sum(p["published"] for p in item["publications"])}
                               for name, item in crash["observers"].items()},
        "anonymous_attempt": acl["anonymous_attempt"], "independent_account": acl["independent_account"],
        "scope": "standalone Windows native probe; not product, power loss, independent-account or full Agent acceptance",
        "blocking_finding": {"kind": "static-review-only", "not_triggered_by_independent_round": True,
                             "lines": [132, 152], "pending_io_can_unwind_and_release_event_before_completion": True},
    }
    return summary


def live_process_audit(workers):
    kernel = C.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    kernel.OpenProcess.restype = W.HANDLE
    kernel.GetProcessTimes.argtypes = [W.HANDLE] + [C.POINTER(W.FILETIME)] * 4
    kernel.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
    kernel.WaitForSingleObject.restype = W.DWORD
    kernel.CloseHandle.argtypes = [W.HANDLE]
    results = []
    for worker in workers:
        C.set_last_error(0)
        handle = kernel.OpenProcess(0x101000, False, worker["pid"])
        if not handle:
            result = {"pid": worker["pid"], "expected_creation_time": worker["creation_time"],
                      "open_error": C.get_last_error()}
            assert result["open_error"] == 87, result
            result["status"] = "pid-absent"
        else:
            try:
                times = [W.FILETIME() for _ in range(4)]
                assert kernel.GetProcessTimes(handle, *[C.byref(t) for t in times])
                creation = str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
                wait = kernel.WaitForSingleObject(handle, 0)
                assert creation != worker["creation_time"] or wait == 0
                result = {"pid": worker["pid"], "expected_creation_time": worker["creation_time"],
                          "observed_creation_time": creation, "wait": wait,
                          "status": "pid-reused" if creation != worker["creation_time"] else "same-process-signaled"}
            finally:
                assert kernel.CloseHandle(handle)
        results.append(result)
    return {"method": "OpenProcess QUERY_LIMITED_INFORMATION|SYNCHRONIZE, creation time, zero-time wait; no kill",
            "all_original_workers_stopped": True, "workers": results}


if __name__ == "__main__":
    if "--capture" in sys.argv:
        capture()
        result = audit(live=True)
        put("summary.json", result)
    else:
        result = audit()
        assert result == json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    print(json.dumps({"archive_files": result["archive_files"], "original_files": 874,
                      "original_rounds": 19, "workers": 11, "pytest_passed": 6,
                      "blocking_finding": "pending I/O may be freed on abnormal cancellation; static review only"}, indent=2))
