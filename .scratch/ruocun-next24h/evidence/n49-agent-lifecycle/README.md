# 49 子代理 Hook 生命周期

冻结 DAO `dao-f17e189-7ac654a0dc06`。`src/agent/agent_hooks.ts:18–101`、`src/agent/agent_hooks.test.ts:11–91`、`src/agent/runAgent.ts:338–365,501–504`、`src/agent/resume_agent.ts:113–122`。

- 子代理只取已装配且可信定义的 SubagentStart、SubagentStop，不继承父工具 Hook。子启动指令完成并确认后，仅将脱敏 additionalContext 保存进子转录，再派发模型。Stop 在正常完成、已知失败或取消时使用独立信号，忽略命令输出。显式授权的新继续运行可执行本次 Start，前台转后台保留同一逻辑生命周期。
- 子事件共用48的独立持久意图和有摘要的已确认输出，作用域是当前代理 run。取消中的窄许可限定当前 owner、已持久 cancel 请求、SubagentStop 的精确身份及同父 Agent。已确认同目标 TaskStop 的取消允许 Stop 与其文字结果写入相邻。其它在途未知操作仍阻止派发。
- 真实 Windows SQLite 原基线红，固定后同步子首请求前收到一次 Start 上下文，正常 Stop，父工具 Hook 未执行。真实后台取消使用独立信号，Start/Stop 两项 scope 回执均确认。在同一夹具将取消卡在 Start 意图登记前，原候选误报未知，修后模型与 Start 命令均未执行，只运行已批准的 Stop。未知执行结果保留原故障路径。
- 相邻同步代理、定义、后台任务、交接与工具 Hook 20 项通过。取消窄修后同一真实生命周期用例再次通过，Ruff、mypy 通过。所有命令由白名单启动，模型使用合成响应。
- 普通会话的启动、输入提交和退出接线与回执由主协调另行组合。
