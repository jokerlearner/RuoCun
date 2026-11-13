# D09：持久化、配置与外部扩展兼容路线

后续范围修订：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)收缩跨重启费用连续及特殊fork现场恢复保证；其余唯一StoragePort、事务、已确认输入和数据隔离契约保持。下文保留原研究依据，不能据旧增强措辞恢复已取消承诺。

日期：2026-11-05。任务：[D09](../issues/09-storage-extension-decision.md)。分支 `research/d09-compat`，起点 `8d978824c0163caef851d592d44ba0c4c4f61110`。本报告为本地研究交付，供主代理收录技术决定和需要的 ADR；没有修改公共状态、规格、矩阵或产品，没有 push、PR、merge。使用 `research` 技能；本任务本身是独立后台研究，不再递归派发。

## 结论和状态

选择标准库 `sqlite3` 加受控 SQLite 官方 **3.54.1** 运行库作为 Windows x64 存储路线；以单 owner、专属线程串行写口和显式事务保存权威状态。选择官方 **`mcp==1.30.0`**，由自有 manager 适配其 env、能力回调、错误、生命周期和未知结果。LSP 用窄的 Python JSON-RPC/Content-Length 客户端；Hooks、文本扩展、Deck 保留各自协议。依赖选择依据是已经接收的 D15/D18/D19，不重做大型实验，不把探针通过数继承成产品通过。[D15](../experiments/extensions/README.md)、[D18最终独立复核](../../ruocun/integration-evidence/d18-accepted-review/README.md)、[D19独立复核](../../ruocun/integration-evidence/d19-identity-review/README.md)

RuoCun 默认用户根为 `Path.home()/.ruocun`，项目根为 `<cwd>/.ruocun`，自身会话仅用后者的 `sessions/`。旧配置和扩展可按用户显式声明的兼容路径读取，默认没有兼容路径；不自动移动 `.dao/.codeds`，不枚举、接管、续写 DAO 会话。格式兼容与数据身份隔离同时成立。此为 R-12 明确留给本票的品牌路径决定，不是重新请求用户逐路径批准。[规格 R-11/R-12/R-16](../../ruocun/spec.md)、[ADR-0001](../../../docs/adr/0001-python-migration-boundaries.md)

