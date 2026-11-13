# DeepSeek Harness 压缩改造实施计划

状态：**自动实现与验证完成，人工体验待验**；最终B-r3交付、真实结果及R1/R2/R3证据复用见delivery.md，决定见ADR-0020。
日期：2026-11-13（Asia/Shanghai）。
范围：用户已选择 B（核心压缩机制＋完整原文归档与回查），并在规划轮后授权完整实施。保留原规划细节，产品结果按实际回执登记。
本批只操作合成会话；不升级真实会话、不调用真实模型，不以范围选择代替技术验收。
规格和验收定义以同目录 `spec.md` 为准；本文件组织实现顺序和接缝，不复制长规格。
来源：[proposal.md](proposal.md)、[research.md](research.md)，固定上游 `e8f7b93a344964de3dca1ace9e72b6e4d6de87cb`。

## 1. 实施基线与责任

- 启动 T01 前读取 CONTEXT、ADR-0005/0009/0012/0014/0015/0018 和当前 implementation；重新核对本目录规格状态。
- 当前压缩文件已有未提交改动；先绑定 HEAD、逐文件差异与哈希，建立包含代码和记录的工作快照，再按位置合并。
- 保留已完成的记忆来源标签修复；DAO 参考目录只读；本次新增来源单独保留 MIT 归属。
- 主协调持有 runtime、client 请求封装、共享存储契约和集成记录；实现者只改派发文件。
- T03 存储契约独立复核后才供 T04/T05 消费；同一存储文件不得并行各自定义接口。
- 所有新增类型和接口名在本计划中均为提议；T01 固定后统一导入，不在各模块另造版本。
- 自动验证、真实模型、真实 Windows Terminal 和用户体验分别记录；本计划不增加真实模型费用授权。

## 2. 沿用的模块接缝

| 模块 | 计划职责 |
| --- | --- |
| `agent/compact.py` | 纯候选计算：普通工具裁剪、配对切点、近期尾部、摘要替换计划。 |
| `agent/context_runtime.py` | 统一预算、摘要请求与质量检查、失败熔断、提交后减量判断。 |
| `agent/loop.py`、`agent/runtime.py` | 完整请求准备后的压力检查，自动/手动/超限与模型切换接线。 |
| `session/archive.py`（新增） | 消息来源、分段与清单校验、读取/导出投影；不自建数据库连接。 |
| `session/contract.py`、`storage_worker.py`、`durable_store.py` | 同一 StoragePort、线程、owner fencing、事务和幂等回执承载归档。 |
| `session/conversation.py` | 锁内校验预期投影，提交原文及候选后才确认内存状态。 |
| `agent/run_agent.py` 的 `_AgentJournal` | 子代理范围的同一接口 Adapter，复用父会话 SQLite。 |
| `session/log.py`、命令与工具注册 | 完整导出、当前视图导出、归档列表和按段读取。 |

保留 `compact → 生成候选 → journal 确认 → 交换 messages` 顺序；不引入 Cordis、TS 运行时或第二个会话权威。
`agent/resources/compact.zh.txt` 改为中文单份交接记录；旧摘要参加重整，不再由程序永久拼接。

拟固定的内部数据形状：

- `RequestPressure`：目标路由、最终输出cap、W/M/B/T/R/S、估算输入和估价限制。
- `ProjectionSnapshot`：scope、当前消息/lineage、scope revision、内容摘要、有效请求描述；不保存凭据。
- `CompactPlan`：候选消息、候选lineage、被替换区间、原文批次、派生记录及可核实减量。
- `ArchiveBatch`：预期scope revision、新原文/消息版本、派生记录、边界、候选lineage和附件digest。
- `ArchivePage`：绑定scope的段元数据、稳定文字分页、next_offset、图像描述及完整性状态。
- 函数返回值区分 `unchanged`、`compacted`、`no_progress`、失败；只有compacted且提交确认才允许超限重试。
- 这些类型的唯一声明放 `session/contract.py` 或新增纯类型模块；策略模块只消费，不持有StorageWorker。

## 3. 预算和默认配置（AC01、AC11）

