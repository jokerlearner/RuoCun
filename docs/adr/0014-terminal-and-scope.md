# ADR-0014：保留完整终端并移出三项扩展能力

Status: Accepted

日期：2026-11-11

用户明确保留完整终端界面，随后决定「20.37.50 这些票不做，其他的票继续做」。本决定在 [ADR-0010](0010-selected-scope-and-lean-workflow.md) 的范围上增加以下三项排除。

| 票 | 移出范围 | 相邻能力 |
| --- | --- | --- |
| [20](../../.scratch/ruocun/issues/20-notebook.md) | `NotebookEdit` 单元格编辑工具及其注册、搜索激活和产品验收 | 通用文件读写编辑、权限、原子保存和恢复继续适用。 |
| [37](../../.scratch/ruocun/issues/37-customcmd.md) | 用户与项目自定义 Markdown 斜杠模板、参数替换及发现路由 | 内置命令、快捷键和已有独立 Skills 的手动与模型调用保留。 |
| [50](../../.scratch/ruocun/issues/50-plugins.md) | 组合插件 manifest 的发现、安装、卸载、列出和跨通道装载 | 独立 Skills、代理定义、Hooks、MCP 和 LSP 保留各自入口与契约。 |

完整终端按 [R-13](../../.scratch/ruocun/spec.md) 和 [WT 验收](../../.scratch/ruocun/acceptance-matrix.md#wt-01) 交付，包含 18、64–69、77。审批、账户选择、终端提示和任务面板使用实际运行能力。Shell 与普通子代理可真实转后台，任务可查看和停止，`/loop` 保留会话内语义。[ADR-0004](0004-final-batch-human-acceptance.md) 的集中人工体验及 [ADR-0006](0006-batched-sprint-workflow.md) 的技术与人工出口继续适用。

保留 02–85 的 84 个历史编号。20、37、50、75、80 标为 `Scope: excluded`，保持原任务状态与来源记录。生效时共 79 张有效票，其中 18 张 resolved、2 张 claimed、59 张 blocked，待完成 61 张。

70 的路由验收覆盖保留命令、别名、CLI 参数及原有未知命令处理规则。70 移除对 50 的硬依赖。79 移除对 20 的硬依赖，继续验证保留资源、SQLite、内部 runner/helper、仓库外安装和实际恢复。37→50 留在两张排除票的历史依赖中。其余活跃边、77/78 自动出口和 85 的人工验收门禁继续按 [依赖图](../../.scratch/ruocun/dependencies.md) 执行。

下一批按 [24 小时计划](../../.scratch/ruocun-next24h/plan.md) 排程。产品实施和验收结果从实际启动后的记录取得。
