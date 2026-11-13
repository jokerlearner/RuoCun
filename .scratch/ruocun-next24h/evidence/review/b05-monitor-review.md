# 批次 05 第 46 票独立复核

普通入口固定候选 `69bbc6fe`，恢复用例沿 `cbb7e4b7`。后者同时含 26 的在途源码，本报告没有把它纳入验收。白名单启动、合成 HOME/工作区/配置、真实受控 SQLite 和 Windows Job、本地 HTTP 模型，未调用外部模型或访问真实凭据。

[普通 CLI 探针](b05-monitor-cli.py) 从 ToolSearch 激活延迟 Monitor，确认 schema 进入下一请求，再执行真实进程。有限命令场景 8 次模型请求，stdout 的首行、末尾无换行片段和“监控结束”最终结果均进入会话；启动计数为一，返回后心跳稳定。持久监控场景 5 次请求，明确传入的 1000ms 超时被 persistent 忽略，所持真实进程 HANDLE 当时仍运行；TaskStop 后 TaskWait 得到“监控已被取消”，HANDLE 已退出且心跳止写。没有以 TaskStop 的“已请求”作为进程停止证明。[实际绿回执](raw/b05-review-monitor-cli-r2/command.json)

最初探针把第一次 TaskWait 唤醒误认成最终完成，故在输出 attention 到达后提前发最终答复，CLI 正常收口取消了尚在运行的监控。失败回执如实保留；修正的仅是合成模型：每次 attention 唤醒后继续用不同调用 ID 等待同一 task，直到真实终态。没有产品修改。[原夹具失败](raw/b05-review-monitor-cli/command.json)

原来源 Monitor 输出/超时/取消用例已与 51 独审一起通过，沿用其绑定回执，不再重复该组。此次另独立执行 `tests/test_b05_monitor.py::test_monitor_owner_loss_keeps_history_without_restarting_the_command`，实际 **1 passed in 5.48s**。该用例启动真实 persistent 监控，父控制器在消息已持久化后 `os._exit`；重开先确认心跳已经停止，再用真实 SQLite 恢复，保留已有消息、标记 interrupted，等待后心跳仍不增长。它证明旧 owner 丢失后的历史恢复和不重启，不冒充后台进程接管。[恢复回执](raw/b05-review-monitor-owner/command.json)

源码核查：普通运行时注册 Monitor 并复用最终 ShellExecutionPlan；权限保留 Monitor 原工具身份，并叠加同一实际命令计划的 deny、危险与未知解析裁决。启动绑定原父 ToolRef，副作用回执确认后才开始命令；输出事件使用同一 run 身份；取消和会话关闭等待实际执行器收口。沿用 [51 独审](b05-mcp-cli-review.md) 的来源测试和权限差异说明。

本次三个回执均扫描无敏感值命中。46 已审技术范围无阻断，可供后继消费；未构包、未重复全量、未代替终端用户体验。
