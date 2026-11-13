"""Read-only sealing and silent secret-value scan; never executes test/build commands."""
import hashlib
import io
import json
import os
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EXTERNAL = Path(r"C:\Users\PC\AppData\Local\Temp\RCm03 1105 中文 空格")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def archive(name, files):
    manifest = []
    with zipfile.ZipFile(HERE / name, "w", zipfile.ZIP_DEFLATED) as z:
        for member, path in sorted(files):
            raw = path.read_bytes()
            z.writestr(member, raw)
            manifest.append({"path": member, "size": len(raw), "sha256": digest(raw)})
    with zipfile.ZipFile(HERE / name) as z:
        assert set(z.namelist()) == {x["path"] for x in manifest}
        assert all(digest(z.read(x["path"])) == x["sha256"] for x in manifest)
    return {"archive": name, "sha256": digest((HERE / name).read_bytes()), "members": manifest}


raw_files = []
for prefix, folder in (("engineering", HERE / "state/raw"),
                       ("external-checks", EXTERNAL / "checks"),
                       ("external-outputs", EXTERNAL / "outputs"),
                       ("external-faults", EXTERNAL / "faults"),
                       ("external-deadline", EXTERNAL / "deadline"),
                       ("oracle12", ROOT / ".cache/merge03/oracle-pytest")):
    raw_files.extend((prefix + "/" + p.relative_to(folder).as_posix(), p)
                     for p in folder.rglob("*") if p.is_file())
for p in (ROOT / ".cache/merge03/oracle").glob("build.*.txt"):
    raw_files.append(("oracle-build/" + p.name, p))
raw_manifest = archive("raw.zip", raw_files)
write_json("raw-manifest.json", raw_manifest)
artifact_files = [("product/" + p.name, p) for p in (ROOT / "dist").iterdir() if p.is_file()]
artifact_files += [("support/" + p.name, p) for p in (ROOT / ".cache/merge03/support").iterdir() if p.is_file()]
artifact_files += [("direct/" + p.name, p) for p in (ROOT / ".cache/merge03/direct").iterdir() if p.is_file()]
write_json("artifact-manifest.json", archive("artifacts.zip", artifact_files))
commands = [json.loads(p.read_text()) for p in sorted((HERE / "state/raw").glob("*/command.json"))]
write_json("commands.json", commands)
maintained = []
for directory in ("src", "tests", "tools"):
    maintained.extend(p for p in (ROOT / directory).rglob("*") if p.is_file()
                      and "__pycache__" not in p.parts and p.suffix != ".pyc")
maintained += [ROOT / name for name in ("pyproject.toml", "requirements-dev.in", "requirements-dev-win311.lock",
                                      ".gitattributes", ".gitignore", "LICENSE", "NOTICE.md", "README.md", "docs/development.md")]
write_json("source-inputs.json", [{"path": p.relative_to(ROOT).as_posix(), "sha256": digest(p.read_bytes())}
                                 for p in sorted(set(maintained))])
values = [value.encode() for name, value in os.environ.items()
          if re.search("KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", name, re.I) and len(value) >= 8]
hit = False


def scan(data):
    global hit
    hit = hit or any(value in data for value in values)
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for name in z.namelist():
                scan(z.read(name))


for path in set(maintained + [p for p in HERE.iterdir() if p.is_file()]
                + list((ROOT / ".cache/merge03/wheels").glob("*.whl"))
                + list((ROOT / ".scratch/ruocun/evidence/03-boot").glob("*.zip"))):
    scan(path.read_bytes())
write_json("scan.json", {"sensitive_values_present": bool(values), "sensitive_match": hit,
                         "scope": "maintained sources/configs/licenses; all new evidence including ZIP members; product/support/development wheels; candidate raw/artifact ZIP members",
                         "secret_names_or_values_logged": False})
assert not hit
assert all(len(p.relative_to(ROOT).as_posix()) <= 150 for p in HERE.iterdir() if p.is_file())
print(json.dumps({"sealed_raw_members": len(raw_manifest["members"]), "commands": len(commands), "sensitive_match": hit}))
