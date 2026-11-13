"""ADR-0006 dependency gates, exercised through the public graph reader."""

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / ".scratch/ruocun/issue_graph.py"
spec = importlib.util.spec_from_file_location("issue_graph", SCRIPT)
graph_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graph_tool)
GIT = shutil.which("git") or r"D:\study_software\Git\cmd\git.exe"


class Repository:
    def __init__(self, root):
        self.root = root
        self.tasks = [
            {"id": 78, "key": "wincaps", "title": "Windows", "deps": [], "cases": ["WIN-01"]},
            {"id": 79, "key": "wheel", "title": "Wheel", "deps": ["wincaps"],
             "dependency_exits": {"wincaps": "automatic"}, "cases": ["PKG-01"]},
        ]
        self.write(".scratch/ruocun/task-graph.json", self.tasks)
        self.write("src/product.py", "# synthetic product\n")
        self.write(".scratch/ruocun/issues/78-wincaps.md", "Status: awaiting-user\nAssignee: none\n用户体验验收：pending\n")
        self.write(".scratch/ruocun/issues/79-wheel.md", "Status: blocked\nAssignee: none\n")
        self.git("init", "--quiet")
        self.git("config", "user.name", "Synthetic Developer")
        self.git("config", "user.email", "synthetic@example.invalid")
        self.product = self.commit()

    def write(self, path, value):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(value, ensure_ascii=False, indent=2) + "\n" if not isinstance(value, str) else value
        destination.write_text(text, encoding="utf-8")
        return destination

    def git(self, *args):
        env = {"SYSTEMROOT": r"C:\Windows", "PATH": str(Path(GIT).parent),
               "HOME": str(self.root / "home"), "USERPROFILE": str(self.root / "home"),
               "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
               "GIT_TERMINAL_PROMPT": "0"}
        return subprocess.run([GIT, "-C", str(self.root), *args], env=env, check=True,
                              capture_output=True, text=True, encoding="utf-8").stdout.strip()

    def commit(self):
        self.git("add", ".")
        self.git("commit", "--quiet", "--allow-empty", "-m", "synthetic fixture")
        return self.git("rev-parse", "HEAD")

    def automatic(self, terminal=False):
        family = "WT-01" if terminal else "WIN-01"
        self.case_id = family + ".process"
        if terminal:
            self.tasks = [
                {"id": 77, "key": "wtaccept", "title": "Terminal", "deps": [], "cases": [family]},
                {"id": 84, "key": "winintegrate", "title": "Integration", "deps": ["wtaccept"],
                 "dependency_exits": {"wtaccept": "automatic"}, "cases": ["TEST-01"]},
            ]
            self.write(".scratch/ruocun/task-graph.json", self.tasks)
            self.write(".scratch/ruocun/issues/84-winintegrate.md", "Status: blocked\nAssignee: none\n")
        self.ticket = ".scratch/ruocun/issues/77-wtaccept.md" if terminal else ".scratch/ruocun/issues/78-wincaps.md"
        self.evidence = ".scratch/ruocun/evidence/windows.txt"
        self.review = ".scratch/ruocun/evidence/review.json"
        self.matrix = ".scratch/ruocun/acceptance-matrix.md"
        self.manifest = ".scratch/ruocun/evidence/automatic.json"
        self.write(self.evidence, "synthetic Windows product verification\n")
        evidence_hash = hashlib.sha256((self.root / self.evidence).read_bytes()).hexdigest()
        self.review_data = {"schema_version": 1, "ticket": self.ticket,
                            "product_commit": self.product, "implementer": "developer",
                            "reviewer": "independent-reviewer", "status": "passed",
                            "cases": [self.case_id]}
        self.write(self.review, self.review_data)
        self.write(self.matrix,
                   f"| ID | 原功能 |\n| --- | --- |\n| {family} | Windows product |\n\n"
                   "| Automatic ticket | Case/subcase | Result | Product commit | Evidence | SHA-256 | Review |\n"
                   "| --- | --- | --- | --- | --- | --- | --- |\n"
                   f"| {self.ticket} | {self.case_id} | passed | {self.product} | {self.evidence} | {evidence_hash} | {self.review} |\n")
        integration = self.commit()
        self.manifest_data = {
            "schema_version": 1, "ticket": self.ticket, "product_commit": self.product,
            "review_commit": integration, "integration_commit": integration, "implementer": "developer",
            "matrix": {"path": self.matrix, "sha256": hashlib.sha256((self.root / self.matrix).read_bytes()).hexdigest()},
            "cases": [{"id": self.case_id, "evidence": {"path": self.evidence, "sha256": evidence_hash}}],
            "review": {"path": self.review, "sha256": hashlib.sha256((self.root / self.review).read_bytes()).hexdigest()},
        }
        self.publish()

    def publish(self):
        self.write(self.manifest, self.manifest_data)
        self.write(self.ticket, f"Status: awaiting-user\nAssignee: none\nAutomatic exit: passed\nAutomatic evidence: {self.manifest}\n用户体验验收：pending\n")
        self.commit()

    def graph(self):
        return graph_tool.read_graph(self.root)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", os.pathsep.join([str(Path(GIT).parent), str(Path(sys.executable).parent), r"C:\Windows\System32"]))
    return Repository(tmp_path)


