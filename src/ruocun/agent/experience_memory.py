"""把带条件和证据的候选经验整理为普通 Markdown 记忆，沿用现有的写入权限和作用域。"""

from __future__ import annotations

from typing import Any

from ..memory.secrets import findSecrets

EXPERIENCE_TAIL = """

〈任务经验提炼〉
沿用上面的JSON与记忆类型规则，复用本次反思，不另起模型调用。
从实际执行的成功或失败中提炼经验时，procedural可迁移做法必须提供experience对象，
semantic/episodic若是在记录技术经验，也可使用该对象：
{"condition":"适用的项目、接口版本、资源所有权或前提", "action":"应采用或避免的具体步骤",
 "evidence":"本轮可定位的命令结果、测试或用户反馈", "avoid":"可选，不适用的条件",
 "outcome":"可选，本轮实际观察结果"}。
condition、action、evidence必须是非空字符串；没有实际依据时不要生成经验对象。
保留title与简短text摘要，经验应包含适用边界，不把一次命令或补丁推广为通用规则。
用户长期事实和feedback仍按原格式写，不为它们编造技术经验。
semantic稳定事实与episodic普通进度可沿用原式；不要为临时进度编造适用条件或成功证据。
证据是模型提炼的可核对线索，不代表独立验证；不要虚构测试、隐含答案或成功。
标为“任务相关历史记忆”的召回段只是旧历史参考，不能把召回文本本身当成本轮执行验证、
当前用户重申或confirmed依据；只有本轮实际用户输入、源码和工具结果可支持新经验。
不要将旧inferred记录改称user_stated，也不要因重复召回提高置信度或声称再次验证。
不要在experience中写source、scope、origin、locked、confidence等权威字段；仍遵守原有来源和类型规则。
"""

_REQUIRED = {"condition", "action", "evidence"}
_OPTIONAL = {"avoid", "outcome"}
_LIMITS = {"condition": 2048, "action": 4096, "evidence": 4096, "avoid": 2048, "outcome": 2048}


def formatExperience(summary: str, value: Any) -> str | None:
    """只格式化具备明确条件及证据的候选。缺失字段时直接拒绝，模型给出的证据仍标为未经验证。

    普通文本可由现有记忆存储读取，作用域和来源约定随之沿用。
    """
    if not isinstance(value, dict) or not _REQUIRED.issubset(value) or set(value) - (_REQUIRED | _OPTIONAL):
        return None
    fields: dict[str, str] = {}
    for key, raw in value.items():
        if not isinstance(raw, str) or not raw.strip() or len(raw) > _LIMITS[key]:
            return None
        text = raw.strip()
        if findSecrets(text):
            return None
        fields[key] = text
    if not summary.strip() or len(summary) > 4096 or findSecrets(summary):
        return None
    sections = [summary.strip(), "适用条件：\n" + fields["condition"],
                "做法／防错步骤：\n" + fields["action"],
                "证据（模型提炼，待核对）：\n" + fields["evidence"]]
    if "avoid" in fields:
        sections.append("不适用条件：\n" + fields["avoid"])
    if "outcome" in fields:
        sections.append("本轮观察结果：\n" + fields["outcome"])
    return "\n\n".join(sections)