1. 在请求消息、动态工具、模式与路由确定后构建与 client 一致的有效请求描述，计入系统提示、工具定义、新增消息及图片。
2. `W` 使用目标 provider/model 的当前窗口；`/context-window` 手动锁继续有效，模型切换仍重新校验参数。
3. `O` 复用 `client.resolveMaxTokens()`、模型 output cap 和最终 wire 请求体的实际输出上限。
4. `extra` 最后覆盖的现有契约继续有效：Chat 读取最终有效字段，Responses 读取最终 `max_output_tokens`，避免测量和发送各自猜值。
5. 只有输出上限完全来自 client 默认值时，预请求将实际默认上限限制为 `min(既有有效默认值, floor(W/4))`；同一值写入真正发出的请求。
6. opts/env/extra 显式指定的输出上限不静默缩小；有效值不是正整数或 `O >= W` 时明确报参数错误并停止该次请求。
7. 默认 `M=W-O`，`B=min(65536, max(32, floor(0.08*M)))`，`T=floor(min(0.8*W, M-B))`。
8. 默认近期预算 `R=floor(0.16*M)`；允许显式固定 token 替代比例，但不同时接受两个相冲突的来源。
9. 默认摘要输出上限 `S=min(8192, max(128, floor(T/4)))`；摘要请求在其目标窗口另行校验 `输入+S+余量`。
10. 校验 `M>0`、`B>=0`、`T>0`、`0<R<T`；显式非法参数直接说明原因，避免默认小窗口被固定 65536 全部拒绝。
11. 1K、8K、128K、1M 窗口均以合成最终请求体验证公式；例如 1K 默认 O=250、M=750、B=60、T=690、R=120、S=172。
12. 自定义摘要模型放不下选定旧段时明确停止并提示配置；本轮不增加分块递归摘要或静默改换模型。

拟用原生环境参数：`RUOCUN_COMPACT_THRESHOLD_RATIO`（0.8）、`COMPACT_HEADROOM_TOKENS`（自适应）、`COMPACT_RETAIN_RATIO`（0.16）、`COMPACT_RETAIN_TOKENS`（未设）、`COMPACT_SUMMARY_MAX_TOKENS`（自适应）；后五项均使用 `RUOCUN_` 前缀。
既有 `RUOCUN_SUMMARY_MODEL`、取消信号、失败冷却和明确硬预算继续复用；不新增一套 profile 配置系统。
计量仍为统一启发式估计，不冒充精确 tokenizer；API 实际用量单独显示并用于校准，不能拿上次用量漏掉本次新增输入。
计量器必须覆盖最终 schema/消息结构开销；图片采用明确、保守的路由估价，无法估价时显示限制并保留服务端超限出口。

## 4. 候选策略（AC02—AC04、AC10、AC12）

- 触发压力后，在深拷贝中裁剪过大普通工具文字；默认按 Python Unicode 码点超过 8192 时保留头 4096、尾 1024及明确中间省略标记。
- 裁剪描述包含可读取的归档段 ID；真实摘要/读取线索的包装开销计入候选大小。
- TaskWait 控制 JSON、未确认结果、未确认的后台投递消息和恢复代码消费的控制资料保持原样；不修改工具 journal。
- `role/tool_call_id`、工具调用 ID、推理字段、`responseItems`、图片与 `imageDelivered` 投递状态完整保留。
- 先裁剪后重测；足够减量则不调用摘要模型；仍超阈值才选择较旧区段。
- 按 R 从尾部累计，使用 pending call ID 集合把切点向前调整至完整工具组之前，验证重复/孤立 ID。
- 至少保留最后一个完整消息或工具组；极大单组导致无可压区时明确报告无进展，不伪报成功。
- 首条系统提示及当前 SessionStart Hook 等明确控制前缀保留；按标记寻找旧摘要，不能假设其总在 index 1。
- 固定八节中文摘要保留用户目标/限制、事实与证据、文件、失败、未完成工作和下一步；只在必要处引精确原话。
- 旧摘要和新旧区段一次重整；旧 Todo 包装移除，最新 Todo 单独钉住；最新运行状态仍由程序权威提供。
- 摘要空白、partial/failed、取消、`length/max-tokens` 截断、非文本无有效正文均失败。
- 含系统包装与归档引用的新摘要必须严格小于被替换段，最终候选也必须减少统一计量压力。
- 裁剪与本次摘要都准备完成才提交一次；摘要失败时本次裁剪副本一起放弃，保持 ADR-0012。
- 一次触发最多两次有实际提交减量的尝试；超限恢复复用既有有界计数，未确认进展时不重发相同超长请求。
- 手动短对话可以无操作返回；自动压力无可压区则明确停止；两者结果类型不得混淆。
- 不改变默认费用提醒；只有既有显式 hard 预算停止。摘要实际用量含失败/取消末尾用量只计一次。

