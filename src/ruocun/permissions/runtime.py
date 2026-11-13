"""Frozen index.ts permission assembly/commands, adapted to native D09 sources.

The caller owns schema validation, final argument selection and the plan dispatch
hard gate. The caller binds the classifier and session audit. Every settings mutation targets a
native user/project file; explicitly declared compatibility sources stay read-only.
"""
from __future__ import annotations

import copy
import json
import os
import re
import sys
from collections.abc import Awaitable, Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Literal, cast

from ..approval.stdin_prompt import makeApprovalPrompt
from ..approval.store import appendAlwaysApproved, loadAlwaysApproved
from ..approval.types import ApprovalPrompt, ApprovalRequest
from ..config.compat import Compatibility, CompatibilitySource, auto_approve
from ..config.trust import hasProjectConfig, shouldTrustProject
from ..platform.shell_plan import ShellExecutionPlan, prepareShellPlan
from ..session.session import Session
from ..tools.tool_batch import BatchCall
from ..tools.types import Tool, ToolRejected
from .audit import auditDecision
from .engine import isDangerousCall, isSensitiveCall
from .gate import Classifier, MessageSource, PermissionGate
from .identity import rememberRule
from .perm_audit import PermAuditSink, PermDecision, createPermAuditSink
from .rules import CallIdentity, Decision, parseRule, ruleMatches
from .secrets import redactSecrets
from .settings import (
    PermissionMode,
    PermissionsConfig,
    RuleKind,
    _rejectConstant,
    appendRule,
    emptyPermissions,
    enterpriseSettingsPath,
    mergePermissions,
    parseSettings,
    removeRule,
)

_KINDS: tuple[RuleKind, ...] = ("allow", "ask", "deny")


@dataclass
class _Tier:
    kind: str
    path: Path | None
    source: CompatibilitySource | None = None
    active: bool = True
    config: PermissionsConfig = field(default_factory=emptyPermissions)
    state: str = ""


@dataclass
class _CallGrants:
    read: set[str] = field(default_factory=set)
    write: set[str] = field(default_factory=set)


def _canonical(path: str | Path) -> str:
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


def _under(path: str | Path, roots: Sequence[Path], *, includeRoot: bool = True) -> bool:
    absolute = _canonical(path)
    for root in roots:
        canonical = _canonical(root)
        try:
            if os.path.commonpath([absolute, canonical]) == canonical and (includeRoot or absolute != canonical):
                return True
        except ValueError:
            continue
    return False


def isMutatingCommand(text: str) -> bool:
    parts = text.strip().split()
    if not parts:
        return False
    if parts[0] in ("/plan", "/bypass", "/yolo"):
        return True
    if parts[0] == "/mode":
        return len(parts) > 1 and parts[1] in ("auto", "default", "yolo", "bypass", "bypassPermissions", "全权放行")
    return (parts[0] == "/permissions" and len(parts) > 3
            and parts[1] in ("add", "remove") and parts[2] in ("allow", "ask", "deny"))


def _describe(tool: str, raw: str) -> str:
    # Frozen tools/execute.ts describeCall, current ordinary CLI language is zh.
    try:
        args = json.loads(raw, parse_constant=_rejectConstant)
    except ValueError:
        return tool + " " + raw.encode("utf-16-le", errors="surrogatepass")[:400].decode("utf-16-le", errors="surrogatepass")
    args = args if isinstance(args, dict) else {}
    def string(name: str) -> str:
        value = args.get(name)
        return value if isinstance(value, str) else ""
    if tool == "Bash":
        return "$ " + (string("command") or tool)
    if tool == "SkillInstall":
        destination = "当前项目" if args.get("scope") == "project" else "用户技能目录"
        return f"安装技能 {string('source')} → {destination}"
    for name, fieldName, prefix in (("Write", "path", "写入"), ("Edit", "path", "编辑"), ("NotebookEdit", "path", "编辑笔记本"), ("WebFetch", "url", "抓取"), ("WebSearch", "query", "搜索")):
        if tool == name:
            return prefix + " " + string(fieldName)
    value = string("path") or string("command") or string("url") or string("query")
    return tool + " " + value if value else tool


