# 04 — T02 实现统一预算与压缩候选策略

Type: task
Mode: AFK
Status: resolved
Assignee: Codex /root/compact_audit
Parent: [02 — B 方案](02-compaction-and-archive.md)
Blocked by: [03 — T01](03-contract-baseline.md)
用户体验验收：not-required

## 实施范围

执行[task.md 的 T02](../task.md#t02--统一计量与压缩候选策略)。仅负责计量、裁剪、配对选区、近期保留、摘要重整和候选有效性；不直接持久化。
与 05 的并行基于 03 已固定的唯一契约，不能各自重定义归档类型或事务签名。

## 验收条件

- [x] AC01–AC04/11/12 的定向来源语义及差异确认通过。
- [x] 实际输出预留与请求体一致，显式设置不静默改小。
- [x] 裁剪和摘要在副本生成；控制消息、工具组、系统/Hook/Todo 受保护。
- [x] 截断、空摘要、未缩小和无法选区可明确判定。

## 证据

22项策略定向通过，Ruff/Mypy通过，独立复核亲跑22项通过；实现/差异/红绿回执见[策略交付](../evidence/t02-summary.md)，独审见`evidence/reviewer-t02-policy/`。最终包级验证由09统一绑定，不把纯策略出口冒充整包通过。
