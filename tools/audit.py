"""Inspect actual build artifacts and their verified development wheelhouse."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import tarfile
import zipfile
from email.parser import BytesParser
from importlib import metadata
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    evidence = Path(".scratch/ruocun/evidence/03-boot")
    wheel = next(Path("dist").glob("*.whl"))
    direct = next(Path(".cache/direct").glob("*.whl"))
    sdist = next(Path("dist").glob("*.tar.gz"))
    support = next(Path(".cache/supportdist").glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        members = archive.namelist()
        meta_member = next(n for n in members if n.endswith(".dist-info/METADATA"))
        info = meta_member.rsplit("/", 1)[0]
        assert all(n.startswith(("ruocun/", info + "/")) for n in members)
        assert "ruocun/resources/help.zh-CN.txt" in members
        meta = BytesParser().parsebytes(archive.read(meta_member))
        assert meta["Name"] == "ruocun" and meta["Version"] == metadata.version("ruocun")
        assert not meta.get_all("Requires-Dist")
        assert archive.read(info + "/licenses/LICENSE") == Path("LICENSE").read_bytes()
        assert archive.read(info + "/licenses/NOTICE.md") == Path("NOTICE.md").read_bytes()
    with tarfile.open(sdist) as archive:
        sdist_members = archive.getnames()
        assert not any("/tests/" in n or "/.scratch/" in n for n in sdist_members)
        assert any(n.endswith("/src/ruocun/resources/help.zh-CN.txt") for n in sdist_members)
    with zipfile.ZipFile(support) as archive:
        support_members = archive.namelist()
        assert "ruocun_acceptance/__main__.py" in support_members
        assert "oracle/network_guard.mjs" in support_members
        assert not any(n.startswith("ruocun/") for n in support_members)
    assert digest(wheel) == digest(direct), "sdist rebuild and direct wheel differ"
    wheels = json.loads((evidence / "wheels.json").read_text(encoding="utf-8"))
    for record in wheels:
        assert digest(Path(".cache/wheels") / record["wheel"]) == record["sha256"]
    result = {
        "python": sys.version, "base_executable": sys.base_prefix,
        "architecture_bits": struct.calcsize("P") * 8,
        "scope": "task03 development / installed CLI subset; not final release support",
        "tools": {name: metadata.version(name) for name in
                  ("hatchling", "build", "pytest", "ruff", "mypy")},
        "artifacts": [{"path": str(path), "size": path.stat().st_size, "sha256": digest(path)}
                      for path in (wheel, sdist, direct, support)],
        "product_wheel_members": members, "product_sdist_members": sdist_members,
        "support_wheel_members": support_members,
        "direct_and_sdist_wheels_identical": True,
        "wheelhouse_reverified": len(wheels),
        "lock_sha256": digest(Path("requirements-dev-win311.lock")),
    }
    (evidence / "artifacts.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("artifacts, resources, licenses, metadata and wheelhouse verified")


if __name__ == "__main__":
    main()
