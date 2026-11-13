# 冻结 DAO 的完整功能、模块职责与运行时调用链研究

日期：2026-11-05。研究票：[查清完整功能、模块职责与运行时调用链](../issues/02-function-runtime-research.md)。研究分支：`research/ruocun-core`。

## 1. 证据范围与结论口径

唯一源码来源为冻结快照 **dao-f17e189-7ac654a0dc06**：来源 HEAD `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`，捕获 797 个已跟踪文件及 8 个未跟踪源码文件；源码树 SHA-256 为 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`。快照记录与校验方式见[唯一参考快照](../reference/README.md)，本报告从已解包的只读副本读取，没有读取活动 DAO 工作区的新内容。

下文 `src/...:行号`、`package.json:行号` 等均指该快照内的相对路径，既包含 HEAD，也包含冻结的本地覆盖层。可在归档内重建相同路径后核查；不以活动绝对路径或远程最新分支代替证据。

- **静态事实**：从文件、注册表、分支条件和调用点直接读到的内容；源码注释中的“实测”“已验收”只表示来源作者的记录，本轮没有复核。
- **静态推断／可疑差异**：多处代码组合产生的可达性或行为判断，均给出入口及下游证据，需最小实验建立测试 oracle。
- **候选建议**：Python 对应原则及选型方向，不表示已作架构决定或已有实现。
- **实验未验证**：本轮没有运行 DAO、测试、API 请求、安装或产品原型；没有获得任何 Windows 终端体验验收。研究脚本仅枚举、读取和统计源码文本。

本轮使用 research 技能要求的一级来源调查；技术说明以真实模块职责为主。已读取本 worktree 的 AGENTS、CONTEXT、两份 ADR、迁移规格、基线、对应表和验收矩阵。文档中的旧版本数字不能覆盖代码证据。

### 1.1 最重要的迁移事实

1. **定义了 43 个内置工具**，普通启动默认注册 **42 个**（LSP 有配置才注册）；`--no-web`／`--eval` 移除 WebFetch、WebSearch 后为 **40 个**，若配置 LSP 则加 1。MCP 另按实际服务动态增减，没有固定总数。注册依据是 `src/index.ts:598-615`、`648`、`650-661`；完整清单见第 3 节。
2. 43 个定义中只有 **16 个 `shouldDefer:true`**，不配置 LSP时为 15 个；Task 系列目前常驻。`src/index.ts:638-645` 中“22 个内置延迟工具”的注释属于滞后说明，不能当现况；TaskCreate 的撤销 defer 说明与实现位于 `src/tools/task_create.ts:25-34`。真正发给模型的工具集合还受模式、激活和 MCP 可见性过滤，见 `src/tools/tools_for_mode.ts:16-26`。
3. 调度器、工具轮、后台任务、持久化各有独立职责；**waiting 不是完成，completed 也不是质量验收**。单轮无工具调用即返回 completed（`src/agent/loop.ts:629-633`），等待转移到 SessionScheduler（`src/agent/session_scheduler.ts:122-139`），没有通用“答案合格才完成”的执行判据。
4. 当前会话恢复以 **SQLite v2 + 工具执行意图/结果 + 后台执行身份/事件 + 代理检查点**为主，`state.json` 是兼容导出，不是唯一真实存储（`src/session/durable_store.ts:48-98`；`src/session/log.ts:94-101,135-138`）。不能降格成“保存聊天 JSON，再重跑剩余工具”。
5. 本地覆盖层增加 Windows 进程身份、若存品牌与 SIXEL 欢迎角色、终端回包过滤、独立视口重排等行为；核心恢复链还保留 Unix socket／进程组等平台假设。Windows 身份支持不等于 Windows 全功能已完成（`src/session/process_identity.ts:11-74`；`src/tools/managed_shell.ts:17-29`；`src/tools/shell_runner.ts:74-105`）。

## 2. 全部顶层模块及职责边界

`src/` 有 **19 个直接子目录**（包含 `data/`），另有 7 个非测试顶层 `.ts` 文件。附录 A 枚举每个目录的全部非测试源码，避免仅凭架构图漏掉配套模块。这里按文件名不含 `.test.` 计“非测试”，并不把它等同于纯产品运行文件：222 个 `.ts`（含声明文件）+ 11 个 `.tsx` = 233 个，再加 1 个 `.mjs`，共 234 个；包含 `lsp/testfixtures/sample.ts`、`mcp/__fixtures__/fake-mcp-server.mjs` 等 fixture，以及 `agent/background_test_helpers.ts` 测试辅助文件。下表是职责与主要调用关系，而非新的 Python 拆分决定。

| 来源模块 | 现行职责与主要调用关系 | 定位证据 |
| --- | --- | --- |
| `index.ts` | 唯一 CLI 组合根：参数、配置、信任、工具与扩展加载、系统提示、Session/上下文/权限组装；建立 taskManager→BackgroundRuntime→store→scheduler→TUI/REPL；选择一次性、交互、管道路径并收尾 | `src/index.ts:177-360,598-667,1212-1283,1702-1755,1839-1916,2635-2693` |
| `repl.ts` | 纯文本循环；判别命令，必要时 pause→settled；普通输入交 scheduler；EOF 等 finished；保留旧 drainAndContinue 适配路径 | `src/repl.ts:58-80,82-118` |
| `plugins.ts` | 用户插件安装/删除/发现；插件打包 skills、commands、agents、hooks；兼容根 manifest 与 `.claude-plugin/plugin.json` | `src/plugins.ts:22-77,83-128` |
| `project_doc.ts` | 用户级及项目祖先 DAO 指令发现；每层 DAO.md 后叠 DAO.local.md，不回退 AGENTS.md／CLAUDE.md | `src/project_doc.ts:5-12,29-46` |
| `env_snapshot.ts` | 环境、网络、顶层目录和内存信息探测及提示文本；组合根早启异步探测，结果经安全边界注入 | `src/env_snapshot.ts:33-93,123-163,198-240`；`src/index.ts:348-350,1562-1563` |
| `schedule.ts` | OS crontab 读写、序号查询删除、构造到点运行 headless DAO 的命令；与会话 scheduler 完全不同 | `src/schedule.ts:9-24,29-53` |
| `version.ts` | 版本常量，启动、界面、更新与构建同步的来源 | `src/version.ts:1`；`src/index.ts:217-219`；`package.json:26` |
| `agent/` | loop 是工具/模型循环；SessionScheduler 管会话状态和输入；BackgroundRuntime 管后台执行快照、事件、等待；tasks 管代理/monitor/手工任务；runAgent 管子 Session；其余文件分别处理定义、提示、权限工具裁剪、生命周期、摘要、fork/resume、记忆、hooks、worktree、反思/压缩、清理、Deck | `src/agent/loop.ts:153-194`；`src/agent/session_scheduler.ts:19-51`；`src/agent/background_runtime.ts:73-126`；`src/agent/runAgent.ts:147-235,378-464` |
| `approval/` | 审批接口、stdin 批量询问和“始终允许”存储；TUI 提供另一套 prompt 端口，最终由 PermissionGate 消费 | `src/approval/types.ts:1`；`src/approval/stdin_prompt.ts:1`；`src/approval/store.ts:5-21`；`src/permissions/gate.ts:139-186` |
| `client/` | SSE 分块解析、Chat Completions 请求与流式/非流式韧性、usage、工具参数片段组装；Responses 桥接将选定路由转换后回到统一事件契约 | `src/client/sse.ts:7`；`src/client/client.ts:62-141,271-411`；`src/client/responses.ts:5-69,85-125` |
| `commands/` | 基础斜杠命令、6 个 prompt 命令、自定义 Markdown 模板及命令暂停分类；业务命令的实际大头仍在 index 的 Ink 分支 | `src/commands/commands.ts:20-81`；`src/commands/builtin.ts:11-98`；`src/commands/custom.ts:48-63`；`src/commands/scheduling.ts:1-13` |
| `config/` | 多 provider/profile、模型属性/窗口/输出限制、凭据/keychain、首次引导、信任、dotenv、旧目录迁移、密钥校验、更新检查；不负责 Agent 主循环 | `src/config/profiles.ts:5-44,118-155`；`src/config/credential.ts:15-43`；`src/config/keychain.ts:17-56`；`src/index.ts:353-358,409-516` |
| `data/` | 道家名句静态资源，供 TUI 使用；不控制任务状态 | `src/data/laozi-maxims.ts:1`；`src/tui/maxim.ts:1` |
| `hooks/` | 解析、匹配与顺序运行事件 hook，汇总 block/context/permissionDecision/updatedInput；只实际运行 command 类型 | `src/hooks/hooks.ts:5-30,54-108,123-143` |
| `i18n/` | 当前语言、用户语言存储、zh/en 消息映射；界面和部分工具描述切换 | `src/i18n/i18n.ts:1`；`src/commands/commands.ts:61-69`；`src/tools/tools_for_mode.ts:16-26` |
| `lsp/` | 读取用户定义的语言 server，按文件惰性启动 JSON-RPC 客户端并退出清理；不自带语言 server 二进制 | `src/index.ts:650-657`；`src/lsp/manager.ts:6-26`；`src/lsp/client.ts:1` |
| `mcp/` | stdio、Streamable HTTP、SSE 连接；动态工具/资源/提示、toggle/reconnect/add/list_changed、elicitation、关闭；当前入口使用 McpManager，旧 connectMcpServers 仍导出 | `src/mcp/mcp.ts:117-162,200-323,332-417,430` |
| `memory/` | Markdown/frontmatter 存储、类型路由、项目过滤、来源验证、注入全文/索引、蒸馏、合并、衰减清理和审计；与 session 持久化分开 | `src/memory/store.ts:8-35,52-105`；`src/memory/validate.ts:9-17`；`src/memory/inject.ts:46-79`；`src/index.ts:675-732` |
| `obs/` | 可选观察后端与 stream/turn/tool 包装，usage/会话关联、事件和退出 flush；业务关闭时仍走原路径 | `src/obs/index.ts:1-3`；`src/index.ts:200-215,2698-2704` |
| `permissions/` | 分层规则、工具身份映射、Shell 语法/AST 与危险模式、敏感目标、deny/ask/allow、auto 分类器和熔断、审计、环境/秘密处理 | `src/permissions/settings.ts:75-97,220`；`src/permissions/engine.ts:83-100,172`；`src/permissions/gate.ts:105-186` |
| `prompt/` | 根系统提示与长任务自主 directive 的模板组装，不运行工具或维持队列 | `src/prompt/system_prompt.ts:1`；`src/index.ts:876,2378-2407` |
| `repomap/` | 文件遍历→tree-sitter WASM 符号提取→图排名→预算裁剪输出，按 mtime/size 缓存；默认预算 2048、最多 4000 文件、单文件 512KiB | `src/repomap/index.ts:11-68`；`src/repomap/graph.ts:1`；`src/repomap/extract.ts:1` |
| `session/` | Session 消息/usage/费用、日志导出、SQLite、所有权与进程身份、工具日志、后台恢复、影子 git 检查点、审计；工作区检查点不是代理检查点/DB 事务 | `src/session/log.ts:84-138`；`src/session/durable_store.ts:48-98,188-222`；`src/session/recovery.ts:7-72`；`src/session/checkpoint.ts:45-106` |
| `skills/` | frontmatter/Markdown 发现、物理文件去重与同名覆盖、条件 paths 动态激活、内置技能、安装、外来技能适配转换及调用审计 | `src/skills/skills.ts:25-76,124-136`；`src/skills/discover.ts:18,72-114`；`src/index.ts:767-786,1160-1210` |
| `tools/` | 工具 schema/契约、注册/激活、执行裁决与并发屏障；各工具 handler；Shell、路径、锁、原子写、输出溢写、SSRF/缓存、沙箱等支撑能力 | `src/tools/types.ts:174-218`；`src/tools/registry.ts:114-312`；`src/tools/execute.ts:108-270` |
| `tui/` | Ink/React 输入、流式转录、审批/问题/选择器、任务面板、粘贴/图片、主题/中英文、窗口布局、标题/焦点/通知/防休眠；本地终端回包/欢迎角色为展示适配层 | `src/tui/app/App.tsx:169-338,407-615,869-1296,1380-1443`；`src/tui/app/run.tsx:15-60` |

### 2.1 仓库配套目录和非产品入口

`package.json:10-41` 指定 `dao→dist/index.js`，开发 `tsx src/index.ts`、TypeScript 构建、Bun 单文件 bundle、postinstall patch-package、Vitest/typecheck/lint 及 memory/cache 接受脚本。依赖包含 Ink/React、Zod、SQLite、MCP SDK、JSON-RPC、tree-sitter（`package.json:65-94`）。这些是工程配套，不可机械改后缀后宣称 Python 发布完成。

快照顶层还包含 `.dao/`（项目 settings）、`.github/`（CI、release、issue 模板）、`docs/`（设计/用户/架构材料及媒体）、`evals/`（评测脚本、任务、trace viewer、memory fixtures）、`patches/`、`scripts/`、`tests/`；完整存在性盘点见附录 A。CI 在 Ubuntu 运行（`.github/workflows/ci.yml:10-12`）；release 在 Ubuntu 交叉编译含 Windows 的五个 Bun 目标（`.github/workflows/release.yml:13-29`），这不是 Windows 实机验收证据。`scripts/generate-mascot-data.mjs:8-14,28-53` 是资源生成入口，运行时读取已嵌入帧，不要求每次启动生成。

## 3. 全部工具：定义、注册、可见性与用途

### 3.1 计数方法

静态枚举 `src/tools/*.ts` 中非测试文件的 `export const ... = defineTool({`，读取紧随其后的 `name`、`capability`、`approval`、`shouldDefer`，得到下表 **43 个不同名字**。再与 `src/index.ts:599-614` 数组的 **40 个工具变量**及单独注册的 ToolSearch、RepoMap、条件 LSP 逐一对账；未将 registry 里的函数、工具上下文回调、MCP 动态工具或 renderer 遗留 case 另算工具。`MultiEdit` 仅见渲染识别等遗留路径（`src/tui/app/App.tsx:124,422-433`），本次注册清单没有该工具，不能由界面字符串推出已实现。

表中“延迟”表示必须通过 ToolSearch 激活后才进入实际 API tools；“常驻”仍可能受 plan、子代理工具集和 no-web 过滤。capability 与 approval 是工具声明，不等于最终裁决；权限规则和自检见第 5 节。

| 工具名 | capability / approval | 初始 schema | 功能边界与定义证据 |
| --- | --- | --- | --- |
| Read | read / auto | 常驻 | 文本带行号、offset/limit、图片；二进制/大文件护栏，记录编辑前读取元信息；`src/tools/read_file.ts:9-17,39-94` |
| ListDir | read / auto | 常驻 | 路径目录列表；`src/tools/list_dir.ts:7-33` |
| Glob | read / auto | 常驻 | 文件/路径 glob，修改时间排序；实际导出变量名 fileSearchTool；`src/tools/file_search.ts:11-34` |
| Grep | read / auto | 常驻 | 正则、内容/文件模式、上下文、分页、跨行、类型等；`src/tools/grep_files.ts:65-126` |
| Write | write / required | 常驻 | 全文创建/覆盖，读前检查、mtime/size 漂移、锁与原子替换；`src/tools/write_file.ts:9-40,67-76` |
| Edit | write / required | 常驻 | old/new string，唯一匹配或 replace_all，锁与 diff；`src/tools/edit_file.ts:11-48,78-85` |
| NotebookEdit | write / required | 延迟 | ipynb 单元格编辑；`src/tools/notebook_edit.ts:9-39` |
| Bash | exec / required | 常驻 | 前台命令、显式后台、沙箱开关、进程转后台；前台当前无超时参数；`src/tools/exec_shell.ts:263-340,354-440` |
| BashOutput | read / auto | 常驻 | 按后台 Shell id 增量读日志并节流；不是阻塞等待；`src/tools/exec_shell_poll.ts:22-65` |
| KillShell | exec / auto | 常驻 | 请求终止已启动 Shell，取消请求不等于退出确认；`src/tools/exec_shell_kill.ts:6-25` |
| WebFetch | network / suggest | 常驻 | URL 抓取、纯文本/按 prompt 抽取、缓存与 SSRF 检查；no-web 时不注册；`src/tools/fetch_url.ts:22-55` |
| WebSearch | network / suggest | 常驻 | DuckDuckGo HTML 搜索，结果上限；no-web 时不注册；`src/tools/web_search.ts:27-50` |
| AskUserQuestion | read / auto | 常驻 | 询问、选项/多选，由上下文提供 UI；`src/tools/ask_user.ts:18-58` |
| TodoWrite | plan / auto | 常驻 | 整表替换的扁平清单，无独立 task id；`src/tools/todo_write.ts:28-68` |
| MemoryRead | read / auto | 常驻 | 取记忆正文；`src/tools/memory_read.ts:15-40` |
| MemoryWrite | plan / auto | 常驻 | 五种类型、三作用域、重要度/来源，或明确删除；`src/tools/memory_write.ts:25-60` |
| Skill | read / auto | 常驻 | 按名加载技能正文；`src/tools/skill.ts:5-34` |
| SkillInstall | exec / required | 延迟 | Git/本地技能安装；`src/tools/skill_install.ts:7-34` |
| Agent | plan / auto | 常驻 | 单/多任务、同步/后台、fork/worktree/model/plan；继续代理由 TaskSend/recovery 路径处理；`src/tools/agent.ts:78-174,175-415` |
| TaskSend | plan / auto | 常驻 | 向代理追加指令，已结束任务的恢复转交 ctx.resumeAgent；`src/tools/task_send.ts:6-49` |
| MessageParent | plan / auto | 延迟 | 子代理发送进展或 attention 给父；`src/tools/message_parent.ts:7-37` |
| TaskWait | read / auto | 常驻 | 对当前会话后台代理或 Shell 的 any/all 事件等待；单独调用，不等待手工/前台任务；`src/tools/task_wait.ts:3-12` |
| TaskCreate | plan / auto | 常驻 | 只建手工任务记录，不启动进程；`src/tools/task_create.ts:6-40` |
| TaskList | read / auto | 常驻 | taskManager 当前/含已结束清单；不是 Shell 统一清单；`src/tools/task_list.ts:19-47` |
| TaskGet | read / auto | 常驻 | taskManager 单任务详情；`src/tools/task_get.ts:4-37` |
| TaskOutput | read / auto | 常驻 | 代理转录增量，WeakMap 游标；手工任务无转录；`src/tools/task_output.ts:33-75` |
| TaskUpdate | plan / auto | 常驻 | 手工任务描述/状态/结果；`src/tools/task_update.ts:4-36` |
| TaskStop | exec / auto | 常驻 | 代理 abort→canceling→执行器确认 canceled，手工任务直接取消；`src/tools/task_stop.ts:6-32` |
| NotifyUser | plan / auto | 延迟 | 请求用户通知，由运行上下文提供；`src/tools/notify_user.ts:7-35` |
| SendUserMessage | plan / auto | 常驻 | 用户可见消息、附件路径、normal/proactive 状态；`src/tools/send_message.ts:8-40` |
| EnterPlanMode | plan / auto | 延迟 | 切换只读规划；`src/tools/plan_mode.ts:6-30` |
| ExitPlanMode | plan / auto | 延迟 | 提交方案并退出规划，由上下文处理批准；`src/tools/plan_mode.ts:35-67` |
| EnterWorktree | write / suggest | 延迟 | 当前代理进入隔离树，记录 previousCwd；不允许叠加进入；`src/tools/enter_worktree.ts:10-46` |
| ExitWorktree | write / suggest | 延迟 | keep/remove，丢弃有改动或新增提交需 discard_changes；恢复 cwd；`src/tools/exit_worktree.ts:4-44` |
| Monitor | exec / required | 延迟 | 后台监控命令，stdout 按行批量通知，persistent/超时与 TaskStop；`src/tools/monitor.ts:13-67,79-120` |
| Config | plan / auto | 延迟 | 配置读取或写用户 settings，含权限模式/主题/检查点及通用点路径；`src/tools/config.ts:12-94` |
| Schedule | exec / required | 延迟 | add/list/remove 共用 OS crontab；`src/tools/schedule_tool.ts:7-44` |
| CronCreate | exec / required | 延迟 | 持久定时创建；显式 durable=false 尚不支持，一次性不自动删；`src/tools/cron_tools.ts:8-46` |
| CronDelete | exec / required | 延迟 | 以清单序号删除；`src/tools/cron_tools.ts:50-66` |
| CronList | read / auto | 延迟 | OS 定时任务清单；`src/tools/cron_tools.ts:70-82` |
| ToolSearch | read / auto | 常驻 | 搜索激活 MCP 和延迟内置工具；无 MCP 也注册；`src/tools/tool_search.ts:6-32`；`src/index.ts:638-648` |
| RepoMap | read / auto | 延迟 | 获取/刷新代码地图；`src/tools/repo_map.ts:8-38` |
| LSP | read / auto | 延迟、条件注册 | 9操作：goToDefinition/findReferences/hover/documentSymbol/workspaceSymbol/goToImplementation/prepareCallHierarchy/incomingCalls/outgoingCalls；`src/tools/lsp.ts:4-7,35-62`；`src/index.ts:650-657` |

MCP 按 server 注册 `mcp__<server>__<tool>`，支持资源时另注册 `list_resources/read_resource`，支持提示时另注册 `list_prompts/get_prompt`（`src/mcp/mcp.ts:207-283`）。前 **5 个** MCP 注册时自动可见，其余 ToolSearch 激活；注册顺序一次性判定，不随总数跨阈值撤销（`src/tools/registry.ts:130-160`）。延迟内置工具真实请求时完全隐藏，系统摘要处保留占位说明；JSON schema 校验失败、截断 JSON 诊断和 handler 调度统一在 registry（`src/tools/registry.ts:215-312`）。

## 4. 命令全集与不同入口的能力差异

### 4.1 操作员 CLI 与参数

直接检查 `process.argv.slice(2)`，没有在这些分支之前做小写归一化：版本为 `--version/-v`；`trust`；`plugin add/list/remove`；源码实际判断 **`Schedule add/list/remove`** 与 **`Skill add`**（S 大写），帮助字符串示例却写小写 schedule/skill（`src/index.ts:197,216-275`）。这是静态入口差异，不能只抄帮助文案；尚未运行确认用户实际输入/打包入口的结果。底部另有内部 `--dao-shell-runner <dir>` 分派，用于持久 Shell runner，不计用户命令（`src/index.ts:2698-2704`）。

显式识别的普通 flag 如下；未知参数没有统一拒绝器，而是过滤已知 token 后拼成一次性 prompt（`src/index.ts:276-346`）：

| 类型 | 参数 |
| --- | --- |
| 权限/长任务 | `--yolo`；`--goal`、`--task`、`--coordinator` 三者进入同一长任务模式 |
| 恢复 | `--continue/-c [session-id]`，紧随非 `-` token 视作 id |
| 凭据/模型 | `--api-key <key>`、`--provider <provider>`、`--model <model>` |
| 调试/反思 | `--verbose/--debug`、`--obs`、`--reflect-memory`、`--reflect-challenger`、`--progress-advice`、`--no-progress-advice` |
| 隔离开关 | `--eval`、`--no-memory`、`--no-skills`、`--no-mcp`、`--no-hooks`、`--no-project-instructions`、`--no-web` |
| 独立权限解析 | `--allow <rule>`、`--deny <rule>`、`--ask <rule>`、`--add-dir <dir>`、`--permission-mode <mode>`；`src/permissions/settings.ts:75-90` |

`--eval` 隐含禁用户/磁盘/插件 skills、自定义 agent/命令、memory 注入、MCP、project instructions、web；**不隐含禁内置 skills 和 hooks**，显式 `--no-skills` 才同时禁内置（`src/index.ts:293-328,741-786,1212-1218`）。`--no-memory` 不是删除 MemoryRead/MemoryWrite 工具的开关：工具仍在注册数组，且启动迁移/GC 在合并条件前运行；因此不能把 eval 叫作“零本地副作用沙箱”（`src/index.ts:606,675-688,723-732`）。

### 4.2 固定斜杠命令：52 个名字，别名计入

计数取 **Ink 分支 index 直接比较的 38 个 distinct name** ∪ **dispatchCommand 的 9 个 case** ∪ **builtin 的 6 个键** ∪ **App 独立处理 theme/loop**，去重得到 **52**；不是将菜单数当实现数。动态 skills、自定义命令不纳入固定数。解析保留大小写；index 先验证名字字符，随后顺序匹配；App 将原始 full 传给 runCommand（`src/index.ts:1917-1920`；`src/tui/app/App.tsx:497-505,572-573`）。

| 名字（均带 `/`） | 分支职责/子命令 | 证据 |
| --- | --- | --- |
| model、plan、clear、compact、cost、lang、help、exit、quit | 模型、只读、清空、压缩、费用、语言、帮助、退出；Ink 对 model/clear/lang/quit 增加专门路径 | `src/commands/commands.ts:29-78`；`src/index.ts:1921-1928,2475-2504`；`src/tui/app/App.tsx:514-525,570-575` |
| skills | 列表/选择器，单项 on/off、bundled 批量开关等 | `src/index.ts:1930-1967`；`src/tui/app/App.tsx:568-569` |
| context、context-window | 上下文分项，窗口值查询/解析 K/M/设置及手动锁定 | `src/index.ts:1968-2041,2251-2267` |
| tasks | 当前 taskManager running 清单 | `src/index.ts:2042-2045` |
| mcp | 列表、reconnect、toggle [on/off]、add server command args | `src/index.ts:2047-2076` |
| diff、doctor | git 未提交改动、自检环境 | `src/index.ts:2078-2097` |
| memory | 记忆审核与 delete | `src/index.ts:2098-2117` |
| permissions | 当前模式/规则显示；后文另有 list/add/remove 实现但受前置 return 遮蔽，见第 9 节 | `src/index.ts:2118-2122,2410-2444` |
| session、audit | 会话信息；memory/reflect/tools/perms/cache/skills 审计等 | `src/index.ts:2123-2158` |
| resume | 列表/按 id 切原会话与 owner/runtime；拒绝有运行代理时切换 | `src/index.ts:2159-2185` |
| branch、rename、rewind | 保存对话分支、命名；按用户消息节点截断，可选 code 影子 git 回退 | `src/index.ts:2187-2226` |
| export | 导出会话 Markdown | `src/index.ts:2228-2238` |
| **Config**、effort、status | 配置显示（大小写保留）、思考档位、状态 | `src/index.ts:2239-2249,2269-2272` |
| plugin、hooks、agents、files | 列出插件/Hook/自定义 agent 类型/已读文件 | `src/index.ts:2274-2300` |
| copy、btw | 复制末条回答；随手备注注入而不立即请求 | `src/index.ts:2297-2311` |
| account、accounts | 账户列表/选择器、add、rm、切换名 | `src/index.ts:2312-2342`；`src/tui/app/App.tsx:566-567` |
| bypass、yolo、mode | 全权放行及权限模式切换，plan 不在 auto↔bypass 循环中 | `src/index.ts:2344-2377,2521-2535` |
| goal、task、coordinator | 长任务开启/关闭及目标 prompt；coordinator 为合并后的别名 | `src/index.ts:2378-2407` |
| restore | 影子 git 回退，并先存回退前自动快照 | `src/index.ts:2458-2465` |
| recovery | 查询、resolve 未决工具、decide unknown 任务、continue interrupted 代理 | `src/index.ts:1284-1306,1922` |
| simplify、remember、review、init、batch、skillify | builtin prompt 展开，batch 提示使用隔离 worktree 派发；本身不是一个新执行器 | `src/commands/builtin.ts:11-98`；`src/index.ts:2446-2451` |
| theme、loop | App 内主题会话切换；loop `<整数>s/m/h <prompt>` 周期排队，off 取消，退出清 timer | `src/tui/app/App.tsx:285-287,506-552` |

`quit --keep-background` 是退出保留 Shell 的单独分支（`src/index.ts:1921,2655,2687-2690`）。52 名字中含 accounts/yolo/task/coordinator/quit 等未列菜单的别名/入口。

### 4.3 内置技能、动态命令与菜单的三个不同集合

8 个 core 内置技能名是 **simplify、debug、make-plan、verify、code-review、deep-research、fewer-permission-prompts、run-skill-generator**（`src/skills/bundled.ts:122-177`）。用户可调用匹配默认开启，名字/slug/namespace:slug 比较不区分大小写（`src/skills/skills.ts:70-76`）。Ink 在已知命令、自定义模板之后尝试技能（`src/index.ts:2446-2471`）。因此未禁用/未覆盖时，除与 simplify 重合外，额外 7 个已知 slash 名字可用，即固定 52 + 7 = 59；这不是任意用户环境下的恒定总数。

自定义 Markdown 命令：插件 < 用户 < 项目覆盖；替换 `$ARGUMENTS`、`$1/$2/...`（`src/commands/custom.ts:48-63`）。技能启动按用户/项目路径加载，同名/realpath 去重，插件命名空间，磁盘定义可覆盖 bundled；路径条件和文件访问时发现也会增加可用集（`src/index.ts:767-786,1160-1180`；`src/skills/skills.ts:124-136`；`src/skills/discover.ts:72-114`）。精确动态名字只能由配置/发现结果决定，快照不包含用户运行目录，不能编造清单。

App 的 `COMMAND_META` 是 **49 个菜单名字**，其中 security-review、debug-session、dod 在本轮核对的固定 handler/builtin/core skill 集合中没有对应实现；可被用户自定义命令或技能提供，但不是开箱即用的固定路径。菜单不会自动产生 handler（`src/tui/app/App.tsx:37-45,572-573`；`src/commands/builtin.ts:11-98`；`src/skills/bundled.ts:122-177`；`src/index.ts:2446-2504`）。完整固定命令计数不能拿 49 或帮助文案代替。

### 4.4 入口能力矩阵

| 路径 | 输入/命令/运行方式 | 关键差异 |
| --- | --- | --- |
| argv 一次性 prompt | 建 durable store→SessionStart→UserPromptSubmit→addUser→keepAlive scheduler→finished | 无完整 slash 路由；已有输入先加入，scheduler user 回调为空；等后台工作结束；仍存审计和工具轮检查点；`src/index.ts:1704-1748` |
| Ink TTY | stdout.isTTY 且非 Deck managed；App→scheduler；index 提供完整命令 | 有审批/选择器、图像输入、检查点/回退、账户切换重试和完整 UI；`src/index.ts:1753-1755,1817-1916` |
| 非 TTY / Deck managed | runRepl→scheduler；自定义 command 只特判 quit/recovery/resume | 基础 dispatch 的 9 名字 + recovery（1）+ resume（1）= **11 个固定名字**；未接入 Ink index 那批 builtin/动态 slash 路由。Deck managed 输入可走桥接，不随面板关闭结束 Agent；`src/index.ts:2622-2669`；`src/repl.ts:82-105` |

同名命令在不同入口的模型持久化/选择器等也不完全相同。迁移规格应逐条注明来源入口，不以“存在一个命令函数”推出三条入口都兼容。

## 5. 启动、单轮及流式调用链

### 5.1 组装顺序

`main → 退出/信号兜底 → dotenv/obs → 版本/操作员早退 → 参数与 workspaceRoot → 语言/旧目录迁移 → profile/凭据/首次引导与信任 → registry + MCP + LSP → 记忆加载/验证/固定注入 → 插件/agent/command/skills → system prompt/环境补充 → PermissionGate + Session + ToolContext → hooks → taskManager → BackgroundRuntime → durable store/recover → SessionScheduler → UI/REPL/一次性`。

调用点分别为 `src/index.ts:177-360,409-516,598-667,675-876,948-1051,1107-1135,1212-1283,1704-1755,1839-1916,2635-2653`。MCP 初始化在 UI 绑定之前，elicitation 未有 UI 端口时拒绝；环境和 repomap 后台构建结果排队，不任意插入工具调用对中间（`src/index.ts:624-637,901-908,1562-1563`）。

权限模式不是 Session.mode 的简单别名：有效优先为 session plan > yolo > 运行覆盖 > loaded defaultMode > auto；settings 低到高 user < trusted project < local < CLI < enterprise，规则数组合并后由 deny>ask>allow 评估（`src/index.ts:948-977`；`src/permissions/settings.ts:95-103`）。配置每种资源有自己的发现规则，不能用这条 settings 优先级概括 MCP、skills、Config 工具等全部资源。

### 5.2 单轮执行

1. scheduler.boundary 消费输入：调用 user hook；被阻止的不加入 Session；再交付已在 inbox 的后台数据，成功保存后确认（`src/agent/session_scheduler.ts:92-107`；`src/agent/background_delivery.ts:9-22`）。
2. runTurn 构造单轮 WaitControl（根任务才有），更新工具 ctx 的 signal/model，开始模型/工具循环；主代理默认无轮数上限，可用 DAO_MAX_TURNS 覆盖（`src/agent/loop.ts:153-194`）。
3. 每个工具轮请求前按预算提醒/硬停、85% 主动压缩，再 onBoundary 消费追加输入、代理信箱、反思、MCP/环境队列；API tools 由当前模式/可见性重新计算（`src/agent/loop.ts:418-479`）。
4. 请求返回后先保存清洗过的 assistant。无工具调用就检查点并 completed；有工具则 durable 下先存调用意图所在的历史，再裁决和执行（`src/agent/loop.ts:628-642`）。plan 还会对工具名作实际允许表核对，不能只靠 prompt（`src/agent/loop.ts:647-679`）。
5. 工具前 hook **只跑一次**，updatedInput 后的最终参数同时用于权限、安全检查、审计及执行；deny 返回工具结果，ask 合批审批；工具异常也转 Error 工具结果（`src/tools/execute.ts:50-99,140-225`）。
6. capability 为 read/network/plan 的批次可并行，上限 8；write/exec 是串行屏障，结果按调用原顺序返回；已发出的批次用 allSettled 收齐后才传播存储等失败（`src/tools/execute.ts:34,108-111,230-270`）。这里 plan **并非无副作用**：Config/MemoryWrite 仍能写存储，迁移不能把标签解释成绝对纯函数（`src/tools/config.ts:24,53-90`；`src/tools/memory_write.ts:31-49`）。
7. tool messages 成对追加；TaskWait 必须单独调用、结果和等待状态存档后才 commit并返回 waiting；余下普通工具轮继续诊断/进度/反思与存档（`src/tools/execute.ts:118-122`；`src/agent/loop.ts:673-696,721-793`）。

headless 第一批必须包含 TodoWrite，缺失时整批拒绝；只检查调用是否包含 TodoWrite，并不先证明计划质量（`src/tools/execute.ts:126-136`）。Bash 崩溃特征可能重置该要求（`src/tools/exec_shell.ts:399-401`）。

### 5.3 流式协议、usage 与重试层次

统一 client 输出 content/reasoning/tool_call 等 delta，工具参数按 index 累积为完整 AssistantMessage；SSE 分块 parser 保留未完整帧；Responses 路由桥接保留函数调用/输出及 response items（`src/client/client.ts:213-264,380-411`；`src/client/sse.ts:7-20`；`src/client/responses.ts:11-47,85-125`）。工具调用时的 reasoning_content 有回传规则，assistant null content 转空串；请求输出上限依模型属性裁剪，默认请求 128000、特殊空截断重试 256000，但并非每个 provider 真支持该值（`src/client/client.ts:72-107`；`src/agent/loop.ts:231,568-590`）。

client 看门狗默认 240 秒，只有解析出实际 delta 才重置；未产出时可重试网络/可重试状态默认 2 次，之后非流式兜底一次；已有内容后不从头重试，避免重复。用户 abort 返回已累积部分；有产出后的 idle 超时显式报错。429 无 Retry-After 上抛，背景查询 529 不重试（`src/client/client.ts:122-141,271-376`）。注意源码实际 delay 是 `600*(attempt+1)+jitter`，不能把注释“指数退避”直接作为测试 oracle（`src/client/client.ts:129-131,349-353`）。

loop 再处理上下文超限（压缩最多 2 次）、根代理限流（交互选择等待/切账户/中止；无人输入时有上限退避）、一般网络/过载原地再试一次，持续失败 ModelUnavailableStop；不自动替换业务主模型（`src/agent/loop.ts:258-264,333-410`）。子代理传 `background:true`，因此根层额外重试/询问分支不适用（`src/agent/runAgent.ts:444-464`）。空响应还有独立的有限重试与 tool_choice 不支持时的降级路径（`src/agent/loop.ts:491-605`）。

usage/费用由 Session 记，cache 审计包括 model/system/tools/tail 前缀指纹；默认成本阈值只提醒，DAO_MAX_BUDGET_HARD=1 才硬停（`src/agent/loop.ts:269-315,418-423`；`src/index.ts:1061-1062`）。缓存保证是消息/工具序列稳定的设计目标，不是本轮测得的命中率。

## 6. 调度、后台任务和子代理

### 6.1 四类状态必须分开

| 状态层 | 枚举/判据 | 证据 |
| --- | --- | --- |
| 会话 scheduler | idle/running/waiting/paused/closed/recovering | `src/agent/background_types.ts:40` |
| 单轮结果 | completed/waiting/interrupted/failed | `src/agent/background_types.ts:35-39` |
| 执行 snapshot | running/canceling/completed/failed/canceled/interrupted/unknown；unknown 不算 isTerminal | `src/agent/background_types.ts:1,41` |
| 手工 task | 纯状态记录，无执行器；不能与 background agent/shell 的运行保证混同 | `src/tools/task_create.ts:4-15`；`src/agent/tasks.ts:115-116,154-168` |

TaskManager 管代理、monitor promise 和手工条目；ProcessManager 管 Shell。BackgroundRuntime 订阅二者，按 taskId/runId/sessionId 汇合执行事件（`src/index.ts:1248-1251`；`src/agent/background_types.ts:3-29`）。TaskList/Get/Output 查询 TaskManager，不是所有 Shell 的通用查询；BashOutput/KillShell 查询 ProcessManager；TaskWait 则等待统一 runtime。

### 6.2 调度与等待精确语义

- submit 追加 inputs、释放旧等待、清 lastError 后调度；active/scheduled 防重复 pump，microtask 发起，工具轮 boundary 才合并输入。因此运行时可接收新输入，但不会与未闭合工具消息任意交错（`src/agent/session_scheduler.ts:58-63,78-107`）。
- TaskWait 去重后只接受 1–32 个**当前后台执行**，固定对应 runId；未知/中断拒绝等待，manual/foreground 不在 runtime 执行集；any 等任一成功、all 等全部成功，失败/取消/attention 可提前唤醒（`src/agent/background_runtime.ts:106-126`；`src/tools/task_wait.ts:3-11`）。
- WaitControl 先 prepare→暂存 consumed→存会话→commit；存失败 rollback，不错误消费后台结果（`src/agent/background_runtime.ts:162-183`；`src/agent/loop.ts:682-696`）。
- 后台 progress/started 只更新运行状态，attention message 和终态等形成 inbox 事件；eventId 去重；投递内容作为“后台数据，非用户指令” user 消息，save 成功后 acknowledge（`src/agent/background_runtime.ts:73-104`；`src/agent/background_delivery.ts:5-22`）。
- completed 后，普通交互 scheduler 回 idle；keepAlive 的一次性/管道调度在仍有后台执行时自动登记 any 等待，最多取 32 个继续等待，不通过 sleep/poll 驱动模型（`src/agent/session_scheduler.ts:127-139`；`src/index.ts:1733-1739,2637-2648`）。
- pause 清输入队列、释放等待、abort 当前轮、保存 paused，但**没有直接 cancelAll 后台任务**；close 则 abort、清队列、取消订阅并 dispose runtime（`src/agent/session_scheduler.ts:65-76`）。用户新输入可从 paused 再唤起；恢复时未知执行/未决操作仍受持久工具门拦截（`src/agent/session_scheduler.ts:58-63,109-145`；`src/session/durable_store.ts:188-195`）。
- help/cost/tasks/status/context/session/diff/files/audit/copy/export/theme 这 13 个查询/显示命令不暂停等待；无参 resume/recovery 也不暂停，其余合法 slash 先 pause→settled（`src/commands/scheduling.ts:1-13`；`src/tui/app/App.tsx:501-505`）。不能按“以 / 开头就全打断”迁移。

### 6.3 子代理调用链与限制

`Agent.handler → 选择 agentDef/模型/隔离 → taskManager 注册前台或后台执行 → runAgent async generator → 子 Session/工具集/权限门 → 共用 runTurn → 逐消息 yield → lifecycle/summary/handoff → task result/event → runtime → scheduler边界`。调用证据：`src/tools/agent.ts:175-260,262-388`；`src/agent/runAgent.ts:175-235,378-480`；`src/agent/agent_lifecycle.ts:38-91`。

内置类型 **general-purpose、explore、plan、verify**，另有 fork 的内部定义；磁盘 agent（插件<用户<项目）可同名覆盖内置（`src/agent/bundled_agents.ts:4-10,32-38,68-73,109-117,229-234`；`src/agent/agent_defs.ts:217-231`；`src/index.ts:744-751`）。explore 默认 inherit，可被 DAO_EXPLORE_MODEL 覆盖；verify 强制 background；不能将 “explore 是只读”仅由自然语言说明推出所有 Shell 都结构禁止——它仍有 Bash，依靠权限/指令限制（`src/agent/bundled_agents.ts:32-59,109-117`）。

普通子代理过滤 Agent、AskUserQuestion、TaskStop、TaskWait；异步再用明确白名单，MCP 等不在该白名单。agentDef 的 tools/disallowedTools 再裁剪；记忆 agent 可补回记忆必需工具（`src/agent/agent_tools.ts:9-89`；`src/agent/runAgent.ts:22-26,326-340`）。**fork/useExactTools 路径复用父 registry，跳过该普通解析**，Agent 和 TaskWait 还有深度自检；不能笼统声称每条子代理路径都经过同样工具过滤（`src/agent/runAgent.ts:183-191`；`src/tools/agent.ts:175-178`；`src/tools/task_wait.ts:9-11`）。

单个任务或最多 20 条 tasks scatter-gather，默认最多 10 并行，其余 worker 队列；子代理默认独立轮数 **500**，优先调用覆盖>定义>DAO_SUBAGENT_MAX_TURNS，与主 DAO_MAX_TURNS 分离（`src/tools/agent.ts:129-136,399-415`；`src/agent/turn_budget.ts:1-6`）。工具描述中遗留“200”等文字不能压过实现函数。

fork 继承过滤后的父对话并复用工具/系统提示；runtime 明确拒绝 fork+model/mode，worktree/remote 优先选择另有分支。remote 目前仍创建 worktree，注释明确尚非独立进程远程执行，不应把 isolation=remote 写成完整远程能力（`src/tools/agent.ts:189-230`）。isolate 改动/新提交保留待 review/merge，无改动清理；不自动合并分支（`src/tools/agent.ts:420` 起；`src/agent/worktree.ts:35-76`）。

worktree 从 **HEAD** 新建分支，不复制父工作区未提交文件；辅助函数还会向根 `.gitignore` 补 `.dao/`，因此隔离创建本身也可能改变主工作区的忽略文件。保留判据包括 baseSha 后新提交，并非只检查 dirty（`src/agent/worktree.ts:12-18,35-47,62-75`；`src/tools/agent.ts:424-428`）。

前台代理创建真实 AbortController 并接父信号；Ctrl+B 可在工具边界转后台，接续消息而不让原执行与新执行同时跑；正常/异常解绑监听并 settle（`src/tools/agent.ts:262-370`）。前台 Bash 也可通过 ForegroundRegistry 转后台（`src/tools/exec_shell.ts:218-248,397-398`；`src/tui/foreground_registry.ts:5-27`）。

子代理持久检查点存 messages + agentType/description/worktree/model，并按 durableRunId 隔离工具 scope；legacy JSONL/meta 仍写，但部分为 fire-and-forget，不能视为同等强保证（`src/agent/runAgent.ts:368-404,423-431`）。恢复有定义/模型/路径/未决操作校验；explore/plan one-shot 禁恢复；恢复是新的 runId 继续同 taskId，而不是重放未知工具（`src/agent/resume_agent.ts:84-126`；`src/agent/agent_tools.ts:31-32`；`src/agent/tasks.ts:285-292`）。

后台活动摘要每30秒从最近消息提取工具数/末次工具/文本片段，当前实现不另调LLM；进度tracker的tokenCount仍固定0，不能把UI进度当准确token计费（`src/agent/agent_summary.ts:14-44`；`src/agent/agent_tools.ts:118-138`）。

auto 模式有子代理 handoff 转录安全复核，但这是**执行后审查**，不等于执行前权限门，也不是业务正确性验收（`src/index.ts:1316-1346`；`src/tools/agent.ts:353-360`）。

## 7. 取消、崩溃恢复和清理

### 7.1 取消不是回滚

App Esc 在忙碌/审批/问题分支 abort 并 scheduler.pause；修改历史的命令等 settled 后才运行（`src/tui/app/App.tsx:985,1043,1083,1105-1112,501-505`）。runTurn 在请求/工具边界检查 signal；若 assistant 已存 tool_calls 但未执行，会补齐每个取消结果；异常时 repairToolPairs、标记该 scope 未知操作并保存（`src/agent/loop.ts:153-173,418-434,635-643`）。

TaskStop 对真实任务先 canceling 并 abort，执行器 settle 后才 canceled；不可取消的 adopted promise 不伪装成功停止。manual 直接 canceled。取消不撤销已经写文件或做过的外部操作（`src/agent/tasks.ts:124-131,154-162`；`src/tools/task_stop.ts:8-14`）。Shell 取消与进程树必须独立核验，当前前台/后台大量采用负 pid 的 Unix 进程组信号；Windows 身份适配并未替换这些代码（`src/tools/exec_shell.ts:193-211`；`src/tools/process_manager.ts:41-49,309-337`；`src/tools/shell_runner.ts:74-88`）。

### 7.2 持久协议与崩溃分界

| 层次 | 必须保留的现行语义 | 证据 |
| --- | --- | --- |
| durable DB | schema v2，WAL/FULL/foreign_keys/busy_timeout，自检生效；工作区 canonical 身份、同会话 owner 排它及 epoch fencing；网络文件系统拒绝启用 | `src/session/durable_store.ts:48-98,108-129` |
| 工具日志 | beforeTool 先写 started；同 scope/id 的 committed 返回缓存结果；已有未决或 unknown 执行阻止新有副作用调用；afterTool 记完整 ToolMessage；崩溃 started→outcome_unknown | `src/session/durable_store.ts:188-219`；`src/tools/execute.ts:91-99` |
| Hook 日志 | PreToolUse 本身有执行意图/结果，避免恢复后自动重复运行有副作用 hook | `src/tools/execute.ts:148-155` |
| Shell runner | manifest/capability、独立 detached runner、grant(epoch)、start.claim 排它、文件日志与终态回执；runner 才执行命令，避免 parent crash 后重启重复运行 | `src/tools/managed_shell.ts:170-239`；`src/tools/shell_runner.ts:30-51,90-136,137-185` |
| runner 接管 | 校验 host/boot/pid/start、runId/epoch/token；重连失败转 unknown，不编造已死/已成功 | `src/session/process_identity.ts:35-74`；`src/tools/managed_shell.ts:73-168` |
| 代理恢复 | 在进程内运行的代理失去原执行器后 running/canceling→interrupted，恢复转录但不自动重放，需明确继续 | `src/session/recovery.ts:29-63`；`src/index.ts:1369-1385` |
| 消息修复 | 已知工具结果从 DB 补齐；有意图/无日志分别显示“结果未知”或“未执行”，均不自动执行 | `src/session/recovery.ts:7-27` |
| 事件投递 | durable eventId + delivered 标记，save 时与消息/后台 checkpoint 一起确认，内存 acknowledge 在后 | `src/session/durable_store.ts:133-172`；`src/agent/background_delivery.ts:9-22` |
| 外部结果附件 | 记录 hash/文件存在性，缺失附件变为恢复核实项 | `src/session/durable_store.ts:173-184`；`src/session/recovery.ts:65-70` |

bindStore 必须先绑定 durable、recoverBackground、绑定 background checkpoint、repairToolPairs、再保存；调度器随后 recover（`src/index.ts:1273-1282,1798-1799,1905-1907`）。恢复状态如果原来 running/paused、有未知/中断/未决或待投递事件则暂停；只有安全的 waiting 可恢复等待（`src/agent/session_scheduler.ts:40-51`）。

`/recovery resolve <scope> <toolCallId> <解释>` 处理未决；`decide <taskId> <completed|failed|canceled> <证据>` 处理 unknown；`continue <taskId> <指令>` 显式继续 interrupted 代理。决定写入用户消息并持久保存，不是模型自行将 unknown 猜成 completed（`src/index.ts:1284-1306,1369-1371`）。RuoCun 不迁移 DAO 旧会话的既定边界不免除这些 RuoCun 自身的恢复语义。

`markDone` 看 pending wait/event、running/canceling/unknown/interrupted 或 paused 决定 done，正常退出不一定置 true；v2 JSON/meta 导出故意 done:true 防旧程序接管，loadState 优先 DB（`src/session/log.ts:94-138`）。不能只读导出 JSON 的 done 判断当前工作已经完成。

### 7.3 三种“检查点”和清理

- **消息/DB checkpoint**：每工具轮与重要边界持久化；**代理 checkpoint**：子 messages/meta；**工作区 checkpoint**：可选 `.dao/shadow.git`。第三者默认关闭，DAO_NO_CHECKPOINT 最高优先，用户设置可开启；超时/太慢则降级停止后续快照；restore reset--hard 只作用影子库工作树，不等于 DB 恢复（`src/session/checkpoint.ts:33-106`；`src/agent/runAgent.ts:400-404`）。
- `/restore` 与 `/rewind ... code` 在回退前先存自动快照；普通 rewind 只截断对话；来源没有承诺回滚已发网络请求/数据库事务（`src/index.ts:2200-2226,2458-2465`）。
- 分支退出路径调用 SessionEnd、DB 备份清理、MCP close、LSP dispose、markDone；最外 finally 关闭 Deck/scheduler、cancelAll tasks、dispose runtime，Shell 按 keep-background detach 否则 reset，关闭 activeStore/readline（`src/index.ts:2577-2584,2672-2693`）。不能由“close scheduler”推断已等待所有取消的 OS 进程退出，见第 9 节实验。
- 启动 maybeCleanup 每日最多一次，默认清理 30 天前 spill/subagents/sessions，worktree 使用不带 force 的安全回收，再 prune（`src/agent/cleanup.ts:9-19,25-45,52-75`；`src/index.ts:946`）。它目前按 mtime 清 session 目录，没有显式 durable owner/pending 状态检查；迁移前须将活跃 runner/旧会话的清理边界列入实验。

## 8. 扩展与辅助功能的运行边界

1. **项目信任**：项目 permissions/settings.local/hooks 受 trustProject 门控，MCP/LSP/DAO 指令/skills 各自仍按其加载点读取；不能把“未信任目录”概括成所有项目扩展都禁止（`src/index.ts:619-623,650-655,744-772,948-955,1214-1218`；`src/project_doc.ts:29-46`）。品牌重命名后的兼容路径另需决定。
2. **Hooks**：根事件有 SessionStart、UserPromptSubmit、PreToolUse、PostToolUse、SessionEnd；子代理还有 start/stop hook 注册器（`src/index.ts:1212-1244,1742`；`src/agent/agent_hooks.ts:18-79`）。解析类型枚举含 prompt/Agent/http/callback/function，但 runHooks 只执行 command，其余跳过；默认 timeout 30 秒，输出解析 code=2/block/context/updatedInput/decision（`src/hooks/hooks.ts:5,30-49,108,123-143`）。不能将类型声明当作已实现执行后端。
3. **MCP**：工具变更在回合边界通知，关闭/重连会 unregister prefix；plan 从请求表及实际 dispatch 双层排除 MCP；stdio 环境与 transport 生命周期也需要适配（`src/mcp/mcp.ts:147-162,286-364,403-417`；`src/tools/tools_for_mode.ts:19-26`；`src/agent/loop.ts:647-664`）。
4. **记忆/反思**：project/user/knowledge 独立；knowledge 只保留 origin 同项目或 locked，stale 不注入、changed 标记；小于 50 记忆时全句注入，较多时高价值全文+长尾索引；来源 hash 验证不是记忆真实性证明（`src/index.ts:704-732`；`src/memory/store.ts:8-35`；`src/memory/validate.ts:9-17`；`src/memory/inject.ts:46-79`）。统一回合末反思默认关闭，需 reflect-memory；challenger 另开关；一次性 prompt 不运行这些反思；启动合并可以后台 LLM（`src/index.ts:286-292,683-702,1566-1575,1659-1675`）。
5. **压缩**：估算约字符/3，85% 阈值；保持首 system、既有摘要原文追加、本轮 Todo pinned；摘要失败变硬截断并明确提示缺细节；不是保证完整上下文无损（`src/agent/compact.ts:3-24,36-76`）。
6. **Shell/文件辅助**：外部路径读写端口、符号路径/原子写/文件锁、编辑旧版本保护；Bash 输出溢写文件、前台无自动 timeout、命令崩溃/数据库文件执行前备份与退出清理、包管理器中断恢复；沙箱仅当前 macOS/Linux 分支，Windows 是补齐域（`src/tools/read_file.ts:45-58`；`src/tools/write_file.ts:39-76`；`src/tools/exec_shell.ts:103-127,167-248,306,354-440`；`src/tools/sandbox.ts:41-65`）。
7. **Agent Deck**：本地 HTTP 桥接复用 scheduler/session/runtime/权限状态，127.0.0.1 动态端口、随机 token，拒绝 origin；可以观察、提交、暂停、回答 attention，managed 模式无本地 readLine；不是第二套 agent 执行器（`src/agent/deck_bridge.ts:29-47,70-92,111-156`；`src/index.ts:1254-1270,2622-2625`）。
8. **通知与桌面能力**：TUI 转录、标签 attention、桌面通知、防休眠、图像粘贴和选择器均属外部可观察功能，需要 Windows 分别验；源码路径盘点见附录 A，标题/焦点和 welcome 本地覆盖详见下节（`src/tui/app/App.tsx:244-338,804-869`；`src/tui/tab_attention.ts:19-42`；`src/index.ts:1910-1913`）。具体平台支持不能混同：桌面通知有 Windows PowerShell NotifyIcon 分支（`src/tui/notifier.ts:25-58`）；剪贴板图片当前仅 macOS，Windows/Linux 返回 null（`src/tui/imagePaste.ts:1-8`）；防休眠仅有 macOS/Linux 分支，Windows 为 no-op（`src/tui/wakelock.ts:5-17`）；keychain 当前也只在 macOS/Linux 标 available（`src/config/keychain.ts:17-56`）。这些是 Windows 补齐研究的明确入口。

9. **Monitor 与一般代理的差异**：Monitor 是 `processManager.start` 的旧式后台 Shell 加 `taskManager.launch` 的 promise 包装，内部有定时 poll/批次 flush，并非模型反复调用 BashOutput；任务枚举中 promise 对外执行快照仍标 kind=agent。取消/超时回调请求 kill 后就 finish，未等待进程退出；崩溃恢复也没有代理定义/消息检查点，不能当普通 runAgent 的等价耐久任务（`src/tools/monitor.ts:48-115`；`src/agent/tasks.ts:115-120,169-180`；`src/session/recovery.ts:45-51`）。后续须核对它在运行时的任务/进程重复通知和恢复限制，不把“所有后台任务都能同样恢复”写入规格。

## 9. 本地覆盖层与静态待核差异

### 9.1 冻结覆盖层的 20 个文件全部处置

快照包含 12 个已跟踪修改和 8 个未跟踪源码文件，均属于统一参照。本表只解释现行字节能支持的行为，不据此宣称已有迁移决定。

| 文件/组 | 可观察差异与边界 | 当前快照证据 |
| --- | --- | --- |
| `src/session/process_identity.ts`（M）及 `.test.ts`（新增） | Windows PowerShell CIM 查询 boot/CreationDate UTC ticks；校验正整数 PID；查询不存在返回 null、权限/查询错误仍抛；保留 host/boot/start 身份核对 | `src/session/process_identity.ts:11-74`；测试文件仅为场景说明，未运行 |
| `src/config/profiles.ts`（M） | 新增 VISION_MODELS Set 兼容旧 UI 导出，底层仍源于 VISION_MODEL_IDS，未新增一个独立模型来源 | `src/config/profiles.ts:118-130` |
| `src/tui/brand.ts`（新增） | 固定“若存 Code”和“绵绵若存，用之不勤。”；展示品牌不等于 package/bin/数据路径都已改名 | `src/tui/brand.ts:1-3`；`package.json:2,10-12` |
| `src/tui/Welcome.tsx`（M）及 `.test.tsx`（M）、onboarding/Onboarding.test.tsx（M） | 欢迎卡片最大146列，图像左上锚、列宽不够退紧凑文本；深色才留角色位，真实 cwd/version 保留；测试期望同步品牌 | `src/tui/Welcome.tsx:9-33,52-124`；测试均未运行 |
| `src/tui/app/run.tsx`（M） | 深色/truecolor/双TTY/非screen-reader/非skipBanner才探测图形；terminalReports 代理 stdin；创建 welcomeMotion；诊断只写展示状态；退出 dispose 并 flush | `src/tui/app/run.tsx:15-60` |
| `src/tui/app/types.ts`（M） | 增加 staticWelcome、welcomeMotion、ownedViewport 端口，承载 UI 适配约定 | `src/tui/app/types.ts:55-69` |
| `src/tui/app/App.tsx`（M）及 `.test.tsx`（M） | Windows/有 motion 首帧 Static；draft/提交/历史/模态/后台活动阻止空首页动画；测量静态行和动态区；ownedViewport resize 才清屏重放 Static；普通共享 Shell 不启动该重建 | `src/tui/app/App.tsx:169-213,350-351,483-500,1380-1443,1804-1820` |
| `src/tui/mascot.ts`、`.test.ts`（新增） | 空首页才推进动画；focus/input/task/modal/resize/dispose 暂停；SIXEL 帧单独写图像坐标，不调用模型；位置不明停止猜锚 | `src/tui/mascot.ts:36-43,52-61,85-107,144-168` |
| `src/tui/mascot_frames.ts`（新增） | SIXEL 字符串、时间线及图像元数据已嵌入；文件头记录外部来源及 hash，原始资产不在这份快照中 | `src/tui/mascot_frames.ts:1-21` |
| `scripts/generate-mascot-data.mjs`（新增） | 从外部 manifest/frame 文件生成上述嵌入资源；默认路径指向邻接预览目录，快照可运行资源不等于资源可完整重建 | `scripts/generate-mascot-data.mjs:8-14,22-53` |
| `src/tui/terminal_reports.ts`、`.test.ts`（新增） | 过滤 DA/单元格/光标报告，保留焦点/粘贴/普通键；query600ms、分片超时、modified-F3歧义保护、raw mode代际与backpressure/释放 | `src/tui/terminal_reports.ts:24-28,79-147,207-261` |
| `src/tui/tab_attention.ts` 及 `.test.ts`（M） | 标题“任务 · 若存 Code”，空标题回品牌；focus 恢复标题，attention/completed 双色标记；控制字符清洗与24字符截断 | `src/tui/tab_attention.ts:12-42,52-67` |
| `patches/ink+7.0.5.patch`（M） | 当前 patch 是宽度任意变化时按重排后的物理行数 eraseLines+log.reset；冻结差异表明原先“overflow路径带staticOutput”patch已被替换，不能假定两补丁都在 | `patches/ink+7.0.5.patch:5-21`；覆盖层差异见归档 tracked-working-tree.patch |

### 9.2 应先实验、再决定 oracle 的差异

以下均为**静态推断/文案差异**，未运行复现；不是本研究直接要求修复的清单，也不扩大范围。完整复现目标仍适用，但规格需要区分既定功能与来源瑕疵。

| 编号 | 静态证据组合 | 必须先回答的 oracle 问题 |
| --- | --- | --- |
| O1 | argv 未小写归一化却比较 Schedule/Skill，说明给小写；App/index 保留名字、/Config 大写，help 说 /config | `src/index.ts:197,229,263,1918,2239`；`src/tui/app/App.tsx:572-573`；`src/commands/commands.ts:74`：对两种大小写分别期望“识别”还是历史兼容别名？先只读命令探针，禁止误发真实 API |
| O2 | /permissions 前置读分支无条件 return，后文 add/remove 永远碰不到同名路径 | `src/index.ts:2118-2122,2410-2444`：入口无规范化可绕过前置同名判断，属于静态不可达；验收应保留实际只读还是兑现文案的管理能力，由规格决定 |
| O3 | 菜单49、固定52、core8，三套名单不同；3菜单名缺内置 handler | 第4节证据：禁所有外部自定义后，security-review/debug-session/dod 实际是否未知；不要由动态技能偶然存在误判内置通过 |
| O4 | CronCreate 文案默认session-only/一次性自删，实现仅显式 false 拒绝，省略仍走OS持久；false recurring仅加“请手动删”prompt | `src/tools/cron_tools.ts:11-44`：持久/会话定时及一次性语义，迁移应按明确规格设 oracle，不照抄互相矛盾的注释 |
| O5 | isolation=remote 当前worktree等价；fork精确工具池绕过普通子代理过滤 | `src/tools/agent.ts:189-223`；`src/agent/runAgent.ts:183-191`：应如何记录支持级别/工具可用性，哪些限制要成为硬行为 |
| O6 | Windows 身份新增，但 endpoint仍临时`.sock`，目录fsync/start.claim、负pid信号及沙箱都保留Unix假设 | `src/tools/managed_shell.ts:17-29`；`src/tools/shell_runner.ts:74-105,137-185`；`src/tools/sandbox.ts:41-65`：Windows IPC、进程树、取消、断线接管各需单独实现验证，不能只跑身份测试 |
| O7 | cleanup按mtime递归清 sessions，无owner/runner豁免；调度器close先dispose再cancelAll，取消不await；退出早期注释说headless保Shell，finally却reset除非keep | `src/agent/cleanup.ts:9-19,52-74`；`src/index.ts:177-195,2577-2584,2684-2693`：保留后台/退出/清理的真实承诺，以强制崩溃和长任务场景决定；只记录设计意图不等于执行成功 |
| O8 | Config文案说enterprise>user>project，读handler实际project??user，写固定user，未访问enterprise | `src/tools/config.ts:18-23,33-50,53-90`：是兼容handler的实际行为，还是统一配置语义；另一个扩展研究票可细化 |
| O9 | 预声明“subagent不能问人/再派发”，普通过滤与fork精确工具不同；worktree子ctx只覆盖workspaceRoot，cwd由spread继承 | `src/agent/agent_tools.ts:9-29`；`src/agent/runAgent.ts:183-191,405-415`：必须做fork及嵌套EnterWorktree场景的路径/权限测试，不能把描述当硬墙 |
| O10 | 冻结改写的Ink patch只包含resize修正；Welcome角色数据来源为快照外资源；新增测试未执行 | `patches/ink+7.0.5.patch:1-21`；`src/tui/mascot_frames.ts:1-11`：验证溢出/缩放及资源生成闭环，静态帧存在只证明可引用，非完整资源构建可复现 |
| O11 | OS定时构造器把传入的daoBin直接作为命令；CLI/工具传process.execPath；package的Node入口与Bun独立二进制的execPath语义不同 | `src/schedule.ts:9-10`；`src/index.ts:236`；`src/tools/schedule_tool.ts:37`；`package.json:10-12,23-28`：需分别验证Node安装/源码开发/Bun bundle的定时启动argv，不能只测crontab字符串 |
| O12 | looksFailed非0退出正则要求`[exit N]`，前台Bash实际拼`[exit N,运行 ...]`；屏障级联依赖looksFailed | `src/tools/execute.ts:37-38,270-272`；`src/tools/exec_shell.ts:406`：静态格式不完全匹配，需用一批“失败命令→写入/下一命令”验证实际跳过、审计、UI失败识别的oracle |

## 10. Python 对应原则与运行时候选路线

本节为候选建议，受 ADR-0001 的纯 Python核心、职责/关系保留及 Windows优先约束；不选择最终UI库、不实现产品、不修改对应表。

1. 保留 `ruocun.__main__/repl` 作为入口与组合根，继续保留 agent/client/tools/session/permissions 等目录，不把调度、存储和渲染揉成一个“聊天循环”。TS命名 `runAgent` 可变为 `run_agent.py`，语义和调用方向保留。
2. 主候选：单进程异步事件循环管理 SessionScheduler、后台事件、模型流、普通子代理；持久 Shell 继续独立 runner 进程；阻塞文件/SQLite工作采用明确串行适配，不允许暂停/恢复时绕过工具日志。备选“每回合启动进程”会显著改变常驻队列/共享registry/缓存/owner与前台转后台语义，只有验证出必要性后再选。
3. 先定义类型契约：TurnOutcome、ExecutionSnapshot/Event、WaitHandle、ToolContext、Tool/ToolRegistry、ApprovalGate、SessionStore/DurableStore、ForegroundRegistry、TurnEvents。保持 sessionId/taskId/runId/toolScope/toolCallId/eventId/epoch 的不同作用，不合并成一个 task_id。
4. 异步 queue/condition/future 应承载事件唤醒和取消；保留“仅boundary追加消息”“写前执行意图”“保存后ack”“取消请求和退出确认不同”等不变量。Python await/task cancellation 不自动提供这些业务保证。
5. `sqlite3` 可作为存储候选，保留事务、owner/epoch、schema版本和附件校验语义，RuoCun 自有格式无需兼容旧DAO数据库。Python库能打开SQLite不代表已证明 WAL/FULL、崩溃落盘和网络盘拒绝策略正确。
6. Windows运行层应有独立的 process_identity/process_tree/runner_ipc/terminal_input 边界，Unix也有对应适配；不能把 `kill(-pid)` 改成 `terminate()` 就宣称进程树取消兼容；Shell名称是否保留 Bash 作为扩展契约、具体执行器采用何种shell须另定。
7. 保留工具外部名字、参数、capability、审批、延迟发现、MCP名字约定；schema语言绑定可替换，但应由同一个定义生成模型JSON schema和运行校验，避免两份参数表漂移。工具说明中的历史数字不进入固定常量。
8. UI经 TurnEvents / scheduler / approval端口适配，品牌/动画/终端报告不触碰模型消息和工具执行状态；同一份输入流只能有一个协议解码拥有者。ownedViewport清屏权限独立于共享Shell，图形失败退文字；UI库候选需另票真实Windows窗口/缩放验证。
9. 保留config/skills/hooks/MCP发现和覆盖的**各自**算法；不能为了统一Python配置框架把既有优先级悄悄改掉。兼容瑕疵单独登记 oracle 决定，既有接口与修正结果都有证据。

### 10.1 已核验的Python平台事实（不是选型完成）

2026-11-05 查阅Python官方文档：Windows下asyncio默认Proactor支持subprocess，Selector不支持；Windows事件循环不支持 `add_signal_handler` 和 `create_unix_server/create_unix_connection`。所以来源Unix socket/信号处理路径不能原样照搬。来源：[asyncio平台支持](https://docs.python.org/3/library/asyncio-platforms.html)。

官方subprocess文档提供 `create_subprocess_exec/shell` 与 Process，但shell参数转义由应用承担；它没有替本产品定义“跨重启接管/防重复执行/进程树确认”。候选IPC与runner必须另证。来源：[asyncio子进程](https://docs.python.org/3/library/asyncio-subprocess.html)。

`sqlite3` 是Python对SQLite的DB-API接口，文档标为可选模块；发行包要验证实际SQLite能力与事务控制，不能只凭“标准库”省略发布检查。来源：[sqlite3官方文档](https://docs.python.org/3/library/sqlite3.html)。本轮未选择Python最低版本，链接当日页面为3.15.2；以后应在目标最低版本文档/环境再验证。

## 11. 最小验证问题和建议补充决策

下列是后续独立可写实验副本/原型票的最小问题；本研究没有执行，不标验收通过。优先核对行为不变量，不以测试条数或源码注释作结论。

| 优先 | 最小场景 | 预期需要得到的证据/决定 |
| --- | --- | --- |
| P0 | mock模型返回text/tool/分片JSON/半截JSON/空响应/429/5xx/超时/取消；三入口对比 | 流事件顺序、无重复输出、错误分层、usage、工具消息配对；精确重试次数/等待可取消性 |
| P0 | 长工具轮中提交新输入；查询slash和变更slash各一条；等待时提交输入 | 输入boundary时序、查询不取消wait、变更先settled、paused清队列行为 |
| P0 | 后台agent与Shell各一；TaskWait any/all；完成/失败/取消/attention/重复event | waiting零模型请求、事件单次持久投递、错误提前唤醒、manual/foreground/跨会话拒绝 |
| P0 | 在assistant存档前后、beforeTool后、外部副作用后、afterTool前后、ack前后逐点kill | 不能重复执行；unknown/interrupted准确；同一工具结果补齐；人工决定可审计；重启等待安全 |
| P0 | runner已获grant/未获grant、start.claim后崩溃、连接丢失、旧epoch、双owner、重用PID | 新owner可接管可信执行，拒绝并发/旧epoch；不确定时只读核实，不猜结果；Windows专用IPC证据 |
| P0 | Windows前台/后台命令派生孙进程，Esc/TaskStop/KillShell/关闭窗口 | 所有后代退出或明确保留；取消不是已终止；中文/空格路径与编码正确 |
| P0 | fork/普通/后台/verify/explore/plan、自定义tools、父yolo、isolate/remote、Ctrl+B | 实际工具池与权限模式、禁止嵌套、最多并发与排队、单run执行、转后台后消息仍投递 |
| P0 | normal exit、SIGINT/SIGTERM、kill、quit keep-background、非TTY EOF、managed panel关闭 | Shell保留/终止策略、任务终态/待恢复状态、SessionEnd/DB关闭/日志不丢，不把注释当结果 |
| P1 | 全43工具的schema/错误/边界；只读/网络/plan并发与write/exec屏障；hook改写参数 | 注册与可见性计数正确、并发不越界、裁决和执行一致、存储失败暂停 |
| P1 | 固定52、内置8技能、菜单49；禁外部自定义；大小写/别名；管道11命令 | O1-O4真实结果，分清实现/菜单/承诺；决定哪些来源瑕疵修正，保留兼容别名 |
| P1 | 一般/不信任/CLI/企业配置，插件重名覆盖，条件skills、MCP变更、非command hooks | 每种资源真实优先级和支持层级；扩展格式兼容，未实现项显式登记 |
| P1 | 85%压缩、摘要失败、memory开关、来源变更、长任务记忆合并并发 | context恢复边界、无旧摘要重复磨损、无凭空完整性承诺；no-memory实际副作用 |
| P1 | Windows Terminal真窗口：输入法、中文宽字、粘贴/图片/焦点、短窗溢出、横纵缩放、共享/独立视口 | 无报告串进草稿、无自动发prompt、无残影/历史错删；SIXEL不支持时可靠退文字，用户体验验收独立记录 |
| P1 | 旧mtime但有活runner/owner的会话；大文件/慢影子git；有改动worktree | cleanup不破坏可恢复数据、checkpoint不冻结UI、保留改动与新增提交 |
| P2 | Windows安装打包/SQLite支持/资源/许可证/更新；Linux/macOS后续实机 | 工程配套交付与平台证据分开，不用交叉构建代替实机 |

建议由主会话补充的决策问题（不是再次确认已知范围）：

1. 对第9.2节已登记的来源瑕疵，采用“保留兼容别名并兑现能力语义”、还是某些按现行可观察行为；逐项确定 oracle，避免迁移时边实现边猜。
2. Windows Shell、进程树与IPC具体适配契约；保留 TaskWait/runner/owner/事件语义，候选机制由小原型证据决定。
3. 明确三入口的命令能力差异是否属于需要对齐的功能目标；例如把管道扩展到完整slash应登记为有意补齐，而不是假称来源本就支持。
4. 明确定时能力分层：会话 `/loop`、CronCreate当前“session-only未实现”、OS定时，以及Windows新增后端的验收语义；一次性任务必须有确定删除机制还是沿来源手动删。
5. 清理与保留策略需优先保护RuoCun自身恢复数据；资源构建的外部输入、品牌兼容路径、UI库由相应票继续决定。

本报告本地提交仅收录研究资产。[查清完整功能、模块职责与运行时调用链](../issues/02-function-runtime-research.md)及地图、对应表和主工作区由主会话收录后更新；当前未做任何产品实现或验收声明。


## 12. 交付自查记录

已逐一对账工具定义与注册变量、固定命令分支与菜单/技能集合，完整枚举源码目录；对报告全部源码引用检查文件存在性与起止行号范围，未发现越界引用。该检查只证明报告可定位和清单一致性，不证明引用所述行为实测通过。未运行产品/测试、未安装依赖、未写参考源码；本分支唯一交付文件为本报告。

## 附录 A. 完整源码与配套盘点
以下由冻结解包树直接枚举；非测试文件全部列出（含测试辅助模块/协议假服务器，表中不把它们算注册工具），每个路径的 `:1` 仅证明文件存在与可定位，职责证据以正文的具体实现行号为准。测试文件另按目录计数，没有运行。
### A.1 `src/` 顶层
`src/env_snapshot.ts:1`、`src/index.ts:1`、`src/plugins.ts:1`、`src/project_doc.ts:1`、`src/repl.ts:1`、`src/schedule.ts:1`、`src/version.ts:1`。

### A.2 `src/` 全部直接子目录

#### A.2.1 `agent/`：非测试 31，测试 37
- `src/agent/agent_defs.ts:1`
- `src/agent/agent_handoff.ts:1`
- `src/agent/agent_hooks.ts:1`
- `src/agent/agent_lifecycle.ts:1`
- `src/agent/agent_memory.ts:1`
- `src/agent/agent_prompt.ts:1`
- `src/agent/agent_summary.ts:1`
- `src/agent/agent_tools.ts:1`
- `src/agent/background_delivery.ts:1`
- `src/agent/background_runtime.ts:1`
- `src/agent/background_test_helpers.ts:1`
- `src/agent/background_types.ts:1`
- `src/agent/bundled_agents.ts:1`
- `src/agent/cleanup.ts:1`
- `src/agent/compact.ts:1`
- `src/agent/deck_bridge.ts:1`
- `src/agent/deck_messages.ts:1`
- `src/agent/fork_agent.ts:1`
- `src/agent/loop.ts:1`
- `src/agent/reflect_cadence.ts:1`
- `src/agent/reflect_persist.ts:1`
- `src/agent/reflect_prompts.ts:1`
- `src/agent/reflect_result.ts:1`
- `src/agent/resume_agent.ts:1`
- `src/agent/runAgent.ts:1`
- `src/agent/session_scheduler.ts:1`
- `src/agent/tasks.ts:1`
- `src/agent/turn_budget.ts:1`
- `src/agent/turn_health.ts:1`
- `src/agent/unified_reflect.ts:1`
- `src/agent/worktree.ts:1`

#### A.2.2 `approval/`：非测试 3，测试 2
- `src/approval/stdin_prompt.ts:1`
- `src/approval/store.ts:1`
- `src/approval/types.ts:1`

#### A.2.3 `client/`：非测试 4，测试 3
- `src/client/client.ts:1`
- `src/client/responses.ts:1`
- `src/client/sse.ts:1`
- `src/client/types.ts:1`

#### A.2.4 `commands/`：非测试 4，测试 3
- `src/commands/builtin.ts:1`
- `src/commands/commands.ts:1`
- `src/commands/custom.ts:1`
- `src/commands/scheduling.ts:1`

#### A.2.5 `config/`：非测试 11，测试 10
- `src/config/auth_wizard.ts:1`
- `src/config/credential.ts:1`
- `src/config/env_file.ts:1`
- `src/config/keychain.ts:1`
- `src/config/migrate_dirs.ts:1`
- `src/config/model_selection.ts:1`
- `src/config/profiles.ts:1`
- `src/config/profiles_store.ts:1`
- `src/config/trust.ts:1`
- `src/config/update_check.ts:1`
- `src/config/validate_key.ts:1`

#### A.2.6 `data/`：非测试 1，测试 0
- `src/data/laozi-maxims.ts:1`

#### A.2.7 `hooks/`：非测试 1，测试 2
- `src/hooks/hooks.ts:1`

#### A.2.8 `i18n/`：非测试 3，测试 1
- `src/i18n/i18n.ts:1`
- `src/i18n/messages/en.ts:1`
- `src/i18n/messages/zh.ts:1`

#### A.2.9 `lsp/`：非测试 4，测试 3
- `src/lsp/client.ts:1`
- `src/lsp/config.ts:1`
- `src/lsp/manager.ts:1`
- `src/lsp/testfixtures/sample.ts:1`

#### A.2.10 `mcp/`：非测试 2，测试 4
- `src/mcp/__fixtures__/fake-mcp-server.mjs:1`
- `src/mcp/mcp.ts:1`

#### A.2.11 `memory/`：非测试 11，测试 11
- `src/memory/audit.ts:1`
- `src/memory/consolidate.ts:1`
- `src/memory/distill.ts:1`
- `src/memory/frontmatter.ts:1`
- `src/memory/gc.ts:1`
- `src/memory/hash.ts:1`
- `src/memory/inject.ts:1`
- `src/memory/memory_audit.ts:1`
- `src/memory/store.ts:1`
- `src/memory/types.ts:1`
- `src/memory/validate.ts:1`

#### A.2.12 `obs/`：非测试 5，测试 4
- `src/obs/attrs.ts:1`
- `src/obs/backend.ts:1`
- `src/obs/index.ts:1`
- `src/obs/init.ts:1`
- `src/obs/wrap.ts:1`

#### A.2.13 `permissions/`：非测试 18，测试 15
- `src/permissions/audit.ts:1`
- `src/permissions/bash/ast.ts:1`
- `src/permissions/bash/bash_ast.ts:1`
- `src/permissions/bash/bash_parser.ts:1`
- `src/permissions/bash/parser.ts:1`
- `src/permissions/bash_preprocess.ts:1`
- `src/permissions/bash_safety.ts:1`
- `src/permissions/classifier.ts:1`
- `src/permissions/classifier_model.ts:1`
- `src/permissions/dangerous_patterns.ts:1`
- `src/permissions/engine.ts:1`
- `src/permissions/gate.ts:1`
- `src/permissions/identity.ts:1`
- `src/permissions/perm_audit.ts:1`
- `src/permissions/rules.ts:1`
- `src/permissions/sanitize.ts:1`
- `src/permissions/secrets.ts:1`
- `src/permissions/settings.ts:1`

#### A.2.14 `prompt/`：非测试 1，测试 1
- `src/prompt/system_prompt.ts:1`

#### A.2.15 `repomap/`：非测试 8，测试 4
- `src/repomap/extract.ts:1`
- `src/repomap/graph.ts:1`
- `src/repomap/index.ts:1`
- `src/repomap/languages.ts:1`
- `src/repomap/loader.ts:1`
- `src/repomap/render.ts:1`
- `src/repomap/wasm-assets.ts:1`
- `src/repomap/wasm.d.ts:1`

#### A.2.16 `session/`：非测试 12，测试 8
- `src/session/audit_switch.ts:1`
- `src/session/cache_audit.ts:1`
- `src/session/checkpoint.ts:1`
- `src/session/cost.ts:1`
- `src/session/durable_file.ts:1`
- `src/session/durable_store.ts:1`
- `src/session/log.ts:1`
- `src/session/process_identity.ts:1`
- `src/session/recovery.ts:1`
- `src/session/session.ts:1`
- `src/session/sqlite.ts:1`
- `src/session/tool_execution.ts:1`

#### A.2.17 `skills/`：非测试 8，测试 9
- `src/skills/adapt.ts:1`
- `src/skills/bundled.ts:1`
- `src/skills/convert.ts:1`
- `src/skills/discover.ts:1`
- `src/skills/install.ts:1`
- `src/skills/skill_audit.ts:1`
- `src/skills/skills.ts:1`
- `src/skills/usage.ts:1`

#### A.2.18 `tools/`：非测试 67，测试 56
- `src/tools/agent.ts:1`
- `src/tools/ask_user.ts:1`
- `src/tools/config.ts:1`
- `src/tools/cron_tools.ts:1`
- `src/tools/diagnostics.ts:1`
- `src/tools/diff_hunk.ts:1`
- `src/tools/edit_file.ts:1`
- `src/tools/edit_mismatch.ts:1`
- `src/tools/enter_worktree.ts:1`
- `src/tools/exec_shell.ts:1`
- `src/tools/exec_shell_kill.ts:1`
- `src/tools/exec_shell_poll.ts:1`
- `src/tools/execute.ts:1`
- `src/tools/exit_worktree.ts:1`
- `src/tools/fetch_cache.ts:1`
- `src/tools/fetch_extract.ts:1`
- `src/tools/fetch_url.ts:1`
- `src/tools/file_lock.ts:1`
- `src/tools/file_search.ts:1`
- `src/tools/fs_atomic.ts:1`
- `src/tools/glob.ts:1`
- `src/tools/grep_files.ts:1`
- `src/tools/lang.ts:1`
- `src/tools/list_dir.ts:1`
- `src/tools/lsp.ts:1`
- `src/tools/managed_shell.ts:1`
- `src/tools/memory_read.ts:1`
- `src/tools/memory_write.ts:1`
- `src/tools/message_parent.ts:1`
- `src/tools/monitor.ts:1`
- `src/tools/notebook_edit.ts:1`
- `src/tools/notify_user.ts:1`
- `src/tools/output.ts:1`
- `src/tools/paths.ts:1`
- `src/tools/pkg_mgr_pattern.ts:1`
- `src/tools/plan_mode.ts:1`
- `src/tools/process_manager.ts:1`
- `src/tools/read_file.ts:1`
- `src/tools/registry.ts:1`
- `src/tools/repo_map.ts:1`
- `src/tools/safe_env.ts:1`
- `src/tools/sandbox.ts:1`
- `src/tools/schedule_tool.ts:1`
- `src/tools/schema.ts:1`
- `src/tools/send_message.ts:1`
- `src/tools/shell_runner.ts:1`
- `src/tools/skill.ts:1`
- `src/tools/skill_install.ts:1`
- `src/tools/spill.ts:1`
- `src/tools/ssrf.ts:1`
- `src/tools/task_create.ts:1`
- `src/tools/task_get.ts:1`
- `src/tools/task_list.ts:1`
- `src/tools/task_output.ts:1`
- `src/tools/task_send.ts:1`
- `src/tools/task_stop.ts:1`
- `src/tools/task_update.ts:1`
- `src/tools/task_wait.ts:1`
- `src/tools/todo_store.ts:1`
- `src/tools/todo_write.ts:1`
- `src/tools/tool_audit.ts:1`
- `src/tools/tool_search.ts:1`
- `src/tools/tools_for_mode.ts:1`
- `src/tools/types.ts:1`
- `src/tools/walk.ts:1`
- `src/tools/web_search.ts:1`
- `src/tools/write_file.ts:1`

#### A.2.19 `tui/`：非测试 33，测试 25
- `src/tui/app/AgentTasksPanel.tsx:1`
- `src/tui/app/App.tsx:1`
- `src/tui/app/format.ts:1`
- `src/tui/app/run.tsx:1`
- `src/tui/app/types.ts:1`
- `src/tui/background.ts:1`
- `src/tui/banner.ts:1`
- `src/tui/brand.ts:1`
- `src/tui/capabilities.ts:1`
- `src/tui/foreground_registry.ts:1`
- `src/tui/imagePaste.ts:1`
- `src/tui/markdown.ts:1`
- `src/tui/mascot.ts:1`
- `src/tui/mascot_frames.ts:1`
- `src/tui/maxim.ts:1`
- `src/tui/notifier.ts:1`
- `src/tui/onboarding/Onboarding.tsx:1`
- `src/tui/onboarding/run.tsx:1`
- `src/tui/onboarding/Select.tsx:1`
- `src/tui/onboarding/steps/KeyStep.tsx:1`
- `src/tui/onboarding/steps/LanguageStep.tsx:1`
- `src/tui/onboarding/steps/ProviderStep.tsx:1`
- `src/tui/onboarding/steps/TrustStep.tsx:1`
- `src/tui/render.ts:1`
- `src/tui/spinner_words.ts:1`
- `src/tui/tab_attention.ts:1`
- `src/tui/taiji.ts:1`
- `src/tui/terminal_reports.ts:1`
- `src/tui/theme.ts:1`
- `src/tui/tips.ts:1`
- `src/tui/wakelock.ts:1`
- `src/tui/Welcome.tsx:1`
- `src/tui/width.ts:1`

统计：`src/` 有 19 个直接子目录；共 234 个文件名不含 `.test.` 的文件（222 个 `.ts`，含声明文件；11 个 `.tsx`；1 个 `.mjs`），203 个文件名含 `.test.` 的文件（195 个 `.ts`、8 个 `.tsx`），合计 437 个文件；其中顶层非测试 7，顶层测试 5。此分类**包含**非 `.test.` 命名的 fixture/测试辅助模块：`src/lsp/testfixtures/sample.ts:1`、`src/mcp/__fixtures__/fake-mcp-server.mjs:1`、`src/agent/background_test_helpers.ts:1` 等，不表示 234 个均为产品运行模块，也不能代表测试用例数或覆盖率。

### A.3 根目录与配套子目录
根目录文件：`.editorconfig:1`、`.gitignore:1`、`.nvmrc:1`、`CHANGELOG.md:1`、`CODE_OF_CONDUCT.md:1`、`CONTRIBUTING.md:1`、`DAO.md:1`、`eslint.config.js:1`、`install.sh:1`、`LICENSE:1`、`package-lock.json:1`、`package.json:1`、`README.md:1`、`README.zh-CN.md:1`、`SECURITY.md:1`、`tsconfig.build.json:1`、`tsconfig.json:1`、`vitest.config.ts:1`。

- `.dao/`：1 个文件。路径：`.dao/settings.json:1`。

- `.github/`：8 个文件。路径：`.github/dependabot.yml:1`、`.github/ISSUE_TEMPLATE/bug_report.yml:1`、`.github/ISSUE_TEMPLATE/config.yml:1`、`.github/ISSUE_TEMPLATE/feature_request.yml:1`、`.github/PULL_REQUEST_TEMPLATE.md:1`、`.github/workflows/ci.yml:1`、`.github/workflows/qemu-startup-native-probe.yml:1`、`.github/workflows/release.yml:1`。

- `docs/`：83 个文件。内容边界已在第2.1节说明；文档/媒体/评测任务与fixture属于工程材料，不计入运行时工具或模块API。

- `evals/`：198 个文件。内容边界已在第2.1节说明；文档/媒体/评测任务与fixture属于工程材料，不计入运行时工具或模块API。

- `patches/`：1 个文件。路径：`patches/ink+7.0.5.patch:1`。

- `scripts/`：58 个文件。路径：`scripts/accept-cache.sh:1`、`scripts/accept-memory.sh:1`、`scripts/debug-distill.ts:1`、`scripts/demo-reflect.tape:1`、`scripts/demo.en.tape:1`、`scripts/demo.tape:1`、`scripts/dump-harness-wire.ts:1`、`scripts/generate-mascot-data.mjs:1`、`scripts/introspect-cancel-async-tasks-taskgroup-dismissed.ts:1`、`scripts/introspect-feal-brute-force-full-space.ts:1`、`scripts/introspect-model-extraction-relu-logits-untested-branch.ts:1`、`scripts/introspect-openssl-selfsigned-cert-pip-vs-stdlib.ts:1`、`scripts/introspect-write-compressor-encoder-decoder-asymmetry.ts:1`、`scripts/introspect-write-compressor-restart-without-run.ts:1`、`scripts/preview-taiji.ts:1`、`scripts/preview-welcome.ts:1`、`scripts/sync-version.mjs:1`、`scripts/verify-ars-introspect.ts:1`、`scripts/verify-autotune-preference.ts:1`、`scripts/verify-background-recovery-live.mjs:1`、`scripts/verify-background-recovery.ts:1`、`scripts/verify-background-wait-live.mjs:1`、`scripts/verify-background-wait.mjs:1`、`scripts/verify-cancel-async-tasks-taskgroup-replay-v2.ts:1`、`scripts/verify-cancel-async-tasks-taskgroup-replay.ts:1`、`scripts/verify-cold-start-dim.ts:1`、`scripts/verify-exec-shell-no-extra-params.ts:1`、`scripts/verify-exec-shell-timeout-introspect.ts:1`、`scripts/verify-extreme-value-probe.ts:1`、`scripts/verify-fasttext-dim-introspect.ts:1`、`scripts/verify-feal-emptyretry-toolchoice-replay.ts:1`、`scripts/verify-feal-sufficiency-clarify-replay.ts:1`、`scripts/verify-grep-only-matching-replay.ts:1`、`scripts/verify-installwindows-candidate-replay.ts:1`、`scripts/verify-installwindows-introspect.ts:1`、`scripts/verify-installwindows-qemuversion-replay.ts:1`、`scripts/verify-largest-eigenval-checkpoint-replay.ts:1`、`scripts/verify-largest-eigenval-introspect.ts:1`、`scripts/verify-largest-eigenval-round4-replay.ts:1`、`scripts/verify-largest-eigenval-tier2-replay.ts:1`、`scripts/verify-memory.ts:1`、`scripts/verify-model-extraction-groundtruth-peek-replay.ts:1`、`scripts/verify-model-extraction-relu-logits-untested-branch-replay.ts:1`、`scripts/verify-openssl-selfsigned-cert-dep-minimization-replay.ts:1`、`scripts/verify-persistence-runtime.ts:1`、`scripts/verify-recovery-entrypoints.mjs:1`、`scripts/verify-reflect.ts:1`、`scripts/verify-train-fasttext-autotune-introspect.ts:1`、`scripts/verify-train-fasttext-timeout-replay.ts:1`、`scripts/verify-tunemjcf-candidate-replay.ts:1`、`scripts/verify-tunemjcf-introspect.ts:1`、`scripts/verify-videoprocessing-introspect.ts:1`、`scripts/verify-write-compressor-hard-block-rewrite.ts:1`、`scripts/verify-write-compressor-missing-dep-default-replay.ts:1`、`scripts/verify-write-compressor-missing-dep-hard-block-replay.ts:1`、`scripts/verify-write-compressor-oracle-search-replay.ts:1`、`scripts/verify-writecompressor-introspect.ts:1`、`scripts/welcome-ink.tsx:1`。

- `tests/`：1 个文件。路径：`tests/setup.ts:1`。
