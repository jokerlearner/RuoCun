"""Verify unchanged prior independent inputs and newly built package contents."""
import hashlib
import json
import zipfile
from email.parser import BytesParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent
ROOT = HERE.parents[4]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
unchanged = []
for record in json.loads((PRIOR / "source-inputs.json").read_text()):
    if record["path"] not in (".gitattributes", "tests/support/ruocun_acceptance/driver.py"):
        assert sha(ROOT / record["path"]) == record["sha256"], record["path"]
        unchanged.append(record)
for record in json.loads((PRIOR / "closure.json").read_text())["packages"].values():
    assert sha(ROOT / ".cache/merge03/wheels" / record["wheel"]) == record["sha256"]
for manifest_name in ("raw-manifest.json", "artifact-manifest.json"):
    manifest = json.loads((PRIOR / manifest_name).read_text())
    assert sha(PRIOR / manifest["archive"]) == manifest["sha256"]
new_product = ROOT / ".cache/merge03/r2/product/ruocun-0.1.0.dev0-py3-none-any.whl"
old_product = ROOT / "dist/ruocun-0.1.0.dev0-py3-none-any.whl"
assert sha(new_product) == sha(old_product) == "feeb2e2d77d3aaeede79681536f90a8955faef8fbc68d054928626ab84e99a8c"
support = ROOT / ".cache/merge03/r2/support/ruocun_dev_support-0.1.0-py3-none-any.whl"
old_support = ROOT / ".cache/merge03/support/ruocun_dev_support-0.1.0-py3-none-any.whl"
with zipfile.ZipFile(support) as new, zipfile.ZipFile(old_support) as old:
    assert set(new.namelist()) == set(old.namelist())
    changed = [n for n in new.namelist() if new.read(n) != old.read(n)]
    assert set(changed) == {"ruocun_acceptance/driver.py", "ruocun_dev_support-0.1.0.dist-info/RECORD"}
    meta = BytesParser().parsebytes(new.read("ruocun_dev_support-0.1.0.dist-info/METADATA"))
    assert not meta.get_all("Requires-Dist")
    assert new.read("ruocun_acceptance/driver.py") == (ROOT / "tests/support/ruocun_acceptance/driver.py").read_bytes()
    assert b"Copyright (c) 2026 DAO CODE contributors" in new.read("ruocun_dev_support-0.1.0.dist-info/licenses/LICENSE")
artifacts = []
for folder in (ROOT / ".cache/merge03/r2/product", ROOT / ".cache/merge03/r2/support"):
    artifacts.extend({"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p), "size": p.stat().st_size}
                     for p in folder.iterdir() if p.is_file())
result = {"unchanged_prior_inputs": unchanged, "prior_raw_and_artifact_archives_unchanged": True,
          "development_wheels_reverified": 18, "new_support_changed_members": changed,
          "product_wheel_unchanged": True, "artifacts": artifacts,
          "new_inputs": [{"path": n, "sha256": sha(ROOT / n)} for n in
                         ("tests/support/ruocun_acceptance/driver.py", "tests/test_acceptance_process.py", ".gitattributes")]}
(HERE / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("unchanged prior input hashes/18 wheels/old archives and new product/support artifact contents verified")