## 5. SQLite 原文归档结构（AC05、AC08、AC12、AC16）

选择消息分段归档，不移植完整事件引擎；归档和当前模型投影是不同读取路径。
复用已有 `meta(key,json)`，表结构及 `PRAGMA user_version=1` 保持，归档内容仍由 SQLite 唯一持久化。
主范围为 `main`，子范围绑定真实 `run_id`；范围由可信 Journal/ToolContext 提供，模型不能指定数据库或任意路径。
每范围维护单调 `raw_seq` 和有序分段；相同正文的两次真实输入分配两个序号。
普通 save 把本次新增、已接纳的消息作为一批原文写入；压缩前尚未保存的新消息也在同一事务中补齐。
当前投影维护 lineage：指向原始消息身份及版本，或指向 summary/prune 派生记录；生成摘要本身不冒充真实用户原话。

建议键与最小记录：

| meta 键 | 内容 |
| --- | --- |
| `archive:manifest` | `format=1`、本地 session 身份、范围清单、每范围 revision/next_raw_seq、有序段索引、覆盖起点及旧资料缺口。 |
| `archive:raw:<scope>:<id>` | 不可变批次：seq 区间、有序原消息及版本、SHA-256、原来源身份和附件依赖。 |
| `archive:derived:<scope>:<id>` | 摘要/裁剪记录：有序 source refs、旧派生来源链、替换范围、策略版本、摘要结果及用量元数据。 |
| `archive:projection:<scope>` | 与 checkpoint/RunRecord 同版本的来源映射、摘要引用及活动原始范围。 |
| `archive:boundary:<scope>:<id>` | clear/rewind/前缀更新等边界、发生顺序、受影响原文范围和原因。 |

key 中范围与 ID 采用固定编码和白名单；读取使用参数化 SQL，记录插入为不可变语义，同 ID 不同摘要为冲突。
大段按批分 JSON，不把全部历史放进每次重写的大数组；清单只保存短索引，读取正文按需分段。
逻辑身份不依赖正文：显式来源 ID/位置映射驱动普通追加、保留区间、派生替换和分支导入。
`imageDelivered` 是投影投递状态；补充 `responseItems`/推理现场等属于同一逻辑消息的版本更新，不计成新用户消息。
版本更新保留原保存版本及可确认的最新版本；默认人类转录显示该消息最终已确认版本，JSON 导出保留版本记录。
仅允许已知元数据更新路径携带原身份；无显式映射的历史改写直接拒绝，不能按全文相等搜索或猜测合并。
内部来源/归档元数据从 wire 请求明确剥离；摘要正文只携带可供 ArchiveRead 使用的短归档引用。
保留既有存储脱敏后的完整字段、图片 data URL/`imageData` 和附件引用；不额外保存 raw HTTP、凭据或流式草稿。
inline 图片在 SQLite 归档原样保留；外部附件记录准确路径、身份及 digest，沿既有缺失附件处理，不自动重读用户原文件补造内容。
spill 指针依赖纳入归档保护索引，不能只扫描当前 checkpoint；本轮“原文”指已保存的会话/工具消息，不追溯工具内部已截断的原始 stdout。

## 6. 提交、幂等与取消（AC05、AC06、AC10）

