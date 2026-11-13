# RuoCun 完整迁移规格

Status: specified；test-entrypoints-confirmed；architecture-reviewed-by-D14
版本：1.1；更新：2026-11-10；产品实现与停止边界读取[实施进度](implementation.md)。
范围依据：用户已确认目标、ADR-0001、ADR-0002。本轮发布至本地 Markdown tracker。

本文定义本轮已确认范围。核心链路跑通只是里程碑；完成须覆盖仍在范围内的条款、模块处理和验收矩阵，明确移出项不算已实现或已通过。

2026-11-10用户按表缩减R1、R3、W3、W5、W6、D2、D3、V1、V2，决定见[ADR-0010](../../docs/adr/0010-selected-scope-and-lean-workflow.md)。保留正常会话与普通代理恢复、本进程费用/预算、Windows凭据/图片剪贴板、欢迎图/向导/面板、72–74评估配套及CI/文档。缩减跨重启费用与特殊fork恢复保证。Windows系统定时/防休眠/桌面通知不交付，最终只交标准Python包并采用手工升级。成套live评分和量化性能保证移出门禁。

当前保留完整TUI，新增移出20 NotebookEdit、37自定义Markdown命令和50组合插件。原84个任务编号和805个来源成员继续记录，当前排除20/37/50/75/80，有效79票。独立的Skills、Hooks、代理及其余能力按各自验收条件交付。[ADR-0014](../../docs/adr/0014-terminal-and-scope.md)

2026-11-10范围修订：[ADR-0008](../../docs/adr/0008-source-first-sandbox-parity.md)按用户要求将OS沙箱改为DAO已有能力兼容（默认可选、macOS/Linux、Windows明确不支持），停止额外原生Windows隔离/组件/VM路线。下文历史实验/完整沙箱前置描述以此修订为准；其它Windows补齐、已确认差异与数据恢复目标保持。

## 阅读入口与证据基准

