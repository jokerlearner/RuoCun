"""依据一轮中已经观察到的行动判断是否需要进展提醒。每次 runTurn 创建独立状态，调用方保存返回的建议并发布终端提示。

规则判定只用本轮证据，无需额外发起模型请求。
"""

from __future__ import annotations

import math
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ..config.compat import resolve_env

PROGRESS_TOOLS = frozenset(("Write", "Edit", "NotebookEdit", "Bash"))
POLL_TOOLS = frozenset(("BashOutput", "TaskOutput", "TaskGet", "TaskList"))

_TEMPLATES = (
    "[进度提醒] 已连续 ${noProgress} 轮没有执行命令或修改文件。"
    "挑一个尚无证据的假设，用小脚本、命令结果或文档核实；也可以先运行一个最小的实现。"
    "已有证据覆盖必要验收时就答复。有具体证据缺口或高风险时再考虑派 verify。"
    "如果缺必要条件，${stuckFallback}。",
    "[进度提醒·第${stuckAdviceCount}次] ${noProgress} 轮没有执行命令或修改文件，"
    "先前 ${stuckAdviceCount - 1} 次提醒后仍无可核实的进展。"
    "现在选一次能判定问题的检查，取得输出再决定下一步。仍无法推进时，${stuckFallback}。",
    "[进度提醒·本会话第${totalStuckEvents}次卡住] 再次连续 ${noProgress} 轮没有执行命令或修改文件。"
    "核对问题本身有没有解决。用一个小脚本或一条调试输出检验还缺证据的具体值或状态。"
    "仍无法推进时，${stuckFallback}。",
)


def _number(text: str) -> float:
    text = text.strip()
    if not text:
        return 0.
    try:
        if re.fullmatch(r"0[xX][0-9a-fA-F]+|0[bB][01]+|0[oO][0-7]+", text):
            return float(int(text, 0))
        if re.fullmatch(r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|Infinity)", text):
            return float(text)
    except OverflowError:
        return math.inf
    return math.nan


@dataclass
class ProgressAdviceState:
    gaps: tuple[float, ...] = (4., 3., 2.)
    noProgress: int = 0
    nextAdviceAt: float = 4.
    stuckAdviceCount: int = 0
    totalStuckEvents: int = 0
    notice: str | None = None

    def step(self, calls: Sequence[str], *, runningBackground: bool = False,
             interactive: bool = True, enabled: bool = False) -> str | None:
        self.notice = None
        polling = bool(calls) and all(name in POLL_TOOLS for name in calls) and runningBackground
        if any(name in PROGRESS_TOOLS for name in calls) or polling:
            self.noProgress = self.stuckAdviceCount = 0
            self.nextAdviceAt = self.gaps[0]
        else:
            self.noProgress += 1
        if not enabled or not self.noProgress or self.noProgress != self.nextAdviceAt:
            return None
        self.stuckAdviceCount += 1
        self.totalStuckEvents += 1
        self.nextAdviceAt = self.noProgress + self.gaps[min(self.stuckAdviceCount, len(self.gaps) - 1)]
        escalate = self.stuckAdviceCount > 1 or self.totalStuckEvents >= 3
        fallback = ("用 AskUserQuestion 请求必要的信息或决定" if interactive else
                    "选合理的可行路径继续，最终说明阻塞点和取舍")
        template = _TEMPLATES[0 if not escalate else 1 if self.stuckAdviceCount > 1 else 2]
        for name, value in {"noProgress": self.noProgress, "stuckAdviceCount": self.stuckAdviceCount,
                            "stuckAdviceCount - 1": self.stuckAdviceCount - 1,
                            "totalStuckEvents": self.totalStuckEvents, "stuckFallback": fallback}.items():
            template = template.replace("${" + name + "}", str(value))
        label = (f"·第{self.stuckAdviceCount}次" if self.stuckAdviceCount > 1 else
                 f"·本会话第{self.totalStuckEvents}次卡住" if escalate else "")
        self.notice = f"\n[进度提醒{label}:已连续 {self.noProgress} 轮无实质推进]\n"
        return template


def createProgressAdvice(environ: Mapping[str, str] | None = None) -> ProgressAdviceState:
    values = os.environ if environ is None else environ
    raw = resolve_env("ADVISE_GAPS", values)
    parsed = (_number(part) for part in raw.split(",")) if raw else iter(())
    gaps = tuple(number for number in parsed if math.isfinite(number) and number > 0) or (4., 3., 2.)
    return ProgressAdviceState(gaps=gaps, nextAdviceAt=gaps[0])
