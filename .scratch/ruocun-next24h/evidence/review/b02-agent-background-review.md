# 40 后台代理独立核验

初始固定候选 `fbbcaca`，修复候选 `797ee0b` 含 `32b5ddf`。两次对齐时独审工作树 `src` 和 `tests` 与相应候选一致。核对 40 的 RUN-09、TaskOutput、TaskStop，冻结 `tasks.ts`、`agent_lifecycle.ts`、`resume_agent.ts` 及两工具定义，沿 ADR-0009/0013/0015。

`b02-review-agent-background` 在初始候选独立定向 2 passed in 5.29s。真实受控 SQLite 确认父 Agent 回执提交后，精确父工具、当前 owner 和后台 run scope 允许实际子 Write。TaskOutput 保存增量游标，TaskWait 收到 attention 及实际终态。TaskStop 提交 canceling 后信号生效，实际停止才结算。并发取消时真实写入回执丢失仍保留 unknown 与未决子意图。显式继续使用不同 run ID、原工具配对和有效剩余轮数。同 ID 命令复用原决定，既有工具不重放。普通入口模型请求、实际崩溃重开与回放幂等沿用 `fb65ef5` 的 6 passed in 22.13s。

普通 CLI 组合的两条合成模型回执发现取消 owner 问题。`b02-review-background-classifier-baseline` 在初始候选收到 TaskStop 回执，后台工具分类请求仍观察到 `classifier_cancel=[False]`，文件未写。`32b5ddf` 改用当前子 owner 后该复现通过。`b02-review-background-handoff-red` 在此中间候选确认交接分类位于子上下文重置之后，同样收到 TaskStop 回执但取消回调为 False。

`797ee0b` 让后台运行和交接分类共享子取消信号。`b02-review-background-classifier-green` 和 `b02-review-background-handoff-green` 均退出 0。父会话收到请求取消回执、后台模型请求实际观察到取消、目标文件未写，关闭前查询 SQLite 的后台 run 状态为 `canceled`。修复在发布前处理已知 completed/failed 与停止竞态，保留 unknown 优先。审批仍由既有单输入 owner 和模态锁串行，取消观察当前子 signal；父会话可以正常结束。

全部核验使用白名单和合成 HOME，敏感扫描无命中。修复后的 40 接缝可供后继任务使用。特殊 fork、TaskSend/MessageParent 及手工任务管理继续由各自票据验证。