1. 取得当前 scope 的消息、lineage、scope revision 和有效请求描述的不可变快照。
2. 在锁外计算预算、裁剪及摘要；候选携带新增原文批次、派生记录、附件依赖和预期来源映射。
3. 回到现有 checkpoint 锁内，比较预期模型投影/lineage及scope状态；合法排队输入只增加父 revision 时不误判内容变化。
4. 深拷贝冻结 `ArchiveBatch`，将其规范 JSON/digest 纳入整个操作的 request_digest 与 operation_id。
5. StorageWorker 将同一请求派给既有 SQLite 串行线程；事务中验证 owner、会话、scope revision、被替换范围和工具配对。
6. 同事务插入原文/派生/边界，更新 manifest与projection，再更新 checkpoint或子RunRecord、事件确认及幂等回执。
7. 同 ID/同 digest 返回既有结果；同 ID/不同归档或候选一律冲突；失败回滚后按既有已确认失败规则重试。
8. 只有提交回执确认才更新 `Session.messages`、scope来源映射、子代理任务视图及上下文用量基线。

拟扩展现有 `commit_checkpoint_ack(..., archive_batch=None)`、`enqueue_checkpoint(...)`；无归档请求保持旧调用方式。
`checkpoint_request_digest()` 覆盖归档规范内容/附件digest/来源版本；不能只哈希摘要后的 messages。
`Conversation.replace_context(..., expected_projection=..., rewrite=...)` 为主接缝；普通追加 save 通过同一归档归一化入口。
数据库事务失败时原文批次、派生记录、candidate checkpoint和事件确认全部回滚。
取消 Python 等待不等于线程停止；已排队操作继续持有材料，并沿 OperationHandle 查询已提交/失败/未知。
未知提交标记 blocked，保留旧内存视图且停止本轮；重开按 operation_id/digest 回读，不能自动重做摘要或派发工具。
摘要失败保存原上下文时，正常 save 仍可原子补齐新增原文；失败摘要不产生成功派生记录。
按现有 BackgroundRuntime 的精确控制结果确认事件；投递账本、waitId、runId和尚未投递事件不交模型重新生成。

## 7. 存储语义版本与旧会话（AC09）

- 新原生会话 `identity.storage_version=3`；`archive:manifest.format=1` 独立描述归档格式。
- `USER_VERSION` 继续 1，保留 `LEGACY_SESSION_USER_VERSION=2` 原含义；语义版本也选 3，避免把两类版本混淆。
- 老程序在 `_validated_checkpoint` 的 storage_version 门禁处拒绝新格式，业务 owner 写入前即停止；不承诺底层目录防护完全零触碰。
- 新程序普通打开/续接 v1 会话时只提示需要显式离线升级，不自动改写；历史列表可只读显示版本和需升级状态。
- 提议入口 `ruocun --config <合成或原生配置> --cwd <工作区> --upgrade-session <id>`，在普通会话 claim/模型初始化之前分派。
- 升级前停止全部使用目标会话的旧进程，包括已通过旧版预检但尚未claim者；本轮提供离线升级，不另建并发升级协议。
- 升级拒绝活动 owner/活动 runner、未知结果或未确认提交；先提示具体未满足条件，保留原状态。
- 显式升级先用 SQLite backup 接口产生独立私有备份，检查数据库完整性及原身份，记录备份路径和摘要。
- 备份确认后开启维护事务，再核对 revision、owner和版本未变；若变化则停止，要求重建备份，不复用过期备份结论。
- 升级事务导入当前主/子投影为 baseline 原文，创建 manifest/lineage并升 storage_version；现有输入、工具、事件、runs和权限保持。
- 现存旧摘要所遮蔽的原文无法补回，manifest记录 coverage_start与legacy_gap；导出明确标记覆盖缺口，不称历史全文恢复。
- 失败升级回滚、备份保留；回退操作为停止进程后显式恢复该备份，本轮不做自动降级。
- 未知未来语义/归档版本仍拒绝；版本检查同样覆盖只读inspect、prune seal、恢复和包外读取路径。

## 8. 查询、导出与生命周期（AC07、AC08、AC13、AC14、AC16）

