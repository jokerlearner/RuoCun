# 02 — 实施核心压缩与完整原文归档（B）

Type: task
Mode: AFK
Status: awaiting-user
Assignee: Codex /root
Parent: [B 方案规格](../spec.md)
Blocked by: none
用户体验验收：pending（仅最终集中验收，当前未执行）

## 目标与来源

用户选择B并调用to-spec制定计划，后续明确指定TDD按spec实施；现实现/自动出口/独审完成，等待最终用户体验验收。
以[规格](../spec.md)为行为权威，[技术计划](../plan.md)为接口基线，[任务依赖](../task.md)为执行顺序，[验收清单](../checklist.md)为结果出口。
固定上游来源与适配边界见[研究](../research.md)，不得把准备文档或旧产品回执计为本功能通过。

## 子任务

- [03 — T01 契约与基线](03-contract-baseline.md)
- [04 — T02 计量与策略](04-pressure-and-selection.md)
- [05 — T03 原文归档与存储](05-transcript-storage.md)
- [06 — T04 主子执行与提交](06-runtime-compaction.md)
- [07 — T05 回查与生命周期](07-archive-access-lifecycle.md)
- [08 — T06 普通入口验收](08-entry-acceptance.md)
- [09 — T07 固定包与交付](09-release-verification.md)

## 验收条件

- [x] AC01–AC16 技术结果有真实回执，依赖与独审门禁满足。
- [x] 原文、引用与新状态同事务；失败保留停止、不自动重放。
- [x] 完整导出和重开回查可用，旧版本已丢内容明确标识。
- [x] 固定包、来源许可、升级说明与用户体验状态分别记录。

## 当前证据

2026-11-13 用户明确指定 TDD 并要求根据 spec 完成计划，已授权实施。测试边界沿规格的既有公开接口，不重新提问。起点 `381f73d7eea7bc25eeba6c08bff7f3aae0564875`；原有相关文件副本及哈希保存在本目录 evidence/baseline（合成开发材料，不含真实会话）。

产品实现、自动出口及独审见[最终交付记录](../delivery.md)，固定B-r3包已发布本地；09的Automatic exit为passed，人工体验保持pending。未创建本轮Git提交、未调用真实模型，原有工作区改动保留。
[文档检查](../evidence/planning-validation.json)核对 40 条用户故事、16 项 AC/清单、7 张实施票、依赖无环和本地链接；[规划复核](../evidence/planning-review.md)记录已处理的一致性问题。文档通过不计作功能通过。
