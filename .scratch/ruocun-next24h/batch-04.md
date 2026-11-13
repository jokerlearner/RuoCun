# 批次04 代理编排与 Hooks

用户确认固定 43、44、48、49，并于 2026-11-11 授权开始实施。主线起点 `5550162`，有效进度 43/79。使用[已批准规格](../ruocun/spec.md)、逐票验收条件及[里程碑规则](../../docs/adr/0015-batch-validation-and-packaging.md)。

| 顺序 | 负责人及工作树 | 所有权与交付 |
| --- | --- | --- |
| 43 → 44 | /root/n24_terminal，`codex/b04-agents` → `codex/b04-goal`，`D:/java supplement/Firstcode/RuoCun/.worktrees/b04-agents` | 43 批量派发、排队取消、父子消息和受确认的继续。44 在 43 独审集成后接长任务目标与内置命令 |
| 48 → 49 | /root/n24_permissions，`codex/b04-hooks` → `codex/b04-lifecycle`，`D:/java supplement/Firstcode/RuoCun/.worktrees/b04-hooks` | 48 工具 Hook 的命令协议、最终参数审批和一次性记录。49 在 48 独审集成、43 代理生命周期接口稳定后接会话和子代理事件 |
| 复核 | /root/n24_review，`codex/b04-review`，`D:/java supplement/Firstcode/RuoCun/.worktrees/b04-review` | 按冻结 DAO 定向复验批量取消、改参后的权限裁决与恢复去重 |
| 集成 | /root，`integration/ruocun-migration`，`D:/java supplement/Firstcode/RuoCun` | 普通运行入口由主协调接线。共享存储与执行契约需要改动时先确定单一写入者 |

43 与 48 先并行。沿用合成配置、回环服务和冻结 DAO 测试，保留逐票证据。结果未确认的写入或执行保留现场并停止受影响操作。批末集中回归、构包与文档汇总。46 留到后续，77/78 整体体验单列。

## 执行记录

43、44、48、49 定向自动测试与独立复核通过，正式进度 47/79。

| 任务 | 实施与证据 |
| --- | --- |
| 43 | 批量按原序收结果、排队取消零派发、活跃代理按顺序接收 TaskSend，已结束代理从确认检查点继续。MessageParent 的普通进展更新摘要，attention 通知父级。真实写入结果未知时，排队项零模型请求。[独立复核](evidence/review/b04-agent-messages-review.md) |
| 44 | 六条内置命令，`/goal`、`/task`、`/coordinator`、`/btw` 及启动别名。普通入口观察到 `/batch` 实际派发两个代理。关闭模式时移除专用指令，保留原目标和备注。[冻结提示对照](evidence/batch-04/n44/README.md) · [独立复核](evidence/review/b04-goal-lifecycle-review.md) |
| 48 | 用户和可信项目命令 Hook，改参后按实际参数裁决，命令超时整树退出。Pre 回执未知后停止原工具，Post 回执未知时仍保留原工具确认结果。[原生进程](evidence/review/b04-native-hook-review.md) · [权限与回执](evidence/review/b04-hook-tool-review.md) |
| 49 | 启动上下文恢复时只保留最新哨兵，提交 Hook 可阻断或注入，正常退出触发 SessionEnd。子代理使用独立的可信定义与作用域，取消时准确判定已停止或结果未知。[子代理生命周期](evidence/n49-agent-lifecycle/README.md) · [独立复核](evidence/review/b04-goal-lifecycle-review.md) |

已记录的对齐差异包括托管子代理主动可见 MessageParent，长任务关闭或无启动开关重开时清除旧专用指令，以及未知 Hook 回执时保留原输入或上下文。Python matcher 完整 JS RegExp 兼容未验证。46 与 77/78 沿原安排。

[固定包 b04-r1](evidence/batch-04/integration/README.md)通过隔离全量回归 1602 项，3 项按默认配置未选。Ruff、Mypy、离线安装、四项冒烟及 253 个产品成员的字节绑定通过。真实模型调用为零。
