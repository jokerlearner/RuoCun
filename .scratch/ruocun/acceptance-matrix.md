# 原功能 → 验收案例 → 实现状态 → 验证证据

## 2026-11-13 B方案扩展

本扩展不改原迁移覆盖分母；[AC01–AC16逐项证据](../deepseek-compaction-20261113/checklist.md#验收追踪表)与[最终B-r3交付](../deepseek-compaction-20261113/delivery.md)为权威。实现、自动技术出口及独审通过；Windows Terminal视觉/缩放、用户体验和真实模型质量分别保留未验。R1全量实际1734pass/1旧目录断言fail/4未选中，原失败经适配及受影响复验收口；R2/R3最小修复按ADR-0015复用未变证据，不伪称B-r3全量重跑。最终314成员绑定、Mypy291源/Ruff及纯包公开三节点通过。

## 批次06技术验收

22、23、25、33、55按五票出口分别验收；[集中交付](../ruocun-next24h/evidence/batch-06/integration/README.md)另记实际全量、产物与纯安装。77/78完整人工出口保持pending。

| 子案例 | 实际验证范围 | 证据与限制 |
| --- | --- | --- |
| B06-CONFIG（25 / TOOL-Config / CMD-Config） | 普通四写真实journal已确认；项目/用户、泛点路径、损坏配置及DACL前置拒写；当前auto、重开plan、状态查询无模型 | [独审](../ruocun-next24h/evidence/review/b06-config-review.md)。无Config热重载；发布后的未知不当成前置拒绝 |
| B06-WEB（22/23） | 默认产品真实HTTP/TLS到受控服务，实际模型消费抓取/搜索、缓存/截断/抽取、HTTP400回退原文；no-web无新增网络或抽取 | [抓取](../ruocun-next24h/evidence/review/b06-webfetch-review.md) · [搜索](../ruocun-next24h/evidence/review/b06-websearch-review.md)。不访问真实DDG或付费模型 |
| B06-MAP（33 / MEM-04） | 7grammar、排名、预算、文件限额及mtime-size；普通工具激活/编辑后刷新，启动只增加一次尾system | [独审](../ruocun-next24h/evidence/review/b06-repomap-review.md)。源整组与必要技术回执复用，不重复扩测 |
| B06-LSP（55 / EXT-11） | 9操作、UTF8分帧/UTF16位置/Windows URI，惰性同步、取消和实际进程关闭；真实TypeScript服务器与独立协议证据分开 | [独审](../ruocun-next24h/evidence/review/b06-lsp-review.md)。不把单语言服务扩张为所有server/平台通过 |

## 批次05技术验收

六票为26、46、51–54；逐票来源测试、普通入口和独立复核见[批次记录](../ruocun-next24h/batch-06.md)。批末全量与隔离安装单独记录，不以某个母案例通过代替所有组合验收。77/78完整人工出口保持pending。

| 子案例 | 实际技术出口与边界 | 证据 |
| --- | --- | --- |
| B05-SESSION（26 / REC-04/14 / CMD-session等） | 普通切换/分支/命名/导出/clear、Hooks先结束后开始、活owner拒绝；暂停与latest原ID，附件/恢复工作树保护 | [会话](../ruocun-next24h/evidence/review/b05-sessions-review.md) · [暂停](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) |
| B05-MONITOR（46 / RUN-09 / TOOL-Monitor） | 真实命令行输出/停止，persistent忽略超时，owner丢失保留历史、不重新执行 | [独审](../ruocun-next24h/evidence/review/b05-monitor-review.md) |
| B05-MCP（51–53 / EXT-08/09 / CMD-mcp / ToolSearch） | 三传输、覆盖/禁用、schema/能力发现和搜索激活、原生写回/重连；依赖锁SDK1.30.0 | [stdio](../ruocun-next24h/evidence/review/b05-mcp-cli-review.md) · [HTTP](../ruocun-next24h/evidence/review/b05-http-review.md) · [能力](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) |
| B05-UNKNOWN（54 / EXT-10 / RUN-07） | 远端副作用一次后断线，74且真实journal unknown，同会话换ID无模型/远端执行；子专属MCP关闭、handoff重绑及配置摘要 | [断线独审](../ruocun-next24h/evidence/review/b05-mcp-recovery-review.md) · [子MCP](../ruocun-next24h/evidence/review/b05-agent-mcp-review.md) |

## 批次03技术验收

| 子案例 | 实际验证范围 | 结果 |
| --- | --- | --- |
| B03-COST（28 / WIRE-06 / WIRE-11 / REC-07） | 普通入口重开后保留累计 token，新进程费用与预算重新计数，状态查询无模型请求 | 独立通过。[回执](../ruocun-next24h/evidence/review/b03-manual-cost-review.md) |
| B03-RECOVERY（29 / WIRE-09 / MEM-03 / CMD-compact） | 合成 HTTP 429 后显式选账户，旧工具不重放；摘要失败保留原上下文和等待，重开仍暂停 | 独立通过。反思和其它 MEM-03 子案例另验。[回执](../ruocun-next24h/evidence/review/b03-model-recovery-review.md) |
| B03-MANUAL（45 / CMD-tasks） | 真实 SQLite 创建、读取、更新、停止与重开；普通 `/tasks` 接线 | 独立通过。[回执](../ruocun-next24h/evidence/review/b03-manual-cost-review.md) |
| B03-LOOP（47 / CMD-loop / RUN-09） | 普通入口周期排队、off、退出以及失败后旧 timer 停止 | 独立通过。[回执](../ruocun-next24h/evidence/review/b03-loop-review.md) |
| B03-FOREGROUND（67 / WT-04 / WT-06 / CMD-copy） | 只读面板、Unicode、前台所有权交接 | 独审和实机技术通过。[实机](../ruocun-next24h/evidence/n18/wt/runs/20261111T101837Z-52f7cc/README.md) · [交接证据](../ruocun-next24h/evidence/batch-03/n67/README.md) |
| B03-NOTIFY-WELCOME（63、68 / WT-07 / WT-08） | 通知标题、焦点清除、Sixel 首帧与原图清晰度 | 实机技术通过。[实机](../ruocun-next24h/evidence/n18/wt/runs/20261111T101837Z-52f7cc/README.md) |

## 批次02技术验收

细分证据见[批次记录](../ruocun-next24h/batch-02.md)和[b02-r1构建](../ruocun-next24h/evidence/batch-02/integration/README.md)。77/78完整人工出口保持pending。

| 子案例 | 已落地与自动证据 | 未完成/待验 |
| --- | --- | --- |
| B02-BG-WAIT（16） | 固定真实run、等待唤醒、消息/delivered事务；普通CLI三请求/一次执行/一次通知，unknown拒成功ack；16独审resolved | 不表示通用代理或调度全部完成 |
| B02-REC（17 / REC-08 / CMD-recovery） | 查询、resolve、decide与持久授权。普通同步与后台代理实际重开以新run继续，旧工具不重放，同决定幂等 | 原权限与实际工具恢复按逐票证据 |
| B02-RENDER（65） | 来源回执通过。用户确认真实WT缩放、草稿和滚动正常，深浅主题输入均清楚 | 最终体验归77 |
| B02-IMAGE（64 / WIN-08） | 显式剪贴板、路径与视觉内容组合；真实WT上传的PNG哈希与64×32合成图相同 | 最终体验归77 |
| B02-MODAL（66 / WT-06 / CMD-model/account/accounts） | 审批owner独审、实际合成HTTP账户/模型切换；用户在真实WT完成问答多选、账户Esc | 最终体验归77 |
| B02-NOTIFY（63 / WIN-10 / TOOL-NotifyUser / WT-07） | 终端best-effort、安全标题、焦点/按键清理、受控dotenv禁用值；来源及独审回执 | 终端渠道实机已在批次03收口 |
| B02-WELCOME（68） | 原帧、同reader探测、CPR、帧队列与备用图通过定向自动验证。真实WT写出原始图形，用户确认清楚 | 已在批次03收口 |
| B02-FIRST-RUN（69 / ENT-02） | 语言、服务商、校验、账户及信任引导已接入。普通入口保存、重启、失败保留与拒信任通过独审 | 真实终端体验归77 |
| B02-AGENTS（38 / 39 / 40 / 41） | 同步和后台真实子请求、角色定义及授权、精确fork目录、取消、Git隔离与未知回执独审 | 后续任务类型和Hook/MCP生命周期按各自任务票 |

Status: maintained / engineering-partial
更新：2026-11-11。本矩阵是产品验收状态的唯一权威表；[规格](spec.md) 定义契约，[对应表](module-map.md) 定位具体文件。

本表在里程碑汇总，日常实施与定向结果读取任务票及[当前批次](../ruocun-next24h/batch-06.md)。更新节奏见[ADR-0015](../../docs/adr/0015-batch-validation-and-packaging.md)。

当前完整TUI继续验收。`TOOL-NotebookEdit`、`EXT-04`和`CMD-plugin`保留来源案例及ID，登记范围移出。Skills、Hooks、代理等独立通道及其他保留案例继续验收。[ADR-0014](../../docs/adr/0014-terminal-and-scope.md)

## 首版历史出口

首版按[ADR-0011](../../docs/adr/0011-python-coding-mvp.md)，覆盖七工具、逐轮文字审批、前台取消、正常保存重开与标准包；后续阶段A的新增覆盖见下方A子案例。原全规格案例族保留ID与历史要求；“首版部分通过”不代表图片/后台/队列/动态扩展/完整TUI已实现，也不改变原82票完成数。源测试、合成产品验收、真实模型和人工体验继续分开。

| 子案例 | 实际覆盖与证据 | 自动状态 | 人工/其它平台 |
| --- | --- | --- | --- |
| MVP-TOOLS | 六文件/计划工具91来源+5必要适配、Bash28定向；[M01](../ruocun-mvp/evidence/m01/README.md)、[M02](../ruocun-mvp/evidence/m02-shell/README.md) | 已独审；只覆盖声明子集 | 不代表原全部工具/语法通过 |
| MVP-LOOP | 普通回答、空重试、完整推理现场、JSON清洗、配对、拒绝、context limit、exec失败屏障；[M03](../ruocun-mvp/evidence/m03/README.md) | 9循环/执行来源断言通过；r2全量601项通过 | 真实模型未验 |
| MVP-CLI-REC | 七工具真实改写/运行、拒绝不写、正常退出后第二进程恢复；普通文字两轮输入；[M03](../ruocun-mvp/evidence/m03/README.md)、[M04](../ruocun-mvp/evidence/m04/README.md) | 现有合成服务接线确认，文字两轮root/独审均通过 | 管道输入非真实Terminal |
| MVP-CANCEL | 实际runtime SIGINT→取消模型请求；Bash层实际子/孙句柄signaled；未知结果不重放 | 独审通过；信号后CLI exit130，进程退出另有真实句柄证据 | 真实按键/视觉/缩放pending |
| MVP-PKG | r2 sdist→wheel=direct wheel；64包成员源码/安装/产物字节绑定；实际SQLite3.54.1；仓库外纯产品环境 | 构建/固定运行库/仓库外安装通过；[产物](../ruocun-mvp/evidence/m03/artifacts.json) | CPython3.11.9/Windows x64；Linux/macOS未验 |
| MVP-EXIT | r2全量、五入口、双轴独审、公共记录与保存点 | 601项通过、五入口及双轴通过；自动技术出口完成 | 人工体验pending，不回填accepted |

## N0／08新增子案例

| 子案例 | 实际覆盖 | 自动状态 | 边界 |
| --- | --- | --- | --- |
| N0-READ-IMAGE | Read图片、独立限额/vision、完整结果、批末投递与重开一次性 | 模块来源＋必要适配/普通CLI/独审通过 | 不包含真实视觉模型质量 |
| N0-TODO-HEADLESS | 完整Todo中英元信息、完成提示及首批规则 | 原case/真实CLI/独审通过 | 清单完成不等于质量验收 |
| N0-WIRE10 | 推理空截断通知、低effort收敛/forced回退、有界空重试及恢复坏JSON清洗 | 真实SSE原例红→绿、loop/全量通过 | 后台/复杂批调度未覆盖 |
| N0-EXIT | 固定70c7464、90成员、SQLite3.54.1与实际安装 | 687项/五入口/构建及独审通过，[N0集成](../ruocun-next20h/evidence/n0-integration/README.md) | 人工/真实模型/Terminal pending |

母案例保留完整范围，以上子路径的通过不代表权限/所有失败排列/后台或体验已完成。

## N1／19已验子路径

| 子案例 | 固定r1自动通过范围 | 后续或未验 |
| --- | --- | --- |
| N1-PERM | A规则/设置/审批、B完整解析、native层级/区外许可及普通入口最终参数、plan执行硬门 | 分类器24、Hook改参及12批量执行后置 |
| N1-RUN | FIFO/持久输入、正文冻结、草稿/审批、旧delta退休和普通入口暂停/关闭 | 后台15–17及真实Terminal/resize未验 |
| N0-SKILLS-CONTROL | 三toggle＋两选择语义、完整目录/禁用/覆盖、原生保存与TTY专用simplify | 动态35、安装36分票推进 |
| N2-SEARCH | 原38项、mypy4及双语/schema、ListDir/Glob/Grep普通入口、/files和零配额片段 | /files本进程记录；不声称跨重启读图 |
| N2-EDIT | Edit/Write来源与既有适配49项、真实五切点15次重开，独审关键14项及两代表切点 | Hook及全部REC-05母族不代填，待后续统一包 |

各条完整命令/来源/限制见[固定r1集成](../ruocun-next20h/evidence/n1-integration/README.md)与[本批独审](../ruocun-next20h/evidence/review/README.md)。全量1154项/3排除、类型/格式/离线、固定包与独审已通过；子路径结果不覆盖人工Terminal/真实模型或完整母族。

## 使用与证据规则

阶段A沿ADR-0012新增下列局部覆盖；[A集成记录](../ruocun-advanced-a/evidence/integration/README.md)是本批回执入口，阶段A自动技术出口已通过（669项、五入口、独审两轴剩余0）。原全规格母行保留，文字入口的通过不覆盖忙时队列/完整TUI/反思/后台。原票仍按全条件判定，人工状态继续pending。

| 子案例 | 实际覆盖 | 当前自动状态 | 未验范围 |
| --- | --- | --- | --- |
| A-INSTRUCTIONS | 原生/显式兼容产品指令顺序、去重、Git边界及AGENTS隔离 | 7项来源/适配、模块独审及普通CLI定向通过 | 阶段A自动出口通过 |
| A-SKILLS | 静态发现、8core正文、model/user调用、启动条件扫描与只读禁用集 | 25项模块独审通过，普通CLI按需/手动调用定向通过 | 选择/禁用写入、35动态、36安装、插件/TUI未完成 |
| A-CONTEXT | 估算/窗口/缓存审计、usage/effort等7命令、成功摘要及失败保留 | 模块24+9项及独审通过，普通CLI压缩后继续/账本投影定向通过 | 反思、后台等待及完整调度未验 |
| A-EXIT | 固定源bccbb57、87包成员及SQLite3.54.1、五入口与双轴 | r2全量669项、五入口/仓库外安装通过；两轴剩余0 | 真实模型/Terminal/人工未验 |

当前测试投入按[ADR-0009](../../docs/adr/0009-source-test-baseline.md)：默认以DAO已有测试语义迁移/通过为基线，以下案例族用于能力与证据追踪，不要求逐票新增超来源的所有失败/恢复排列。已有未验项继续实记，来源测试通过不冒充最终体验或性能测量通过。

完整迁移历史层仍保留[ADR-0010](../../docs/adr/0010-selected-scope-and-lean-workflow.md)的R1/R3/W3/W5/W6/D2/D3/V1/V2决定与原始案例ID；当前首版以顶部ADR-0011子范围和出口表为准，评估工程等高级能力后置。既有07与Session/cost证据保持，范围移出或后置不等于完成，不能声明DAO原功能全部通过。

- 实现、自动、Windows和HITL按各行及子案例分别记录；前置研究和技术探针不能填入产品通过列，来源对照仅在相关工程案例登记，业务仍须产品路径验证。
- [D11复用清单](../ruocun-discovery/research/11-test-replay-gates.md)登记374项来源资产的门禁/责任，不是第二套实现状态表。D07/D17等最小技术证据的限定结果在对应决策票，不能据此将PKG/WIN产品案例勾通过。
- 每行是案例族：按“有效/非法/边界/取消/恢复”等动作展开为稳定子ID（如 TOOL-Edit.01），保留母行，不以一条冒烟覆盖全族。工具 schema 和命令优先级需从冻结定义/既有测试建立 oracle。
- Oracle 优先：冻结参考实现+已存在测试 → 已确认规格/ADR → 经确认修复差异；README/注释与实际行为冲突时登记。实际未运行的静态判断写“待oracle确认”，不得记为原版已故障。
- 实现状态与自动测试、Windows结果、用户体验分别维护。状态允许未开始/进行中/已实现；结果允许未验/部分通过/通过/失败/环境无效；HITL pending/accepted/not-required；Linux/macOS目前均后续实机。
- 每份证据至少含：case/subcase、来源/产品commit与参考树hash、OS/终端/Python/依赖lock/SQLite实际运行库、命令或操作、隔离输入/预期/实际、退出状态/日志hash、进程及临时资源清理。live加模型/端点/参数/次数/时间/成本；终端加IME/字体/DPI/几何和截图/用户确认。
- 失败必须写故障ID及原始证据。source与port分开复现，测试预期不能从Python当前输出倒推；修改oracle需要来源或确认决定。未经确认的行为变化不靠更新测试“修绿”。
- MM链接定位源路径和拟目标；外部协议、模型请求、CLI、真实进程和真实终端是主要验收层。具体新测试命令见规格T-N表；用户已一次确认全部五项，实施/执行状态仍单独维护。

## 初始 AC 域的覆盖关系

| 原ID | 当前案例族 |
| --- | --- |
| AC-01 | ENT、CFG、CMD-model/account/accounts |
| AC-02 | WIRE、RUN、TOOL、PROMPT契约（WIRE-01） |
| AC-03 | RUN、REC、CMD-tasks/loop/recovery |
| AC-04 | TOOL-Read/ListDir/Glob/Grep/Write/Edit/Bash/BashOutput/KillShell、WIN-01/02/04。来源TOOL-NotebookEdit保留为范围移出记录 |
| AC-05 | PERM、RUN-05/06、CMD-plan/mode/yolo/bypass/permissions |
| AC-06 | REC、CMD-resume/session/branch/rename/export |
| AC-07 | REC-13、CMD-rewind/restore、TOOL-EnterWorktree/ExitWorktree |
| AC-08 | MEM、WIRE-06/11、TOOL-MemoryRead/MemoryWrite、CMD-compact/context/cost/memory |
| AC-09 | EXT-01..05、SKILL、CMD-skills/agents及builtin |
| AC-10 | EXT-04/06/07、CMD-plugin/hooks |
| AC-11 | EXT-08..10、TOOL-ToolSearch、CMD-mcp |
| AC-12 | WT-01..09、CMD-lang/theme、WIN-08 |
| AC-13 | EXT-11/12、MEM-04/05、WIN-07/10 |
| AC-14 | WIN-06、TOOL-Schedule/CronCreate/CronDelete/CronList |
| AC-15 | TEST、PKG、REC-15/16 |

## 全量案例

以下各表“自动证据/Windows/HITL”三列分别记录，不合成笼统完成状态。Linux/macOS全行均为“后续实机”，静态/构建通过时另外附证据，仍不改为实机通过。


### PKG

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="ent-01"></a>ENT-01 | 安装后的启动/版本/帮助 | 仓库外、中文空格路径运行 console 命令及版本参数 | 名称 RuoCun、版本一致，资源可读，退出码正确 | [MM-483](module-map.md#mm-483) | 既有 CLI/协议/模块行为 | 首版普通文字Agent已实现；其余路由后置 | [M03产物/闭环](../ruocun-mvp/evidence/m03/README.md)与[M04独审](../ruocun-mvp/evidence/m04/README.md)；r2全量601项及独审通过 | 仓库外纯产品安装已通过；真实Terminal未验 | not-required |
| <a id="pkg-01"></a>PKG-01 | 标准包/源码包 | wheel/sdist构建、从sdist重建、仓库外新venv/无PYTHONPATH安装 | 名称/版本/依赖/entrypoint/license/资源完整；移走源仓库仍可启动并做自身恢复 | [工程与发布逐文件表](module-map.md#d--评估数据文档许可与发布配套其余298)；[交付研究](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 已确认安装/真实终端/发布验收 | 最终 b09-r4 标准 wheel/sdist 已交付 | [固定包绑定](../ruocun-next24h/evidence/batch-09/package-r3/README.md) · [仓外会话与 Shell 恢复](../ruocun-next24h/evidence/batch-09/n79-probe/README.md) | R4 309 成员一致，仓外同一 run 恢复通过。[R4 安装与验证](../ruocun-next24h/evidence/batch-final/package-r4/README.md) | not-required |
| <a id="pkg-02"></a>PKG-02 | Windows独立程序（本轮移出） | D2：保留历史来源与打包实验，不执行最终独立exe构建/验收 | 只交标准Python wheel/sdist；不得将原型或移出视为独立程序已通过 | [工程与发布逐文件表](module-map.md#d--评估数据文档许可与发布配套其余298)；[交付研究](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 已确认安装/真实终端/发布验收 | 范围移出（D2，非完成） | 未运行；非通过 | 范围移出 | not-required |
| <a id="pkg-03"></a>PKG-03 | 标准包runner生命周期 | 已安装Python包启动内部runner，owner退出、手工更新及接管取消 | 后台/恢复/取消不依赖开发仓库，调用同版本内部角色；独立exe/onefile生命周期按D2移出 | [工程与发布逐文件表](module-map.md#d--评估数据文档许可与发布配套其余298)；[交付研究](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 已确认安装/真实终端/发布验收 | 未开始 | 无 | 未验 | not-required |
| <a id="pkg-04"></a>PKG-04 | 标准包安装/手工更新/卸载 | 中文空格路径/PATH、干净安装、停进程一致备份、手工安装更新/恢复与卸载 | D3不承诺自动跨版本原地迁移或失败自动回退；保护原数据，未知/损坏格式拒绝；不改DAO原数据，缺依赖可诊断 | [工程与发布逐文件表](module-map.md#d--评估数据文档许可与发布配套其余298)；[交付研究](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 已确认安装/真实终端/发布验收 | 手动更新、备份、恢复和卸载已验证 | [81 仓外证据](../ruocun-next24h/evidence/batch-09/n81-upgrade/README.md) · [安装恢复说明](../../docs/install-and-recovery.md) | 中文空格路径下使用模块入口，同一会话可恢复，异常配置与数据库拒绝并保留原字节 | pending |
| <a id="pkg-05"></a>PKG-05 | 资源与许可 | embedded帧/语言/提示/core skills/parser资源、第三方清单 | 全部随包可读、hash/provenance与许可齐全；缺外部PNG生成源如实登记，不把注释当授权 | [工程与发布逐文件表](module-map.md#d--评估数据文档许可与发布配套其余298)；[交付研究](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 已确认安装/真实终端/发布验收 | 本批随包资源与第三方清单已交付 | [资源验包](../ruocun-next24h/evidence/batch-09/n79-probe/README.md) · [许可与帧来源](../../docs/release/batch-09.md#第三方组件与终端资源) | 17 个代表成员与 44 个运行 wheel 许可文件通过核验，E-02 原图与独立授权仍缺材料 | not-required |
| <a id="pkg-06"></a>PKG-06 | CI和发布配套 | Windows原生检查/安装冒烟、Linux/macOS设计检查，版本/hash/release notes | 测试、文档、恢复/兼容差异/支持矩阵/构建指令配套；交叉编译不作实机验收；不在本轮公开发布 | [工程与发布逐文件表](module-map.md#d--评估数据文档许可与发布配套其余298)；[交付研究](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 已确认安装/真实终端/发布验收 | 本地门禁、构建及发布配套已交付 | [82 门禁](../ruocun-next24h/evidence/batch-09/n82-ci/README.md) · [83 发布记录](../../docs/release/batch-09.md) | Windows 实测，Ubuntu WSL 源码适配实跑，macOS 与托管工作流待验 | not-required |
| <a id="pkg-07"></a>PKG-07 | 本轮范围完成门禁 | 逐项核对保留矩阵行、MM处置、决策依赖与用户体验；范围移出单列 | 79票有效范围的Windows支持证据和完整TUI体验证据齐全。20/37/50/75/80逐项记录范围移出，V1/V2依原决定，其他平台实机pending | [工程与发布逐文件表](module-map.md#d--评估数据文档许可与发布配套其余298)；[交付研究](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 已确认安装/真实终端/发布验收 | b09-r4 范围交付完成 | [85 的范围核验](issues/85-delivery.md) · [最终实机回执](../ruocun-next24h/batch-final.md#最终验收与交付) | b09-r4 本轮交付通过。805 来源成员、374 验证资产、215 案例族、79 张有效票已复核，范围排除与其它平台单列 | accepted |

### CFG

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="ent-02"></a>ENT-02 | 首次引导 | 无账户/合成凭据下选择语言/provider/模型并重启 | 引导可完成/取消；仅保存已确认数据，重启不重复已完成步骤 | [MM-453](module-map.md#mm-453) | 既有 CLI/协议/模块行为 | 69已实现 | [独审](../ruocun-next24h/evidence/review/b02-onboarding-review.md) | 普通入口、重启及安全边界通过 | not-required |
| <a id="ent-04"></a>ENT-04 | CLI 参数与操作员命令 | 逐个核对保留的flag、trust/Schedule/Skill、缺值及未知token。来源plugin入口移出 | 大小写/未知参数 oracle 单列；帮助不充当实现证据；不得误吞 prompt | [MM-483](module-map.md#mm-483) | 既有 CLI/协议/模块行为 | 70普通入口通过 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | 冻结11例参数oracle与正常入口比对。原生终止符和凭据保护单列差异 | not-required |
| <a id="cfg-01"></a>CFG-01 | 账户格式 | 新旧 profile JSON、坏 JSON、空/缺字段及未知顶层字段 | v2 格式和宽容边界沿用源；新增/删除/切换及保存不丢其它顶层数据 | [MM-466](module-map.md#mm-466) | 既有 CLI/协议/模块行为 | 04本票路径已实现 | [04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；208 passed，五项入口全0 | 04自动通过；其它未验 | not-required |
| <a id="cfg-02"></a>CFG-02 | 模型目录 | 6 provider 默认值、同名模型不同端点、自定义模型 | 保持冻结 ID/endpoint/window/vision/output cap；自定义网关不猜便宜档 | [MM-464](module-map.md#mm-464) | 既有 CLI/协议/模块行为 | 04本票路径已实现 | [04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；208 passed，五项入口全0 | 04自动通过；其它未验 | not-required |
| <a id="cfg-03"></a>CFG-03 | 模型继承 | 主模型、agent 定义、调用 override/inherit 组合 | override > agent > parent；缺 parent 明确报错，不暗换 provider | [MM-462](module-map.md#mm-462) | 既有 CLI/协议/模块行为 | 04与39路径已实现 | [04验证](evidence/04-chat/README.md)、[39自定义模型](../ruocun-next24h/evidence/n39-agent-defs/README.md) | 04与39自动通过 | not-required |
| <a id="cfg-04"></a>CFG-04 | 凭据优先级 | inline key 与 keyRef 同时/单独/取回失败 | inline 优先；缺 key 不靠通用环境变量自动挑账户；fallback 准确显示且不泄漏 | [MM-455](module-map.md#mm-455) | 既有 CLI/协议/模块行为 | 04原路径保持；58补系统keyRef与fallback | [04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；208 passed，五项入口全0 | 04、58 普通入口和 R4 重启后系统凭据读回均已验证 | not-required |
| <a id="cfg-05"></a>CFG-05 | dotenv | cwd 文件、进程已有空值、引号/注释/非法行 | 只用参考简化方言；已有环境含空值优先，不增加 export/插值语义 | [MM-457](module-map.md#mm-457) | 既有 CLI/协议/模块行为 | 04本票路径已实现 | [04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；208 passed，五项入口全0 | 04自动通过；其它未验 | not-required |
| <a id="cfg-06"></a>CFG-06 | 环境开关 | 缺省、空、0、1、负数/非法数字及 bool 字符串 | 逐变量复刻取值判据；AUTO_APPROVE=0 与 TRUST=0 不混同 | [MM-483](module-map.md#mm-483) | 既有 CLI/协议/模块行为 | 04本票路径已实现 | [04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；208 passed，五项入口全0 | 04自动通过；其它未验 | not-required |
| <a id="cfg-07"></a>CFG-07 | 设置分层 | user/project/local/CLI/enterprise 冲突与不可信项目 | 只对参考实际 gated 通道施加现有信任；defaultMode 后覆盖、规则并集；deny > ask > allow | [MM-560](module-map.md#mm-560) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="cfg-08"></a>CFG-08 | 项目指令 | 用户级、Git root..cwd、.git 文件、无Git、去重 | DAO顺序/trim去重；D09原生RUOCUN.md/local及显式兼容，AGENTS不自动进入产品 | [MM-564](module-map.md#mm-564) | 既有 CLI/协议/模块行为 | 已实现 | [A-INSTRUCTIONS](../ruocun-advanced-a/evidence/integration/README.md)定向与模块独审通过；阶段A自动出口通过 | 合成CLI已验；真实Terminal未验 | not-required |
| <a id="cfg-09"></a>CFG-09 | 品牌/数据边界 | RuoCun 与 DAO 并存、相同账户名/目录、旧目录存在 | RuoCun 自身会话隔离；不自动移动/接管旧 DAO 会话；配置别名写回策略依决策票 | [MM-460](module-map.md#mm-460) | 既有 CLI/协议/模块行为 | 04本票路径已实现 | [04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；208 passed，五项入口全0 | 04自动通过；其它未验 | not-required |
| <a id="cfg-10"></a>CFG-10 | 信任与校验/更新 | trust root、有效/无效 key、更新离线/关闭 | 信任范围真实可见，认证错误可修正；更新失败不阻断业务，版本/URL 策略待发布决定 | [MM-468](module-map.md#mm-468) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |

### RUN

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="ent-03"></a>ENT-03 | TTY/REPL/一次性入口 | 分别终端启动、管道输入、argv prompt 与 EOF | 按来源入口能力运行；headless 首工具批包含 TodoWrite；keepAlive 等真实后台完成 | [MM-483](module-map.md#mm-483) | 既有 CLI/协议/模块行为 | 70普通入口及56 Deck通过 | [批次08](../ruocun-next24h/batch-08.md#交付记录) | CLI、REPL、TTY与回环Deck共享实际调度；一次性入口按来源只读 | not-required |
| <a id="run-01"></a>RUN-01 | 安全边界与队列 | 流式/工具批运行中追加多条输入和后台消息 | 边界合并、保序不丢失；不得插断 assistant/tool 对；提交 hook 拦截不入历史 | [MM-422](module-map.md#mm-422) | 既有 scheduler/真实进程验收 | 未开始 | 无 | 未验 | not-required |
| <a id="run-02"></a>RUN-02 | 状态机区分 | 分别达 idle/running/waiting/paused/closed/recovering | 单轮 completed/waiting/interrupted/failed 与执行状态独立；paused 可继续，closed 不再 pump | [MM-385](module-map.md#mm-385) | 既有 scheduler/真实进程验收 | 未开始 | 无 | 未验 | not-required |
| <a id="run-03"></a>RUN-03 | TaskWait | any/all、1/32/33、重复 id、前台/manual/未知/重跑 task | 固定 task+run，去重与上限；错误/取消/attention唤醒；存失败 rollback consumed | [MM-383](module-map.md#mm-383) | 既有 scheduler/真实进程验收 | 未开始 | 无 | 未验 | not-required |
| <a id="run-04"></a>RUN-04 | 输入暂停与后台解绑 | Esc pause、Ctrl+B 转后台、随后前台 abort | pause 清队列/释放等待/停当前轮但不 cancelAll；已转后台不被旧前台 signal 杀死 | [MM-422](module-map.md#mm-422) | 既有 scheduler/真实进程验收 | 未开始 | 无 | 未验 | not-required |
| <a id="run-05"></a>RUN-05 | 工具批并发/屏障 | read/network/plan 多调用夹 write/exec；取消/存储失败 | 最多8并行，write/exec 串行屏障、原序收结果；allSettled收齐后传播失败；plan标签不当纯函数 | [MM-642](module-map.md#mm-642) | 既有 scheduler/真实进程验收 | 12前台read/plan和write/exec路径已实现 | [来源及普通入口](../ruocun-next20h/evidence/n2-shared/README.md)与独审通过；network/Hook后置 | 合成CLI/受控TTY已验 | not-required |
| <a id="run-06"></a>RUN-06 | 审批与 prehook 一次性 | hook updatedInput 后命中不同规则、批量 ask、失败重试 | hook只执行一次，最终参数用于 gate/审计/handler；deny也返回对应结果；hook自身副作用journal | [MM-642](module-map.md#mm-642) | 既有 scheduler/真实进程验收 | 未开始 | 无 | 未验 | not-required |
| <a id="run-07"></a>RUN-07 | 子代理与 fork | 同步/后台/自定义模型/工具白名单、当前fork/exactTools、普通代理恢复与特殊现场不足 | 保留来源工具裁剪及权限/目录；R3允许重启特殊fork材料不足时明确拒绝继续，查看转录后新建任务，不降为普通agent | [MM-420](module-map.md#mm-420) | 既有 scheduler/真实进程验收 | 38/39/40/41及43本票路径已实现；本批补子专属MCP接缝 | [后台生命周期](../ruocun-next24h/evidence/n40-agent-background/README.md)、[fork独审](../ruocun-next24h/evidence/review/b02-fork-isolation-review.md) · [代理消息独审](../ruocun-next24h/evidence/review/b04-agent-messages-review.md) · [子MCP独审](../ruocun-next24h/evidence/review/b05-agent-mcp-review.md) | 普通入口和冻结来源定向独审通过；母案例其余组合按逐票 | not-required |
| <a id="run-08"></a>RUN-08 | worktree 隔离 | 普通/嵌套 EnterWorktree、worktree/remote 选项、失败清理 | Git边界/路径/权限正确；remote 原为worktree不能宣称真远程；未提交用户改动不被清理 | [MM-432](module-map.md#mm-432) | 既有 scheduler/真实进程验收 | 27/41已实现 | [工作树证据](../ruocun-next24h/evidence/n41-worktree/README.md)、[ADR-0017](../../docs/adr/0017-agent-isolation-failure.md) | 自动通过，已知失败拒绝派发 | not-required |
| <a id="run-09"></a>RUN-09 | 异构任务恢复 | Shell、普通/fork agent、Monitor、manual、loop | Shell重连；材料完整的代理显式checkpoint继续，R3特殊fork现场不足明确拒绝；Monitor不冒充代理；manual不启动执行；loop不是OS定时 | [MM-424](module-map.md#mm-424) | 既有 scheduler/真实进程验收 | Shell、代理、Monitor、manual、loop 离线契约及独审通过 | [76 离线与 R3 定向](../ruocun-next24h/evidence/batch-09/eval/n76/README.md) · [79 仓外](../ruocun-next24h/evidence/batch-09/n79-probe/README.md) | Shell 接管同一 run，代理显式继续，Monitor 失主终止且无重放；manual 与 loop 保持各自边界 | not-required |
| <a id="run-10"></a>RUN-10 | 取消终态 | TaskStop/KillShell 在 coop、忽略信号、进程树下执行 | 先canceling，真实close/受管后代止写后canceled；未知保持unknown；不回滚已发生副作用 | [MM-704](module-map.md#mm-704) | 既有 scheduler/真实进程验收 | 15本票Windows路径已实现，相关母案例其余路径按后票 | [runner与恢复独审](../ruocun-next24h/evidence/review/managed-shell-review.md)、[固定r2纯安装](../ruocun-next24h/evidence/review/pure-r2-review.md) | 真实owner强杀/同run接管/Job止写及ACL路径已核，跨账户与非Windows未验 | not-required |
| <a id="run-11"></a>RUN-11 | 事件投递与通知 | 重复event、宕机在save/ack之间、附件大结果 | 先run+event落盘；消息+delivered同事务后ack；进展与用户指令分离，无重复投递 | [MM-381](module-map.md#mm-381) | 既有 scheduler/真实进程验收 | 未开始 | 无 | 未验 | not-required |
| <a id="run-12"></a>RUN-12 | 前台/退出/keepAlive | 一次性与管道有后台任务、关闭面板/显式keep-background | scheduler基于事件等待而非不断模型poll；仅明确保留的runner跨owner存在；后续可接管/取消 | [MM-422](module-map.md#mm-422) | 既有 scheduler/真实进程验收 | 未开始 | 无 | 未验 | not-required |

### EXT

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="ent-05"></a>ENT-05 | 禁用与 eval | 组合 eval/no-memory/no-skills/no-mcp/no-hooks/no-project-instructions/no-web | 按真实源子集分别断言；动态技能泄漏风险单列缺陷，不声称零副作用 | [MM-483](module-map.md#mm-483) | 既有 CLI/协议/模块行为 | 71普通入口与恢复通过 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | 真实Read、SQLite旧队列和回环MCP对照。保留旧记录，关闭通道不再加载 | not-required |
| <a id="ext-01"></a>EXT-01 | Skills 解析与发现 | 简单frontmatter、paths/别名、slug/SKILL布局、realpath及同名 | 元信息/正文分离、model/user invocable、命名空间及用户→项目覆盖按oracle；不擅自扩大YAML方言 | [MM-616](module-map.md#mm-616) | 既有文件格式/外部协议 fixture | 静态子路径已实现 | [A-SKILLS](../ruocun-advanced-a/evidence/integration/README.md)模块/定向通过；非整族通过 | 合成CLI已验；动态/插件未验 | not-required |
| <a id="ext-02"></a>EXT-02 | Skills 动态激活/禁用 | 启动路径扫描、文件访问嵌套技能、disabled/usage排序 | 保留缓存/边界注入与顺序；no-skills/eval动态泄漏按缺陷登记不当正确预期 | [MM-610](module-map.md#mm-610) | 既有文件格式/外部协议 fixture | 35子路径已实现，实际目录顺序沿来源，usage评分不虚作目录重排 | [模块和入口](../ruocun-next20h/evidence/n3-shared/README.md)通过；eval后置 | Windows合成普通入口已验，真实Terminal未验 | not-required |
| <a id="ext-03"></a>EXT-03 | 技能安装/适配 | 本地/Git、无效正文、资源目录、同名、callFlash成功/失败/cache | 完整目录安装、原文不修改、适配缓存/失败fallback可观察；真实生成不作逐字golden | [MM-608](module-map.md#mm-608) | 既有文件格式/外部协议 fixture | 36已实现，确认后刷新、原生适配缓存/回退 | [模块和实际入口](../ruocun-next20h/evidence/n3-install-shared/README.md)及独审通过 | 本地资源、合成Git argv/模型；真实远端与Terminal未验 | not-required |
| <a id="ext-04"></a>EXT-04 | 插件与自定义命令 | 两种manifest、hooks根、插件→用户→项目、参数/同名slash | 发现/覆盖及字符串替换等价；安装/删除约束插件根，路径逃逸作为原版缺陷修复记录 | [MM-562](module-map.md#mm-562) | 既有文件格式/外部协议 fixture | 范围移出（37/50） | 未运行 | 范围移出 | not-required |
| <a id="ext-05"></a>EXT-05 | agent 文本格式 | frontmatter全部支持字段、排除工具、memory/model/isolation/hooks/MCP引用 | 按实际简化parser接纳边界；内联MCP类型不当完整支持；bundled覆盖与生命周期一致 | [MM-366](module-map.md#mm-366) | 既有文件格式/外部协议 fixture | 39已实现 | [来源与真实派发](../ruocun-next24h/evidence/n39-agent-defs/README.md) | 39自动通过，Hook/MCP生命周期按后续任务 | not-required |
| <a id="ext-06"></a>EXT-06 | Hook 选择与命令协议 | user→trustedproject、5事件、matcher/if、timeout/async。plugin层保留为来源记录 | 顺序附加；仅command实际执行；stdin字段/args字符串、exit2、block/context/input/permission按事件消费 | [MM-477](module-map.md#mm-477) | 既有文件格式/外部协议 fixture | 48已实现本票路径 | [工具Hook独审](../ruocun-next24h/evidence/review/b04-hook-tool-review.md) | 命令选择、改参后人工权限及未知结果独审通过；完整 JS RegExp 未验 | not-required |
| <a id="ext-07"></a>EXT-07 | Hook 生命周期 | startup/resume哨兵、防重复、正常退出与异常退出、子代理start/stop | 只保证实际有调用点的事件；PostToolUse不回滚副作用；子代理hook独立注册表 | [MM-370](module-map.md#mm-370) | 既有文件格式/外部协议 fixture | 49已实现本票路径 | [普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) · [子代理生命周期](../ruocun-next24h/evidence/n49-agent-lifecycle/README.md) | 正常/恢复及取消的子案例自动通过；未知结果停止，完整异常族未验 | not-required |
| <a id="ext-08"></a>EXT-08 | MCP 配置/传输 | user→project server覆盖、坏JSON、stdio/.cmd、HTTP/SSE、禁用 | 协议实际接线保持、单server失败隔离；命令cwd/env/超时按声明；生命周期可取消 | [MM-496](module-map.md#mm-496) | 既有文件格式/外部协议 fixture | 51/52本票路径已实现 | [stdio](../ruocun-next24h/evidence/review/b05-mcp-cli-review.md) · [HTTP/SSE](../ruocun-next24h/evidence/review/b05-http-review.md) · [能力/命令](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) | stdio/HTTP/SSE及来源定向独审通过；单服务失败隔离；不是全协议认证 | not-required |
| <a id="ext-09"></a>EXT-09 | MCP 能力/可见性 | tools/resources/prompts、非text、空结果、listChanged/elicitation | 前5自动可见其余搜索，schema原样；结果格式按oracle；UI未绑定elicitation拒绝；不凭SDK推断未接线能力 | [MM-496](module-map.md#mm-496) | 既有文件格式/外部协议 fixture | 53本票路径已实现 | [stdio](../ruocun-next24h/evidence/review/b05-mcp-cli-review.md) · [HTTP/SSE](../ruocun-next24h/evidence/review/b05-http-review.md) · [能力/命令](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) | 前5/搜索、schema、资源/提示、变更和无UI拒绝等来源子案例通过；全部交互体验另验 | not-required |
| <a id="ext-10"></a>EXT-10 | MCP 断线/副作用 | 请求服务端已执行后断线、重连与重复请求 | 已确认ADR-0003：可能已执行但结果不明不得自动重放，持久保留未决；连接/发现可重连，重启不重复副作用 | [MM-496](module-map.md#mm-496) | 既有文件格式/外部协议 fixture | 54本票路径已实现 | [断线独审](../ruocun-next24h/evidence/review/b05-mcp-recovery-review.md) · [子MCP独审](../ruocun-next24h/evidence/review/b05-agent-mcp-review.md) | stdio/HTTP/SSE真实effect保持1、退出74、重开换ID阻挡；SDK日志脱敏；不承诺远端exactly-once | not-required |
| <a id="ext-11"></a>EXT-11 | LSP 协议 | 9操作、UTF8字节frame、UTF16位置、Unicode URI/盘符/UNC | 1-based外部位置映射正确，Location/Link可读；惰性启动didOpen/didChange/版本，故障可退出 | [MM-485](module-map.md#mm-485) | 既有文件格式/外部协议 fixture | 55本票子路径已实现 | [独审](../ruocun-next24h/evidence/review/b06-lsp-review.md) | 来源语义及普通入口技术通过；覆盖范围/限制见独审，完整终端及其它平台另验 | not-required |
| <a id="ext-12"></a>EXT-12 | Agent Deck | 协议1、token/Origin、snapshot/messages/command、commandid重复冲突 | 仅loopback认证、幂等和409；面板关闭不等于Agent退出；身份/会话/事件不串 | [MM-396](module-map.md#mm-396) | 既有文件格式/外部协议 fixture | 56已实现并独审 | [批次08](../ruocun-next24h/batch-08.md#交付记录) | 回环/token/Origin、幂等、回执与子审批隔离、重连和退出 | not-required |
| <a id="skill-simplify"></a>SKILL-simplify | core skill simplify | 开启/禁用、同名磁盘覆盖、手动和模型调用 | 冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数 | [MM-606](module-map.md#mm-606)、[MM-616](module-map.md#mm-616) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="skill-debug"></a>SKILL-debug | core skill debug | 开启/禁用、同名磁盘覆盖、手动和模型调用 | 冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数 | [MM-606](module-map.md#mm-606)、[MM-616](module-map.md#mm-616) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="skill-make-plan"></a>SKILL-make-plan | core skill make-plan | 开启/禁用、同名磁盘覆盖、手动和模型调用 | 冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数 | [MM-606](module-map.md#mm-606)、[MM-616](module-map.md#mm-616) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="skill-verify"></a>SKILL-verify | core skill verify | 开启/禁用、同名磁盘覆盖、手动和模型调用 | 冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数 | [MM-606](module-map.md#mm-606)、[MM-616](module-map.md#mm-616) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="skill-code-review"></a>SKILL-code-review | core skill code-review | 开启/禁用、同名磁盘覆盖、手动和模型调用 | 冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数 | [MM-606](module-map.md#mm-606)、[MM-616](module-map.md#mm-616) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="skill-deep-research"></a>SKILL-deep-research | core skill deep-research | 开启/禁用、同名磁盘覆盖、手动和模型调用 | 冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数 | [MM-606](module-map.md#mm-606)、[MM-616](module-map.md#mm-616) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="skill-fewer-permission-prompts"></a>SKILL-fewer-permission-prompts | core skill fewer-permission-prompts | 开启/禁用、同名磁盘覆盖、手动和模型调用 | 冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数 | [MM-606](module-map.md#mm-606)、[MM-616](module-map.md#mm-616) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="skill-run-skill-generator"></a>SKILL-run-skill-generator | core skill run-skill-generator | 开启/禁用、同名磁盘覆盖、手动和模型调用 | 冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数 | [MM-606](module-map.md#mm-606)、[MM-616](module-map.md#mm-616) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |

### REC

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="ent-06"></a>ENT-06 | 退出与资源收尾 | 正常退出、EOF、异常路径及 keep-background | 保存状态，关闭该关闭的进程/扩展/终端；保留后台时可恢复且无无主执行 | [MM-568](module-map.md#mm-568) | 既有 CLI/协议/模块行为 | 70普通入口及56 Deck收尾通过 | [批次08](../ruocun-next24h/batch-08.md#交付记录) | 既有后台保留行为继续生效。Deck 客户端关闭不影响 Agent，Agent 正常退出移除记录并关监听 | not-required |
| <a id="rec-01"></a>REC-01 | 权威恢复数据 | SQLite、JSON导出、旁路日志不一致/导出失败 | SQLite权威；JSON/events.jsonl不被当等价真相；正常重启聊天与状态连续 | [MM-593](module-map.md#mm-593) | 既有恢复脚本/真实进程/SQLite契约 | 07本票保存/恢复路径已实现；其它子项按后票 | [07来源映射](evidence/07-store/sprint-session/README.md)、[独立复核](integration-evidence/sprint07/README.md) | 07自动/实际wheel路径通过；最终产物/其它未验范围保留 | not-required |
| <a id="rec-02"></a>REC-02 | schema/损坏 | 版本0/2/未来、缺可信checkpoint、损坏数据库 | 既有v2语义作为内部baseline；新字段/版本须明确迁移；未来/损坏拒绝，不静默空会话 | [MM-601](module-map.md#mm-601) | 既有恢复脚本/真实进程/SQLite契约 | 07本票保存/恢复路径已实现；其它子项按后票 | [07来源映射](evidence/07-store/sprint-session/README.md)、[独立复核](integration-evidence/sprint07/README.md) | 07自动/实际wheel路径通过；最终产物/其它未验范围保留 | not-required |
| <a id="rec-03"></a>REC-03 | 事务与配置 | 读回WAL/FULL/busy3000、BEGIN IMMEDIATE失败、磁盘满/并发写 | 消息/background/revision/delivered原子；run/event原子；失败保留原错，不伪造成功 | [MM-593](module-map.md#mm-593) | 既有恢复脚本/真实进程/SQLite契约 | 07本票保存/恢复路径已实现；其它子项按后票 | [07来源映射](evidence/07-store/sprint-session/README.md)、[独立复核](integration-evidence/sprint07/README.md) | 07自动/实际wheel路径通过；最终产物/其它未验范围保留 | not-required |
| <a id="rec-04"></a>REC-04 | 会话筛选/切换 | 同cwd最近unfinished、显式ID、无user、done/paused/waiting/unknown | 列表排序/continue精确；存在活owner/运行代理时拒危险切换；done判据不漏后台未决 | [MM-595](module-map.md#mm-595) | 既有恢复脚本/真实进程/SQLite契约 | 26本票路径已实现 | [会话独审](../ruocun-next24h/evidence/review/b05-sessions-review.md) · [暂停补验](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) | 普通入口与SQLite独审通过；latest仅未完成、完成会话显式ID；只读重开保留paused | not-required |
| <a id="rec-05"></a>REC-05 | 工具journal故障切点 | 意图前/后、effect后、结果提交前/后强杀再重启三次 | 已知结果复用；无意图可证未执行；started→outcome_unknown；禁止盲重放含prehook | [MM-602](module-map.md#mm-602) | 既有恢复脚本/真实进程/SQLite契约 | 未开始 | 无 | 未验 | not-required |
| <a id="rec-06"></a>REC-06 | checkpoint/事件故障切点 | save确认前/后、run/eventcommit前、delivery提交/ack之间kill | 消息/事件一致、不重投不丢已确认checkpoint；保存失败rollback wait consumed | [MM-593](module-map.md#mm-593) | 既有恢复脚本/真实进程/SQLite契约 | 未开始 | 无 | 未验 | not-required |
| <a id="rec-07"></a>REC-07 | 本轮会话保存恢复状态 | 消息/model/mode/title、四累计token、任务等待/普通代理恢复，重启费用统计边界 | R1：历史分模型费用不承诺完整，重启新费用另计并标明统计范围/预算口径；R3特殊现场不足明确拒绝；缓存本地元数据重建不误报 | [MM-600](module-map.md#mm-600) | 既有恢复脚本/真实进程/SQLite契约 | 28范围通过 | 真实普通重开保留累计token，新进程费用与预算独立通过 | Windows合成入口 | not-required |
| <a id="rec-08"></a>REC-08 | 恢复决定 | 未知工具/任务resolve/decide/continue、失败/重复提交 | 决定与消息持久化、同ID不能重复执行；用户显式承担未知处理，无自动猜测 | [MM-598](module-map.md#mm-598) | 既有恢复脚本/真实进程/SQLite契约 | 17决定及普通继续已接入 | [恢复证据](../ruocun-next24h/evidence/n17-recovery/README.md) | 普通CLI与SQLite验证通过 | not-required |
| <a id="rec-09"></a>REC-09 | owner 与进程身份 | 活owner、死owner、epoch接管、PID同号错误start、host/boot变化 | canonicalcwd+host/boot/pid/start；旧writer fencing；查询失败不冒充死亡；跨host不自动接管 | [MM-597](module-map.md#mm-597) | 既有恢复脚本/真实进程/SQLite契约 | 07本票保存/恢复路径已实现；其它子项按后票 | [07来源映射](evidence/07-store/sprint-session/README.md)、[独立复核](integration-evidence/sprint07/README.md) | 07自动/实际wheel路径通过；最终产物/其它未验范围保留 | not-required |
| <a id="rec-10"></a>REC-10 | runner握手与启动认领 | grant前/后kill、重复start、错token/run/epoch、断开重连 | start.claim排他，可能grant后保守unknown；接管不重启副作用；终态receipt身份校验 | [MM-668](module-map.md#mm-668) | 既有恢复脚本/真实进程/SQLite契约 | 15本票Windows路径已实现，相关母案例其余路径按后票 | [runner与恢复独审](../ruocun-next24h/evidence/review/managed-shell-review.md)、[固定r2纯安装](../ruocun-next24h/evidence/review/pure-r2-review.md) | 真实owner强杀/同run接管/Job止写及ACL路径已核，跨账户与非Windows未验 | not-required |
| <a id="rec-11"></a>REC-11 | 大结果附件 | 超过24000字符、附件删除/篡改、stdout/stderr缺失 | 先文件持久再登记hash；显示溢写路径；恢复异常形成未决，不伪装完整 | [MM-383](module-map.md#mm-383) | 既有恢复脚本/真实进程/SQLite契约 | 未开始 | 无 | 未验 | not-required |
| <a id="rec-12"></a>REC-12 | 原子文件与权限 | Windows文件占用/replace、临时文件异常、IPC ACL、磁盘错误 | 持久确认边界真实；私密文件/能力受限；失败不吞；无实证不承诺断电不丢 | [MM-591](module-map.md#mm-591) | 既有恢复脚本/真实进程/SQLite契约 | 07本票保存/恢复路径已实现；其它子项按后票 | [07来源映射](evidence/07-store/sprint-session/README.md)、[独立复核](integration-evidence/sprint07/README.md) | 07自动/实际wheel路径通过；最终产物/其它未验范围保留 | not-required |
| <a id="rec-13"></a>REC-13 | 工作区检查点 | 创建/restore/rewind、未提交文件、忽略/大二进制、Git不可用 | 聊天/代理/影子Git三类检查点分开；回退前保存；范围可解释、不误删用户外部数据 | [MM-588](module-map.md#mm-588) | 既有恢复脚本/真实进程/SQLite契约 | 未开始 | 无 | 未验 | not-required |
| <a id="rec-14"></a>REC-14 | 分支/导出/清理 | branch后父后台继续、Markdown导出、活动会话mtime很老 | 分支聊天不复制运行副作用；清理不得删除活动/可恢复数据；修复源mtime风险单列差异 | [MM-392](module-map.md#mm-392) | 既有恢复脚本/真实进程/SQLite契约 | 26本票路径已实现 | [会话独审](../ruocun-next24h/evidence/review/b05-sessions-review.md) · [暂停补验](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) | 分支/导出和受控封存独审通过；附件拥有者保守保留，异常保留现场 | not-required |
| <a id="rec-15"></a>REC-15 | SQLite运行库修复门禁 | 实际保留的开发/测试/wheel环境读取version/sourceid/compileoptions；独立产物按D2移出 | 有官方WAL修复或可审计backport；探针3.45.1不合产品门禁，普通压力通过不证明已修复 | [MM-601](module-map.md#mm-601) | 既有恢复脚本/真实进程/SQLite契约 | 07本票保存/恢复路径已实现；其它子项按后票 | [07来源映射](evidence/07-store/sprint-session/README.md)、[独立复核](integration-evidence/sprint07/README.md) | 07自动/实际wheel路径通过；最终产物/其它未验范围保留 | not-required |
| <a id="rec-16"></a>REC-16 | 一致备份/手工更新恢复 | 手工停进程后取得一致快照或SQLite backup，再安装更新/重装/还原 | D3移出自动跨版本原地迁移/失败回退；保护原数据且拒绝未知/损坏版本；单拷活db不当备份成功 | [MM-593](module-map.md#mm-593) | 既有恢复脚本/真实进程/SQLite契约 | 停进程后的备份、换包与手动恢复已验证 | [81 仓外升级](../ruocun-next24h/evidence/batch-09/n81-upgrade/README.md) | 原会话恢复并继续提交，异常数据副本未写回，卸载保留用户数据 | not-required |

### CMD

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="cmd-model"></a>CMD-model | /model | 在基础9+TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 模型查询/切换、provider/账户约束及持久化；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | pending |
| <a id="cmd-plan"></a>CMD-plan | /plan | 在基础9+TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 进入/退出只读规划；实际可用工具裁剪；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="cmd-clear"></a>CMD-clear | /clear | 在基础9+TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 清空当前上下文，保留明确的会话生命周期处理；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 26本票路径已实现 | [会话独审](../ruocun-next24h/evidence/review/b05-sessions-review.md) · [暂停补验](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) | 普通命令入口、状态与生命周期独审通过；完整终端体验归77/78 | not-required |
| <a id="cmd-compact"></a>CMD-compact | /compact | 在基础9+TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 主动压缩、工具消息配对及可恢复检查点；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 29范围通过 | 失败保留原上下文，等待和重开独立通过 | Windows合成入口 | not-required |
| <a id="cmd-cost"></a>CMD-cost | /cost | 在基础9+TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 用量/缓存与本进程费用查询；R1重启后标明历史费用不完整、新费用另计；查询不无故暂停，操作按pause→settled，幂等性沿来源 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 阶段A子路径已实现；其余原规格后置 | [阶段A局部来源/接线](../ruocun-advanced-a/evidence/integration/README.md)通过；阶段A自动出口通过，非整族通过 | Windows合成CLI已验；真实模型/Terminal未验 | not-required |
| <a id="cmd-lang"></a>CMD-lang | /lang | 在基础9+TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 中英文查询/切换与存储；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="cmd-help"></a>CMD-help | /help | 在基础9+TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 对应入口实际可用命令及帮助；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 70已实现 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | 普通入口查询和实际目录验证通过 | not-required |
| <a id="cmd-exit"></a>CMD-exit | /exit | 在基础9+TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 正常收尾、保存、释放终端与执行资源；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 70已接入 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | 普通退出与既有终端/后台收尾回执复用 | not-required |
| <a id="cmd-quit"></a>CMD-quit | /quit | 在基础9+TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 退出别名；显式 keep-background 时仅保留受支持后台执行；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 70已接入 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | 普通别名与keep-background开关已核，复用受管Shell证据 | not-required |
| <a id="cmd-skills"></a>CMD-skills | /skills | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 列表/选择器、单项禁用及 bundled 批量控制；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 文字列表已实现；选择/禁用写入及TUI未完成 | [阶段A局部来源/接线](../ruocun-advanced-a/evidence/integration/README.md)通过；阶段A自动出口通过，非整族通过 | Windows合成CLI已验；真实模型/Terminal未验 | pending |
| <a id="cmd-context"></a>CMD-context | /context | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 上下文组成/预算显示；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 29范围通过 | 普通上下文组成与窗口查询通过 | Windows合成入口 | not-required |
| <a id="cmd-context-window"></a>CMD-context-window | /context-window | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 查询、K/M 解析/设置、手动锁定窗口；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 阶段A子路径已实现；其余原规格后置 | [阶段A局部来源/接线](../ruocun-advanced-a/evidence/integration/README.md)通过；阶段A自动出口通过，非整族通过 | Windows合成CLI已验；真实模型/Terminal未验 | not-required |
| <a id="cmd-tasks"></a>CMD-tasks | /tasks | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | TaskManager 当前运行项；不假装包含全部 Shell；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 45已实现 | 普通入口接线和SQLite任务管理独立通过 | Windows合成入口 | not-required |
| <a id="cmd-mcp"></a>CMD-mcp | /mcp | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 列表、重连、开关与 add；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 53本票路径已实现 | [stdio](../ruocun-next24h/evidence/review/b05-mcp-cli-review.md) · [HTTP/SSE](../ruocun-next24h/evidence/review/b05-http-review.md) · [能力/命令](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) | 普通命令入口实际列表/禁用/重连/重开独审通过；完整终端体验归77/78 | not-required |
| <a id="cmd-diff"></a>CMD-diff | /diff | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 工作区 Git 未提交差异；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="cmd-doctor"></a>CMD-doctor | /doctor | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 账户/依赖/环境自检与平台诊断；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 70已实现 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | 普通入口真实环境、账户来源和平台能力说明通过 | not-required |
| <a id="cmd-memory"></a>CMD-memory | /memory | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 查看、审核、删除记忆；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 30路径已实现 | [30来源、实际入口和独审](../ruocun-next20h/evidence/n4-shared/README.md)通过 | Windows合成CLI/受控TTY已验；真实Terminal未验 | not-required |
| <a id="cmd-permissions"></a>CMD-permissions | /permissions | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 规则/模式显示；编辑分支遮蔽另列 SOURCE-CANDIDATE；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="cmd-session"></a>CMD-session | /session | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 当前会话身份、保存与状态；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 26本票路径已实现 | [会话独审](../ruocun-next24h/evidence/review/b05-sessions-review.md) · [暂停补验](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) | 普通命令入口、状态与生命周期独审通过；完整终端体验归77/78 | not-required |
| <a id="cmd-audit"></a>CMD-audit | /audit | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 记忆/反思/工具/权限/缓存/技能审计查询；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 57已实现 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | 普通查询与脱敏旁路独审通过 | not-required |
| <a id="cmd-resume"></a>CMD-resume | /resume | 在TTY+REPL特接执行有效/缺参/非法参数；busy/waiting 状态执行 | 列表/显式会话切换、活 owner 与运行代理保护；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 26本票路径已实现 | [会话独审](../ruocun-next24h/evidence/review/b05-sessions-review.md) · [暂停补验](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) | 普通命令入口、状态与生命周期独审通过；完整终端体验归77/78 | pending |
| <a id="cmd-branch"></a>CMD-branch | /branch | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 复制聊天分支；不重复启动原后台副作用；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 26本票路径已实现 | [会话独审](../ruocun-next24h/evidence/review/b05-sessions-review.md) · [暂停补验](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) | 普通命令入口、状态与生命周期独审通过；完整终端体验归77/78 | not-required |
| <a id="cmd-rename"></a>CMD-rename | /rename | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 会话标题保存及重启一致性；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 26本票路径已实现 | [会话独审](../ruocun-next24h/evidence/review/b05-sessions-review.md) · [暂停补验](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) | 普通命令入口、状态与生命周期独审通过；完整终端体验归77/78 | not-required |
| <a id="cmd-rewind"></a>CMD-rewind | /rewind | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 按用户消息截断；显式 code 时关联工作区检查点；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | pending |
| <a id="cmd-export"></a>CMD-export | /export | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 会话 Markdown 导出与路径显示；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 26本票路径已实现 | [会话独审](../ruocun-next24h/evidence/review/b05-sessions-review.md) · [暂停补验](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) | 普通命令入口、状态与生命周期独审通过；完整终端体验归77/78 | not-required |
| <a id="cmd-config"></a>CMD-Config | /Config | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 保留大写入口的配置显示；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 25本票子路径已实现 | [独审](../ruocun-next24h/evidence/review/b06-config-review.md) | 来源语义及普通入口技术通过；覆盖范围/限制见独审，完整终端及其它平台另验 | not-required |
| <a id="cmd-effort"></a>CMD-effort | /effort | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 思考强度查询/设置并应用后续请求；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 阶段A子路径已实现；其余原规格后置 | [阶段A局部来源/接线](../ruocun-advanced-a/evidence/integration/README.md)通过；阶段A自动出口通过，非整族通过 | Windows合成CLI已验；真实模型/Terminal未验 | not-required |
| <a id="cmd-status"></a>CMD-status | /status | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 运行状态/模式/预算显示；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 阶段A子路径已实现；其余原规格后置 | [阶段A局部来源/接线](../ruocun-advanced-a/evidence/integration/README.md)通过；阶段A自动出口通过，非整族通过 | Windows合成CLI已验；真实模型/Terminal未验 | not-required |
| <a id="cmd-plugin"></a>CMD-plugin | /plugin | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 已安装插件清单；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 范围移出（50） | 未运行 | 范围移出 | not-required |
| <a id="cmd-hooks"></a>CMD-hooks | /hooks | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 实际载入 Hook 清单；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 48已实现本票路径 | [普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) | 受信来源、禁用与清单自动通过 | not-required |
| <a id="cmd-agents"></a>CMD-agents | /agents | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 内置/自定义代理定义清单；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 70已实现 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | 普通入口代理目录及禁用边界已验 | not-required |
| <a id="cmd-files"></a>CMD-files | /files | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 已读文件与上下文信息；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="cmd-copy"></a>CMD-copy | /copy | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 复制末条回答，Unicode 和空回答处理；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 67已实现 | 普通输入owner验证空回答、Unicode和零模型请求 | 真实 Windows Terminal 复制与粘贴 Unicode 通过 | not-required |
| <a id="cmd-btw"></a>CMD-btw | /btw | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 备注注入而不立即请求模型；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 44已实现本票路径 | [普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) · [冻结提示对照](../ruocun-next24h/evidence/batch-04/n44/README.md) | 合成入口与来源定向通过；真实终端总体验单列 | not-required |
| <a id="cmd-account"></a>CMD-account | /account | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 账户列表/选择/新增/删除/切换；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | pending |
| <a id="cmd-accounts"></a>CMD-accounts | /accounts | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 账户别名入口；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="cmd-bypass"></a>CMD-bypass | /bypass | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 显式放行模式与状态一致性；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="cmd-yolo"></a>CMD-yolo | /yolo | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 放行别名与可见模式；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="cmd-mode"></a>CMD-mode | /mode | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 模式查询/切换；plan 不混入 auto/bypass 循环；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="cmd-goal"></a>CMD-goal | /goal | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 长任务开启/关闭、目标提示与边界；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 44已实现本票路径 | [普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) · [冻结提示对照](../ruocun-next24h/evidence/batch-04/n44/README.md) | 合成入口与来源定向通过；真实终端总体验单列 | not-required |
| <a id="cmd-task"></a>CMD-task | /task | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 长任务别名入口；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 44已实现本票路径 | [普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) · [冻结提示对照](../ruocun-next24h/evidence/batch-04/n44/README.md) | 合成入口与来源定向通过；真实终端总体验单列 | not-required |
| <a id="cmd-coordinator"></a>CMD-coordinator | /coordinator | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 合并后的长任务别名入口；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 44已实现本票路径 | [普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) · [冻结提示对照](../ruocun-next24h/evidence/batch-04/n44/README.md) | 合成入口与来源定向通过；真实终端总体验单列 | not-required |
| <a id="cmd-restore"></a>CMD-restore | /restore | 在TTY执行有效/缺参/非法参数；busy/waiting 状态执行 | 工作区恢复前先建自动快照；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="cmd-recovery"></a>CMD-recovery | /recovery | 在TTY+REPL特接执行有效/缺参/非法参数；busy/waiting 状态执行 | 未决查询/resolve/decide/continue，决定持久化；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-483](module-map.md#mm-483)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 17决定及普通继续已接入 | [恢复证据](../ruocun-next24h/evidence/n17-recovery/README.md) | 普通CLI与SQLite验证通过 | not-required |
| <a id="cmd-simplify"></a>CMD-simplify | /simplify | 在TTY builtin执行有效/缺参/非法参数；busy/waiting 状态执行 | 内置简化 prompt 展开；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-446](module-map.md#mm-446)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 44已实现本票路径 | [普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) · [冻结提示对照](../ruocun-next24h/evidence/batch-04/n44/README.md) | 合成入口与来源定向通过；真实终端总体验单列 | not-required |
| <a id="cmd-remember"></a>CMD-remember | /remember | 在TTY builtin执行有效/缺参/非法参数；busy/waiting 状态执行 | 内置记忆 prompt 展开；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-446](module-map.md#mm-446)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 44已实现本票路径 | [普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) · [冻结提示对照](../ruocun-next24h/evidence/batch-04/n44/README.md) | 合成入口与来源定向通过；真实终端总体验单列 | not-required |
| <a id="cmd-review"></a>CMD-review | /review | 在TTY builtin执行有效/缺参/非法参数；busy/waiting 状态执行 | 内置审查 prompt 展开；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-446](module-map.md#mm-446)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 44已实现本票路径 | [普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) · [冻结提示对照](../ruocun-next24h/evidence/batch-04/n44/README.md) | 合成入口与来源定向通过；真实终端总体验单列 | not-required |
| <a id="cmd-init"></a>CMD-init | /init | 在TTY builtin执行有效/缺参/非法参数；busy/waiting 状态执行 | 内置项目初始化 prompt 展开；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-446](module-map.md#mm-446)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 44已实现本票路径 | [普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) · [冻结提示对照](../ruocun-next24h/evidence/batch-04/n44/README.md) | 合成入口与来源定向通过；真实终端总体验单列 | not-required |
| <a id="cmd-batch"></a>CMD-batch | /batch | 在TTY builtin执行有效/缺参/非法参数；busy/waiting 状态执行 | 内置并行任务/worktree prompt 展开；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-446](module-map.md#mm-446)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 44已实现本票路径 | [普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) · [冻结提示对照](../ruocun-next24h/evidence/batch-04/n44/README.md) | 合成入口与来源定向通过；真实终端总体验单列 | not-required |
| <a id="cmd-skillify"></a>CMD-skillify | /skillify | 在TTY builtin执行有效/缺参/非法参数；busy/waiting 状态执行 | 内置技能提取 prompt 展开；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-446](module-map.md#mm-446)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 44已实现本票路径 | [普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) · [冻结提示对照](../ruocun-next24h/evidence/batch-04/n44/README.md) | 合成入口与来源定向通过；真实终端总体验单列 | not-required |
| <a id="cmd-theme"></a>CMD-theme | /theme | 在App执行有效/缺参/非法参数；busy/waiting 状态执行 | 会话主题切换，不改变调度器状态；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-747](module-map.md#mm-747)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | pending |
| <a id="cmd-loop"></a>CMD-loop | /loop | 在App执行有效/缺参/非法参数；busy/waiting 状态执行 | 整数 s/m/h 周期排队、off 取消与退出清理；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断 | [MM-747](module-map.md#mm-747)、[MM-451](module-map.md#mm-451) | 既有 CLI/协议/模块行为 | 47已实现 | 普通输入owner及会话调度独立通过 | Windows合成入口 | pending |

### WIRE

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="wire-01"></a>WIRE-01 | 请求保真 | 捕获各 provider/模型/语言/模式/上下文请求 | 固定 system/messages/tool schema 顺序、角色/字段/空值和 extra 覆盖与冻结 oracle 一致；品牌替换差异白名单 | [MM-439](module-map.md#mm-439) | 既有模型 transport/请求回放 | 04本票路径已实现 | [04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；208 passed，五项入口全0 | 04自动通过；其它未验 | not-required |
| <a id="wire-02"></a>WIRE-02 | 输出上限/思考参数 | 默认、env、单次 maxTokens、模型 cap、effort 与空截断重试 | 128000 默认、256000 特殊重试并裁 cap；max_tokens/max_completion_tokens 选择、thinking/effort/parallel/tool_choice 原规则；不加未配置采样参数 | [MM-404](module-map.md#mm-404) | 既有模型 transport/请求回放 | 04本票路径已实现 | [04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；208 passed，五项入口全0 | 04自动通过；其它未验 | not-required |
| <a id="wire-03"></a>WIRE-03 | Chat SSE 分帧 | 拆 UTF-8 字节、CR/LF、跨帧/多帧/空行与 DONE | 文本/reasoning/工具参数按 index 完整累积；usage/finish_reason 只按有效数据确认 | [MM-443](module-map.md#mm-443) | 既有模型 transport/请求回放 | 04本票路径已实现 | [04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；208 passed，五项入口全0 | 04自动通过；其它未验 | not-required |
| <a id="wire-04"></a>WIRE-04 | Responses 桥 | 函数调用/输出、reasoning items、结束/错误与流式事件 | 路由判据、store/include、effort 映射及统一事件回传与冻结桥等价 | [MM-441](module-map.md#mm-441) | 既有模型 transport/请求回放 | 05本票路径已实现 | [05实现证据](evidence/05-responses/README.md)、[05独立复核](../../integration-evidence/05-responses/README.md)；256 passed，契约36/36、安装28/28 | 05自动通过；其它未验 | not-required |
| <a id="wire-05"></a>WIRE-05 | 历史 wire 清洗 | assistant null、reasoning 有/无 tools、imageData/responseItems | null 转空串；工具轮 reasoning 按原规则带回；内部字段不泄漏 | [MM-439](module-map.md#mm-439) | 既有模型 transport/请求回放 | 04本票路径已实现 | [04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；208 passed，五项入口全0 | 04自动通过；其它未验 | not-required |
| <a id="wire-06"></a>WIRE-06 | usage/缓存/费用 | 原生 cache 字段、cached_tokens fallback、多模型重启 | 原字段优先、miss非负、四累计token恢复连续；本进程分模型费用累计，重启历史费用不完整并明确标注（R1）；不保证供应商命中率 | [MM-590](module-map.md#mm-590) | 既有模型 transport/请求回放 | 28范围通过 | 实际API用量和缓存累计、本次费用与重开独立通过 | Windows合成回环 | not-required |
| <a id="wire-07"></a>WIRE-07 | 重试与非流式 fallback | 产出前/后断线、408/429/529、Retry-After、background | 只在参考允许阶段/次数重试；已有内容不从头重复；529 background、无 Retry-After 的429保留分支 | [MM-439](module-map.md#mm-439) | 既有模型 transport/请求回放 | 06本票路径已实现；母案例族仍按子项 | [06独立复核](integration-evidence/sprint06/README.md)及[回修](evidence/06-resilient/sprint-fixes/README.md) | 06自动通过；真实模型/最终终端及其它未覆盖项未验 | not-required |
| <a id="wire-08"></a>WIRE-08 | idle watchdog | 只有心跳/无有效 delta、已有部分内容、用户 abort | 默认240秒仅有效 delta 重置；用户取消保留部分；产出后 idle 显示明确错误 | [MM-439](module-map.md#mm-439) | 既有模型 transport/请求回放 | 06本票路径已实现；母案例族仍按子项 | [06独立复核](integration-evidence/sprint06/README.md)及[回修](evidence/06-resilient/sprint-fixes/README.md) | 06自动通过；真实模型/最终终端及其它未覆盖项未验 | not-required |
| <a id="wire-09"></a>WIRE-09 | loop 错误与限流 | 上下文过长、根限流选择、子代理失败、持续服务不可用 | 压缩上限/有界重试/账户选择/ModelUnavailableStop 保持；不自动换业务主模型 | [MM-404](module-map.md#mm-404) | 既有模型 transport/请求回放 | 29范围通过 | 真实合成HTTP限流、同模型有界重试、失败保留独立通过 | Windows合成回环 | not-required |
| <a id="wire-10"></a>WIRE-10 | 空响应/坏工具 JSON | 空文本、reasoning-only、finish length、截断参数/不支持 tool_choice | 不把空坏 assistant 永久污染历史；有界修复与诊断，参数非法不调用 handler | [MM-693](module-map.md#mm-693) | 既有模型 transport/请求回放 | N0前台子路径已实现 | N0-WIRE10/687项及独审通过 | Windows自动通过；Terminal未验 | not-required |
| <a id="wire-11"></a>WIRE-11 | 预算与轮数 | 主/子代理轮数、提醒/硬预算开关、价格覆盖 | 默认主轮数无上限、子代理规则和hard开关沿来源；R1费用阈值按本次运行口径，重启可能重新计数，不承诺跨重启总额限制；completed非质量验收 | [MM-426](module-map.md#mm-426) | 既有模型 transport/请求回放 | 28范围通过 | 原轮数边界、显式硬预算及恢复口径通过 | Windows合成入口 | not-required |
| <a id="wire-12"></a>WIRE-12 | 取消流与迟到事件 | 取消已读/排队 delta、切换会话/epoch后收旧事件 | 当前运行不再消费旧事件；部分内容只提交一次；网络取消与底层副作用分开确认 | [MM-422](module-map.md#mm-422) | 既有模型 transport/请求回放 | 未开始 | 无 | 未验 | not-required |

### TOOL

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="tool-read"></a>TOOL-Read | Read | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 文本带行号、offset/limit、图片；二进制/大文件护栏，记录编辑前读取元信息；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-691](module-map.md#mm-691)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 文本/图片及N0普通回合已实现；完整权限/并发后继另验 | 91来源+5必要适配独审通过；[M01](../ruocun-mvp/evidence/m01/README.md)；母族未全验 | Windows来源适配通过；真实Terminal未验 | not-required |
| <a id="tool-listdir"></a>TOOL-ListDir | ListDir | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 路径目录列表；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-664](module-map.md#mm-664)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="tool-glob"></a>TOOL-Glob | Glob | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 文件/路径 glob，修改时间排序；实际导出变量名 fileSearchTool；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-655](module-map.md#mm-655)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 首版文本七工具子集已实现；完整扩展/图片能力后置 | 91来源+5必要适配独审通过；[M01](../ruocun-mvp/evidence/m01/README.md)；母族未全验 | Windows来源适配通过；真实Terminal未验 | not-required |
| <a id="tool-grep"></a>TOOL-Grep | Grep | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 正则、内容/文件模式、上下文、分页、跨行、类型等；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-661](module-map.md#mm-661)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 首版文本七工具子集已实现；完整扩展/图片能力后置 | 91来源+5必要适配独审通过；[M01](../ruocun-mvp/evidence/m01/README.md)；母族未全验 | Windows来源适配通过；真实Terminal未验 | not-required |
| <a id="tool-write"></a>TOOL-Write | Write | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 全文创建/覆盖，读前检查、mtime/size 漂移、锁与原子替换；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-742](module-map.md#mm-742)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 首版文本七工具子集已实现；完整扩展/图片能力后置 | 91来源+5必要适配独审通过；[M01](../ruocun-mvp/evidence/m01/README.md)；母族未全验 | Windows来源适配通过；真实Terminal未验 | not-required |
| <a id="tool-edit"></a>TOOL-Edit | Edit | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | old/new string，唯一匹配或 replace_all，锁与 diff；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-631](module-map.md#mm-631)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 首版文本七工具子集已实现；完整扩展/图片能力后置 | 91来源+5必要适配独审通过；[M01](../ruocun-mvp/evidence/m01/README.md)；母族未全验 | Windows来源适配通过；真实Terminal未验 | not-required |
| <a id="tool-notebookedit"></a>TOOL-NotebookEdit | NotebookEdit | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | ipynb 单元格编辑；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-678](module-map.md#mm-678)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 范围移出（20） | 未运行 | 范围移出 | not-required |
| <a id="tool-bash"></a>TOOL-Bash | Bash | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 前台命令、显式后台、沙箱开关、进程转后台；前台当前无超时参数；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-637](module-map.md#mm-637)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 前后台受管路径及60/61沙箱路由通过 | [批次08](../ruocun-next24h/batch-08.md#交付记录) | 普通/一次性绕过、Windows不支持、Linux文件与禁网真实验证，macOS实机单列 | not-required |
| <a id="tool-bashoutput"></a>TOOL-BashOutput | BashOutput | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 按后台 Shell id 增量读日志并节流；不是阻塞等待；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-640](module-map.md#mm-640)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 15本票Windows路径已实现，相关母案例其余路径按后票 | [runner与恢复独审](../ruocun-next24h/evidence/review/managed-shell-review.md)、[固定r2纯安装](../ruocun-next24h/evidence/review/pure-r2-review.md) | 真实owner强杀/同run接管/Job止写及ACL路径已核，跨账户与非Windows未验 | not-required |
| <a id="tool-killshell"></a>TOOL-KillShell | KillShell | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 请求终止已启动 Shell，取消请求不等于退出确认；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-639](module-map.md#mm-639)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 15本票Windows路径已实现，相关母案例其余路径按后票 | [runner与恢复独审](../ruocun-next24h/evidence/review/managed-shell-review.md)、[固定r2纯安装](../ruocun-next24h/evidence/review/pure-r2-review.md) | 真实owner强杀/同run接管/Job止写及ACL路径已核，跨账户与非Windows未验 | not-required |
| <a id="tool-webfetch"></a>TOOL-WebFetch | WebFetch | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | URL 抓取、纯文本/按 prompt 抽取、缓存与 SSRF 检查；no-web 时不注册；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-651](module-map.md#mm-651)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 22本票子路径已实现 | [独审](../ruocun-next24h/evidence/review/b06-webfetch-review.md) | 来源语义及普通入口技术通过；覆盖范围/限制见独审，完整终端及其它平台另验 | not-required |
| <a id="tool-websearch"></a>TOOL-WebSearch | WebSearch | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | DuckDuckGo HTML 搜索，结果上限；no-web 时不注册；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-740](module-map.md#mm-740)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 23本票子路径已实现 | [独审](../ruocun-next24h/evidence/review/b06-websearch-review.md) | 来源语义及普通入口技术通过；覆盖范围/限制见独审，完整终端及其它平台另验 | not-required |
| <a id="tool-askuserquestion"></a>TOOL-AskUserQuestion | AskUserQuestion | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 询问、选项/多选，由上下文提供 UI；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-623](module-map.md#mm-623)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 21普通工具与入口已实现 | [来源与普通TTY独审](../ruocun-next24h/evidence/review/user-tools-review.md)通过，固定包待验 | 受控TTY已验；真实WT未验 | not-required |
| <a id="tool-todowrite"></a>TOOL-TodoWrite | TodoWrite | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 整表替换的扁平清单，无独立 task id；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-729](module-map.md#mm-729)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 完整元信息/扁平清单及N0首批/完成提示已实现 | 91来源+5必要适配独审通过；[M01](../ruocun-mvp/evidence/m01/README.md)；母族未全验 | Windows来源适配通过；真实Terminal未验 | not-required |
| <a id="tool-memoryread"></a>TOOL-MemoryRead | MemoryRead | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 取记忆正文；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-670](module-map.md#mm-670)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 30路径已实现 | [30来源、实际入口和独审](../ruocun-next20h/evidence/n4-shared/README.md)通过 | Windows合成CLI/受控TTY已验；真实Terminal未验 | not-required |
| <a id="tool-memorywrite"></a>TOOL-MemoryWrite | MemoryWrite | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 五种类型、三作用域、重要度/来源，或明确删除；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-672](module-map.md#mm-672)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 30路径已实现 | [30来源、实际入口和独审](../ruocun-next20h/evidence/n4-shared/README.md)通过 | Windows合成CLI/受控TTY已验；真实Terminal未验 | not-required |
| <a id="tool-skill"></a>TOOL-Skill | Skill | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 按名加载技能正文；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-705](module-map.md#mm-705)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 静态调用已实现 | [A-SKILLS](../ruocun-advanced-a/evidence/integration/README.md)模块独审及CLI按需正文通过；阶段A自动出口通过 | 合成CLI已验；真实模型未验 | not-required |
| <a id="tool-skillinstall"></a>TOOL-SkillInstall | SkillInstall | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | Git/本地技能安装；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-707](module-map.md#mm-707)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="tool-agent"></a>TOOL-Agent | Agent | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 单/多任务、同步/后台、fork/worktree/model/plan；继续代理由 TaskSend/recovery 路径处理；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-621](module-map.md#mm-621)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 43已实现本票路径 | [代理消息独审](../ruocun-next24h/evidence/review/b04-agent-messages-review.md) | 普通入口和冻结来源定向独审通过；母案例其余组合按逐票 | not-required |
| <a id="tool-tasksend"></a>TOOL-TaskSend | TaskSend | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 向代理追加指令，已结束任务的恢复转交 ctx.resumeAgent；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-721](module-map.md#mm-721)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 43已实现本票路径 | [代理消息独审](../ruocun-next24h/evidence/review/b04-agent-messages-review.md) | 普通入口和冻结来源定向独审通过；母案例其余组合按逐票 | not-required |
| <a id="tool-messageparent"></a>TOOL-MessageParent | MessageParent | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 子代理发送进展或 attention 给父；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-674](module-map.md#mm-674)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 43已实现本票路径 | [代理消息独审](../ruocun-next24h/evidence/review/b04-agent-messages-review.md) | 普通入口和冻结来源定向独审通过；母案例其余组合按逐票 | not-required |
| <a id="tool-taskwait"></a>TOOL-TaskWait | TaskWait | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 对当前会话后台代理或 Shell 的 any/all 事件等待；单独调用，不等待手工/前台任务；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-726](module-map.md#mm-726)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="tool-taskcreate"></a>TOOL-TaskCreate | TaskCreate | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 只建手工任务记录，不启动进程；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-713](module-map.md#mm-713)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 45已实现 | 来源与真实SQLite记录、重开独立通过 | Windows合成入口 | not-required |
| <a id="tool-tasklist"></a>TOOL-TaskList | TaskList | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | taskManager 当前/含已结束清单；不是 Shell 统一清单；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-717](module-map.md#mm-717)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 45已实现 | 来源与真实SQLite当前/历史清单独立通过 | Windows合成入口 | not-required |
| <a id="tool-taskget"></a>TOOL-TaskGet | TaskGet | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | taskManager 单任务详情；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-715](module-map.md#mm-715)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 45已实现 | 来源与真实SQLite单项详情独立通过 | Windows合成入口 | not-required |
| <a id="tool-taskoutput"></a>TOOL-TaskOutput | TaskOutput | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 代理转录增量，WeakMap 游标；手工任务无转录；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-719](module-map.md#mm-719)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 40已实现 | [40证据](../ruocun-next24h/evidence/n40-agent-background/README.md) | 来源定向通过 | not-required |
| <a id="tool-taskupdate"></a>TOOL-TaskUpdate | TaskUpdate | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 手工任务描述/状态/结果；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-725](module-map.md#mm-725)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 45已实现 | 来源与真实SQLite更新、停止与原执行状态保护独立通过 | Windows合成入口 | not-required |
| <a id="tool-taskstop"></a>TOOL-TaskStop | TaskStop | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 代理 abort→canceling→执行器确认 canceled，手工任务直接取消；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-723](module-map.md#mm-723)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 40已实现 | [40独审](../ruocun-next24h/evidence/review/b02-agent-background-review.md) | 真实SQLite与取消owner复验通过 | not-required |
| <a id="tool-notifyuser"></a>TOOL-NotifyUser | NotifyUser | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | W6：仅终端内提示/安全标题，准确说明未发送桌面通知；schema与来源差异单列，错误结果可配对，副作用不盲重放 | [MM-680](module-map.md#mm-680)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="tool-sendusermessage"></a>TOOL-SendUserMessage | SendUserMessage | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 用户可见消息、附件路径、normal/proactive 状态；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-703](module-map.md#mm-703)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 21普通工具与入口已实现 | [来源与普通TTY独审](../ruocun-next24h/evidence/review/user-tools-review.md)通过，固定包待验 | 受控TTY已验；真实WT未验 | not-required |
| <a id="tool-enterplanmode"></a>TOOL-EnterPlanMode | EnterPlanMode | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 切换只读规划；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-687](module-map.md#mm-687)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="tool-exitplanmode"></a>TOOL-ExitPlanMode | ExitPlanMode | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 提交方案并退出规划，由上下文处理批准；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-687](module-map.md#mm-687)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="tool-enterworktree"></a>TOOL-EnterWorktree | EnterWorktree | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 当前代理进入隔离树，记录 previousCwd；不允许叠加进入；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-635](module-map.md#mm-635)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="tool-exitworktree"></a>TOOL-ExitWorktree | ExitWorktree | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | keep/remove，丢弃有改动或新增提交需 discard_changes；恢复 cwd；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-645](module-map.md#mm-645)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="tool-monitor"></a>TOOL-Monitor | Monitor | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 后台监控命令，stdout 按行批量通知，persistent/超时与 TaskStop；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-676](module-map.md#mm-676)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 46本票路径已实现 | [Monitor独审](../ruocun-next24h/evidence/review/b05-monitor-review.md) | 激活/真实执行/输出/持久/停止及owner丢失独审通过；不重启旧监控 | not-required |
| <a id="tool-config"></a>TOOL-Config | Config | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 配置读取或写用户 settings，含权限模式/主题/检查点及通用点路径；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-624](module-map.md#mm-624)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 25本票子路径已实现 | [独审](../ruocun-next24h/evidence/review/b06-config-review.md) | 来源语义及普通入口技术通过；覆盖范围/限制见独审，完整终端及其它平台另验 | not-required |
| <a id="tool-schedule"></a>TOOL-Schedule | Schedule | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | W3：Windows系统级定时明确不支持，不用会话loop冒充；来源其它平台add/list/remove路由及schema保留未验，错误结果可配对 | [MM-700](module-map.md#mm-700)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 59已接入 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | Windows普通入口拒绝，POSIX合成端口通过 | not-required |
| <a id="tool-croncreate"></a>TOOL-CronCreate | CronCreate | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | W3：Windows持久系统定时创建明确不支持；来源其它平台语义/定义保留未验，错误结果可配对，不假称已创建 | [MM-625](module-map.md#mm-625)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 59已接入 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | Windows拒绝，POSIX合成端口通过 | not-required |
| <a id="tool-crondelete"></a>TOOL-CronDelete | CronDelete | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | W3：Windows系统定时删除明确不支持；来源其它平台清单序号删除语义保留未验，错误结果可配对 | [MM-625](module-map.md#mm-625)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 59已接入 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | Windows拒绝，POSIX合成端口通过 | not-required |
| <a id="tool-cronlist"></a>TOOL-CronList | CronList | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | W3：Windows系统级定时查询明确不支持，不以空表假称成功；来源其它平台清单语义保留未验 | [MM-625](module-map.md#mm-625)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 59已接入 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | Windows拒绝，POSIX合成端口通过 | not-required |
| <a id="tool-toolsearch"></a>TOOL-ToolSearch | ToolSearch | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 搜索激活 MCP 和延迟内置工具；无 MCP 也注册；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-733](module-map.md#mm-733)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 21原生及53 MCP本票路径已实现 | [stdio](../ruocun-next24h/evidence/review/b05-mcp-cli-review.md) · [HTTP/SSE](../ruocun-next24h/evidence/review/b05-http-review.md) · [能力/命令](../ruocun-next24h/evidence/review/b05-caps-paused-review.md) | 原生deferred与MCP搜索激活、精确可见性恢复通过来源子案例 | not-required |
| <a id="tool-repomap"></a>TOOL-RepoMap | RepoMap | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 获取/刷新代码地图；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-695](module-map.md#mm-695)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 33本票子路径已实现 | [独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) | 来源语义及普通入口技术通过；覆盖范围/限制见独审，完整终端及其它平台另验 | not-required |
| <a id="tool-lsp"></a>TOOL-LSP | LSP | 有效参数、缺必填/错误类型/边界值；允许/拒绝/取消；同名重试与恢复 | 9操作：goToDefinition/findReferences/hover/documentSymbol/workspaceSymbol/goToImplementation/prepareCallHierarchy/incomingCalls/outgoingCalls；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放 | [MM-666](module-map.md#mm-666)、[MM-693](module-map.md#mm-693)、[MM-642](module-map.md#mm-642) | 既有 CLI/协议/模块行为 | 55本票子路径已实现 | [独审](../ruocun-next24h/evidence/review/b06-lsp-review.md) | 来源语义及普通入口技术通过；覆盖范围/限制见独审，完整终端及其它平台另验 | not-required |

### PERM

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="perm-01"></a>PERM-01 | 规则和身份 | Tool/Tool(specifier)、路径glob、domain、Bash前缀和大小写 | 各工具匹配方言与deny>ask>allow；路径canonical化和最终参数一致，非通用fnmatch替换 | [MM-554](module-map.md#mm-554) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="perm-02"></a>PERM-02 | 模式裁决 | plan/yolo/运行覆盖/defaultMode/auto组合 | plan优先，提示与API裁剪及执行复核一致；权限拒绝可解释 | [MM-547](module-map.md#mm-547) | 既有 CLI/协议/模块行为 | 未开始 | 无 | 未验 | not-required |
| <a id="perm-03"></a>PERM-03 | Shell 安全 | Bash AST复杂/嵌套/危险模式，PowerShell/cmd对应语法与转义 | 未知复杂语义ask，拒绝不能借换shell绕过；审批文本等于实际执行语义 | [MM-537](module-map.md#mm-537) | 既有 CLI/协议/模块行为 | 13真实方言/最终计划及一次性审批已实现 | [来源与普通TTY独审](../ruocun-next24h/evidence/review/shell-plan-review.md)通过，固定包待验 | 受控TTY已验；真实WT未验 | not-required |
| <a id="perm-04"></a>PERM-04 | 审批持久化/分类器 | ask合批、始终允许、拒绝、无stdin、auto分类器失败/熔断 | 自动批准仅显式配置；无交互不挂死/不默许；拒绝原因、审计和保存规则一致 | [MM-539](module-map.md#mm-539) | 既有 CLI/协议/模块行为 | 分类器/熔断与普通入口已实现 | [来源与普通TTY独审](../ruocun-next24h/evidence/review/permissions-review.md)通过，固定包待验 | 受控TTY已验；实机未验 | not-required |
| <a id="perm-05"></a>PERM-05 | 秘密与信任边界 | env/token/路径敏感数据、未信任扩展和Hook输出 | 按实际边界脱敏与裁决；来源信任缺口/扩大gate的建议单列差异待决，不谎报隔离 | [MM-558](module-map.md#mm-558) | 既有 CLI/协议/模块行为 | 秘密脱敏与既有权限信任路径已接；扩展/Hook边界待对应票 | [本票秘密与审计独审](../ruocun-next24h/evidence/review/permissions-review.md)通过 | 实机未验 | not-required |

### MEM

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="mem-01"></a>MEM-01 | 记忆存储与来源 | 五类型/三scope、Markdown/locked/手改、过期或失效source | 类型/项目过滤、来源验证/审计及删除正确；session与长期记忆分开 | [MM-514](module-map.md#mm-514) | 既有 CLI/协议/模块行为 | 30存储、来源、审核及删除已实现；31启动项目过滤已实现 | [30来源、实际入口和独审](../ruocun-next20h/evidence/n4-shared/README.md)通过 | Windows合成CLI/受控TTY已验；真实Terminal未验 | not-required |
| <a id="mem-02"></a>MEM-02 | 注入与整理 | 固定全文/索引、distill/consolidate/衰减/GC、失败fallback | 预算/稳定前缀、源引用和locked保护；模型失败不丢原数据 | [MM-510](module-map.md#mm-510) | 既有 CLI/协议/模块行为 | 31启动注入、32蒸馏/门控合并/GC已实现；自动反思归42 | [31/32来源、实际入口及独审](../ruocun-next20h/evidence/n4-shared/README.md)通过；未知同名发布保留原始副本 | Windows合成入口已验；真实模型/Terminal未验 | not-required |
| <a id="mem-03"></a>MEM-03 | 压缩与反思 | 85%主动、超限反应式、间隔/同步、fork蒸馏、重启 | 保留用户目标/工具对/背景等待状态；提示、触发/预算与注入边界按oracle | [MM-394](module-map.md#mm-394) | 既有 CLI/协议/模块行为 | 29压缩与42反思路径通过 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | 定向验证默认关闭、热前缀、工具配对、写入与恢复保护 | not-required |
| <a id="mem-04"></a>MEM-04 | 代码地图 | 多语言图/缓存、超过4000文件或512KiB、预算/刷新 | 默认2048 token预算、符号/排名/裁剪与mtime+size缓存语义；失败不污染主历史 | [MM-574](module-map.md#mm-574) | 既有 CLI/协议/模块行为 | 33本票子路径已实现 | [独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) | 来源语义及普通入口技术通过；覆盖范围/限制见独审，完整终端及其它平台另验 | not-required |
| <a id="mem-05"></a>MEM-05 | 审计与可选观测 | 每流开关、trace/tool/perm/cache/skill、关闭obs/退出flush | 旁路失败不伪造业务失败；隐私脱敏；关闭观测时业务等效；缓存归因不冒充真实命中率 | [MM-523](module-map.md#mm-523) | 既有 CLI/协议/模块行为 | 57审计及可选观测通过 | [批次07证据](../ruocun-next24h/batch-07.md#交付记录) | 本地collector实际导出、父子归因、脱敏、失败旁路与关闭独审 | not-required |

### UI

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="wt-01"></a>WT-01 | 真实中文IME/Unicode编辑 | Windows Terminal 可见Python进程，中文IME、CJK/emoji/组合字符、光标/删除/多行 | 候选窗/光标/提交内容正确，字符不丢不劈，hash与用户输入一致 | [MM-747](module-map.md#mm-747)、[MM-794](module-map.md#mm-794)、[MM-767](module-map.md#mm-767) | 已确认真实 Python Windows Terminal 操作 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [真实WT五项反馈与退出](../ruocun-next24h/evidence/n18/wt/runs/20261111T044203Z-514e10/README.md)、[独立复核](../ruocun-next24h/evidence/review/terminal-wt-review.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | R4 中文 IME 候选、表情提交与回显实机通过 | accepted |
| <a id="wt-02"></a>WT-02 | 粘贴/折叠/图片 | CRLF/CR、>280 JS单位或>6行、报告样字符串、图片路径与clipboard | 粘贴不自动提交，折叠提交展开原文；不吞真实文本；图片类型/5MB边界准确 | [MM-747](module-map.md#mm-747)、[MM-794](module-map.md#mm-794)、[MM-767](module-map.md#mm-767) | 已确认真实 Python Windows Terminal 操作 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [真实WT五项反馈与退出](../ruocun-next24h/evidence/n18/wt/runs/20261111T044203Z-514e10/README.md)、[独立复核](../ruocun-next24h/evidence/review/terminal-wt-review.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | 实机粘贴折叠、图片与文字送达，中文表情剪贴板回环通过 | accepted |
| <a id="wt-03"></a>WT-03 | 流式与忙时输入 | 连续token+工具输出时编辑草稿并Enter排队，多条输入/模态 | 草稿稳定，队列保序，可见等待状态，工具对不被插断 | [MM-747](module-map.md#mm-747)、[MM-794](module-map.md#mm-794)、[MM-767](module-map.md#mm-767) | 已确认真实 Python Windows Terminal 操作 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [真实WT五项反馈与退出](../ruocun-next24h/evidence/n18/wt/runs/20261111T044203Z-514e10/README.md)、[独立复核](../ruocun-next24h/evidence/review/terminal-wt-review.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | 实机流式排队保序、草稿保留和取消回执通过 | accepted |
| <a id="wt-04"></a>WT-04 | 中断与退出 | Esc、模态Esc、Ctrl+C两次/间隔、Ctrl+B前台转后台 | Esc按模态优先/先清队列再暂停；2秒双Ctrl+C退出；后台不被旧前台取消 | [MM-747](module-map.md#mm-747)、[MM-794](module-map.md#mm-794)、[MM-767](module-map.md#mm-767) | 已确认真实 Python Windows Terminal 操作 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [真实WT五项反馈与退出](../ruocun-next24h/evidence/n18/wt/runs/20261111T044203Z-514e10/README.md)、[独立复核](../ruocun-next24h/evidence/review/terminal-wt-review.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | 实机先清队列再暂停，前台取消时同一后台 Shell 继续并正常完成，正常退出已核验 | accepted |
| <a id="wt-05"></a>WT-05 | 缩放/原生scrollback | 连续变窄变宽/高低、超高消息、选择复制/滚动、共享窗口 | 清理旧物理行无残影/吞历史，重绘不丢草稿；仅owned窗口按确认策略清理自有视口 | [MM-747](module-map.md#mm-747)、[MM-794](module-map.md#mm-794)、[MM-767](module-map.md#mm-767) | 已确认真实 Python Windows Terminal 操作 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [实机缩放、草稿与滚动](../ruocun-next24h/evidence/n18/wt/runs/20261111T075358Z-ea4e4c/README.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | 实机专属与共享窗口缩放、草稿与历史保留通过 | accepted |
| <a id="wt-06"></a>WT-06 | 面板/快捷键/审批 | Ctrl+T/G/O、Shift+Tab、账户/技能/模型选择器、问题/审批/主题语言 | 焦点与模态层级正确，无stdin竞争，选择/拒绝和状态反馈一致 | [MM-747](module-map.md#mm-747)、[MM-794](module-map.md#mm-794)、[MM-767](module-map.md#mm-767) | 已确认真实 Python Windows Terminal 操作 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [66独审](../ruocun-next24h/evidence/review/b02-modals-notify-review.md)、[真实WT](../ruocun-next24h/evidence/n18/wt/runs/20261111T075358Z-ea4e4c/README.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | 问答、面板、主题、焦点、审批与交接经实机确认 | accepted |
| <a id="wt-07"></a>WT-07 | 焦点/安全标题/终端提示 | 焦点丢失/恢复、后台注意状态、标题控制字符、终端提示去向 | W6只保留终端内提示与安全标题，不冒充桌面通知；W5不提供Windows自动防休眠保证；焦点/状态行为仍须真实验收 | [MM-747](module-map.md#mm-747)、[MM-794](module-map.md#mm-794)、[MM-767](module-map.md#mm-767) | 已确认真实 Python Windows Terminal 操作 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [63来源与定向验证](../ruocun-next24h/evidence/batch-02/n63/README.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | 实机终端通知、标签先黄后绿、切回清除通过 | accepted |
| <a id="wt-08"></a>WT-08 | Sixel欢迎区与回包 | 能力探测、分片/迟到DA/CPR/focus、resize/modal/背压、失败终端 | 单owner解析，粘贴不吞；图形最多一帧在途/旧epoch丢弃；失败回文本且无转义泄露 | [MM-747](module-map.md#mm-747)、[MM-794](module-map.md#mm-794)、[MM-767](module-map.md#mm-767) | 已确认真实 Python Windows Terminal 操作 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [原图实机回执](../ruocun-next24h/evidence/n18/wt/runs/20261111T092536Z-1592d0/README.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | 实机 R4 欢迎原图清晰，缩放后恢复；文字欢迎正常 | accepted |
| <a id="wt-09"></a>WT-09 | 管道与终端恢复 | 非TTY、重定向、EOF、异常退出/强杀后重开终端 | 可读文本无光标控制污染；可控退出恢复mode/cursor/paste/focus/title；强杀后给出可执行恢复说明 | [MM-747](module-map.md#mm-747)、[MM-794](module-map.md#mm-794)、[MM-767](module-map.md#mm-767) | 已确认真实 Python Windows Terminal 操作 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [真实WT五项反馈与退出](../ruocun-next24h/evidence/n18/wt/runs/20261111T044203Z-514e10/README.md)、[独立复核](../ruocun-next24h/evidence/review/terminal-wt-review.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | R4 主会话、文字降级和重启恢复三阶段正常退出，控制台模式均恢复 | accepted |

### WIN

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="win-01"></a>WIN-01 | Shell/环境探测 | 普通用户 cmd/Windows PowerShell/pwsh，中文/空格/引号/换行/env/管道/.cmd | 方言显式、编码/argv不损坏，doctor与env不执行POSIX误语法，审批与执行一致 | [NEW 平台模块](module-map.md#新增适配层候选位置)；[Windows研究](../ruocun-discovery/research/16-windows-capabilities.md) | 已确认 Windows 本机能力探针/产品验收 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | R4 原生 Shell、执行和环境定向证据通过 | not-required |
| <a id="win-02"></a>WIN-02 | 受管进程树 | 前台/后台/独立runner，子孙忽略温和停止、继承pipe、owner退出/强杀 | 身份核验、有限force收口、真实close才canceled；keep-background独立生命周期，无多余可见窗口 | [NEW 平台模块](module-map.md#新增适配层候选位置)；[Windows研究](../ruocun-discovery/research/16-windows-capabilities.md) | 已确认 Windows 本机能力探针/产品验收 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | R4 受管进程、仓外同 run 恢复及实机 Shell 转后台完成 | not-required |
| <a id="win-03"></a>WIN-03 | IPC与ACL | 命名管道或认证loopback、错token/run/epoch、其他本地用户/宽DACL反例 | 已认证且最小访问范围可实证；HMAC不替代ACL，进程身份/句柄继承可查 | [NEW 平台模块](module-map.md#新增适配层候选位置)；[Windows研究](../ruocun-discovery/research/16-windows-capabilities.md) | 已确认 Windows 本机能力探针/产品验收 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [runner与恢复独审](../ruocun-next24h/evidence/review/managed-shell-review.md)、[固定r2纯安装](../ruocun-next24h/evidence/review/pure-r2-review.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | 实际 Windows IPC、ACL 及签名回执通过，其它本地账户实机待验 | not-required |
| <a id="win-04"></a>WIN-04 | 持久文件/SQLite | NTFS、占用、原子替换、flush、中文目录/长路径/网络盘误用 | 失败保持原文件，持久确认含义真实、网络不支持明确拒绝；不把目录fsync失败吞掉 | [NEW 平台模块](module-map.md#新增适配层候选位置)；[Windows研究](../ruocun-discovery/research/16-windows-capabilities.md) | 已确认 Windows 本机能力探针/产品验收 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | R4 Windows 文件、SQLite 定向门禁通过，实机原会话重启恢复 | not-required |
| <a id="win-05"></a>WIN-05 | 系统凭据 | 假秘密写取删、账户名大小写、拒绝/后端不可用、文件fallback | Credential Manager或等效后端，case collision可区分，失败不误报系统保存，秘密不入日志 | [NEW 平台模块](module-map.md#新增适配层候选位置)；[Windows研究](../ruocun-discovery/research/16-windows-capabilities.md) | 已确认 Windows 本机能力探针/产品验收 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [来源/新UUID/普通入口独审](../ruocun-next24h/evidence/review/credentials-review.md)通过；最终包待验 · [R4 自动出口](evidence/b09-r4-automatic/README.md) | 实机 Windows 重启后系统凭据读回一致，删除后为 not-found | accepted |
| <a id="win-06"></a>WIN-06 | 系统定时支持边界 | Windows调用Schedule/Cron入口准确返回本轮不支持；会话loop另验 | W3取消Task Scheduler/Windows dispatcher，不能用loop替代后标系统定时通过；来源其它平台路由保留未验 | [NEW 平台模块](module-map.md#新增适配层候选位置)；[Windows研究](../ruocun-discovery/research/16-windows-capabilities.md) | 已确认 Windows 本机能力探针/产品验收 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [批次07证据](../ruocun-next24h/batch-07.md#交付记录) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | Windows 明确拒绝系统级定时，保留会话内 loop，定向技术门禁通过 | accepted |
| <a id="win-07"></a>WIN-07 | 电源支持边界 | Windows长任务不宣称取得唤醒锁；提示用户管理电源，取消/退出仍正确 | W5不提供Windows自动防休眠保证；原系统锁能力范围移出，不将无锁状态记为acquire成功 | [NEW 平台模块](module-map.md#新增适配层候选位置)；[Windows研究](../ruocun-discovery/research/16-windows-capabilities.md) | 已确认 Windows 本机能力探针/产品验收 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [批次07证据](../ruocun-next24h/batch-07.md#交付记录) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | Windows 电源能力准确说明，实机 doctor 正常，定向技术门禁通过 | accepted |
| <a id="win-08"></a>WIN-08 | 图片/文本clipboard | Unicode文本、RGBA图片、空剪贴板、不支持格式/超限、文件附件 | Windows原生读取，图片类型/上限一致；失败不吞原文本、不执行路径为命令 | [NEW 平台模块](module-map.md#新增适配层候选位置)；[Windows研究](../ruocun-discovery/research/16-windows-capabilities.md) | 已确认 Windows 本机能力探针/产品验收 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [真实WT与PNG哈希](../ruocun-next24h/evidence/n18/wt/runs/20261111T075358Z-ea4e4c/README.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | R4 Windows 终端图片与 Unicode 文本剪贴板通过 | accepted |
| <a id="win-09"></a>WIN-09 | 来源OS沙箱兼容 | 默认关闭、macOS/Linux路由、缺工具、Windows显式启用、no-net开关 | [ADR-0008](../../docs/adr/0008-source-first-sandbox-parity.md)：Windows明确不支持；未启用普通Shell不冒充隔离；支持平台验证真实限制并单列实机状态 | [MM-698](module-map.md#mm-698) | 冻结sandbox.ts及测试/产品路径 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [批次08](../ruocun-next24h/batch-08.md#交付记录) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | Windows 显式启用 OS 沙箱时拒绝；既有 WSL 文件及网络隔离实跑保留，macOS 实机待验 | not-required |
| <a id="win-10"></a>WIN-10 | 终端提示与通知边界 | 中文/命令样载荷只作终端文本、安全标题/焦点/任务状态；报告未发送桌面通知 | W6移出桌面通知端口/窗口，保留终端注意提示且不注入控制字符；不以标题变化假称系统通知发送 | [NEW 平台模块](module-map.md#新增适配层候选位置)；[Windows研究](../ruocun-discovery/research/16-windows-capabilities.md) | 已确认 Windows 本机能力探针/产品验收 | 批次08同候选自动子案例通过 | [本轮自动回执](evidence/b08-automatic/README.md) · [R4 自动出口](evidence/b09-r4-automatic/README.md) | 终端 NotifyUser、标签注意状态和安全边界通过 | accepted |
| <a id="win-11"></a>WIN-11 | 跨平台端口 | 检查核心导入、所有平台分支、可选后端缺失及支持矩阵 | Windows全范围；Linux/macOS可构建/静态检查与真实验收分别记，不能Linux通过冒充Windows补齐 | [NEW 平台模块](module-map.md#新增适配层候选位置)；[Windows研究](../ruocun-discovery/research/16-windows-capabilities.md) | 已确认 Windows 本机能力探针/产品验收 | Windows 正式门禁与 POSIX 源码适配入口已交付 | [82 CI 和实际平台](../ruocun-next24h/evidence/batch-09/n82-ci/README.md) | Windows 定向和安装通过，Ubuntu WSL 源码与原生 Shell 通过，macOS 实跑待验 | not-required |

### TEST

| ID | 原功能/要求 | 验收动作 | 预期契约 | oracle/对应 | 入口 | 实现 | 自动证据 | Windows | HITL |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="test-01"></a>TEST-01 | 来源断言迁移 | 215 test、58 scripts、16 tasks、85 fixture逐项D/R/S/P登记 | 没有漏项或无理由跳过；未执行来源行为不写passed，材料缺失先物化受控fixture | [全部资产定位](module-map.md#已确认测试资产与入口定位)；[研究附录](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 测试工程/文档门禁 | 本轮保留范围的来源断言与冻结材料已绑定 | [02 来源对照](evidence/02-oracle/README.md) · [D14 全映射](../ruocun-discovery/research/14-spec-readiness.md) · [84 安装集成](../ruocun-next24h/evidence/batch-09/n84-installed/README.md) | 来源与产品结果按实际用例登记，未运行资产维持原状态 | not-required |
| <a id="test-02"></a>TEST-02 | 离线/协议确定性 | 合成profile、fake HTTP/SSE/MCP/LSP/Hook/Deck和固定随机/时钟 | 优先现有高层CLI与协议，缺实模型不造测试答案；不读真实用户配置/凭据 | [全部资产定位](module-map.md#已确认测试资产与入口定位)；[研究附录](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 测试工程/文档门禁 | 本地离线协议及最终安装包接线已验 | [76 运行时与协议](../ruocun-next24h/evidence/batch-09/eval/n76/README.md) · [84 安装集成](../ruocun-next24h/evidence/batch-09/n84-installed/README.md) | 等待、取消、恢复与扩展通过对应来源语义复验 | not-required |
| <a id="test-03"></a>TEST-03 | 回放与评估入口 | 恢复/等待脚本、专题replay、memory/cache/reflect与Harbor/SWE/TB | 72–74评估工程、定义/fixture/评分与报告仍保留；确定性/联网/live/第三方分列，V1移出成套付费成绩但不删除资产或虚填评分 | [全部资产定位](module-map.md#已确认测试资产与入口定位)；[研究附录](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 测试工程/文档门禁 | 72–74 离线评估工程与普通入口已验 | [72 评估轨迹](../ruocun-next24h/batch-08.md#交付记录) · [73 记忆与缓存](../ruocun-next24h/evidence/batch-09/eval/n73/README.md) · [74 反思](../ruocun-next24h/evidence/batch-09/eval/n74/README.md) | 定义、轨迹、合成评分、脱敏及失败分类已验，真实模型与第三方环境条件单列 | not-required |
| <a id="test-04"></a>TEST-04 | 成套真实模型任务（本轮移出） | V1：保留16任务定义/fixture及原RUNS=3来源协议，不要求本轮成套付费成绩 | 75成套live评分范围移出；76离线runtime/protocol结果不能回填本行live通过，也不继承DAO历史成绩 | [全部资产定位](module-map.md#已确认测试资产与入口定位)；[研究附录](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 测试工程/文档门禁 | 范围移出（V1，非通过） | 未运行；无成套成绩 | 未验 | not-required |
| <a id="test-05"></a>TEST-05 | 故障归因 | 同输入受控source与port运行，发生失败时最小复现 | SOURCE-DEFECT/PORT-REGRESSION/INTENTIONAL-DELTA/ENV/UNVERIFIED分开；原故障不稀释迁移完成门禁 | [全部资产定位](module-map.md#已确认测试资产与入口定位)；[研究附录](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 测试工程/文档门禁 | 本批实际缺陷、宿主限制及测试环境回执已归因 | [81 数据保护](../ruocun-next24h/evidence/batch-09/n81-upgrade/README.md) · [82 QA 环境](../ruocun-next24h/evidence/batch-09/n82-ci/README.md) · [84 分类](../ruocun-next24h/evidence/batch-09/n84-installed/README.md) | 账户覆盖回归已修，应用控制和原 QA 缺依赖有各自实证和复验 | not-required |
| <a id="test-06"></a>TEST-06 | 验收证据 | 每case保存命令/环境/输入预期实际、版本/lock/SQLite/清理、截图或日志hash | 证据脱敏入Git且可复跑，自动与HITL独立；技术probe不继承为产品通过 | [全部资产定位](module-map.md#已确认测试资产与入口定位)；[研究附录](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 测试工程/文档门禁 | 最终候选、回执、独立复核和图门禁已绑定 | [84 安装集成](../ruocun-next24h/evidence/batch-09/n84-installed/README.md) · [77/78 自动出口](evidence/b09-r3-automatic/README.md) | 自动技术证据可复跑，真实终端和登录重启按 77、78 待验 | not-required |
| <a id="test-07"></a>TEST-07 | 已确认入口的工程落地 | 按已确认的T-N1..T-N5及统一驱动子套件配置并验证入口 | 五项入口已获用户确认（见[确认票](issues/01-test-entrypoints.md)）；既有语义seams沿用；工程实现及执行仍须实际验证，不因确认即宣称可运行 | [全部资产定位](module-map.md#已确认测试资产与入口定位)；[研究附录](../ruocun-discovery/research/04-terminal-platform-delivery.md) | 测试工程/文档门禁 | 进行中；03五入口/offline已实现，其余suite待接入产品 | [03独立修复复核](integration-evidence/03-boot/r2/README.md) | 03自动通过；全量门禁未验 | not-required |


## 故障、行为差异与证据不足登记

本节分别记录来源调查、实验和开发工程缺陷。03工程已实现，业务核心尚未开始；P-01是本次已修复的开发验收驱动缺陷。SOURCE-CANDIDATE 经同输入运行后才可升为 SOURCE-DEFECT；新迁移故障以 P-xx/PORT-REGRESSION 单列；经确认的有意差异以 D-xx/INTENTIONAL-DELTA 单列。环境或材料无效以 ENV/MATERIAL-GAP 记录，不计通过或静默跳过。
| ID | 归类 | 观察 | 证据状态/关联案例 |
| --- | --- | --- | --- |
| S-01 | SOURCE-CANDIDATE | Schedule/Skill操作员命令大小写与help不一致 | 静态；ENT-04；待受控运行oracle确认，不自动加别名 |
| S-02 | SOURCE-CANDIDATE | /permissions编辑分支被前置return遮蔽；菜单3名字无固定handler | 静态；CMD-permissions/CMD-help；动态扩展能供同名，不能当总缺失 |
| S-03 | SOURCE-CANDIDATE / 产品边界已修复 | 来源启动过滤后仍有文件访问发现回调 | 冻结源静态定位。RuoCun 已通过启动、Read、旧队列恢复的真实入口对照。见[71独审](../ruocun-next24h/evidence/review/b07-eval-isolation-review.md) |
| S-04 | SOURCE-CANDIDATE / SCOPE-DELTA | 模型费用桶/lastPrompt/缓存指纹未完整持久化 | 静态；REC-07；R1移出补齐历史分模型费用的保证，消息/四累计token等保留；新费用统计范围明确、缓存元数据可重建，不把原静态疑点伪升实测缺陷 |
| S-05 | SOURCE-CANDIDATE | 前台Bash非0退出文本与looksFailed匹配格式不一致 | 静态；RUN-05/TOOL-Bash；受控批次验证失败屏障/审计/UI oracle |
| S-06 | SOURCE-DEFECT | MCP断线自动重试已实测重复远端副作用 | D15已实测重复副作用；EXT-10按已确认ADR-0003实施，不承诺exactly-once |
| S-07 | SOURCE-CANDIDATE | LSP缺少显式timeout/shutdown及位置转换缺口 | 来源结论仍为静态，不虚报来源运行故障；目标55已按D09补齐并以UTF16/UTF8/超时取消/真实整树退出验证，见[独审](../ruocun-next24h/evidence/review/b06-lsp-review.md) |
| S-08 | SOURCE-CANDIDATE | 插件名称/移除路径未约束；清理按mtime可能碰活会话 | 静态。EXT-04插件路径随50移出。REC-14活会话清理仍按已确认数据边界处理并记录差异 |
| S-09 | SOURCE-CANDIDATE / SCOPE-DELTA | fork exactTools/子代理cwd继承与描述边界不完全一致 | 静态；RUN-07/08；R3保留当前fork/普通恢复，重启特殊现场不足明确拒绝，不承诺补齐所有现场或降为普通agent |
| S-10 | SOURCE-CANDIDATE / SCOPE-DELTA | 系统定时process.execPath在Node安装与独立二进制含义不同 | 静态；W3/D2移出Windows系统定时及独立程序；标准Python包runner同版本内部角色仍须可运行，来源记录保留 |
| S-11 | SOURCE-GAP / SCOPE-DELTA | 原生Windows定时/系统凭据/唤醒锁/图片clipboard缺口；OS沙箱仅macOS/Linux | WIN-05系统凭据/WIN-08图片clipboard保留；W3/W5移出Windows系统定时/防休眠补齐并准确说明；WIN-09沿ADR-0008，缺口不写为已修复 |
| S-12 | SOURCE-CANDIDATE | Unix IPC/负PID取消/POSIX持久文件及通知PowerShell转义风险 | 静态；WIN-01..04/10；已有Python局部探针不等于原版Windows实测失败 |
| E-01 | EXPERIMENT-LIMIT | 运行时probe的SQLite3.45.1处官方WAL-reset受影响范围 | 仅早期实验环境已读回；D19已用固定3.54.1完成局部验证，REC-15产品仍待实现；未证明DAO实际库受影响 |
| E-02 | MATERIAL-GAP | Sixel原始PNG/manifest、部分replay外部路径不在快照 | PKG-05/TEST-01/03；嵌入帧存在，重生成/原图授权未核实；不得当移植regression |


### 后续缺陷记录模板

| ID/归类 | 案例 | source实际结果/证据 | port实际结果/证据 | 期望来源 | 处理/决定/任务 | 复测证据 |
| --- | --- | --- | --- | --- | --- | --- |
| P-01 / PORT-REGRESSION（开发驱动，已修复） | TEST-07.03.cleanup | 独立工程契约要求真实退出观察，非来源功能故障 | 旧驱动communicate抛OSError后child仍活却写joined=true；取消实际exit丢失 | D21/TEST-07与03票的失败取消边界 | 修复90efe4f；保留首次独立失败25c56bc | [独立初轮及修复复核](integration-evidence/03-boot/README.md)、[实现修复轮](evidence/03-boot/r2/README.md) |

## 前置实验与产品证据隔离

[运行时实验报告](../ruocun-discovery/experiments/runtime/README.md) 的25/25是预设观察（含反例），仅支持取消、进程接管和事务故障的局部可行性。它不覆盖真实provider取消、完整agent恢复、Windows Terminal/IME/resize、ACL隔离、断电或最终打包程序。除单独列明的工程子路径证据外，未实现的业务列保持未开始/未验。新实验和路线前置票见 [地图](../ruocun-discovery/map.md)，不在本表替换产品证据。

## 关闭矩阵的条件

本轮保留母行及必要子案例具备实际实现、来源处理决定、可复跑自动证据和Windows结果；范围移出按ADR-0010单列，绝不当通过。HITL项目由用户accepted，保留缺口/修复及真实技术前置闭合；Linux/macOS实机可pending。最终只宣布选定范围完成，标准包/手工更新、完整文档/CI仍须满足门禁；不再宣称原84票全部完成、成套live成绩或量化性能达标。

## 已完成的工程子案例

- TEST-01.02 / TEST-02.02 / TEST-05.02：来源CLI对照驱动已接收（f99ae1ef，merge eefab839），12项驱动测试与190项相关来源断言通过；来源Node24退出失败保留为ENV。这里不表示Python产品、整套215来源测试或真实模型/终端验收通过。

- ENT-01.03.version/help/resource/unimplemented：已安装产品的版本单源、帮助/包资源、仓库外中文空格路径和未实现路径非零通过；不代表普通Agent启动已实现。详见[03实现](evidence/03-boot/README.md)及[独立复核](integration-evidence/03-boot/README.md)。
- TEST-07.03.toolchain/offline/negative/cleanup：五入口及18包hash闭包已实跑；修复后默认pytest29通过/3来源CLI取消选择，offline4通过，Ruff/mypy11文件/build/pipcheck通过；真实owned-child OSError/取消/观察失败/清理阶段中断4项修复回归及独立wheel-only故障脚本通过。其它六suite非零not-run；原独立来源12输入未变，修复轮未重跑。详见[独立修复轮](integration-evidence/03-boot/r2/README.md)。

## 已确认的执行语义差异

| ID | 来源行为 | RuoCun目标 | 决定与产品证据 |
| --- | --- | --- | --- |
| D-01 / INTENTIONAL-DELTA | MCP效果已写后断线，来源自动重放实测effect:2 | 结果不明停止自动重放并持久未决；连接/能力发现可重连 | 用户2026-11-05确认，[ADR-0003](../../docs/adr/0003-mcp-unknown-outcome-no-replay.md)；[D15协议证据](../ruocun-discovery/experiments/extensions/README.md)已验；产品EXT-10三传输副作用断线/重开已独审，见[54最终独审](../ruocun-next24h/evidence/review/b05-mcp-recovery-review.md) |
| D-02 / INTENTIONAL-DELTA | 冻结来源仅version早退，不提供相同的本地--help/-h入口 | 03提供符合ENT-01/R-15/D21的离线本地帮助，保留版本早退优先级 | 已确认工程规格的实现选择；[03证据](evidence/03-boot/README.md)，不是声称来源已有此行为 |

## 前置体验与最终人工验收

按[ADR-0004](../../docs/adr/0004-final-batch-human-acceptance.md)，人工体验统一到77/78/85。D06第一组IME/emoji、流式排队与草稿、缩放与历史选择，用户回复“正常”；该记录归原型指定子项。最终实机结果在下文汇总。

最终 b09-r4 的 19 个自动子案例和人工体验分别留证。77、78 已结题，85 汇总通过。最终实机覆盖当前 Windows 账户，其他本地账户安全负例、macOS 实机、完整 POSIX 安装运行和托管 CI 继续待验。[最终实机与交付](../ruocun-next24h/batch-final.md#最终验收与交付)

## PKG-07性能观察与历史量化门槛

V2已按[ADR-0010](../../docs/adr/0010-selected-scope-and-lean-workflow.md)移出ADR-0006原耗时≤1.20、进程树峰值内存≤1.30及正式采样门禁。四子ID保留为来源/历史与有限观测位置，不新增案例族；观察未执行仍未验，不能写成量化达标。保留修复明显卡顿、失控内存与取消故障，真实终端体验仍归77。

| 子ID | 场景 | 实现/证据资产 | 自动结果 | Windows结果 | HITL |
| --- | --- | --- | --- | --- | --- |
| PKG-07.perf-startup | 启动有限本机观测，条件据实记录 | 正式采样移出；有限观测待执行 | 未验；无量化达标声明 | 未验 | not-required |
| PKG-07.perf-dispatch | 本地模型流与工具调度有限观测 | 正式采样移出；有限观测待执行 | 未验；无量化达标声明 | 未验 | not-required |
| PKG-07.perf-store | 消息/工具结果提交与恢复有限观测 | 正式采样移出；有限观测待执行 | 未验；无量化达标声明 | 未验 | not-required |
| PKG-07.perf-terminal | 历史/流式处理有限观测 | 正式采样移出；有限观测待执行 | 未验；无量化达标声明 | 未验 | not-required（77 实机体验已验） |

## Session／费用基础子案例（28局部）

| 子ID | 实际范围 | 实现/自动结果 | 未完成范围 |
| --- | --- | --- | --- |
| WIRE-06.28.session-memory | 系统/用户消息、模型/模式、用量累计、缓存骤降监听/归因、清空及摘要 | 冻结session.test.ts的10项语义迁移，独立通过 | 保留的恢复状态、commands/loop接线及缓存审计仍未完成；R1历史费用补齐移出 |
| WIRE-06.28.cost-memory | 分桶估算基础、命中/未命中/输出计价、20条冻结价格、模型名归一/回退与格式 | 冻结cost.test.ts的9项语义迁移，独立通过；分桶求和另为源码审查 | R1历史分模型费用连续范围移出；新费用统计/命令及预算口径接线待做，不声称当前厂商报价 |

证据：[实现](evidence/28-context/session-cost/README.md)、[独立复核](integration-evidence/session-cost/README.md)。只运行上述19项来源测试及必要静态/构建安装检查，没有扩测。28保持claimed，REC-07、WIRE-11、CMD-cost/effort/context-window/status未由本切片标为通过；ADR-0010修改的是范围与门禁，不增加性能、真实模型或人工体验通过结果。

## 2026-11-10确认的范围差异

下表只记录要求变化；各保留路径仍待对应任务实际实现和复核。唯一决定为[ADR-0010](../../docs/adr/0010-selected-scope-and-lean-workflow.md)。

| 选项 | 本轮要求 | 不再承诺/范围移出 | 责任与证据状态 |
| --- | --- | --- | --- |
| R1 | 消息/model/mode/title及四累计token恢复，本进程费用累计，重启明确新费用统计/预算口径 | 跨重启历史分模型费用完整连续 | 28局部基础已验；剩余接线未验 |
| R3 | 当前fork/exactTools、普通代理恢复；特殊现场不足明确拒绝 | 为每种特殊fork补齐重启现场并继续 | 41未验；不得降为普通agent |
| W3 | Windows系统定时准确不支持；会话loop独立 | Task Scheduler/Windows dispatcher及关闭会话后的定时触发 | 59的Windows拒绝与POSIX合成路由技术通过 |
| W5 | Windows准确说明无自动防休眠保证；正常取消/退出 | Windows唤醒锁补齐与系统锁生命周期保证 | 62的Windows提示和每轮释放技术通过 |
| W6 | 终端内提示与安全标题；NotifyUser准确呈现去向 | 桌面通知发送与窗口端口 | 63路径未验；不能声称已发系统通知 |
| D2 | 标准Python wheel/sdist可安装，资源/SQLite/runner真实运行 | Windows独立程序及其冻结角色生命周期 | 80范围移出；79与84的标准包技术门禁通过 |
| D3 | 手工停进程、一致备份、安装更新/手工恢复，保护旧数据 | 自动跨版本原地迁移与失败自动回退 | 81仓外手动更新、备份与数据保护已通过 |
| V1 | 保留任务/fixture/72–74评估工程及76离线runtime/protocol证据 | 成套16×3真实模型成绩/评分门禁 | 72–74和76技术证据已通过；75范围移出，成套真实模型未运行 |
| V2 | 有限观测并修明显卡顿/失控内存/取消故障 | 1.20/1.30量化保证及正式采样门禁 | 未测仍未验，不声明量化达标 |

<a id="批次08自动技术出口"></a>

## 当前自动技术出口

最终批次固定候选 b09-r4 的自动出口。按实际终端改动定向复跑并逐项引用未受影响的原案例，人工条件按票记录。

| Automatic ticket | Case/subcase | Result | Product commit | Evidence | SHA-256 | Review |
| --- | --- | --- | --- | --- | --- | --- |
| .scratch/ruocun/issues/77-wtaccept.md | WT-01.unicode-edit | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/wt-01.unicode-edit.json | fd0c74234b87e28921a15fb6aebe33420288a37210ff7bfb2c18348f85460b59 | .scratch/ruocun/evidence/b09-r4-automatic/77-wtaccept-review.json |
| .scratch/ruocun/issues/77-wtaccept.md | WT-02.paste-fold-and-image | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/wt-02.paste-fold-and-image.json | 09f0b7310e54c21e092555f999cb8327339d8a56461f7563517f6addad8273ee | .scratch/ruocun/evidence/b09-r4-automatic/77-wtaccept-review.json |
| .scratch/ruocun/issues/77-wtaccept.md | WT-03.owner-and-queue | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/wt-03.owner-and-queue.json | 5e927ed8de4cd502f1f8db26f66aa7812dddf3c481d237948a9b490d7d2a3151 | .scratch/ruocun/evidence/b09-r4-automatic/77-wtaccept-review.json |
| .scratch/ruocun/issues/77-wtaccept.md | WT-04.interrupt-and-handoff | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/wt-04.interrupt-and-handoff.json | f8748da46838cef88b1e6dc2f45fb6f4764482bba5fef0a178b75f048f473abe | .scratch/ruocun/evidence/b09-r4-automatic/77-wtaccept-review.json |
| .scratch/ruocun/issues/77-wtaccept.md | WT-05.owned-repaint | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/wt-05.owned-repaint.json | 4a27e6ccd7e3ef0cd851757252145857400591c2ef07db1a36708eca3051eb28 | .scratch/ruocun/evidence/b09-r4-automatic/77-wtaccept-review.json |
| .scratch/ruocun/issues/77-wtaccept.md | WT-06.modal-and-panels | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/wt-06.modal-and-panels.json | 39411320271986a8df8162cdb98bc44ba149d31c07a304233b247667e8e80b48 | .scratch/ruocun/evidence/b09-r4-automatic/77-wtaccept-review.json |
| .scratch/ruocun/issues/77-wtaccept.md | WT-07.terminal-attention | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/wt-07.terminal-attention.json | fc319143b9ed84f0515d1281da6351cc7b748d6dbeee71ec0a451442cf06821a | .scratch/ruocun/evidence/b09-r4-automatic/77-wtaccept-review.json |
| .scratch/ruocun/issues/77-wtaccept.md | WT-08.graphics-owner-and-fallback | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/wt-08.graphics-owner-and-fallback.json | 3c2e9d6412424fbe1a5dd5258147627e4815865b6b22402b24283027770889fb | .scratch/ruocun/evidence/b09-r4-automatic/77-wtaccept-review.json |
| .scratch/ruocun/issues/77-wtaccept.md | WT-09.pipe-and-mode-lifecycle | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/wt-09.pipe-and-mode-lifecycle.json | ac3733e48ff033d12600d0be3a1f496ca50ebe8fb551affed2168fcb20a159af | .scratch/ruocun/evidence/b09-r4-automatic/77-wtaccept-review.json |
| .scratch/ruocun/issues/78-wincaps.md | WIN-01.native-shell | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/win-01.native-shell.json | a6c16c23763bb8a5ae43f678b22fdaea3c9d7de3b8b5d05d3c45653579ccc82e | .scratch/ruocun/evidence/b09-r4-automatic/78-wincaps-review.json |
| .scratch/ruocun/issues/78-wincaps.md | WIN-02.managed-processes | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/win-02.managed-processes.json | d09a92a6c745bce139a146fb78059ed7c0fc259fc063e4261d842cd2c8c631c2 | .scratch/ruocun/evidence/b09-r4-automatic/78-wincaps-review.json |
| .scratch/ruocun/issues/78-wincaps.md | WIN-03.named-pipe-and-acl | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/win-03.named-pipe-and-acl.json | cf611f7d86be64f8e41e4f1a6a4e4036c55a9cc4b62a7312b53f35e59074545e | .scratch/ruocun/evidence/b09-r4-automatic/78-wincaps-review.json |
| .scratch/ruocun/issues/78-wincaps.md | WIN-04.files-and-sqlite | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/win-04.files-and-sqlite.json | 02fc13f830aa9fd730665dc0767a346ba50856ac87825ad7b7a5a80e6c30e39f | .scratch/ruocun/evidence/b09-r4-automatic/78-wincaps-review.json |
| .scratch/ruocun/issues/78-wincaps.md | WIN-05.credential-manager | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/win-05.credential-manager.json | a008e1fcbfad4dcaaa8ab60fb3d624bf7623920b7207437e02d67b47139a79bf | .scratch/ruocun/evidence/b09-r4-automatic/78-wincaps-review.json |
| .scratch/ruocun/issues/78-wincaps.md | WIN-06.schedule-boundary | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/win-06.schedule-boundary.json | d31dde22d07b8c130fc8e063622dd379e4ae43db24e8fd2f2d61977681d2b482 | .scratch/ruocun/evidence/b09-r4-automatic/78-wincaps-review.json |
| .scratch/ruocun/issues/78-wincaps.md | WIN-07.power-boundary | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/win-07.power-boundary.json | 8a13f910e359871a69a1618af350bac2864aa98417c6cff9b117fb01a763dce3 | .scratch/ruocun/evidence/b09-r4-automatic/78-wincaps-review.json |
| .scratch/ruocun/issues/78-wincaps.md | WIN-08.clipboard-acceptance | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/win-08.clipboard-acceptance.json | 91c35925ea68f0adb4ae3c2b56d746323ade23c448ca38dce6c618bffe625425 | .scratch/ruocun/evidence/b09-r4-automatic/78-wincaps-review.json |
| .scratch/ruocun/issues/78-wincaps.md | WIN-09.sandbox-boundary | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/win-09.sandbox-boundary.json | 575b4550327aa2181342eb11fccad0e17a8fa875611b65a82e21659d74645420 | .scratch/ruocun/evidence/b09-r4-automatic/78-wincaps-review.json |
| .scratch/ruocun/issues/78-wincaps.md | WIN-10.terminal-channel | passed | 2d57674be8ea4715de26ba04939d74e1a8bc2cdf | .scratch/ruocun/evidence/b09-r4-automatic/win-10.terminal-channel.json | 8ac2ec36fcef22beeef14cc9aecdc053ffefafb6bab4003b0dd0a35914f82746 | .scratch/ruocun/evidence/b09-r4-automatic/78-wincaps-review.json |