- [项目上下文](../../CONTEXT.md)、[架构决定](../../docs/adr/)、[迁移决策地图](../ruocun-discovery/map.md)。
- 持续维护附件一：[原模块 → RuoCun 模块对应表](module-map.md)，保存详细来源/目标路径、调用链、依赖替换和逐文件处理。
- 持续维护附件二：[原功能 → 验收案例 → 实现状态 → 验证证据](acceptance-matrix.md)，保存全部产品状态、平台结果、用户验收及故障归因。
- 执行组织：[ADR-0006](../../docs/adr/0006-batched-sprint-workflow.md)的小批与出口规则由[ADR-0010](../../docs/adr/0010-selected-scope-and-lean-workflow.md)补充普通批末独审、执行减负及范围调整；原量化性能契约已由V2移出。[48小时计划](sprint-48h.md)保留批次安排，当前授权与计时只读实施进度。
- 事实来源：[功能与运行时研究](../ruocun-discovery/research/02-function-runtime.md)、[数据与扩展研究](../ruocun-discovery/research/03-data-extension.md)、[终端、测试与交付研究](../ruocun-discovery/research/04-terminal-platform-delivery.md)、[Windows 系统能力研究](../ruocun-discovery/research/16-windows-capabilities.md)。研究中的源码定位均指冻结快照。
- 唯一参考：[dao-f17e189-7ac654a0dc06](../ruocun-discovery/reference/README.md)，DAO v0.5.15，提交 `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`，包含12个本地修改及8个未跟踪文件；源码树 SHA-256 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`。805个成员均在对应表登记。活动参考仓库后续变化不改变本规格基线。

地图的当前状态读取[迁移决策地图](../ruocun-discovery/map.md)与frontier，不由本文缓存早期票数。技术候选、已接受路线、产品实现和验收分别记录；已写规格不表示地图或产品完成。ADR-0010只撤销明确选中的保证与交付形态，其余真实前置继续保留。

## 问题（Problem Statement）

用户希望获得可在 Windows 使用、核心实现为 Python 的 RuoCun，并能沿原 DAO 的目录职责、工具和运行链路继续理解与扩展项目。首版明确不支持的能力按ADR-0010呈现；其余输入体验、权限、异构后台任务、恢复和扩展协议继续迁移。仅用单测或无头终端不能证明真实 Windows Terminal 体验。

迁移需要同时回答“用户能做什么”“模型实际收到什么”“副作用发生后怎样取消和恢复”“各平台怎样提供同一能力”。来源自身已有缺口或可疑故障，不能一律作为正确预期，也不能将迁移失败全部归因于原版。

## 方案（Solution）

以冻结工作区为唯一对照，逐项迁移仍在本轮范围内的可观察功能和关键行为，对ADR-0010的移出或缩减项记录明确差异。RuoCun 使用独立仓库、统一产品名 RuoCun、包/命令技术标识 ruocun；核心采用 Python，保留模块职责和主要调用方向，语言绑定与平台实现可替换。

Codex 负责编码、调试、测试和证据；用户负责行为取舍及体验验收。Windows按本轮支持范围验收，Linux/macOS保留跨平台设计和后续实机记录。配置与扩展兼容、已保留的保存恢复保证、版权与许可、测试及标准Python包发布配套共同构成完成条件。

### 范围清单

| 范围 | 必须交付的用户能力 |
| --- | --- |
| 启动与入口 | 首次引导、多账户/多provider/模型、CLI参数、一次性任务、TTY交互、非TTY/管道、继续会话、诊断和正常退出 |
| 对话与模型 | 流式文本/推理/工具调用、图片、请求参数与提示保真、上下文管理、重试/限流/预算/费用与缓存归因 |
| 工具 | 从来源43个定义逐项核对保留范围。NotebookEdit移出，LSP仍按配置注册。保留延迟加载、搜索激活、权限模式裁剪及动态MCP工具 |
| 命令与扩展 | 从来源52个固定slash名字逐项核对保留范围及入口差异。保留8个core技能、动态Skills、原生agent、Hooks、MCP、LSP和Agent Deck。`/plugin`与自定义Markdown模板移出 |
| Agent运行 | 主循环、任务队列、前后台转换、等待、子代理/fork、worktree、长期目标、Monitor、手工任务、会话loop；Windows系统级定时明确不支持，来源其它平台路由保留未验 |
| 状态与数据 | 会话/消息/工具journal/执行快照/事件/附件、owner与epoch、恢复决定、聊天分支/导出、工作区检查点和长期记忆 |
| 终端体验 | 内联转录及原生scrollback、编辑与中文IME、粘贴/图片、流式时输入、审批/选择器/任务面板、快捷键、焦点/标题、欢迎图形/降级、缩放和退出恢复 |
| Windows补齐 | Shell方言/编码、真实受管进程树取消、认证IPC及ACL、持久文件、系统凭据、图片剪贴板、终端内提示与安全标题；系统定时、防自动休眠、桌面通知按ADR-0010移出，OS沙箱沿用来源平台边界 |
| 工程交付 | 805成员映射、来源测试/回放与72–74评估配套、真实终端体验、标准Python包干净安装/恢复、手工备份更新、版本/资源/许可/CI及完整发布文档；独立程序、成套live成绩和量化性能保证移出 |

固定命令52个、core技能8个、工具43个分别是不同集合；菜单项不等于已实现命令，动态扩展名称不能预先穷举。对应表逐项列出，不以README或菜单数量替代实际实现盘点。

## 用户故事（User Stories）

以下序号是稳定需求标识，不表示优先级；具体本轮支持边界以ADR-0010及验收矩阵为准，移出的保证保留编号和历史来源。

1. 作为用户，我希望安装后直接运行 ruocun，以便在不依赖开发仓库的环境工作。
2. 作为新用户，我希望用中英文引导设置账户、模型和信任，以便明确数据保存和权限状态。
3. 作为用户，我希望管理多个provider和账户，以便显式选择凭据、端点和模型。
4. 作为用户，我希望已有配置、环境开关和命令参数保持既有语义，以便复用工作习惯。
5. 作为用户，我希望RuoCun与DAO数据边界明确，以便并存时不损坏原有项目或会话。
6. 作为用户，我希望交互、一次性任务和管道入口各自可靠，以便终端操作与自动化都可使用。
7. 作为用户，我希望查版本、帮助、自检和状态，以便识别实际支持能力与故障条件。
8. 作为用户，我希望选择模型、思考档位及上下文窗口，以便控制成本和任务能力。
9. 作为用户，我希望看到持续输出且能保留被中断的部分，以便判断进度和继续工作。
10. 作为用户，我希望限流或认证失败时能修正账户、等待或停止，以便不被静默换模型。
11. 作为用户，我希望理解费用、缓存、上下文和预算，以便作出使用决策。
12. 作为用户，我希望执行期间仍能编辑和提交后续输入，以便在安全边界调整任务。
13. 作为用户，我希望审批、问题、选择器和任务面板层级清楚，以便准确完成交互。
14. 作为用户，我希望中文IME、宽字符、emoji和组合字符编辑正确，以便输入内容完整。
15. 作为用户，我希望多行粘贴不自动执行，以便检查内容后再提交。
16. 作为用户，我希望长粘贴能折叠显示并完整提交，以便编辑区可用且不丢原文。
17. 作为用户，我希望粘贴或附加图片，以便让支持视觉的模型读取真实图片内容。
18. 作为用户，我希望边流式输出边输入、滚动和复制，以便保持原生终端工作体验。
19. 作为用户，我希望窗口连续缩放后光标、草稿和历史仍正确，以便自由调整布局。
20. 作为用户，我希望Esc、Ctrl+C和转后台各有明确作用，以便停止当前活动而不误杀其它任务。
21. 作为用户，我希望焦点、安全标题与终端内提示随任务状态工作；本轮不承诺桌面通知或Windows自动防休眠，需自行关注终端和管理电源。
22. 作为用户，我希望欢迎图形和动画可用且能可靠降级，以便不支持图形的终端仍正常工作。
23. 作为用户，我希望使用所有文件读取、搜索和修改能力，以便完成真实代码任务。
24. 作为用户，我希望并发文件变化和错误编辑被识别，以便不覆盖自己或其它程序的改动。
25. 作为用户，我希望运行Shell、读取后台输出并取消整个受管进程树，以便长命令可靠结束。
26. 作为用户，我希望网络抓取和搜索遵循权限及地址检查，以便获得可核查信息。
27. 作为用户，我希望使用询问、清单和用户消息工具，以便任务进展和取舍可见。
28. 作为用户，我希望创建、查询、更新和停止任务，以便区分手工记录与实际执行。
29. 作为用户，我希望后台等待基于明确任务和执行身份，以便旧结果不误唤醒新运行。
30. 作为用户，我希望将前台任务转入后台并继续对话，以便两者取消范围互不混淆。
31. 作为用户，我希望派发同步或后台子代理、fork并追加消息，以便不同职责可协同完成。
32. 作为用户，我希望子代理模型、权限和工具限制有效，以便派发不会扩大已授能力。
33. 作为用户，我希望使用worktree隔离任务，以便不同改动有明确Git边界。
34. 作为用户，我希望Monitor与周期任务可靠启动停止，以便重复观察不会留下无主工作。
35. 来源系统定时与会话内loop保持语义区别；本轮Windows系统级定时明确不支持，不用仍需程序运行的loop冒充关闭会话后可触发。
36. 作为用户，我希望允许、询问、拒绝和plan等模式正确裁决，以便实际执行符合显示状态。
37. 作为用户，我希望审批展示实际将执行的参数，以便Hook改写后仍能作出知情选择。
38. 作为用户，我希望复杂Shell命令和敏感目标得到正确判断，以便不借换平台绕过权限。
39. 作为用户，我希望可选OS沙箱按DAO已有平台能力工作：支持平台有真实隔离，Windows显式要求时准确拒绝不支持，默认关闭和网络开关语义保持。
40. 作为用户，我希望启用和禁用技能、Hook及MCP，以便控制当前扩展集合。组合插件移出当前范围。
41. 作为用户，我希望现有技能格式、资源目录、命名空间与覆盖顺序保持兼容，以便复用技能资料。
42. 作为用户，我希望保留的命令、内置prompt和动态Skills按原入口优先级运行，以便同名行为可预测。
43. 作为用户，我希望自定义agent的frontmatter和生命周期兼容，以便继续复用角色定义。
44. 作为扩展作者，我希望Hook的输入、事件、结果和错误语义稳定，以便扩展不需重写。
45. 作为扩展作者，我希望MCP传输、工具schema、资源、提示和能力更新兼容，以便外部服务继续可用。
46. 作为用户，我希望MCP断线或执行结果不明时得到真实状态，以便不重复远端副作用。
47. 作为用户，我希望LSP位置、URI和协议分帧在Windows正确，以便导航到真实代码位置。
48. 作为用户，我希望Agent Deck协议、认证和幂等保持可用，以便外部面板可连接同一运行。
49. 作为用户，我希望产品指令按真实发现顺序加载，以便不会把工程代理规则误当产品上下文。
50. 作为用户，我希望模型收到原有提示、工具描述和请求参数，以便迁移不暗中改变Agent行为。
51. 作为用户，我希望记忆可保存、查询、删除、审核并按项目过滤，以便长期知识可控。
52. 作为用户，我希望反思、蒸馏、合并、压缩和代码图延续原职责，以便长任务上下文稳定。
53. 作为用户，我希望关闭程序后可继续同一会话，消息、四累计token、等待及已保留状态延续；历史分模型费用不承诺完整，重启新费用另计并标明统计范围。
54. 作为用户，我希望崩溃恢复不盲重放工具，以便外部副作用不被重复执行。
55. 作为用户，我希望未知结果、损坏状态和附件缺失被显式指出，以便选择恢复处理。
56. 作为用户，我希望同一会话只由有效owner写入，以便旧进程不能覆盖新恢复状态。
57. 作为用户，我希望保留后台执行后能重新接管和取消，以便后台不变成无法管理的进程。
58. 作为用户，我希望聊天分支、命名、导出、回退和工作区检查点语义清楚，以便操作可追溯。
59. 作为用户，我希望会话清理和升级保留仍需恢复的数据，以便长期工作不被误删。
60. 作为Windows用户，我希望系统凭据与图片/文本剪贴板有本机实现；系统定时、自动防休眠与桌面通知本轮明确不支持，不以WSL或终端提示冒充已补齐。
61. 作为Windows用户，我希望Shell方言、编码、中文空格路径和外部扩展启动可靠，以便原生工具链可用。
62. 作为用户，我希望标准Python包的安装、手工停进程/备份/更新/卸载有清楚说明并保护旧数据；本轮不承诺自动跨版本原地迁移或失败自动回退。
63. 作为维护者，我希望每个来源模块和测试资产有对应记录，以便后续worktree能继续完整迁移。
64. 作为维护者，我希望原故障与迁移回归分别记录，以便测试预期不会被错误实现反向定义。
65. 作为维护者，我希望离线测试、真实模型任务和终端操作分别留证，以便结论有明确边界。
66. 作为用户，我希望验收真实任务结果，以便不会把模型结束、历史成绩或局部探针当作完成。
67. 作为维护者，我希望发布资源、版权许可、版本和构建记录完整，以便产物可复现且可交付。
68. 作为用户，我希望Linux/macOS保留合理适配设计并标明尚未实机验收，以便平台承诺可信。

## 实现决定与行为契约（Implementation Decisions）

下列“必须”为验收约束；“保持参考”均指冻结实现及其已存在测试，排除已登记缺陷未经决定就被默认为正确预期。候选库及未收口策略只在前置决定表出现。

### R-01 · 模块边界与调用关系

保持组合根、REPL、Agent、Client、Prompt、Tools、Approval/Permissions、Session、Memory、Config、Commands、Skills、Hooks、MCP、LSP、RepoMap、Obs、TUI、i18n及资源的职责划分。模块拆合、命名与依赖替换均登记对应表；通过集中业务接口解耦语言绑定，不将调度、恢复、输入和渲染合并成一个聊天循环。

主要关系为：组合根完成配置/扩展/提示及运行时组装；输入交SessionScheduler；scheduler在安全边界调用runTurn；runTurn通过统一client获取模型事件，保存assistant工具意图后交dispatcher；dispatcher经过参数、Hook、权限和审批才执行handler；结果落盘后进入下一模型轮。后台运行通过run/event事务进入inbox，消息保存成功后才确认消费。UI通过业务事件观察这些状态，不拥有副作用执行真相。

目录、详细源/目标路径和逐文件例外只在对应表维护。核心不得依赖Node/Bun进程代理原业务执行；外部Hooks/MCP/LSP及用户Shell仍按声明命令和协议运行，可使用其它语言。

### R-02 · 启动、CLI与入口差异

完整保留首次引导、账户/模型/语言/信任加载、工具扩展注册、记忆/技能/指令/提示组装、权限/会话/后台/持久化/scheduler绑定和收尾顺序所形成的可观察行为。初始化失败需定位具体资源，部分扩展失败不得隐瞒或破坏其它已独立可用扩展。

支持TTY、非TTY/Deck-managed、argv一次性prompt三个入口。TTY保留完整命令/选择器；非TTY保持基础9命令及recovery/resume共11个固定名字；argv prompt不假定支持完整slash。headless首次工具批包含TodoWrite的参考要求保留，并验证拒绝批次与重试行为。EOF、后台keepAlive和正常退出独立测试。

所有现有CLI flags、trust/plugin/Skill/Schedule操作员入口、恢复参数、权限规则参数及长任务别名均纳入附件。保留大小写和参数消费规则；未知token在原实现中可能成为prompt，不擅自统一改成拒绝未知参数。操作员命令大小写与帮助冲突登记来源问题，经oracle/明确决定后处理，不直接照抄文案。

| CLI契约 | 稳定参数与行为 |
| --- | --- |
| 标识/管理 | --version/-v；trust；plugin add/list/remove；冻结实际入口Schedule add/list/remove、Skill add（大小写冲突见来源问题） |
| 模型/凭据 | --api-key、--provider、--model的值消费与覆盖；不将密钥写入验收日志 |
| 会话 | --continue/-c及可选session-id；紧随的非横线token在参考中作为ID，不能默认为普通prompt |
| 权限 | --yolo、--allow、--deny、--ask、--add-dir、--permission-mode；实际规则独立解析并与分层设置合并 |
| 长任务 | --goal、--task、--coordinator进入同一长任务模式；不再建立不同旧coordinator执行器 |
| 诊断/反思 | --verbose/--debug、--obs、--reflect-memory、--reflect-challenger、--progress-advice、--no-progress-advice |
| 按通道关闭 | --eval、--no-memory、--no-skills、--no-mcp、--no-hooks、--no-project-instructions、--no-web；--eval不等于关闭全部内置技能和Hooks，--no-memory不等于删除Memory工具；动态发现隔离疑点单列 |

各参数的缺值、重复/冲突、位置及未知token组合建立来源golden；内部runner角色不混入用户flags兼容清单。

### R-03 · 固定命令、动态命令和技能

附件保留来源52个固定slash名字供盘点。`/plugin`及操作员`plugin`入口移出。大小写敏感的Config、别名及App内theme/loop继续按各入口核对。8个core技能和磁盘Skills继续交付。菜单中security-review/debug-session/dod在冻结固定实现集中缺少对应路径，菜单展示仅是来源记录，同名原生Skills按实际支持规则调用。

保留命令解析、参数空白处理及内置命令和Skills之间的优先级。用户、项目及插件提供的自定义Markdown命令模板移出。查询和展示命令维持当前运行，状态变更先暂停并等待当前操作收尾。theme、loop、恢复查询和带参数恢复的暂停语义分别验收。loop采用整数s/m/h周期排队，在off和退出时清理，仅在当前程序运行期间有效。

### R-04 · 工具全集与注册契约

| 工具域 | 稳定外部名字 |
| --- | --- |
| 文件 | Read、ListDir、Glob、Grep、Write、Edit。来源的NotebookEdit移出 |
| Shell/网络 | Bash、BashOutput、KillShell、WebFetch、WebSearch |
| 用户交互/清单/消息 | AskUserQuestion、TodoWrite、NotifyUser、SendUserMessage |
| 记忆/技能 | MemoryRead、MemoryWrite、Skill、SkillInstall |
| 代理与任务 | Agent、TaskSend、MessageParent、TaskWait、TaskCreate、TaskList、TaskGet、TaskOutput、TaskUpdate、TaskStop |
| 模式/隔离/监控/配置 | EnterPlanMode、ExitPlanMode、EnterWorktree、ExitWorktree、Monitor、Config |
| 定时/发现/导航 | Schedule、CronCreate、CronDelete、CronList、ToolSearch、RepoMap、LSP |

来源默认42个，配置LSP后43个。RuoCun按上表保留项注册，NotebookEdit不进入工具注册表。Web禁用或eval移除WebFetch/WebSearch。保留延迟集合、工具搜索、顺序、首次可见性和模式裁剪的注册语义。MCP工具按server动态加入，前5个自动可见，其余搜索激活。plan既从发送schema中裁剪，也在真实执行前复核。

每个工具保留name、描述、输入JSON schema、required、枚举、缺省/可空/未知字段接纳、返回文本/附件、capability、approval、错误和取消语义。Python内部类型可改，发送模型的契约不能由新校验器习惯重写。每个定义及registry序列建立来源golden；工具参数片段完整/合法前不执行handler。工具错误仍形成可配对结果，并保留诊断与审计。

文件工具保留读取前置、并发修改检测、锁/原子替换、diff、编码、二进制/图片/大文件和路径边界；中文空格、盘符/UNC、大小写及符号链接必须按各平台验证。Shell输出增量、溢写、exit/失败标记与屏障联动均属行为。TaskCreate是手工记录，TaskList/Get/Output查询TaskManager；BashOutput/KillShell查询Shell管理器，不能合并成虚构的统一清单。

CronCreate的durable=false在来源中不支持，一次性不自动删除；这类明确不支持返回保留，不据工具名字擅自扩充能力。LSP的9个操作全部在范围；RepoMap保留提取、排名、预算及缓存。

### R-05 · 提示词保真和上下文组装

系统模板、长任务directive、子代理提示、内置agent/技能/命令prompt、反思/压缩/记忆蒸馏与适配、权限分类器、工具描述、失败恢复提示和注入哨兵都纳入迁移。对相同输入建立参考生成结果，并比对实际模型请求；不能只对模板常量做测试。

保留消息角色、顺序、分段、优先级、占位符、语言变体、模型/视觉说明及固定前缀和尾部动态注入边界。环境、后台消息、记忆和工具输出按原安全提示界限进入上下文，不能冒充用户指令；异步结果不能插入未闭合assistant/tool对中间。SessionStart上下文去旧再注入，恢复不无限累积。

已确定产品改名所需的身份/命令引用及Python/Windows真实环境说明允许准确替换；形成明确差异白名单及请求golden。其它prompt重写、删节、翻译或行为建议修改需要单独差异决定，不能归入“语言迁移”。JSON序列化稳定、工具列表和消息前缀稳定，保留缓存感知设计；不把这一设计宣称为供应商缓存命中率保证。

### R-06 · 模型目录、参数和路由

provider为冻结的6种定义；profile存端点、模型及凭据引用，模型目录中的ID、contextWindow、vision、maxOutputTokens和每provider默认端点/模型都是冻结数据。迁移时不以供应商后来发布的新目录替换基线。自定义模型/网关沿用原fallback，不自动猜provider或廉价辅助模型。子代理选择优先级为调用override > agent定义 > parent继承；缺可继承主模型明确失败。

保持Chat Completions及现有Responses桥的路由判据、消息转换、function call/output、reasoning items、错误和usage归一化。不能以SDK支持某接口推定参考已经支持原生的另一套provider协议。

默认请求输出上限128000、可由环境/单次覆盖并受模型上限裁剪；特殊空截断重试256000也须裁剪。保留按模型选择max_tokens/max_completion_tokens、thinking/reasoning_effort（loop缺省max）、parallel_tool_calls、tool_choice及extra覆盖规则。无配置的temperature/top_p等不主动添加。Response桥的store、include和effort映射按冻结请求测试。

assistant null content转空串；工具轮reasoning_content按原规则回传，无工具轮不能机械附带；图片内部字段不泄漏到wire；Response专有items仅适用路由保留。usage兼容原生cache字段及cached_tokens补齐，原生字段优先；四累计token在自身恢复后连续。本进程保留分模型用量/费用累计；重启后的历史费用可能不完整，新费用另计并明确展示统计范围，不宣称全会话总价。

### R-07 · 流式、失败与预算

按增量字节正确解码UTF-8/SSE，处理分片、多帧、结束标记、reasoning/text/tool-call参数按index累积、usage和finish_reason。默认idle watchdog240秒，仅实际delta重置；心跳不假装模型产出。用户取消保留已累积部分，有内容后idle错误需明确显示；迟到事件受当前run/epoch约束。

保持client与loop不同重试层：client默认2次可重试前产出失败及一次非流式fallback，有内容后不从头重放；429是否带Retry-After、background529、认证/上下文错误分别处理。退避按实际公式而非“指数退避”注释设oracle。loop的上下文压缩、有限空响应恢复、tool_choice不支持降级、根限流选择和持续ModelUnavailableStop独立验收；子代理不能误继承根交互分支。不自动更换业务主模型。

默认主代理无轮数上限、子代理预算及所有已存在覆盖值按参考入口分别保持。费用阈值默认提醒，仅显式hard开关硬停；R1缩减后费用阈值按本次运行统计，重启可能重新计数，必须说明不保证跨重启会话总额限制。completed表示当前无进一步工具请求，不表示任务质量通过；失败、waiting、interrupted各有真实状态与可执行后续。

### R-08 · 权限、信任和审批

保留user→trusted project→local→CLI→enterprise设置次序，规则并集、defaultMode后覆盖及deny > ask > allow。有效模式优先级为session plan > yolo >运行覆盖>加载defaultMode>auto。工具身份、路径/域名/命令匹配方言和大小写保持；Bash AST/安全预处理不能被通用glob替换，复杂无法证明安全的语法进入ask。Windows PowerShell/cmd采用真实方言判断与原生执行适配，不能借平台更换扩大权限。

PreToolUse只执行一次；updatedInput后的最终参数同时进入权限、安全、审批、审计与执行。批量审批、始终允许保存、拒绝/超时/无交互、auto分类器与熔断按原行为验证。只读/plan能力标签不代表纯函数，Config/MemoryWrite等仍有副作用，必须经过相应持久保护。

来源信任检查适用于部分settings/local/hooks。保留MCP、LSP、Skills、agents和项目指令的实际信任边界。扩大信任检查需另作兼容决定。组合插件安装与删除的路径约束保留在来源记录。审计对秘密及敏感参数脱敏，fixture使用合成凭据。

### R-09 · 并发、调度和异构任务

区分scheduler状态idle/running/waiting/paused/closed/recovering、单轮completed/waiting/interrupted/failed及执行快照running/canceling/completed/failed/canceled/interrupted/unknown；unknown不当作已确定终态。任务ID、执行runID、会话ID、工具scope/ID和eventID各有作用域，不用一个ID替代。

普通输入排队，工具轮安全边界合并，active/scheduled防重复pump。TaskWait去重后接受1–32个当前后台执行，固定task+run；any/all、失败/取消/attention提前唤醒、prepare/save/commit与失败rollback消费一致。手工任务/前台执行/未知或已中断目标按原错误语义处理。

工具read/network/plan批次最多8个并行，write/exec是串行屏障，结果原序交付；已发批次allSettled收齐后再传播持久化等失败。来源失败文本与屏障判定冲突先单列oracle，不能通过丢结果掩盖。

TaskManager、Shell管理器和BackgroundRuntime保持边界。Shell是独立持久runner；普通agent保留可显式继续的checkpoint，当前进程fork/exactTools及工具裁剪继续对照来源；R3允许重启后特殊工具/提示现场不足的fork明确拒绝继续，保留转录供查看后新建任务，不降为普通agent。Monitor按其真实执行器恢复；manual只恢复记录；loop不承诺跨owner定时执行。权限门、模型、最大并发/turn预算、消息/summary/handoff和worktree生命周期分别对照。remote在冻结实现中实为worktree，不宣称真实远程执行能力。

Agent批量scatter一次最多20个任务，默认并行worker为10并保留对应环境覆盖；主代理turn覆盖不替代子代理独立预算。各入口fork/exactTools的默认差异仍按来源分别建例，不因统一Python类型而合并。

### R-10 · 取消与退出语义

Esc先按模态层消费；主活动暂停时清输入队列、释放等待、abort当前轮并保存paused，不隐式cancelAll后台。转后台解绑旧前台signal；前台随后取消不得杀已独立的后台运行。TaskStop/KillShell先请求/记录canceling，执行器确认close及受管进程树止写后才记canceled；无法确认保守unknown。取消不回滚已发生文件/网络/扩展副作用。

取消await不等于线程或底层操作停止，任何to_thread/SDK阻塞适配不得仅凭CancelledError确认副作用已终止。模型流停止、工具终止、后台等待释放、终端按键和应用退出分开核实。用户中断后旧run/epoch的回调不能污染新轮。

正常退出释放输入/输出模式、订阅、扩展、观测与任务资源；显式keep-background仅保留有协议支持、可重新接管的执行，不能留下无主进程。关闭Deck面板不等于结束managed Agent。强杀、注销、重启、断电分别记录能力边界，不由owner存活实验推出其它保证。

### R-11 · SQLite、持久化与恢复

RuoCun自身会话采用权威SQLite状态，保留参考v2模型的逻辑角色：metadata/owner/epoch/checkpoint/revision/background/attachments、runs、events及delivered、作用域工具journal、agent checkpoint。无需旧DAO数据库或会话格式导入；因此物理表/版本可经ADR演进，但下述原子性、身份与结果语义不可降级。SQLite不是可任意替换成旁路JSON的日志细节。

WAL、FULL同步、busy timeout3000ms及BEGIN IMMEDIATE事务语义保留并读回核验。消息/后台checkpoint/revision/消费事件delivered同事务；run与event同事务，先持久后通知；save成功后才ack。SQL foreign_keys开关不等于已有外键约束，实际跨表一致性须由事务与验证承担。锁、磁盘满、权限、同步/提交失败应保留真实错误，不伪造成功。

工具意图在副作用前落盘，结果提交后才能复用。恢复时已提交结果不重执行；可证明无意图的操作才判未执行；started无可信结果变outcome_unknown。PreToolUse等非read副作用同样受保护。恢复补齐消息对，未知工具/任务须通过显式resolve/decide/continue处理，决定同历史一起持久化。本地journal不能保证任意远端服务的exactly-once。

owner使用canonical cwd、session、host/boot/pid/start及instance/epoch；活owner拒绝并发恢复，死owner可接管并递增epoch，每次写检查fencing。查询失败不冒充死亡，PID重用不误认原进程，不同host不自动接管。runner校验token/run/epoch、排他start.claim、grant及终态receipt；可能已grant而无结果保持unknown，不能重拉命令试运气。

大结果超过24000字符保留全文附件并先持久后登记hash；恢复检验附件和stdout/stderr，缺失/变更成为明确未决。state/meta导出及events.jsonl/审计是旁路；损坏、未来版本或缺可信checkpoint拒绝恢复，不静默创建空会话。备份采用数据库备份或一致停机快照，不能复制单个活db就宣称可恢复。

保存恢复覆盖：消息/工具结果、当前模型与会话模式、标题/目标、四累计token、执行快照/事件/等待、普通代理checkpoint和显式恢复决定，以及继续正确运行所需元数据。按R1不补齐历史分模型费用桶，重启后费用只计新产生部分并标明历史不完整，费用预算采用同一口径；按R3材料不足的特殊fork明确拒绝继续，不伪造等价恢复。缓存归因可重建但不能重启后误报连续命中。运行队列/草稿哪些是已接受输入必须明确；R2未被选中，已接受且已确认保存的输入不能丢失；未提交编辑草稿不承诺崩溃恢复。秘密只保留必要引用，不复制明文进入会话。

聊天分支不复制或重启父后台执行；影子Git工作区检查点、聊天检查点、代理checkpoint和SQLite WAL checkpoint各自独立。restore/rewind范围、自动回退前快照、忽略/大二进制/Git不可用均有案例。清理不得删除活owner、可恢复执行或未解决数据；来源mtime清理风险作为差异修复记录。

Windows原子替换、文件占用、flush和ACL必须实证；目录fsync的POSIX写法不能直接当Windows保证。进程kill实验不等于断电验证。产品使用含官方WAL-reset修复或可审计回移的SQLite，最终产物读回实际version/sourceid/compile options；实验3.45.1不满足产品门禁，普通压力测试通过不证明修复。修复版本及回移依据沿用[SQLite官方WAL说明](https://www.sqlite.org/wal.html#walreset)，地图19负责验证实际运行库。

### R-12 · 配置和产品扩展兼容

兼容包括外部字段/大小写、接纳/错误边界、发现与覆盖、调用参数/事件/协议、文本及资源目录。保留各资源自己的优先级，不用一个“全局配置合并”替代所有loader。

| 通道 | 保持的格式与语义 |
| --- | --- |
| profiles | version2、activeProfile/profiles及provider/baseUrl/model/key/keyRef；旧单账户格式接纳、未知顶层字段保存、增删/激活规则；inline key优先keyRef；不凭通用API_KEY环境变量自动选账户 |
| dotenv/环境 | 只加载cwd，已有环境含空值优先；参考简化引号/注释方言，无自动export/变量展开；每变量缺省/空/0/1/非法数字语义独立 |
| settings/permissions | 分层及规则字符串方言、additional directories、托管配置与模式；不以新通用校验器改变宽容边界 |
| 产品指令 | 用户级→Gitroot至cwd每层DAO指令及local指令，trim去重；只沿受控Git边界；AGENTS开发文件不自动进入产品 |
| Skills | slug Markdown或一级SKILL布局、简单frontmatter字段别名、paths、model/user invocation、同名覆盖和realpath去重、原生Skills命名空间、资源根及参数包装、按需正文和动态激活、禁用和使用排序及适配缓存。插件贡献移出 |
| 自定义命令 | 用户、项目和插件的Markdown命令模板发现、覆盖和参数替换保留为来源记录。当前范围移出 |
| agents | 当前parser实际支持的name/body、工具白/黑名单、model/inherit、permissionMode、turn/effort、skills/memory/background/isolation等字段，独立SubagentStart/Stop hooks及MCP字符串引用 |
| plugins | 两种manifest位置、技能/命令/agent/hooks组合、根目录环境变量及安装和删除流程保留为来源记录。当前范围移出 |
| Hooks | user→trusted project顺序附加。保留matcher/if、command/timeout/async子集、实际5事件及子代理独立事件，以及stdin/out、exit2和各事件实际消费方式 |
| MCP | mcpServers按server整项覆盖、坏JSON处理、command/args/env或URL传输定义、disabled状态；stdio/StreamableHTTP/SSE、动态tools/resources/prompts/listChanged/elicitation、开关/重连/关闭 |
| LSP | servers按name整项覆盖、command/args/extensions、按扩展名首个匹配/惰性启动；9操作、Content-Length UTF8字节、UTF16位置及Windows URI映射 |
| 长期记忆 | Markdown/frontmatter、五类型/三scope、来源引用/locked/项目过滤、编辑/删除、验证/蒸馏/整理/衰减/审计；与会话保存分开 |
| Deck/观测 | 既有协议1、loopback/token/Origin、snapshot/messages/command及重复commandId语义；观测开关、事件/用量关联和退出flush |

记忆五类型是user/feedback/semantic/procedural/episodic，scope为project/user/knowledge；缺省路由保持procedural→knowledge、user/feedback→user、其余→project。重要度1–10及缺省5、可选confidence 0–1等输入契约由工具schema保持，不能变成任意Markdown仓库即可算兼容。

Hooks的PreToolUse传tool与JSON字符串args，最终改写进入后续裁决；PostToolUse返回不能撤销已经发生的副作用；UserPromptSubmit可拦截，SessionStart只消费实际上下文并防重复，SessionEnd不承诺崩溃必达。声明但未实际执行的Hook类型不凭文档扩成已支持功能。

MCP的工具schema透传、text/非text/空结果、资源blob摘要与提示消息格式保持实际适配层语义；分页、模板、订阅、sampling/roots等未接线能力不因SDK存在就承诺。用户已确认[ADR-0003](../../docs/adr/0003-mcp-unknown-outcome-no-replay.md)：工具请求可能已执行但结果不明时停止自动重放，持久记录未决并等待明确恢复决定；连接与能力发现仍可重连。断线回放须证明重启后也不重复副作用，不能仅凭换调用ID或readOnlyHint绕过。LSP无响应超时和shutdown改进也登记差异，不假称原版已有。

配置品牌别名、RuoCun新默认数据根、旧DAO配置读取和写回优先级已由09票及ADR-0005收口：原生独立根，兼容材料按用户显式只读声明装载，各loader顺序与来源独立保持；准确格式及凭据provenance见唯一兼容契约。格式兼容不等于自动接管旧目录，RuoCun自身会话和DAO会话隔离，不跨品牌自动rename。

### R-13 · TUI与Windows Terminal

保留内联交互、原生scrollback/选择复制、稳定历史与活动渲染区、流式编辑、任务/审批/问题/账户/模型/技能选择器、中英文/主题和状态提示。不得未经决定用全屏界面替代来源内联体验。UI只能有一个输入owner、一个协调输出owner；终端协议与用户输入在同一解码链分离，不能额外reader抢stdin。

真实覆盖中文IME、CJK/emoji/组合字符、光标/删除/换行、CRLF/CR归一、多行/超长粘贴、图片路径和Windows图片剪贴板。粘贴不自动提交，超过280个JS UTF16单位或6行的来源折叠触发与提交还原需保持；编辑Unicode修正允许作为明确平台差异登记，不能以Python索引自然不同解释丢字符。图片magic/MIME/大小及视觉能力提示与真实模型输入一致。

Esc模态优先；Ctrl+C两次2秒内退出的语义、Ctrl+B后台、Ctrl+T任务、Ctrl+G历史、Ctrl+O展开、Shift+Tab模式切换完整验收，Windows Terminal本身快捷键冲突需记录环境。连续缩放、宽高极小、长消息、流式/图形并发、焦点切换不丢输入、不残留旧帧、不删除非自有历史。仅owned终端允许确认过的视口重建策略，共享终端不得随意清屏。

终端回包分片、超时、raw generation、迟到CSI/DA/CPR/focus、paste内相似内容和dispose全覆盖。Sixel支持以真实探测为准，单图在途、串行输出、背压、resize后的epoch与锚点、防止模态/草稿/后台状态闪烁均保持；失败文本降级。嵌入帧/时序可转存数据并保留来源hash，快照外原PNG未收齐不声称生成链已复现。

正常及可控异常退出恢复ConsoleMode、cursor、paste、focus/title；强杀无法运行finally时如实记录边界并提供恢复操作。PTY、headless、状态单测只能作为自动证据，不能代替Windows Terminal可见画面、用户中文IME及真实连续窗口缩放验收。

### R-14 · Windows本轮支持范围与平台差异

Windows须覆盖本轮保留范围，而非仅终端启动。系统凭据、图片/文本clipboard、进程与持久文件等未被取消；已有分支也需实际验收。W3/W5/W6只缩减下表对应能力，明确不支持或有限提示分支仍须如实实现和记录，不能将范围移出写成原功能通过。

| 能力 | Windows必须达到的契约 | 平台差异/边界 |
| --- | --- | --- |
| Shell/进程 | 明确cmd/Windows PowerShell/pwsh/Bash调用方式、编码/环境/argv/.cmd启动；真实子孙树取消，前后台和独立runner生命周期 | POSIX组信号与Windows控制事件/Terminate不可混为同一操作；后台helper默认隐藏，交互窗口明确 |
| IPC/持久文件 | 认证token/run/epoch、最小访问ACL、重连/fencing、排他启动、占用/替换/flush错误可见 | 命名管道或受认证loopback仍需实测；HMAC不代替ACL；chmod数字不证明Windows权限 |
| 凭据 | 本机系统凭据写/取/删、账户隔离/case collision、拒绝/超时及准确文件fallback | 后端类型/失败状态真实显示，日志不含秘密；旧keyRef映射由兼容决定收口 |
| 系统定时 | W3：Windows系统级创建/列出/删除/触发明确不支持，取消Task Scheduler及Windows dispatcher补齐；来源其它平台路由保留未验 | 会话内loop继续按其职责实现，不能冒充程序关闭后仍可定时触发 |
| 唤醒 | W5：Windows本轮不提供自动防休眠保证，长任务不声明已取得系统唤醒锁 | 用户自行管理电源设置，休眠可能暂停任务；正常取消、退出和其它资源释放继续验收 |
| 图片/文本clipboard | Unicode文本、图片类型/大小/RGBA、无图片/失败不吞文本 | 文件路径图片与clipboard图片是两个入口，分别验 |
| 通知/标题 | W6：本轮只提供终端内状态/注意提示与安全标题，不发送桌面通知；NotifyUser准确说明通知去向 | 终端提示和标题不称为已发送系统通知；来源桌面分支保留记录，桌面载荷/窗口实现不列本轮交付 |
| OS沙箱 | 按[ADR-0008](../../docs/adr/0008-source-first-sandbox-parity.md)迁移DAO可选Seatbelt/bwrap及网络开关；Windows显式启用返回不支持 | 默认不开启，不要求额外Windows后端；未启用的普通Shell不能称为隔离，启用不可用明确拒绝；其它平台实机状态单列 |

Linux/macOS保留同一能力端口及合理后端划分；避免核心导入Win32依赖或假设POSIX信号/路径。构建、静态检查、自动测试、实机操作分别记录；本次可保留其它平台实机pending，但不得以它们的结果替代Windows缺口。

### R-15 · 安装、打包与发布

标准Python wheel/sdist与可安装CLI、版本元数据、锁定依赖、必要提示/语言/技能/帧/parser资源、许可、CI及完整文档仍须交付。D2移出本轮Windows独立产物，用户准备兼容Python环境；实际支持组合沿已收录路线验证，不把历史原型当最终包通过。

wheel/sdist须在仓库外隔离安装、无PYTHONPATH及开发源码依赖下运行，支持中文空格路径，资源和实际SQLite组合可用。D3采用手工停止进程、取得一致备份、安装更新及手工恢复流程，不承诺自动跨版本原地迁移或失败自动回退；未知/损坏格式拒绝且保护原数据。卸载与数据位置说明继续保留。OS沙箱保持ADR-0008边界，不增加管理员隔离组件。

持久runner必须调用同版本已安装Python产物的明确内部角色入口，owner退出后的接管、取消与恢复仍须真实可运行。Windows系统级定时角色按W3移出；其它来源平台调用保留对应关系与未验状态。D2移出的冻结exe/onefile解包生命周期不列本轮门禁，不能连带取消标准包后台运行行为。内部角色不作为用户新业务命令泄漏。

发布配套含标准包安装/手工升级/卸载、配置与会话位置/一致备份恢复、权限与隔离、实际平台支持、模型与扩展兼容差异、贡献/开发测试、版本/release notes、构建环境/commit/lock/OS/arch、产物hash及来源许可清单。Windows本机CI及来源其它平台构建/静态检查配套仍保留，桌面IME/缩放独立HITL；保留上游MIT及必要版权。已取消的独立产物与自动回退不以空报告冒充完成。本轮调整记录，不执行公开发布或恢复产品开发。

### R-16 · 允许的实现差异与待决事项

允许：Python命名/类型/异步API、语言绑定底层库、Windows能力后端、非TTY输出适配、品牌身份和真实环境信息、为自身完整恢复补齐的状态字段、对危险无效路径的边界修复。每项仍须记录来源行为、目标行为、理由、任务/ADR、案例和证据。性能优化不得改变可见排序、参数、权限或持久确认边界。

并发、SQLite/IPC/MCP及跨品牌配置/写回路线沿ADR-0005，MCP结果不明停止重放沿ADR-0003；本轮只按ADR-0010缩减明确选中的保证，未选R2/R4/R5及其它功能继续保留。首轮工具链不冒充最终发行支持范围；TUI和标准Python包仍由实际产品证据验证。技术路线不等于产品验收，新的范围冲突才请用户取舍，源码/测试/官方文档能查明的事实由Codex调查。

## 测试决定（Testing Decisions）

2026-11-10用户调整测试基线：[ADR-0009](../../docs/adr/0009-source-test-baseline.md)优先迁移并通过DAO已有测试，后续不主动新增大量边界/故障/组合测试。以下资产分类和矩阵用于来源追踪，超出来源测试的排列不再作为逐票强制新增门槛；必要工程可运行确认、已捕获缺陷最小复验及真实未验范围分别记录。

### T-01 · Oracle、状态与故障归因

测试预期依次来自冻结实现及既有测试、已确认规格/ADR、经确认的修复决定。文案/注释冲突通过受控source运行确认，避免以当前Python输出回填期望。source oracle在独立可写快照副本、合成HOME/config/session和自有Git fixture执行，不修改活动参考、不借真实用户状态。

验收矩阵每行保留实现/自动/Windows/HITL/其它平台状态；必要时展开子案例。故障归类为SOURCE-DEFECT、PORT-REGRESSION、INTENTIONAL-DELTA、ENV或UNVERIFIED，分别保存source与port结果。静态疑点先用SOURCE-CANDIDATE，不称已证实原版故障。已知缺陷不自动豁免完整规格；应修复/明确错误边界，确需改变范围交用户决定。

### T-02 · 沿用的测试入口与资产

已确认的语义入口直接沿用，不再请用户重复确认：

1. 原测试对模块外部行为的断言、数据fixture与纯算法输入输出；TS绑定断言按S重写，D/R优先复用数据和协议。
2. 现有CLI/REPL/TTY/一次性入口、模型transport/fake HTTP/SSE、真实工具/文件/进程、会话存储和恢复脚本。
3. Hook/stdin-out、MCP、LSP、Agent Deck现有外部协议与扩展发现fixture。
4. 已有后台等待/恢复、持久化、memory/cache/reflect验收脚本的意图和证据口径；专题replay按实际是否调用模型分类。
5. 原评估runner、16个任务定义、评分/trace/HTML材料及Harbor/TerminalBench/SWE等已有适配意图；不把外部未收齐材料视为已可运行。
6. 已明确要求的真实Python Windows Terminal操作、Windows能力探针、真实模型任务和干净安装/升级/卸载验收。

ADR-0010覆盖上述入口的本轮执行范围：Windows只验保留能力及准确不支持分支；干净安装与手工升级/恢复继续，独立程序和成套live评分不作门禁。资产和原预期保留；范围移出项不写成DAO原断言已通过。72–74评估工具/任务定义/fixture仍须迁移，实际付费运行另需明确授权。

215个来源测试、58个脚本、16个task.json及85个独立fixture逐项在对应表/研究附录可追溯。优先覆盖真实CLI、协议及进程等最高可用层；只在无法从高层观察原子性/竞态时补有限状态或故障测试，不测试私有字段、线程数、框架widget树等偶然实现。

### T-03 · 已确认的新增测试入口

用户于2026-11-05回复“全部采用（推荐）”，一次确认以下全部五项入口及统一驱动子套件；[确认记录](issues/01-test-entrypoints.md)已解决。它们只改变开发验收组织，不增加产品业务功能。入口已确认，工程配置、依赖安装与执行尚未开始；既有semantic seam与Windows/HITL目标不重新审批。

| ID | 建议入口 | 用途/覆盖 | 影响与状态 |
| --- | --- | --- | --- |
| T-N1 | `python -m pytest`；live/HITL/安装按显式标记不混入默认离线运行 | 承接Vitest及纯评估断言，按来源语义改写；async插件随路线锁定 | 已确认；待工程配置 |
| T-N2 | `python -m ruocun_acceptance <suite>`，suite=`oracle/offline/runtime/protocol/live/terminal/install` | **一个统一高层验收驱动**；组织既有CLI/协议/进程/终端/安装入口，输出统一case证据清单；live显式选账户与成本上限 | 已确认；开发期模块位置见对应表NEW-11；不向产品添加远程调试或绕权限接口；可取消/可清理 |
| T-N3 | `python -m ruff check .` | 承接lint，配置与格式规则保持统一 | 已确认；待工程配置 |
| T-N4 | `python -m mypy`（仅迁移核心及明确类型的支撑范围） | 承接typecheck；SDK边界窄适配，不为类型检查改变协议接纳范围 | 已确认采用mypy；若实验有具体阻碍再提替代 |
| T-N5 | `python -m build` | 构建wheel/sdist并供install套件在干净环境验证；D2移出独立程序构建 | 已确认；公开工具链按已收录路线锁定 |

T-N2仅作为统一验收驱动，以实际产品入口和已有协议注入合成模型/扩展/配置。开发环境须安装测试支撑包使该模块可导入，用户标准包不因此增加测试依赖；干净安装套件不能借开发源码路径使产品冒充已独立安装。真实故障切点优先复用既有probe和恢复脚本，使用独立进程/文件证据；若产品实现确需新增内部故障注入端口，先在本表登记其最高层边界、仅测试可达条件与影响，再集中补充确认，不能默认为已授权长期隐藏API。

上述一次确认已满足用户要求及[to-spec](C:/Users/PC/.codex/skills/to-spec/SKILL.md)的测试入口确认步骤，后续直接采用，不再重复询问。项目tracker要求前置满足才ready-for-agent；终端/平台/存储/发布等技术依赖仍按原地图推进，不因入口获批就把整个迁移标为可立即实施。

### T-04 · 自动化测试层次与最小覆盖

| 层次 | 必须验证 | 证据限度 |
| --- | --- | --- |
| 数据/请求golden | 提示生成、schema/可见性、provider参数、消息转换/usage、格式解析/覆盖、权限规则及代码图/评分纯函数 | 比较真实边界行为，模型生成文本不作逐字质量golden |
| 协议与CLI集成 | fake模型SSE/Responses、Hooks、MCP三传输/重连、LSP、Deck；完整启动/参数/命令/禁用 | 协议fixture不能证明供应商当前支持或真实终端画面 |
| 真实进程与存储 | 来源已有工具屏障/取消/迟到事件、owner/epoch、runner启动接管、SQLite/journal/附件/权限案例及必要最小确认 | 复用已有缺陷复现，按ADR-0009不再扩故障排列；未验断电/注销/重启能力不推断 |
| Windows本机功能 | 保留Shell/进程树/IPC/文件/凭据/clipboard；W3/W5/W6准确支持边界与终端提示；OS隔离沿来源 | 不支持分支通过只证明准确说明，不等于原系统能力实现；Job/HMAC/WSL不扩大保证 |
| 真实终端与安装 | 保留WT-01..09真实操作、中文IME/resize；仓库外标准Python包干净安装与手工备份更新恢复 | D2独立产物和D3自动回退移出；headless/PTY/CI不能填写用户体验accepted |

来源已有故障场景和已证实缺陷复用现有输入/独立预期做最小复验；既有25项运行时probe仅是历史技术证据，不自动升级成每票新增矩阵。产品实际路径只做必要确认。所有本次runner/子孙进程/测试凭据/临时资源保留拥有标识与退出回执，避免遗留影响后续运行。

### T-05 · 真实模型任务与评估

V1移出本轮成套真实模型成绩及评分门禁，不执行原16任务默认各3次的付费跑批；75保留历史票/来源且范围移出，不记通过。16个任务定义、fixture、运行/评分/trace口径与72–74评估工程仍保留；TS runner适配Python产品，离线与live明确区分。冻结RUNS=3、有效timeout等作为来源协议记录，不当作本轮已完成成绩；未来若单独授权运行，按实际次数/条件报告，不能用一次成功冒充原条件。Harbor/SWE/TerminalBench材料不足如实分类。

按ADR-0009，本轮不新增覆盖全规格的组合真实任务作为默认门禁；按V1也不要求另一组成套live评分替代75。76继续覆盖保留功能的来源离线runtime/protocol行为与必要工程确认，原live资产保留、未运行结果如实登记。任何真实模型调用仍需明确授权和预算，本次范围调整不调用模型。

每次记录产品commit、参考hash、模型ID/provider/endpoint、关键参数/seed支持、任务/fixture版本、运行次数、timeout、成功/失败/环境无效、结果断言、轨迹/diff、工具使用、耗时和费用。真实质量按任务断言及体验判断；不能以模型completed或source历史70/89当RuoCun成绩。已有heldout开发暴露据实标记，不声称严格未见。live执行前沿既有授权选择合成工作区及明确成本预算，不在本轮规格工作中调用付费模型。

### T-06 · Windows终端与安装验收

终端使用实际Python程序、真实可见Windows Terminal；覆盖矩阵WT-01..09，用户亲自操作中文IME及窗口连续缩放。记录OS/Terminal/Python/backend/依赖、Shell、IME、字体/DPI、快捷键与paste设置、几何、截图/视频、业务接收内容hash和状态日志；自动内容/状态一致性与用户主观体验分开。原型通过后，最终产品与安装产物仍须复验。

安装在仓库外新venv/干净普通用户环境，移走源码/关闭PYTHONPATH，不依赖Node/Bun、开发配置或外部preview资源。仅验本轮标准Python包：版本、资源、SQLite真实库、外部扩展、runner内部角色、正常/异常恢复、手工停进程备份/更新/卸载与数据保留。独立exe及自动升级回退按D2/D3移出；Windows x64先验，其它组合据实pending，不扩展支持声明。

## 完成标准与迁移门禁

2026-11-10补充：按ADR-0006/0010分别报告“本轮范围实现及自动门禁完成”和“人工体验accepted后的交付”。77/78只汇总保留能力及诚实不支持分支的真实证据，85继续等待两票完整人工验收。V2移出原耗时≤1.20/峰值内存≤1.30及正式采样保证；保留有限本机观测并修明显卡顿、失控内存和取消故障。未测结果仍未验，不把有限观测写成量化性能达标。

### 完成标准

1. 805来源成员均有实际对应、保留理由或经确认移出处理，MM ID不遗漏；43工具、52命令、8 core技能和动态通道逐项记录本轮支持/不支持边界，不能宣称未做的来源功能全通过。
2. 本轮R条款和矩阵案例有来源语义及必要工程证据，已实现、自动通过、Windows结果、用户体验与范围移出状态独立；不扩建超来源测试排列。
3. Windows保留能力和不支持分支通过实际检查，终端/标准包安装HITL由用户accepted；W3/W5/W6是明确范围差异，不是假成功或skip清空失败。
4. 正常保存恢复、普通代理checkpoint、前后台、未知副作用及附件异常满足已保留契约；R1/R3按准确统计口径和材料不足拒绝处理。owner/fencing/事务/已修复SQLite底座不降级。
5. 提示/工具schema/参数/streaming、配置/扩展发现/协议与权限契约有来源对照golden及集成证据；所有有意差异可追溯。
6. 原版已复现故障、静态疑点、环境/材料不足及迁移回归分别闭环；阻断核心数据/权限/Windows功能的项未解决则不宣告完整完成。
7. 测试资产保留D/R/S/P处理记录，本轮来源离线、协议/进程/终端/标准包安装门禁完成；V1范围移出与未来另行授权的live结果分别记录，不夸大来源成绩。
8. 完整文档、标准包安装/手工备份更新/卸载、构建/版本/hash/资源/许可与CI配套齐备；D2/D3移出的产物/自动回退不作必交。Linux/macOS实机pending及有限性能观测边界如实保留。

### 迁移顺序与前置依赖

以下是按职责和证据制定的建议顺序；具体路线仍由既有票收口，阶段不可被当作范围裁剪。

| 阶段 | 交付和出口 | 前置 |
| --- | --- | --- |
| M0 决策收口 | 终端/协议/系统能力/文件IPC/SQLite/打包最小验证完成，08–13路线形成可执行决定，14核验通过；新增入口已一次确认 | 06、07、15、17、18、19、20、22实验及08–14决定 |
| M1 契约与基础 | Python工程、类型/配置/提示/schema/权限/持久化接口及Windows端口；来源golden可跑 | 相关08/09/11/12决定；不能越过各自未解库/平台门禁 |
| M2 核心链路 | CLI→模型流→工具→权限→事务→自身恢复，最小真实任务与安装入口可用 | M1；只标阶段完成 |
| M3 本轮运行时 | 队列/后台runner/agent/fork/wait/取消/worktree/恢复决定、保留工具命令与准确不支持路由 | M2及08/18/19；R1/R3恢复边界单列 |
| M4 扩展与上下文 | 保留的Skills、Hook、MCP、LSP、Deck、记忆、反思、代码图及观测 | M1/M3相关边界及09/15 |
| M5 本轮终端与Windows | 完整TUI及保留Windows能力、不支持分支与对应WT/WIN验收；欢迎图/向导/面板/图片/凭据仍在范围 | 06/10/17及真实产品路径；可早做原型，不能延后才发现架构阻碍 |
| M6 本轮范围交付 | 保留矩阵门禁、标准Python包安装复验、完整文档/许可/CI；V1/V2不作量化成绩门禁 | M2–M5本轮范围、12/14及用户体验 |

| 未关闭决定 | 当前推荐及影响 | 既有依赖票 |
| --- | --- | --- |
| 来源沙箱兼容 | ADR-0008按用户要求采用DAO的可选macOS/Linux能力及Windows不支持边界；D22调查收口但历史A仍FAIL，不新增Windows后端 | [10](../ruocun-discovery/issues/10-terminal-windows-decision.md)、[20](../ruocun-discovery/issues/20-windows-psec-experiment.md)、[22](../ruocun-discovery/issues/22-windows-token-psec-experiment.md) |
| 安装发布 | 本轮按D2只交标准Python包；既有onedir实验保留但不作最终交付，手工备份更新和完整资源/角色仍由79/81/83验证 | [07](../ruocun-discovery/issues/07-python-distribution-experiment.md)、[12](../ruocun-discovery/issues/12-install-release-decision.md)、[21](../ruocun-discovery/issues/21-development-bootstrap-decision.md) |
| 最终映射/实施就绪 | 本附件提供全量拟对应和建议顺序；13/14仍须按实际实验结论收口，不因有spec就伪闭合 | [13](../ruocun-discovery/issues/13-module-sequence-decision.md)、[14](../ruocun-discovery/issues/14-spec-readiness-check.md) |

## 已确认的范围排除（Out of Scope）

- 旧DAO会话及其内部数据库导入/迁移；格式兼容不要求两个产品共享同一活会话。RuoCun自身保存恢复按已保留契约及R1/R3准确边界实现。
- ADR-0010明确移出：Windows系统级定时/Task Scheduler及dispatcher补齐、Windows自动防休眠、桌面通知、Windows独立程序、自动跨版本原地迁移/失败自动回退、成套live成绩及量化性能保证。75/80保留原票与来源且范围移出，不算resolved。
- ADR-0014移出NotebookEdit专用工具（20）、自定义Markdown命令（37）及组合插件（50）。保留原票号、来源资产与验收ID，记录范围移出和未运行结果。完整TUI按原范围交付并实际验收。
- 本轮Linux/macOS实机验收；保留跨平台设计和后续验收状态，不排除其设计/适配工作。
- 公开发布和推送研究分支；本地实现、测试与集成已获实施阶段授权。
- 核心业务保留TypeScript/Node/Bun作为运行依赖不符合目标；外部声明命令与TS语言测试样例/数据不受此限制。

不承诺来源未实现的完整远程agent执行、任意MCP未接线能力、任意YAML/dotenv新语法、任意第三方语言服务器随包安装、任意外部副作用exactly-once或尚未实测的断电/重启保活。这些来源边界不扩张ADR-0010的选项清单；未选中的Windows补齐和恢复保证继续保留。若希望新增，按新范围决定记录。

规格编写阶段没有执行编码/依赖安装/付费跑批；当前按用户停止边界暂停产品开发。此次范围与执行减负确认只调整项目记录，不恢复实现、不调用付费模型，也不扩张远程发布授权。

## 补充说明（Further Notes）

本规格替代初始化概要作为迁移权威正文；旧入口保留指针。对应表和矩阵是持续维护记录，不能随实现进展另造并行真相。每个行为变化同步规格/差异决定、模块对应及案例证据；源码路径只在对应表维护，规格以稳定职责和契约为主。

本次文档校验仅证明记录覆盖和链接/来源一致性，不表示任何产品自动测试或Windows体验通过。新增入口已确认，具体实施票仍须满足各自技术前置才能按项目tracker标ready-for-agent；当前范围不重新采访，地图未关闭票不凭文档或入口确认直接解决。

## 实施期协作补充

基础工程入口、技术路线与产品交付分别记录。03等已完成工程证据保持，发布路线D12的标准包/独立产物双形态决定仅在D2指定范围由ADR-0010替代；85按本轮支持范围、真实依赖及验收矩阵核对，不以早期工程入口通过代替产品交付。

用户已确认[ADR-0004](../../docs/adr/0004-final-batch-human-acceptance.md)：人工体验统一到最终77/78/85，前期原型与实现票保留未验清单，不由逐票人工操作卡住独立工作；本轮范围按ADR-0010，恢复实施仍等待用户明确指令。