下文标为“路线”的条目是本票选定的实现约束，尚无产品实现证据；物理 schema 的 ADR 与统一票据由主代理收录。唯一外部行为基准是冻结快照 `dao-f17e189-7ac654a0dc06`（805成员，tree SHA-256 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`）。本轮直接从 ZIP 读源码并逐成员核对长度/SHA-256：805/805、零不符，ZIP SHA-256 `1f8308959d8b9ac0783b6ce6ddbffe7a71cc60bc59332f309f0d62083efac078`。所有 `src/...:行号` 均指该归档，不指活动 DAO。[冻结说明](../reference/README.md)

## 证据采用及限度

| 已有证据 | 本票采用的事实 | 不能外推的结论 |
| --- | --- | --- |
| [D03研究](03-data-extension.md)、[D02研究](02-function-runtime.md)、[D04研究](04-terminal-platform-delivery.md) | 来源五表、journal/事件/owner关联；每种 loader 的真实规则；外部协议子集 | 静态定义及测试文本不是已运行结果 |
| [D05与独立审查](../experiments/runtime/audit.md) | 25项合成契约；意图/结果、消息/ack故障切点；三次独立恢复；取消线程等待不停止副作用 | 非完整 Agent、断电、host退出/注销、真实PID复用或真实模型验证 |
| [D15独立复核](../../ruocun/integration-evidence/d15/merger-review.json) | 候选30b9299、独立6945f41；11 passed，805源及144旧raw字节一致；SDK默认env丢sentinel、来源MCP断线effect=2、Hook超时晚副作用 | 非产品registry、全部标准/第三方服务、SDK v2或全部解析边界通过 |
| [D18最终接收](../issues/18-windows-durable-io-experiment.md) | 最终候选1860c70、接收b858327；独立18 passed；pending材料所有权与退出确认已补证；匿名token三对象真实拒绝 | 匿名token不等于独立账户；4096 probe上限不替代来源65536字符；无断电保证 |
| [D19最终接收](../issues/19-patched-sqlite-runtime-experiment.md) | 0419c42/564f8ca；2 passed、12/12、21恢复、35库清单、34受管进程/Job0；8次强杀同句柄绑定真实worker | 旧launcher身份缺口未被抹去；非上游WAL-reset缺陷复现、产物验收或全平台ABI证明 |

本轮只做来源/工程记录读取、归档校验和文档检查，没有运行模型、扩展命令、native探针、真实配置或付费API；没有更改全局环境。后续进程按 AGENTS 的显式白名单及合成 HOME 启动；来源“完整环境继承”用合成父环境验证，不能借此继承用户真实秘密。[工程规则](../../../AGENTS.md)、[测试门禁](11-test-replay-gates.md)

## 内部可变与外部必须保留

| 对象 | 路线与变化边界 | 依据/关联 |
| --- | --- | --- |
| SQLite物理表、索引、JSON布局、版本 | RuoCun独立格式可变；保留metadata、run、event、tool journal、agent checkpoint的逻辑角色及下文事务。使用独立product标记，不能仅凭`user_version=2`认作RuoCun | `src/session/durable_store.ts:41-99,133-222`；R-11；REC-01..09 |
| 自身会话/runner文件/IPC编码 | 可自有版本化；完整自身恢复、身份、grant/claim、回执、未知结果保护不降级；不兼容旧DAO会话不等于可删这些保证 | `src/tools/managed_shell.ts:40-81,89-167,170-240`；REC-10..12 |
| 导出、审计、缓存 | state/meta/events.jsonl均旁路，不回退为空会话；缓存可重建且不伪报连续命中；用户Markdown导出保持可用 | `src/session/log.ts:94-140`；REC-01/07/14 |
| 配置与扩展文件 | 字段、缺失/null/空串、宽容边界、顺序、大小写、资源根与参数包装是契约；不能用一个通用merge/YAML/dotenv parser替代 | R-12；CFG、EXT；D15来源loader对照 |
| Hooks/MCP/LSP/Deck线协议 | 输入、schema、事件、错误、输出/退出语义属于外部兼容；协议中产品身份可准确改名，协议版本和能力不可凭SDK扩张 | `src/hooks/hooks.ts`、`src/mcp/mcp.ts`、`src/lsp/client.ts`、`src/agent/deck_bridge.ts`；EXT-06..12 |
| 长期记忆Markdown | 用户可编辑的外部数据，保留frontmatter/locked/source/作用域；不能当任意可丢缓存，也不因旧会话范围外就自动读取DAO记忆 | `src/memory/store.ts:42-59,109-159`、`frontmatter.ts:3-57`；MEM-01..03 |

物理 schema 推荐从 RuoCun `storage_version=1` 开始，数据库 `user_version=1`，`meta.identity` 必含 `product="ruocun"`、`format="ruocun-session"`。它沿用来源v2的逻辑模型，**不是DAO v1导入器**。任务07的ADR应明确只初始化真正空数据库（版本0且没有已有表/状态）；只接受本产品已登记版本；DAO v2、未来版本、非空版本0、缺可信checkpoint或损坏均拒绝，不自动转换、覆写或改为JSON恢复。若实施选择其它物理版本，先同步这一唯一契约及ADR，不在并行分支各自发明迁移器。[R-11](../../ruocun/spec.md)、[任务07](../../ruocun/issues/07-store.md)

## SQLite及文件路线

Windows x64 采用D19已验组合的受控官方SQLite 3.54.1 DLL与标准库DB-API。D19验过的解释器是CPython3.11.9 x64，最低Python/最终打包版本由D12决定；更换解释器、架构或绑定需重验实际组合，不能沿用这份ABI结论。不选择未经本项目验证的APSW/pysqlite替代，也不静默落回系统3.45.1。[D19候选与发布交接](../experiments/sqlite-runtime/README.md)

固定供应源为 `sqlite-dll-win-x64-3540100.zip`，DLL SHA-256 `4b59d3cded9dc1608544160f3b4b10ac974c6ac0d6ffc23064e5f4c8dbd05aea`；source ID `2026-10-16 14:45:20 555e07ef33f69a0957d24d8e555b702464a131d6f1607f4c3c1e4551e8e6ca76`。启动在导入`_sqlite3`前按绝对路径/受限搜索加载；每个UI、runner/recovery、内部角色入口都核对实际version/source ID/compile options、DLL及驱动路径/hash与VFS；缺库、hash不符、旧库已加载或实际库不符明确失败。开发、CI、仓库外wheel和独立产物分别留清单。[candidate.json](../experiments/sqlite-runtime/candidate.json)、[D19独立新轮](../../ruocun/integration-evidence/d19-identity-review/README.md)

WAL/FULL、`busy_timeout=3000`、显式`BEGIN IMMEDIATE/COMMIT/ROLLBACK`保留并读回。连接默认线程检查保持；DB线程外不暴露原连接或游标。WAL-reset修复依据来自官方构建/版本（含可审计回移），普通并发成功不是修复证明；本轮不追随官方下载页漂移。备份用SQLite backup或停止写入的一致快照，不能单拷活跃`.db`；升级先备份再事务迁移，未来版本原地拒绝。[D19保存的官方WAL材料](../experiments/sqlite-runtime/sources/wal.html)、`src/session/sqlite.ts:20-38`、`durable_store.ts:48-79`；REC-03/15/16

持久文件走私有父目录→同目录唯一临时文件→完整写入/flush→同卷`os.replace`→平台目录同步与状态记录。Windows用显式DACL/真实ACL读回，不以chmod数字代替；目录RW句柄flush仅有本机API成功证据。已知暂拒才按绝对总预算重试（D18的350ms为起始候选），永久权限拒绝明确失败。错误5本身不能分辨占用/ACL。replace前失败保旧；replace已发生而后续同步失败应报告“发布已可见、持久确认未完成”，不能伪报未执行或盲删候选。ReplaceFileW带backup曾有2/32打开错误，因此不选它作默认路径。[D18](../experiments/durable-io/README.md)、[最终facts](../../ruocun/integration-evidence/d18-accepted-review/facts.json)

权限/同步失败不降级成成功；未完成临时文件不是终态。文件原子可见、进程崩溃后冷读、断电持久性分别记录。私密材料包含能力token、启动清单、日志/附件与SQLite sidecar。拒绝已知网络盘/UNC，不把来源少数statfs magic当Windows网络盘检测；不能确定本地WAL/权限保证时明确拒绝启用耐久恢复。独立账户、断电及其它文件系统仍是产品边界，不能沿用匿名拒绝或一次flush宣称通过。[R-11/R-14](../../ruocun/spec.md)、REC-12、WIN-04

<a id="storage-port-v1"></a>
## StoragePort v1：D08/D09唯一公共持久契约

本节已与D08直接对齐；D08负责scheduler/执行器/角色，D09负责此契约和物理持久化。以下是业务端口及数据约束，不是新产品命令、远程API或测试故障注入接口。方法名为共享语义名，Python编码时用同一声明处导入；不得同时维护第二套类型。来源依据为`durable_store.ts:108-222`、`background_delivery.ts:9-22`、`recovery.ts:6-72`及R-09..11。

| 数据记录 | 最小必须信息及不变量 |
| --- | --- |
| `DbOwner` | `session_id/canonical_cwd/instance_id/owner_epoch`和`ProcessIdentity(host,boot,pid,start)`；每个写事务内校验当前owner，不能只在入队前检查 |
| `RunRef` / `ToolRef` | 前者`task_id/run_id`，后者`scope/tool_call_id`；连同session关联。续跑同task产生新run；不把一个ID复用于全部层 |
| `Intent` | ToolRef、run关联、工具名、最终参数/必要脱敏引用、最终参数digest、审批/策略版本与副作用类别、owner/创建时点；不能把明文凭据持久进journal。若真实执行必须含敏感参数，存安全引用与digest，重启需重新提供秘密，不假装已具可自动重放材料 |
| `ToolRecord` | `started/result_committed/outcome_unknown`、Intent、完整可配对ToolMessage/附件引用、恢复决定引用；重用已提交结果前核对同一操作，ID同而参数变为冲突 |
| `RunRecord` | 执行类别、状态、取消请求、runner/进程身份/launch关联、agent检查点/日志附件引用；kind明确区分shell/agent/fork/monitor/manual，unknown不是已知终态。Monitor不伪装agent；loop配置和已接受tick另存，timer不跨owner补tick |
| `OutboxEvent` | 唯一`event_id`、session、RunRef、事件类型/快照、提交时owner、DB分配单调`seq`、`delivered_revision`；重试同event ID且内容不符报冲突，不能把旧快照再覆盖新run |
| `Checkpoint` | 消息/工具配对、模型/账户引用/模式、标题/目标、scheduler/wait、run视图、agent状态、revision、accepted输入、pending interaction、用量；只存数据，不序列化Task/Future/callback/连接/句柄 |
| accepted输入 | `input_id/seq/payload/attachment_refs/state(queued,consumed,discarded)`；显示“已接受并保存”须在提交后。pause显式清队列写discarded；崩溃不能默默丢已确认输入。未提交草稿可选`last_draft`，无崩溃恢复承诺 |
| pending interaction | kind、持久request ID、ToolRef/最终参数digest/规则版本、问答数据与已知决定；恢复分配新UI ID。不能复用旧callback；历史批准仅作用同一未变操作，不能越过unknown |
| usage/费用 | request/attempt ID去重、累计/分模型桶、provider/model/endpoint身份、预算与价格快照或可审计估价依据；恢复不重计同usage，取消而缺usage保留统计不完整/估计，不伪零，不把source内存费用桶遗漏照抄为预期 |
| agent checkpoint | messages、type/model/worktree、普通/fork/exactTools模式、有效system/prompt/工具/权限/预算必要描述；fork材料不足明确`blocked-recovery`诊断，run仍为interrupted/unknown，不退成普通agent或自动重启 |

| 方法 | 事务/返回契约 |
| --- | --- |
| `open_or_claim(identity)` | 拒活owner/身份不符；死owner接管递增epoch；身份查询错误不当死亡，不同host不自动接管。返回DbOwner和可信恢复视图 |
| `commit_intent(owner, intent)` | 副作用获许可前提交；同ToolRef有已知结果则返回复用结果；已有started/unknown或全会话未决副作用阻挡新副作用，即使模型换tool_call_id。只读核实仍可用；不能靠readOnlyHint扩大安全例外 |
| `commit_result_and_event(owner, tool_ref, result, run_update?, event?)` | 结果、关联run状态与应产生的outbox事件同一DB事务。无意图/冲突关联拒绝；COMMIT确认前不发布成功。并非每个普通工具都虚构后台事件 |
| `commit_run_event(owner, run_update, event?)` | 无工具结果的后台进展使用此口；有event时run+event原子，DB事件成功后才通知/唤醒。started/纯progress可只保存快照，不虚构inbox消息或另造saveRun端口 |
| `commit_checkpoint_ack(owner, expected_revision, checkpoint, consumed_event_ids)` | 消息、background/wait、accepted输入/usage状态、revision和delivered_revision同事务；返回新revision后才内存ack。失败rollback内存prepare/消费，不吞事件；重复请求用同操作ID读回已提交结果 |
| `record_recovery_decision(owner, decision_id, target, decision, explanation)` | 用户决定、对应消息/journal/run变化一起提交，decision ID幂等且内容冲突拒绝；resolve不自动执行旧工具，continue新run仍经dispatcher |
| `load_recovery_view / read_pending_events` | 从同一一致视图按seq读，检查损坏、附件hash/执行身份；不触发副作用；已知结果只补消息，started无可信结果转unknown |
| `close(owner)` | 停止接受新写，收齐已提交请求并关闭本线程连接；只有仍为本owner才释放owner，旧writer不能清掉新owner |

连接由专属单工作线程创建/使用/关闭，事件循环只await有序请求。取消await不能取消已经接受/执行中的事务；调用者必须通过操作ID获知提交结果，不能因为CancelledError推断rollback。事务体不得await网络、进程、审批或调用任意业务callback；可组合的写入在一个显式请求中表达，避免线程内/跨await伪嵌套事务。SQL异常、rollback异常及“提交结果未确认”分开保留；出现DB错误停止后续副作用，不能以结果写失败为理由重执行工具。[D05](../experiments/runtime/README.md)、[D19](../experiments/sqlite-runtime/README.md)

runner文件与session DB是**两个原子域**。runner不直接写session DB；独立runner先flush输出再发布身份完整的terminal receipt。controller验证receipt/run/task、token关联、stdout/stderr/附件后，经`commit_result_and_event`幂等导入。receipt已发布但尚未导入可在恢复重导；DB已导入不能再执行。grant/claim前后仍保留launch证据；没有跨文件/DB的分布式原子性或全局exactly-once承诺。存储错误不能把“可能已grant”降为未执行。`src/tools/managed_shell.ts:89-115,170-240`、`shell_runner.ts:42-63,90-121`；REC-05/06/10/11

<a id="epoch-contract"></a>
## 三类epoch及IPC边界

| 标识 | 所有者/作用 | 迟到或失败处理 |
| --- | --- | --- |
| `owner_epoch` | SQLite会话所有权；接管时递增并在写事务内fence | 旧owner不得写；同epoch不同instance仍拒绝 |
| `stream_generation` | D08每个模型流/当前轮的内存代次，切换/取消淘汰回调 | 旧delta不得改新轮；并不因此删除已合法提交的结果 |
| `control_epoch` | 某runner的控制租约，来自持久接管授权；不是模型流代次 | token/run/控制epoch全部核验；更高控制租约fence旧连接；可信旧终态receipt仍可经恢复幂等导入 |

Windows选择显式私有DACL、拒远端、首实例及有界握手的原生具名管道候选；不用AF_PIPE默认DACL或无界Listener鉴权直接作产品。D08选定将raw OVERLAPPED限定在受监督的**transport helper角色**：原生提交前建立强所有权；未确认完成就poison并保留buffer/event/OVERLAPPED/handle，helper fail-stop由父进程持原handle确认退出。不能让UI或执行权威runner因一条IPC异常直接自杀；runner及其Shell Job独立存活，旧helper和pipe确认终止后才能重开端点。helper没有第二套业务持久schema。[D18最终复核](../../ruocun/integration-evidence/d18-accepted-review/README.md)、D08对齐；[CancelIoEx官方契约](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex)

选择内部长度前缀UTF-8 JSON帧和增量严格解码；帧长先验证再分配。产品请求上限取262144字节，须容纳来源65536个JS UTF-16单位缓冲内的有效JSON（包括换行及分片边界），超长在执行前拒绝；这不是把4096探针阈值当产品阈值。来源`data.toString()`按chunk解码和65536缓冲先验检查的Unicode/多帧瑕疵不复制为正确预期。空帧、半帧、65536单位边界、中文/emoji跨字节分片、多帧、超长声明与资源耗尽须产品实测。内部换编码不改变外部MCP/LSP/Deck协议。`src/tools/shell_runner.ts:137-173`（冻结源定位）；REC-10/12、WIN-04

握手总期限保留来源3秒，重连上限3次；nonce/HMAC、token/run/control_epoch校验及绝对期限由适配层显式实现，期限覆盖连接、认证、读写与取消完成。D18的350ms/1500ms是探针值，不直接设为产品时限；产品清理预算应显式有界并测“未确认”出口。失败重连只接管原run，不能重发start产生第二次副作用。同用户恶意进程仍在信任边界；HMAC不代替ACL，匿名实际拒绝不代替独立账户验收。`src/tools/managed_shell.ts:89-158`；[D18](../experiments/durable-io/README.md)

## 原生路径、兼容source map与写回

原生位置：用户`~/.ruocun/{config,settings,hooks,mcp,lsp,trusted}.json`及skills/commands/agents/plugins/memory/knowledge；项目`<cwd>/.ruocun/`对应扩展/记忆/会话；产品指令为用户`~/.ruocun/RUOCUN.md`及Git根至cwd的`RUOCUN.md/RUOCUN.local.md`。项目链仍遇`.git`文件/目录就停止，无Git只cwd；AGENTS.md/CLAUDE.md不会自动成为产品指令。企业路径为Windows `%ProgramData%/RuoCun/managed-settings.json`、macOS `/Library/Application Support/RuoCun/managed-settings.json`、其它`/etc/ruocun/managed-settings.json`。路径由平台端口解析，测试注入合成根，不通过修改真实HOME测试。[来源路径](03-data-extension.md#32-发现覆盖信任矩阵事实)、`src/project_doc.ts:14-46`

兼容声明只读自原生用户根`compatibility.json`，默认等价`{"version":1,"sources":[]}`。此文件属于RuoCun品牌路径适配格式，不声称DAO认识；程序不从兼容来源递归加载另一个source map，不新增操作员命令。示例仅合成路径：

```json
{
  "version": 1,
  "sources": [
    {"id":"old-profile","scope":"user","resource":"profiles","path":"X:/fixture/.dao/config.json"},
    {"id":"old-user-skills","scope":"user","resource":"skills","path":"X:/fixture/.dao/skills"},
    {"id":"old-project-mcp","scope":"project","workspace":"X:/work","resource":"mcp","path":"X:/work/.dao/mcp.json"},
    {"id":"old-project-doc","scope":"project","workspace":"X:/work","resource":"instructions","path":"X:/work/DAO.md"}
  ]
}
```

| 字段/资源 | 精确规则 |
| --- | --- |
| `version/sources/id` | version必须1；sources有序数组；id非空且唯一；同物理文件同resource/scope去重保留首项，不把不同loader的输入合并。声明错误有路径/字段诊断，不能当空map继续；未知版本拒绝 |
| `path` | 用户明确给出的绝对文件/目录路径；不做`${VAR}`/`~`/glob/URL/可执行表达式展开。解析后显示canonical路径和provenance；只读，不自动复制、移动或写回；symlink解析不扩大扫描范围 |
| `scope/workspace` | user不带workspace；project必须绝对workspace且与当前canonical cwd完全匹配；managed仅接受settings。作用域不是trust；项目permissions/local/hooks仍需本产品信任 |
| 文件类`resource` | `profiles/settings/settings_local/hooks/mcp/lsp/instructions`；settings_local仅project，profiles仅user且最多1条；instructions逐个明确文件路径，不自动扫其父目录或派生DAO.local |
| 目录类`resource` | `skills/commands/agents/plugins/memory/knowledge`，knowledge仅user，memory可user/project；各自只扫描来源支持的层级。声明skills目录不意味着加载相邻hooks/会话/凭据 |
| 禁止资源 | sessions、数据库、runs、receipt、capability、trusted.json、mcp_state、skills-disabled/usage、cache/审计、shadow.git和更新/cleanup状态不接受为兼容源；它们属于RuoCun自己的状态/授权 |
| 错误与来源显示 | 显式声明路径缺失/不可读报该source错误；其它独立源可继续，但该源不能填通过。文件已读后坏JSON/字段的容错仍由该loader决定（下表）。界面/诊断显示source id、原路径、scope、是否生效/被覆盖，绝不显示secret |

兼容源在同一作用域按sources数组顺序，随后原生资源；user与project层级关系仍优先于品牌。相同资源的原生材料在本层最后，**不意味着所有loader都做覆盖**。信任记录从RuoCun`trusted.json`读写，source map不导入旧信任、不因声明路径就执行`trust`。不扩大全局信任gate；MCP/LSP/Skills/agents/commands/指令沿用真实未gate边界并准确呈现，若要扩大另报兼容差异。`DAO_TRUST=1`的显式别名语义可授权当前项目，但不自动装载旧目录。[R-08](../../ruocun/spec.md)、`src/config/trust.ts:5-36`、`src/index.ts:617-657,738-790,948-960,1212-1219`

| loader | 输入顺序及接纳/合并契约 | 写回位置 |
| --- | --- | --- |
| profiles | **整份选择，不合并账户字典**。原生config.json存在即选原生（即使空/损坏也不偷偷换账户）；原生不存在才选唯一显式兼容profiles；再无则空档案。JSON损坏→空档案、新旧迁移/未知顶层字段保持来源。被原生遮蔽的声明明确显示 | 首次修改将已选整份cfg（含未知顶层字段）写入原生config.json，去旧apiKey、保留v2；后续原生优先。原兼容文件零写入；不能无意把两个同名账户混用 |
| permissions/settings | user兼容→user原生→可信project兼容→project原生→可信local兼容→local原生→CLI→managed兼容→managed原生；allow/ask/deny/additionalDirectories去重并集，mode后覆盖；deny>ask>allow，不能靠原生空数组清掉旧deny | Config及始终允许只写原生user/project既定目标，不写旧源；通用Config读取仍按其handler的project??user，不能伪称enterprise统一覆盖 |
| checkpoint/lang | checkpoint只可信project bool>user bool>false；NO_CHECKPOINT最高，保留组合根显式bool使CHECKPOINT不能越过false的实际关系。lang只环境>user settings>locale>en | 各自原生settings，不让local/managed泛化接管 |
| dotenv | 只cwd `.env`；已有process env含空串优先；简化KEY=VALUE/配对引号，无export/变量插值；不引入跨品牌dotenv扫描 | 不写.env |
| MCP/LSP | user兼容→user原生→project兼容→project原生；按server名**整项**覆盖，不递归补command/args/env；坏JSON跳过；不额外信任gate | addServer按来源写首目标语义改为原生user mcp.json；disabled/toggle仅自身mcp_state；失败需诊断，不写兼容源 |
| Hooks | user兼容→user原生→按加载顺序插件hooks→可信project兼容→project原生；逐个附加，全部顺序执行；相同event不覆盖 | 原生hooks.json；不得用name去重删掉合法多个hook |
| Skills | 用户兼容→用户原生→项目兼容→项目原生，同realpath去重、同name后覆盖；插件带namespace单独追加；内置core仅无同名磁盘项时补。动态发现只在显式允许的来源根/原生目录，保留既有缓存/层级顺序 | 安装、禁用、usage/适配cache只写自身根；兼容skills资源路径仍指原目录，不改原正文 |
| commands/agents/plugins | commands/agents先plugin，再user各源，再project各源；按来源name/agentType后覆盖，磁盘agent压bundled。插件两manifest位置、hooks文件优先及namespace保持；多个插件不擅自全局deep merge | 安装/删除只在原生插件/skill根；兼容插件只可停用自身注册，不能删除旧目录 |
| 产品指令 | 用户显式兼容文件→原生用户RUOCUN.md；Git根到cwd每层：该层显式兼容文件顺序→RUOCUN.md→RUOCUN.local.md；按trim内容去重，保留来源标签 | 不写产品指令；显式DAO.md为格式/路径适配，不把AGENTS自动加入 |
| 长期记忆 | 显式目录按scope进入原memory模型；同名/来源记录保留provenance，locked保护不变，不把三个scope深合并 | 新建/修改/删除写原生scope；旧只读记忆若要编辑/删除须先明确导入原生（已有记忆工具呈现只读来源错误），不假装已删除原文；session隔离不能隐式关闭显式记忆加载 |

来源逐项依据：`src/config/profiles_store.ts:5-66`、`profiles.ts:159-210`、`permissions/settings.ts:31-70,95-129`、`index.ts:163-174,617-657,767-845,948-960,1212-1219`、`skills/skills.ts:122-136`、`commands/custom.ts:48-63`、`agent/agent_defs.ts:217-231`、`plugins.ts:9-79`、`project_doc.ts:29-46`；D15只对代表性样本实跑。[研究03完整来源索引](03-data-extension.md)

## 环境别名与凭据范围

逐个真实读取点实现`RUOCUN_<suffix>`优先、同名`DAO_<suffix>`仅fallback；判断键是否存在，空值也阻止fallback，然后按**该变量原谓词**处理，不统一bool解析。DAO_AUTO_APPROVE的`"0"`仍为非空真，DAO_TRUST只`"1"`，USE_KEYCHAIN的`0/off`才关闭。完整需要映射的实际入口沿[研究03环境清单](03-data-extension.md#33-环境变量兼容清单事实与解释边界)，所有已用键逐行fixture；不得仅字符串替换所有DAO前缀、凭`DAO_NO_MEMORY`旧注释增加不存在功能。Windows环境键按OS大小写规则处理，发现大小写碰撞固定原生优先并记录来源。[CFG-05/06](../../ruocun/acceptance-matrix.md)、`src/index.ts:940-942`、`config/trust.ts:33-36`

第三方标准/协议变量保留原名：`CLAUDE_PROJECT_DIR/CLAUDE_PLUGIN_ROOT/AGENT_DECK_HOME/LMNR_*/HTTP(S)_PROXY/locale/TERM`等不机械改名；Hook同时提供DAO_HOOK_EVENT/DAO_TOOL_NAME/DAO_PLUGIN_ROOT及对应RUOCUN别名，值由运行上下文覆盖父环境。AGENT_DECK_HOME是外部发现根，保持其明确路径语义，不变成RuoCun session根。清理、会话、信任、runner路径不从DAO别名推导，所有状态写自身根。MCP显式sc.env键值原样覆盖，不对第三方进程任意合成品牌变量。`src/hooks/hooks.ts:104-130`、`mcp/mcp.ts:149-170`、`agent/deck_bridge.ts:29-38`（冻结源定位）

产品普通Shell/runner沿`safe_env.ts`脱敏继承；**Hook与MCP stdio**保持来源完整父环境再覆盖协议/声明env，manager必须显式传完整受控env，不能用Python SDK默认allow-list。两通道边界真实显示，不声称未信任项目不会启动外部命令；未来收紧需单独差异。开发/验收运行器始终合成allowlist，这是工程约束，与产品继承契约不矛盾。[D15 env反例](../experiments/extensions/README.md)、`src/tools/safe_env.ts:1-10`

凭据的新写服务名`ruocun-api-key`，账户`ruocun/<profile原始名称>`，新keyRef仍用兼容前缀`keychain:ruocun/<profile>`。Windows用已验证的Credential Manager窄端口候选，TargetName以服务名及原账户UTF-8 hex编码，保留Profile/profile区别；不依赖系统TargetName大小写敏感。准确区分stored=system/file、not-found/refused/timeout-unconfirmed；系统写结果不明不伪报已存。端口实现归58/D10，不引入未经验证的keyring自动backend。[D17凭据证据](../experiments/windows/README.md)、[任务58](../../ruocun/issues/58-credentials.md)

`key`内联非空优先`keyRef`，凭据仍经active profile或完整`--api-key+--provider`临时输入；不从OPENAI_API_KEY等自动选账户。显式兼容profiles中的原`keychain:<account>`合法格式可用：按原始account精确**只读**查询旧`dao-api-key`服务（`dao/<profile>`及旧`dao`也不重写），不枚举其它账户、不凭同名尝试其它服务。兼容文件中即使account字面以`ruocun/`开头也仍按其DAO来源解析，不能因碰到新前缀改读另一服务。首次写入原生须保留匹配profile名及精确keyRef的来源标记，例如原生config的额外顶层`_ruocun.credentialOrigins`中记录`{name:{keyRef,service:"dao-api-key"}}`；不含秘密、经原loader未知顶层字段保留。参数/ref改变就不沿用标记，新保存移除旧标记并写新服务；不能仅凭profile同名路由。原生无来源标记时，新`keychain:ruocun/`映射新服务，旧`keychain:dao/`或其它旧account按DAO服务精确只读；手工复制的歧义ref可通过显式兼容source恢复正确provenance。未知非keychain前缀按来源无可用凭据；查不到/平台没有对应本地凭据明确提示重新配置，不能猜新账户或远端迁移秘密。来源Windows本来无系统keychain，不承诺把macOS/Linux系统秘密跨OS自动搬来。这样既保留合法配置读取，又不自动扫描DAO凭据。`src/config/credential.ts:11-45`、`keychain.ts:5-33`（冻结源定位）

用户在既有账户保存流程重新提供/明确迁入key时只写新服务并换成原生ref；删除RuoCun账户不得删除旧服务的secret，即使profile同名。系统不可用/明确失败按原格式文件fallback，写私有原生config并真实显示file；key不进session/trace/示例。兼容config的首次原生写回会保留原内联key是格式语义，须私有ACL/秘密日志门禁，不宣称已经转成系统凭据。任何“只读兼容源”都不能成为对DAO写凭据的授权。[CFG-01/04/09、WIN-05](../../ruocun/acceptance-matrix.md)

## 外部扩展实际子集与适配义务

| 通道 | 实际兼容子集/必须保持 | 不作支持承诺或宣传与实际的区别 |
| --- | --- | --- |
| 工具schema/结果 | 原43定义及动态MCP名/schema原样、required/未知字段/空值/描述/顺序/可见性；MCP `mcp__server__tool`，text拼接、非text JSON化、空`(无输出)`；resource blob只摘要，prompt按role渲染 | 不用Pydantic默认删未知/补default/nullable改写；isError/structuredContent不凭SDK自动变新模型输出；不以capability=read宣称纯函数。R-04、`mcp.ts:70-89,212-280` |
| Skills frontmatter | 简单逐行冒号、字段别名、paths拆分、扁平md/一级SKILL目录、220个JS单位元信息、正文按需/资源根/args | 不是完整YAML；不能把引号/布尔多行映射为新语义。JS UTF16截断和Python码点区别单测。`skills.ts:25-136` |
| commands/agent frontmatter | commands只一级md、字符串参数替换/空白分词；agent保留实际白黑名单、model等字段、嵌套command hook/MCP字符串列表 | 不改成shell shlex；agent接口内联MCP类型不等于文本支持；不同frontmatter parser不合并。`custom.ts:4-63`、`agent_defs.ts:83-201` |
| memory frontmatter | 独立type/status/locked/source模型；保持有效LF输入与serialize，CRLF在Windows补齐并登记差异 | 不把Skills parser拿来共用并悄悄改变接纳；缺失字段与null分开。`memory/frontmatter.ts:3-57` |
| Hook选择/执行 | command实际执行；user→plugin→trusted project顺序；matcher为JS RegExp语义、if用权限rule；UTF8 JSON stdin无附加换行、cwd工作根、timeout毫秒缺省30000、4MiB输出边界 | prompt/Agent/http/callback/function仅声明/部分解析；async字段不代表后台执行。不把Python re当全部JS RegExp等价，48须保留来源合法pattern/错误边界golden，发现不能覆盖的具体语法再报差异。`hooks.ts:53-115,123-143` |
| Hook结果/事件 | code2阻断(reason stderr优先)，其它非0空outcome；0 JSON/text优先级；deny>ask>allow、context顺序拼接、updatedInput后者**整对象**覆盖；PreToolUse `{tool,args:JSON字符串}`并先改参再裁决；Post结果忽略，UserPrompt可拦截，SessionStart只context去重，SessionEnd尽力；子代理start/stop独立 | 非全产品统一payload；未接线事件写在配置里不触发；Post不能回滚副作用；崩溃不保证SessionEnd。超时须确认子树止写或留下unknown，不能复制来源晚副作用后“已停止”的错觉。`hooks.ts:29-48,118-143`、`index.ts:1220-1244` |
| MCP三传输 | 有非空url优先；type=sse旧SSE，否则Streamable HTTP；无url stdio command/args/env；headers原样、tools/resources/prompts/listChanged/elicitation接线、单server失败隔离、disabled/toggle/close | `${VAR}`插值/OAuth配置、分页自动循环、templates/subscriptions/roots/sampling未接线；HTTP GET持续事件/resumption/会话过期等D15未验，不冒称支持全部标准。`mcp.ts:19-43,149-170,286-378` |
| MCP manager适配 | 精确`mcp==1.30.0`；明确stdio完整env、显式HTTP client/headers/timeout、notification到registry重建、断线重新绑定、UI elicitation未绑定decline；客户端品牌`ruocun`及真实包版本 | 一次性来源无handler仍宣告elicitation而回-32601，与主UI不同；产品补为显式decline并登记差异，不能用SDK默认不声明能力偷偷缩小。D15实测不替代产品路径 |
| MCP错误/超时/重试 | 区分确定未发送、明确协议错误/结果、已发送但结果未知；发现/连接可有界重连，**callTool未知不重放**并跨新调用ID阻挡副作用；SDK/HTTP异常归一时保留诊断类别与journal状态；请求deadline明确60000ms，progress不默认重置 | 来源文本正则重试一次是ADR0003已改行为；isError不是传输未发送；readOnlyHint/模型建议不提供重放授权。D15的3/5秒session、4/10秒HTTP仅probe值，不是来源默认。来源锁定TS SDK1.29.0的实际`protocol.js:8,712-714`为60000及resetTimeoutOnProgress=false，Python显式实现该语义 |
| LSP | 小型asyncio Content-Length/JSON-RPC端口，UTF8字节长度、request ID、1-based外部转0-based UTF16、九操作、initialize/initialized/didOpen/didChange和版本、懒启动首扩展名匹配；Windows URI decode/盘符/空格/中文/UNC正确 | 不自动装server；不因用pygls宣称完整标准。选择无响应request缺省30秒、shutdown最多3秒→exit→有界进程收口，取消发$/cancelRequest并忽略迟到响应；这些是R12/S07允许的故障可退出修正，不伪称来源已有。D15只测代表样本，9操作/恶意头/上限/真实server仍由55验证 |
| Deck | 外部协议1、AGENT_DECK_HOME发现、loopback动态port/token、拒Origin、snapshot/messages/command；session/id/签名去重，同id不同签名409；复用同一scheduler/attention，不成第二执行器 | 内部runner重命名不能改掉Deck外部字段/发现文件；不同产品同目录用独立instance/session/文件名，不能接管旧记录；窗口关闭不代表agent退出。`deck_bridge.ts:29-38,64-149` |

本轮补查D15隔离来源依赖缓存：`@modelcontextprotocol/sdk` package.version为1.29.0，其`dist/esm/shared/protocol.js`明确请求缺省60000ms、progress缺省不重置；冻结DAO调用点没有传覆盖值。又核对了[固定tag官方协议源码](https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/v1.29.0/src/shared/protocol.ts)，确认同一默认值。该补查只涉及冻结lock绑定的第三方库，不是引入新DAO基线；本票[校验记录](09-storage-extension-route.validation.json)保存依赖文件hash/行定位。Python1.30通过显式session请求deadline实现60秒，HTTP连接/读取配置不能暗中用probe的较短值截断这个契约；取消/超时后的副作用状态仍按journal处理。

[Python SDK1.30官方发布说明](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v1.30.0)说明其HTTP跨origin重定向默认拒绝；D15没有做对应来源差分，不能把这个候选默认宣布成DAO兼容或直接算成来源故障。任务52需用最小loopback双endpoint固定冻结transport行为和header处理；若必须适配，应在自有HTTP边界完成，并保留未知结果不重放。该项是已选SDK的明确兼容风险，无现成产品证据。MCP与LSP的关闭/超时须有真实helper退出证据，业务未知结果与transport关闭分别处理。Hooks/Skills等JS RegExp/JS UTF16/JSON.stringify差异由来源golden固定；能由源码查明的输入不重问用户，真正无法保持范围的具体冲突才上报。[T-01/T-04](../../ruocun/spec.md)、[D11协议门禁](11-test-replay-gates.md)

## 允许修正、范围冲突与实施交接

| 差异/观察 | 本票目标及分类 | 依据、任务和case |
| --- | --- | --- |
| 来源MCP断线effect=2 | 停止自动重放，未决跨重启与新调用ID保持；已确认INTENTIONAL-DELTA D-01，不再询问用户 | ADR-0003；54；EXT-10/REC-05/08 |
| 费用桶遗漏、输入确认、fork材料不足 | 自身格式补齐；缺材料blocked-recovery，不伪继续/重计费用 | R-09/R-11允许；07/17/28/40/41；REC-07、RUN-07/08 |
| 插件路径逃逸、mtime清理活数据风险 | 拒越扩展根，清理排除活owner、可恢复run、pending event/unknown；SOURCE-CANDIDATE保留，实施差异不是复制危险缺口 | R-08/R-11/R-16；26/36/50；EXT-03/04、REC-14 |
| no-skills/eval动态发现缺口 | 将关闭状态带入动态loader，禁止该关闭通道再注入；不扩展成eval自动关闭Hooks等来源仍开启项 | 规格ENT-05/EXT-02已登记S-03；35/71 |
| LSP缺timeout/shutdown/Windows URI | 采用上表有界关闭及Windows路径修正；静态S-07与D15实际formatter差异分开留证 | R-12；55；EXT-11 |
| Hook超时后仍有晚副作用 | 保留非0输出语义，真实停止/unknown保护补齐；不将“返回空outcome”当已停 | R-10/T-04、D15；48/49；EXT-06/07、REC-05 |
| 跨品牌根、指令名/env/keychain客户端身份 | 本报告精确别名、路径声明与只读旧凭据映射；INTENTIONAL-DELTA工程决定，来源格式不变 | R-12/R-16明确授权本票收口；04/25/26/34..58/81；CFG-01/04..10、EXT |
| IPC编码/helper与DB schema | 独立内部格式/Windows后端；保存原子性、身份、未知结果及source65536/Unicode覆盖 | R-11/R-14/R-16；07/15/17/79/80；REC-01..16、WIN-04、PKG-03 |

以上没有发现必须缩小既定目标的新范围冲突；不扩大全局trust gate，不默认降级Windows沙箱，不迁移DAO会话。尚未实测的独立账户、断电、其他平台、真实第三方服务/模型、完整产品和最终WT均保持未验。R-16中的技术推荐不等于已完成产品验收；物理格式及品牌路径决定由主代理统一写入ADR/规格/矩阵，不在本分支私改。

| 实施组及MM | 必过案例/已有seam | 尚待完成的具体工作 |
| --- | --- | --- |
| 07/10/15/16/17/26/28；MM-591/593/595/597/598/600/601/602/668/704 | REC-01..16、RUN/BG；实际SQLite/进程CLI/runtime | StoragePort、双原子域导入、三epoch、真实角色spawn、取消与故障前后强杀/三次恢复；产品重新跑D05/D19故障族 |
| 04/25/58/69/81；MM-453/455/457/458/460/464/466/468/560/564 | CFG-01/04..10、WIN-05；纯loader+完整启动/真实凭据 | 空map、旧目录并存、显式路径/遮蔽/坏JSON、双品牌环境空值与冲突、旧keyRef精确只读/新写/删除隔离；不读真实秘密 |
| 34..39/48..50；MM-366/450/477/504/562/608/610/612/616/619 | EXT-01..07、ENT-05、MEM；来源loader/Hook helper | 每类parser独立fixture，LF/CRLF/Unicode/未知字段、相同物理路径与命名空间、动态隔离、Hook最终参数及prehook journal、超时后迟到副作用 |
| 51..54；MM-491/496 | EXT-08..10；三传输独立fake server+wire | SDK1.30适配60秒deadline及重定向窄差分、registry重建/开关/elicitation、来源反例与ADR预期、重启/换ID仍阻挡；未接线标准能力不得虚填 |
| 55/56；MM-485/487/489/396 | EXT-11/12；独立LSP/Deck协议fixture | 9操作/帧恶意边界/取消迟到/真实server；Deck认证/Origin/409及同机不同产品发现记录 |
| 79..85；MM-601与NEW-03、PKG/TEST | REC-15/16、TEST-01..07、PKG；install/CI | 每产物真实SQLite与内部角色、仓库外新环境、升级/卸载保留原生及旧DAO、许可/来源/hash；最终WT/HITL集中验收 |

本票不要求新增独立大型前置实验。最小尚缺事项在已有产品票实际seam补齐：source map与keyRef合成树；MCP1.30重定向最小差分与60秒实际路径；JS RegExp差异样本；产品transport helper包装/65536与Unicode；安装产物SQLite库清单。若其中出现无法兼容的具体输入或必要外部条件，再带最小source/port复现报告主代理；不能静默删支持，也不能把未验写成既定失败。

本报告为D08提供的稳定引用是[StoragePort v1](#storage-port-v1)和[三类epoch](#epoch-contract)。D08直接链接，不再复制另一份schema；调度规则、执行器和helper角色的细节以其运行时路线为准。