class PermissionRuntime:
    def __init__(
        self, cwd: Path, session: Session, tiers: list[_Tier], prompt: ApprovalPrompt,
        interactive: bool, yolo: bool, readOnlyRoots: Sequence[Path], alwaysApproved: set[str],
        *, executionEnv: Mapping[str, str] | None = None,
    ) -> None:
        self.cwd, self.session, self._tiers = cwd, session, tiers
        self._executionEnv = dict(executionEnv) if executionEnv is not None else None
        self.localSettingsFile = cwd / ".ruocun" / "settings.local.json"
        self.approvalsFile = cwd / ".ruocun" / "approvals.json"
        self.sourceStates: dict[str, str] = {}
        self._rules = emptyPermissions()
        self._sessionAllow: list[str] = []
        self._interactiveRules = emptyPermissions()
        self._ruleOwners: dict[str, _Tier] = {}
        self._override: PermissionMode | None = None
        self._yolo = yolo
        self._prompt, self._interactive = prompt, interactive
        self._readOnlyRoots = tuple(readOnlyRoots)
        self._externalRead = "external-read" in alwaysApproved
        self._externalWrite = "external-write" in alwaysApproved
        self._callGrants: ContextVar[_CallGrants | None] = ContextVar("permission_call_grants", default=None)
        self._audit: PermAuditSink | None = None
        self._auditDirectory: Path | None = None
        self._auditEnv: Mapping[str, str] = {}
        self._redact: Callable[[str], str] = redactSecrets
        self._shellPlans: ContextVar[Mapping[str, ShellExecutionPlan]] = ContextVar("shell_plans", default=MappingProxyType({}))
        self._approvedShellPlans: ContextVar[Mapping[str, ShellExecutionPlan]] = ContextVar("approved_shell_plans", default=MappingProxyType({}))
        self.gate = PermissionGate(self.getMode, self.getRules, prompt, self._remember, self._sessionAllow.append,
                                   canClassify=self._canClassify)

    def _canClassify(self, name: str, raw: str) -> bool:
        if name not in {"Bash", "Monitor"}:
            return True
        try:
            command = json.loads(raw)["command"]
        except (ValueError, KeyError, TypeError):
            return False
        plan = self._shellPlans.get().get(command)
        return plan is not None and plan.analysis.known

    def getShellPlan(self, command: str, cwd: str) -> ShellExecutionPlan:
        plan = self._approvedShellPlans.get().get(command)
        if plan is None or _canonical(plan.cwd) != _canonical(cwd):
            raise ToolRejected("Shell执行计划未获批准或工作目录已改变，命令未执行。")
        return plan

    @staticmethod
    def _dangerousShell(plan: ShellExecutionPlan) -> bool:
        for command in plan.analysis.commands:
            if isDangerousCall("Bash", json.dumps({"command": command})):
                return True
            words = command.strip().split(maxsplit=1)
            name = Path(words[0]).stem.casefold() if words else ""
            if plan.dialect == "cmd" and name in {"format", "diskpart", "clear-disk", "initialize-disk"}:
                return True
            if name in {"remove-item", "del", "rd", "rmdir"} and re.search(r"[a-zA-Z]:[\\/](?:\*|\*\.\*)?(?:['\"]?\s|['\"]?$)", command):
                return True
        return False

    def _shellDecision(self, plan: ShellExecutionPlan) -> Decision:
        rules, mode = self.getRules(), self.getMode()
        identities: list[CallIdentity] = [{"ccTool": "Bash", "value": command} for command in plan.analysis.commands]
        identities.append({"ccTool": "Bash", "value": plan.command})
        denyIdentities = identities
        denyRules = rules["deny"]
        if plan.dialect == "cmd":
            # Windows command/cmdlet names are case-insensitive. Folding deny targets is conservative.
            denyIdentities = [{"ccTool": "Bash", "value": identity["value"].casefold()} for identity in identities]
            folded: list[str] = []
            for rule in denyRules:
                parsed = parseRule(rule)
                if parsed.get("tool") == "Bash" and "specifier" in parsed:
                    folded.append("Bash(" + parsed["specifier"].casefold() + ")")
                else:
                    folded.append(rule)
            denyRules = folded
        if any(ruleMatches(parseRule(rule), identity) for rule in denyRules for identity in denyIdentities):
            return "deny"
        if mode == "plan":
            return "deny"
        if not plan.analysis.known:
            return "ask"
        if self._dangerousShell(plan):
            return "ask"
        if mode == "bypassPermissions":
            return "allow"
        if any(ruleMatches(parseRule(rule), identity) for rule in rules["ask"] for identity in identities):
            return "ask"
        # A full-command allow applies only after actual syntax was understood.
        if any(ruleMatches(parseRule(rule), {"ccTool": "Bash", "value": plan.command}) for rule in rules["allow"]):
            return "allow"
        if mode == "auto":
            read_names = {"echo", "dir", "type", "cd", "chdir", "ver", "vol"} if plan.dialect == "cmd" else {"echo", "pwd"}
            if (not plan.analysis.wrappers and all(command.split(maxsplit=1)[0].casefold() in read_names
                    for command in plan.analysis.commands) and not isSensitiveCall("Bash", json.dumps({"command": plan.command}))):
                return "allow"
        return "ask"

    def bindClassifier(self, classify: Classifier, getMessages: MessageSource) -> None:
        self.gate.classify, self.gate.getMessages = classify, getMessages

    def bindAudit(self, sessionDir: str | Path, env: Mapping[str, str], *, redact: Callable[[str], str] = redactSecrets) -> None:
        self._auditEnv, self._redact = env, redact
        self._auditDirectory = Path(sessionDir)
        self._audit = createPermAuditSink(sessionDir, self.getMode, env)


    async def _reload(self) -> None:
        configs: list[PermissionsConfig] = []
        owners: dict[str, _Tier] = {}
        modeOwner: _Tier | None = None
        self.sourceStates.clear()
        for tier in self._tiers:
            if not tier.active:
                tier.state = "项目未信任，未加载"
            elif tier.path is None:
                configs.append(tier.config)
            else:
                try:
                    raw = tier.path.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    tier.state = "缺失或不可读，未加载"
                    tier.config = emptyPermissions()
                else:
                    tier.config = parseSettings(raw)
                    try:
                        json.loads(raw, parse_constant=_rejectConstant)
                    except ValueError:
                        tier.state = "坏 JSON，按来源使用空权限配置"
                    else:
                        tier.state = "已参与合并"
                    configs.append(tier.config)
            if tier.active and tier.state not in ("缺失或不可读，未加载",):
                for kind in _KINDS:
                    for rule in tier.config[kind]:
                        owners[f"{kind}:{rule}"] = tier
                if "defaultMode" in tier.config:
                    modeOwner = tier
        self._rules = mergePermissions(configs + [self._interactiveRules])
        localOwner = _Tier("local", self.localSettingsFile)
        for kind in _KINDS:
            for rule in self._interactiveRules[kind]:
                owners[f"{kind}:{rule}"] = localOwner
        self._ruleOwners = owners
        for tier in self._tiers:
            if tier.source is None:
                continue
            state = tier.state
            if state == "已参与合并":
                total = sum(len(tier.config[kind]) for kind in _KINDS)
                owned = sum(owners.get(f"{kind}:{rule}") is tier for kind in _KINDS for rule in tier.config[kind])
                state += f"：{total} 条规则，{owned} 条保留来源归属"
                if "defaultMode" in tier.config:
                    state += "；默认模式进入合并结果" if modeOwner is tier else "；默认模式被后层覆盖"
                if total != owned:
                    state += "；重复规则来源被后层覆盖"
            self.sourceStates[tier.source.id] = state

    def forAgent(self, cwd: Path, session: Session, mode: PermissionMode) -> PermissionRuntime:
        """Use the parent rules and prompt port with a child-local mode, state and transcript."""
        child = PermissionRuntime(cwd, session, [], self._prompt, self._interactive,
                                  mode == "bypassPermissions", self._readOnlyRoots,
                                  {name for name, enabled in (("external-read", self._externalRead),
                                   ("external-write", self._externalWrite)) if enabled},
                                  executionEnv=self._executionEnv)
        child._rules = copy.deepcopy(self.getRules())
        child._rules["defaultMode"] = mode
        child._override = mode
        if self._auditDirectory is not None:
            child.bindAudit(self._auditDirectory, self._auditEnv, redact=self._redact)
        if self.gate.classify is not None:
            child.bindClassifier(self.gate.classify, lambda: session.messages)
        return child

    def externalAgentPolicy(self) -> dict[str, object]:
        """Capture the persistent parent boundary without any once-only grants."""
        return {
            "yolo": self._yolo, "externalRead": self._externalRead, "externalWrite": self._externalWrite,
            "additionalDirectories": sorted(_canonical(self.cwd / path) for path in self._rules["additionalDirectories"]),
            "readOnlyRoots": sorted(_canonical(path) for path in self._readOnlyRoots),
        }

    def getMode(self) -> PermissionMode:
        if self.session.mode == "plan":
            return "plan"
        if self._yolo:
            return "bypassPermissions"
        return self._override or self._rules.get("defaultMode", "auto")

    def getRules(self) -> PermissionsConfig:
        return {**self._rules, "allow": self._rules["allow"] + self._sessionAllow}

    def setMode(self, mode: Literal["normal", "plan"]) -> None:
        self.session.mode = mode
        if mode == "normal":
            self._override = None

    def setDeckMode(self, mode: PermissionMode) -> None:
        self.session.mode = "plan" if mode == "plan" else "normal"
        self._yolo = mode == "bypassPermissions"
        self._override = mode if mode in {"default", "auto"} else None

    def setGoalMode(self, enabled: bool) -> None:
        if not self._yolo and (not enabled or self.session.mode != "plan"):
            self._override = "auto" if enabled else None

    @staticmethod
    def isMutatingCommand(text: str) -> bool:
        return isMutatingCommand(text)

    async def _remember(self, rule: str) -> None:
        await appendRule(self.localSettingsFile, rule)

    async def authorizeBatch(self, calls: Sequence[BatchCall], *, executionCwd: Path | None = None) -> dict[str, bool]:
        decisions: dict[str, bool] = {}
        requests: list[ApprovalRequest] = []
        force_human: set[str] = set()
        plans: dict[str, ShellExecutionPlan] = {}
        for call in calls:
            if call.tool.name in {"Bash", "Monitor"}:
                args = json.loads(call.raw_args)
                command = args.get("command")
                if not isinstance(command, str):
                    raise ValueError("Shell command must be a string")
                if command not in plans:
                    plans[command] = await prepareShellPlan(command, str(executionCwd or self.cwd), environ=self._executionEnv)
        self._shellPlans.set(MappingProxyType(plans))
        self._approvedShellPlans.set(MappingProxyType({}))
        for call in calls:
            tool, raw = call.tool, call.raw_args
            shell_args = json.loads(raw) if tool.name in {"Bash", "Monitor"} else {}
            command = shell_args.get("command")
            plan = plans.get(command) if isinstance(command, str) else None
            sandbox_bypass = tool.name == "Bash" and shell_args.get("dangerouslyDisableSandbox") is True
            if plan is not None and tool.name == "Bash":
                decision = self._shellDecision(plan)
                checked = tool.checkPermissions(raw) if tool.checkPermissions else None
                if checked == "deny" or checked == "ask" and decision == "allow" and self.getMode() != "bypassPermissions":
                    decision = checked
            else:
                decision = await self.gate.decideAsync(tool.name, raw, tool)
                if plan is not None and decision != "deny":
                    shell_decision = self._shellDecision(plan)
                    if shell_decision == "deny":
                        decision = "deny"
                    elif self._dangerousShell(plan) or not plan.analysis.known:
                        decision = "ask"
                        force_human.add(call.call_id)
            hook = call.hook_decision
            if hook == "deny":
                decision = "deny"
            elif (hook == "ask" or sandbox_bypass) and decision != "deny":
                decision = "ask"
                force_human.add(call.call_id)
            if decision != "ask":
                decisions[call.call_id] = decision == "allow"
                continue
            dangerous = isDangerousCall(tool.name, raw)
            if plan is not None:
                dangerous = dangerous or self._dangerousShell(plan)
            sensitive = isSensitiveCall(tool.name, raw) or dangerous or sandbox_bypass
            if hook == "allow" and not sensitive and (plan is None or plan.analysis.known):
                decisions[call.call_id] = True
                continue
            summary = plan.summary() if plan is not None else _describe(tool.name, raw)
            if sandbox_bypass:
                summary = "请求本次绕过沙箱\n" + summary
            requests.append({
                "id": call.call_id, "toolName": tool.name, "capability": tool.capability,
                "summary": redactSecrets(self._redact(summary)), "argsJson": raw,
                "sensitive": sensitive,
                "dangerous": dangerous, "noPersist": (sandbox_bypass or rememberRule(tool.name, raw) is None
                    or plan is not None and (not plan.analysis.known or bool(plan.analysis.wrappers))),
            })
        asked = {request["id"] for request in requests}
        if requests:
            answers = await self.gate.requestBatch(requests, forceHuman=force_human)
            decisions.update((request["id"], answers.get(request["id"], False)) for request in requests)
        approved = {json.loads(call.raw_args)["command"] for call in calls
                    if call.tool.name in {"Bash", "Monitor"} and decisions.get(call.call_id)}
        self._approvedShellPlans.set(MappingProxyType({command: plan for command, plan in plans.items() if command in approved}))
        if self._audit is not None:
            for call in calls:
                allowed = decisions.get(call.call_id, False)
                wasAsked = call.call_id in asked
                auditDecisionKind: PermDecision = ("ask-approved" if allowed else "ask-denied") if wasAsked else ("allow" if allowed else "deny")
                source = self.gate.lastApprovalSource(call.call_id) if wasAsked else "rule"
                self._audit.decided(call.tool.name, call.tool.capability, auditDecisionKind, source or "human")
                if call.tool.capability in ("write", "exec"):
                    auditDecision(self.cwd, datetime.now(timezone.utc).isoformat(), {
                        "tool": call.tool.name, "capability": call.tool.capability,
                        "decision": "allow" if allowed else "deny", "summary": self._redact(plans[json.loads(call.raw_args)["command"]].summary() if call.tool.name == "Bash" else _describe(call.tool.name, call.raw_args)),
                    }, self._auditEnv)
        return decisions

    @contextmanager
    def callScope(self) -> Iterator[None]:
        """Keep a once-only outside path grant in its actual dispatch task."""
        token = self._callGrants.set(_CallGrants())
        try:
            yield
        finally:
            self._callGrants.reset(token)

    async def authorize(self, tool: Tool, rawArgs: str) -> bool:
        # Compatibility with callers that authorize and dispatch sequentially.
        self._callGrants.set(_CallGrants())
        return (await self.authorizeBatch([BatchCall("tool", tool, rawArgs)]))["tool"]

    async def _approveExternal(self, absolute: str, *, write: bool) -> bool:
        grants = self._callGrants.get()
        once = (grants.write if write else grants.read) if grants is not None else None
        key = _canonical(absolute)
        extra = [Path(os.path.abspath(self.cwd / path)) for path in self._rules["additionalDirectories"]]
        if self._yolo or (self._externalWrite if write else self._externalRead) or (once is not None and key in once) or _under(absolute, extra):
            return True
        if not write and _under(absolute, self._readOnlyRoots, includeRoot=False):
            return True
        if not self._interactive:
            return False
        id = "extw" if write else "ext"
        request: ApprovalRequest = {
            "id": id, "toolName": "写入(工作区外)" if write else "读取(工作区外)",
            "capability": "write" if write else "read",
            "summary": ("写入工作区外路径:" if write else "访问工作区外路径:") + absolute,
        }
        decision = (await self._prompt([request])).get(id, "deny")
        if decision == "deny":
            return False
        if decision == "always":
            await appendAlwaysApproved(self.approvalsFile, "external-write" if write else "external-read")
        if decision in ("always", "session"):
            if write:
                self._externalWrite = True
            else:
                self._externalRead = True
        elif once is not None:
            once.add(key)
        return True

    async def approveExternalRead(self, absolute: str) -> bool:
        return await self._approveExternal(absolute, write=False)

    async def approveExternalWrite(self, absolute: str) -> bool:
        return await self._approveExternal(absolute, write=True)

    async def command(self, text: str) -> str | None:
        parts = text.strip().split()
        if not parts:
            return None
        name = parts[0]
        if name == "/plan":
            self.session.mode = "normal" if self.session.mode == "plan" else "plan"
            return "已进入 plan 模式(只读+提方案)" if self.session.mode == "plan" else "已回到 normal 模式"
        if name in ("/bypass", "/yolo"):
            if self._yolo:
                self._yolo, self._override = False, None
                return "全权放行已关闭:恢复智能判定审批。"
            self.session.mode, self._yolo, self._override = "normal", True, None
            return "⚡ 全权放行:免审批已开启(权限全交出去,deny 规则与危险命令仍拦)。慎用。"
        if name == "/mode":
            arg = parts[1] if len(parts) > 1 else ""
            if not arg:
                mode = "全权放行" if self.getMode() == "bypassPermissions" else "智能判定" if self.getMode() == "auto" else self.getMode()
                return f"当前权限模式:{mode}。可用 /mode <auto|全权放行|default>；plan 只读规划用 /plan 进入。auto 按配置使用分类器，分类失败转人工审批。"
            if arg == "plan":
                return 'plan 是只读规划权限模式,不经 /mode 切换——用 /plan(会话只读)或 settings.defaultMode = "plan"/`--permission-mode plan` 进入。'
            if arg in ("yolo", "bypass", "bypassPermissions", "全权放行"):
                self.session.mode, self._yolo, self._override = "normal", True, None
                return "⚡ 全权放行:免审批已开启(权限全交出去,deny 规则与危险命令仍拦)。慎用。"
            if arg in ("default", "auto"):
                self.session.mode, self._yolo = "normal", False
                self._override = cast(PermissionMode, arg)
                return "⊙ 智能判定:只读命令/工作区内编辑自动放行；其余由分类器判定，失败转人工审批；deny 规则/危险命令仍拦。" if arg == "auto" else "权限模式已设为 default(写/执行前询问)"
            return f"未知模式:{arg}(可选 auto / 全权放行 / default)"
        if name != "/permissions":
            return None
        sub = parts[1] if len(parts) > 1 else "list"
        if sub == "list":
            sections = []
            rules = self.getRules()
            for kind in ("deny", "ask", "allow"):
                rows = []
                for rule in rules[kind]:
                    owner = self._ruleOwners.get(f"{kind}:{rule}")
                    source = str(owner.path) if owner is not None and owner.path is not None else "session/cli"
                    rows.append(f"  {rule}  ({source})")
                sections.append(f"[{kind}]\n" + ("\n".join(rows) or "  (无)"))
            return "权限规则:\n" + "\n".join(sections)
        if sub in ("add", "remove"):
            kindText = parts[2] if len(parts) > 2 else ""
            if kindText not in ("allow", "ask", "deny"):
                return "用法:/permissions add <allow|ask|deny> <规则>  或  /permissions remove <allow|ask|deny> <规则>"
            kind = cast(RuleKind, kindText)
            rule = " ".join(parts[3:])
            if not rule:
                return "缺少规则。用法:/permissions add deny Bash(rm:*)"
            if sub == "add":
                await appendRule(self.localSettingsFile, rule, kind)
                if rule not in self._interactiveRules[kind]:
                    self._interactiveRules[kind].append(rule)
                await self._reload()
                return f"✓ 已添加 {kind} 规则:{rule}(写入 {self.localSettingsFile})"
            owner = self._ruleOwners.get(f"{kind}:{rule}")
            if owner is None or owner.path is None:
                return f"✗ 规则不在任何已加载的 settings 文件中(可能是 session/CLI 规则,无法通过此命令删除):{rule}"
            if owner.source is not None or owner.kind == "managed":
                return f"✗ {owner.path} 为只读兼容/托管来源，未修改；请在原来源管理规则。"
            removed = await removeRule(owner.path, rule, kind)
            if not removed:
                return f"✗ 未在 {owner.path} 中找到规则:{rule}"
            if rule in self._interactiveRules[kind]:
                self._interactiveRules[kind].remove(rule)
            await self._reload()
            return f"✓ 已移除 {kind} 规则:{rule}(从 {owner.path})"
        return "用法:\n  /permissions list\n  /permissions add <allow|ask|deny> <规则>\n  /permissions remove <allow|ask|deny> <规则>"


