"""Read only the frozen archive and export selected, hash-verified source files."""

from pathlib import Path
import hashlib
import json
import zipfile

repo = Path(__file__).resolve().parents[4]
reference = repo / ".scratch/ruocun-discovery/reference/dao-f17e189-7ac654a0dc06"
manifest = json.loads((reference / "manifest.json").read_text(encoding="utf-8"))
wanted = {
    "src/session/durable_file.ts", "src/session/durable_store.ts",
    "src/session/durable_store.test.ts", "src/session/sqlite.ts",
    "src/session/process_identity.ts", "src/session/process_identity.test.ts",
    "src/session/log.ts", "src/session/log.test.ts", "src/session/session.ts",
    "src/session/session.test.ts",
}
destination = repo / ".cache/sprint07-review/source"
destination.mkdir(exist_ok=False)
verified = []
with zipfile.ZipFile(reference / "source.zip") as archive:
    for item in manifest["files"]:
        if item["path"] not in wanted:
            continue
        data = archive.read(item["path"])
        assert len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        target = destination / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        verified.append({"path": item["path"], "sha256": item["sha256"]})
assert len(verified) == len(wanted)
print(json.dumps({"archive_sha256": hashlib.sha256((reference / "source.zip").read_bytes()).hexdigest(), "verified": verified}, indent=2))
