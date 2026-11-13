# 43 代理批量派发与双向消息

冻结 `src/tools/agent.test.ts`、`task_send.test.ts`、`message_parent.test.ts`、`src/agent/tasks.ts`、`loop.ts` 和 `resume_agent.ts` 为本票来源。scatter 沿用最多 20 项、默认 10 worker 和环境覆盖。结果按原序汇总，已知单项失败只影响该项，取消后未领用的任务不启动，结果不明的任务停止后续领取。

`TaskSend` 按当前父工具意图和目标 RunRef 持久追加，工具回合已配对后将 FIFO 指令与子代理检查点同事务保存，再清收件。收件保留在旧运行记录，正常继续引用精确历史。`MessageParent` 只绑定当前后台运行，`progress` 更新摘要，`attention` 进入既有父后台事件流，消息事件绑定子工具身份。冻结声明为延迟工具，但普通后台子代理的过滤目录缺 `ToolSearch`，重建目录后没有激活入口。RuoCun 仅在新建、有实际父消息通道且定义已允许的普通后台实例激活此工具，父目录仍延迟，旧恢复目录和 fork 精确快照按原保存目录核验。

已结束的普通代理 TaskSend 以同一 task ID 和新 run 恢复。验证当前 ToolRef、原终态、成对转录、定义、权限、路径与剩余预算；持久登记后等待父 TaskSend 结果提交才发新模型请求。中断代理需要用户 `/recovery continue`；未知、一次性、缺失附件和无法核实的特殊现场均不自动启动。TaskSend 只引用原有工具结果。

`b04-43-tools-red` 保存超额领取和缺失消息工具两个源行为红，`b04-43-tools-green` 两项通过。`b04-43-durable-green` 三项通过，使用受控 Windows SQLite 与白名单合成工作区。两代理同时运行时，父在 A 的 Read 尚待回执时向 A 追加两条、B 追加一条，实际模型请求保持各自顺序；两边实际调用 MessageParent，只有 attention 进入父消息事件。最终定向及 40/67 相关邻接回执另附。无真实模型调用，普通入口和独审由主协调统一登记。
