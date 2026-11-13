# D08 · Python 并发、后台执行、取消与恢复路线

日期：2026-11-05。任务：[D08](../issues/08-python-runtime-decision.md)。分支：`research/d08-runtime`，起点 `8d97882`。本文是供完整迁移实施使用的技术路线；没有实现产品或取得产品验收。主会话收录报告与结论，研究分支保留，不 push、PR 或 merge。

## 1. 结论、依据和所有权

**采用一个 asyncio 业务主循环、明确拥有者的阻塞端口、每会话串行 SQLite 工作线程，以及独立 Shell runner。Windows runner 自持命令 Job；原生 overlapped IPC 放在可隔离的受监督 helper 内。取消请求、执行器真实停止、结果持久化和通知确认分别处理。恢复从 SQLite 与可信 runner 收据重建状态，不重新执行结果未知的副作用。**

这保持 [规格 R-01、R-07—R-11](../../ruocun/spec.md) 和模块链 C0—C4/C7，不把 UI、工具执行、持久化和调度合成一个聊天循环。普通代理、fork、Monitor、manual 和 Shell 的执行材料不同，分别按第 8 节恢复。当前无须改变既定目标的新范围取舍。

本文标记：**事实**表示冻结源码或已收录实验；**选择**表示本次工程路线；**待验证**表示后续产品必须补的证据，不能据此填写产品通过。共享物理 schema、StoragePort、配置别名和扩展协议由 D09 单独维护：唯一契约为 [StoragePort v1](09-storage-extension-route.md#storage-port-v1) 与[三类 epoch](09-storage-extension-route.md#epoch-contract)。下文只说明运行时如何使用它们，不维护第二套接口或 schema。

### 1.1 冻结源与已读证据

- 唯一 DAO 来源为 [dao-f17e189-7ac654a0dc06](../reference/README.md)，基准 `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`，源码树 SHA-256 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`。本轮执行 `reference_tool.py verify` 成功，797 tracked + 8 untracked；从 ZIP 直接读取成员，不跟随活动 DAO。下文 `src/...:行号` 均定位这份快照。
- 已读 AGENTS、CONTEXT、domain/issue-tracker、全部 ADR，尤其 [ADR-0003](../../../docs/adr/0003-mcp-unknown-outcome-no-replay.md) 的 MCP 未知不重放与 [ADR-0004](../../../docs/adr/0004-final-batch-human-acceptance.md) 的最终集中人工验收；D02/D03/D05/D18/D19 任务、研究/实验和独立复核；规格 R-01/R-07—11/T-01/T-04、相关 MM/案例，以及正式任务 04—18、26、28、40—49。
- [D02 功能/运行时研究](02-function-runtime.md) 与 [D03 存储/扩展研究](03-data-extension.md) 是事实索引；关键顺序已回到 ZIP 中 `session_scheduler`、`background_types/delivery/runtime`、`tasks`、`execute`、`shell_runner`、`runAgent/resume_agent`、`fork_agent`、`monitor`、`durable_store/recovery`、`client` 核对。

| 已收录事实 | 可用结论 | 不能外推 |
| --- | --- | --- |
| [D05 报告](../experiments/runtime/README.md)及[独立审查](../experiments/runtime/audit.md)末轮 25/25 | 已排队回调可以晚到；`Task.cancel` 后线程仍写文件；owner/epoch、真实 runner/Job/接管、合成事务故障族成立 | 完整 Agent/fork/Monitor 恢复、宿主退出/注销/重启、完整 Shell 权限或最终 WT 通过 |
| [D18 最终独立接收](../../ruocun/integration-evidence/d18-accepted-review/README.md)，候选 `1860c70`、接收 `b858327`，18 passed | 原生提交前必须持有全部 I/O 材料；取消不等于完成；真实 worker 最外入口覆盖诊断异常；当前 SID 可用及匿名 token 拒绝；文件替换/flush/占用有本机事实 | 真实坏驱动超时、精确 Ctrl+C 竞态、独立账户、断电；probe 的整进程 fail-stop 不等于产品 UI/runner 路线 |
| [D19 报告](../experiments/sqlite-runtime/README.md)及[独立复核](../../ruocun/integration-evidence/d19-identity-review/README.md)，候选 `0419c42`、接收 `564f8ca` | 官方固定 SQLite 3.54.1 DLL + stdlib 候选真实 worker；8 次同 retained handle 身份强杀后再恢复，21 次冷恢复、12/12 合同、并发/checkpoint及清理成立 | 最终依赖/产物已定、罕见 WAL-reset 已复现、任意绑定均安全或产品 REC/PKG 已通过 |

## 2. 并发与执行角色

**选择：业务状态只在一个 asyncio loop 改变。** scheduler、Session、TaskManager、ProcessManager 的业务快照、BackgroundRuntime 和输入/审批端口由该 loop 串行调度。工具可以并发等待，但工作线程、helper 和 runner 只通过带身份的消息返回，不从其它线程直接改 Session 或 UI。UI 观察业务事件，不拥有执行真相。[R-01；快照 `src/agent/session_scheduler.ts:19-38,85-90,109-149`；MM-422]

| 角色 | 采用方式与职责 | 不承担的保证/失败处理 |
| --- | --- | --- |
| asyncio 主循环 | 网络流、调度泵、等待、工具批次、审批/问题、生命周期；单入口创建和关闭 | `create_task` 不是持久执行器；任务必须有 owner/登记/收尾，不能 fire-and-forget 后遗忘 |
| 短阻塞工作线程 | 文件读取、哈希、可合作停止的有限同步库；显式限流，保留 Future/停止令牌与完成回执 | 取消 await 不停线程；发生副作用的工作在真实完成前保持未决，不因超时重试 |
| 专属 DB 工作线程 | 每会话连接在该线程创建/使用/关闭；有界请求队列，顺序执行 D09 StoragePort 事务 | 不共享同一 connection 给任意线程，不在 event loop 执行最长 3000ms 锁等待，不通过取消 Future 中断 COMMIT |
| 受管工作进程 | 必须可硬停止的阻塞适配、较重 CPU 工作或不可靠第三方阻塞执行；输入/输出为版本化数据 | 不是默认把每个 Python agent 变成进程；杀死进程不回滚已产生副作用，结果仍可能 unknown |
| Shell runner | 同版本 Python 内部角色，独立于 controller；拥有命令、输出、启动认领/收据与命令 Job | 不执行模型/调度整个会话，不持有 session DB owner，不因 controller 断线重启命令 |
| IPC helper | 仅承载 Win32 管道 I/O、帧、握手与原生材料寿命；由 controller/runner 分别监督 | 不拥有 Shell 业务终态，不写 session DB，不由 IPC 断线推定命令停止 |
| 平台适配 | 进程身份/Job、IPC/ACL、文件发布、控制台与 Shell 方言均留窄端口 | Job 只管生命周期，不冒充文件/网络沙箱；Shell 方言/隔离具体选择仍归平台职责 |

为什么不是纯线程：D05 实际线程取消反例否定了“取消等待就停止副作用”。为什么不是全进程 Agent：冻结普通/fork 代理依赖父工具集、消息边界与权限上下文，进程化会增加另一套 IPC/状态复制，现有目标没有要求这种替换。为什么需要独立 runner：只有独立生命周期、grant/claim 和收据能表达 controller 退出后的接管；只保留 Python Task 无法做到。[快照 `src/agent/runAgent.ts:378-415`、`src/tools/managed_shell.ts:170-240`；D05 audit 第 3 节]

**Windows 主循环选 Proactor 可用路径，不能全局切成 Selector 来迁就终端输入。** Python 3.11 官方文档确认 Windows Proactor 支持 subprocess，Selector 不支持 subprocess/pipe；Windows loop 不支持 POSIX `add_signal_handler`。终端专用输入读取经 D10 的输入 owner 投递业务事件；不在此重选 UI 库。默认 `asyncio.run`/公开 subprocess API 可用，Windows Job 和裸 IPC 则经自有窄 Win32 适配，产品不依赖 D05 的私有 `_winapi`。[Python 平台说明](https://docs.python.org/3.11/library/asyncio-platforms.html)

### 2.1 结构化并发与失败域

- 每轮/代理/工具批次有明确 lifetime owner 和登记任务集合。父 scope 结束必须收齐该 scope 仍在执行的工作；后台转换先完成所有权交接，再从旧取消域摘除。只把可共同失败的短期辅助任务放入同一 TaskGroup。
- **工具批次采用 all-settled 语义**，最多 8 个 read/network/plan worker，write/exec 前 flush 再独占，结果按原调用顺序拼回。一个 worker 持久化失败后停止领取新工作，已发工具收齐再传播失败；不能直接用“首异常取消其它工具”的 TaskGroup 默认行为替换。plan 标签不是无副作用证明。[快照 `src/tools/execute.ts:230-277`；MM-642；RUN-05]
- 20 条 scatter / 默认 10 worker 是另一层额度，不用工具上限 8 替代；主代理 turn、子代理 turn、网络 retry 和费用阈值分别计数。[快照 `src/tools/agent.ts:129-136,399-415`；R-09；正式任务 43]
- 事件与输入队列有界；可合并纯显示 progress，不能丢内容 delta、工具结果、终态、attention 或已确认接受输入。满时背压/显式拒收；不以覆盖最老记录隐藏丢失。队列具体容量属于实现常量及压力验收，不改来源可观察上限。

Python TaskGroup 会在子任务异常时取消其余任务，`gather(return_exceptions=True)` 可用于收集各结果；取消依赖协作，需显式 finally 清理。上述失败域是业务选择，不因使用库自动成立。[Python 任务文档](https://docs.python.org/3.11/library/asyncio-task.html)

## 3. 身份、epoch 与流式事件

采用 D09 的 `DbOwner`（含 session/canonical cwd/instance_id/owner_epoch）、`RunRef(task_id, run_id)`、`ToolRef(scope, tool_call_id)`。session/canonical cwd 与进程 `{host, boot, pid, start}` 共同校验 owner；查身份失败保持未知，不当死亡，不跨 host 自动接管。终止/清理对 retained handle 读 PID+创建时间后作用同一句柄，避免“先查 PID、另开句柄杀”的竞态。[快照 `src/session/process_identity.ts:4-74`、`src/session/durable_store.ts:80-129`；D05 audit A1；D19 独立复核]

| 标识 | 运行时用途 | 不能混用 |
| --- | --- | --- |
| owner_epoch | 每次合法会话所有权接管递增，所有 DB 写带 fencing | 不能每次 Esc 都接管 owner |
| stream_generation | 每轮请求/取消或 reset 后隔离模型流回调、timer 和 UI 更新 | 不是已持久结果的有效性判断，也不是 runner 授权 |
| control_epoch | runner 接管控制权/排除旧 controller，绑定 run/token | 不允许凭更大数字绕过 DB owner；新 controller 先合法取得 owner |
| event_id / seq | 事件幂等身份与持久投递次序；wait 固定 task+run | 不用 task_id 取最新 run 后偷换旧 wait，不靠时间戳去重 |
| request/attempt identity | 归属模型部分输出、usage 与重试；同事实只累计一次 | provider request ID 缺失不能将两个真实收费尝试合并；不当全局 exactly-once |

**流式选择：** client 字节解码/SSE parser → 请求级累积器 → 带 session/run/generation 的业务事件 → 当前轮校验 → UI。tool_call 参数完整合法前绝不执行。取消先关闭本 generation 的接收入口，冻结已累积部分；再关闭网络读取/清理 timer，最终部分 assistant 通过一次性完成口保存。已排队 callback 即使执行也不能污染新轮；client 与 loop 的有限 retry 保持原阶段和次数，有产出不从头重放。[快照 `src/client/client.ts:228-264,271-295,320-376`、`src/agent/loop.ts:628-643`；R-07；WIRE-03/07/08/12]

内容/显示回调失效不表示可信历史结果全部丢弃：旧 generation 对应的已持久工具结果，只能经身份核验与恢复导入；有效 usage 的迟到对账由 request/attempt 身份去重，不能靠旧 UI callback 直接加费。网络 abort 不证明服务端停止生成或不计费；没有最终 usage 的请求保留“统计不完整/估计”，不能伪报零成本。[选择；完整统计要求见 R-11、WIRE-06；D05 流式实验只验证已排队回调]

## 4. 意图—副作用—结果—消息—ack 的提交顺序

### 4.1 一次工具调用

1. **保存模型决定**：完成 assistant/tool_calls 校验，先持久会话检查点，保持工具调用关联；未保存成功不得执行 handler。
2. **PreToolUse 单独受保护**：以同 ToolRef 的 prehook 关联先持久意图，再运行 Hook，再持久结果。已存结果复用；有意图无结果不能自动再跑 Hook。随后把 updatedInput 生成的最终参数用于权限、敏感判断、批量审批、审计与 handler。
3. **等待审批/问题**：保存待交互语义记录后展示；批准绑定最终参数与当前操作。拒绝形成可配对结果。恢复旧交互不复用已死 callback；参数/规则/上下文改变重新裁决。未知副作用不能因旧批准而重做。
4. **提交执行意图**：经 D09 `commit_intent` 校验 owner/epoch、未知保护与同 ToolRef 已提交缓存；记录最终参数、审批来源和执行关联。**事务成功确认以后**才放行真正副作用。capability 非 read 均采用来源保护，network/plan 或 Hook 不因名称被排除。
5. **执行一次**：原生执行器持有执行身份、取消域和资源。外部成功但尚未入库的窗口客观存在；异常不能当作“未执行”。MCP 可能已发送/执行但结果不明，按 ADR-0003 停止透明重放，包括换 tool_call_id 的同类绕行。
6. **提交结果**：使用 D09 `commit_result_and_event` 保存 ToolMessage；有后台 run/事件时在同一 DB 事务保存相关终态/outbox。普通即时工具不虚构后台 run/event。事务确认后才允许复用或向下一模型轮发布“已知结果”。
7. **提交消息与消费**：原序补齐所有 assistant/tool pair；经 `commit_checkpoint_ack` 原子保存消息、background/wait、revision、待消费事件 delivered。成功后才做内存 acknowledge、释放 wait 和发 UI 成功通知。

事实起点：快照 `src/agent/loop.ts:628-696`、`src/tools/execute.ts:91-99,140-225,230-277`、`src/session/durable_store.ts:133-172,188-221`、`src/agent/background_delivery.ts:9-22`。选择将跨端口结果提交整合到 D09 的公共事务口，避免在多个模块各自实现半次提交；没有声称远端效果和本地数据库具备分布式原子性。

### 4.2 两个持久域与崩溃处理

**runner 的 grant/claim/收据文件与会话 DB 是两个原子域。** runner 不直接写 session DB；controller 验证收据身份/日志/附件后幂等导入。离线收据可晚于 controller 退出产生，导入失败不删除原收据，也不重拉命令。收到 IPC ack 仅说明协议请求/响应，不等于 session 消息已提交。[快照 `src/tools/shell_runner.ts:42-72,90-135`、`src/tools/managed_shell.ts:40-115,170-240`；D09 契约]

无工具结果的独立后台进度/attention/终态经 D09 `commit_run_event` 保存相应run与应产生的事件，再通知内存调度器；不伪造ToolRef。纯显示progress可按公共契约仅更新快照，不因此生成可投递的用户消息。[快照 `src/agent/background_runtime.ts:73-94`]

| 崩溃/失败窗口 | 恢复动作 | 禁止动作 |
| --- | --- | --- |
| 可信 journal 可证明尚无意图 | 补“未执行”工具对；后续是否执行由新的明确操作决定 | 恢复程序自动补执行 |
| 意图提交后，无可信结果（含效果可能已发生） | `started → outcome_unknown`，只读核实/显式决定 | 因效果看似 0、模型给新 ID 或工具 readOnlyHint 而重放 |
| 结果已提交，消息尚未保存 | 从结果修复消息，不重复效果；保存完整工具对 | 再调 handler“补齐结果” |
| run/event 提交前失败 | 两者同回滚，不发布成功事件 | 先通知完成再异步补 DB |
| 消息/delivered 提交前失败 | 保留/回滚 staged consumption；重试同一批，不再追加第二份消息 | 先 ack 或丢 inbox |
| 消息/delivered 已提交，内存 ack 前崩溃 | 读 delivered/revision，不重投；内存缓存可重建 | 以未收到内存 ack 为由再通知一次 |
| SQLite COMMIT 回执丢失/取消等待 | 用相同操作身份查询已提交状态；结果未知则暂停新副作用 | 取消 Future 后立刻重发事务/工具 |

前六种故障族已有 D05/D19 合成证据；最后一项是线程化存储口必须验证的产品分支。所有事务错误保留原错；DB worker 队列中的已接受请求要有完成回执与强引用，使用屏蔽外层取消的等待/显式 drain，不能让取消当前轮丢失 COMMIT 结果。关闭连接须在 DB worker 内等待已发请求结束；异常挂起时停新效果并保留“持久确认未知”，不能强杀 Python 线程或伪报取消完成。[选择；D05 线程反例及 R-11]

## 5. 独立 Shell runner、Job 与 Windows IPC

### 5.1 生命周期与启动

选择所有可转后台 Shell 从受管执行后端启动，前台/后台改变观察与取消所有权，不二次 spawn 原命令。runner 是独立 Python 内部角色，启动入口由分发任务提供同版本包/资源定位，不能直接照抄 D19 的 base-interpreter 实验捷径。启动流程为：DB intent/run/launch 关联 → 私有 run 目录/manifest/capability → runner bootstrap 与真实身份确认 → 授权 grant → 排他持久 start.claim → 持久 started → suspended 创建命令、归入 runner 自有 Job → resume。

grant/claim/started 后任意失联均不重启命令。能证明 grant 从未发出的失败才判未执行/failed-before-grant；不能证明就 unknown。启动早死、bootstrap 晚到和 grant ack 丢失都需要受管回执，不能只依赖“已登记 runner 列表”清理。[快照 `src/tools/managed_shell.ts:170-240`、`src/tools/shell_runner.ts:90-135`；D05 audit A3；REC-10]

前台观察同一 runner 的 stdout/stderr 日志增量，保留各通道游标、增量解码与完整溢写；转后台不重置执行/日志，也不把通道合并后猜退出码。大输出不积在无限内存或阻塞未排空pipe中；controller断开不使命令日志写者消失。展示游标可重建，完整结果与终态材料不能依赖UI曾读过。[选择；来源输出职责见 `src/tools/shell_runner.ts:53-63,114-134`；任务14/15]

runner 持命令 Job 的最后有效句柄；默认不让子进程继承多余句柄或 breakaway。必须先确定受管树再放行，不能 spawn 后靠枚举补收。温和取消后预算内不退出可 TerminateJobObject；仍必须等待 retained process handles 与 Job active=0、输出停止，才生成 canceled 收据。Job 的具体创建/继承和外部宿主 Job 约束由平台实现验证；不盲目添加 BREAKAWAY 或宣称任意树逃逸均阻断。[D05 真实 Job；D19 suspended→Job→resume；[Microsoft Job 契约](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)]

**keep-background 的关键：controller 的退出清理边界不能包含需保留的 runner。** runner 自己持命令 Job，controller 只在“未获保留许可的启动/执行”上负责清理；显式 detach 先持久保留政策、确认 runner 可接管，再关闭控制连接。测试 supervisor Job 可兜住所有实验进程，不得机械作为产品 TUI Job。若当前宿主限制无法满足独立生命周期，启动前明确失败/提示能力不支持，不留下无主命令。[R-10；D05 audit 第 4 节 A3]

### 5.2 IPC 路线与 D18 的正确复用

Windows 选择本地私有具名管道、当前 SID DACL、拒远端/首实例、随机 capability challenge/HMAC、run/control_epoch 校验、版本化 UTF-8 字节帧、握手/读写绝对期限。HMAC 不代替 ACL；同用户其它进程仍在相同信任边界，独立账户访问尚未验。协议解析错误、超长、半帧和无响应连接必须收口。[D18 报告及最终独立复核；MM-668/704，NEW-02]

**原生 I/O 只在专用受监督 IPC helper 里运行。** controller/runner 通过公开 asyncio subprocess 管道与 helper 交换有限数据；helper 不执行 Shell、模型或 session 事务。helper 对 Connect/Read/Write 在原生提交前持有 handle/event/OVERLAPPED/buffer/count；CancelIoEx 后只有真实完成/确认未提交才释放。未确认完成则保留材料、poison 禁止复用，走 helper 最外入口 fail-stop；父进程持原 handle 确认退出后，才认定该 helper 的资源已由 OS 回收。诊断抛错也不能绕过保护。

这是从 D18 UAF 风险推出的**工程选择，尚无产品证据**。它把不可安全展开的裸 I/O 故障隔离到 transport：IPC helper 失败时，UI 可继续呈现 unknown，runner 本体仍能监督 Shell Job 并保存收据；不能让整个 UI 或业务 runner 为清 ctypes 材料直接自杀。只有确认旧 helper 退出/旧端点释放后才能新建 helper/端点，并使用新的不可猜 endpoint nonce 防晚到连接。若无法确认退出，保留句柄/故障状态，不宣称已回收或启动第二个竞争端点。

该隔离增加一个内部角色，但不改变原模块的业务所有权、不增加用户操作入口。实现 15 必须从真实产品角色入口验证父/子及最终产物，不得以 wrapper 代替目标保护，不把 D18 18 passed 移作产品通过。将来若以成熟绑定替换 raw 实现，须证明相同所有权/有界退出契约再缩减 helper，而非仅凭库名删掉边界。[D18 最终复核“两处阻断”；D05 线程反例]

帧与时限按 [D09 唯一契约](09-storage-extension-route.md#epoch-contract)：长度前缀UTF-8 JSON、增量严格解码、产品请求上限262144字节，先检查长度再分配；握手总期限3秒、最多3次重连。冻结来源 `src/tools/shell_runner.ts:137-174` 是 JS 字符串 buffer 长度65536，不是UTF-8字节，需容纳边界内合法中文/emoji/JSON转义帧；大输出走日志/附件引用。D18的4096/350ms/1500ms仅为probe阈值，不替代产品值。读写/取消完成预算显式有界并保留未确认出口，具体产品证据交实现15，不另创持久schema。

## 6. 取消与退出契约

| 动作 | 真实顺序和结果 | 不承诺 |
| --- | --- | --- |
| Esc/pause | 模态输入层先消费；清队列须持久标记 discarded，释放 wait，关闭 stream generation、请求当前轮停止、保存 paused | 不 cancelAll 后台；不回滚已发生效果；清队列是用户显式动作，与崩溃丢已确认输入不同 |
| 模型流取消 | 停止当前消费和 timer，关闭 transport，保留部分一次；旧回调过滤 | 服务端停生成/不计费、远端效果未发生 |
| 工具线程取消 | 停止派新工作，发合作令牌，保留在途 Future，等待真实结束/结果提交 | `CancelledError` 不能证明线程止写；没有强制安全杀线程 |
| 工具进程/Shell取消 | 先持久 requested/canceling，按真实执行器温和停止→必要时 Job 强停→确认受管树/日志关闭→提交 canceled/事件 | 超时只到 unknown/未确认；Kill请求不当完成 |
| TaskStop 普通代理 | 记录 canceling，停止新模型/工具轮，收齐在途工具/Hook/持久请求，再 settle/canceled | 未决副作用不通过补一条“取消”消除 |
| 前台 Shell 转后台 | 保持同执行/run，先持久交接和 background 标识，再解绑旧前台取消令牌 | 旧轮随后 abort 不结束后台；不二次执行命令 |
| 前台 Agent 转后台 | 在安全消息边界保存子检查点，旧生成器及嵌套前台执行确认收尾后，按来源接续新后台任务；记录 predecessor/new RunRef | 来源5秒 race超时不能视为旧执行已停；无法确认则中止交棒并待核实，绝不双跑 |
| 普通退出/EOF | 阻止新输入，持久状态，停loop/订阅/模型/非保留执行，收齐任务与DB请求，关闭扩展/观测，释放owner与终端模式 | 关闭scheduler不等于OS进程已关闭；正常退出不必标done=true |
| 显式 keep-background | 仅保留有独立协议、身份、收据与接管路径的 runner，保存 detach 决定；其余执行安全收尾/记 interrupted | 不保留普通内存 Agent/Monitor poller；不由owner退出实验推断注销/系统重启存活 |

来源：`src/agent/session_scheduler.ts:58-76,109-149`、`src/agent/tasks.ts:124-131,154-163`、`src/tools/agent.ts:262-370`、`src/tools/shell_runner.ts:42-88`；R-10；RUN-04/10/12。**Agent 转后台不是 Shell detach 的同一实现**：源码真实创建新 agentId/run，保留消息；Python 不能把新旧执行同时跑来模拟“平滑切换”。

正常退出的 `cancelAll` 也覆盖仍为 running 的手工条目：保存为 canceled 即可，没有执行器需等待；不能因为它没有 controller 而漏掉来源这条清理语义。[快照 `src/agent/tasks.ts:267-271`]

自然完成与取消相撞时，由执行器提供实际完成事实和取消到达次序；已确认终态不回退，重复取消/收据按同 RunRef 幂等。若取消请求到达前真实效果已完成，可记录已完成加取消请求审计，不能为了UI按钮强改成“效果未发生”。无法确认停止则 unknown，并保留未决工具journal；unknown 不是已知终态。[选择；R-09/10；快照 `background_types.ts:1-41`]

## 7. 持久边界：输入、附件、审批与费用

具体字段、schema版本和事务签名遵循 [D09 StoragePort v1](09-storage-extension-route.md#storage-port-v1)。本节是运行时义务；除来源明确字段外，均为规格“自身完整恢复”下的补齐选择。

凭据只保存必要引用；intent、输入、审批、收据和异常不得为了恢复把真实凭据明文复制进会话/日志。执行时通过配置端口解析引用；引用失效或无法还原同一操作须明确停止，不以脱敏占位值冒充真实参数继续执行。具体敏感字段处理及兼容策略由D09统筹。[R-11]

| 对象 | 何时算确认/如何恢复 | 边界及相应职责 |
| --- | --- | --- |
| 已接受输入队列 | input identity/顺序/正文或附件引用入库后才向输入端确认排队；安全边界消费、Hook结果和历史保存保持关联，失败不丢旧队列 | queued/consumed/discarded 可区分；pause显式丢弃有证据；恢复不会在原工具对中间插入；任务11/26，RUN-01、REC-07 |
| 未提交编辑草稿 | 可存last_draft改善恢复，但它仍是待编辑数据，不能当用户已提交指令自动执行 | R-11不承诺未提交草稿崩溃恢复；UI重绘/正常交互不丢草稿另属D10/WT |
| 输入图像与大结果附件 | 已确认输入依赖的附件先保存/校验，再提交引用；结果超过来源24000字符阈值先持久全文，再登记hash、消息/事件引用 | 临时上传/clipboard buffer不能替代持久附件；缺失/篡改成为未决，不伪装完整；Unicode阈值按来源golden；任务16/64 |
| stdout/stderr | runner在终态前flush并关写者，收据记录身份和输出引用；导入时确认文件/哈希等所需材料 | 不将日志路径存在推成完整；轮询游标是展示状态，不改变执行终态；任务15/16 |
| 审批/问题 | 保存类型、操作关联、最终参数身份、选择/待回答状态；重启生成新UI交互ID，恢复语义状态 | 不序列化活callback/Future；不复用过期回答授权不同操作；已发生效果仍受unknown保护；任务09/17/21/49 |
| 消息/等待/事件 | checkpoint+background/wait+revision+delivered同事务；wait固定task+run，prepare→save→commit，存失败rollback consumed | TaskWait 1—32、any/all、错误/取消/attention唤醒；manual/前台/unknown/interrupted仍按来源拒绝；任务16 |
| 模型用量/费用/预算 | request/attempt事实去重后持久累计+分模型桶、估价依据及必要预算状态；恢复前再计算提醒/硬停 | 默认提醒、显式hard才硬停；未知usage不编造零，旁路进度tokenCount不是计费真相；任务28，WIRE-06/11 |
| 子代理/反思/父子消息 | child checkpoint保存messages、模型/定义/路径、普通/fork/exactTools所需描述、权限与预算必要元数据；接受的TaskSend/attention经持久安全边界交付 | 不序列化registry活对象；无材料不回退普通agent；反思和SessionStart上下文有身份防重复注入；任务40—44/49 |
| 手工任务 | 独立记录保存描述/状态/结果，恢复列表与更新 | 不把manual编成agent，也不加入可等待执行集；任务45 |
| 清理/分支 | 活owner、runner、未解决journal、引用附件与可恢复checkpoint均作为GC根；分支聊天不复制执行 | mtime不单独授权删除；聊天/代理/影子Git/SQLite WAL checkpoint分开；任务26/27/81 |

来源字段与缺口：`src/session/log.ts:28-41,94-140`、`src/session/session.ts:17-31,52-65,91-94`、`src/agent/background_runtime.ts:64-104,162-183`、`src/agent/runAgent.ts:368-415`、`src/agent/tasks.ts:115-120,245-250`；R-11已明确补齐分模型费用与已确认输入，不能因冻结源内存实现较少而降级。

## 8. 异构执行恢复表

启动恢复顺序：核验运行库/路径/版本与可信checkpoint → 取得合法owner/epoch → 绑定store与runtime → 核验run/runner/附件/代理材料、归类未决 → 修复工具pair → 保存恢复checkpoint → scheduler.recover。存在unknown/interrupted/未决/待投递事件时保持paused；只有安全且身份完整的waiting恢复事件等待，不靠循环模型poll等待任务。[快照 `src/session/recovery.ts:7-72`、`src/agent/session_scheduler.ts:40-51,109-139`；R-11]

| 类别 | 保存/恢复什么 | 继续与停止的边界 |
| --- | --- | --- |
| Shell runner | manifest/token、grant/claim、runner/child身份、控制epoch、输出与terminal receipt；先可信终态导入，否则原runner重连接管 | 不重拉命令；runner失联/结果缺证据则unknown。显式decide有证据才解除；不承诺runner自身崩溃后重启原命令或跨系统重启继续 |
| 普通后台 agent | agent messages、定义/模型、worktree、run/tool scope、权限/预算等；原执行器丢失时running/canceling→interrupted | 用户显式continue/已授权TaskSend续接路径创建新run，先解决未知；一次性explore/plan维持来源不支持恢复。不是重新连上原Python栈 |
| fork/exactTools agent | 除普通材料，还保存父上下文来源、实际system/工具集合与裁剪模式、隔离/路径关系、定义版本等足够描述 | R-09要求可显式继续；来源resume对fork描述不足是待补齐差异，不能称已具备完整fork恢复。缺材料时blocked-recovery/明确报错，禁止退普通agent或复制父执行 |
| Monitor | 保存真实kind=monitor、命令执行关联、已持久行事件/终态/通知游标和超时/persistent语义；执行采用会话受管进程/Job | 不伪装普通agent。owner活时事件驱动输出分行+200ms批量；owner丢失后仅重建已知历史并标interrupted/unknown，不自动重启脚本，不保留无主poller；显式重建是新执行需权限/journal |
| manual | 保存记录、状态、描述和结果 | 不启动工作、不造转录、不接管执行器；停止仅改变记录 |
| 会话loop | 保留可展示的配置/历史和已接受排队输入；owner活时按周期投递scheduler | timer随owner结束；恢复默认不补触发停机期间tick，不宣称OS定时。OS Schedule/Cron由独立平台任务负责 |
| 反思/异步fork/消息 | 保存checkpoint及已完成产物/投递身份，结果仅安全边界注入 | 未知工具不重放，已完成产物不重复注入；无法恢复的执行明确中断，不能“为了恢复”偷偷新增模型调用 |

`blocked-recovery` 是恢复诊断，不是新增ExecutionStatus；对应run保持真实interrupted/unknown。monitor/manual的类别在D09同一RunRecord契约维护，不在这里另造持久记录。

来源：`src/session/recovery.ts:29-70`、`src/agent/resume_agent.ts:84-126`、`src/agent/runAgent.ts:400-415`、`src/agent/fork_agent.ts:11-25,129-148`、`src/tools/monitor.ts:48-115`、`src/agent/tasks.ts:115-120,154-180`。Monitor当前源码在abort/timeout发kill后立即finish，不能作为R-10真实close的验收预期；Python须修到真实关闭后终态。这属于已定取消契约的实现修复，保留来源差异证据，不新增用户取舍。

恢复决定统一走 D09 `record_recovery_decision`：`resolve`处理ToolRef未决，`decide`处理unknown RunRef，`continue`处理可恢复interrupted agent；决定与用户历史同事务，保留说明与旧状态。决定是用户处置未知，不把任意解释伪装成客观执行证据。连接/能力发现允许重试，与MCP工具请求重放分开。[快照 `src/index.ts:1284-1306,1369-1385`；ADR-0003；REC-08]

## 9. 对应与实施门禁

下表为本路线的职责交接，不改权威 [module-map](../../ruocun/module-map.md) / [acceptance-matrix](../../ruocun/acceptance-matrix.md) 状态。全部产品证据仍待实施；T-01/T-04的来源oracle、真实进程与分层口径继续适用。

| 路线单元/原模块 | MM / 案例 | 正式实现任务 |
| --- | --- | --- |
| client流/usage/retry、loop | MM-439/441/443/404/600；WIRE-03/04/06—12 | 04/05/06/08/28；不改变D09配置/模型路由所有权 |
| scheduler/input/foreground | MM-422/385/762；RUN-01/02/04/12、WT-03/04 | 11/18/26，终端65—67及最终77；D10拥有输入/渲染库路线 |
| execute/审批/Hook | MM-642/593/477；RUN-05/06、REC-05、PERM-01—03、EXT-06/07 | 09/10/12/13/48/49 |
| DB/身份/恢复 | MM-591/593/595/597/598/600/601/602；REC-01—09/12/15/16 | 07/10/17/26/28；D09持有唯一schema/StoragePort |
| Shell/process/runner/IPC | MM-637/668/689/704、NEW-01/02/03；RUN-10/12、REC-09/10/12、WIN-01—04 | 14/15/17；平台实现与79/80/81发布验证 |
| BackgroundRuntime/delivery/wait | MM-381/383/384/385/726；RUN-03/11/12、REC-06/11 | 16；后台结果附件、消息事务和ack共享D09口 |
| 普通/fork/恢复/scatter | MM-401/417/420/424/621/674/721；RUN-07—09、REC-07/08 | 38/39/40/41/43；代理定义/工具裁剪不因统一类型合并 |
| 反思/长任务/父子Hook | MM-408/410/413/415/430/370/372；MEM-03、EXT-07、CMD-goal等 | 42/44/49；只在安全边界注入 |
| manual/Monitor/loop | MM-713/715/717/725/676/424/747/422；RUN-09、TOOL-Monitor、CMD-loop | 45/46/47；各类执行恢复边界如第8节 |

### 9.1 必须由产品实际路径重新验证

1. **04—12/28：** fake Chat/Responses SSE 拆UTF-8、多帧/心跳、部分输出、idle/取消/迟到callback；多输入保序、queue保存失败、pause显式丢弃；8并发/屏障/all-settled、Hook一次与最终参数审批；usage按真实尝试去重及多模型重启费用连续。来源失败标记疑点按T-01独立oracle，不从Python输出回填预期。
2. **07/10/16/17：** 沿D05/D19故障族，在实际worker同retained handle校验身份后强杀，确认退出才冷恢复；至少三次独立恢复；追加DB工作线程取消等待/commit回执丢失、checkpoint/ack间kill、附件缺失/hash错与等待rollback。证明产品不重效果、不重投已确认事件。
3. **14/15：** 每种支持Shell方言的真实argv/env/中文/管道、子孙忽略温和停止后的Job收口；grant前后、claim后spawn前、bootstrap迟到、controller正常退出/外部结束与接管，前后台交接和显式keep-background各自验证。保留宿主Job限制分支，不继承D05外层supervisor为产品保证。
4. **15/平台IPC：** 用真实产品helper/controller/runner入口重做D18 native提交前所有权、未确认取消/完成、诊断异常保护、原handle退出确认、旧端点释放与新端点接管。分别记录真实OS完成和适配注入；覆盖source65536字符/中文emoji/转义及byte上限、半帧、错误token/run/epoch、无响应握手和资源耗尽。不让测试wrapper替目标保护。
5. **40—49：** 实际普通agent/fork检查点恢复、定义/模型/工具/路径缺失阻断、转后台旧执行未停则不交棒、TaskSend/attention投递去重、scatter排队取消、Monitor真实close再终态、manual无执行器、loop退出无tick；离线模型fixture验证请求/状态，不冒称真实模型质量。
6. **发布79—81及D13：** wheel/standalone/controller/runner/recovery分别核验角色是否使用DB及其实际SQLite version/sourceid/compile options/驱动与DLL摘要；使用DB的角色统一初始化且不先加载旧库，拒静默fallback。Windows x64运行库采用D09已选的官方3.54.1 + stdlib路线，具体产物布局交D13/发布；其它平台/架构须有官方修复/可审计backport，不能仅比较数字。仓库外无PYTHONPATH/开发DLL路径再运行上述恢复合同。

沿用既有 `python -m pytest`、`python -m ruocun_acceptance <suite>`（分别选择 runtime、protocol 等）已确认入口，不再请求测试入口批准；若实施确需新增内部故障注入端口，按T-03先登记最高层边界及仅测试可达条件，不能自加长期隐藏产品API。所有测试子进程显式env白名单、合成HOME/config/session、受管身份与清理回执；真实模型、Windows Terminal与最终人工验收分别交75—78/85，不在本研究中调用或代签。

## 10. 本轮完成与剩余边界

本轮完成技术路线、源/实验/规格/任务映射及D09公共契约对齐；只新增本文，未修改产品、冻结源、probe、统一Status/map/spec/matrix或全局配置。命令环境从显式OS变量白名单构造，HOME/配置指向本worktree合成根；没有模型调用、真实凭据/会话读取或大型probe重跑。只做快照verify、只读源码/报告核对与报告静态检查，**没有新增产品测试通过数**。

尚需证明的不是新的范围决定，而是既定路线的产品实现：IPC helper隔离与分发、SQLite串行线程取消回执、完整fork恢复材料、Monitor真实停止、队列/审批/费用持久化、真实产品故障注入和最终终端体验。独立账户/断电/注销/重启/其它系统未有相应证据时如实保持未验；本报告不据有限样本承诺这些能力。主会话收录时保留D05/D18/D19历史失败与接收指针，不把研究完成等同完整迁移完成。
