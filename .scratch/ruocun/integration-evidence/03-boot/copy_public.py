"""Copy only the two explicitly authorized public Node/dependency inputs."""
import hashlib
import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[4]
public = Path(r"D:\java supplement\Firstcode\RuoCun\.worktrees\impl-02-oracle")
node = public / ".worktrees/oracle/node22/node_modules/node/bin/node.exe"
deps = public / ".worktrees/oracle-node22/source/node_modules"
target = root / ".cache/merge03/oracle/source/node_modules"
assert target.parent.is_dir() and not target.exists()
assert (target.parent / "package-lock.json").is_file()
shutil.copytree("\\\\?\\" + str(deps), "\\\\?\\" + str(target))
node_target = root / ".cache/merge03/node.exe"
shutil.copyfile(node, node_target)
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(node) == digest(node_target)
manifest = []
for p in Path("\\\\?\\" + str(target)).rglob("*"):
    if p.is_file():
        rel = p.relative_to(Path("\\\\?\\" + str(target))).as_posix()
        manifest.append((rel, p.stat().st_size, digest(p)))
manifest.sort()
record = {"authorization": "root message: only public Node22 exe and node_modules; no private homes/runs/dist read",
          "node_source": str(node), "node_target": str(node_target), "node_sha256": digest(node_target),
          "deps_source": str(deps), "deps_target": str(target), "files_copied": len(manifest),
          "dependency_tree_manifest_sha256": hashlib.sha256(json.dumps(manifest).encode()).hexdigest(),
          "source_lock_sha256": digest(target.parent / "package-lock.json")}
(Path(__file__).parent / "public-inputs.json").write_text(json.dumps(record, indent=2) + "\n")
print("authorized public Node22 and node_modules copied to independent owned source")