def test_declared_79_edge_accepts_integrated_reviewed_78_automatic_exit(repo):
    repo.automatic()
    assert [item["id"] for item in repo.graph()["frontier"]] == [79]


def test_changed_product_evidence_cannot_unlock_automatic_edge(repo):
    repo.automatic()
    repo.write(repo.evidence, "changed after verification\n")
    repo.commit()
    assert repo.graph()["frontier"] == []


def test_nonexistent_integration_commit_cannot_unlock_automatic_edge(repo):
    repo.automatic()
    repo.manifest_data["integration_commit"] = "f" * 40
    repo.publish()
    assert repo.graph()["frontier"] == []


def test_manifest_cannot_override_failed_authoritative_matrix_case(repo):
    repo.automatic()
    matrix = repo.root / repo.matrix
    repo.write(repo.matrix, matrix.read_text(encoding="utf-8").replace("| passed |", "| failed |"))
    repo.manifest_data["matrix"]["sha256"] = hashlib.sha256(matrix.read_bytes()).hexdigest()
    repo.manifest_data["integration_commit"] = repo.commit()
    repo.publish()
    assert repo.graph()["frontier"] == []


def test_implementer_cannot_supply_their_own_independent_review(repo):
    repo.automatic()
    repo.review_data["reviewer"] = "developer"
    repo.write(repo.review, repo.review_data)
    repo.manifest_data["review"]["sha256"] = hashlib.sha256((repo.root / repo.review).read_bytes()).hexdigest()
    repo.manifest_data["review_commit"] = repo.commit()
    repo.manifest_data["integration_commit"] = repo.manifest_data["review_commit"]
    repo.publish()
    assert repo.graph()["frontier"] == []


def test_delivery_requires_user_accepted_even_if_78_says_resolved(repo):
    repo.tasks.append({"id": 77, "key": "wtaccept", "title": "Terminal", "deps": [], "cases": ["WT-01"]})
    repo.write(".scratch/ruocun/issues/77-wtaccept.md", "Status: resolved\nAssignee: none\n用户体验验收：accepted\n")
    repo.tasks.append({"id": 85, "key": "delivery", "title": "Delivery", "deps": ["wincaps"], "cases": ["PKG-07"]})
    repo.write(".scratch/ruocun/task-graph.json", repo.tasks)
    repo.write(".scratch/ruocun/issues/85-delivery.md", "Status: blocked\nAssignee: none\n")
    repo.write(".scratch/ruocun/issues/78-wincaps.md", "Status: resolved\nAssignee: none\n用户体验验收：pending\n")
    assert 85 not in [item["id"] for item in repo.graph()["frontier"]]


def test_review_commit_must_contain_the_independent_review(repo):
    repo.automatic()
    repo.manifest_data["review_commit"] = repo.product
    repo.publish()
    assert repo.graph()["frontier"] == []


@pytest.mark.parametrize("mode", ["--json", "--mermaid", "text"])
def test_existing_cli_output_modes_support_an_isolated_repository(repo, mode):
    repo.automatic()
    arguments = [sys.executable, "-I", str(SCRIPT), "--root", str(repo.root)]
    if mode != "text":
        arguments.append(mode)
    result = subprocess.run(arguments, capture_output=True, encoding="utf-8", check=True)
    if mode == "--mermaid":
        assert "I78 --> I79" in result.stdout
    else:
        assert [item["id"] for item in json.loads(result.stdout)["frontier"]] == [79]


