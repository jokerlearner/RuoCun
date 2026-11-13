"""Read-only archive validation; --capture NAME SOURCE is append-only collection."""
from pathlib import Path
import ctypes as C
import hashlib
import json
import os
import re
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LAB = ROOT / ".scratch/ruocun-discovery/experiments/durable-io"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def inspect(archive):
    members = json.loads(archive.with_suffix(".json").read_text(encoding="utf-8"))
    assert sha(archive.read_bytes()) == members["archive_sha256"]
    workers, rounds = [], []
    with zipfile.ZipFile(archive) as zipped:
        assert sorted(zipped.namelist()) == sorted(members["files"])
        for name, expected in members["files"].items():
            assert sha(zipped.read(name)) == expected, name
        for name in zipped.namelist():
            if name.endswith("/environment.json"):
                base = name.rsplit("/", 1)[0]
                environment = json.loads(zipped.read(name))
                for script, expected in environment["harness_sha256"].items():
                    assert sha(zipped.read(base + "/h/" + script)) == expected
                rounds.append({"round": base, "exit": json.loads(zipped.read(base + "/exit.json"))["returncode"]})
            if name.endswith("/process.json"):
                base = name.rsplit("/", 1)[0]
                process = json.loads(zipped.read(name))
                ready = json.loads(zipped.read(base + "/ready.json"))
                cleanup = json.loads(zipped.read(base + "/cleanup.json"))
                identity = (process["pid"], process["creation_time"])
                assert identity == (ready["pid"], ready["creation_time"])
                assert identity == (cleanup["pid"], cleanup["creation_time"])
                assert cleanup["held_handle_signaled"] and cleanup["same_creation_time"]
                assert cleanup["process_handle_closed"]
                if "pending_reclaimed_by_os_after_process_exit" in cleanup and cleanup["returncode"] == 96:
                    assert cleanup["pending_reclaimed_by_os_after_process_exit"]
                workers.append({"path": base, **process, "returncode": cleanup["returncode"]})
    return {"archive": archive.name, "files": len(members["files"]), "rounds": rounds,
            "workers": workers, "worker_receipts_verified": len(workers)}


def capture(name, source):
    archive = HERE / (name + ".zip")
    assert not archive.exists() and not archive.with_suffix(".json").exists()
    files = {str(path.relative_to(source)).replace("\\", "/"): path.read_bytes()
             for path in sorted(source.rglob("*")) if path.is_file()}
    # Only report category/count, never a credential value or matching line.
    credentials = [value.encode() for key, value in os.environ.items()
                   if re.search(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", key, re.I) and len(value) >= 12]
    known_values = sum(any(value in data for value in credentials) for data in files.values())
    token_shapes = sum(bool(re.search(rb"(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|gh[opusr]_[A-Za-z0-9]{24,})", data))
                       for data in files.values())
    assert known_values == 0 and token_shapes == 0, "sensitive-content scan matched; do not publish"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as zipped:
        for member, data in files.items():
            zipped.writestr(member, data)
    write(archive.with_suffix(".json"), {"archive_sha256": sha(archive.read_bytes()),
        "files": {member: sha(data) for member, data in files.items()},
        "sensitive_scan": {"known_environment_credential_matches": known_values, "token_shape_matches": token_shapes}})
    result = inspect(archive)
    sys.path.insert(0, str(LAB))
    import probe as p
    p.bind(p.K, "OpenProcess", [p.W.DWORD, p.W.BOOL, p.W.DWORD], p.W.HANDLE)
    post = []
    for worker in result["workers"]:
        C.set_last_error(0)
        handle = p.K.OpenProcess(0x100000 | 0x1000, False, worker["pid"])
        if handle:
            try:
                same = p.creation_time(handle) == worker["creation_time"]
                signaled = p.K.WaitForSingleObject(handle, 0) == 0
                post.append({"path": worker["path"], "pid": worker["pid"], "pid_reused": not same,
                             "original_exited": not same or signaled})
            finally:
                p.K.CloseHandle(handle)
        else:
            error = C.get_last_error()
            post.append({"path": worker["path"], "pid": worker["pid"], "open_error": error,
                         "original_exited": error == 87})
    assert all(item["original_exited"] for item in post)
    write(HERE / (name + "-os.json"), post)
    write(HERE / (name + "-summary.json"), result)
    return {"archive": name, "files": result["files"], "worker_receipts_verified": len(post),
            "rounds": result["rounds"], "sensitive_matches": 0}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--capture":
        print(json.dumps(capture(sys.argv[2], Path(sys.argv[3]).resolve()), indent=2))
    else:
        inventory = HERE / "evidence-sha256.json"
        if inventory.exists():
            for name, expected in json.loads(inventory.read_text(encoding="utf-8")).items():
                assert sha((HERE / name).read_bytes()) == expected, name
        results = [inspect(path) for path in sorted(HERE.glob("*.zip"))]
        print(json.dumps([{key: value for key, value in result.items() if key != "workers"}
                          for result in results], indent=2))
