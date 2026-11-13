# 批次 05 第 26 票独立复核

普通候选 `c0f317ff`，后续暂停关闭窄修已同步 `2601a73e`。只提交独审脚本与回执。所有运行由 tools/run.py 白名单启动，合成 HOME、工作区、配置、受控 SQLite 和回环模型，未调用付费模型。四份回执扫描均无敏感值命中。

[普通 pipe 探针](b05-session-cli.py) 逐条等待实际下一输入提示，实际只发 **3 个模型请求**。首轮之后改名、分支，再查询原 ID 证明分支不自动切换；`/resume` 分支后实际请求带原用户/助手历史，再追加分支输入。第一次 Markdown 导出包含原聊天和分支聊天的 UTF-8 中文/emoji；`/clear` 保持分支 ID，下一请求和第二次导出均不再含旧聊天。最终显式重开原 ID，标题保持，导出只有原聊天，没有分支或 clear 后输入，且无额外模型请求。[完整入口回执](raw/b05-review-sessions-cli/command.json)

同一探针配置真实用户 SessionStart/SessionEnd command Hook。切换后在新会话输入前，事件文件恰为 `start,end,start`；全部正常退出后 3 组生命周期各一次。源码外循环完整 await 旧 `_run_session` 的 finally 和 startup 资源，再进入新会话；旧 SessionEnd 后执行 MCP close 和存储 worker close，后者释放实际 owner，随后才启动新会话。没有在原闭包中替换 Conversation 或重复派发旧用户输入。

在 `2601a73e` 上只补独立活动 owner 入口：第一个真实 CLI 持有会话，第二个 CLI `/resume` 该 ID，实际退出 1、明确报告活动所有者，零模型请求；原进程随后正常退出，生命周期恰一对。[活动 owner 回执](raw/b05-review-session-active/command.json)

原来源 `tests/test_b05_sessions.py` 实际 **4 passed in 18.54s**，包括同 cwd 未完成筛选、Unicode 摘录与导出、摘要不覆盖任务标题、clear 重置任务摘要而保留手动标题；分支无 accepted/tool/run/event 账本，显式登记附件引用；真实 SQLite 封存删除 closed 记录而保留未完成记录；真实 Git 保留被留存恢复材料引用的旧干净工作树。[来源回执](raw/b05-review-session-source/command.json)

原 MCP probe 改用首轮 banner 保存的显式 ID 后，在 26 候选上复验：正常 initialize/list/call/result，远端 effect 先写一再断线，未知退出 74；重开同 ID 换新调用 ID 仍退出 74、不发新模型请求、effect 保持一。证明已完成会话重开语义与未知结果保护没有因 latest 的来源筛选变化而被夹具绕开。[明确重开回执](raw/b05-review-mcp-explicit-resume/command.json)

清理源码核查：活 owner、非 closed、queued 输入、未知工具/非终态 run、待投递事件或附件均阻止封存；IMMEDIATE 事务写 tombstone 后新 claim 拒绝，再核文件身份/seal、移入私有 trash 回读后才删除。读不全任一会话时停止 spill/subagent/worktree 回收；留存 run 的精确工作树及附件有保护。封存后物理删除失败会留下现场，不计成成功。未做断电或并发恶意替换等新矩阵。

`2601a73e` 窄修只读确认：真实暂停/未完成结果在关闭 worker 前另存 paused；操作命令内部 pause_settled 保留旧 preserve_pause 值，不把每次 rename/branch 都误标为用户暂停。新增 paused 退出后 latest 继续的实际回执由主协调单独收取，本报告不把源码阅读冒充该场景已运行。

上述已审入口、存储与恢复保护无阻断。未构包或全量，未代填用户体验；最终批次结题仍由主协调结合暂停恢复新回执与里程碑出口决定。