def test_delivery_cannot_drop_the_explicit_77_78_human_gates(repo):
    repo.tasks.append({"id": 85, "key": "delivery", "title": "Delivery", "deps": [], "cases": ["PKG-07"]})
    repo.write(".scratch/ruocun/task-graph.json", repo.tasks)
    repo.write(".scratch/ruocun/issues/85-delivery.md", "Status: blocked\nAssignee: none\n")
    assert 85 not in [item["id"] for item in repo.graph()["frontier"]]


def test_declared_84_edge_accepts_integrated_reviewed_77_automatic_exit(repo):
    repo.automatic(terminal=True)
    assert [item["id"] for item in repo.graph()["frontier"]] == [84]


@pytest.mark.parametrize("value", ["", "pending", "failed", "unknown"])
def test_automatic_exit_requires_exact_passed_value(repo, value):
    repo.write(".scratch/ruocun/issues/78-wincaps.md", f"Status: resolved\nAutomatic exit: {value}\nAutomatic evidence: none\n")
    assert repo.graph()["frontier"] == []


@pytest.mark.parametrize("mutation", ["missing-schema", "wrong-ticket", "empty-cases", "missing-file", "bad-hash", "traversal", "absolute", "invalid-json", "missing-manifest"])
def test_invalid_or_missing_automatic_evidence_stays_blocked(repo, mutation):
    repo.automatic()
    if mutation == "missing-schema":
        del repo.manifest_data["schema_version"]
    elif mutation == "wrong-ticket":
        repo.manifest_data["ticket"] = ".scratch/ruocun/issues/77-wtaccept.md"
    elif mutation == "empty-cases":
        repo.manifest_data["cases"] = []
    elif mutation == "missing-file":
        repo.manifest_data["cases"][0]["evidence"]["path"] = ".scratch/ruocun/missing.txt"
    elif mutation == "bad-hash":
        repo.manifest_data["cases"][0]["evidence"]["sha256"] = "0" * 64
    elif mutation == "traversal":
        repo.manifest_data["cases"][0]["evidence"]["path"] = ".scratch/ruocun/../../outside.txt"
    elif mutation == "absolute":
        repo.manifest_data["matrix"]["path"] = str(repo.root / repo.matrix)
    repo.publish()
    if mutation == "invalid-json":
        repo.write(repo.manifest, "{invalid}")
        repo.commit()
    if mutation == "missing-manifest":
        (repo.root / repo.manifest).unlink()
        repo.commit()
    graph = repo.graph()
    assert graph["frontier"] == []
    assert graph["tasks"][1]["dependency_blockers"]


@pytest.mark.parametrize("target", ["product_commit", "review_commit", "integration_commit"])
def test_short_or_unavailable_commit_is_not_integrated_proof(repo, target):
    repo.automatic()
    repo.manifest_data[target] = repo.product[:8]
    repo.publish()
    assert repo.graph()["frontier"] == []


def test_product_changes_expire_prior_automatic_exit(repo):
    repo.automatic()
    repo.write("src/product.py", "# changed product\n")
    repo.commit()
    assert repo.graph()["frontier"] == []


def test_an_uncommitted_publication_is_not_an_integrated_exit(repo):
    repo.automatic()
    repo.write(repo.ticket, (repo.root / repo.ticket).read_text(encoding="utf-8") + "\nUncommitted note\n")
    assert repo.graph()["frontier"] == []


@pytest.mark.parametrize("change", ["wrong-product", "wrong-cases", "failed", "missing-reviewer"])
def test_review_must_cover_the_same_product_and_cases(repo, change):
    repo.automatic()
    if change == "wrong-product":
        repo.review_data["product_commit"] = "0" * 40
    elif change == "wrong-cases":
        repo.review_data["cases"] = ["WIN-01.other"]
    elif change == "failed":
        repo.review_data["status"] = "failed"
    else:
        del repo.review_data["reviewer"]
    repo.write(repo.review, repo.review_data)
    repo.manifest_data["review"]["sha256"] = hashlib.sha256((repo.root / repo.review).read_bytes()).hexdigest()
    repo.manifest_data["review_commit"] = repo.commit()
    repo.manifest_data["integration_commit"] = repo.manifest_data["review_commit"]
    repo.publish()
    assert repo.graph()["frontier"] == []