`/archive list [--scope <本会话已登记范围>] [--offset N --limit N]`：分页返回段ID、类别、序号范围、覆盖缺口和摘要引用。
`/archive read <id> [--offset N --limit N]`：稳定文字呈现按 Unicode 码点分页，默认4096、最大16000，返回 total/next_offset。
新增只读 `ArchiveRead`：参数 `id`、`offset`、`limit`，范围由当前主/子 ToolContext绑定；不接受任意会话ID、scope或路径。
主模型只能读取本身范围及明确派发结果允许的引用；用户命令可查看当前数据库登记的主/子范围，不能跨工作区猜ID读取。
查询复用只读 StorageWorker 任务，不暂停运行、不调用摘要模型、不改变归档内容；普通工具调用的既有journal记录照常。
图片默认返回描述/附件ref/digest，不把巨量base64塞入模型；需要图像时走已有Read能力与权限，不自动执行历史命令。
`/export` 默认按raw_seq完整输出已覆盖原文与clear/rewind边界，包含被移除部分及状态标记。
`/export --context` 只输出当前模型投影；`/export --format json` 输出机器可读完整归档字段/版本及图片payload或准确附件引用。
导出按scope与已记录时间序输出，消息身份只出现一次；同文两次保留两次，摘要来源链不再造成原文重复拼接。
导出复用现有脱敏与私有文件发布；大历史流式读取分段，不能为一次命令常驻加载所有历史/图片。
`clear` 保存待确认新增原文并记录clear边界，清当前投影及Todo；输入、journal和归档继续保留。
`rewind`（含code）记录被移除投影的来源范围与回退边界；工作区恢复仍走原WorkspaceRestore journal，归档不被文件快照回退。
代码恢复与数据库不宣称跨域原子；文件恢复已成功而会话提交未知时沿现有未决保护停止，不自动恢复第二次。
`branch` 仅将当前投影可达的归档来源闭包复制到新数据库，保留这些来源的原始顺序/版本，再一次提交新checkpoint。
不复制当前投影未引用的废弃分支或clear前独立epoch；目标manifest标记该覆盖边界，避免声称继承父会话全部历史。
复制保留原来源身份/版本和分支来源，目标manifest绑定新session；后续本地序号独立递增，不依赖父数据库存活。
分支沿现有“当前上下文快照”语义，不复制父会话的可执行副作用/等待所有权；子范围只复制实际引用的只读原文闭包。
恢复只加载当前投影及短索引，按需读取正文；模型上下文不因重开而重新展开全历史。
清理只在既有封存门禁满足时删除整个session及其内部归档；活动/未决/被引用附件保护继续有效。
归档存在本身不使已完成会话永久免清理；分支复制闭包后父子可独立封存，外部共享附件仍按显式依赖保护。
损坏段、缺失引用、循环来源或digest不符时停止相关读取/恢复，不静默省略并声称完整导出。

## 9. 主/子代理接线（AC10—AC13）

- 主代理自动、手动 `/compact`、服务端超限和模型切换都接同一策略；最终请求前检查动态工具目录与模式。
- 当前 `runPreparedAgent()` 尚未传 compact 回调；同步、后台、交接后的普通子代理都须接入共享 ContextManager。
- `_AgentJournal.save/replace_context` 不能只替换内存：通过同一 scope归档 Adapter 把批次与RunRecord/recovery_material同事务提交。
- 子代理scope为实际run_id，archive revision与该RunRecord现场绑定；父checkpoint的正常推进不覆盖子来源映射。
- 同步/后台切换保留同一scope；普通恢复沿原run的原文血缘创建新执行边界，权限、工具目录和工作区身份仍按现有核验。
- fork继承父请求的精确工具/消息时复制相关原文引用闭包；继承资料与子任务原文来源分开，不重复计为用户新指令。
- fork/explore/plan原有材料不足拒绝继续的边界保持；新增归档不扩大它们的执行恢复权限。
- 子代理当前输出索引 `output_start` 不能继续按压缩后的messages下标截取；改用来源身份定位子任务输出，保持TaskOutput和前台展示。
- 主/子scope均验证成对工具ID、取消未知提交和图片投递状态；父子归档读取互不越权。
- SessionStart、反思注入、技能目录刷新和图片flush属于显式投影更新，走来源映射接口，避免被当成新真实用户发言。
- `prepareAgentRun` 克隆父ToolContext时清除归档读取回调，再绑定子scope；同一run的前后台handoff保留该scope。
- fork导入只授权其精确继承的来源闭包，标记为继承资料；不因子任务持有一个归档ID而开放父范围全部历史。
- `_AgentJournal` 补齐 ContextJournal 所需的redact/确认接口；scope归档、recovery_material和output_start替代定位一起确认。

