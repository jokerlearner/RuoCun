# 01 — 依赖查询识别已审查的自动技术出口

Type: task
Status: resolved
Assignee: /root/workflow_tooling
Branch: codex/sprint-tooling
Worktree: .worktrees/sprint-tooling
Blocked by: none
用户体验验收：not-required

## 已批准规格

来源为[ADR-0006](../../../docs/adr/0006-batched-sprint-workflow.md#自动技术出口与人工出口)及[冲刺适配清单](../../ruocun/sprint-48h.md#依赖查询工具待适配)，本票不计入84张产品实现票，也不改变产品范围。

## 验收条件

- 仅79→78、84→77声明的automatic边可以消费实际已集成、独立复核通过的自动出口；状态pending/failed/缺字段/未知出口/证据缺失或不匹配时保持阻塞。
- 驱动核对出口票、完整commit、证据hash、矩阵case/subcase及独立复核身份，不能只凭Automatic exit: passed放行。证据格式保持简单、可审查并写明字段，实际77/78仍pending，无产品通过结果被新增。
- 其它普通依赖和D节点仍按原门禁；85对77/78完整结题与用户accepted均有检查，不能接受automatic覆盖或单改resolved绕过人工。
- 保留原JSON/文本/Mermaid入口；claimed票继续显示真实占用，不能重新当无人认领的frontier。增加可诊断的阻塞原因，不执行证据文件。
- 使用独立合成Git/矩阵/票据夹具TDD覆盖上述正反例及路径越界、无效/过期证据；所有执行白名单环境/合成HOME，数据不含秘密。
- 只修改.scratch/ruocun/issue_graph.py、相关开发测试与本票/格式说明，产品src和公共状态/矩阵不动。独立审查及真实仓库frontier一致性核验后才结题。

## 验证证据

实现候选e9c7798经未参与实现的主协调在独立worktree复核并提交c366fc7，已快进集成，本票resolved。独立者复用已有8项核心用例+84正例1项及真实图查询，均通过；未新增或重跑无关全量。见[独立复核](../integration-evidence/automatic-exits/README.md)。实际77/78仍pending/none，无产品通过被新增。证据见[实现候选](../evidence/automatic-exits/README.md)，格式见[自动出口格式](../../../docs/agents/automatic-exit-evidence.md)。

375 passed、3 deselected（含56项工具测试），复核身份夹具最终定向1 passed；Ruff默认范围及显式scratch脚本、mypy配置32文件、build wheel/sdist、既有offline 4项均通过。真实图仍84票、5resolved/2claimed/77blocked、frontier空；77/78保持pending/none，用户体验未代填。

## Comments

- 2026-11-10：在`codex/sprint-tooling`领取，起点`f06e866019b35b17fb16af0a7e0826d793945588`；交付前合入`435f71f8f997b54d80b67b050d4bfd6f41281dd6`。实施与证据仅在本票批准范围内。约19:15完成隔离准备、19:16首个正例形成、19:29准备送审；全部自有命令已结束，合成资源保留复验，待协调者派独立审查。最终候选SHA由本提交及交付回执绑定，不自行关闭本票或任何产品票。
- 交付前追加合入`fa9bb86e846af39f8c9dfd0c66c56dae45027e35`的D22环境前提文档记录；无产品代码变化，工具范围与人工门禁保持。
