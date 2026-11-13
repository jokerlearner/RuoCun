# RuoCun 完整迁移实施进度

开始基线：`f199624aa2902e0519bcb1191b4b9bba18a291b8`（main，工作区干净）。
集成分支：`integration/ruocun-migration`。
用户已确认全部规格、84张任务和5项开发入口，并授权子代理/worktree/TDD/本地提交及集成合并。

## 当前状态

2026-11-13 用户选择摘要原始前缀方案B并授权真实API，确认现用硅基流动渠道。[摘要前缀交付](../summary-prefix-20261113/delivery.md)完成：仅4产品成员相对B-r3变化；138项定向回归、全仓Ruff/Mypy284源、独审、固定wheel314成员仓外绑定和CLI三案通过。固定B-r3旧控制器/选区与新路径各三组首摘要，旧均0%，新加权98.2162%，含原图案例；47次请求峰价保守估算¥1.57135704，未超过¥2，配置只读。候选包dist/summary-prefix-b1；日常入口仍B-r3，未Git提交，不把受控暖摘要指标当全任务永久保证。已确认的旧单页验收假设失败按公开分页适配，原内容断言及失败日志保留。

2026-11-13 用户进一步授权把B-r3更新现用安装。[真实部署](../deepseek-compaction-20261113/deploy-current.md)已完成：桌面原入口切到Apps/RuoCun/venv-compaction-b-r3；28原文件/6一致性DB私有备份，6会话全部升级且原业务表/meta/配置保持；实际新解释器本地SSE三节点通过，真实配置旧会话启动及另进程原用户消息回查相等，外部网络尝试0。旧环境与入口备份保留，未改产品或Git提交。10票resolved；09视觉/缩放验收仍pending。

2026-11-13 [B-r3压缩与完整原文归档](../deepseek-compaction-20261113/delivery.md)实现、自动出口及独审完成，T01–T06已resolved，T07自动passed/awaiting-user。最终包在dist/compaction-b-r3，314成员绑定一致；R1全量实际1734 passed/1旧目录计数failed/4 deselected，目录适配及R2/R3确定缺陷修复按ADR-0015定向复验，原失败和差异指纹完整保留。全仓Ruff、Mypy291源通过；最终pure无源码注入的压缩/升级/重开/回查/Todo三节点通过。未调用真实模型、未切换日常安装、未Git提交；真实Windows Terminal显示/缩放与用户体验仍pending，[合成入口](../deepseek-compaction-20261113/evidence/manual_terminal.py)已备好。

2026-11-13 用户明确要求用 TDD 按 B 规格完成计划。主票02已领取，T01基线/契约完成，T02压缩策略与T03存储分文件并行；主协调负责运行时/工具/导出接线，独立角色复核存储与权限。起点381f73d，23个相关原文件副本与指纹已保存，所有原有改动保留；固定来源和测试边界沿已发布spec。实现与测试结果从各票及本批执行记录读取，不将计划通过计为产品通过。

2026-11-13 用户已选择 B：核心压缩机制＋完整原文归档与回查，并调用 to-spec 要求详细计划。[规格](../deepseek-compaction-20261113/spec.md)、[技术计划](../deepseek-compaction-20261113/plan.md)、[七票任务与依赖](../deepseek-compaction-20261113/task.md)、[验收清单](../deepseek-compaction-20261113/checklist.md)已发布；主票[02](../deepseek-compaction-20261113/issues/02-compaction-and-archive.md)为ready-for-agent，T01可领取，其余按硬依赖阻塞。来源固定并已完成文档一致性检查。尚未实施产品改造，产品测试/安装/体验均未执行；既有失败保留停止及工作区改动保留。

2026-11-13 用户授权的[记忆来源标签修复](../memory-source-recall-20261113/README.md)已完成：确认反思写入的 `user_stated` / `inferred` 被当成缺失文件而漏召回，现兼容识别标签、保留有效期与真实文件校验。146 项受影响回归、两个独立产品进程的启动召回、Ruff/Mypy 和独立复核通过；真实模型 0 调用，已有记忆无需重写，改动未提交。固定发行包未重建，本次结果对应当前源码工作区。

[最终批次](../ruocun-next24h/batch-final.md)已交付，有效进度 **79/79**。固定 [b09-r4](../ruocun-next24h/evidence/batch-final/package-r4/README.md) 的 19 个自动子案例、77 的完整终端体验、78 的 Windows 重启后会话与凭据恢复，以及 85 的范围核对均通过。合成凭据删除读回 `not-found`。五张排除票保留历史状态。macOS 实机和托管 CI 保持待验。[最终发布说明](../../docs/release/batch-09.md)

