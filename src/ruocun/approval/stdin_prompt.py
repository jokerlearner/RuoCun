"""通过调用方提供的终端输入接口逐项询问审批。

危险操作和禁止持久化的操作只能批准一次。非交互模式下直接拒绝。
"""
from typing import Awaitable, Callable

from .types import ApprovalDecision, ApprovalPrompt, ApprovalRequest


def makeApprovalPrompt(ask: Callable[[str], Awaitable[str]], isInteractive: bool) -> ApprovalPrompt:
    async def prompt(requests: list[ApprovalRequest]) -> dict[str, ApprovalDecision]:
        out: dict[str, ApprovalDecision] = {}
        for request in requests:
            if not isInteractive:
                out[request["id"]] = "deny"
                continue
            once_only = request.get("dangerous") or request.get("noPersist")
            if once_only:
                hint = "[y]是(仅本次) [n]否"
            elif request.get("sensitive"):
                hint = "[y]是(仅本次) [a]始终允许(同类不再问) [n]否"
            else:
                hint = "[y]是(允许一次) [a]始终允许(记住,同类不再问) [n]否"
            answer = (await ask(f"\n需要批准:{request['summary']}\n  {hint} > ")).strip().lower()
            decision: ApprovalDecision = "once" if answer == "y" else "always" if answer == "a" and not once_only else "deny"
            out[request["id"]] = decision
        return out
    return prompt
