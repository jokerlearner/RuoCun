# 测试、回放与评估复用门禁研究

日期：2026-11-05。任务：[确定测试、回放与评估的复用门禁](../issues/11-test-replay-decision.md)。研究分支：`research/d11-test-gates`；起点：`84258fc06ab62a784bbf4c164328bac09dde2996`。本票为本地只读研究；不实现产品，不修改公共 tracker/矩阵，不推远程、不建 PR、不合并。

## 结论与证据范围

采用已确认的 pytest、统一验收驱动七个子套件、Ruff、mypy、build 五项入口，无需重新选择。以**独立预期、输入材料、真实边界结果**迁移测试意图；保留可复用数据与协议，语义重写 TS/平台绑定，真实模型质量单列。固定 52 个 slash、49 个菜单项、非 TTY 11 个名字和动态集合分别建立 oracle，不能合成一个“命令都支持”的断言。门禁按离线、真实协议、真实进程/存储、Windows 本机、可见终端、live、干净安装分层，但最终全量范围不缩减。依据：[规格 T-01～T-06](../../ruocun/spec.md#测试决定testing-decisions)、[ADR-0003](../../../docs/adr/0003-mcp-unknown-outcome-no-replay.md)、[ADR-0004](../../../docs/adr/0004-final-batch-human-acceptance.md)。

本次交付：

- [机器可读复用清单](11-test-replay-gates.assets.json)：215 test、58 script、16 task、85 fixture，共 374 条；每条有 D/R/S/P 处置、入口、依赖、拥有任务、来源 hash/行锚点、既有 MM 稳定锚点及拟目标。不是另建一套产品状态表。
- [只读重建器](11-test-replay-gates-build.py)：从冻结 ZIP、manifest、既有 module-map/task-coverage 重建清单，不启动子进程或网络；跨模块测试的责任归属显式展开，不更改原表。
- [静态校验结果](11-test-replay-gates.validation.json)：验证 805 成员集合/原字节、374 项无漏项、拥有任务均存在、52/49/11 集合数量、38 个专题脚本均含真实模型调用入口。本结果仅证明目录完整性，不证明产品或来源测试通过。
- 本目录[换行规则](.gitattributes)只固定本票前缀文件为LF，避免Windows检出换行改写报告/派生清单的hash；其它研究文件不受影响。

唯一来源为 [dao-f17e189-7ac654a0dc06](../reference/README.md)：提交 `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`，tree SHA-256 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`。本票直接读取归档原字节；下文 `src/...:行号`、`scripts/...:行号`、`evals/...:行号` 均指这个 ZIP 的内部成员。没有读取活动 DAO、真实凭据或真实用户配置，没有运行来源测试、真实模型、产品、系统设置探针或 Windows Terminal 验收。

## 已有证据如何复用

| 证据 | 已证实 | 不能外推 |
| --- | --- | --- |
| [实现02 Source-Oracle](../../ruocun/evidence/02-oracle/README.md)及[驱动说明](../../../tests/support/oracle/README.md) | Node 22.23.4 的 plan/read、首批无 TodoWrite 拒绝后继续、deadline 清理；12 个 Python 驱动测试；直接相关 6 个来源文件合计 190 断言通过 | 不是全量 215 文件通过；没有 port 产品、真实模型或真实终端结果。`ORACLE_COMPLETE` 只是 fake assistant 的脚本结束哨兵，不是质量答案 |
| 同一 Source-Oracle 的 Node24 对照 | 相同来源 tree/lock/构建路径的业务回合完成，但 native 退出 `3221226505` / `UV_HANDLE_CLOSING`；独立差分记为 ENV | 不能升级为源码已证实缺陷或 Python 回归；没有定位 libuv 内部根因；不能删掉失败 raw 后只留成功记录 |
| [D15扩展协议探针](../experiments/extensions/README.md) | 锁定候选 MCP 1.30.0 和来源 TS SDK 1.29.0 下，11 项代表性真实协议/解析探针；stdio/HTTP/SSE 副作用后断线；Hook 晚副作用；LSP 分帧与 UTF-16/URI 代表样本 | 不是完整标准一致性、产品 manager、所有第三方扩展或所有平台通过。源码公共 loader 被实跑不等于对应全部来源测试通过 |
| [D06终端技术复核](../issues/06-python-terminal-prototype.md)、[ADR-0004](../../../docs/adr/0004-final-batch-human-acceptance.md) | 有可运行原型、自动/进程证据；用户对指定 IME/emoji、流式队列/草稿、缩放/历史选择回复“正常” | 不是最终产品/安装产物 WT 通过；粘贴、前后台、焦点图形、退出恢复等未验项仍待最终用户操作 |
| [研究02](02-function-runtime.md)、[研究03](03-data-extension.md)、[研究04](04-terminal-platform-delivery.md) | 冻结调用链、格式与测试资产的静态事实 | 静态分支/测试名称不代表功能已运行或当前来源可离线启动 |

本票不扩张为重跑全套来源或新的大型性能实验；已具备足够证据确定门禁。产品实现须通过自身入口复验，不把最小探针分数继承到产品列。

## 资产处置与拥有任务

D=直接复用数据，R=高层 CLI/协议回放适配，S=语义重写，P=保留评估协议。可组合而非互斥：例如 task 的题目/工作区是 D，runner 是 R/S，真实模型判定是 P。完整路径已有[逐文件对应表](../../ruocun/module-map.md)和[研究04附录](04-terminal-platform-delivery.md)；本报告不再抄写 374 行 Markdown。清单中的 `entries` 是**拟迁移语义所属门禁**，不是承诺该来源文件当前可安全执行；UI 项的 terminal 表示产品后续体验，不要求每条 width 纯函数测试都人工操作。拥有任务来自[责任覆盖表](../../ruocun/task-coverage.json)及现有任务职责；只表示计划责任。

| 类别/数量 | 处置及入口 | 条件、拥有任务与来源锚点 |
| --- | --- | --- |
| 215 test：203 src + 12 evals | S 重写断言，D/R 保留合成输入/事件/响应；pytest 主入口，按实际路径补 offline/protocol/runtime/terminal | 语言绑定 mock/私有 widget 树不当产品契约。各条关联对应功能任务；CI 总收口由[跨平台质量门禁](../../ruocun/issues/82-crossci.md)和[全量交付核对](../../ruocun/issues/85-delivery.md)负责。`vitest.config.ts:3–8`、`tests/setup.ts:1–4`；逐条源文件/MM 锚点见 JSON |
| 5 确定性脚本 | R/S/D；oracle/runtime（纯记忆部分可 offline） | `verify-memory.ts`→记忆任务；persistence→存储/恢复；background wait/recovery→runner/等待/恢复；recovery-entrypoints→自身保存恢复/路由。`scripts/verify-persistence-runtime.ts:5–25`、`verify-background-wait.mjs:1–57`。POSIX FIFO、TS prototype 与旧 DAO 导入不能直接复用为 Python 核心要求 |
| 2 live 后台/恢复脚本 | P/R/S；live + runtime 对应路径 | [真实模型运行时组合](../../ruocun/issues/76-liveruntime.md)会同等待/恢复任务；必须显式模型/账户/预算，不能读取 active profile 作为默认。`scripts/verify-background-wait-live.mjs:29–39,68–87` |
| 38 模型专题脚本 | P 主处置；D/R 提取合法输入、S 改编排；live | [评估轨迹](../../ruocun/issues/72-evalrunner.md)、[16来源真实任务](../../ruocun/issues/75-livebase.md)、[运行时组合](../../ruocun/issues/76-liveruntime.md)负责；先收齐轨迹/system prompt/候选，再审答案暴露。清单逐文件静态确认 `streamChat`；不是确定性 replay |
| 4 memory/cache/reflect 脚本 | P/S/D；live；纯评分另走 offline | [记忆/缓存评估](../../ruocun/issues/73-memoryeval.md)、[反思评估](../../ruocun/issues/74-reflecteval.md)及对应记忆维护/费用任务。`scripts/accept-memory.sh:1–22`、`accept-cache.sh:1–24`；后者稳态≥90%是原脚本目标，不是所有 provider 的保证 |
| 1 harness wire 诊断 | R/S/D；offline | 观测/评估轨迹任务；合成输入和请求/schema 可以回放，真实用户 raw 需脱敏。`scripts/dump-harness-wire.ts:1` |
| 3 预览 + 3 VHS 演示 | 预览 S/D/R→terminal；VHS 增加 P→显式 live | 终端渲染/欢迎/最终 WT，反思演示再归记忆/反思评估；`scripts/preview-welcome.ts:1–34`、`welcome-ink.tsx:20–57`、`demo.tape:16–31`、`demo-reflect.tape:14–57`。VHS 会调用模型且有 POSIX 清理，不原样执行；可用合成 trace 复用视觉意图，但不能继承真实模型效果 |
| mascot 生成1 + 版本同步1 | mascot D/S→offline/terminal/install；版本 S→install | 欢迎资源、标准包/独立产物、发布任务；嵌入帧可用，原始 PNG/manifest 未收齐。版本改用 Python metadata 单源。`scripts/generate-mascot-data.mjs:9–38`、`sync-version.mjs:1` |
| 16 task：10 oss + 4 double + 2 local | D/R/P/S；offline 只检格式/评分/verifier有效性，live 才是模型任务 | 评估轨迹与16来源真实任务负责。保留题目原语言及外部 verifier；不因核心 Python 把 TS 题改成 Python。`evals/run.mjs:146–157,179–232,276–309`；16行 JSON 均有 hash/类型/受保护字段，无复述题解 |
| 85 fixture：memory71 + reflect12 + MCP1 + LSP1 | memory/reflect D/R/P，解析/评分 offline、模型 live；MCP D/R/S 与 LSP D/R→protocol | 记忆/反思评估、MCP stdio/HTTP/能力/恢复、LSP 任务。`evals/memory/README.md:34–56`、`evals/reflect/README.md:7–43`、`src/mcp/__fixtures__/fake-mcp-server.mjs:1–17`、`src/lsp/testfixtures/sample.ts:1–19`。外部 Node fixture 可继续验证非 Python 扩展，不使产品核心依赖 Node |

215 文件不等于 215 test case；独立 fixture 也不含每个测试体内临时创建的输入。迁移时逐断言登记正例、反例、失败/取消与最终副作用，保留测试体内生成的数据。清单分组是静态主入口安排，不能代替实现时对网络/进程副作用的审计。

## 分层门禁与稳定回归集

下列入口均已获确认，完整 Python 工程配置仍待相应实现任务落地；本报告没有创建这些产品命令。pytest 的默认选择必须排除显式 live/人工/安装案例，受控 loopback 与真实本机进程可进入各自自动集。对无法观测原子性/竞态的情况才使用有限状态/故障切点，不增加产品调试 API。依据：[规格 T-02～T-04](../../ruocun/spec.md#t-02--沿用的测试入口与资产)、[已确认入口](../../ruocun/issues/01-test-entrypoints.md)。

| 门禁/入口 | 必须结果及可用 seam | 放行与证据限度 |
| --- | --- | --- |
| `python -m pytest` + `ruocun_acceptance offline` | 提示/工具 schema/可见性、消息/usage转换、配置缺失/null/空串/未知字段、发现覆盖、命令参数、权限与纯评分；fake 时钟/随机值。断言由独立源码/既有测试/ADR先给出 | 所有已迁移稳定离线用例无未解释失败；不能靠快照更新接纳 port 输出。fake 模型文本仅驱动控制流，不计质量成功 |
| `ruocun_acceptance oracle` | 独立可写来源副本+自有 Git fixture；真实 CLI argv、stdin、HTTP/SSE 请求/schema、工具结果和退出；同材料/语言/时钟条件比较 port | 优先复用实现02；Node22成功与Node24 ENV分列。源码不可启动先归ENV；只有source/port有效才判回归。来源固定tree/lock，不能引用活动DAO新版本 |
| `ruocun_acceptance protocol` | 实际 loopback监听或独立helper：HTTP/SSE/Responses碎片与结束、Hook stdin/env/cwd/code/超时、MCP三传输、LSP Content-Length/关联/UTF-16/Windows URI、Deck认证/消息 | 无真实provider或第三方服务依赖。解析/协议子集逐条expected；服务自证同SDK不足，保留wire与独立server。D15未验范围逐case补齐，而非整体打勾 |
| `ruocun_acceptance runtime` | 实际文件/SQLite/进程树/IPC：工具意图与结果提交边界、owner/epoch、重复恢复、runner接管、等待inbox、旧/迟到事件、EOF/退出保留后台、cancel→force→确认止写 | fake transport可以驱动真实工具/进程；不能只mock abort/kill，不能拿25项技术probe当产品通过。时钟故障尽量用事件屏障；真实超时保留界限与单调耗时 |
| `ruocun_acceptance terminal` | 实际Python/安装产物在可见WT；自动收业务输入hash、转录/状态与截图，用户最终操作IME/缩放等 | 无头/PTY只证明状态或字节；按ADR4把人工留到最终77/78/85。不得代填accepted或因为等待人工而停掉已授权编码/自动化 |
| `ruocun_acceptance live` | 显式账户/provider/模型/endpoint/参数与费用上限；16任务、运行时/工具/扩展/记忆组合；任务结果由独立verifier判定 | 本轮0调用。缺预算/模型/材料记明确未运行原因；不降级成假答案或已通过。模型结束、历史分数和LLM自评均不代替结果 |
| `python -m build` + `ruocun_acceptance install` | wheel/sdist及最终独立形态，在仓库外/新venv或普通用户VM运行；关PYTHONPATH、移走源码后版本/资源/SQLite/扩展/self-spawn runner/升级恢复/卸载与数据保留 | 构建成功不等于可安装；源码目录启动不等于独立安装。Windows独立产物具体命令与锁由发布路线决定；每个发行架构独立记录 |
| Ruff / mypy / 构建CI | 已确认的 `python -m ruff check .`、`python -m mypy`、`python -m build`，核心及明确类型支撑范围 | 质量门禁不能为类型方便缩窄外部格式接纳，也不替代功能/平台/体验 |

稳定集从现有实现02六文件的请求/Read/TodoWrite/plan/首批屏障和deadline开始，逐功能纳入已移植离线断言；同时加入规格现有恢复、未决副作用、权限拒绝/Hook改写、动态隔离、命令路由、Unicode/CRLF边界的负例。日常修改跑受影响功能集及其调用链，集成/发行跑完整稳定离线、protocol、runtime与Windows自动集；live和人工仍独立。禁止把“稳定集”解释为永远只验这六个文件，或用固定通过率容忍核心遗漏。[规格 T-04/完成标准](../../ruocun/spec.md#t-04--自动化测试层次与最小覆盖)、[完整验收矩阵](../../ruocun/acceptance-matrix.md)。

### CLI、TTY、非TTY、argv的独立oracle

| 集合/路由 | 冻结事实 | 门禁输入及预期 |
| --- | --- | --- |
| 操作员CLI | `rawArgs`未先统一小写；识别`trust`、`plugin`、大写`Schedule`、`Skill add`，help却写小写。`src/index.ts:197–275` | 大/小写、缺值、重复flag、冲突顺序、未知token各跑独立case；只在受控配置/本地fake模型中试，不让小写落入prompt后接真实API。不执行真实系统定时/安装；预期先保留SOURCE-CANDIDATE，不能静态“修好别名”后当等价 |
| 固定slash52 | index分支、基础dispatch、builtin6、App内theme/loop的名字并集；保留`/Config`大小写。`src/index.ts:1917–2504`、`src/commands/commands.ts:19–83`、`src/commands/builtin.ts:11–98`、`src/tui/app/App.tsx:497–573` | JSON的`routes.fixed_slash`给完整52名单；每名按现有CMD案例所属任务验证查询、参数、错误、暂停/settled、状态/文件/后续请求。别名要同场景，不以help出现替代执行 |
| 菜单49 | `COMMAND_META`49项；security-review/debug-session/dod不在固定handler/builtin/core名单。`App.tsx:37–44` | 菜单展示/补全与命令执行分离；先禁所有外部扩展，再证实3项行为；另造动态同名定义验证可由扩展提供。菜单不创造handler，动态成功不证明固定内置成功 |
| 非TTY/Deck11 | 基础9：model/plan/clear/compact/cost/lang/help/exit/quit，加recovery/resume特接。`src/repl.ts:82–105`、`src/index.ts:2622–2671` | 管道stdin/EOF、换行/CRLF、首尾空白、未知slash、/Config与TTY-only项分别观测；Deck关闭不应自动等同EOF。help文案可能列更多名字，不由文案扩大路由 |
| argv一次性 | `argvPrompt`直接进入scheduler，不经过完整slash派发。`src/index.ts:1704–1755` | 将`/help`等作为argv与stdin/TTY分别跑；记录模型实际收到的prompt/工具与keepAlive行为；不能因统一驱动而把三种入口统一语义 |
| 动态命令/Skills | 用户/项目/插件及文件访问发现可改变名单；core8与固定slash重合simplify，额外7不计固定52。技能匹配不区分大小写，固定命令保留。`src/skills/skills.ts:70–76,124–136`、`src/index.ts:767–786,1160–1180,2446–2471` | 合成发现根、同名/命名空间/realpath/paths触发与开启关闭矩阵；冻结每case的动态清单、覆盖顺序、最终展开prompt。eval/no-skills/no-project-instructions/未信任与恢复分别测；不继承机器上已有skills |

对大小写冲突、/permissions编辑不可达及3菜单项的**实际受控运行**仍由[完整路由实现](../../ruocun/issues/70-routes.md)和对应oracle展开；本研究没运行这些路径，不伪报复现。实现02只跑了明确的headless工具链，不替代这些case。

### D15协议门禁的实际边界

三种MCP传输均要重测工具/资源/提示、显式header/env、listChanged后产品registry重建、elicitation回调与关闭；一次性connect无handler的`-32601`和主UI默认decline不是同一oracle。SDK默认env会丢sentinel，兼容目标的继承策略须由manager显式构造，不能用SDK默认allowlist替代来源外部契约；**测试运行器**仍必须只传本次合成allowlist，不能继承真实父环境。来源继承语义用完全合成父环境验证。[D15报告](../experiments/extensions/README.md)。

ADR-0003最小必过序列：服务端先写effect=1→断线无结果→产品呈现并持久化未决→关闭/重启→重连/发现能力仍effect=1→模型换tool_call_id仍不绕过未决→用户明确恢复决定后才允许再次执行并留决定记录。另测确定未发出、明确错误、明确结果三类；未知不能猜readOnlyHint或模型建议安全。**来源effect=2是反例，port在未授权前effect=1才是正确目标**；HTTP resumption、幂等服务端结果恢复未经验证，不能作为自动重放豁免。[ADR-0003](../../../docs/adr/0003-mcp-unknown-outcome-no-replay.md)、[MCP恢复实现](../../ruocun/issues/54-mcprecovery.md)。

Hook需在原超时返回后等过已知晚副作用窗口再查marker/进程，普通超时结果不足；补输出上限/完整matcher与事件/所有支持shell的产品路径。LSP需9操作、分片/合帧、恶意/额外header与大小上限、错误/迟到响应/服务器退出、同步/位置/URI和有界关闭；继续保留TS样本语言。其余HTTP GET持续事件、resumption/session失效、分页/订阅/roots/sampling、TLS/OAuth/代理等按产品声明逐项登记；D15未验不自动填支持，也不把标准上存在但来源未接线的能力擅自新增为兼容承诺。[D15未验证清单](../experiments/extensions/README.md#未验证与后续门禁)、[完整扩展规格](../../ruocun/spec.md#r-12--配置和产品扩展兼容)。

## Windows必验与跨平台后续矩阵

| 平台/层 | 必验覆盖 | 证据与责任 |
| --- | --- | --- |
| Windows x64 开发核心 | 所有工具/命令/配置/扩展的完整功能，真实cmd/PowerShell方言、UTF-8/中文空格路径、外部`.cmd/.bat`启动，允许/拒绝与错误 | 各功能任务+CI82；不能在Linux把Windows-only skip后声称完成。`src/session/process_identity.test.ts:7–56`已有Windows-only意图；来源CI只有Ubuntu Node20/22，不能继承为Windows证据 |
| Windows真实资源 | PID+creation time/三层进程与止写、runner接管、认证IPC/ACL/epoch、持久文件/SQLite、凭据假秘密写取删、系统定时真实触发与清理、power、文本/图片clipboard、通知字面载荷、OS文件与网络隔离 | [Windows能力最终组合](../../ruocun/issues/78-wincaps.md)及对应能力任务；测试仅操作本次拥有资源，密钥只记hash/状态。Job/认证IPC/WSL不证明OS文件/网络隔离；probe只覆盖实际检查的范围 |
| Windows可见终端 | WT-01..09：输入/粘贴/图片、流式并行编辑、审批/选择/任务面板、Esc/Ctrl+C/后台、滚动复制、IME/emoji、连续缩放、焦点标题/图形降级、退出恢复 | [最终WT验收](../../ruocun/issues/77-wtaccept.md)；按ADR4集中用户体验。记录Terminal/OS/Python/backend/Shell/IME/字体DPI/geometry/截图及业务hash；原型用户反馈只覆盖明确子项 |
| Windows安装形态 | 标准wheel/sdist、独立程序及self-spawn runner，普通用户、无源码/开发配置/Node/Bun、中文空格安装路径、升级/回退/卸载与自身数据恢复 | [标准包](../../ruocun/issues/79-wheel.md)、[独立产物](../../ruocun/issues/80-standalone.md)、[升级卸载](../../ruocun/issues/81-upgrade.md)、[Windows总门禁](../../ruocun/issues/84-winintegrate.md)；候选打包探针不是成品验收 |
| Linux/macOS | 各自质量/导入/构建、平台后端条件化；后续真实进程/扩展/终端/安装矩阵 | 按ADR1保留后续实机pending；Windows失败不能以Linux通过抵消，静态/交叉构建不能填实机通过 |

依据：[规格 R-13～R-15、T-06](../../ruocun/spec.md)、[Windows静态研究](16-windows-capabilities.md)、[研究04平台/CI事实](04-terminal-platform-delivery.md#4-windows已补齐明确空缺与静态风险)。本票没有新增系统任务、凭据、通知或沙箱设置。

## 评估、缺材料与答案隔离

保留来源16个实际task（包含README遗漏的06，90目录是模板不计task）。原runner默认RUNS=3，`EVAL_TIMEOUT_MS`默认180000；本快照16个task均没有单独timeout字段，因此逐case记录**实际有效timeout**，不虚称已有16个独立超时配置。保留double/oss双轨、L1五checkpoint的加权完成、local check和失败不计空验证器成功；模型语言/题目工作区/外部verifier不随核心迁移改写。score纯函数的退化样本、未知checkpoint、全过/全不过、阈值和p50/p80走S/D/R独立断言；质量统计仍为P。`evals/run.mjs:35–43,179–232,276–309`、`evals/score.mjs:5–70`。

每次先验证base确实因任务目标失败、通过fix/受控正控验证verifier有效，再对agent结果评分。命令不存在126/127、安装/网络/缺可选依赖、collection error、无Docker、任务base已过、材料缺失分别记录，不能混成模型失败或从分母静默丢弃。单测通过与CLI取消/崩溃并行保存：若任务结果通过但执行被中断，保留任务判定同时记录运行失败，不把它算整条产品运行通过。来源工具数由文本`→ `计数、耗时取`r.ms??0`而exec只返回code/out；这是静态度量局限，RuoCun应从事件和单调时钟真实采集，不复用零耗时或文本箭头作为事实。`evals/run.mjs:54–68,250–260,302–309`；本票未运行这些脚本，不将静态局限宣称已复现bug。

隔离最低要求：

1. agent只获得任务prompt/input与base工作区；gold、隐藏tests/check、fix_ref、validation_note、参考实现/solutions、历史成功diff/轨迹及judge提示存于scorer根，运行后再注入验证。清单只标受保护字段名，不复制题解。
2. OSS来源流程会fetch base和fix并把隐藏测试临时检入后撤掉；这证明隐藏**工作区文件**的意图，不能证明Git对象、refs、缓存或联网答案都隔离。复用时准备scorer副本验证base/fix，给agent一个不含fix对象/remote解题路径的base导出或独立受限仓库；原始base/fix hash在评估侧留证。不能让产品repo、研究归档或开发文档成为agent可读答案库。`evals/run.mjs:87–125,281–307`。
3. source/port对比使用相同可见材料、发现配置与工具权限；scorer拒绝拿port输出自动生成gold。所有题目都已作为本次开发材料存在，不能宣传为模型/维护者严格未见；新保留集也需记录谁、何时、用于何种迭代而非只用held_out标签。
4. memory gold由Claude起草、用户抽查校正；redact只覆盖已知key/homedir/nameMap，邮箱/电话/IP/真实姓名/他人路径需逐份通读。本票仅建立保留/待审计划，不宣称85个fixture均已完成隐私人审。gold只给评分器；`injection-ab`是judge模拟检索触发，不是真正memory_read多轮任务。`evals/memory/README.md:41–56`。
5. judge默认K=3多数票须保留每票有效性/原始输出和无效/空票，不能空票自动满分；extract/recall/reflect指标与真实使用任务分开。Terminal-Bench的held_out实际与其它题统一逐题迭代，历史70/89不作为RuoCun成绩或严格未见成绩。`evals/memory/README.md:31–32`、`evals/terminal-bench/README.md:118–136`、[研究04评估资产](04-terminal-platform-delivery.md#55-评估工具与外部运行环境)。

| 材料/环境依赖 | 状态与处置 | 拥有任务 |
| --- | --- | --- |
| 38专题脚本中的绝对轨迹/system prompt引用 | 清单逐脚本保存外部引用行锚点；如FEAL `scripts/introspect-feal-brute-force-full-space.ts:31–35`、QEMU安装Windows `verify-installwindows-candidate-replay.ts:16`、groundtruth peek `verify-model-extraction-groundtruth-peek-replay.ts:39`。引用不是快照成员，不推测运行时机器仍有该文件；未合法物化时记MATERIAL-GAP；抽取输入hash与暴露级别后再跑 | 评估轨迹/16真实任务/组合live |
| 模型专题答案/peek/oracle变体 | 诊断与反作弊实验可按其原协议保留，不能混入未见能力成绩；不让模型解释其历史动机当因果证据 | 评估协议及报告任务 |
| mascot原始PNG/manifest | 冻结嵌入帧/时序存在；生成脚本默认读仓库外`.codex-analysis/.../manifest.json`，原图/授权/可重生成尚缺。保留现成数据hash，重生成单列MATERIAL-GAP | 欢迎/包资源/发布 |
| OSS源码/工具链、Docker、Harbor/SWE/TB数据与镜像 | task.json存在不等于外部repo/依赖/数据已物化；锁repo/base/fix、toolchain、dataset revision、image digest和官方verifier。SWE v2需显式harness环境与Linux产物，Harbor已有Linux下载逻辑需改安装；README旧dao_code_agent.py不在快照，不伪造脚本 | 评估轨迹/真实任务/发布；非Windows原生能力替代 |
| accept-memory退出蒸馏期望 | 脚本17–22行预期退出蒸馏，当前`src/index.ts:2683`明确不再退出蒸馏；先固定热回合增量记忆的现行高层结果，脚本旧文案只作历史意图，不能把缺退出日志判为新port回归 | 记忆维护/记忆评估 |

本表和JSON只列静态已发现的引用，不能声称穷尽脚本运行后才能确定的外部文件、模型行为或授权。材料缺口不阻止门禁方案收口，但相应live/重生成case不能通过或静默跳过。

## 故障分类、证据结构与放行规则

| 类型 | 认定依据 | 本次适用 |
| --- | --- | --- |
| SOURCE-CANDIDATE | 静态不可达/文案冲突/疑似平台错配，尚无同输入受控运行 | S-01大小写、S-02permissions/菜单、S-03动态发现隔离、费用/恢复、Bash失败格式、fork/cwd等矩阵既有疑点仍保持静态；本票未执行不能批量升级 |
| SOURCE-DEFECT / 已复现来源反例 | 相同冻结源码、可控输入、实际副作用/输出与目标冲突，有原始wire/日志和环境 | D15证明MCP副作用后断线会再执行为2；Hook150ms超时返回后helper仍在2s后写marker。仅适用于已测fixture/Windows shell组合，不推为任意服务/所有进程树缺陷 |
| INTENTIONAL-DELTA | 用户已接受的不同目标，有ADR/规格与产品复测 | MCP按ADR3停止未知结果透明重放并持久未决；source=2/port=1必须明确标差异，不使差分驱动误报回归。D15候选LSP关闭/URI或env默认差异还不是自动Accepted决定 |
| ENV / MATERIAL-GAP | 运行时、依赖、权限、外部材料不满足；没有有效功能结果 | 实现02 Node24 native退出是ENV；缺轨迹/原图/容器/工具链另记材料原因。不删除坏raw，不算passed，不用宽泛“环境问题”掩盖port错误 |
| PORT-REGRESSION | 有效source契约/ADR预期与有效port实际不符 | 当前本票无产品运行，不能认定。后续双侧结果、前置有效性、最小复现与修复证据必须齐全 |
| UNVERIFIED | 未运行、单侧缺失、证据不足或无法归因 | 实现02 port未运行、D15未覆盖能力、终端剩余人工、所有本票产品项目。保留unknown，不猜成功或故障 |

统一case记录建议是验收驱动的**开发证据格式**，不是新增产品API：`case_id/spec_ids/asset_MM_ids/owner_task`、来源tree/产品commit/依赖锁/真实SQLite版本、输入与可见材料hash、argv/cwd/输入通道、独立expected及出处、source/port各自`pass|fail|canceled|not-run|unsupported|skip`与退出码、归因/差异ADR、原始wire/结果文件/hash、耗时/成本、资源拥有标识与清理回执。产品实现/自动结果/Windows结果/HITL的维度各存，不以单个status覆盖。`accepted`仅来自用户最终反馈。

运行器每次创建子进程都从空映射构造env allowlist：Windows所需`SystemRoot/WINDIR/COMSPEC/PATHEXT`和明确工具PATH；HOME/USERPROFILE/APPDATA/LOCALAPPDATA/TEMP/TMP指向本次合成根；语言/时区/fixture变量按case显式加入。模型、代理、遥测、配置/扩展路径、云凭据等父变量不透传；source MCP“继承父env”的测试也只继承合成父输入。记录允许键和经审查的合成路径/hash，不打印`os.environ`、凭据或真实env值；fake transport绑定本地origin并阻断意外公网，`.env`/Git发现也在自有边界。沿用[实现02合成环境驱动](../../../tests/support/oracle/README.md)与[D15运行器](../experiments/extensions/README.md#复跑)。

失败/不支持/跳过规则：失败保留raw和重现命令；expected不由重跑输出回填。来源不支持但属于Windows补齐目标仍须实现并测试，不能标expected skip。平台不适用可记skip+精确条件，Windows必验缺失则是未通过。未验证记not-run+原因/依赖。需要暂留的xfail必须有缺陷ID、独立预期和拥有任务，不允许作为关闭对应产品母案例的通过数。模型超时/环境无效/任务失败分别统计；禁止只公布去掉失败后的成功分母。

## 收口与真正未决依赖

本票已经能给出复用方式、入口、依赖、责任与放行条件，**无新增用户取舍问题**。既定目标、五项入口、人工最终集中时点均保持已确认；公共Status/map/matrix由主代理收录本报告后更新。

剩余是现有实施/外部条件依赖：兼容路线锁定具体发现/品牌/SDK策略；Windows能力/持久IPC/SQLite与终端路线按其已有任务推进；发布路线决定最终独立构建命令；任务72–76物化缺失评估材料、锁外部环境并获得实际live预算后执行；任务77/78/85取得最终用户体验反馈。它们不是本研究未答的问题，也不能因本票技术收口就写成产品已完成。完整D15剩余协议和215来源断言的产品复验仍由各功能任务承担。

静态复跑命令（只读来源，写本目录两份派生JSON）：

```powershell
python .scratch/ruocun-discovery/research/11-test-replay-gates-build.py
```

结果：805原字节一致；374条均有处置/拥有任务/入口/依赖/锚点；52固定/49菜单/11非TTY；本票真实模型调用0、来源测试执行0、构建器子进程0。产品状态不变。报告与派生清单由独立本地研究提交保留，提交SHA见主会话收录指针及本票交付消息。
