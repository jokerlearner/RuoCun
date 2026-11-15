"""读取随若存发布的内置技能目录和对应正文。"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import TypedDict


class BundledSkill(TypedDict, total=False):
    name: str
    description: str
    body: str
    core: bool
    modelInvokable: bool
    userInvocable: bool


_RESOURCES = files("ruocun.skills").joinpath("resources")


def _body(name: str) -> str:
    return _RESOURCES.joinpath(f"{name}.md").read_bytes().decode("utf-8")


SIMPLIFY_BODY = _body("simplify")
DEBUGGING_BODY = _body("debug")
FEWER_PERMS_BODY = _body("fewer-permission-prompts")
PLANNING_BODY = _body("make-plan")
CODE_REVIEW_BODY = _body("code-review")
DEEP_RESEARCH_BODY = _body("deep-research")
VERIFY_BODY = _body("verify")
RUN_SKILL_GEN_BODY = _body("run-skill-generator")

BUNDLED_SKILLS: list[BundledSkill] = [
    {"name": item["name"], "description": item["description"],
     "body": _body(item["name"]), "core": item["core"]}
    for item in json.loads(_RESOURCES.joinpath("catalog.json").read_text(encoding="utf-8"))
]
