"""Read the approved task graph and report the live dependency frontier."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EFFORT = ROOT / ".scratch" / "ruocun"
PRODUCT_INPUTS = ("src", "tests", "tools", "pyproject.toml", "requirements-dev.in", "requirements-dev-win311.lock")


def field(path: Path, key: str, default: str = "") -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return default
    matches = re.findall(rf"^\**{re.escape(key)}\**[:：][ \t]*(.*)$", text, re.MULTILINE)
    return matches[0].strip() if len(matches) == 1 else default


def evidence_path(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not re.fullmatch(r"\.scratch/ruocun/[A-Za-z0-9_./-]+", value):
        raise ValueError("invalid evidence path")
    if any(part in ("", ".", "..", ".git") for part in value.split("/")):
        raise ValueError("non-canonical evidence path")
    path = (root / value).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("evidence outside repository")
    return path


def checked_file(root: Path, reference: dict) -> Path:
    path = evidence_path(root, reference["path"])
    expected = reference["sha256"]
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("invalid evidence hash")
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("evidence hash mismatch")
    return path


def evidence_json(path: Path) -> dict:
    def unique_fields(pairs: list) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_fields)


def git_read(root: Path, *arguments: str) -> bytes:
    executable = shutil.which("git")
    if not executable:
        raise ValueError("Git unavailable")
    state = root / ".cache" / "issue-graph"
    env = {
        "SYSTEMROOT": r"C:\Windows", "PATH": os.pathsep.join([str(Path(executable).parent), r"C:\Windows\System32"]),
        "HOME": str(state), "USERPROFILE": str(state), "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
    }
    result = subprocess.run(
        [executable, "--no-pager", "--no-replace-objects", "-c", "core.fsmonitor=false",
         "-C", str(root), *arguments], env=env, capture_output=True, timeout=10,
    )
    if result.returncode:
        raise ValueError("Git verification failed")
    return result.stdout


def check_integration(root: Path, parent: Path, evidence: Path, manifest: dict) -> None:
    product = manifest["product_commit"]
    review = manifest["review_commit"]
    integration = manifest["integration_commit"]
    for commit in (product, review, integration):
        if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError("full commit required")
        if git_read(root, "rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip() != commit:
            raise ValueError("commit mismatch")
    if review == product:
        raise ValueError("review must follow product")
    git_read(root, "merge-base", "--is-ancestor", product, review)
    git_read(root, "merge-base", "--is-ancestor", review, integration)
    git_read(root, "merge-base", "--is-ancestor", integration, "HEAD")
    # An exit is stale after its tested product inputs change, even if old evidence remains.
    git_read(root, "diff", "--quiet", "--no-ext-diff", "--no-textconv", product, "--",
             *PRODUCT_INPUTS)
    if git_read(root, "ls-files", "--others", "--exclude-standard", "--", *PRODUCT_INPUTS):
        raise ValueError("untracked product inputs")
    for path in (parent, evidence, root / ".scratch/ruocun/task-graph.json"):
        relative = path.relative_to(root).as_posix()
        if git_read(root, "show", f"HEAD:{relative}") != path.read_bytes():
            raise ValueError("uncommitted publication")
    references = [manifest["matrix"], manifest["review"], *(case["evidence"] for case in manifest["cases"])]
    for reference in references:
        path = evidence_path(root, reference["path"])
        if git_read(root, "show", f'{integration}:{reference["path"]}') != path.read_bytes():
            raise ValueError("unintegrated or stale evidence")
        if git_read(root, "show", f'HEAD:{reference["path"]}') != path.read_bytes():
            raise ValueError("evidence changed after integration")
    review_path = manifest["review"]["path"]
    if git_read(root, "show", f"{review}:{review_path}") != evidence_path(root, review_path).read_bytes():
        raise ValueError("review commit does not contain the recorded review")


def check_matrix(root: Path, manifest: dict, parent_task: dict) -> None:
    if manifest["matrix"]["path"] != ".scratch/ruocun/acceptance-matrix.md":
        raise ValueError("authoritative matrix required")
    text = checked_file(root, manifest["matrix"]).read_text(encoding="utf-8")
    header = ["Automatic ticket", "Case/subcase", "Result", "Product commit", "Evidence", "SHA-256", "Review"]
    families = set(parent_task["cases"])
    mothers = set()
    rows = []
    in_table = False
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            in_table = False
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        mothers.add(re.sub(r"<[^>]*>", "", cells[0]).strip())
        if cells == header:
            in_table = True
        elif in_table and cells[0] == manifest["ticket"]:
            if len(cells) != 7:
                raise ValueError("invalid automatic matrix row")
            rows.append(cells)
    cases = {case["id"]: case["evidence"] for case in manifest["cases"]}
    if len(cases) != len(manifest["cases"]) or len(rows) != len(cases):
        raise ValueError("missing or duplicate automatic case")
    if {row[1] for row in rows} != set(cases):
        raise ValueError("matrix case set mismatch")
    if {case.split(".", 1)[0] for case in cases} != families or not families <= mothers:
        raise ValueError("case family coverage mismatch")
    for row in rows:
        case = row[1]
        if not re.fullmatch(r"[A-Z]+-[0-9]{2}\.[A-Za-z0-9][A-Za-z0-9_.-]*", case):
            raise ValueError("stable subcase ID required")
        expected = [manifest["ticket"], case, "passed", manifest["product_commit"],
                    cases[case]["path"], cases[case]["sha256"], manifest["review"]["path"]]
        if row != expected:
            raise ValueError("matrix result or evidence mismatch")


def check_review(root: Path, manifest: dict) -> None:
    review = evidence_json(checked_file(root, manifest["review"]))
    if type(review["schema_version"]) is not int or review["schema_version"] != 1:
        raise ValueError("invalid review schema")
    for key in ("ticket", "product_commit", "implementer"):
        if review[key] != manifest[key]:
            raise ValueError("review target mismatch")
    identities = [review["implementer"], review["reviewer"]]
    if any(not isinstance(name, str) or not name.strip() or name.strip().casefold() in
           ("none", "unknown", "pending") for name in identities):
        raise ValueError("review identity missing")
    if identities[0].strip().casefold() == identities[1].strip().casefold():
        raise ValueError("independent reviewer required")
    cases = [case["id"] for case in manifest["cases"]]
    if review["status"] != "passed" or not isinstance(review["cases"], list):
        raise ValueError("review not passed")
    if len(review["cases"]) != len(cases) or set(review["cases"]) != set(cases):
        raise ValueError("review case set mismatch")


def automatic_reason(root: Path, parent: Path, parent_task: dict) -> str:
    if field(parent, "Automatic exit") != "passed":
        return "automatic-exit-not-passed"
    failure = "invalid-automatic-evidence"
    try:
        evidence = evidence_path(root, field(parent, "Automatic evidence"))
        manifest = evidence_json(evidence)
        if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
            return "invalid-automatic-evidence"
        if manifest["ticket"] != parent.relative_to(root).as_posix():
            return "automatic-ticket-mismatch"
        if not isinstance(manifest["cases"], list) or not manifest["cases"]:
            return "automatic-cases-missing"
        for case in manifest["cases"]:
            checked_file(root, case["evidence"])
        checked_file(root, manifest["matrix"])
        checked_file(root, manifest["review"])
        failure = "automatic-integration-invalid"
        check_integration(root, parent, evidence, manifest)
        failure = "automatic-matrix-invalid"
        check_matrix(root, manifest, parent_task)
        failure = "automatic-review-invalid"
        check_review(root, manifest)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError):
        return failure
    return ""


def read_graph(root: Path | None = None) -> dict:
    root = (root or ROOT).resolve()
    effort = root / ".scratch" / "ruocun"
    tasks = json.loads((effort / "task-graph.json").read_text(encoding="utf-8"))
    by_key = {task["key"]: task for task in tasks}
    decisions = {"D" + p.name[:2]: p for p in (root / ".scratch/ruocun-discovery/issues").glob("*.md")}
    records = []
    for task in tasks:
        path = effort / "issues" / f'{task["id"]:02d}-{task["key"]}.md'
        blockers = []
        reasons = {}
        dependencies = list(task["deps"])
        if task["id"] == 85:
            dependencies = list(dict.fromkeys([*dependencies, "wtaccept", "wincaps"]))
        for key in dependencies:
            parent_task = by_key.get(key)
            if key.startswith("D"):
                parent = decisions.get(key)
            elif parent_task:
                parent = effort / "issues" / f'{parent_task["id"]:02d}-{key}.md'
            else:
                parent = None
            if parent is None:
                missing = f"missing:{key}"
                blockers.append(missing)
                reasons[missing] = "dependency-record-missing"
                continue
            exits = task.get("dependency_exits", {})
            declaration = exits.get(key) if isinstance(exits, dict) else "invalid"
            if task["id"] == 85 and key in ("wtaccept", "wincaps"):
                reason = "" if field(parent, "Status") == "resolved" and field(parent, "用户体验验收") == "accepted" else "full-user-acceptance-required"
            elif declaration is not None:
                allowed = (task["id"], task["key"], key, parent_task["id"] if parent_task else None) in {(79, "wheel", "wincaps", 78), (84, "winintegrate", "wtaccept", 77)}
                reason = automatic_reason(root, parent, by_key[key]) if allowed and declaration == "automatic" else "unsupported-dependency-exit"
            else:
                reason = "dependency-not-resolved" if field(parent, "Status") != "resolved" else ""
            if reason:
                relative = parent.relative_to(root).as_posix()
                blockers.append(relative)
                reasons[relative] = reason
        records.append({"id": task["id"], "key": task["key"], "title": task["title"], "path": str(path.relative_to(root)).replace("\\", "/"), "status": field(path, "Status"), "assignee": field(path, "Assignee", "none"), "unresolved_dependencies": blockers, "dependency_blockers": reasons})
    counts = collections.Counter(record["status"] for record in records)
    return {"implementation_tickets": len(records), "statuses": dict(counts), "frontier": [record for record in records if record["status"] in ("ready-for-agent", "blocked", "open") and record["assignee"] == "none" and not record["unresolved_dependencies"]], "tasks": records}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--mermaid", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (defaults to this script's repository)")
    args = parser.parse_args()
    graph = read_graph(args.root)
    if args.mermaid:
        tasks = json.loads((args.root / ".scratch/ruocun/task-graph.json").read_text(encoding="utf-8"))
        ids = {task["key"]: f'I{task["id"]:02d}' for task in tasks}
        print("flowchart TD")
        for task in tasks:
            node = ids[task["key"]]
            print(f'  {node}["{task["id"]:02d} {task["title"]}"]')
            for dep in task["deps"]:
                print(f"  {ids.get(dep, dep)} --> {node}")
    elif args.json:
        print(json.dumps(graph, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({key: graph[key] for key in ("implementation_tickets", "statuses", "frontier")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    main()
