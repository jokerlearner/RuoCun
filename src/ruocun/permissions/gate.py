"""Reference PermissionGate (MIT); classifier callback is optional, never created here."""
from __future__ import annotations

import time
from typing import Awaitable, Callable, Literal

from ..approval.types import ApprovalPrompt, ApprovalRequest, GateDecision, TripNotice
from ..client.types import ChatMessage
from ..tools.types import Tool
from .bash.types import BashParser
from .engine import decide, decideAsync
from .identity import rememberRule
from .settings import PermissionMode, PermissionsConfig

Classifier = Callable[[str, str, list[ChatMessage]], Awaitable[bool]]
MessageSource = Callable[[], list[ChatMessage]]
ApprovalSource = Literal["classifier", "human"]


class PermissionGate:
    def __init__(
        self, getMode: Callable[[], PermissionMode], getRules: Callable[[], PermissionsConfig],
        prompt: ApprovalPrompt, onRemember: Callable[[str], Awaitable[None]],
        addSessionAllow: Callable[[str], None], classify: Classifier | None = None,
        getMessages: MessageSource | None = None, *, parseBash: BashParser | None = None,
        canClassify: Callable[[str, str], bool] | None = None,
    ) -> None:
        self.getMode, self.getRules, self.prompt = getMode, getRules, prompt
        self.onRemember, self.addSessionAllow = onRemember, addSessionAllow
        self.classify = classify
        self.getMessages = getMessages if getMessages is not None else lambda: []
        self.parseBash = parseBash
        self.canClassify = canClassify
        self.lastSources: dict[str, ApprovalSource] = {}
        self.consecutiveDenials = self.totalDenials = 0
        self.lastResetTime = time.time() * 1000
        self.pendingTripNotice: TripNotice | None = None
        self.notifiedThisTrip = False

    def lastApprovalSource(self, id: str) -> ApprovalSource | None:
        return self.lastSources.get(id)

    def recordClassifierAllow(self) -> None:
        self.consecutiveDenials = 0

    def recordClassifierDenial(self) -> None:
        self.consecutiveDenials += 1
        self.totalDenials += 1
        if not self.notifiedThisTrip and (self.consecutiveDenials >= 3 or self.totalDenials >= 20):
            self.notifiedThisTrip = True
            self.pendingTripNotice = {"consecutiveDenials": self.consecutiveDenials, "totalDenials": self.totalDenials}

    def consumeTripNotice(self) -> TripNotice | None:
        notice = self.pendingTripNotice
        self.pendingTripNotice = None
        return notice

    def _isTripped(self) -> bool:
        if time.time() * 1000 - self.lastResetTime > 30 * 60 * 1000:
            self.consecutiveDenials = self.totalDenials = 0
            self.lastResetTime = time.time() * 1000
            self.notifiedThisTrip = False
        return self.consecutiveDenials >= 3 or self.totalDenials >= 20

    def withModeOverride(self, mode: PermissionMode, getMessages: MessageSource | None = None) -> PermissionGate:
        return PermissionGate(
            lambda: mode, self.getRules, self.prompt, self.onRemember, self.addSessionAllow,
            self.classify, self.getMessages if getMessages is None else getMessages, parseBash=self.parseBash,
            canClassify=self.canClassify,
        )

    def _toolCheck(self, decision: GateDecision, argsJson: str, tool: Tool) -> GateDecision:
        if decision == "deny":
            return decision
        checked = tool.checkPermissions(argsJson) if tool.checkPermissions else None
        if checked == "deny":
            return "deny"
        if checked == "ask" and decision == "allow" and self.getMode() != "bypassPermissions":
            return "ask"
        return decision

    def decide(self, toolName: str, argsJson: str, tool: Tool) -> GateDecision:
        decision = decide({"toolName": toolName, "argsJson": argsJson, "capability": tool.capability, "mode": self.getMode(), "rules": self.getRules()})
        return self._toolCheck(decision, argsJson, tool)

    async def decideAsync(self, toolName: str, argsJson: str, tool: Tool) -> GateDecision:
        if toolName != "Bash":
            return self.decide(toolName, argsJson, tool)
        decision = await decideAsync({"toolName": toolName, "argsJson": argsJson, "capability": tool.capability, "mode": self.getMode(), "rules": self.getRules()}, parseBash=self.parseBash)
        return self._toolCheck(decision, argsJson, tool)

    async def requestBatch(self, requests: list[ApprovalRequest], *, forceHuman: set[str] | None = None) -> dict[str, bool]:
        self.lastSources = {}
        out: dict[str, bool] = {}
        toAsk = requests
        if self.getMode() == "auto" and self.classify is not None:
            needHuman: list[ApprovalRequest] = []
            tripped = self._isTripped()
            for request in requests:
                if (request.get("dangerous") or tripped or forceHuman is not None and request["id"] in forceHuman
                        or self.canClassify is not None and not self.canClassify(request["toolName"], request.get("argsJson", ""))):
                    needHuman.append(request)
                    continue
                try:
                    allow = await self.classify(request["toolName"], request.get("argsJson", ""), self.getMessages())
                except Exception:
                    allow = False
                if allow:
                    out[request["id"]] = True
                    self.lastSources[request["id"]] = "classifier"
                    self.recordClassifierAllow()
                else:
                    self.recordClassifierDenial()
                    needHuman.append(request)
            if not needHuman:
                return out
            toAsk = needHuman
        decisions = await self.prompt(toAsk)
        for request in toAsk:
            decision = decisions.get(request["id"], "deny")
            if decision in ("always", "session") and "argsJson" in request and not request.get("noPersist"):
                rule = rememberRule(request["toolName"], request["argsJson"])
                if rule:
                    self.addSessionAllow(rule)
                    if decision == "always":
                        await self.onRemember(rule)
            self.lastSources[request["id"]] = "human"
            out[request["id"]] = decision != "deny"
        return out
