"""Capture, verify and extract the exact DAO reference source without modifying it."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_ROOT = ROOT / ".scratch" / "ruocun-discovery" / "reference"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(source: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(source), *args])


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def capture(source: Path) -> Path:
    source = source.resolve(strict=True)
    head = git(source, "rev-parse", "HEAD").decode().strip()
    status_before = git(source, "status", "--porcelain=v1", "-z", "-uall")
    stage_before = git(source, "ls-files", "--stage", "-z")
    entries: dict[str, tuple[str, str]] = {}
    for record in stage_before.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, blob, stage = metadata.decode("ascii").split()
        if stage != "0":
            raise RuntimeError("Unmerged Git index; resolve before freezing reference")
        if mode == "160000":
            raise RuntimeError("Submodule needs an explicit snapshot strategy")
        entries[os.fsdecode(raw_path)] = (mode, blob)
    untracked = [os.fsdecode(p) for p in git(source, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if p]
    for name in untracked:
        entries[name] = ("100644", "")
    payloads: dict[str, bytes] = {}
    manifest_files = []
    for name in sorted(entries):
        path = source / name
        mode, blob = entries[name]
        if not path.exists() and not path.is_symlink():
            manifest_files.append({"path": name, "mode": mode, "index_blob": blob, "state": "deleted", "origin": "tracked"})
            continue
        if mode == "120000":
            data = os.readlink(path).encode("utf-8") if path.is_symlink() else path.read_bytes()
        else:
            if not path.is_file():
                raise RuntimeError(f"Expected regular source file: {name}")
            data = path.read_bytes()
        payloads[name] = data
        manifest_files.append({"path": name, "mode": mode, "index_blob": blob, "state": "present", "origin": "untracked" if name in untracked else "tracked", "bytes": len(data), "sha256": digest(data)})
    patch_head = git(source, "diff", "--binary", "--no-ext-diff", "--no-textconv", "HEAD", "--")
    patch_index = git(source, "diff", "--cached", "--binary", "--no-ext-diff", "--no-textconv", "HEAD", "--")
    manifest = {"schema": 1, "base_commit": head, "files": manifest_files}
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    tree_hash = digest(canonical)
    snapshot_id = f"dao-{head[:7]}-{tree_hash[:12]}"
    target = REFERENCE_ROOT / snapshot_id
    if target.exists():
        verify(target)
        return target
    # Re-read every source file before publishing a snapshot.
    for row in manifest_files:
        path = source / row["path"]
        if row["state"] == "deleted":
            if path.exists() or path.is_symlink():
                raise RuntimeError(f"Source changed during capture: {row['path']}")
            continue
        data = os.readlink(path).encode("utf-8") if row["mode"] == "120000" and path.is_symlink() else path.read_bytes()
        if digest(data) != row["sha256"]:
            raise RuntimeError(f"Source changed during capture: {row['path']}")
    if head != git(source, "rev-parse", "HEAD").decode().strip() or status_before != git(source, "status", "--porcelain=v1", "-z", "-uall") or stage_before != git(source, "ls-files", "--stage", "-z"):
        raise RuntimeError("Git state changed during capture; retry without using partial material")
    target.mkdir(parents=True, exist_ok=False)
    archive = target / "source.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for row in manifest_files:
            if row["state"] != "present":
                continue
            info = zipfile.ZipInfo(row["path"], date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            kind = stat.S_IFLNK if row["mode"] == "120000" else stat.S_IFREG
            permission = 0o755 if row["mode"] == "100755" else 0o644
            info.external_attr = (kind | permission) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, payloads[row["path"]])
    dump(target / "manifest.json", manifest)
    (target / "tracked-working-tree.patch").write_bytes(patch_head)
    (target / "staged-index.patch").write_bytes(patch_index)
    (target / "status.porcelain.z").write_bytes(status_before)
    (target / "index.entries.z").write_bytes(stage_before)
    metadata = {
        "snapshot_id": snapshot_id,
        "capture_date": datetime.now(timezone(timedelta(hours=8))).date().isoformat(),
        "reference_path": str(source),
        "base_commit": head,
        "source_remote": git(source, "remote", "get-url", "origin").decode().strip(),
        "source_version": json.loads(payloads["package.json"])["version"],
        "source_tree_sha256": tree_hash,
        "tracked_present": sum(r["origin"] == "tracked" and r["state"] == "present" for r in manifest_files),
        "untracked_present": sum(r["origin"] == "untracked" for r in manifest_files),
        "deleted_tracked": [r["path"] for r in manifest_files if r["state"] == "deleted"],
        "status_porcelain": git(source, "status", "--porcelain=v1", "-uall").decode("utf-8"),
        "git_version": subprocess.check_output(["git", "--version"], text=True).strip(),
        "scope": "All tracked working-tree bytes plus all non-ignored untracked files. No .git directory, ignored dependencies, credentials or runtime state.",
    }
    dump(target / "metadata.json", metadata)
    checksums = {p.name: digest(p.read_bytes()) for p in sorted(target.iterdir()) if p.is_file()}
    dump(target / "checksums.json", checksums)
    verify(target)
    return target


def verify(snapshot: Path) -> dict:
    snapshot = snapshot.resolve(strict=True)
    checksums = json.loads((snapshot / "checksums.json").read_text(encoding="utf-8"))
    for name, expected in checksums.items():
        pure = PurePosixPath(name)
        if pure.is_absolute() or len(pure.parts) != 1 or "\\" in name:
            raise RuntimeError(f"Unsafe checksum entry: {name}")
        if digest((snapshot / name).read_bytes()) != expected:
            raise RuntimeError(f"Snapshot artifact mismatch: {name}")
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    metadata = json.loads((snapshot / "metadata.json").read_text(encoding="utf-8"))
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if digest(canonical) != metadata["source_tree_sha256"]:
        raise RuntimeError("Source manifest identity mismatch")
    present = {row["path"]: row for row in manifest["files"] if row["state"] == "present"}
    with zipfile.ZipFile(snapshot / "source.zip") as bundle:
        names = bundle.namelist()
        if len(names) != len(set(names)) or set(names) != set(present):
            raise RuntimeError("Archive paths differ from manifest")
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or "\\" in name or ":" in name:
                raise RuntimeError(f"Unsafe snapshot path: {name}")
            if digest(bundle.read(name)) != present[name]["sha256"]:
                raise RuntimeError(f"Archive payload mismatch: {name}")
    return metadata


def extract(snapshot: Path, destination: Path) -> dict:
    metadata = verify(snapshot)
    destination = destination.resolve()
    if destination.exists():
        raise RuntimeError("Extraction destination must not already exist")
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    if any(row["mode"] == "120000" and row["state"] == "present" for row in manifest["files"]):
        raise RuntimeError("Symlink extraction requires an explicit platform strategy")
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(snapshot / "source.zip") as bundle:
        for row in manifest["files"]:
            if row["state"] != "present":
                continue
            path = destination / row["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bundle.read(row["path"]))
            if os.name != "nt" and row["mode"] == "100755":
                path.chmod(0o755)
    return metadata


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["capture", "verify", "extract"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.operation == "capture":
        snapshot = capture(args.path)
        output = verify(snapshot)
        output["snapshot_path"] = str(snapshot)
    elif args.operation == "verify":
        output = verify(args.path)
    else:
        if args.destination is None:
            parser.error("extract requires --destination")
        output = extract(args.path, args.destination)
        output["extracted_to"] = str(args.destination.resolve())
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
