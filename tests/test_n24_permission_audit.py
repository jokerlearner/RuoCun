"""Frozen secrets/sanitize/perm_audit.test.ts assertions."""
import json

from ruocun.permissions.perm_audit import (
    createPermAuditSink,
    formatPermReport,
    summarizePermTrace,
)
from ruocun.permissions.sanitize import hasNullByte, hasSuspiciousUnicode, sanitizeText
from ruocun.permissions.secrets import findSecrets, redactSecrets


def test_secrets():
    for text in ["AKIA1234567890ABCDEF", "-----BEGIN OPENSSH PRIVATE KEY-----", 'token = "abcdefgh12345678"', "ghp_"+"a"*36, "sk-"+"a"*30]:
        assert findSecrets(text)
    for text in ["the api returns a json object", "用户偏好 TypeScript,喜欢简洁实现", "const x = 1; // a short token"]:
        assert findSecrets(text) == []
    result = redactSecrets("key AKIA1234567890ABCDEF here")
    assert "AKIA1234567890ABCDEF" not in result and "已隐去" in result


def test_sanitize():
    for text in ["ｒｍ -rf /", "rm\u200b -rf", "a\0b", "ls\u202e"]:
        assert hasSuspiciousUnicode(text)
    for text in ["rm -rf node_modules", "cat 项目/说明.md", "echo hi\n  && ls\t-l", ""]:
        assert not hasSuspiciousUnicode(text)
        assert sanitizeText(text) == {"clean":text,"suspicious":False}
    assert hasNullByte("a\0b") and not hasNullByte("normal/path.ts")
    assert sanitizeText("ｒｍ -rf /") == {"clean":"rm -rf /", "suspicious": True}
    assert sanitizeText("a\0b")["clean"] == "ab"


def test_audit_mode_switch_and_statistics(tmp_path):
    mode = ["default"]
    sink = createPermAuditSink(tmp_path, lambda: mode[0], {})
    mode[0] = "auto"
    sink.decided("Write", "write", "ask-approved", "classifier")
    sink.decided("Write", "write", "ask-denied", "human")
    sink.decided("Read", "read", "allow", "rule")
    events = [json.loads(line) for line in (tmp_path / "perm-trace.jsonl").read_text(encoding="utf-8").splitlines()]
    assert events[0]["mode"] == "auto" and events[0]["source"] == "classifier"
    stats = summarizePermTrace(events)
    assert stats[0]["tool"] == "Write" and stats[0]["askRate"] == 1
    assert "询问率" in formatPermReport(stats)
    disabled = tmp_path / "disabled"
    createPermAuditSink(disabled, lambda: "auto", {"RUOCUN_PERM_AUDIT":"0"}).decided("Write", "write", "allow", "rule")
    assert not (disabled / "perm-trace.jsonl").exists()
