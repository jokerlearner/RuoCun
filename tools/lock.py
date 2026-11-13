"""Verify downloaded development wheels against official PyPI metadata and seal a lock."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
import zipfile
from email.parser import BytesParser
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheelhouse", type=Path)
    parser.add_argument("--output-lock", type=Path, default=Path("requirements-dev-win311.lock"))
    parser.add_argument("--evidence-dir", type=Path, default=Path(".scratch/ruocun/evidence/03-boot"))
    args = parser.parse_args()
    records = []
    for wheel in sorted(args.wheelhouse.glob("*.whl")):
        with zipfile.ZipFile(wheel) as archive:
            member = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
            metadata = BytesParser().parsebytes(archive.read(member))
        name, version = str(metadata["Name"]), str(metadata["Version"])
        endpoint = f"https://pypi.org/pypi/{name}/{version}/json"
        with urllib.request.urlopen(endpoint, timeout=60) as response:
            upstream = json.load(response)
        selected = next(item for item in upstream["urls"] if item["filename"] == wheel.name)
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        if selected["yanked"] or selected["digests"]["sha256"] != digest:
            raise ValueError(f"unverified wheel: {wheel.name}")
        records.append({
            "name": name, "version": version, "wheel": wheel.name,
            "sha256": digest, "size": wheel.stat().st_size,
            "metadata_url": endpoint, "url": selected["url"],
            "requires_dist": metadata.get_all("Requires-Dist", []),
            "requires_python": metadata["Requires-Python"],
            "license_expression": metadata["License-Expression"],
            "license": metadata["License"],
        })
    records.sort(key=lambda item: str(item["name"]).lower())
    lock = "# CPython 3.11.9 Windows x64 development closure; wheel hashes verified on PyPI.\n"
    lock += "# Not a final product support policy. Regenerate: see docs/development.md.\n"
    lock += "".join(
        f"{r['name']}=={r['version']} --hash=sha256:{r['sha256']}\n" for r in records
    )
    args.output_lock.write_text(lock, encoding="utf-8")
    evidence = args.evidence_dir
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "wheels.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"verified {len(records)} wheels; complete development lock written")


if __name__ == "__main__":
    main()
