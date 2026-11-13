# 38 同步子代理独立核验

固定候选 `b1e6d9b`，核对 38 任务票、TOOL-Agent/RUN-07 子路径、冻结 `src/agent/runAgent.ts` 和 `src/agent/agent_tools.ts`、ADR-0009/0013/0015。使用独立工作树的源码、真实受控 Windows SQLite、合成 HOME 和白名单环境，模型边界由测试注入。

`b02-review-agent-sync` 实际 3 passed in 7.82s，退出码 0，敏感扫描无命中。保留原普通 CLI 父模型 → 子模型 → 父模型通过回执。独立核验范围包括精确父 Agent 意图、同 ID 父子 scope、伪造 scope 拒绝、父规则与子 Session 局部模式、父子转录与模型隔离、取消和单任务失败。真实子 Write 后 handler 抛错时，子 run 标记 unknown，父子意图保留且重开不重放。

存储核对确认仅同当前 owner 的已开始父 Agent、匹配 run 的 tool scope 和明确父引用可以排除该父意图。其它未决工具或 unknown run 仍阻断副作用。子工具批串行持有会话锁，模型请求可以并行。子权限端口复制父有效规则，保留父审批接口和硬拒绝，分类读取子转录。冻结来源的 explore 保留 Bash 但裁剪 Write/Edit，按真实能力裁剪和审批理解只读提示。

补做一条不同的回执故障。复用原真实 Write，移除 handler 故障注入，在 SQLite 子工具结果提交端口注入 `CommitUnconfirmedError`。`b02-review-agent-result-loss-red` 实际观测到文件已写一次、父轮为 `outcome_unknown`、会话 `blocked=False`、子 run 仍 running、父子工具均 started。存储线程封锁后续写入，已提交的原状态留待重开核实。

修复候选 `f305bc9` 的 `src`、`tests` 与集成 `d458dc7` 一致。`b02-review-agent-result-loss-green` 复跑同一现场，退出码 0，实际观察到当前 `blocked=True`，重开同 run 为 unknown，父子工具均未决，文件只写一次。`b02-review-agent-result-loss` 另独立复跑两个提交状态，2 passed in 5.01s，退出码 0。未提交子工具结果时重开归为 unknown。已提交后丢回执则保留真实子工具结果，原执行归为 interrupted，父 Agent 结果仍未决。两条都未重放，敏感扫描无命中。

同步子代理接缝通过独立审查，可供 39/40 使用。两票各自的后台、fork 和继续执行仍按对应验收入口核对。
