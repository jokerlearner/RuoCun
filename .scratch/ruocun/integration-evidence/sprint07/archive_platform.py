"""Archive reviewed outputs and inspect only this run's exact synthetic cases."""

from pathlib import Path
import argparse
import json
import shutil

repo = Path(__file__).resolve().parents[4]
parser = argparse.ArgumentParser()
parser.add_argument("--phase", choices=("r1", "r2"), default="r1")
args = parser.parse_args()
state = repo / ".cache/sprint07-review"
evidence = Path(__file__).resolve().parent
labels = ("venv", "dev-tools", "platform-install", "source-prepare",
          "platform-regression", "platform-independent", "platform-transition",
          "platform-guard-window")
if args.phase == "r2":
    labels = ("platform-r2-install", "platform-r2-independent", "platform-r2-regression")
for label in labels:
    source = state / "raw" / label
    receipt = json.loads((source / "command.json").read_text(encoding="utf-8"))
    assert not receipt["sensitive_pattern_match"]
    destination = evidence / "raw" / label
    destination.mkdir(parents=True, exist_ok=False)
    for filename in ("command.json", "stdout.bin", "stderr.bin"):
        shutil.copyfile(source / filename, destination / filename)

counts = {"directories_checked": 0, "reparse_points": 0, "guards_remaining": 0}
temporary = state / "tmp/pytest-of-unknown"
for run in temporary.iterdir():
    if run.name == "pytest-current" or run.lstat().st_file_attributes & 0x400:
        continue
    for case in run.iterdir():
        if case.lstat().st_file_attributes & 0x400:
            continue  # pytest itself creates convenience aliases; never traverse them.
        for name in ("private", "alternate"):
            target = case / name
            if not target.exists():
                continue
            counts["directories_checked"] += 1
            if target.lstat().st_file_attributes & 0x400:
                counts["reparse_points"] += 1
                continue
            counts["guards_remaining"] += sum(p.name.startswith(".ruocun-guard-") for p in target.iterdir())
assert counts["reparse_points"] == counts["guards_remaining"] == 0
filename = "platform-resource-check.json" if args.phase == "r1" else "platform-r2-resource-check.json"
(evidence / filename).write_text(json.dumps(counts, indent=2) + "\n", encoding="utf-8")
print(json.dumps(counts))
