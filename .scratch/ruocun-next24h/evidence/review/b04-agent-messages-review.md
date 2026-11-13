# 批次 04 第 43 票批量代理和双向消息独立复核

固定候选 `11168d4`，独立树 `src`、`tests` 与主线相同。白名单合成 HOME、会话和本机 HTTP 替身，Windows 真实 SQLite。最终两次退出码均为 0，敏感值扫描无命中。

- 原 `tests/test_b04_agent_messages.py`、`tests/test_b02_agent_background_entry.py` 共 9 项通过。默认十个 scatter worker 占用后排队，父取消后未领取项不派发，汇总保持输入顺序。该上限是同时处理 scatter 调用的 worker 数，后台登记后会归还 worker。真实 SQLite 两个代理的 FIFO 指令各归原 run，写入检查点后才清收件。Progress 更新自己的摘要，attention 才进入父会话事件，原工具对及等待行为保持。[回执](raw/b04-review-agent-messages/command.json)
- 普通 CLI TaskSend 在已结束的普通后台代理上继续，同一 task id 对应新 run；精确历史与追加指令进入新的请求，之后正常投递。校验同一父工具、owner epoch、原终态、工作区与原权限，父 TaskSend 结果确认前新执行器等待；canceling、未知、一次性或缺可信材料拒绝自动续跑。[回执](raw/b04-review-agent-messages/command.json)
- 复用原 38 真实 Write 结果丢失夹具，唯一变化是让两项通过 Agent `tasks[]` 且设一个 worker。实际首个子代理写入一次，第二项未发模型，父无虚构回执，重开父和原子工具仍为 outcome_unknown，只有原子 run，伪造另一作用域被拒。[复现](b04-scatter-unknown.py) · [回执](raw/b04-review-scatter-unknown-final/command.json)

首次探针在 ToolContext 上直接设置并行数，普通运行器初始化按环境恢复默认值，两个任务都领取。改用产品实际读取的合成环境配置后明确验证排队路径。首轮属于夹具设置问题。独审只新增证据，未修改产品。43 接缝在已审范围无阻断。
