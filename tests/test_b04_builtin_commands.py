"""Frozen builtin.test.ts semantics for the six commands retained in scope."""


def test_source_builtins_expand_or_return_usage():
    from ruocun.commands.builtin import BUILTIN_COMMANDS, runBuiltinCommand
    from ruocun.skills.bundled import SIMPLIFY_BODY

    assert runBuiltinCommand("simplify", "ignored") == {"prompt": SIMPLIFY_BODY}
    assert "质量清理" in SIMPLIFY_BODY
    assert runBuiltinCommand("remember", "  ") == {"output": "用法:/remember <要记住的事实>"}
    remember = runBuiltinCommand("remember", " 用户偏好简洁 ")["prompt"]
    assert "MemoryWrite" in remember and remember.endswith("用户偏好简洁")
    assert runBuiltinCommand("batch", "") == {"output": "用法:/batch <大改动指令>"}
    batch = runBuiltinCommand("batch", "把模块拆成微服务")["prompt"]
    assert all(part in batch for part in ("tasks:[...]", "isolate:true", "worktree", "把模块拆成微服务"))
    assert ".ruocun/skills/<kebab-name>/SKILL.md" in runBuiltinCommand("skillify", "")["prompt"]
    assert runBuiltinCommand("skillify", "writing-demo")["prompt"].endswith("建议技能名:writing-demo")
    assert "gh pr diff 42" in runBuiltinCommand("review", " 42 ")["prompt"]
    assert "git status / git diff" in runBuiltinCommand("review", "４２")["prompt"]
    assert "用 Write 写 RUOCUN.md" in runBuiltinCommand("init", "ignored")["prompt"]
    assert set(BUILTIN_COMMANDS) == {"simplify", "remember", "review", "init", "batch", "skillify"}
    assert all(command.description for command in BUILTIN_COMMANDS.values())
    assert runBuiltinCommand("nope", "") is None


def test_english_builtins_keep_the_same_actions_and_argument_requirements():
    from ruocun.commands.builtin import BUILTIN_COMMANDS, runBuiltinCommand

    assert runBuiltinCommand("remember", "", lang="en") == {"output": "Usage: /remember <fact to remember>"}
    assert runBuiltinCommand("batch", " ", lang="en") == {"output": "Usage: /batch <change request>"}
    cases = (
        ("simplify", "", ("quality cleanup", "Edit", "tests or build")),
        ("remember", "a preference", ("MemoryWrite", "procedural", "a preference")),
        ("review", "42", ("gh pr diff 42", "gh pr view 42", "review report")),
        ("review", "", ("git status", "git diff", "review report")),
        ("init", "", ("Write", "RUOCUN.md", "testing conventions")),
        ("batch", "separate modules", ("at most six", "tasks:[...]", "isolate:true", "separate modules")),
        ("skillify", "writing-demo", (".ruocun/skills/<kebab-name>/SKILL.md", "60 characters", "writing-demo")),
    )
    for name, args, expected in cases:
        result = runBuiltinCommand(name, args, lang="en")
        assert result is not None and all(part in result["prompt"] for part in expected)
    assert all(command.descriptionEn for command in BUILTIN_COMMANDS.values())


def test_frozen_long_task_directive_preserves_the_actual_execution_boundaries():
    from ruocun.prompt.system_prompt import LONG_TASK_DIRECTIVE, LONG_TASK_DIRECTIVE_EN

    assert "长任务自主模式" in LONG_TASK_DIRECTIVE
    assert "Long-task autonomous mode" in LONG_TASK_DIRECTIVE_EN
    for directive in (LONG_TASK_DIRECTIVE, LONG_TASK_DIRECTIVE_EN):
        assert all(part in directive for part in ("Agent", "background:true", "TaskWait", "TaskOutput",
                                                  'agent_type:"explore"', "Ctrl+B", "`verify`", "AskUserQuestion"))
    assert "研究(并行)→ 综合 → 实现 → 验证" in LONG_TASK_DIRECTIVE
    assert "research (parallel) → synthesize → implement → verify" in LONG_TASK_DIRECTIVE_EN