## 10. 任务顺序与验收出口

| 任务 | 实现与文件归属 | 完成出口 |
| --- | --- | --- |
| T01 基线契约 | 固定脏工作区快照、来源测试映射、归档数据形状/版本/操作摘要/权限接口，登记设计决定提案。 | AC01—AC16逐项有承担模块及现有证据；规格和计划状态一致。 |
| T02 策略计量 | compact/context_runtime、摘要资源、client有效请求描述；先纯候选及预算。 | AC01—AC04、AC11、AC12纯函数/合成请求定向红绿；不提前接无归档的产品裁剪。 |
| T03 归档存储 | archive/contract/worker/store，主子scope通用批次、版本门禁、显式备份升级。 | AC05、AC06、AC09、AC16事务/故障注入独审通过后冻结Interface。 |
| T04 候选提交接线 | Conversation、主loop/runtime、_AgentJournal、恢复/交接材料；依赖T02+T03。 | AC02—AC06、AC10—AC13主子均有真实普通入口证据。 |
| T05 读取导出生命周期 | ArchiveRead、/archive、/export、branch/clear/rewind、cleanup与附件索引。 | AC07、AC08、AC12—AC14、AC16；按身份去重、跨scope拒绝和独立清理通过。 |
| T06 跨进程验证 | 合成HTTP/SSE与受控SQLite，保存重开、故障未知、模型切换、旧版拒写及手动升级。 | AC01—AC14、AC16完整合成闭环，无真实模型调用；覆盖缺口单列。 |
| T07 构包独审 | 冻结候选、工程入口、许可/说明、wheel-only安装、独立接缝复核。 | AC15及全部AC证据绑定同一候选；实现/自动/体验分别记录。 |

T02与T03在T01冻结后可分文件并行；T04持有runtime公共接线，T05不得并行改其同一区段。
T03/T04出现未确认存储行为时先修复并复核，再释放下游；不靠增加独立“容错存储”绕过唯一权威。
各任务增量交接其来源、实际差异、红绿回执及未验项；不重复生成整套大型汇总。

### T01：先固定调用契约

- 核对所有 `save/replace_context` 调用点，按追加、投影更新、compact、clear、rewind、恢复和分支分类。
- 列出当前主/子messages来源和元数据更新路径，先确定身份传递方式，再实现按序归档；避免在DB层猜测消息身份。
- 固定请求体复用函数、ArchiveBatch摘要规则、版本检查位置与升级命令分派点。
- 交付当前源码哈希、来源断言清单和确认差异；技术提案与用户已确认范围分开记录。

### T02：先验证无副作用的候选

- 用合成请求覆盖Chat/Responses、最终extra覆盖、切模型、动态工具及小窗口；计量和真正发送复用同一请求准备结果。
- 复用上游已冻结的工具头尾裁剪与安全切点断言，再增加RuoCun已有控制结果保护的必要适配。
- 旧摘要替换、Todo钉住、空/截断/变长摘要和无可压区都返回可辨结果；摘要模型仅作为可注入依赖。
- 出口只包含候选与ArchiveBatch提案；T03通过前不接产品历史改写。

### T03：先证明原文与检查点同成同败

- 先实现记录校验、不可变插入、来源映射、分页读取；再扩展主checkpoint与子RunRecord两个现有事务入口。
- 复用一个既有 `_put_meta` 确认回滚 seam，在归档写入后且 checkpoint/回执提交前注入一次失败，核对归档、投影与回执均未半提交；取消和丢确认沿既有独立用例复验，不扩展为每个 SQL 位置的故障矩阵。
- 同时验证“同op同batch”“同op异batch”“scope revision冲突”“owner被fence”和已提交回执丢失。
- 独立复核旧binary写门禁、SQLite备份一致性、显式升级回滚及旧摘要缺口声明后，发布稳定Interface给下游。

### T04：在真实入口消费已审存储

- 主loop在最终请求前调用统一检查；保留on_boundary、技能发现、反思drain及wait_control的现有顺序语义。
- 普通save、图片flush、SessionStart和权限/技能注入全部提供显式lineage更新原因，不静默跳过归档。
- 子Journal先完成scope与RunRecord原子保存，再接同步/后台/恢复/交接的ContextManager。
- 原上下文失败停止测试仍保留；新增减量进展与迟到响应隔离断言，不复用摘要失败后的旧请求。