@pytest.mark.parametrize("target", ["other-edge", "unknown-exit", "undeclared", "wrong-parent-id"])
def test_only_the_explicit_approved_edge_can_consume_automatic_exit(repo, target):
    repo.automatic()
    if target == "other-edge":
        repo.tasks[1].update(id=80, key="other")
        repo.write(".scratch/ruocun/issues/80-other.md", "Status: blocked\nAssignee: none\n")
    elif target == "unknown-exit":
        repo.tasks[1]["dependency_exits"]["wincaps"] = "other"
    elif target == "undeclared":
        del repo.tasks[1]["dependency_exits"]
    else:
        repo.tasks[0]["id"] = 76
        repo.write(".scratch/ruocun/issues/76-wincaps.md", (repo.root / repo.ticket).read_text(encoding="utf-8"))
    repo.write(".scratch/ruocun/task-graph.json", repo.tasks)
    repo.commit()
    assert repo.graph()["frontier"] == []


@pytest.mark.parametrize("acceptance_colon", [":", "："])
def test_delivery_accepts_only_complete_77_and_78_with_user_acceptance(repo, acceptance_colon):
    repo.tasks.extend([
        {"id": 77, "key": "wtaccept", "title": "Terminal", "deps": [], "cases": ["WT-01"]},
        {"id": 85, "key": "delivery", "title": "Delivery", "deps": ["wtaccept", "wincaps"],
         "dependency_exits": {"wtaccept": "automatic", "wincaps": "automatic"}, "cases": ["PKG-07"]},
    ])
    repo.write(".scratch/ruocun/task-graph.json", repo.tasks)
    repo.write(".scratch/ruocun/issues/85-delivery.md", "Status: blocked\nAssignee: none\n")
    for ticket in ("77-wtaccept", "78-wincaps"):
        repo.write(f".scratch/ruocun/issues/{ticket}.md", f"Status: resolved\nAssignee: none\n用户体验验收{acceptance_colon}accepted\n")
    assert [item["id"] for item in repo.graph()["frontier"]] == [85]


def test_delivery_automatic_override_cannot_accept_pending_human_exit(repo):
    repo.automatic()
    repo.tasks.extend([
        {"id": 77, "key": "wtaccept", "title": "Terminal", "deps": [], "cases": ["WT-01"]},
        {"id": 85, "key": "delivery", "title": "Delivery", "deps": ["wtaccept", "wincaps"],
         "dependency_exits": {"wincaps": "automatic"}, "cases": ["PKG-07"]},
    ])
    repo.write(".scratch/ruocun/task-graph.json", repo.tasks)
    repo.write(".scratch/ruocun/issues/77-wtaccept.md", "Status: resolved\nAssignee: none\n用户体验验收：accepted\n")
    repo.write(".scratch/ruocun/issues/85-delivery.md", "Status: blocked\nAssignee: none\n")
    repo.commit()
    assert [item["id"] for item in repo.graph()["frontier"]] == [79]


def test_ordinary_and_decision_dependencies_remain_full_ticket_gates(repo):
    repo.tasks[1]["deps"] = ["wincaps", "D22"]
    del repo.tasks[1]["dependency_exits"]
    repo.write(".scratch/ruocun/task-graph.json", repo.tasks)
    repo.write(".scratch/ruocun/issues/78-wincaps.md", "Status: resolved\nAutomatic exit: pending\n")
    decision = ".scratch/ruocun-discovery/issues/22-decision.md"
    repo.write(decision, "Status: claimed\nAutomatic exit: passed\n")
    assert repo.graph()["tasks"][1]["unresolved_dependencies"] == [decision]
    repo.write(decision, "Status: resolved\n")
    assert [item["id"] for item in repo.graph()["frontier"]] == [79]


def test_claimed_ticket_is_reported_but_never_dispatched_again(repo):
    repo.automatic()
    repo.write(".scratch/ruocun/issues/79-wheel.md", "Status: claimed\nAssignee: none\n")
    repo.commit()
    graph = repo.graph()
    assert graph["frontier"] == []
    assert graph["statuses"]["claimed"] == 1
    assert graph["tasks"][1]["status"] == "claimed"


