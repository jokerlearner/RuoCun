# 批次 03 第 29 票模型恢复独立复核

集成候选 `6e48323` 定向 7 项通过。固定修复 `b1b03de`、`f667668` 的两条反例已分别复绿，原等待边界定向回归 2 项通过。白名单合成 HOME/配置/会话，Windows 真实 SQLite 和回环 HTTP，仅使用合成账号。敏感值扫描无命中。未构包或进行终端人工验收。

- 普通入口收到真实 HTTP 429，显式选择第二个账户。再次发出的请求采用其 URL、凭据和模型，调度当前代际无自等待。[回执](raw/b03-review-model-switch/command.json)
- 相邻 6 项覆盖等待中完成事件留在队列直至门闩退出，切账户确认、拒绝、未知三条路径的请求数，非交互 429 上限，同模型瞬态失败额外一次重试，部分输出保留且未完成工具不执行。工具派发结果未知时直接停止，核对了循环不会进入请求重试分支。冻结 `src/agent/loop.ts:342–410` 和 `src/agent/runAgent.ts` 同样区分前台限流、前台同模型重试与子代理直接返回。[回执](raw/b03-review-model-boundaries/command.json)

已确认的 ADR-0012 要求摘要失败时保留原上下文并停止受影响轮。初版手动压缩遇到已等候的后台完成事件时，即使摘要请求失败，门闩仍自动唤醒旧轮。复现复用既有等待和摘要夹具，调用实际 ContextManager 与 SessionScheduler。按普通命令相同方式设置异常捕获范围，修复前为 `calls=2 pending=0 state=idle`，修复后为 `calls=1 pending=1 state=paused`，原上下文和保存点保持。显式成功压缩后，同一等待只恢复一次。[原复现](b03-compact-wait-failure.py) · [红回执](raw/b03-review-compact-wait-red/stdout.bin) · [绿回执](raw/b03-review-compact-wait-green/stdout.bin)

真实 SQLite 重开复验复用原受控库和旧 TaskWait 恢复夹具。仅修门闩时，初始读回 paused，`refresh_recovery` 的隐式保存将它覆盖为 waiting。最终 `f667668` 在恢复刷新及普通启动保存后均维持 paused，零新轮次、同一条未消费事件；显式成功压缩才恢复一次。原未暂停等待恢复和事件唤醒边界保持通过。[SQLite 复现](b03-compact-wait-reopen.py) · [红回执](raw/b03-review-compact-reopen-red-detail/stdout.bin) · [绿回执](raw/b03-review-compact-reopen-green-detail/stdout.bin) · [原用例回归](raw/b03-review-compact-adjacent/command.json)

本票已审范围无剩余阻断。复核仅新增证据。
