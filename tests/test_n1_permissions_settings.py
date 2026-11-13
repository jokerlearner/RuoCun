"""DAO permissions/settings.test.ts assertions; native brand paths follow D09."""
import asyncio
import json

import pytest

from ruocun.permissions.settings import (
    emptyPermissions,
    enterpriseSettingsPath,
    extractCliPermissions,
    loadPermissions,
    mergePermissions,
    parseSettings,
    removeRule,
)


def test_parse_fields():
    permissions = {"allow": ["Bash(npm run test:*)"], "ask": ["Edit(src/**)"], "deny": ["Read(.env)"], "additionalDirectories": ["/tmp/x"], "defaultMode": "auto"}
    assert parseSettings(json.dumps({"permissions": permissions})) == permissions


def test_missing_and_bad():
    assert parseSettings("{}") == emptyPermissions()
    assert parseSettings("{bad") == emptyPermissions()
    assert parseSettings('{"permissions":{"defaultMode":"bypassPermissions"},"bad":NaN}') == emptyPermissions()


@pytest.mark.parametrize("permissions,expected", [
    ({"autoMode": {"allow": ["运行测试和构建命令"], "deny": ["禁止外泄数据到外部端点"], "environment": ["项目使用 pnpm"]}}, {"allow": ["运行测试和构建命令"], "deny": ["禁止外泄数据到外部端点"], "environment": ["项目使用 pnpm"]}),
    ({"bashClassifier": ["禁止 rm -rf"]}, {"deny": ["禁止 rm -rf"]}),
    ({"bashClassifier": ["旧规则"], "autoMode": {"deny": ["新规则"]}}, {"deny": ["新规则", "旧规则"]}),
    ({"autoMode": {"allow": ["只配了 allow"]}}, {"allow": ["只配了 allow"]}),
])
def test_auto_rules(permissions, expected):
    cfg = parseSettings(json.dumps({"permissions": permissions}))
    assert cfg["autoMode"] == expected
    if "bashClassifier" in permissions:
        assert cfg["bashClassifier"] == permissions["bashClassifier"]


def test_merge():
    cfg = mergePermissions([
        {"allow": ["Bash(a)"], "ask": [], "deny": ["Read(x)"], "additionalDirectories": ["/a"]},
        {"allow": ["Bash(a)", "Bash(b)"], "ask": ["Edit(y)"], "deny": [], "additionalDirectories": ["/b"]},
    ])
    assert cfg == {"allow": ["Bash(a)", "Bash(b)"], "ask": ["Edit(y)"], "deny": ["Read(x)"], "additionalDirectories": ["/a", "/b"]}
    assert mergePermissions([{**emptyPermissions(), "defaultMode": "default"}, {**emptyPermissions(), "defaultMode": "plan"}])["defaultMode"] == "plan"
    assert mergePermissions([{**emptyPermissions(), "defaultMode": "auto"}, emptyPermissions()])["defaultMode"] == "auto"


def test_enterprise_native_paths():
    assert "Application Support" in enterpriseSettingsPath("darwin")
    assert enterpriseSettingsPath("linux") == "/etc/ruocun/managed-settings.json"
    assert "ProgramData" in enterpriseSettingsPath("win32")


def test_cli():
    out = extractCliPermissions(["修复bug", "--deny", "Bash(rm:*)", "--allow", "Read", "--add-dir", "/x", "--permission-mode", "plan", "--yolo"])
    assert out["config"] == {**emptyPermissions(), "deny": ["Bash(rm:*)"], "allow": ["Read"], "additionalDirectories": ["/x"], "defaultMode": "plan"}
    assert out["rest"] == ["修复bug", "--yolo"]
    assert extractCliPermissions(["hello", "--yolo"]) == {"config": emptyPermissions(), "rest": ["hello", "--yolo"]}


def test_load_tiers(tmp_path):
    user, local = tmp_path / "user.json", tmp_path / "local.json"
    user.write_text(json.dumps({"permissions": {"deny": ["Bash(rm:*)"], "defaultMode": "default"}}), encoding="utf-8")
    local.write_text(json.dumps({"permissions": {"allow": ["Bash(npm:*)"], "defaultMode": "auto"}}), encoding="utf-8")
    out = asyncio.run(loadPermissions([user, tmp_path / "missing.json", local]))
    assert out["config"]["deny"] == ["Bash(rm:*)"]
    assert out["config"]["allow"] == ["Bash(npm:*)"]
    assert out["config"]["defaultMode"] == "auto"
    assert out["sources"] == {"deny:Bash(rm:*)": str(user), "allow:Bash(npm:*)": str(local)}


def test_remove(tmp_path):
    file = tmp_path / "settings.json"
    file.write_text(json.dumps({"permissions": {"allow": ["Bash(npm:*)", "Read"], "deny": ["Read(.env)"]}, "other": "keep"}), encoding="utf-8")
    assert asyncio.run(removeRule(file, "Bash(npm:*)"))
    assert json.loads(file.read_text(encoding="utf-8")) == {"permissions": {"allow": ["Read"], "deny": ["Read(.env)"]}, "other": "keep"}
    assert not asyncio.run(removeRule(file, "Bash(nonexistent:*)"))
    assert not asyncio.run(removeRule(tmp_path / "missing.json", "Bash(npm:*)"))