[批次09](../ruocun-next24h/batch-09.md#技术交付记录)八票 73、74、76、79、81、82、83、84 技术通过，D13/D14 通过，有效进度 **76/79**。最终产品 `8e7760ce` 的[固定标准包 b09-r3](../ruocun-next24h/evidence/batch-09/package-r3/README.md)通过仓外安装、恢复、手动升级和安装集成。R3 受影响用例 110 通过、最终包集成 61 通过。R1 默认首跑的 20 个 QA 依赖失败全部精确复跑通过，两轮原记录均保留。77、78 自动出口通过，用户体验待最终批次，85 仅等待两票的人工出口。macOS 实跑和托管 CI 保持待验。[安装与发布记录](../../docs/release/batch-09.md)

[批次08](../ruocun-next24h/batch-08.md)四票56、60、61、72通过，有效进度 **68/79**。固定产品 `8ee4a9b9` 的[集中构建与安装](../ruocun-next24h/evidence/batch-08/integration/README.md)通过，默认全量 `1699 passed, 4 deselected in 621.80s`。77/78自动出口通过、人工待验。79标准包前置当时已齐，由批次09接续。

[批次07](../ruocun-next24h/batch-07.md)六票42、57、59、62、70、71完成技术交付，有效进度 **64/79**。产品 `d00d4a1b` 的[b07-r2集中交付](../ruocun-next24h/evidence/batch-07/integration/README.md)通过，默认全量 `1684 passed, 3 deselected in 668.43s`，306 个产品成员严格绑定。77 的批内前置已齐，自动与人工出口继续待验。78 仍待61。下一批由后续排程领取。

[批次06](../ruocun-next24h/batch-06.md)五票22、23、25、33、55已定向技术与独审通过，有效进度 **58/79**。代码地图/导航、网页抓取/搜索与Config普通入口均落地；真实TS源9操作与编辑同步、协议故障和进程树关闭分别留证。产品`0a0c1cea`的[b06-r1集中交付](../ruocun-next24h/evidence/batch-06/integration/README.md)已完成：唯一全量实际`1641 passed, 3 deselected in 727.16s`，Ruff、Mypy254源码、4项离线冒烟、44项运行依赖纯安装和285成员严格字节绑定通过。70新增22/23/42真实依赖，70/71未提前结题；77/78整体体验仍待验。

按[ADR-0014](../../docs/adr/0014-terminal-and-scope.md)保留完整终端及其余范围，5张excluded。[批次03](../ruocun-next24h/batch-03.md)已结题，有效进度 **43/79**。28、29、45、47通过普通入口及独立复核。63、67、68通过终端技术复验，用户确认交接、面板、Unicode 剪贴板、通知与焦点表现正常。[实机回执](../ruocun-next24h/evidence/n18/wt/runs/20261111T101837Z-52f7cc/README.md)固定包为[b03-r1](../ruocun-next24h/evidence/batch-03/integration/README.md)，全量1587通过，另1项夹具隔离修正后同包定向通过。

[批次04](../ruocun-next24h/batch-04.md)的 43、44、48、49 已通过定向自动测试和独立复核，有效进度 **47/79**。批量派发、父子双向消息、六条内置命令、长任务和 Hook 生命周期均经普通入口或受控 SQLite 验证。未知结果保留现场并停止受影响的后续操作。46 留给后续安排，77/78 整体体验仍待验。

[固定包 b04-r1](../ruocun-next24h/evidence/batch-04/integration/README.md)对应产品源码 `dc3f76d1`，隔离全量 1602 通过、3 未选。Ruff、Mypy、离线安装与包字节绑定通过。

[批次05](../ruocun-next24h/batch-05.md)的26、46、51–54已集成，来源定向自动及独立高风险复核通过，有效进度 **53/79**。会话切换/分支/清理、真实Monitor、stdio/HTTP/SSE MCP及未知结果保护已落地；子专属MCP接现有代理生命周期与恢复摘要。固定产品`c85b80d5`的[b05-r1集中交付](../ruocun-next24h/evidence/batch-05/integration/README.md)已完成：唯一全量实际`1621 passed, 3 deselected in 737.20s`，Ruff、Mypy231源码、四项离线冒烟、隔离安装与262成员严格字节绑定通过。未运行付费模型，77/78整体体验仍待验。

上次固定候选为[批次02 b02-r1](../ruocun-next24h/evidence/batch-02/integration/README.md)，源码5be452c，wheel SHA256为834e9fb2932aaebae5d01363a1f1b8ca158b9f1be0b3b8616ba1a3bbb616ea39。Ruff、mypy193源、offline、213成员仓外纯安装与默认后台角色已通过。唯一全量实际1520 passed/7 failed/3 deselected，原7项经夹具/环境诊断定向通过。此次接续的69是后续源码，固定包证据仍对应原源码。

上一批固定产品为[N24-r2](../ruocun-next24h/evidence/integration/README.md)，源码31208a9，wheel SHA256为c12ead3d1174a2b6099431a1984a30cd50edaae13b7d1dfb013650d9a9b6baa9。r1全量实际1445通过、4项夹具路径失败、3项默认未选中。夹具修正后原4项在r2通过，按ADR-0015复用1445项旧通过，未重复整套全量。Ruff/mypy/offline及构建通过，168成员严格绑定，仓外纯安装默认后台角色真实接管/取消通过。真实终端五项用户技术反馈与正常退出已记录，77整体体验仍pending。


N24上一批新增13、14、15、18、21、24、58共7票resolved。权限分类、实际Shell方言、增量输出、独立runner、系统凭据与问答消息均经实际入口和独审集成。用户已确认A+B+C及现有模块对应，落实于[ADR-0015](../../docs/adr/0015-batch-validation-and-packaging.md)。[批次02](../ruocun-next24h/batch-02.md)安排终端6票与16/17高风险接缝，已按用户要求开始实施。28原在途保持。所有原失败和旧固定包保留。

原排程：[下一轮 24 小时计划](../ruocun-next24h/plan.md)，T0 为 2026-11-11 09:50:11 +08:00，检查点为 2026-11-12 09:50:11 +08:00。上一轮里程碑见[约 20 小时计划](../ruocun-next20h/plan.md)，其有限失败保留规则继续适用。

最初范围调整时曾核对171条历史边、161条有效边；批次02另补17对39/40/41的真实整票依赖并重核无环，不能继续引用旧边数作为当前统计。

**纯Python首版自动技术出口已完成，人工体验pending。** T0：2026-11-10 21:01:03 +08:00，起点01e4606。最终产品代码1ad72d6，固定r2 wheel SHA256=`802e22a52be3b24917460d81353dca50a8ae736e70da5ab2449a3b20abaa8ad7`，位于`dist/mvp-r2/`。601项自动回归通过、3项oracle显式排除；Ruff/mypy/offline及sdist→wheel=direct构建通过，64包成员字节绑定、实际SQLite3.54.1及独立仓库外七工具/拒绝/保存重开/两轮交互/SIGINT通过。Standards产品0问题，Spec原失败屏障1项已修，剩余0。详见[M03](../ruocun-mvp/evidence/m03/README.md)、[M04](../ruocun-mvp/evidence/m04/README.md)及[启动](../../docs/mvp-start.md)。

本机Temp安装的`ruocun.exe`被应用控制WinError4551阻止，真实记ENV；已验证`python -m ruocun`。没有真实模型/付费API调用，真实Windows Terminal按键/视觉/缩放及用户体验未验、不accepted。按[ADR-0011](../../docs/adr/0011-python-coding-mvp.md)，M01/M02首版子集resolved；M03/M04自动通过、按任务流转规则为awaiting-user等待体验，未虚标全部结题。原82票完成数仍6，不自动开始高级功能。工作树、私有环境、合成状态、旧产物与失败材料保留。

首版高级功能已后置；原82票完成数不因首版子路径增加，旧issue_graph不用于首版派发。保留旧worktree、候选和历史失败；tools/types.py由主协调固定唯一接口，六文件/计划工具及前台Shell已分别独审集成后注册，M01–M04的首版自动技术条件已满足，最终体验继续单列。

### 首版启动前保存点（历史）

本轮已落实[ADR-0010](../../docs/adr/0010-selected-scope-and-lean-workflow.md)：R1、R3、W3、W5、W6、D2、D3、V1、V2缩减，Q1/Q2执行减负生效。仅改规格、约定和计划，产品仍停止；没有新产品测试、模型调用或通过结果。原84票保留，75/80本轮excluded且未完成；有效范围82票，目前6 resolved、3 claimed、73 blocked。旧issue_graph不识别scope，恢复前先适配或按ADR显式过滤75/80并留证。

**已按用户要求停止。** 2026-11-10用户要求“再完成一个小模块后保存进度并停止”，本边界替代连续冲刺授权。最后的Session／费用基础已完成、独立复核并集成；实现`c8b30e3`，复核`f51d214`，详见[实现](evidence/28-context/session-cost/README.md)与[独立证据](integration-evidence/session-cost/README.md)。19项DAO来源语义测试独立通过，Ruff/mypy及sdist→wheel构建、非editable安装通过。所有本次自有工程进程已退出，worktree、环境、缓存与历史证据保留。再次执行等待用户明确恢复，不再自动调度。

本批08与28两票保持claimed。已集成Session类公开接口沿冻结session.ts；实际为`Session(systemPrompt, model, *, env=None)`、`addUsage(u, model=None)`及来源其余内存方法。此前08交接中的request/attempt/provider扩展与toCheckpoint/fromCheckpoint仅早期方案，均未提供；继续时以实际代码为准。cli及公共表归主协调，Checkpoint等共享存储仍归既有唯一契约，未在本切片扩展。

| 保存对象 | 保存点与接续位置 |
| --- | --- |
| 08 / B01 | `codex/b01-tools`，`a6d4923`；[交接](evidence/08-readloop/HANDOFF.md)。只读来源及环境准备完成，尚无产品代码/测试；09未开始 |
| 28 / E01 | `codex/e01-context`，`c8b30e3`，基础小模块已集成。按R1收缩跨重启费用保证；仍余历史费用不完整标记/预算口径、cache_audit、轮数/loop预算及命令接线；29未开始 |
| 58 | 原`impl/58-credentials`候选`433d980`及未跟踪材料保持；07前置已满足，未接续或验收 |
| D13 | 报告`c3a0140`已收存，尚未主协调逐项收录，claimed；D14未派发 |

- 冲刺曾于2026-11-10 19:01:22 +08:00启动；现已停止，原48小时连续调度不再自动执行。
- 历史84票仍只有02–07共6票完成；排除75/80不增加完成数。当前有效82票中完成6票，28基础小模块不计整票完成；08/28/58前置满足，仍等待恢复授权。
- 来源优先与沙箱范围按ADR-0008：DAO可选macOS/Linux后端、Windows显式不支持；额外Windows后端/组件/VM已停止，D22调查收口但原A仍FAIL，不伪造产品通过。
- 测试按ADR-0009，仅以DAO已有测试语义迁移为默认基线，不再主动扩测。自动出口工具工程票已独立复核集成c366fc7；77/78仍pending/none，工具不会因此放行产品票。
- D12中Windows onedir由D2移出本轮，仅保留标准Python包；3.11.* metadata与3.11.9实测基线区分保持。81改人工停进程/备份/安装更新；72–74/82/83评估工程、CI与完整文档继续保留，产品仍待实施。

## 冲刺历史检查点

以下按保存时点保留，当前授权、范围与进度以顶部为准；其中未启动、D22/管理员组件等旧安排已由后续明确指令替代。

用户最新测试要求已记[ADR-0009](../../docs/adr/0009-source-test-baseline.md)：默认迁移并通过DAO已有测试，不主动扩额外测试门槛。已通知全部实现/审查者安全收尾正在运行的检查；07仅修已亲验的来源关联错误并复跑原5项，之后收口；既有测试/证据保留。工具适配已有有限用例收口，不继续扩展，未验范围仍如实记录。

用户新指令已落实[ADR-0008](../../docs/adr/0008-source-first-sandbox-parity.md)：沙箱模仿DAO现有能力，默认可选，仅macOS/Linux实现OS后端，Windows显式启用时明确不支持。额外Windows原生隔离补齐目标和ADR-0007组件/VM评估被替代；D22调查收口但A仍为失败，原始证据保留。60/61仍待实际实现与验收，不因删去额外目标标通过；其它已解锁任务和07继续。后续不确定机制优先查来源，保留既有明确差异，避免自行扩大架构/保证。

D22路线取舍已获用户确认：接受额外隔离组件，先在可回滚Windows环境验证，见[ADR-0007](../../docs/adr/0007-windows-sandbox-prerequisite.md)。当前仅只读查询宿主环境，未安装/启用任何组件、未重启或改防火墙；Windows11Pro 26200，Hyper-V及Windows Sandbox功能未启用，已启用VirtualMachinePlatform但未发现现成VM管理命令或VMware/VirtualBox/Sandboxie安装。先确认可回滚测试环境，安全门禁保持，其他产品票继续。

首批A01已接收：06由独立审查`daf2f5d`验证并快进集成，正式完成**5/84**（02–06）。公开模型重试/取消/fallback已实现；07仍是当前基础解锁点，58等待07。06的319全量测试及21独立边界、五入口和仓库外wheel均通过，具体范围与限制见[独立证据](integration-evidence/sprint06/README.md)。下文4/84及06未完成描述保留为历史检查点。

2026-11-10 19:01:22 +08:00 冲刺正式启动：用户明确“现在启动，由你统一负责”，本指令替代此前“完成06后停止”的边界。T0为上述时间，48小时目标时点为2026-11-12 19:01:22 +08:00，质量优先、未通过继续修复；基线为`13f0241778da8cb7072b546f9551b82df31a4258`。主协调接管既定范围，按ADR-0006连续实施、本地提交和集成；付费模型预算、真实人工体验及原异常探针限制仍按原记录。下文“未启动”和停止描述为启动前历史。

首批调度：A01由新的独立审查者在新worktree复核06候选`4b8a63d`，不重复派实现；A02在`.worktrees/wb-i07`接续既有存储候选和未保存材料，使用diagnosing-bugs/TDD修复真实私密文件边界；D22在新研究worktree先基于失败证据建立可判别调查，保留A失败后的禁止扩大实验边界。主协调独占公共任务图、状态、cli/注册接线及总表；两个实现槽和一个审查槽均计入四名额。58继续等待07；本次启动不将任何候选或既有子测试视为完成。

2026-11-10 工作流调整：用户已确认[ADR-0006](../../docs/adr/0006-batched-sprint-workflow.md)与[48小时计划](sprint-48h.md)的执行方向。本轮仅修改项目流程文档和任务图数据，不派发产品实现、不调用付费模型；冲刺状态为**未启动**，t0未设置。“仅完成和复核06后停止”的既有边界继续有效，07/58及D22不因计划落地恢复执行。任务完成数和验收结果保持原记录，后续正式启动时重新核对在途分支及最新证据。

本轮只读核对在途保存点：06为`4b8a63d`，早期`4530028`的DNS问题描述属于历史检查点，最新实现者证据仍待独立复核，不能按已集成计算；07为`b06e238`，保留未提交的`test_session_identity.py`及原探针/异常对象；58为`433d980`，保留其未跟踪证据。未改动上述worktree，06/07/58均保持claimed。

2026-11-10 用户指定由 Codex 接手后续工作，替代此前 WorkBuddy 接续安排；既定规格、授权和最终统一体验验收不变。集成基线为 `588c1f9`，06/07/58 的各自 worktree 有未提交候选，不能直接按完成计算。Codex 独立核查发现：06 的阻塞网络流、取消及真实 HTTP 错误需补齐；07 的 SQLite 加载、只读、串行线程与恢复契约需核查修正；58 的 demo 存在覆盖已有配置风险，修复验证前不得运行该 demo。未发现本地 WorkBuddy/CodeBuddy 进程，但这不足以证明其它方式无活动。三票保留原工作并由 Codex 独立实现者接续；实际行为及最终验证以各票证据为准。

D22 历史候选及独立静态复核已收录至 `a7b28f4`，见[复核记录](integration-evidence/d22/README.md)。A 失败，B/C 未运行，安全门禁仍未解锁；其历史 `audit.py` 会覆盖原审计文件，禁止直接在历史证据目录运行。06 未完成检查点为 `4530028`，DNS 阻塞取消仍未解决；07 未完成检查点为 `88459e0`，其平台端口三轮独立复核尚未通过，第三轮发现检查后父目录可被同用户替换为 junction 的竞争，失败证据保留在分支 `codex/review-platform07-r3` 的 `493e5f5`；58 未完成检查点为 `433d980`，等待07私有文件端口及其他验收。三个候选均未合入、未结题；不因检查点或已通过的子测试标记完成。

07 句柄相对重命名探针发生对象越出合成目录事件，详见[事件记录](integration-evidence/07-relative-probe-incident.md)：一个 10 字节合成对象由持有句柄确认移至 `wb-i07` 根目录，另有一个同名模式对象来源未证实；均保留，探针已停且自有进程已确认退出。不要重跑该探针或清理上述对象；共享平台候选仍不得集成。

用户要求完成当前小模块后停止：仅继续完成和复核 06，不再派发后续工作。07 已停在未完成检查点 `b06e238`（安全并行子集 13 项通过，不能替代产品持久化验收）；`.worktrees/wb-i07/tests/test_session_identity.py` 在停止前另有未提交、未运行的一项改动，保持原状；两个异常对象及其他未跟踪材料保留。07/58 均继续 claimed，不可整体合入含未通过平台候选的分支。

已发布02–85实现票，共84张正式任务；01为入口确认，不计入84张。02/03/04/05已resolved，正式完成4/84；05 已由独立复核集成至 `b0b5052`。05 落地后共享 client 契约已稳定：06 可基于 `streamChat` 新增的 `chunks` 消费与 Responses 路由分支实现重试层；07/58 接口独立。三张票已按 implement-spec Step 6 的并发精神**同一批并行领取并派发**：`impl/06-resilient`/`.worktrees/wb-i06`、`impl/07-store`/`.worktrees/wb-i07`、`impl/58-credentials`/`.worktrees/wb-i58`，均从含本批领取记录的集成 tip 开始；各自独立复核后由主代理统一集成，`cli.py` 等共享文件的合并由主代理统筹。02为来源对照驱动，03为安装/启动和开发工程，04为配置→提示/参数→Chat SSE 首轮流式对话，05为 Responses 路由两轮工具回合；实际工具执行、会话存储与模型韧性等业务核心尚未完成并集成。
决策票仍在discovery目录，未关闭前置按frontier实时查询；不以实施授权代替技术验证或用户体验。

## 接续与调度

1. 读取AGENTS、CONTEXT、规格和本进度。
2. 派发前按[当前范围](../../docs/adr/0014-terminal-and-scope.md)过滤旧 frontier，并核对保留任务的实际前置。工具适配见[工具票](../sprint-tooling/issues/02-scoped-frontier.md)。
3. 按顶部[当前排程](../ruocun-next24h/plan.md)登记实际起点及文件归属。复用已有分支和证据前核对在途状态。
4. 子代理读取TDD及对应来源测试，原断言red→green；普通2–3票可按ADR-0010记录批内许可后连续实施、批末独审。关键接缝及跨批调用先独审集成再用，逐票提交和证据保留。
5. 四个名额按ADR-0006分配；独立审查在另一worktree验证，主工作区fast-forward后由主协调更新逐票记录。自动出口工具已集成c366fc7；77/78尚无通过证据，实际门禁保持。

## 证据规则

每票记录提交、red/green及运行证据。研究/探针、产品测试、真实模型、真实Windows Terminal和用户体验分开记录。
完整规格未完成前不得将本文件、父规格或验收矩阵标为全量完成。最后审查基线之后的提交与未提交/新增文件。
仅清理本次创建、已合并且干净的worktree；历史研究/实验worktree保留。

## 执行日志

- 2026-11-10：九项缩减与Q1/Q2已完成文档/图数据调整，[独立复核](integration-evidence/scope-0010/README.md)无剩余阻断。历史84节点/173边、有效82节点/169边，DAG与逐票Blocked by/Mermaid一致；215母案例ID、805来源MM映射保持，全部Status不变。75/80excluded不算完成；有效6 resolved/3 claimed/73 blocked。产品、测试、工具Python、冻结来源和原始技能参考未改，无新产品/模型/性能/人工通过。Scope工具适配单独登记，恢复派发前适配或显式过滤，停止边界保持。

- 沙箱按DAO能力修订已提交`d5bb7ec`，D22以调查失败/新增目标被替代的结论resolved，原A仍FAIL、无产品沙箱通过。决策frontier实查只解锁D12，已领取给/root/release_route，在新分支整理已验证打包/运行时与来源一致的发布路线；产品60/61仍blocked等待Shell/网络工具等前置。07平台修复已通过独立9项与20回归的子集，整票存储仍待最终候选；工具适配候选e9c7798待独立审查。

- 首批A01结题：06候选`f12f949`经独立审查最终`daf2f5d`（含集成f06e866）通过，主工作区已ff-only接收。独立319 passed / 3 deselected、21边界、ruff/mypy32/build/offline4/pipcheck、仓库外纯wheel公开503→fallback路径全部通过；真实DNS helper退出及服务器线程join，34回执scan_hits=0。主协调同步06 resolved、WIRE-07/08子路径及MM-439/新增适配登记；无人工accepted或完整案例族通过被新增。

- 冲刺首轮：06独立来源对照发现fallback参数校验、Retry-After数字、未渲染工具片段和fallback错误status四类差异，主协调已在原候选分支TDD回修（代码`bb22239`、字节保护`f12f949`），18定向用例及319全量测试通过，五项入口通过，现交/root/sprint_review06最终独立复验，尚未结题。07已在新隔离目录完成竞态红信号并修复进程退出误判等子路径，真实存储全量仍待完成。D22诊断及独立纯数据复核已收录，严格A仍失败，后续取舍等待用户；独立产品工作继续。依赖工具适配另记[工程票](../sprint-tooling/issues/01-automatic-exits.md)，不计产品84票、无产品通过被新增。

- 2026-11-10：本轮仅落实ADR-0006、小批工作流与48小时计划；补58→07硬依赖，声明77/78自动技术出口以及79/84未来消费规则，85显式保留77/78完整人工门禁。Python依赖查询工具与产品代码均未适配，未运行产品测试或付费模型、未改变任务完成状态、未启动计时。验证及具体差异见[计划](sprint-48h.md)。历史“07/58接口独立”描述属于当时派发判断，当前以58等待07私密文件端口的显式依赖为准。
- 本轮文档核查通过：基线`01e6dabecdda5fc5bf5e8581727a677a3ad0d203`；84票状态保持4 resolved / 3 claimed / 77 blocked；38批覆盖80票无重漏；172条硬边在任务图、票据与Mermaid一致；图无环；23份原参考文件符合manifest hash；新增本地链接/锚点与Git差异格式核查通过。核查进程使用环境白名单、合成HOME及Python隔离模式，只解析文档/数据，不加载产品或运行项目测试。独立文档审查完成，已修复“工具待适配导致全项目停工”的过宽措辞；21个文档/任务图文件属于本轮范围。产品自动、真实性能、真实模型和人工体验结果均未因此改变。

- 2026-11-05：已记录开始基线并建立集成分支，发布确认后的任务图。下一步领取02及可并行的决策前置实验。

- 2026-11-05：首批领取实现02及决策实验D15/D19，分别使用独立实现分支和worktree；其余实现票仍受真实前置约束。

- 2026-11-05：已核验task-coverage.json：215案例族与234个非测试源码条目均有任务引用；这只表示责任覆盖，不是产品实现/验证通过。

- 2026-11-05：D19候选b1b15b5经merger在60404b8复测2 passed，但kill目标与事务worker的身份绑定尚不足；主分支未快进，保留证据并派fresh修正代理。D19仍claimed，未冒充产品通过。

- 2026-11-05：02和D15已提交候选交独立merger分批复验；D19补身份证据与历史证据长路径可读性。开始D06终端原型，HITL反馈前保持claimed。未接收D19首次merge60404b8。

- 2026-11-05：已接收02（实现f99ae1ef、merge eefab839），独立12 Python/190相关来源断言通过。D15独立复测因深路径复制ENV尚未执行，交fresh merger以显式长路径读取修复其隔离准备；不改产品/期望。D19修正仍在复核。

- 2026-11-05：已接收D15（候选30b9299、独立merge6945f41），11项复验通过，决策票resolved。用户明确确认MCP未知结果停止重放，新增ADR-0003并同步规格/EXT-10/54票。D19身份修正0419c42待fresh独立复验；领取D18文件/IPC实验。

- 2026-11-05：D19修正0419c42经独立复验已接收564f8ca，D19 resolved；不采用先前无直接身份绑定的证据作结题。用户首组D06体验回复“正常”，随后要求人工统一最终验收，已记ADR-0004并调整D06/18验收时点；未验人工项不再阻塞继续编码。领取D17自动系统能力实验，准备独立复核D06候选ad48d6c。

- 2026-11-05：D06候选ad48d6c经独立14项复验接收b114609，按ADR-0004技术票resolved，所有未做人工仍归最终77/78/85。当前已完成实现02；技术决策06/15/19新增resolved。D18候选14fcde3待独立merger；D17仍执行；领取D07分发探针。

- 2026-11-05：WorkBuddy主协调会话接手，核对分支/HEAD/工作区/两个frontier均与本文件一致。实际创建 `.worktrees/wb-capcheck`（`wb/capability-check`）并派发两次独立上下文只读子代理，核实其cwd/分支/HEAD及读取文件来自该worktree；后台shell任务经结果回收确认。本客户端子代理无原生cwd参数，工作目录由绝对路径prompt指定；带后台标志的子代理结果随调用同步返回，未出现可异步轮询的agent task_id，已如实记录该适配方式。实现图frontier仅04，决策图frontier为空。领取04并记录分支/worktree，从含领取记录的集成tip创建独立实现worktree；独立merger另派。

- 2026-11-05：04实现候选 `9c7c43e`→`2b896f1`→`df552f4`（31文件/+4703行主体，另有资源字节保真与收尾补证），独立merger `dbdd0bc` 在 `.worktrees/wb-m04` 两次merge后亲自复验五项入口、仓库外wheel-only安装、7类配置失败/非法UTF-8/SSE断流与资源退出边界、来源断言独立性，全部通过、无阻断缺陷；主工作区 `--ff-only` 快进 `dbdd0bc`。04 resolved，正式完成3/84。实现者证据 `.scratch/ruocun/evidence/04-chat/`、独立复核 `integration-evidence/04-chat/`。全量pytest 208 passed/3 deselected，五项入口全0，真实模型0，HITL按ADR-0004未验，来源oracle全量本票not-run；母案例族与全量规格未标通过。独立复核两项观察 O-1（`[DONE]`缺失但EOF干净结束返回complete，属冻结来源忠实迁移，登记为WIRE-03后续子案例语义，不改变既定行为）与 O-2（4处弱/结构自洽断言，登记为后续独立oracle加强项）已写入04票，不私改产品掩盖。主代理同步更新任务票、对应表与验收矩阵，并释放05/06/07为ready-for-agent。

- 2026-11-05：技能适配补记。`ruocun-workflow` 及其 `references/implement-spec/SKILL.md`、tdd 等原始参考在本客户端未注册为可调用 Skill，主代理与实现子代理均按项目技能第21行的适配方式**直接读取文件并执行其步骤**，未使用 Skill 工具注册路径；此前只记录了子代理/worktree 适配，未单独记录这一条，现补齐。implement-spec 的 Step 6 与开头是「frontier 变化后派更多实现子代理 / background where possible 以最大化并发」，属鼓励而非强制；本项目按 `ruocun-workflow` 第23行与任务票「共享接口与并行」段，由主代理统筹共享接口后决定并行集合。05/06 共享 `src/ruocun/client/client.py`（05 已新增 `buildRequestBody(use_responses=...)`、`streamChat` Responses 路由分支与 `chunks` 消费逻辑，06 重试层须在此基础上组织），`cli.py` 亦为共享文件，故二者串行；07/58 接口独立，本可并行而此前未并行，属主代理保守取舍，后续按接口稳定后的同一批并行派发。

- 2026-11-05：主工作区提交 04 结题公共记录 `7623e7d`（04票 resolved、05/06/07 释放、11个MM行与11个案例族状态、NEW-12..15 登记、implementation 更新）。复核 `issue_graph.py` 真实 frontier 为 05/06/07/58，其中 58 的 Blocked by 仅 04 却仍为 blocked，已修正为 ready-for-agent 保持状态一致。领取 05（`impl/05-responses` / `.worktrees/wb-i05`），派发独立实现子代理；06 因与 05 共享 `client/client.py` 待本票接口稳定后再派，07/58 保留 ready-for-agent。人工体验仍按 ADR-0004 集中最终 77/78/85。

- 2026-11-10：05 实现候选 `2884cac`（12文件/+1933行，Responses 路由、function/reasoning items、统一事件、两轮工具回合）。前两个独立复核子代理分别受频率限制与会话中断影响，只完成合入 `5e89e75`、无复核证据；主代理核实真实状态后重新派发独立 merger，补完全部复验并提交 `b0b5052`（9 个证据文件，clean）。复核亲跑五项入口（pytest 256 passed/3 deselected、ruff、mypy 30 文件、build、offline 4 case）、共享 client 契约 `contract.py` 36/36（`types.py` 未改、默认 Chat 输出与 04 一致、路由 URL/请求体）、仓库外 wheel-only 安装 `verify_demo.py` 28/28、`boundaries.py` 11 流场景/6 CLI 场景失败取消边界、服务端口与线程清理，全部通过、无阻断缺陷。主工作区 `--ff-only` 快进 `b0b5052`，05 resolved，正式完成 4/84。O-1 六处弱断言、O-2 边界粒度、OBS 前序残留、ENV 复用公开 wheel 闭包均写入 05 票，不私改产品掩盖。05 直接后继 28（还缺 07）与 64（还缺 18）仍未满足，frontier 保持 06/07/58。真实模型 0、HITL 按 ADR-0004 未验、来源 oracle 全量 not-run，母案例族 WIRE-04 未标全量通过。

- 2026-11-10：05 结题公共记录提交 `637fc37`（05票 resolved、MM-441 与 WIRE-04 状态、NEW-16/17 登记、implementation 更新）。复核真实 frontier 为 06/07/58 三张，05 的直接后继 28（还缺 07）/64（还缺 18）仍未满足。按此前对 implement-spec Step 6 的说明，把 06/07/58 作为**同一批并行**领取并派发独立实现子代理，从同一集成 tip 各建独立 worktree/分支；主代理统筹共享边界（`cli.py` 只允许各追加独立 demo 分发、06 不动 `types.py`/`responses.py`/`sse.py`/`session/`、07 不动 `client/`、58 不动 `client/` 与 `session/`），避免多个分支各自重定义。三票均按既定 TDD、五项入口、独立 merger 复核执行；人工体验仍按 ADR-0004 集中最终 77/78/85。

## 历史接续要点（03完成后交接WorkBuddy，现已由Codex接手）

- 用户要求本会话在03完成后交接，Codex不再派发04。后续由WorkBuddy沿用本项目规则继续完整规格；[接续指南](../../docs/agents/workbuddy.md)、[可直接复制的prompt](../../docs/agents/workbuddy-prompts.md)和[项目技能](../../.codebuddy/skills/ruocun-workflow/SKILL.md)已纳入Git。主handoff依技能要求保存在Windows临时目录，正式状态以本文件和任务票为准。
- 起始基线`f199624aa2902e0519bcb1191b4b9bba18a291b8`；集成`integration/ruocun-migration`，main未改。03修复候选`90efe4f7a271c8c39f9fc6d35479bdeed6813028`及独立复核见[03票](issues/03-boot.md)。完成2/84，下一步领取[04首轮Chat流式对话](issues/04-chat.md)，前置02/03/D08/D09均已满足；先核验WorkBuddy实际代理能力，再建独立实现worktree。
- 03真实包版本/帮助/资源、18包固定Windows311开发闭包、五入口和offline4已验。修复后默认pytest29通过/3来源CLI取消选择；Ruff、mypy11文件、build/pipcheck及新support wheel仓库外安装通过。四个真实owned-child故障/取消边界另有独立wheel-only脚本复验。原来源12输入未变，修复轮不重复；所有失败原字节保留。普通Agent仍以69明确未实现，其余六suite非零not-run，不是全量通过。
- 03首轮独立复核`25c56bc`暴露communicate OSError后无kill/wait却声称joined的缺陷；修复候选已完整保留该失败。详见[首轮](integration-evidence/03-boot/README.md)及[独立修复轮](integration-evidence/03-boot/r2/README.md)。这属于开发驱动P-01，不是原版故障；完整参数/提示词路由在后续实现。
- D22安全停止候选`319923eb4fbd64a0db43aabf143eeae8041f4cb3`，`impl/d22-token-psec` / `.worktrees/i22`，Git clean、尚未合入主集成且待独立复核，本票保持claimed。实际报告/资源状态/最小下一步见[22票检查点](../ruocun-discovery/issues/22-windows-token-psec-experiment.md)。组合cmd能启动，restricting SIDs/删权保留，但NEW_PROCESS_MIN位未保留；组合Python/B/C未运行，严格安全目标未达到。先独立只读复核候选，不把pytest或run.py当只读检查，不重复扩大试跑。
- D10公共平台已resolved，不等待未使用的完整沙箱即可实施公共Shell/终端端口；D12/60/61/最终门禁仍受D22真实结果约束。04显式保留D09，13/18显式保留D10；84任务与完整安全目标不减。
- D08/D09已收录并resolved，[ADR0005](../../docs/adr/0005-runtime-storage-compatibility.md)固定单业务loop、专属DB线程、独立runner、IPC helper和唯一StoragePort。工程品牌/数据身份、显式只读兼容source map、各loader优先级和RUOCUN/DAO变量规则直接沿用，不再重新定义。
- D11的374项测试资产/805来源映射、D21最小工具链已定。D21当时仅metadata的Ruff/mypy，已在03真实安装执行；历史被拒复合helper未重试。完整发行支持仍由D12决定，不用开发pin代替发布支持范围。
- D07标准包/onedir局部验证已接收，报告实际在根`integration-evidence/d07/README.md`；onefile4551为ENV未证实，无Python干净VM和完整产品包未验。D17独立用例后审计hook异常使总体exit1，不能写独立全绿；补审计与未验保留。D18/D19二次修复后的独立证据已收录，不能以早期失败候选结题，参照各决策票。
- D20原生PSEC的outside WRITE_DAC/真实ACE修改成功是目标FAIL，D22尚未修复该证据缺口。原D17/D20跟踪字节保留；没有安装组件、改全局ACL或削弱目标来取得成功。
- [ADR0003](../../docs/adr/0003-mcp-unknown-outcome-no-replay.md)：MCP未知结果不自动重放；[ADR0004](../../docs/adr/0004-final-batch-human-acceptance.md)：人工统一最终77/78/85。不逐票要求用户操作。i06可能仍有真实WT原型/草稿/未提交HITL记录，保留窗口/worktree，接手时核实，不自动kill或清理。首组仅用户回复正常，其余待最终，不回填产品WT通过。
- 来源Node22仅6文件190断言/12驱动通过；Node24原生退出归ENV，不是全量来源215文件或产品通过。所有证据区分来源、产品自动、真实模型和终端/HITL；当前真实模型调用0。
- D07曾有真实token进入工具输出，明文未入Git，已隔离/脱敏并告知用户建议轮换，无法声称已轮换。见[事件记录](integration-evidence/log-environment-incident.md)。禁止读取隔离DPAPI日志、复述秘密或输出父环境；测试使用白名单/合成HOME，产品Hook/MCP父环境兼容另以合成环境验证。
- Temp pytest-1612、i17/run、m17若干私有缓存和D22 ignored字节码缓存的清理曾被自动审查以blocked by policy拒绝，均保留，不换入口绕过。Git clean不是磁盘全清。仅清理本次创建、已合入且无未保存工作的worktree；历史研究、失败setup脏worktree、公开只读Node缓存与有活动程序者保留。
- 本会话实现/实验代理均交回保存点后才结束；D22候选不是活动执行授权。WorkBuddy接手时重新核对实际HEAD/分支/Git状态，创建自己的新会话/代理，不能依赖Codex内存中的agent ID。最终全量code-review固定基线`f199624`，尚未到执行时机。
