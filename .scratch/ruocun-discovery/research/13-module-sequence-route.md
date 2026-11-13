# D13：模块对应原则与迁移顺序

日期：2026-11-10。任务：[D13](../issues/13-module-sequence-decision.md)。研究分支 `codex/sprint-module-route`，起点 `0a680af14084dc1bc1358263f4836f4fa6cb35b2`；本文仅收口路线，不修改产品、公共状态、对应表或验收矩阵。

**结论：现有资料足够，D13可由主协调独立核对后结题，并解锁D14。** 保留既定805成员映射、84票和实际依赖；未发现需要新增架构或用户取舍的路线缺口。研究完成不等于产品实现、自动验收或人工体验完成。[D13完成条件](../issues/13-module-sequence-decision.md)、[D14](../issues/14-spec-readiness-check.md)

## 对应原则与唯一契约

1. 以[唯一冻结快照](../reference/README.md)为准；不确定先查其入口、调用方与既有测试，按来源最小适配。保持[对应表19个目录职责及C0–C7](../../ruocun/module-map.md)：组合根组装→scheduler→loop/client→dispatcher→Hook/权限/审批→handler/journal；后台结果经事务/inbox/消息确认进入安全边界，UI只观察业务事件。[R-01](../../ruocun/spec.md)、[ADR-0008](../../../docs/adr/0008-source-first-sandbox-parity.md)
2. 顶层入口沿既有归属：`index.ts`→轻量`__main__.py`与`cli.py`（MM-483）；`repl.ts`→`repl.py`（MM-568）；`schedule.ts`→公共定时模块/平台叶子（MM-582）；版本、插件、项目指令和环境探测仍由MM-801/562/564/475负责。完整CLI/入口隔离归70/71，版本与最终产物归79–83；不另建第二套组合根。[逐文件位置](../../ruocun/module-map.md)
3. 命名可用Python snake_case；外部工具名、命令大小写、schema字段、事件、扩展格式及各loader顺序保持。拆合只为语言或平台绑定所需，保留MM ID并登记实际目标、理由/ADR、责任票与证据；新增适配用NEW ID。[对应表维护规则](../../ruocun/module-map.md)

| 处置 | 实施原则与现有入口 |
| --- | --- |
| S 语义改写 | TS/TSX及其断言转Python；机械语法转换不改变业务职责、顺序、限制或取消语义；语言库替换留窄边界 |
| D 数据复用 | 提示、schema、模型定义、i18n、技能正文、fixture和嵌入帧保留实际数据、许可及来源；不能由模型重写后冒充原文 |
| R 协议/回放适配 | 保留已有CLI/HTTP/SSE/Hook/MCP/LSP/Deck输入与独立预期，替换语言/平台启动绑定；外部命令仍按声明执行 |
| P 评估协议 | 保留任务、评分、次数和有效timeout；真实模型结果、材料缺失及预算单列，不继承DAO历史成绩 |

S/D/R/P可组合，详见[D11的374项资产清单](11-test-replay-gates.assets.json)。后续测试投入由[ADR-0009](../../../docs/adr/0009-source-test-baseline.md)覆盖旧研究的扩测措辞：迁移来源已有断言，保留已有失败并最小复验已确认缺陷，不为每票新增故障排列或另一套测试框架。

