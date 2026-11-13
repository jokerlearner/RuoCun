"""只从唯一冻结归档校验、提取本次独立 oracle 所需四个模块。"""
import hashlib
import json
from pathlib import Path
import zipfile

root = Path.cwd()
reference = root / ".scratch/ruocun-discovery/reference/dao-f17e189-7ac654a0dc06"
target = root / ".cache/sprint06-source"
assert not target.exists()
manifest = json.loads((reference / "manifest.json").read_text(encoding="utf-8"))
hashes = {item["path"]: item["sha256"] for item in manifest["files"]}
names = ["src/client/client.ts", "src/client/responses.ts", "src/client/sse.ts", "src/config/profiles.ts"]
with zipfile.ZipFile(reference / "source.zip") as archive:
    for name in names:
        data = archive.read(name)
        assert hashlib.sha256(data).hexdigest() == hashes[name]
        output = target / name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
print(json.dumps({"verified_source_modules": names, "output": str(target)}))