def test_duplicate_acceptance_fields_do_not_fake_user_acceptance(repo):
    repo.tasks.append({"id": 85, "key": "delivery", "title": "Delivery", "deps": ["wincaps"], "cases": ["PKG-07"]})
    repo.write(".scratch/ruocun/task-graph.json", repo.tasks)
    repo.write(".scratch/ruocun/issues/85-delivery.md", "Status: blocked\nAssignee: none\n")
    repo.write(".scratch/ruocun/issues/78-wincaps.md", "Status: resolved\n用户体验验收: accepted\n用户体验验收：pending\n")
    assert repo.graph()["tasks"][-1]["dependency_blockers"][".scratch/ruocun/issues/78-wincaps.md"] == "full-user-acceptance-required"


@pytest.mark.parametrize("mutation", ["extra-case", "missing-mother", "wrong-product", "wrong-evidence", "duplicate-case"])
def test_matrix_case_coverage_and_evidence_must_match_the_manifest(repo, mutation):
    repo.automatic()
    matrix_text = (repo.root / repo.matrix).read_text(encoding="utf-8")
    if mutation == "extra-case":
        matrix_text += matrix_text.splitlines()[-1].replace("WIN-01.process", "WIN-01.cancel") + "\n"
    elif mutation == "missing-mother":
        matrix_text = matrix_text.replace("| WIN-01 | Windows product |\n", "")
    elif mutation == "wrong-product":
        matrix_text = matrix_text.replace(repo.product, "0" * 40)
    elif mutation == "wrong-evidence":
        matrix_text = matrix_text.replace(repo.evidence, ".scratch/ruocun/other.txt")
    else:
        repo.manifest_data["cases"].append(repo.manifest_data["cases"][0])
    repo.write(repo.matrix, matrix_text)
    repo.manifest_data["matrix"]["sha256"] = hashlib.sha256((repo.root / repo.matrix).read_bytes()).hexdigest()
    repo.manifest_data["integration_commit"] = repo.commit()
    repo.publish()
    assert repo.graph()["frontier"] == []


def test_unavailable_git_cannot_unlock_automatic_exit(repo, monkeypatch):
    repo.automatic()
    monkeypatch.setenv("PATH", str(repo.root / "empty-path"))
    assert repo.graph()["frontier"] == []


def test_untracked_product_input_expires_prior_exit(repo):
    repo.automatic()
    repo.write("src/new_input.py", "# unreviewed product input\n")
    assert repo.graph()["frontier"] == []


def test_invalid_case_id_is_blocked_instead_of_crashing_the_graph(repo):
    repo.automatic()
    repo.manifest_data["cases"][0]["id"] = 17
    repo.publish()
    assert repo.graph()["frontier"] == []


def test_duplicate_json_fields_cannot_hide_invalid_evidence_values(repo):
    repo.automatic()
    text = (repo.root / repo.manifest).read_text(encoding="utf-8")
    repo.write(repo.manifest, text.replace('"schema_version": 1', '"schema_version": 99, "schema_version": 1'))
    repo.commit()
    assert repo.graph()["frontier"] == []


def test_available_but_unintegrated_branch_is_not_an_exit(repo):
    repo.automatic()
    original = repo.git("rev-parse", "HEAD")
    repo.git("checkout", "--quiet", "-b", "unintegrated")
    repo.write(".scratch/ruocun/branch-note.txt", "unintegrated synthetic branch\n")
    branch = repo.commit()
    repo.git("checkout", "--quiet", original)
    repo.manifest_data["integration_commit"] = branch
    repo.publish()
    assert repo.graph()["frontier"] == []


def test_ancestor_review_commit_must_actually_contain_the_review_file(repo):
    before_review = repo.commit()
    repo.automatic()
    repo.manifest_data["review_commit"] = before_review
    repo.publish()
    assert repo.graph()["frontier"] == []


def test_deeply_invalid_json_is_fail_closed(repo):
    repo.automatic()
    repo.write(repo.manifest, '{"untrusted":' + '[' * 1100 + '0' + ']' * 1100 + '}')
    repo.commit()
    assert repo.graph()["frontier"] == []
