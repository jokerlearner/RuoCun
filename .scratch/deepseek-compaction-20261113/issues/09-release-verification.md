# 09 — T07 固定包、独立复核与交付

Type: task
Mode: AFK
Status: awaiting-user
Assignee: Codex root + memory_audit + harness_provenance
Parent: [02 — B 方案](02-compaction-and-archive.md)
Blocked by: [08 — T06](08-entry-acceptance.md)
用户体验验收：pending
Automatic exit: passed
Automatic evidence: ../delivery.md、../evidence/t07-r3-delivery.md、../evidence/r3x/command.json

## 实施范围

执行[task.md 的 T07](../task.md#t07--固定候选构包独审与交付)。集中全量/工程入口后构建同一固定包，仓库外纯安装执行压缩、重开与回查，核对来源许可及产物绑定。
新命令的 Windows Terminal 显示、分页和缩放最终集中验证；自动出口与用户体验分别记录。

## 验收条件

- [x] AC15 通过，AC01–AC16 已有回执可完整追踪。
- [x] Ruff/Mypy、所选全量、构包与纯安装结果真实留证，旧失败保留。
- [x] 来源许可、升级/备份与限制说明、模块对应和验收矩阵同步。
- [ ] Windows 技术体验留证；人工未验时保持 pending/awaiting-user。
- [x] 独立复核通过，最终产品与包指纹固定。

## 证据

最终候选B-r3输入指纹`5f530430e385fef8b05837f06165d5c8cdd3c308cc70c87bdd52bfcab0744486`；314成员四路绑定、全仓Ruff/Mypy291源、同包公开CLI三节点通过。完整f2保留实际1734 passed/1旧目录断言failed/4 deselected，原失败及R2/R3改动定向复验和证据复用逐项见[交付记录](../delivery.md)，不改写为最终包重跑全量。

Windows Terminal显示/缩放及用户体验未验，按项目“用户负责体验验收”边界保持awaiting-user；[合成验收脚本](../evidence/manual_terminal.py)已准备、原空项目prepare-only通过，但不能代替视觉/按键验收。真实模型质量未验，不新增费用授权。
