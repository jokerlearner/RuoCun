"""Check the bundled skill contracts and packaged resource integrity."""

import hashlib
import json
import re
from importlib.resources import files
from pathlib import Path

from ruocun.skills.bundled import BUNDLED_SKILLS


def test_core_skill_names_are_complete():
    assert sorted(skill["name"] for skill in BUNDLED_SKILLS) == [
        "code-review", "debug", "deep-research", "fewer-permission-prompts", "make-plan",
        "run-skill-generator", "simplify", "verify",
    ]


def test_every_core_skill_has_nonempty_description_and_body():
    for skill in BUNDLED_SKILLS:
        assert len(skill["description"].strip()) > 10
        assert len(skill["body"].strip()) > 20


def test_descriptions_express_triggers_instead_of_workflows():
    for skill in BUNDLED_SKILLS:
        assert re.search(r"→|->|红.*绿|先[^,。]*再[^,。]*(最后|然后)", skill["description"]) is None
        assert re.search(r"仅在|遇到|时(?:使)?用|之前用|前用|时\b|之前", skill["description"]) is not None


def test_each_description_fits_60_characters():
    for skill in BUNDLED_SKILLS:
        assert len(skill["description"]) <= 60


def test_core_skill_names_are_unique():
    names = [skill["name"] for skill in BUNDLED_SKILLS]
    assert len(set(names)) == len(names)


def test_plan_and_verify_refer_to_existing_source_agent_roles():
    plan = next(skill for skill in BUNDLED_SKILLS if skill["name"] == "make-plan")
    verify = next(skill for skill in BUNDLED_SKILLS if skill["name"] == "verify")
    assert "plan" in plan["body"]
    assert "verify 子代理" in verify["body"]


def test_packaged_core_resources_keep_contracts_and_use_new_text():
    golden_file = (Path(__file__).resolve().parents[1]
                   / ".scratch/ruocun-advanced-a/evidence/skills/core-golden.json")
    golden = json.loads(golden_file.read_text(encoding="utf-8"))
    resources = files("ruocun.skills").joinpath("resources")
    catalog = json.loads(resources.joinpath("catalog.json").read_text(encoding="utf-8"))
    for skill, entry, previous in zip(BUNDLED_SKILLS, catalog, golden, strict=True):
        assert skill["name"] == entry["name"] == previous["name"]
        assert skill["core"] is entry["core"] is previous["core"] is True
        assert skill["description"] == entry["description"] != previous["description"]
        body = skill["body"].encode("utf-8")
        assert hashlib.sha256(body).hexdigest() == entry["body_sha256"] != previous["body_sha256"]
