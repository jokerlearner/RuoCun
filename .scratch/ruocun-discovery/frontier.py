"""Query local wayfinder child tickets and validate their dependency graph."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent


def load():
    tickets = {}
    for path in sorted((ROOT / "issues").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = re.search(r"^# (.+)$", text, re.M)
        def field(name):
            match = re.search(r"^" + re.escape(name) + r": (.*)$", text, re.M)
            if not match:
                raise ValueError(f"{path.name}: missing {name}")
            return match.group(1)
        tickets[path.name] = {
            "path": path.name,
            "title": title.group(1),
            "label": field("Labels"),
            "status": field("Status"),
            "assignee": field("Assignee"),
            "mode": field("Mode"),
            "blocked_by": re.findall(r"\]\(([^)]+)\)", field("Blocked by")),
        }
    visiting, visited = set(), set()
    def visit(name):
        if name in visiting:
            raise ValueError(f"Dependency cycle: {name}")
        if name in visited:
            return
        visiting.add(name)
        for parent in tickets[name]["blocked_by"]:
            if parent not in tickets:
                raise ValueError(f"Unknown dependency: {parent}")
            visit(parent)
        visiting.remove(name)
        visited.add(name)
    for name, ticket in tickets.items():
        if ticket["status"] not in {"open", "claimed", "resolved"}:
            raise ValueError(f"Invalid wayfinder status: {name}")
        if ticket["label"] not in {"wayfinder:research", "wayfinder:prototype", "wayfinder:grilling", "wayfinder:task"}:
            raise ValueError(f"Invalid wayfinder label: {name}")
        if ticket["mode"] not in {"AFK", "HITL"}:
            raise ValueError(f"Invalid interaction mode: {name}")
        if ticket["status"] == "claimed" and ticket["assignee"] == "none":
            raise ValueError(f"Claimed ticket has no assignee: {name}")
        if ticket["status"] == "resolved" and "\n## Answer\n" not in (ROOT / "issues" / name).read_text(encoding="utf-8"):
            raise ValueError(f"Resolved ticket has no answer: {name}")
        visit(name)
    return tickets


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--mermaid", action="store_true")
    args = parser.parse_args()
    tickets = load()
    frontier = [
        ticket for ticket in tickets.values()
        if ticket["status"] == "open" and ticket["assignee"] == "none"
        and all(tickets[parent]["status"] == "resolved" for parent in ticket["blocked_by"])
    ]
    if args.mermaid:
        print("flowchart TD")
        identifiers = {name: f"n{i}" for i, name in enumerate(tickets)}
        for name, ticket in tickets.items():
            print(f'  {identifiers[name]}["{ticket["title"]} · {ticket["status"]}"]')
        for name, ticket in tickets.items():
            for parent in ticket["blocked_by"]:
                print(f"  {identifiers[parent]} --> {identifiers[name]}")
    elif args.json:
        pending = [dict(ticket, unresolved_dependencies=[tickets[parent]["title"] for parent in ticket["blocked_by"] if tickets[parent]["status"] != "resolved"]) for ticket in tickets.values() if ticket["status"] != "resolved"]
        print(json.dumps({"tickets": len(tickets), "resolved": sum(t["status"] == "resolved" for t in tickets.values()), "claimed": sum(t["status"] == "claimed" for t in tickets.values()), "frontier": frontier, "pending": pending}, ensure_ascii=False, indent=2))
    else:
        print("当前可领取的决策任务：")
        for ticket in frontier:
            print(f'- {ticket["title"]} [{ticket["label"]}; {ticket["mode"]}]')
        if not frontier:
            print("无；检查正在研究的子票或尚未闭合的依赖。")


if __name__ == "__main__":
    main()