| 接缝 | 唯一契约及责任，禁止并行重造 |
| --- | --- |
| 品牌/数据/扩展 | [D09原生路径、source map、环境与凭据](09-storage-extension-route.md)：`.ruocun`独立写入，显式只读兼容；各loader分开；04/25/26/34–58/81接线，不导入旧DAO会话或信任 |
| 存储 | [StoragePort v1](09-storage-extension-route.md#storage-port-v1)唯一schema/类型/事务语义；[ADR-0005](../../../docs/adr/0005-runtime-storage-compatibility.md)固定每会话串行DB线程与SQLite 3.54.1实际组合；07拥有底座，10/15–17/26/28/40–49调用 |
| 三类代次 | [epoch-contract](09-storage-extension-route.md#epoch-contract)：DB `owner_epoch`、流 `stream_generation`、runner `control_epoch`分别fence；不能互代或凭UI取消丢弃合法持久结果 |
| 运行时/runner/helper | [D08第2–8节](08-python-runtime-route.md)：单业务loop、工具all-settled/写屏障、先意图后效果再结果/消息/ack；runner拥有Shell/Job与收据，IPC helper只管原生I/O，两个持久域不伪称跨域原子；11–17/38–49按职责接入 |
| 平台叶子与TUI | [D10第3–6节](10-terminal-windows-route.md)：ptk/Rich单输入/协调输出，真实Shell方言；公共端口由factory按OS延迟加载，Win32/POSIX留叶子，不把平台假设放核心；13–18/55/58–68负责 |
| 语言依赖/解析 | [对应表替换边界](../../ruocun/module-map.md)与[D09扩展子集](09-storage-extension-route.md)：Python校验/SDK/JSON-RPC窄适配保留来源语义；RepoMap解析绑定与grammar由33落实、55落实LSP；具体依赖/产物锁随所属票交付，不借替换重写算法或扩协议承诺 |
| 分发/内部角色 | [D12](12-install-release-route.md)：wheel/sdist＋Windows x64 console onedir，同版本CLI/runner/IPC/DNS/dispatcher明确角色；79–83实现资源、运行库、版本化payload和许可，不增执行框架 |

沙箱仅按[ADR-0008](../../../docs/adr/0008-source-first-sandbox-parity.md)迁移DAO默认可选的macOS Seatbelt/Linux bwrap、网络默认允许与原开关；Windows显式请求时拒绝不支持。D22原严格A仍FAIL，额外驱动/service/VM目标已被替代，当前60无D22硬边；60/61/78/79/85验证修订后的真实能力，不重开额外后端。

来源缺陷不自动成为正确预期。既定差异继续保留：MCP未知结果不重放（ADR-0003/54）；自身完整恢复、费用/已确认输入/fork材料补齐（07/17/28/40/41）；请求沙箱不可用不降为普通Shell（R-16/60/61）。其它来源疑点按SOURCE-CANDIDATE与已证实缺陷分列，归原责任票最小处理，不借“模仿”撤销明确决定。[D09差异交接](09-storage-extension-route.md)、[T-01](../../ruocun/spec.md)

## 覆盖核对：表示责任完整，不表示实现通过

本次以起点文件做纯数据读取，直接比较ZIP/manifest与Markdown行，未执行来源或产品：

| 核对对象 | 结果 |
| --- | --- |
| 冻结来源 | 797 tracked＋8 untracked＝805；ZIP额外成员0，逐成员SHA-256/长度不符0 |
| 805成员映射 | MM ID、源路径各805且唯一，漏项/多项/空目标均0；A产品及源码内fixture234、B来源测试215、C脚本58、D其它298 |
| 责任覆盖 | [task-coverage](../../ruocun/task-coverage.json)的215案例族和234核心条目均有有效责任票；`module_references`总数275，其中另41条是其它来源责任引用，不能把275误写为核心数 |
| 资产覆盖 | [D11清单](11-test-replay-gates.assets.json)登记215测试＋58脚本＋16任务＋85独立fixture＝374；其任务注册路径均存在；交付85仍核对全部805成员实际处置 |
| 任务/依赖 | [task-graph](../../ruocun/task-graph.json)恰为02–85共84票，171硬边，无环；逐票Blocked by及[现有依赖图](../../ruocun/dependencies.md)边集合一致 |
| 小批归属 | [冲刺表](../../ruocun/sprint-48h.md)38批覆盖06–85共80票，无重/漏；加已完成02–05即84票，不另拆票 |

## 迁移顺序、闭环与调度

完整拓扑以现有任务图为准，阶段只说明集成时点，不增加跨阶段全局硬门禁；具体票满足自身前件即可推进。

| 顺序/闭环 | 既有责任票与可执行出口 |
| --- | --- |
| 已有工程/模型基础 | 02来源oracle与03仓库外启动汇入04 Chat→05 Responses；06公开重试/取消/fallback已复核集成，实际范围见各票，不扩称完整Agent |
| 最小工具闭环 | 07持久确认→08 TodoWrite/Read→09审批写入→10编辑journal；06＋08→11队列/取消，10＋11→12批工具；以真实产品请求→意图→工具结果→后续回答留证 |
| Shell/后台/恢复 | 09→13，13＋11→14→15→16，16＋10→17；后台交接、等待/事件和自身恢复接入存储契约；11→18尽早接终端产品路径 |
| 上下文/工具/扩展 | 28→29费用/压缩，30→31→32记忆，19/33代码图，34–37技能/插件，38–49子代理/长期任务/Hook，51–54 MCP及55 LSP；依各自硬前件并行补齐 |
| 平台/TUI/完整入口 | 58/59/60–64各能力接叶子，18→65–69完成终端；70汇集其真实前件，70＋54→71隔离入口；不把原型或Job当最终WT/沙箱通过 |
| 评估与交付 | 70→72→73/74，75/76沿既有材料及明确费用授权；77/78技术/人工分列；79→80→81、79→82、81＋82→83；84/85按图等待实际出口和D14 |

各阶段复用已确认五入口（pytest、统一验收驱动、Ruff、mypy、build）；按所属票运行受影响的来源测试/已有复现与必要可运行确认，protocol/runtime/terminal/live/install按实际行为分别留证。未运行、ENV、来源缺陷、迁移回归和有意差异分开，来源测试通过不代填真实平台、性能、模型或人工状态。[ADR-0009](../../../docs/adr/0009-source-test-baseline.md)、[D11入口](11-test-replay-gates.md)

普通同领域2–3票复用上下文/worktree；存储、权限、取消、恢复等关键边界可单票。**链式前件必须独立复核、集成并结题后，才实施同批后票**；无依赖且已解锁票可同送审。候选、子测试绿或批末统一审查均不提前解锁。共享入口、StoragePort、事件结构及总表由主协调锁定唯一写者；四槽及审查积压规则按[ADR-0006](../../../docs/adr/0006-batched-sprint-workflow.md)与原冲刺表执行。

本起点实际为5 resolved（02–06）/2 claimed（07/58）/77 blocked：06已接收`daf2f5d`；07候选`6a4228d`待独立复核，不能用其局部存储/平台通过解锁后继。先完成07既有最小回修与复核集成，再优先08解除09/11/19/34等主链；另一路可做28或接续58。58必须等07私密文件端口；28依07＋已完成05，与08无硬依赖，但二者涉及存储时先划清写权。28/58均保留原小批归属，不增设等待整包完成的门槛。[当前实施记录](../../ruocun/implementation.md)、[08](../../ruocun/issues/08-readloop.md)、[28](../../ruocun/issues/28-cost.md)、[58](../../ruocun/issues/58-credentials.md)

77/78当前仍pending/none；自动出口工具已独立集成`c366fc7`。只有声明的78→79、77→84可在真实自动证据满足时放行；85始终等待77/78完整结题与用户accepted，其它普通票与D节点仍按硬前件。人工集中最终77/78/85；Linux/macOS实机与未执行项目保持pending。[ADR-0006](../../../docs/adr/0006-batched-sprint-workflow.md)、[工程票](../../sprint-tooling/issues/01-automatic-exits.md)

## 精确遗留与收录动作

这些是索引/历史措辞修订或已有实施义务，不是新增D13研究前置；主协调在D14核对并统一收录，历史失败字节不改。

| 遗留位置 | 正确处理与责任 |
| --- | --- |
| spec头部“产品未开始”、第20行19票/6resolved，R-16仍列10/12待收口，M0仍把22列额外前提 | 按已收录D08–12/ADR-0008/9及实际状态更新叙述；D14核对，产品状态仍取任务/矩阵 |
| sprint第109行D22→D12链、旧D22阻塞60反例；D10/旧研究的完整Windows后端段 | 标明由ADR-0008替代，仅保留调查失败历史；D14/主协调，60/61消费来源能力契约 |
| dependencies说明、spec完成标准补充与sprint“待适配”旧段仍称工具尚不支持 | 以已收录`c366fc7`及真实77/78证据为准，标历史而不删硬边；D14/工具票/主协调 |
| module-map第4行、替换边界与NEW候选段仍有早期“未定案”概括 | 保留MM/NEW身份，指向已接受D08–12与实际证据；D14整理索引；33/55锁其实际解析适配，79–83核对产物，85核对全量成员 |
| coverage末段称18/19待执行；map已决定摘要仍提完整Windows沙箱 | 只更新索引到已收录决定及ADR-0008，不重写实验失败；D14/主协调 |

本轮只写本文；覆盖/hash计算的Python进程使用清空后的环境白名单、合成HOME/配置/TEMP与隔离模式，仅标准库读文档/JSON/ZIP。未运行产品、来源测试或历史探针，未安装、付费、读取真实配置/秘密或新增测试；没有新增产品通过数。D13可结题的依据是对应与顺序可执行，实际实现、依赖版本/角色产物及最终用户验收由上述原票继续完成。
