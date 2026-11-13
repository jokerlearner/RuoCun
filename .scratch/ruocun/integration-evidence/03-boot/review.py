"""Independent Task03 read-only artifact and closure checks; no product edits."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
import tarfile
import urllib.request
import zipfile
from email.parser import BytesParser
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save(name: str, data: object) -> None:
    (EVIDENCE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def closure() -> None:
    from packaging.markers import default_environment
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
    from packaging.version import Version
    wheelhouse = ROOT / ".cache/merge03/wheels"
    rows = {}
    lock = {}
    for line in (ROOT / "requirements-dev-win311.lock").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        name, version, digest = re.fullmatch(r"([^=]+)==([^ ]+) --hash=sha256:([0-9a-f]{64})", line).groups()
        lock[canonicalize_name(name)] = (version, digest)
    env = default_environment()
    env["extra"] = ""
    for wheel in sorted(wheelhouse.glob("*.whl")):
        with zipfile.ZipFile(wheel) as z:
            member = next(n for n in z.namelist() if n.endswith(".dist-info/METADATA"))
            meta = BytesParser().parsebytes(z.read(member))
        name, ver = canonicalize_name(meta["Name"]), str(meta["Version"])
        digest = sha(wheel.read_bytes())
        assert lock[name] == (ver, digest)
        endpoint = f"https://pypi.org/pypi/{name}/{ver}/json"
        with urllib.request.urlopen(endpoint, timeout=60) as response:
            data = response.read()
        official = json.loads(data)
        selected = next(x for x in official["urls"] if x["filename"] == wheel.name)
        assert not selected["yanked"] and selected["digests"]["sha256"] == digest
        active = []
        for raw in meta.get_all("Requires-Dist", []):
            req = Requirement(raw)
            if req.marker is None or req.marker.evaluate(env):
                key = canonicalize_name(req.name)
                assert key in lock and Version(lock[key][0]) in req.specifier, raw
                active.append(raw)
        rows[name] = {"version": ver, "wheel": wheel.name, "sha256": digest,
                      "official_metadata": endpoint, "official_response_sha256": sha(data),
                      "active_requires_dist": active}
    assert len(rows) == len(lock) == 18 and set(rows) == set(lock)
    expected = {"hatchling": "1.33.0", "build": "1.6.1", "pytest": "8.4.2", "ruff": "0.17.3", "mypy": "2.4.1"}
    assert all(rows[n]["version"] == v for n, v in expected.items())
    assert platform.python_version() == "3.11.9" and sys.maxsize > 2 ** 32
    save("closure.json", {"packages": rows, "closure_complete": True, "count": len(rows),
                          "tools": {n: metadata.version(n) for n in expected}, "python": sys.version})
    print("18 wheels: hashes, official fixed metadata, activated dependency closure verified")


def artifacts() -> None:
    wheel = next((ROOT / "dist").glob("*.whl"))
    direct = next((ROOT / ".cache/merge03/direct").glob("*.whl"))
    sdist = next((ROOT / "dist").glob("*.tar.gz"))
    support = next((ROOT / ".cache/merge03/support").glob("*.whl"))
    with zipfile.ZipFile(wheel) as z:
        names = z.namelist()
        metaname = next(n for n in names if n.endswith(".dist-info/METADATA"))
        prefix = metaname.rsplit("/", 1)[0]
        meta = BytesParser().parsebytes(z.read(metaname))
        assert meta["Name"] == "ruocun" and meta["Version"] == "0.1.0.dev0"
        assert not meta.get_all("Requires-Dist")
        assert all(n.startswith(("ruocun/", prefix + "/")) for n in names)
        assert "ruocun/resources/help.zh-CN.txt" in names
        for n in ("LICENSE", "NOTICE.md"):
            assert z.read(prefix + "/licenses/" + n) == (ROOT / n).read_bytes()
        assert b"Copyright (c) 2026 DAO CODE contributors" in z.read(prefix + "/licenses/LICENSE")
        with zipfile.ZipFile(direct) as zd:
            assert set(zd.namelist()) == set(names)
            assert all(z.read(n) == zd.read(n) for n in names)
    assert sha(wheel.read_bytes()) == sha(direct.read_bytes())
    with tarfile.open(sdist) as t:
        sdist_names = t.getnames()
        assert not any("/tests/" in n or "/.scratch/" in n for n in sdist_names)
        assert any(n.endswith("/src/ruocun/resources/help.zh-CN.txt") for n in sdist_names)
    with zipfile.ZipFile(support) as z:
        support_names = z.namelist()
        assert "oracle/network_guard.mjs" in support_names
        assert "ruocun_acceptance/driver.py" in support_names
        assert not any(n.startswith("ruocun/") for n in support_names)
        meta = BytesParser().parsebytes(z.read(next(n for n in support_names if n.endswith(".dist-info/METADATA"))))
        assert not meta.get_all("Requires-Dist")
    save("artifacts.json", {"artifacts": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p.read_bytes()), "size": p.stat().st_size} for p in (wheel, direct, sdist, support)],
                            "product_wheel_members": names, "sdist_members": sdist_names,
                            "support_members": support_names, "direct_sdist_identical": True})
    print("artifact members, metadata, real resource, original MIT/NOTICE and direct/sdist wheel identity verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("closure", "artifacts"))
    args = parser.parse_args()
    {"closure": closure, "artifacts": artifacts}[args.mode]()
