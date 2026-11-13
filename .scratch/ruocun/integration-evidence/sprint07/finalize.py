"""Archive completed existing checks; inspect only known synthetic targets."""

from pathlib import Path
import hashlib
import json
import shutil

repo = Path(__file__).resolve().parents[4]
evidence = Path(__file__).resolve().parent
state = repo / ".cache/sprint07-review"
external = Path("C:/Users/PC/AppData/Local/Temp/RuoCun 独立wheel sprint07-20261110")
labels = (
    "wheel-venv", "store-final-install", "store-association-green",
    "store-final-ruff", "store-final-mypy", "store-final-build", "store-final-offline",
    "store-wheel-install", "store-wheel-demo", "store-wheel-isolation", "store-wheel-pip-check",
)
for label in labels:
    source = state / "raw" / label
    receipt = json.loads((source / "command.json").read_text(encoding="utf-8"))
    assert receipt["exit"] == 0 and receipt["command_joined"]
    assert not receipt["sensitive_pattern_match"]
    destination = evidence / "raw" / label
    destination.mkdir(parents=True, exist_ok=False)
    for name in ("command.json", "stdout.bin", "stderr.bin"):
        shutil.copyfile(source / name, destination / name)

wheel_report = json.loads((state / "raw/store-wheel-demo/stdout.bin").read_text(encoding="utf-8"))
assert wheel_report["status"] == "passed"
assert wheel_report["server_closed"] and wheel_report["processes_exited"]
counts = {"protected_targets_checked": 0, "protected_target_reparses": 0, "guards_remaining": 0}

def inspect(target: Path) -> None:
    try:
        info = target.lstat()
    except FileNotFoundError:
        return
    counts["protected_targets_checked"] += 1
    if info.st_file_attributes & 0x400:
        counts["protected_target_reparses"] += 1
        return
    counts["guards_remaining"] += sum(p.name.startswith(".ruocun-guard-") for p in target.iterdir())

for run in (state / "tmp/pytest-of-unknown").iterdir():
    if run.lstat().st_file_attributes & 0x400:
        continue  # Never follow pytest convenience aliases.
    for case in run.iterdir():
        if case.lstat().st_file_attributes & 0x400:
            continue
        for name in ("private", "alternate", "closed-session"):
            inspect(case / name)
for name in ("", "config", "runtime", "session"):
    inspect(external / "store-demo" / name)
assert counts["protected_target_reparses"] == counts["guards_remaining"] == 0
resource = {
    **counts, "direct_commands_joined": True,
    "wheel_demo_processes_exited": wheel_report["processes_exited"],
    "wheel_demo_server_closed": wheel_report["server_closed"],
    "scope": "exact synthetic protected targets only; fixture junctions and historical worktrees retained",
    "state_retained": True,
}
(evidence / "final-resource-check.json").write_text(json.dumps(resource, indent=2) + "\n", encoding="utf-8")
artifacts = {
    path.name: {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    for path in sorted((repo / "dist").iterdir()) if path.is_file()
}
(evidence / "artifact-hashes.json").write_text(json.dumps(artifacts, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"archived": len(labels), "resources": resource}))
