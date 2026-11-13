"""Seal only this independent repair round; preserve all prior evidence unchanged."""
import hashlib
import io
import json
import os
import re
import tarfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
EXTERNAL = Path(r"C:\Users\PC\AppData\Local\Temp\RCm03 1105 中文 空格")
digest = lambda data: hashlib.sha256(data).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def archive(name, pairs):
    rows = []
    with zipfile.ZipFile(HERE / name, "w", zipfile.ZIP_DEFLATED) as z:
        for member, source in sorted(pairs):
            data = source.read_bytes()
            z.writestr(member, data)
            rows.append({"path": member, "size": len(data), "sha256": digest(data)})
    with zipfile.ZipFile(HERE / name) as z:
        assert set(z.namelist()) == {x["path"] for x in rows}
        assert all(digest(z.read(x["path"])) == x["sha256"] for x in rows)
    return {"archive": name, "sha256": digest((HERE / name).read_bytes()), "members": rows}


raw_pairs = []
for prefix, folder in (("engineering", HERE / "state/raw"),
                       ("pytest", ROOT / ".cache/merge03/r2/pytest"),
                       ("outside-faults", EXTERNAL / "r2-faults"),
                       ("outside-offline", EXTERNAL / "r2-offline")):
    raw_pairs.extend((prefix + "/" + p.relative_to(folder).as_posix(), p)
                     for p in folder.rglob("*") if p.is_file())
manifest = archive("raw.zip", raw_pairs)
write("raw-manifest.json", manifest)
artifact_pairs = []
for name in ("product", "support"):
    folder = ROOT / ".cache/merge03/r2" / name
    artifact_pairs.extend((name + "/" + p.name, p) for p in folder.iterdir() if p.is_file())
write("artifact-manifest.json", archive("artifacts.zip", artifact_pairs))
commands = [json.loads(p.read_text()) for p in sorted((HERE / "state/raw").glob("*/command.json"))]
assert len(commands) == 13 and all(c["exit"] == 0 and not c["sensitive_match"] for c in commands)
write("commands.json", commands)
faults = json.loads((HERE / "faults.json").read_text(encoding="utf-8"))
offline = json.loads((EXTERNAL / "r2-offline/summary.json").read_text(encoding="utf-8"))
assert len(faults) == 4 and len(offline["cases"]) == 4
assert offline["logical_exit"] == 0 and all(c["status"] == "passed" for c in offline["cases"])
assert all(p["real_exit"] is not None and p["streams_closed"]
           for test in faults.values() for p in test["reviewer_cleanup"])
write("result.json", {"candidate": "90efe4f7a271c8c39f9fc6d35479bdeed6813028",
                      "merge": "e11a20d9cc004c8d2fc02170dd112fa21f3ae6b9",
                      "status": "passed-for-task03-defined-paths", "default_pytest": {"passed": 29, "deselected": 3},
                      "mypy_source_files": 11, "independent_real_child_boundary_checks": 4,
                      "outside_final_wheel_offline_passed": 4, "engineering_commands": len(commands),
                      "prior_source_oracle": {"passed": 12, "rerun": False, "unchanged_inputs_verified": True},
                      "prior_failure_evidence_preserved": True, "owned_children_reaped": True,
                      "paid_model_calls": 0, "task04_started": False,
                      "scope": "ENT-01/TEST-07 task03 child paths; not full Agent/TUI/SQLite/release/terminal acceptance"})
values = [v.encode() for n, v in os.environ.items()
          if re.search("KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", n, re.I) and len(v) >= 8]
hit = False


def scan(data):
    global hit
    hit = hit or any(v in data for v in values)
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for member in z.namelist():
                scan(z.read(member))
    elif data[:2] == b"\x1f\x8b":
        try:
            with tarfile.open(fileobj=io.BytesIO(data)) as t:
                for member in t.getmembers():
                    if member.isfile():
                        scan(t.extractfile(member).read())
        except tarfile.TarError:
            pass


paths = [p for p in HERE.iterdir() if p.is_file()]
for folder in (ROOT / "src", ROOT / "tests", ROOT / "tools"):
    paths.extend(p for p in folder.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
paths.extend(ROOT / n for n in ("pyproject.toml", "requirements-dev.in", "requirements-dev-win311.lock", ".gitattributes", ".gitignore", "LICENSE", "NOTICE.md"))
paths.extend(p for _, p in artifact_pairs)
paths.extend((ROOT / ".cache/merge03/wheels").glob("*.whl"))
paths.extend((ROOT / ".scratch/ruocun/evidence/03-boot").rglob("*.zip"))
paths.extend((HERE.parent).glob("*.zip"))
for path in set(paths):
    scan(path.read_bytes())
write("scan.json", {"sensitive_values_present": bool(values), "sensitive_match": hit,
                    "secret_names_or_values_logged": False,
                    "scope": "maintained sources/config; prior/current raw and artifact ZIP members; new package tar members; 18 development wheels"})
assert not hit
assert all(len(p.relative_to(ROOT).as_posix()) <= 150 for p in HERE.iterdir() if p.is_file())
print(json.dumps({"commands": len(commands), "raw_members": len(manifest["members"]), "sensitive_match": hit}))
