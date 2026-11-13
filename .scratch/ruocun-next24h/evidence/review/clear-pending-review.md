# 排队清理接缝独审

`2016257` 与修复 `128af4c`、`0855282` 已独立应用，审查树为 `06cb281`。模块可集成，剩余审查阻断 0。18 的终端接线和实际 Terminal 证据另行验收。

`clear_pending` 在原调度控制锁内处置尚未消费队列，并将当前前台状态交由 Conversation 的原 `discard_queued` 持久提交。成功不改变运行轮次、generation 或取消事件。保存失败时暂停并使当前轮次失效。并发关闭已开始时保留 closed 及其 generation，使等待中的 close 完成其持久处置。

首次复跑既有调度套件 8 passed，Ruff 与定向 mypy 通过。随后对一次实际关切作最小复现，发现 clear_pending 保存失败与 close 并发时会使已关闭状态回退为 paused，持久状态仍 closed。原失败保存在 [回执](raw/n24-review-clear-close-repro/command.json)，仅使用既有 QueueStore 和合成存储错误，未新增故障矩阵。

`128af4c` 修复后同一复现退出 0，内存与持久状态都为 closed。原套件 8 passed in 0.14s，Ruff 通过。该修复首次 mypy 报状态属性窄化产生的 comparison-overlap，原回执保留。`0855282` 改用公开状态快照核对并发关闭，定向 mypy 最终通过。此最后一步仅改变等价状态读取，沿前述功能回执作静态复核。

最终 Git blob 分别为 `session_scheduler.py` 的 `f225394fcc0524c083bbc3389045d138f17132cb` 和测试的 `8895c2bcb7f7d74ddb5a3e9ccd10d4413749e1fe`。所有回执均通过 `tools/run.py` 的明确环境白名单与合成 HOME/config/TEMP 生成，`scan_hit=false`。源码显式加载本独审 worktree，根 venv 仅提供已锁依赖，使用 `-I -B`。没有产品修改、真实模型或 Terminal 体验结果。
