"""Memory evaluation report keeps offline and live results separate."""

from typing import Any

from .lib.metrics import PR


def _value(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "N/A"


def _pr(values: PR) -> str:
    return f"{values['p']:.2f} / {values['r']:.2f} / {values['f1']:.2f}"


def formatReport(report: dict[str, Any]) -> str:
    lines = ["# 记忆评估", "", f"运行模式 {report['mode']}。", ""]
    for row in report["rows"]:
        lines.extend((f"## {row['case']} · {row['kind']}", f"- 状态 {row['status']}"))
        if row["status"] not in ("scored", "failed"):
            continue
        kind = row["kind"]
        if kind == "extract":
            lines.extend((f"- 事实召回 {_value(row['factRecall'])}", f"- 画像召回 {_value(row['profileRecall'])}",
                          f"- 精确率 {_value(row['precision'])}",
                          f"- 单条质量 {_value(row['quality'])} ± {_value(row['qualityStdev'])}",
                          f"- type/scope {_value(row['typeScopeMatch'])}"))
            lines.extend(f"  - {'覆盖' if item['covered'] else '缺失'} {_value(item['agreement'])} · {item['fact']}"
                         for item in row["perFact"])
        elif kind == "recall":
            lines.extend((f"- 价值 P/R/F1 {_pr(row['valuePR'])}", f"- stale 泄漏 {row['staleLeak']}",
                          f"- 相关性缺口 {_value(row['relevanceGapValue'])}",
                          f"- judge-人工一致度 {_value(row['judgeHumanAgreement'])}"))
        else:
            lines.extend((f"- push P/R/F1 {_pr(row['push'])}", f"- pull P/R/F1 {_pr(row['pull'])}",
                          f"- 召回差值 {_value(row['delta'])}"))
        lines.append("")
    return "\n".join(lines) + "\n"
