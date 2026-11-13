# SQLite、配置与扩展兼容契约研究

日期：2026-11-05。任务：[查清 SQLite、配置与扩展兼容契约](../issues/03-data-extension-research.md)。研究分支：`research/ruocun-compatibility`。

## 1. 结论与证据边界

- **既定范围**：旧 DAO 会话无需迁移；RuoCun 自身的会话保存、恢复必须完整。配置、Skills、Hooks、MCP 等外部扩展格式保持兼容，外部命令按其声明运行；Python 可以替换语言绑定依赖。这些是 `CONTEXT.md` 和 ADR-0001 已确认的约束，不是本报告新增建议。
- **事实**：冻结版本以 SQLite v2 保存权威恢复状态，`state.json`、`meta.json` 和事件日志不能替代数据库。恢复关联包括会话、工作目录、进程启动身份、所有权 epoch、task/run/tool/event ID、附件及 runner 收据，而不只是聊天消息。证据：`src/session/durable_store.ts:41-99,133-221,235-248`；`src/session/log.ts:84-140`；`src/session/recovery.ts:29-72`。
- **建议**：内部数据库表名、JSON 布局、runner IPC 和缓存文件可以重新版本化；先保持事务及恢复不变量，再讨论布局。配置字段、发现及覆盖顺序、工具命名、Hooks stdin/stdout/退出码、MCP 与 LSP 线协议属于外部可观察契约，不能因更换 Python 库而无记录地改变。
- **待决定**：`.ruocun` 与 `.dao` 的读取/写入和冲突规则、`RUOCUN_*` 与 `DAO_*` 的别名优先级、`RUOCUN.md` 与 `DAO.md`、系统凭据服务名、企业配置路径、协议中的品牌元信息。此类问题已经由模块对应表及后续存储扩展决策票预留，**未发现新的范围冲突**。
- **未实测**：本轮只读源码、测试定义和官方资料；没有运行 DAO、来源测试、扩展命令或 SDK，没有安装依赖。下文“测试”均指快照中已有测试资产，不表示本轮通过；最小实验均是后续方案。

