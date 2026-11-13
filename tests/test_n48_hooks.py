"""Frozen Hook command protocol and tool-call durability."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import threading

from ruocun.hooks.hooks import (
    HookFileRef,
    HookRuntime,
    HookSpec,
    RunCtx,
    loadHooks,
    parseHookOutput,
    selectHooks,
)


def test_source_hook_parse_match_and_configuration_order(tmp_path):
    first = tmp_path / "user.json"
    second = tmp_path / "project.json"
    first.write_text(json.dumps({"hooks": {"PreToolUse": [{"matcher": "^Write$", "if": "Write(src/**)", "hooks": [
        {"command": "first", "async": True}, {"type": "prompt", "prompt": "declared"}]}]}}), encoding="utf-8")
    second.write_text(json.dumps({"PreToolUse": [{"command": "second"},
                                                   {"type": "", "command": "must not execute"}]}), encoding="utf-8")
    specs = loadHooks([HookFileRef(first), HookFileRef(tmp_path / "missing.json"), HookFileRef(second)])
    assert [s.type for s in specs] == ["command", "prompt", "command", ""] and specs[0].async_
    assert [s.command for s in selectHooks(specs, "PreToolUse", tool_name="Write", args_json='{ "path": "src/a.py" }')] == [
        "first", None, "second", "must not execute",
    ]
    assert selectHooks(specs, "PreToolUse", tool_name="Read") == specs[-2:]
    assert HookRuntime(specs, {}).matching("PreToolUse", RunCtx(str(tmp_path), tool_name="Read")) == (specs[-2],)
    assert selectHooks([HookSpec("SessionStart", matcher="^(startup|resume)$")], "SessionStart", source="resume")
    parsed = parseHookOutput('{"hookSpecificOutput":{"additionalContext":"inside","permissionDecision":"deny", "updatedInput":{}},"additionalContext":"outside"}', "", 0)
    assert parsed.additional_context == "inside" and parsed.permission_decision == "deny" and parsed.updated_input == {}
    assert parseHookOutput("old stdout", "actual reason", 2).reason == "actual reason"
    assert parseHookOutput("plain text", "", 0).additional_context == "plain text"
    assert parseHookOutput("ignored", "", 1).additional_context == ""


def test_source_actual_hook_commands_receive_utf8_stdin_and_merge_in_order(tmp_path):
    script = tmp_path / "hook.py"
    script.write_text(
        "import json, os, sys\n"
        "raw = sys.stdin.buffer.read()\n"
        "assert not raw.endswith(b'\\n')\n"
        "data = json.loads(raw)\n"
        "assert data == {'tool': 'Write', 'args': '{\"path\":\"原文.py\"}'}\n"
        "assert os.environ['RUOCUN_HOOK_EVENT'] == 'PreToolUse'\n"
        "assert os.environ['RUOCUN_TOOL_NAME'] == 'Write'\n"
        "assert os.path.samefile(os.environ['CLAUDE_PROJECT_DIR'], os.getcwd())\n"
        "assert 'SYNTHETIC_API_KEY' not in os.environ\n"
        "tag = sys.argv[1]\n"
        "if tag == 'block':\n sys.stderr.write('synthetic block'); sys.exit(2)\n"
        "print(json.dumps({'hookSpecificOutput': {'permissionDecision': tag, 'additionalContext': tag,\n"
        "      'updatedInput': {'path': tag + '.py'}}}))\n", encoding="utf-8",
    )
    argv = f'"{sys.executable}" -I -X utf8 "{script}"'
    specs = [HookSpec("PreToolUse", command=argv + " " + tag, async_=True) for tag in ("deny", "allow", "block")]
    env = {**os.environ, "SYNTHETIC_API_KEY": "synthetic-environment-key"}
    args = '{"path":"原文.py"}'
    hook = HookRuntime(specs, env)
    result = asyncio.run(hook.run("PreToolUse", RunCtx(str(tmp_path), tool_name="Write", args_json=args,
                             payload={"tool": "Write", "args": args}), threading.Event()))
    assert result.block and result.reason == "synthetic block"
    assert result.permission_decision == "deny" and result.additional_context == "deny\nallow"
    assert result.updated_input == {"path": "allow.py"}



def test_source_hook_rewrite_is_single_and_applies_to_gate_receipt_handler_and_post(tmp_path):
    from ruocun.config.compat import Compatibility
    from ruocun.permissions.runtime import createPermissionRuntime
    from ruocun.permissions.settings import emptyPermissions
    from ruocun.session.session import Session
    from ruocun.tools.registry import ToolRegistry
    from ruocun.tools.tool_batch import executeToolBatch
    from ruocun.tools.types import ToolContext
    from ruocun.tools.write_file import writeFileTool

    script = tmp_path / "toolhook.py"
    script.write_text(
        "import json, os, pathlib, sys\n"
        "data = json.load(sys.stdin)\n"
        "params = json.loads(data['args'])\n"
        "event = os.environ['RUOCUN_HOOK_EVENT']\n"
        "with pathlib.Path('hook-execution.txt').open('a', encoding='utf-8') as out:\n"
        " out.write(event + ':' + params['path'] + '\\n')\n"
        "if event == 'PostToolUse':\n"
        " assert 'result' in data and pathlib.Path(params['path']).read_text() == params['content']\n"
        " sys.exit(2)\n"
        "target = 'blocked.txt' if params['path'] == 'original-denied.txt' else 'confirmed.txt'\n"
        "decision = 'allow' if target == 'blocked.txt' else 'ask'\n"
        "print(json.dumps({'hookSpecificOutput': {'permissionDecision': decision,\n"
        " 'additionalContext': 'synthetic hook context',\n"
        " 'updatedInput': {'path': target, 'content': params['content']}}}))\n",
        encoding="utf-8",
    )
    command = f'"{sys.executable}" -I -X utf8 "{script}"'
    audit_root = tmp_path / "audit"
    if os.name == "nt":
        from ruocun.platform.windows.durable_file import ensure_private_dir

        ensure_private_dir(audit_root)
    else:
        audit_root.mkdir(mode=0o700)
    hook = HookRuntime([HookSpec(event, matcher="^Write$", command=command)
                        for event in ("PreToolUse", "PostToolUse")], {**os.environ, "RUOCUN_AUDIT": "1"},
                       audit_dir=audit_root, redact=lambda text: text.replace("synthetic-secret", "[REDACTED]"))
    ctx = ToolContext(str(tmp_path), toolHooks=hook)
    registry = ToolRegistry()
    registry.register(writeFileTool)
    rules = emptyPermissions()
    rules["allow"] = ["Write"]
    rules["deny"] = ["Write(blocked.txt)"]
    rules["defaultMode"] = "auto"

    class Journal:
        def __init__(self):
            self.started = {}
            self.saved = {}
            self.effects = []

        async def intent(self, call_id, name, args, effect):
            if call_id in self.started:
                assert self.started[call_id] == (name, args, effect)
                return self.saved[call_id]
            self.started[call_id] = (name, args, effect)
            self.effects.append((name, effect))
            return None

        async def result(self, call_id, text, image_data=None):
            self.saved[call_id] = text

    journal = Journal()

    async def scenario():
        asked = []

        async def no_prompt(*_args):
            raise AssertionError("the hook ask must use the structured human approval port")

        async def human(requests):
            asked.extend(requests)
            assert [request["id"] for request in requests] == ["allowed"]
            assert json.loads(requests[0]["argsJson"])["path"] == "confirmed.txt"
            return {"allowed": "once"}

        permissions = await createPermissionRuntime(
            tmp_path, tmp_path / "config", Compatibility(1, ()), Session("SYS", "synthetic", env={}),
            rules, no_prompt, interactive=True, env={"ProgramData": str(tmp_path / "policy")}, approvalPrompt=human,
        )
        permissions.bindClassifier(no_prompt, lambda: [])
        calls = [("denied", "Write", json.dumps({"path": "original-denied.txt", "content": "denied"})),
                 ("allowed", "Write", json.dumps({"path": "original-allowed.txt", "content": "synthetic-secret"}))]
        results = []
        for _ in range(2):
            result = await executeToolBatch(calls, registry, ctx, approve=no_prompt, journal=journal, authorize=None,
                                            authorize_batch=permissions.authorizeBatch, call_scope=permissions.callScope,
                                            permission_mode=permissions.getMode)
            results.append(result.messages)
        assert results[0] == results[1] and len(asked) == 2
        assert "拒绝" in results[0][0]["content"]
        assert "synthetic hook context" in results[0][1]["content"]

    asyncio.run(scenario())
    assert journal.effects == [("PreToolUse:Write", True), ("PreToolUse:Write", True),
                               ("Write", True), ("PostToolUse:Write", True)]
    assert journal.started["allowed"][1] == '{"path":"confirmed.txt","content":"synthetic-secret"}'
    assert (tmp_path / "confirmed.txt").read_text() == "synthetic-secret"
    assert all(not (tmp_path / name).exists() for name in ("original-denied.txt", "original-allowed.txt", "blocked.txt"))
    assert (tmp_path / "hook-execution.txt").read_text().splitlines() == [
        "PreToolUse:original-denied.txt", "PreToolUse:original-allowed.txt", "PostToolUse:confirmed.txt",
    ]

    audit_files = list((audit_root / "hook-audit").glob("*.json"))
    assert audit_files
    if os.name == "nt":
        from ruocun.platform.windows.durable_file import local_path, verify_private_file

        audit_files = [local_path(file) for file in audit_files]
        assert all(verify_private_file(file) for file in audit_files)
    raw_audit = "\n".join(file.read_text("utf-8") for file in audit_files)
    assert "synthetic-secret" not in raw_audit and "[REDACTED]" in raw_audit
    audit = [json.loads(file.read_text("utf-8")) for file in audit_files]
    assert any(row["event"] == "ToolUse" and row["status"] == "completed"
               and json.loads(row["args"])["path"] == "confirmed.txt" for row in audit)