### T05：沿来源身份实现读取与生命周期

- 读取只接受本地归档ID；先验证scope与digest，再分页呈现，绝不把归档正文解释为命令或权限决定。
- 完整export按有序原身份输出，不把当前messages和所有归档直接拼接；两个同文输入用不同序号确认。
- clear/rewind测试包含压缩前和压缩后场景，核对原文保留、活动投影与边界标记分别正确。
- branch复制闭包和必要附件依赖后关闭父会话，验证分支读取/导出；清理扫描归档索引而非仅检查最新投影。

### T06：跨进程验证而非仅用内存fake

- 采用本地HTTP/SSE fixture和受控SQLite，首进程压缩保存、第二进程恢复并捕获真实首个模型请求。
- 复用既有进程取消/崩溃夹具，确认未知提交在重开后只回读已确认记录，不重复摘要或工具副作用。
- 将旧v1副本、带旧摘要副本和新storage3副本分开；旧程序测试只运行受控合成副本。
- 证据记录最终请求体、scope来源、归档段摘要与退出码；真实模型0调用与摘要质量未验同时说明。

### T07：固定包和独立交付

- 从完成T06的同一候选构建wheel；包外安装后验证新增模块、命令帮助、摘要资源、许可与普通恢复入口。
- 独立审查者不编写被审产品实现；重点查事务、未知提交、来源去重、附件清理和父子scope隔离。
- 产品有修复时保留前轮失败，用新候选重新绑定受影响证据；集中工程出口按ADR-0015复用已有效材料。
- 交付README/发布说明中的升级与回退操作及覆盖缺口；不以代码量或任务resolved代替质量与体验验收。

## 11. 验证与交付记录

- 复用 `test_advanced_context_compact/runtime/conversation`、`test_mvp_loop/product`、n16等待/后台存储、n17恢复及现有图片/子代理测试。
- 来源断言因新行为发生变化时登记“确认差异”；保留旧证据，不能修改预期后冒称原来源语义未变。
- 最少新增：预算最终body、小窗口、真实同文输入两条、元数据版本、二次摘要原文不重、主子scope事务、归档未知提交及旧程序拒写。
- 本地HTTP跨进程验证实际请求、关闭重开、完整export/--context、branch后删父会话、clear/rewind及spill/图片保护。
- 所有进程使用明确环境白名单；HOME/配置/会话均为合成工作区，日志只保存审查过的合成值。
- 摘要文本与权限指令分离：历史归档正文不能授予执行权限、修改工具参数或绕过deny规则。
- 五项现有工程入口按影响执行：pytest、统一验收驱动、Ruff、mypy、build；固定包额外做仓库外纯安装和资源绑定。
- 无真实模型时只证明接线、存储和合成摘要契约；摘要质量不因fixture通过而标“已优化”。
- 新命令涉及Windows显示时做真实WT可操作/缩放技术检查；用户整体体验验收仍单列，不逐票重复要求。
- 提交代码与本目录记录一起交付，保留原有未提交内容的来源；不得用Git clean冒充用户资料已清理。
- 最终记录实际新增/修改规模、版本升级/备份/回退说明、来源许可和未验平台；预算估算不作为已完成证据。

## 12. 执行前最后核对

- 原规划提案已由用户后续的实施指令启动；当前技术决定见ADR-0020，不重新询问A/B或开展采访。
- root核对spec中的D09/D10、AC编号与本计划一致；关键行为的最终决定记录到项目ADR/任务票再进入实施。
- 核对有效输出默认W/4是发出的真实cap，而非仅在UI计算；显式extra覆盖必须与最终body一致。
- 核对普通save原文增量与压缩批次同样进入既有事务；归档不能只在第一次/手动压缩时才开启。
- 核对老程序业务写前拒绝storage3、v1只显式备份升级、legacy版本2保持原拒绝含义。
- 核对工具/图片/后台/子代理/branch/clear/rewind/清理都具有明确的来源身份和验收承担者，之后才领取T02/T03。