唯一源码：快照 `dao-f17e189-7ac654a0dc06`，提交 `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`，源码树 SHA-256 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`。所有 `src/...:行号` / `package-lock.json:行号` 均指该快照已校验只读解包 `D:/java supplement/Firstcode/RuoCun/.worktrees/reference-dao-f17e189-7ac654a0dc06/source/`，包括冻结的本地覆盖层；不指活动 DAO，也不宣称远程当前版本。快照不含用户凭据或运行会话，不能据此提供“真实用户会话数据库 fixture”。参照说明见 [reference/README.md](../reference/README.md)。

## 2. SQLite 与恢复保证

### 2.1 数据模型和事务域（事实）

数据库位于每个会话目录的 `session.db`。驱动口只有 `exec/prepare/run/get/all/close`；Bun 采用 `bun:sqlite`，Node 采用 `better-sqlite3`；读写连接超时 3000 ms，事务包装显式 `BEGIN IMMEDIATE` → 同步 body → `COMMIT`，异常 `ROLLBACK` 并保留原错误。证据：`src/session/sqlite.ts:2-38`；`src/session/durable_store.ts:48-61`。锁文件固定 TS MCP SDK 1.29.0、better-sqlite3 12.11.1、vscode-jsonrpc 9.0.1；这些不是 Python 选型要求：`package-lock.json:1106-1107,3895-3896,9053-9054`。

| 表 | 快照 schema | 权责、关联 |
| --- | --- | --- |
| `meta` | `key TEXT PRIMARY KEY, json TEXT NOT NULL` | `identity`、`owner`、`epoch`、`checkpoint`、`revision`、`background`、`attachments`、`launch:<runId>` |
| `runs` | `id TEXT PRIMARY KEY, json TEXT NOT NULL` | `ExecutionSnapshot`，主键为 `runId` |
| `events` | `seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL, json TEXT NOT NULL, delivered INTEGER` | event ID 去重、单调读取次序、`delivered` 记录被哪次 revision 消费 |
| `tools` | `scope TEXT NOT NULL, id TEXT NOT NULL, json TEXT NOT NULL, PRIMARY KEY(scope,id)` | 同一作用域内工具调用 ID 与意图/结果状态 |
| `agents` | `run_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, json TEXT NOT NULL` | 子代理消息及 metadata，关联 task ID、run ID |

表定义与 `user_version=2`：`src/session/durable_store.ts:37,74-79`；meta 使用：`:80-107,131-187`；工具与代理：`:188-222`。虽然打开 `foreign_keys=ON`，这五表没有 SQL 外键声明；跨表约束由应用逻辑维护，不能把该 PRAGMA 误称为已有外键关系。

打开过程先检查 `user_version`：只接受 0 或 2；拒绝其它版本，设置 `busy_timeout=3000; journal_mode=WAL; synchronous=FULL; foreign_keys=ON`，随后读回验证 WAL 和 synchronous=2。拒绝部分已知网络文件系统 magic 值；会话目录设 0700，数据库设 0600。证据：`src/session/durable_store.ts:48-79,99-104`。这是源码中的检查，不能推定它识别所有 Windows 网络盘，也不能推定 POSIX chmod 等价于 Windows ACL。

所有权事务检查 `sessionId` 与 `realpath(cwd)`，活 owner 存在则拒绝并发恢复，死亡 owner 接管时 epoch 加一，并写随机 `instanceId`。每次 `atomic()` 写入检查当前 instanceId + epoch；同一同步调用栈内的嵌套 atomic 共用事务，没有 savepoint。关闭时清空 owner。证据：`src/session/durable_store.ts:80-129,223-232`。

必须保留的逻辑不变量：

1. `save()` 将消息检查点、background checkpoint、revision 和已消费事件的 delivered 标记一起提交；不能先确认通知、后保存消息。`src/session/durable_store.ts:133-143`。
2. `event()` 在同一事务保存 run 和 event，event ID 重复不重复插入；待消费事件按 seq 返回；写入失败不能向消费者发布成功事件。`src/session/durable_store.ts:152-172`；`src/agent/background_runtime.ts:73-94`。
3. `beforeTool()` 先落意图；已提交结果直接复用，已有未结束记录或未核实副作用会阻止再次执行；执行结果落盘后成为 `result_committed`，恢复时 `started` 变为 `outcome_unknown`。`src/session/durable_store.ts:188-219`。
4. dispatcher 对 capability 不是 `read` 的工具采用副作用保护；PreToolUse 也单独记为 `<toolCallId>:prehook`。因此保护面不只 Bash/Write，不能在 Python 里缩窄成“只有 exec 有风险”。`src/tools/execute.ts:91-99,146-155`。
5. 数据库损坏、未来版本或缺少可信 checkpoint 时抛错，不能静默退到空会话或旧 JSON。`src/session/durable_store.ts:235-252`；`src/session/log.ts:135-140`。

SQLite 官方说明 WAL 要求同机共享，WAL 的 `-wal` / `-shm` 是数据库状态的一部分；FULL 与 NORMAL 的断电持久性不同。因此复制单个活跃 `.db` 文件不能作为可靠备份方案，不能仅为性能把 FULL 改成 NORMAL。此处是设计推论，后续备份应采用数据库备份接口或停机一致快照。[SQLite WAL](https://www.sqlite.org/wal.html)、[SQLite synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous)。

### 2.2 会话检查点、恢复和原子文件（事实）

`PersistedState` 保存 `storageVersion/id/cwd/model/mode/title/taskTitle/messages/usage/updatedAt/done/backgroundWait`；usage 是 prompt/completion/cacheHit/cacheMiss 四项累计值。`BackgroundCheckpoint` 保存 `sessionId/state/wait/runs/events/seq/consumed`。证据：`src/session/log.ts:28-41`；`src/session/durable_store.ts:9-17`。

| 文件/目录 | 真正用途与写入保证 |
| --- | --- |
| `<cwd>/.dao/sessions/<id>/session.db`（及 SQLite sidecar） | 权威恢复数据，上述事务域；会话路径：`src/index.ts:1710-1714,1767-1799` |
| `state.json`、`meta.json` | v2 导出刻意写 `done:true`；state 额外 `formatVersion:2`，让旧二进制不自动续跑活 v2；state 用固定 `.tmp` + rename，无 fsync；meta 直接写，导出失败不影响 durable 成功：`src/session/log.ts:94-111` |
| `events.jsonl` | 追加 `t + ts`，覆盖 user/assistant/tool_result/notice/usage/compaction/checkpoint/turn_end；追加失败吞掉。不能按文件顶部旧注释当作 v2 恢复真相流：`src/session/log.ts:13-26,118-119,145-173` |
| `runs/<runId>/manifest.json`、`runner-state.json`、`grant.json`、`cancel.json`、`terminal.json` | runner 协议状态/收据。durableJson 使用随机同目录临时文件 `wx` 0600 → 写入 → fsync(file) → close → rename → fsync(parent)：`src/session/durable_file.ts:4-28`；创建位置：`src/tools/managed_shell.ts:170-195` |
| `capability`、`start.claim`、`runner.log`、`stdout.log`、`stderr.log` | capability token、排他启动认领、启动诊断、命令输出。capability 是直接写入；start.claim 用 `wx` 并同步文件和目录；终态收据前 fsync stdout/stderr：`src/tools/managed_shell.ts:183-195`；`src/tools/shell_runner.ts:42-63,90-121` |
| `results/<sha256>.txt` | 超过 24000 字符的完整结果：先 durableText，后登记附件哈希；显示截断文本及完整路径。恢复检验缺失/哈希变化并产生未决记录：`src/agent/background_runtime.ts:64-69`；`src/session/durable_store.ts:173-184`；`src/session/recovery.ts:65-70` |
| `cache.jsonl`、`memory-trace.jsonl`、`tool-trace.jsonl`、`perm-trace.jsonl`、`skill-trace.jsonl`、`skills-catalog.json` | 旁路观测。对应写入失败不阻断主流程；tool trace 参数摘要只保留 120 字符。证据：`src/session/cache_audit.ts:52-55,101`；`src/memory/memory_audit.ts:29-34`；`src/tools/tool_audit.ts:15-22`；`src/permissions/perm_audit.ts:23-30`；`src/skills/skill_audit.ts:18-23`；`src/index.ts:1810-1814` |
| `.dao/shadow.git` | 影子 Git 文件检查点，独立于 SQLite 聊天/后台检查点；排除依赖、产物、`.dao`、大二进制等。不是会话数据库备份：`src/session/checkpoint.ts:5-10,21-30,45-78` |

`loadState/loadMeta` 检测有数据库就优先读数据库；`listSessions` 按 updatedAt 降序，可按 canonical cwd 过滤；自动 continue 取同 cwd、done=false、至少一条 user 消息的最近会话；显式 ID 则精确恢复，继续写原会话。`markDone()` 在有等待、未消费事件、running/canceling/unknown/interrupted run 或 paused 状态时保持 done=false。证据：`src/session/log.ts:125-140,178-220`；`src/index.ts:277-284,1772-1798,2170-2185`。

恢复会保留 assistant 和已知 tool result，补齐缺失 pair：可信 journal 没意图为“未执行”，有意图而无结果为“结果未知”；禁止自动重放。runner shell 尝试接管；in-process/legacy 活任务变 interrupted；agent 由保存的 messages 恢复为可显式继续的任务；用户 `/recovery resolve/decide/continue` 的决定也随消息落事务。证据：`src/session/recovery.ts:6-72`；`src/index.ts:1273-1306`。

**完整恢复的静态缺口，需在 RuoCun 自身规格处理，不能照抄丢失**：`Session.modelUsage` 的分模型桶、lastPromptTokens、lastSentLength 与缓存归因指纹是内存字段，PersistedState 只存四项 usage；恢复入口只回填累计 usage，costCNY 却从 modelUsage 估价。`/branch` 还调用非 durable store，仅分支聊天快照，不复制后台执行。证据：`src/session/session.ts:17-31,52-65,91-94`；`src/session/log.ts:28-41`；`src/index.ts:1781-1786,2187-2191`。建议将“完整”定义为哪些统计/任务需连续，保持 `branch` 不重复启动副作用，另列自动回归；本报告未判定这些缺口的运行影响大小。

### 2.3 持久执行身份和 runner 协议（事实）

- 进程身份是 `{host,boot,pid,start}`，不是 PID 单值。Linux 用 boot_id + `/proc/<pid>/stat`，macOS 用 kern.boottime + ps lstart，Windows 本地覆盖层用 PowerShell CIM 的 LastBootUpTime/CreationDate UTC ticks；PID 必须是正 32 位整数，查不到进程可为 null，权限/查询错误继续抛出。不同 host 拒绝自动接管，不同 boot 视为死亡，start 不同防 PID 重用。`src/session/process_identity.ts:4-74`。
- 执行身份区分 `taskId`（用户可见任务）、`runId`（某次执行）、sessionId、eventId、seq；wait target 固定 taskId+runId，防任务继续后错误唤醒旧等待。状态有 running/canceling/completed/failed/canceled/interrupted/unknown；wait 模式 any/all。`src/agent/background_types.ts:1-40`。
- ManagedShell 启动前保存 run 与 `launch:<runId>.tool={scope,id}`，写 manifest/token，启动独立 runner，再以 token + runId + epoch 握手；grant 写入后才要求 start；runner 用排他 `start.claim` 防重复，先持久 started 才 spawn。`src/tools/managed_shell.ts:69-115,170-219`；`src/tools/shell_runner.ts:90-121,147-168`。这是“不盲目重放”的协议，不是对任意外部副作用的全局 exactly-once 承诺。
- 恢复首先验证 terminal.json 的 run/task 身份与终态，要求 stdout/stderr 存在；否则验证 manifest session/run、runner 活身份再连接。3 秒握手超时，失联最多重连 3 次，随后 unknown；不能连不上就再启动命令。grant 前可证明未执行的失败会记为 failed，grant 可能发出则保守 unknown。`src/tools/managed_shell.ts:40-81,89-158,222-240`。
- 取消先持久 canceling 与 cancel.json，runner 在真实 close 后写 canceled；只发取消信号不等于已经取消。runner 接受更高 epoch 会断开旧客户；拒绝旧 epoch/token/runId。`src/tools/managed_shell.ts:160-167`；`src/tools/shell_runner.ts:42-62,74-88,147-168`。
- **Windows 补齐点（静态）**：endpoint 为临时目录 `.sock` 路径并校验 Unix 104 字节限制；取消用负 PID 的 SIGTERM；durable 文件同步父目录也直接按 POSIX 打开。已补 Windows process identity 不代表 runner 全链路已可用。需要 Python 平台适配及实验，属于既定 Windows 补齐范围。`src/tools/managed_shell.ts:17-29`；`src/tools/shell_runner.ts:81-85,100-105`；`src/session/durable_file.ts:21-27`。

## 3. 配置、凭据、环境和指令发现

### 3.1 账户与凭据（事实）

账户格式是 `~/.dao/config.json`：`{version:2,onboardingComplete?,activeProfile,profiles:{<name>:{provider,baseUrl,model,key?,keyRef?}}}`。provider 为 deepseek/anthropic/openai/volcengine/qianfan/zhipu；具体模型/端点默认值是快照数据，不在本研究更新为供应商当前值。`src/config/profiles.ts:5-30`；路径：`src/index.ts:361`。

- `loadProfiles()` 缺失/JSON 损坏回空档案；旧 `{apiKey,baseUrl?,model?}` 转为 default/deepseek v2，内存迁移不立即回写；只以 `version===2` 识别 v2，不做完整 schema 校验。Python 严格模型校验若直接替代，会改变接纳边界，需用 fixture 确认。`src/config/profiles_store.ts:5-12`；`src/config/profiles.ts:159-185`。
- 保存保留其它顶层字段，去旧 apiKey，再更新 version/onboardingComplete/activeProfile/profiles，建目录、直接 writeFile、尽力 chmod 0600。不是原子写；新增同名账户拒绝，新账户自动激活；删除当前账户转剩余首项或 default。`src/config/profiles_store.ts:15-66`。
- 有效临时凭据是同时提供有效 `--api-key` + `--provider` 时优先；该路径的 `--model` 覆盖 provider 默认；否则解析 active profile。仅有一个参数不能视为完整临时覆盖。`src/index.ts:330-343,406-423`。该片段没有为“只有 profile + --model”应用启动覆盖，不能仅按 flag 名推定生效。
- profile 内联 key 优先；没有 key 且 keyRef 以 `keychain:` 开头才经端口查系统凭据。没有凭据返回 null。不会从 DEEPSEEK_API_KEY/ARK_API_KEY/OPENAI_API_KEY 等变量自动选账户。`src/config/credential.ts:15-30`；`src/config/profiles.ts:196-210`。`ResolvedCredential.source` 的旧注释提到 env 不能当真实支持。
- 保存 key 优先系统凭据，成功只留 `keychain:dao/<profile>`，失败/不优先则明文文件兜底。服务名 `dao-api-key`、旧默认账户 `dao`；macOS security/Linux secret-tool，8 秒超时，`DAO_USE_KEYCHAIN=0/off` 禁用；Windows 此快照不支持系统凭据。`src/config/credential.ts:11-13,33-45`；`src/config/keychain.ts:5-71`。

### 3.2 发现、覆盖、信任矩阵（事实）

这里不存在一个统一“项目配置覆盖用户配置”的算法。

| 通道 | 输入与顺序 | 合并及信任 |
| --- | --- | --- |
| 环境 | 启动 cwd 的 `.env`，不是父目录链 | 已有 process env（包括空字符串）优先；只补不存在键。简单 KEY=VALUE、去两端配对引号；不实现变量展开/export/完整 dotenv 文法：`src/index.ts:197-203`；`src/config/env_file.ts:3-44` |
| profiles | `~/.dao/config.json` | 用户级单文件；不是 project settings 中的账户。见上节 |
| permissions | user settings → project settings → project settings.local → CLI → enterprise managed-settings | allow/ask/deny/additionalDirectories 跨层去重并集，defaultMode 后层覆盖，deny>ask>allow 独立于层；project/local 仅 trust 后加载。autoMode allow/deny/environment 也并集，旧 bashClassifier 映射 autoMode.deny：`src/index.ts:948-960`；`src/permissions/settings.ts:31-63,95-129` |
| enterprise | macOS `/Library/Application Support/DaoCode/managed-settings.json`；Windows `C:/ProgramData/DaoCode/managed-settings.json`；其它 `/etc/dao/managed-settings.json` | “最高层”主要指 defaultMode 后覆盖及规则并集，并非任意字段可删除下层规则：`src/permissions/settings.ts:66-70`；`src/index.ts:956-960` |
| checkpoint.enabled | user settings、可信 project settings | project 明确 bool > user bool > false；**不读 local/CLI/enterprise 的此字段**。`createCheckpointer` 的真实顺序是非空 DAO_NO_CHECKPOINT 关 > 显式 options.enabled > DAO_CHECKPOINT 真值 > false；index 总传 bool，因此该调用点 DAO_CHECKPOINT 不会覆盖显式 false，与旁边“环境优先”的注释不一致：`src/index.ts:163-174,1816-1822`；`src/session/checkpoint.ts:33-42` |
| UI lang | user settings.lang、DAO_LANG、系统 locale | DAO_LANG > 用户 settings.lang > LC_ALL/LC_MESSAGES/LANG > en；project/local 不参与：`src/i18n/i18n.ts:12-27,50-68` |
| MCP | `~/.dao/mcp.json` → `<cwd>/.dao/mcp.json` | mcpServers 以 server 名整项后覆盖，缺失/坏 JSON 跳过；无 trustProject gate：`src/index.ts:617-630`；`src/mcp/mcp.ts:33-43` |
| LSP | `~/.dao/lsp.json` → `<cwd>/.dao/lsp.json` | servers 按 server 名整项后覆盖；无 trustProject gate：`src/index.ts:650-657`；`src/lsp/config.ts:20-30` |
| Hooks | user hooks.json → plugins 的 hooks 文件 → 可信 project hooks.json | 逐个附加，全部选中后顺序执行；不按 event 覆盖，也不从 settings.hooks 加载：`src/index.ts:1212-1219`；`src/hooks/hooks.ts:54-84,123-143` |
| Skills | 用户 skills → 项目 skills；插件单独加载追加；内置 core 无同名磁盘条目时加入 | 用户/项目同物理文件 realpath 去重、同 name 后覆盖；插件保留 namespace，未与本地数组再做统一同名覆盖；无 trustProject gate。`src/skills/skills.ts:122-136`；`src/index.ts:767-790` |
| agents / commands | plugin → user → project；agent 磁盘定义覆盖同名 bundled | 按 name/agentType 后覆盖；无 trustProject gate：`src/agent/agent_defs.ts:217-231`；`src/commands/custom.ts:48-55`；`src/index.ts:738-758` |
| 产品指令 | 用户 DAO.md → git 根到 cwd 的每级 DAO.md、DAO.local.md | 内容 trim 后去重，后项更具体；只认 DAO 文件名，不回退 AGENTS.md/CLAUDE.md；无 trustProject gate。`src/project_doc.ts:5-46` |

信任文件是 `~/.dao/trusted.json` 的 root 字符串数组；检测 `.dao/settings.json/settings.local.json/hooks.json` 才要求信任，`DAO_TRUST=1` 可显式绕过；源码按传入 root 原字符串 includes，无 realpath 归一。证据：`src/config/trust.ts:5-36`。这不能被解释为“未信任仓库不自动启动外部命令”：项目 MCP 会在启动连接，LSP 在调用时启动。建议后续决策明确是否扩大信任边界；若扩大，属于已登记兼容行为差异，不由 Python 实现擅自决定。

权限字符串本身也是配置契约：`Tool` / `Tool(specifier)`；Bash 支持精确、词边界 `prefix:*`、glob，路径工具使用简化 `* / ** / ?` 与 basename 规则，WebFetch 支持 domain 及子域，工具名匹配区分大小写。主权限 Bash 路径还有 AST/安全预处理和 too-complex→ask，不能用一个通用 fnmatch 替代。Hook 的 if 只走 `parseRule + ruleMatches`，并不执行完整 Bash AST 裁决。`src/permissions/rules.ts:32-112,235-287`；`src/permissions/engine.ts:142-147`。具体 AST/平台补齐与运行时研究交叉验收。

产品指令向上遇见 `.git` 存在就停，兼容 `.git` 文件；一直没找到则只读 cwd，不扫无关父目录；用户级始终先读。根目录 AGENTS.md 是工程代理规则，不因此自动成为产品规则。`src/project_doc.ts:14-46`。`src/index.ts:884` 的旧注释写了 AGENTS/CLAUDE，而实际 loader 和 `src/project_doc.test.ts:15-28` 明确不读取，报告以实现为准。

DAO 自己会把 home/cwd 的旧 `.codeds` 整体 rename 为 `.dao`，仅当新目录不存在。`src/config/migrate_dirs.ts:5-13`；`src/index.ts:355-361`。**建议 RuoCun 不照抄跨品牌自动 rename**：这会移动 DAO 配置及会话，不能由“格式兼容”推得“接管旧数据”；读取旧配置别名和旧会话迁移是两个不同契约。

### 3.3 环境变量兼容清单（事实与解释边界）

必须保留实际读值的语义，不能把所有开关统一成 Python 的 `bool(str)`，也不能把缺省/空值/`0` 混成一类。例如 DAO_AUTO_APPROVE 是字符串存在且非空就开启，`"0"` 也为真；DAO_TRUST 则严格 `=="1"`。证据：`src/index.ts:940-942`；`src/config/trust.ts:33-36`。

| 领域 | 需纳入 alias/fixture 的当前实际环境入口 | 来源 |
| --- | --- | --- |
| 扩展与安全 | DAO_TRUST；DAO_USE_KEYCHAIN；DAO_SANDBOX、DAO_SANDBOX_NO_NET；DAO_AUTO_APPROVE；Hook 输出 DAO_HOOK_EVENT、DAO_TOOL_NAME、DAO_PLUGIN_ROOT、CLAUDE_PROJECT_DIR、CLAUDE_PLUGIN_ROOT | `src/config/trust.ts:34`；`src/config/keychain.ts:18-19`；`src/tools/sandbox.ts:7-12`；`src/index.ts:942`；`src/hooks/hooks.ts:107-130` |
| 审计 | DAO_AUDIT；DAO_MEMORY_AUDIT、DAO_TOOL_AUDIT、DAO_PERM_AUDIT、DAO_CACHE_AUDIT、DAO_SKILL_AUDIT（单流 0/1 优先总开关） | `src/session/audit_switch.ts:1-9`；老 audit.log 直接看总开关：`src/permissions/audit.ts:14-18` |
| 恢复/清理/文件检查点 | DAO_NO_CHECKPOINT、DAO_CHECKPOINT、DAO_CHECKPOINT_TIMEOUT_MS、DAO_CHECKPOINT_MAX_MS；DAO_NO_CLEANUP、DAO_CLEANUP_DAYS | `src/session/checkpoint.ts:33-42,59,85`；`src/agent/cleanup.ts:66-73` |
| 模型/上下文/费用 | DAO_REASONING_EFFORT、DAO_MAX_OUTPUT_TOKENS、DAO_STREAM_IDLE_MS、DAO_MAX_CONTINUE、DAO_CONTEXT_WINDOW、DAO_MAX_BUDGET、DAO_MAX_BUDGET_HARD、DAO_CLASSIFIER_MODEL、DAO_FETCH_EXTRACT_MODEL、DAO_EXPLORE_MODEL、DAO_SUMMARY_MODEL、DAO_CONSOLIDATE_MODEL；DAO_PRICE_INPUT_HIT/MISS/OUTPUT 和 DAO_PRICE_FLASH_INPUT_HIT/MISS/OUTPUT | `src/agent/loop.ts:259`；`src/client/client.ts:104,127,390`；`src/index.ts:990,1062,1078,1432-1434,1471,689`；`src/agent/loop.ts:423`；`src/agent/bundled_agents.ts:35`；`src/session/cost.ts:55-71` |
| 调度与自恢复参数 | DAO_MAX_TURNS、DAO_SUBAGENT_MAX_TURNS、DAO_MAX_PARALLEL_AGENTS、DAO_ADVISE_GAPS、DAO_EMPTY_MAX_RETRIES、DAO_EMPTY_RETRY_MAX_TOKENS、DAO_RATE_LIMIT_MAX_RETRIES、DAO_RATE_LIMIT_WAIT_MS、DAO_HARD_RETRY_DELAY_MS、DAO_FAIL_STREAK、DAO_REPEAT_ERR、DAO_REFOCUS_EVERY | `src/agent/loop.ts:194-200,231,264,361,404,502`；`src/agent/turn_budget.ts:5`；`src/tools/agent.ts:401`；`src/agent/turn_health.ts:27-30` |
| 记忆/反思/代码图 | DAO_REFLECT、DAO_REFLECT_EVERY、DAO_REFLECT_MAX_INTERVAL、DAO_REFLECT_SYNC、DAO_DISTILL_FORK、DAO_COMPACT_COOLDOWN_MS、DAO_PROVISIONAL_DAYS、DAO_REPO_MAP_TOKENS、DAO_DEBUG_MEMORY、DAO_DEBUG_REFLECT | `src/index.ts:1500,1598-1606,1649,1682`；`src/memory/gc.ts:37`；`src/repomap/index.ts:25`；`src/memory/distill.ts:82` |
| 界面、平台、运维 | DAO_LANG、DAO_THEME、DAO_NO_NOTIFY、DAO_NOTIFY_MIN_MS、DAO_NO_WAKELOCK、DAO_DEBUG_TUI、DAO_MASCOT_DIAGNOSTICS、DAO_OWNED_TERMINAL、DAO_NO_UPDATE_CHECK、DAO_UPDATE_URL | `src/i18n/i18n.ts:21-26`；`src/tui/background.ts:11-13`；`src/tui/notifier.ts:30-31`；`src/index.ts:1525`；`src/tui/wakelock.ts:6`；`src/tui/app/App.tsx:361,1373`；`src/tui/app/run.tsx:18,47`；`src/config/update_check.ts:33-40` |
| 外部协议与观测 | DAO_DECK、DAO_DECK_MANAGED、AGENT_DECK_HOME；LMNR_PROJECT_API_KEY/BASE_URL/GRPC_PORT/HTTP_PORT、DAO_OBS_CACHE_LOW_FLOOR/RATE | `src/agent/deck_bridge.ts:29-38`；`src/obs/init.ts:11-16,45`；`src/obs/attrs.ts:40-41` |

标准环境另有 HOME/TMPDIR/PATH、locale、代理大小写变体、TERM/COLORTERM/COLUMNS/NO_COLOR/FORCE_COLOR/COLORFGBG/TERM_PROGRAM/INK_SCREEN_READER 等，平台选型票需继续保留。具体入口：`src/agent/agent_memory.ts:20,50,70`；`src/tools/managed_shell.ts:17-29,195`；`src/env_snapshot.ts:82-87`；`src/tui/capabilities.ts:17-22`；`src/tui/background.ts:11-13,84`；`src/tui/app/run.tsx:27`。Windows HOME 缺失和大小写映射要单独 fixture，不能直接沿用 POSIX 假设。

**不要误登记为可用环境开关**：本快照 `DAO_NO_MEMORY` 出现在旧注释，而实际隔离走 `--no-memory/--eval`（`src/index.ts:318,718`）；`DAO_VERBS` 是词库常量（`src/tui/spinner_words.ts:3-27`）。配置发现必须以读取点为据。

环境继承分通道：普通 shell/runner 使用 `scrubbedEnv()`，删除匹配 API_KEY/SECRET/TOKEN/PASSWORD/CREDENTIAL/供应商名等的键；Hooks 和 MCP stdio 则继承完整 process env，再覆盖自己的协议 env/配置 env。`src/tools/safe_env.ts:1-10`；`src/tools/shell_runner.ts:114-121`；`src/hooks/hooks.ts:106-114`；`src/mcp/mcp.ts:155-159`。换 SDK 的默认 allow-list 或给所有通道统一脱敏都会改变扩展可用性，必须显式实现及记录，不可假设现有代码已统一隔离。

## 4. Skills、插件、自定义命令与子代理定义

### 4.1 Skills（事实）

- 输入为 `<root>/<slug>.md` 或 `<root>/<slug>/SKILL.md`，不递归扫描任意层级。frontmatter 使用简单逐行冒号解析，不是完整 YAML；无 frontmatter 也可加载非空正文。字段有 name、description、when_to_use / when to use / whentouse、paths、disable-model-invocation（及下划线别名）、user-invocable（及下划线别名）。paths 支持逗号/空格/方括号/去引号；名称/描述值不会通用 YAML 解码。`src/skills/skills.ts:25-67,79-103`。
- modelInvokable=false 不进模型目录；userInvocable=false 不进手动 slash 入口；默认均开。目录只给元信息，description+whenToUse 截到 220 个 JS 字符；正文用 Skill 按需取，返回资源根目录及用户 args。模型查找 namespace:slug → 精确 name → 忽略大小写 name → slug；用户查找是允许手动的列表中首个 slug/name/namespace 匹配。`src/skills/skills.ts:70-76,106-119`；`src/tools/skill.ts:23-54`。
- 插件 namespace 用 manifest name；裸 slug 仍可能与本地或另插件重名，不能从“有 namespace”推定裸调用唯一。用户/项目 `loadSkills` 用 name 大小写敏感去重，调用却多用 lower-case；插件独立追加而非全局统一去重。`src/skills/skills.ts:122-136`；`src/index.ts:769-790`；`src/tools/skill.ts:29-36`。
- 禁用名单为用户级 `skills-disabled.json` 的 name 数组，内置/磁盘同名共用该键；`skill-usage.json` 记录 count/lastUsedAt，影响发现排序；`skill-adapted/<hash>.md` 缓存外来正文转换。`src/index.ts:779-817`；`src/skills/usage.ts:6-9,21-35,38-46`；`src/skills/convert.ts:42-58`。
- 条件 paths 启动最多预扫描 4000 文件；已匹配进常驻目录，未匹配进待激活池；文件操作后激活，追加尾部 system 消息，不改固定前缀。动态发现文件路径向上到 cwd（不含 cwd），子目录 `.dao/skills`，跳过路径包含 node_modules；存在目录正缓存，缺失不负缓存。`src/index.ts:819-845,1167-1189`；`src/skills/discover.ts:14-62,71-110`。代码注释说 deepest first 优先，但 `loadSkills(...dirs)` 后者覆盖：同时发现深浅目录同名时，实际结果需 golden 固定，不能只照注释。
- 安装接受本地路径或 http(s)/git@ clone，优先仓库 skills 子目录，递归找 SKILL.md；每个技能目录内容整体复制，安装要求正文 trimStart 后以 `---` 开始；安装路径决定 user/project。运行时 SkillInstall 可把新无 paths 技能加入当前会话；CLI 安装提示重启。`src/skills/install.ts:10-71`；`src/index.ts:1155-1165`。
- 外来技能识别与适配不是可执行 JS 插件：匹配工具/跨技能引用，辅助模型按用途改写正文，缓存键含 `inherit-model-v2 + catalog + body`，失败退原文+通用提示，源文件不改。不要用单一生成输出做稳定 golden；应注入固定 callFlash 覆盖命中/失败路径。`src/skills/adapt.ts:1-16`；`src/skills/convert.ts:6-16,42-58`；`src/tools/skill.ts:41-45`。

### 4.2 插件、命令、agent 文本定义（事实）

插件是 `~/.dao/plugins/<dir>` 的目录组件：优先根 `plugin.json`，否则 `.claude-plugin/plugin.json`，读取 name/description；skills、commands、agents、hooks 各自复用原加载器。hooks 优先根 `hooks.json`，其次 `hooks/hooks.json`，`CLAUDE_PLUGIN_ROOT/DAO_PLUGIN_ROOT` 指插件根，不能指 hooks 子目录。此插件机制不是运行 TypeScript 模块的 ABI，无需为了“插件兼容”把核心保留为 Node。`src/plugins.ts:9-79`。

安装插件本地复制或浅 clone；manifest 要有 name，按 manifest.name 覆盖目标目录，安装/删除提示重启。源码对 manifest.name 和 remove 名直接 path.join 后 rm，无路径边界校验；**不要将不受约束删除路径视为必须复现的兼容特性**，后续实现须约束在插件根并记录错误行为差异。`src/plugins.ts:82-132`。本轮没有执行安装或删除。

自定义 slash 命令只读 commands 的第一层 `.md`，正文为 prompt 模板，可有 description frontmatter；`$ARGUMENTS` 替换全部 trim 后参数，随后 `$1/$2/...` 以空白切词替换，缺参为空，**没有 shell 引号解析/执行**。plugin<user<project 覆盖。`src/commands/custom.ts:4-63`。TTY 入口先有大量专用操作分支，然后 runBuiltinCommand，再 custom command，再 restore，再可手动 Skill（保留 model/clear/compact/cost/help/exit），最后通用 dispatcher；因此并非统一“全部内置高于 custom”，而且 slash 入口会先按空白分词再 join，原参数空白已折叠。手动 Skill 返回原 body，不走 Skill 工具的适配、资源目录和 args 包装。`src/index.ts:1917-1930,2448-2471,2501`。需用入口集成 fixture 固定冲突与不同交互入口，不能只测 expandCommand。

agent 文本定义是另一外部格式：`.dao/agents/*.md` 及插件 agents；name 与非空 body 必须存在；支持 tools/allowed-tools（逗号、`*`、`!exclude`）、disallowedTools、model/inherit、permissionMode、maxTurns、effort、skills、memory、background、isolation/worktree/remote、color、omitClaudeMd、initialPrompt、criticalSystemReminder。嵌套 hooks 只解析 SubagentStart/Stop 的 command，MCP 文本段只解析字符串引用列表；接口中的内联 MCP 类型不等于文本 parser 完整支持。plugin<user<project，同名磁盘定义压 bundled。`src/agent/agent_defs.ts:10-57,83-201,217-231`；`src/index.ts:741-751`。Python 完整 YAML parser 可能接纳更多输入，应明确宽容扩展而非宣称逐字等价。

`--no-skills` 在启动加载阶段同时关磁盘/插件 Skills、自定义 agents/custom commands、内置 Skills；`--eval` 只隐含前述磁盘隔离并关 memory/MCP/项目指令/web，仍保留内置 Skills 和 Hooks；只有 `--no-hooks` 关闭 hooks。`src/index.ts:293-328`。**静态隔离缺口**：后面的 ctx.onFileAccessed 动态发现没有 noSkills gate，Read/Edit/Write 会无条件调用该回调，因此“评测全程禁止磁盘 Skill 注入”不能仅由启动 flag 推定。`src/index.ts:1167-1189`；`src/tools/read_file.ts:130`；`src/tools/edit_file.ts:84`；`src/tools/write_file.ts:79`。建议将预期隔离与这一路实现差异纳入 fixture/决策，不把缺口默认为必须复现。

### 4.3 其它持久文本（事实）

记忆分 cwd `.dao/memory`、用户 `.dao/memory`、用户 `.dao/knowledge`，现有 legacy memories.json 会转 Markdown；单条 `name.md` 带 type/status 等 frontmatter，用户可编辑、可 locked，不适合只当无外部意义的缓存。`src/index.ts:670-682`；`src/memory/store.ts:42-59,109-159`。解析器正则目前只接受 LF，字段按简单 key/value，serialize 输出 LF；CRLF 是 Windows fixture 必须覆盖的现状差异。`src/memory/frontmatter.ts:3-40,44-57`。不迁移 DAO 会话并不自动决定“是否读取旧 DAO 记忆目录”；由命名/目录别名决策明确，避免误扩范围。

## 5. Hooks 运行契约

### 5.1 配置、选择和执行（事实）

格式接受 `{hooks:{<event>:[group]}}` 或裸 `{<event>:[group]}`；group 可带 matcher/if，内部 hooks 数组或把 group 本身作 hook；type 缺省 command；inner if 覆盖 group if；timeout 为数值原样传入毫秒。缺失/坏 JSON 文件跳过。`src/hooks/hooks.ts:53-84`。

`HookType` 声明 command/prompt/Agent/http/callback/function，但 `runHooks` 只执行有 command 的 command 类型；url/prompt/async 仅解析，async 没有调度行为，callbackId 也没有从文件加载。它不是完整 Claude Code Hook 实现。`src/hooks/hooks.ts:5-18,69-79,122-131`。

matcher 是 JS RegExp，工具事件匹配 toolName，SessionStart 匹配 source；其它事件带 matcher 且无 toolName/source 会不匹配。if 仅在有 toolName 时调用权限 `matchesIfClause`，不是任意表达式。错误正则没有 catch，会抛；不能把所有配置错误都说成“静默跳过”。`src/hooks/hooks.ts:87-101`。

命令经 shell exec，cwd=workspaceRoot；stdin 为单个 JSON 文本（不自动加换行），无 payload 时 `{}`；默认 timeout 30000 ms，maxBuffer=4 MiB；继承 process env 并覆盖事件/插件变量。非数值执行错误折为 code=1。顺序 await 每个 hook，无并发与 async fire-and-forget。`src/hooks/hooks.ts:104-115,123-143`。

### 5.2 事件 payload 与结果使用（事实）

| 实际事件 | stdin | 结果使用与特别说明 |
| --- | --- | --- |
| PreToolUse | `{tool:<name>,args:<JSON字符串>}` | block/permissionDecision/updatedInput/additionalContext 返回 dispatcher；不是 tool_input 对象。`src/index.ts:1220-1222` |
| PostToolUse | `{tool,args:<最终JSON字符串>,result:<工具文本>}` | 仅执行副作用，runHooks 返回 outcome 被丢弃；阻断不能撤销已完成工具。`src/index.ts:1224-1225`；`src/tools/execute.ts:69-73` |
| UserPromptSubmit | `{prompt:<text>}` | block 拒本次提交，否则 additionalContext 注入。`src/index.ts:1240-1244,2639-2645` |
| SessionStart | `{}`，source 仅供 matcher 选 startup/resume | 使用 additionalContext；不检查 block。每次启动以 `[[dao:session-start-hook]]` 哨兵去旧注入再插入 system 后，防 continue 累积；source 判定用 continueFlag，不能推定所有 `/resume` 切换都会重发。`src/index.ts:1227-1238,2170-2178` |
| SessionEnd | `{}` | headless/TTY/REPL 均有调用点，返回 outcome 丢弃；不据此保证崩溃/所有提前退出都会发事件。`src/index.ts:1742,2579,2675` |
| 子代理 frontmatter SubagentStart / SubagentStop | `{hook_event_name,agent_id,agent_type}` | 独立注册表，不是全局 hooks.json 的统一生命周期传播。Start additionalContext 注入，Stop 收尾忽略失败；转换的 HookSpec 只有 command，无自定义 timeout/async。`src/agent/agent_hooks.ts:18-35,46-100`；`src/agent/runAgent.ts:338-341,502-503` |

未提供完整的 session_id/transcript_path/permission_mode 等统一输入包，不能因为部分字段兼容就宣称支持所有第三方 Hook。通知、PreCompact 等事件也不能仅通过在配置写名字获得触发；全局实际 runHooks 入口见以上行号。

退出码和 stdout 规则：code=2 阻断，reason 优先 stderr 再 stdout；其它非零（含普通超时）忽略输出；code=0 空 stdout 无效果；有效 JSON 支持 `hookSpecificOutput.additionalContext` → 顶层 additionalContext → additional_context，permissionDecision 仅取 hookSpecificOutput 的 allow/ask/deny，updatedInput 可取 nested 或顶层；有效但无已识别字段的 JSON 不变成文本。无效 JSON 的非空 stdout 作为 additionalContext。多个 hook block OR、reason/context 按顺序换行拼接、permission deny>ask>allow、updatedInput 后者覆盖。`src/hooks/hooks.ts:29-48,118-143`。

PreToolUse 改写的 updatedInput 是整个最终参数对象，不是局部 patch；先改写再做权限判断、敏感检测、执行、审计和 PostToolUse，避免旧参审批新参执行。hook deny/block 不可放行，ask 强制人工，allow 不能覆盖规则 deny，只能把非敏感/非危险 ask 降为 allow。`src/tools/execute.ts:44-47,140-184`。此顺序必须跨语言 golden，包含 prehook 只执行一次及 durable 结果复用。

## 6. MCP 兼容面

### 6.1 配置和传输（事实）

输入 `{mcpServers:{<server>:{command?,args?,env?,type?:stdio|http|sse,url?,headers?}}}`。有非空 url 就走远程，`type==sse` 用 SSE，其他 type（包括 stdio+url）均用 Streamable HTTP；没有 url 就走 stdio，缺 command 变空字符串。env 显式覆盖继承 env；HTTP headers 原样给 transport；没有在应用层实现 `${VAR}` 展开或 OAuth 配置字段。`src/mcp/mcp.ts:19-43,149-170`。不要把 Python SDK 支持的额外字段自动算作现有格式。

客户端身份为 name=`dao-code`, version=`0.1.1`，不是 package 0.5.15；声明 elicitation 能力。有 handler 时将 message/requestedSchema 交给 UI，返回 accept/decline/cancel 和可选 content；组合根 UI 未绑定时 decline。`src/mcp/mcp.ts:46-51,161-170`；`src/index.ts:624-629`。品牌元信息可以议定重命名，但须与格式别名分开。

### 6.2 工具/资源/提示、生命周期（事实）

| 能力 | DAO 暴露及返回语义 |
| --- | --- |
| tools | `mcp__<server>__<tool>`，inputSchema 原样给 API 参数；运行时 schema 为未知值映射，capability=network、approval=suggest；调用参数原样转 callTool。`src/mcp/mcp.ts:212-223` |
| tool result | text 块换行拼接，非 text 块 JSON 序列化，空为 `(无输出)`；未单独把 `isError` 或 structuredContent 暴露成独立错误判据。`src/mcp/mcp.ts:70-75` |
| resources | 声明能力才注册 list_resources/read_resource；列表实时取 URI/名称，不塞工具描述；read text 直拼，blob 仅 MIME/URI 标注，不倒 base64 到上下文。`src/mcp/mcp.ts:77-82,226-249` |
| prompts | 声明能力才注册 list_prompts/get_prompt；get 参数 arguments 是 string map，缺省 `{}`；messages 渲染为 `role: text`，其它 content JSON 化。`src/mcp/mcp.ts:84-89,252-280` |
| 变更通知 | tools/prompts/resources 的 listChanged 能力触发对应通知处理，重建该 server 全部工具；通知失败吞掉。`src/mcp/mcp.ts:286-319` |
| 运行时管理 | 用户 mcp_state.json 的 disabled 数组持久化；init 跳过禁用项，单个连接失败不影响其它；toggle off 注销并断开，reconnect 禁用项只提示。`src/mcp/mcp.ts:91-103,130-143,322-360` |

连接错误按 closed/not connected/EPIPE/ECONNRESET/transport 等文本正则识别，关旧客户端→重连→重新绑定通知→重试原请求一次；普通工具错误直接抛。**原请求可能已在服务端产生副作用，重试不等于安全幂等**；不能把本地 journal 保护与 MCP 内部自动 retry 混为一谈，后续选型需决定重试边界并保留可复现断线 case。`src/mcp/mcp.ts:64-67,174-185`。

主会话 `McpManager` 枚举工具成功才登记 holder；init catch 后状态显示“未连接”，不会保留原错误细节；status.tools 统计合成工具，resources/prompts 字段硬置 0。一次性 `connectMcpServers`（子代理）另有 status 错误文本及真实资源/提示计数，两个接口不能混为一份行为。`src/mcp/mcp.ts:188-203,381-399,422-430,486-550`。addServer 实际只尝试 configFiles[0]，失败吞掉；不是注释所说逐个找可写文件。`src/mcp/mcp.ts:363-378`。

源码调用没有显式循环处理 listTools/listResources/listPrompts 的 pagination cursor，也没有 resource template/subscription、sampling/roots 的接线。此结论仅指 DAO 适配层；SDK 内部默认/协议版本协商须后续按**锁定版本**实验，不宣称 SDK 不支持。MCP 传输本体由 TS SDK 所有，源码缺少的隐式超时/握手/关闭细节不能靠本报告猜出。

## 7. LSP 与其它协议

LSP 配置 `{servers:{<name>:{command,args?,extensions:[]}}}`，按扩展名不分大小写取注册顺序第一个匹配 server；没配置报错，不自动安装 language server。按 server name 懒启动/复用客户端。`src/lsp/config.ts:4-39`；`src/lsp/manager.ts:4-27`。

客户端 spawn(command,args) 走 stdin/stdout，JSON-RPC 分帧/关联由 vscode-jsonrpc；initialize 带 processId/rootUri 与 definition/references/hover/documentSymbol/implementation/callHierarchy/workspace symbol 能力，随后 initialized。每个文件首次 didOpen、mtime 变化后 didChange 全量同步并递增 version。对外 line/character 1-based，对协议减一；支持 definition/references/implementation/hover/documentSymbol/workspaceSymbol/prepareCallHierarchy/incoming/outgoing，整理文本并处理 Location/LocationLink。dispose 直接 exit notification+dispose+kill，没有 shutdown request 或显式请求超时。`src/lsp/client.ts:1-20,40-101,104-201`。

迁移风险：JS 字符索引与 Python code point 长度不同；文件 URI 在 Windows 盘符、空格、中文、UNC 上不能用简单 URL.pathname 输出机械替代。建议固定 UTF-16 位置和 UTF-8 字节 Content-Length fixture，并对不响应 server 增加可取消超时的决策记录。LSP 3.17 官方定义 Content-Length 是内容**字节**长度、UTF-8 JSON-RPC，而不是换行分隔 JSON。[LSP 官方规范源](https://raw.githubusercontent.com/microsoft/language-server-protocol/gh-pages/_specifications/lsp/3.17/specification.md)。当前 DAO 没有显式 positionEncodings 协商或 code point 转换：`src/lsp/client.ts:14-20,56-66`；这是待验证边界。

Agent Deck 是另一个外部协议，不能当内部 runner 文件任意改名：发现记录在 `AGENT_DECK_HOME` 或 `~/.agent-deck/agents/<pid>-<instance>.json`，含 protocol=1/sessionId/instanceId/port/token 等；HTTP 端点 `/snapshot`、`/messages`、`/command`，Bearer token，拒绝 Origin，命令校验 sessionId/唯一 id，重复同签名返回旧结果、冲突 409；消息/暂停/回答/权限有独立输入及状态限制。`src/agent/deck_bridge.ts:29-38,64-110,113-149`。该接口细节应由运行时/平台研究与本报告交叉收录；本报告只登记其身份/目录/JSON 是外部兼容面，不再另起产品范围。

## 8. 内部格式可变与外部必须保留的分界（建议，待规格采纳）

| 分类 | 可以调整 | 必须用行为验收约束 |
| --- | --- | --- |
| RuoCun 自有 session DB | 新 schema/version、JSON 列改关系列、驱动、查询缓存 | 消息/工具 pair、等待、paused、run 身份、所有权、事务确认、结果附件、异常恢复、错误不清空数据；RuoCun 发布后的版本升级需自行迁移/明确拒绝 |
| runner 内部文件与 IPC | Python helper 入口、Unix socket/Windows named pipe、内部文件名和编码 | 先意图后执行、grant/claim 防重复、epoch fencing、收据验证、取消到真实关闭、失联 unknown、断点不自动重放；不能依赖 DAO helper 进程存活来满足自身恢复 |
| 日志/索引/适配缓存 | 内部格式、拆分方式、重建方式 | `/audit`、诊断、导出与可追溯结果可用；观测故障不损坏权威状态。若对外发布日志格式，再建立明确版本契约 |
| 配置/Skills/commands/agents/插件数据 | Python parser/loader 实现、在兼容范围内增加校验与错误信息 | 既有字段、目录结构、覆盖规则、触发和参数展开；路径安全修复需记录；无依据不扩大到“所有 Claude/Codex 生态文件全部兼容” |
| Hooks/MCP/LSP/Deck | Python 库、进程与网络实现 | 实际输入输出、命名、通知、错误、连接、退出/重连和鉴权；外部命令允许非 Python，这是既定范围 |
| 产品品牌路径与变量 | RuoCun 新技术标识（已定 ruocun） | `.dao/DAO.md/DAO_*` 的兼容读取、优先级和写入目标必须决定；不能通过搜索替换全部品牌字符串完成 |

源事实分别见第 2—7 节。这里是迁移边界建议，不是已通过的实现设计。

需后续存储/扩展决策票确定的具体契约：

1. 默认 `.ruocun` 写入，是否兼容读取用户/项目 `.dao`，两者并存时按整文件或字段合并；会话目录须独立，不能自动恢复旧 DAO session。配置读取与 session 查找要两个 root 策略。
2. `RUOCUN_*` 和 `DAO_*` 双设时优先级，是否保留 Hook 的 DAO_* 输出；`CLAUDE_*` 是生态接口而非可随品牌删除的文案。
3. 产品 `RUOCUN.md/RUOCUN.local.md` 与 DAO 对应物并存顺序、内容去重；是否新增 AGENTS.md 兼容（当前 DAO 明确不读，不能凭本仓库 AGENTS 决定）。
4. 凭据服务/账户新命名及旧 keyRef 是否只读解析；Windows 系统凭据补齐方式、拒绝/超时/明文兜底及 ACL。不能无授权批量搬动/复制用户秘密。
5. managed-settings 的新路径、旧路径兼容和企业规则最高层语义；trust 是否覆盖 MCP/LSP/插件/skill 等命令来源；trusted.json 是否 canonicalize（Windows 大小写、junction、UNC）。
6. 固定已实现的 Hook 子集还是扩展更多 Hook 类型/事件；保留忽略非零/超时现状还是改为可见错误。扩能力是新设计，不能记成“补齐 Python parser”。
7. MCP 连接错误自动重试副作用、分页、错误/isError 显示、status 计数缺口；选择保持现状或修复并记录。LSP 超时/URI/Unicode 修正同理。
8. “自身完整恢复”需包含费用模型桶、待审批/待回答输入、队列、branch、附件生命周期等哪些状态；优先用运行时恢复实验票收敛，不能只复刻 PersistedState 字段便宣布完整。

这些都是已登记的规格决策前置事实；没有新增“要不要迁移旧 DAO 会话”的问题。

## 9. Python 替换候选与官方资料核对（建议，全部未安装/未实测）

资料核对日期 2026-11-05。在线 main/latest 是候选说明，不是冻结源码证据，也不代表已选版本；实施前必须锁定 Python、SQLite 运行库和第三方包版本，不能把本报告在线链接当永久 API 保证。

| 端口 | 候选 | 核对事实与最小风险 |
| --- | --- | --- |
| SqlDatabase/DurableStore | 标准库 `sqlite3` + 显式事务包装 | Python sqlite3 默认事务控制不等于 DAO 显式 BEGIN IMMEDIATE；autocommit/isolation_level 要显式选择，避免 with/隐式事务嵌套；连接默认 check_same_thread=True，跨线程写需串行化。建议单 owner 连接/串行端口，先不引 ORM。[Python sqlite3](https://docs.python.org/3/library/sqlite3.html) |
| durableJson/Text | 标准库 tempfile/pathlib/os + 平台 fsync 适配 | buffered file 先 flush 再 os.fsync；Windows fsync 映射 `_commit()`；os.replace 可覆盖目标，同文件系统成功 rename 有原子性。目录元数据持久化、Windows 文件占用/ACL 仍需独立实测，不能把“原子替换”当“断电完整持久”。[Python os](https://docs.python.org/3/library/os.html#os.fsync)、[os.replace](https://docs.python.org/3/library/os.html#os.replace) |
| MCP | 官方 `mcp` Python SDK，通过自有 manager 端口封装 | 官方当前 transport 文档包含 stdio、Streamable HTTP、旧 SSE；默认 stdio 只继承 allow-list，与 DAO 全继承不同，需明确传 env。[官方 transports](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/client/transports.md)。v1→v2 指南显示 API、字段名、HTTP 参数和默认探测等变化；先锁 major+精确版本，验证 classic 服务兼容，不能直接复制旧教程 API。[官方 migration](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/migration.md) |
| keychain 端口 | `keyring` + 严选系统 backend，或保留平台 CLI adapter | 官方列出 macOS Keychain、Secret Service/KWallet、Windows Credential Locker，支持 get/set password；默认 backend 自动选择，不能因此假设所有机器可用或所有 fallback 安全。保留超时/失败兜底端口语义并单测 Windows backend。[keyring 官方文档](https://keyring.readthedocs.io/en/latest/) |
| LSP | `pygls` 的 JsonRPCClient/BaseLanguageClient 或自有小型 JSON-RPC stdio adapter | 官方源码有 stdio start_io、退出时拒绝 pending request、生成的 async LSP 方法；LanguageClient 仍是薄类，JsonRPCClient 注释主要测试上下文，故只列候选，不称成熟即插即用客户端。必须验证自身初始化/同步/输出语义。[JsonRPCClient](https://github.com/openlawlibrary/pygls/blob/main/pygls/client.py)、[BaseLanguageClient](https://github.com/openlawlibrary/pygls/blob/main/pygls/lsp/_base_client.py)、[LanguageClient](https://github.com/openlawlibrary/pygls/blob/main/pygls/lsp/client.py) |
| Hooks/子进程 | asyncio subprocess + 兼容 shell adapter、JSON | 不需要执行 TS/JS loader；但要保留 command 的 shell 含义、毫秒 timeout、UTF-8 stdin/stdout、4 MiB 限制和进程树退出。此为设计建议，实际 Windows shell 选择由平台票验收，不把 POSIX 单引号 fixture 机械执行 |
| 解析器 | json + 小型兼容 frontmatter/.env/参数解析器 | 先复刻来源明确接纳子集，再考虑 YAML/dotenv 等完整库；Python 标准 YAML/dotenv 并非来源依赖，默认能力常会改变引号/布尔/路径和变量展开语义。此为由第 3—5 节源码推得的建议，不是第三方库能力断言 |

## 10. 跨语言 fixture 与最小实验

### 10.1 可复用的真实来源资产（静态清单）

| 来源 fixture / 测试定义 | 可抽取 golden | 证据限度 |
| --- | --- | --- |
| `src/session/durable_store.test.ts:25-56` | 活 owner 拒绝、旧 epoch fencing、事件确认与消息 rollback、重复终态、等待恢复不轮询、paused 离线完成、未知工具阻副作用、future/corrupt 拒绝、附件缺失、事务失败不发布 | 测试源中的 mock identity 和临时数据库构造；本轮没运行，无用户数据库 |
| `src/tools/managed_shell.test.ts:29-145`；`src/session/process_identity.test.ts:8-63` | grant 前失败/诊断、离线完成去重、真实取消、附件缺失与身份不匹配、失联 unknown、PID 重用和权限错误 | 部分命令 sleep/Unix shell 形状需 Windows 等价 fixture；现有测试文本不是 Windows 已通过证据 |
| `src/config/credential.test.ts:23-84`；`src/config/env_file.test.ts:7-65`；`src/config/profiles_store.test.ts`；`src/permissions/settings.test.ts` | 内联/keyRef、无 secret、keychain 写失败兜底、env 已设不覆盖、v1→v2、保留其它字段、分层权限 | 使用脱敏合成 key，禁止读取真实凭据作 golden |
| `src/project_doc.test.ts:12-58`；`src/skills/skills.test.ts:8-145`；`src/skills/discover.test.ts:25-167` | DAO-only、git 父链/local 顺序、扁平/目录技能、触发开关、别名与 namespace、paths、realpath、动态正/负缓存 | 补同名大小写、emoji 截断、Windows junction、深浅同时发现；原定义不能覆盖所有冲突 |
| `src/hooks/hooks.test.ts:7-89`；`src/hooks/integration.test.ts:7-21`；`src/tools/execute.test.ts` | CC-like nested/裸格式、exit 2、纯文本/JSON、最强权限、updatedInput 同一最终参、prehook once | 原 JS shell 单引号命令不可直接当 Windows 输入；应改为可控 helper argv+shell wrapper |
| `src/mcp/__fixtures__/fake-mcp-server.mjs:1-58`；`src/mcp/mcp.connect.test.ts:37-137` | echo、MCP_FAKE_RICH 的资源/提示/elicitation、持久 crash 计数器断线重试 | 是真实现成协议 server fixture 源；后续可在独立可写实验副本执行，不改只读快照；本轮未运行 |
| `src/mcp/mcp.http.test.ts:1-65`；`src/mcp/mcp.manager.test.ts:11-78` | HTTP 真往返、失败隔离、禁用状态落盘与重连、崩溃自愈 | HTTP fixture 不等于 SSE 覆盖；需补旧 SSE、headers、listChanged、分页、关闭/取消 |
| `src/plugins.test.ts:17-97`；`src/commands/custom.test.ts:7-32`；`src/agent/agent_defs.test.ts` | 两种 manifest/hooks 布局、组件聚合、plugin<user<project、参数展开、agent 解析子集 | 增加路径穿越拒绝、name/slug 冲突、换行、空 body 和有引号参数 |
| `src/lsp/testfixtures/sample.ts`；`src/lsp/client.test.ts:27-88`；`src/lsp/config.test.ts`；`src/lsp/manager.test.ts` | 定义/引用/hover/符号/实现/调用层级、编辑后同步、配置覆盖与复用 | 测试在 CI=1 时跳过，实际用 npx --yes 启 typescript-language-server，依赖本地 TypeScript；`src/lsp/client.test.ts:8-20`。需补可控协议假 server，不把真实 server 可用假设搬进单测 |

### 10.2 Golden 比较规范（建议）

先从快照测试中的**输入和预期断言**提取 UTF-8 JSON manifest，再用后续隔离的来源执行器与 Python adapter 比较。输入目录树、env、命令 argv、事件/response transcript、预期 registry/persisted state 分离；统一注入 clock/UUID/identity/路径根。仅归一已声明的不稳定值（临时绝对根、时间戳、UUID），不能排序覆盖次序、把 undefined/null/缺失字段合并或抹掉 stdout/stderr/换行差异。

JS 与 Python 特别需要覆盖：UTF-16 slice（220/60/120/24000 字符）对 emoji 的边界、JSON.stringify 的省略 undefined 与 Python None 的差别、空串真值和 Number(x)||default、对象插入顺序、RegExp vs re、Windows env 大小写、CRLF/LF、realpath 大小写/junction/UNC、同名服务整项覆盖与数组并集合并。来源依据分别为 `src/skills/skills.ts:117,135`；`src/session/log.ts:58-63`；`src/tools/tool_audit.ts:21`；`src/agent/background_runtime.ts:66-69`；`src/config/env_file.ts:39`；`src/hooks/hooks.ts:95`；`src/permissions/settings.ts:95-129`。

### 10.3 建议最小实验及通过条件（全部待执行）

| 编号 | 实验 | 最小通过条件 |
| --- | --- | --- |
| E1 | Python sqlite3 两进程 owner+事务实验；本地 NTFS；逐个杀死 beforeTool、afterTool、事件入库/消息保存之间的阶段 | 第二活 owner 拒绝；旧 owner 写拒绝；没有结果未知的自动副作用重放；事件确认和检查点同成同败；读回 WAL/FULL/timeout，记录 SQLite runtime 版本 |
| E2 | 原子 receipt/附件写入及重启；模拟磁盘满/只读/占用；Windows ACL 与目录同步 | 未完成临时文件不被当终态；旧有效收据不变；缺失/哈希错能报告 unknown；证明 rename 原子性和持久性分别覆盖；不声称一次 kill 测试等同断电验证 |
| E3 | Python runner 独立启动、父进程退出、重新接管、cancel、host/boot/start/epoch mismatch | grant 前绝不执行，grant 后不自动重发；离线完成仅消费一次；canceling 到真实 close；Windows named pipe/进程树选型有证据；不依赖 POSIX 负 PID |
| E4 | 配置树固定 fixture（双品牌目录/变量、坏 JSON、空值、keyRef、trust、managed、DAO.local、无 .git） | 先决定 alias 表，再验证每通道独立顺序；账户环境不意外抢占 profile；原未知顶层字段保留；Windows 权限失败行为可见、秘密不写日志 |
| E5 | Hook helper：捕获 stdin/env/cwd，输出 code 0/2/1、JSON/text、超时、4 MiB、非法 matcher、updatedInput | 字段和毫秒单位一致；code 2 阻断；改写后再审批/执行；prehook once/durable reuse；SessionStart 不累积；未支持 type 有清晰既定处理 |
| E6 | Python MCP client 连冻结 fake server（未来独立可写副本）及受控 HTTP/SSE server | 三传输 tools/resources/prompts/elicitation、headers/env、listChanged、禁用/重连/失败隔离全覆盖；记录 classic handshake 版本；断线副作用计数验证重试；输出与来源 adapter golden 一致 |
| E7 | Python LSP adapter 连可控 Content-Length server，再连一款真实 server | 分片帧/合帧/乱序 response/错误/退出不挂死；initialize→initialized→didOpen→didChange；九类操作、LocationLink、emoji UTF-16、中文空格 Windows URI；超时/取消行为已决定 |
| E8 | 安装到临时插件/skills 根，不运行任意真实插件；命令分派集成 | 合法插件组件和覆盖正确、越界名字被拒；本地相对资源齐全；namespace/裸名/内置命令冲突可预测；所有拷贝在实验根，无修改来源/用户目录 |

验收证据应写明输入、锁定版本、自动结果和剩余平台限制；Windows Terminal 真实交互与缩放属于其它验收票，以上协议/存储实验不能代替用户体验验收。

## 11. 本轮完成与后续入口

本轮完成：已形成 schema/事务/原子文件/身份关联、配置与环境发现、产品规则、Skills、Hook 实际子集、MCP 三传输及能力、插件命令/agent 定义、LSP/Deck 边界、跨语言 fixture 和 Python 候选实验清单。没有声称任何产品实现或自动测试通过。

建议收录至[确定持久化与外部扩展的兼容边界](../issues/09-storage-extension-decision.md)，与[用最小 Python 实验验证取消与崩溃恢复契约](../issues/05-runtime-recovery-experiment.md)、[确定 Python 并发、任务与恢复技术路线](../issues/08-python-runtime-decision.md)、[确定测试、回放与评估的复用门禁](../issues/11-test-replay-decision.md)共同约束规格。研究报告单独本地提交，由主会话收录结论后关闭本研究票；本分支不修改地图、子票、主工作区，不 push、不 merge。
