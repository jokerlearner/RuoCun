# N1 前台 SessionScheduler 候选

起点 `de82088217b72d5196d866c8bc81dc0b00471f48`。本切片只新增 `agent/session_scheduler.py`、11 专属来源测试与本证据，不改 Conversation、loop、runtime、CLI 或公共状态。任务11尚待普通入口集成及独审；本候选通过不表示后台15–17已实现。

## 可消费接口

`SessionScheduler` 注入 `queued_inputs()`、async `queue_user(content)`、`consume_user(input_id)`、`discard_queued(state)`、`set_state(state)` 与 `run(Event, boundary, generation)`，可选 `notice(text)`。队列快照为不可变 AcceptedInput tuple，按 seq 消费；内容在排队前 deepcopy。所有持久化、Hook及 blocked 判断由已审 Conversation 端口掌管，不创建另一份会话、DB 或恢复框架。

- `await submit(content)` 返回已确认的 AcceptedInput；closed 返回 None。保存失败原异常抛出、不确认，当前代次失效并暂停。
- `await pause()` 先失效 generation、设置本轮独有 Event，再确认 discarded 队列和 paused。`reset()` 同样丢弃后回 idle；`close()` 进入 closed，确认丢弃并等待活跃 run 自然返回，之后不再 pump。不使用 Task.cancel。
- `await recover(state)` 将旧 foreground-only/idle/closed 映射 idle，running/其他状态映射 paused；恢复 paused 保留已确认 queued，明确新输入才继续。未知工具的恢复阻断仍由 Conversation.blocked 拒绝。
- `status()`、`subscribe()`、`hasQueued(text)`、`is_current(generation)` 同步；`settled()` 等当前泵停止，`finished()` 等无活动且已暂停/关闭或队列清空。无轮询。status.runningTasks 固定0只表示当前没有后台执行后端。
- root 在 run 回调把 boundary 交给 run_turn.on_boundary；业务循环实际执行 delta 时检查 is_current(generation)、requestid 和 Event。可信 usage/完整 tool pair 的保存仍由 run_turn 完成，不受旧 delta 过滤影响。scheduler 不导入 loop，也不自行解析或提交模型输出。

`consume_user(False)` 仅表示 Hook 拒绝或该项此前已消费，端口必须已将其从 queued 移出；不会因此运行模型或重放原输入。持久化异常保留 lastError 并暂停，不把未确认提交视为成功。

## 来源、适配与验证

只读冻结 `dao-f17e189-7ac654a0dc06`（参考提交 f17e189dc68a0a0a0b9937784e1b7ce29aed80eb）中 `src/agent/session_scheduler.ts` 和同名 test.ts。迁移前台 boundary/pump/close/pause/reset/settled/finished 与 interrupted 收口。相对来源的必要适配：内存 inputs 改为 Conversation 已确认账本；AbortController 改每轮 threading.Event；epoch 延伸为可供主循环检查的 generation；close 为 async 等待持久确认和可信回合结束。没有迁移 BackgroundRuntime、等待句柄、事件投递、keepAlive、后台解绑产品。

7 项定向用例通过，Ruff 两文件通过：

1. 来源 late results never start concurrent model turns 的前台子路径：忙时多输入在 boundary 按 seq 合并，模型不并发。
2. 来源 close resolves existing waiters after active run settles。
3. 来源 submit during interrupted run waits then starts one new run；附 D08 的旧 generation 无效、新 Event 不复用。
4. 来源 Hook 拒绝与 reset 的前台分支，明确不声称 earlier background events 分支已过。
5. R2 必要账本适配：恢复 queued 保留、明确 pause 保存 discarded、closed 新进程可回 idle。
6. R2 保存失败无确认、无模型调用；真实 blocked 接缝由 root 的 Conversation 用例验证。
7. 来源 interrupted 终态的 Python Event 适配；捕获直接设置 Event 后遗留空 running 的实际失败，已 red→green 修复。

来源9例中的 implicit wait、progress/foreign success、后台 Esc事件保留、delivery保存重试、headless keepAlive及上述前台用例内的后台部分均未验证，不把7项写成来源9例完整通过。

所有命令由白名单启动器 → tools/run.py，使用本树私有 Python3.11 与合成 HOME/config/temp；开发阶段经显式 src 入口，原字节见 source-pytest.py。最终 wheel/安装与全量由 root 统一构建验证，本切片不重复构建。mypy 沿已记录的本私有环境编译扩展被 Windows 应用控制阻断状态，未重探替代入口/安装/移动 DLL，待 root/独审既有工具链执行，不回填类型通过。

原始 red/green/Ruff、exit 与敏感值扫描见 command-index.json 和 raw/；最终源码及冻结成员 SHA256 见 source-members.json。所有 scan 为 false，只有合成输入，无真实模型/付费API调用，无 Windows Terminal/resize 人工体验结论。

## 独审回修：关闭期间晚到的排队失败

独审捕获 submit 持有控制锁等 queue 时 close 已先失效代次并置 closed，随后 queue 失败把终态改回 paused。复用第6项同一保存失败替身，添加受控 Event 的实际交错，先见 closed/paused 断言失败，再仅限制 submit 异常分支不得覆盖 closed；lastError、原异常与无确认保持。原7项复跑通过、Ruff通过；没有新增独立用例或故障矩阵。首候选95a3042的旧hash及回执保留在该提交，本目录source-members更新为此回修字节。
