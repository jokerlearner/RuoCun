# 批次 03 第 67 票 Agent 交接独立复核

固定候选 `3d1fdcf`、`6d96efe`。白名单执行使用合成 HOME、配置和仓外临时工作区，复用受控 Windows SQLite。测试请求为合成替身，退出码 0，敏感值扫描无命中。未构包或操作 Windows Terminal。

- 独立复跑原 `tests/test_n67_agent_handoff.py`，1 项通过。首个真实 Write 已提交配对后交接，旧父 signal 置位，新后台仍只执行第二次 Write。模型历史中旧结果只有一份，旧新行分别持有双向 run 引用，剩余轮次记录真实。[回执](raw/b03-review-agent-handoff/command.json)
- 复用同一夹具，在实际 SQLite 事务内旧行更新后注入新行写入失败。读取数据库证实只有旧行，仍为 running，无交接指针。未发出新模型请求，无第二次或重复写入，转换计数为零，无成功回执。[复现](b03-agent-handoff-rollback.py) · [回执](raw/b03-review-agent-rollback/command.json)

源码核对确认 SQLite 所有者、父 Agent 意图、原 run、完整消息对、无未决工具与新执行原子关联。后台执行继承原 cwd、工作区、权限运行时及剩余预算，公开工具为原子代理目录与后台白名单的交集。前台父取消先于交接领取时拒绝新执行。普通 Ctrl+B 同时向 Shell 和 Agent owner 发请求，等待两者完成后统计确认的交接。关闭在释放审批后等待已发的交接，随后关闭执行 owner 和数据库。

普通无隔离 Agent 和 Shell 的自动切换接缝无阻断。冻结 `src/tools/agent.ts` 将普通前台调用登记到前台注册表，保留 fork/worktree 参数；当前候选明确仅登记可安全接续的普通无隔离 Agent，fork 和隔离目录保持前台。两者及真实终端体验不计入本次独审通过。Shell 真实 runner 另见[已有独审](b03-shell-handoff-review.md)。