async def createPermissionRuntime(
    cwd: Path, userRoot: Path, compatibility: Compatibility, session: Session,
    cliConfig: PermissionsConfig, ask: Callable[[str], Awaitable[str]], *,
    interactive: bool, env: Mapping[str, str], yolo: bool = False,
    readOnlyRoots: Sequence[str | Path] = (),
    executionEnv: Mapping[str, str] | None = None,
    approvalPrompt: ApprovalPrompt | None = None,
    projectTrusted: bool | None = None,
) -> PermissionRuntime:
    cwd, userRoot = cwd.resolve(), userRoot.resolve()
    projectSources = [source for source in compatibility.sources if source.scope == "project" and source.resource in ("settings", "settings_local")]
    present = hasProjectConfig(cwd) or any(Path(source.path).exists() for source in projectSources)
    trusted = (projectTrusted if projectTrusted is not None else
               await shouldTrustProject(cwd, userRoot=userRoot, environ=env, projectConfigPresent=present))
    tiers: list[_Tier] = []
    def compatible(scope: str, resource: str, *, active: bool = True) -> None:
        tiers.extend(_Tier("compatible", Path(source.path), source, active) for source in compatibility.sources if source.scope == scope and source.resource == resource)
    compatible("user", "settings")
    tiers.append(_Tier("user", userRoot / "settings.json"))
    compatible("project", "settings", active=trusted)
    tiers.append(_Tier("project", cwd / ".ruocun/settings.json", active=trusted))
    compatible("project", "settings_local", active=trusted)
    tiers.append(_Tier("local", cwd / ".ruocun/settings.local.json", active=trusted))
    tiers.append(_Tier("cli", None, config=cliConfig))
    compatible("managed", "settings")
    managed = Path(enterpriseSettingsPath())
    if sys.platform == "win32" and env.get("ProgramData"):
        managed = Path(env["ProgramData"]) / "RuoCun/managed-settings.json"
    tiers.append(_Tier("managed", managed))
    prompt = approvalPrompt if approvalPrompt is not None and interactive else makeApprovalPrompt(ask, interactive)
    runtime = PermissionRuntime(cwd, session, tiers, prompt, interactive,
                                yolo or auto_approve(env), tuple(Path(root) for root in readOnlyRoots),
                                await loadAlwaysApproved(cwd / ".ruocun/approvals.json"), executionEnv=executionEnv)
    await runtime._reload()
    if runtime._rules.get("defaultMode") == "plan":
        session.mode = "plan"
    elif runtime._rules.get("defaultMode") == "bypassPermissions":
        runtime._yolo = True
    return runtime
