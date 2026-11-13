"""冻结 src/skills/skills.test.ts 的Skill工具断言及调用包装最小确认。"""

import asyncio

from ruocun.tools.skill import skillTool
from ruocun.tools.types import ToolContext


def test_loads_known_skill_body(tmp_path):
    context = ToolContext(str(tmp_path), skills=[{
        "name": "pdf", "description": "处理 PDF", "body": "PDF 步骤详解", "dir": str(tmp_path),
    }])
    output = asyncio.run(skillTool.handler({"name": "pdf"}, context))
    assert "Skill: pdf" in output
    assert "PDF 步骤详解" in output


def test_unknown_skill_lists_available_names(tmp_path):
    context = ToolContext(str(tmp_path), skills=[{
        "name": "pdf", "description": "", "body": "x", "dir": str(tmp_path),
    }])
    output = asyncio.run(skillTool.handler({"name": "nope"}, context))
    assert "未找到 skill" in output
    assert "pdf" in output


def test_matches_slug_and_case_insensitive_name(tmp_path):
    context = ToolContext(str(tmp_path), skills=[{
        "name": "Brainstorming Ideas Into Designs", "slug": "brainstorming", "description": "",
        "body": "头脑风暴正文", "dir": str(tmp_path),
    }])
    by_slug = asyncio.run(skillTool.handler({"name": "brainstorming"}, context))
    by_case = asyncio.run(skillTool.handler({"name": "brainstorming ideas into designs"}, context))
    assert "头脑风暴正文" in by_slug
    assert "头脑风暴正文" in by_case


def test_matches_namespace_slug_and_local_bare_name(tmp_path):
    context = ToolContext(str(tmp_path), skills=[
        {"name": "Test-Driven Development", "slug": "test-driven-development", "namespace": "superpowers",
         "description": "", "body": "TDD 正文", "dir": str(tmp_path)},
        {"name": "tdd", "slug": "tdd", "description": "", "body": "本地 TDD", "dir": str(tmp_path)},
    ])
    by_namespace = asyncio.run(skillTool.handler({"name": "superpowers:test-driven-development"}, context))
    bare = asyncio.run(skillTool.handler({"name": "tdd"}, context))
    assert "TDD 正文" in by_namespace
    assert "本地 TDD" in bare
