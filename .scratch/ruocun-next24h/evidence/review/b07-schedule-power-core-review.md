# 59 / 62 核心独审

候选：59 `61a81c16`（作者 `4c0e959a`）；62 `cbc74e1e`（作者 `f6c09487`）。结论：本核心切片无阻断；普通注册、CLI 和每轮异常/取消 finally 释放仍待主协调接线独审，不提前结整票。

核对冻结 `dao-f17e189-7ac654a0dc06/source.zip` 中 `src/schedule.ts:1–53`、`src/tui/wakelock.ts:1–18`，按 ADR-0010 的 W3/W5 保留当前 Windows 缩减。引用候选来源与静态回执 `batch-07/n59/`、`batch-07/n62/`；原 Cron 行与 POSIX 电源 argv/别名/缺后端纯来源断言复用实现者回执，不重复。

独立风险定向复跑实际 `5 passed in 0.41s`，原始回执在 `raw/b07-review-schedule-power-core/`，`sensitive_match=false`。仅合成 HOME、命令和工作区，没有修改系统 crontab 或电源设置、调用模型、全量或构包。

- Schedule/Cron 的 Windows add/list/remove 均返回明确 Error，不伪造创建成功或空表，注入 forbidden runner 未被调用；Wake Windows unsupported、无防休眠保证，释放重复调用也不启动后端。
- 合成 POSIX crontab add/list/remove 保留非本项目任务和 DAO 旧标记；读取失败在写前拒绝、原表不变。源码只将明确无表回执当空表，不沿用来源所有读取错误都当空表的丢信息分支。
- 原 Windows 实物确认用例直接运行独占合成 Python 命令，先写 effect 再取消，结果为 UnknownToolOutcome，effect 保持一次；取消返回时原进程保留的独立 HANDLE 已 signaled。该用例证明当前命令取消收口，不冒称 Windows 系统调度已支持或 POSIX 进程组已实机验证。自动不重放还须普通工具 journal 接线保持现有 exec 副作用契约。
- 原 Wake 实物确认用例使用合成进程替代系统电源 helper，release 返回时已退出/reap，二次 release 幂等；源码支持 TERM/超时 KILL/等待及未确认状态。它不证明 macOS/Linux 真正持锁或整个平台不会休眠。

待普通接线核对：Wake 在实际回合 acquire 后，完成/异常/取消均经同一 finally 释放；Windows 不 spawn；Schedule CLI 的 helper False 返回值与工具 Error 不被转成假成功，未知写不被重试。

42 另记待审风险：共享秘密过滤窄修 `eb349877` 将中文周边秘密的正则词边界对齐冻结 JavaScript；本次未将其当 59/62 功能或重复运行秘密测试，随 42 运行候选独审消费。
