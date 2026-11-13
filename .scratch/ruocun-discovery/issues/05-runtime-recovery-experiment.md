# 用最小 Python 实验验证取消与崩溃恢复契约

Labels: wayfinder:task
Mode: AFK
Status: resolved
Assignee: Codex/runtime-experiment
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [查清完整功能、模块职责与运行时调用链](02-function-runtime-research.md), [查清 SQLite、配置与扩展兼容契约](03-data-extension-research.md)

## Question

在选择运行时路线前，能否用独立 Python 小实验验证流式取消、工具任务的前后台切换、进程身份与 SQLite 崩溃恢复所需的关键保证？

## 依据与边界

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 实验只放 discovery/experiments/runtime/，不进入产品核心。
- 使用可重放的流式 fixture 驱动异步事件；记录取消后仍可能到达的事件及一致性处理。
- Windows 上运行真实子进程、子进程树和后台 runner；覆盖退出、取消、重连及 PID 重用/启动身份校验。
- 对拟支持的 Windows Shell 方言分别验证 argv/引号、环境、管道、中文编码和取消；来源工具名或 Bash 权限规则不自动证明后端 PowerShell/cmd 语义兼容。
- 验证 Windows 本地 IPC、路径/权限和进程树终止语义；文件名或静态 API 用法只作为风险线索，失败需要真实实验或明确平台契约证据。
- 使用真实 SQLite 数据库，覆盖正常退出、提交前/后强制结束、WAL 恢复、工具调用关联和重复恢复。
- 区分 Shell runner、可恢复代理、fork、Monitor/会话内轮询等执行类别；记录它们各自的恢复材料、取消确认和不能自动继续的状态。
- 保留 Python/SQLite/Windows 版本、命令、事件日志和故障注入记录；无真实模型 API 的项目注明范围。
- 产出可供运行时和存储决策使用的事实，不扩展为产品实现。

## Assets

- [Python 取消与崩溃恢复实验、运行记录和结论](../experiments/runtime/README.md)
- [独立只读证据审查](../experiments/runtime/audit.md)
- [末轮入口与计数](../experiments/runtime/latest.json)
- 实验分支：experiment/ruocun-runtime-recovery；首轮代码/失败证据提交：26c528a。

## Comments

- 2026-11-05：建图时建立；前置票闭合后领取，本轮尚未执行。
- 2026-11-05：本轮按 frontier 顺序认领；在独立实验分支验证真实 Python 进程、SQLite、流式取消和恢复边界，证据仅覆盖实际运行场景。
- 2026-11-05：末轮 25/25 符合预设观察，受管清理检查通过；首轮失败与修补过程保留，审查确认三项清理问题已修补。后续前置任务已建立，本票完成实验，不代替运行时路线定案。

## Answer

在 Windows NT 构建 26200、CPython 3.11.9、SQLite 3.45.1 上运行真实子进程、Job、具名管道和数据库故障注入。末轮 25 项覆盖工具意图/结果提交与消息事件原子确认、七场景各三次独立恢复进程、流式已排队回调过滤、线程取消反例、owner/epoch、PID/start 校验、前后台转移、owner 外部终止后的 runner 接管、子孙进程终止及四种命令启动路径。
清理采用同句柄身份核验及实验 supervisor Job，故意迟到 bootstrap 的未登记 runner 也被收口，Job active_processes=0。该监督层不等同产品 TUI。
结论限于最小合成 guard 与所列样本；没有真实 PID 复用/断电/LLM/Windows Terminal 体验或完整 Agent 引擎验收。任务类别的不同恢复材料已单独记录。
新增 [Windows 持久文件与 IPC 权限探针](18-windows-durable-io-experiment.md) 及 [含 WAL 修复的 SQLite 运行环境验证](19-patched-sqlite-runtime-experiment.md)，作为运行时和存储路线的必要前置。当前没有必须改变既定目标的用户取舍；候选建议和影响见实验报告。
