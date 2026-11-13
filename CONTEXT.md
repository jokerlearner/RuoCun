# RuoCun 项目上下文

2026-11-13后续[摘要原始前缀复用](.scratch/summary-prefix-20261113/delivery.md)实现、定向自动与独审、真实硅基流动对照通过：新三组首次摘要加权98.2162%，固定B-r3旧控制器0%；固定候选包summary-prefix-b1已生成。原始连续历史含图片/Hook/Todo，本轮47次API按峰价估算¥1.57135704。日常入口仍为下述B-r3，未自动切换、未Git提交；受控摘要指标不是永久缓存保证。

当前状态：原迁移[最终批次](.scratch/ruocun-next24h/batch-final.md)79/79已交付；后续B方案的B-r3已按用户授权更新到现用桌面入口，原配置保持、6会话备份升级，启动/压缩/重启回查通过。[当前部署](.scratch/deepseek-compaction-20261113/deploy-current.md)。原生配置、产品文案和历史Windows体验见[发布说明](docs/release/batch-09.md)。B新增命令的视觉/缩放体验另保持待验。

上一里程碑：批次05的26、46、51–54通过来源定向自动测试和独立复核，有效进度53/79。固定包b05-r1已通过集中全量（1621通过、3未选）、隔离安装及262成员字节绑定；整体终端体验归77/78。

接续安排：[批次04](.scratch/ruocun-next24h/batch-04.md)记录代理编排、长任务和 Hooks。上一批真实终端技术复验见[b03-r1](.scratch/ruocun-next24h/evidence/batch-03/integration/README.md)。当前状态见[实施进度](.scratch/ruocun/implementation.md)。

此前里程碑见[批次05](.scratch/ruocun-next24h/batch-05.md)。会话管理、Monitor及完整MCP接入/未知结果保护已集成；[固定包出口](.scratch/ruocun-next24h/evidence/batch-05/integration/README.md)单独记录实际全量与安装结果。用户已确认普通同领域5–8票、固定会话增量交接和大型文档里程碑汇总，模块沿现有对应迁移。具体执行和验证按[ADR-0015](docs/adr/0015-batch-validation-and-packaging.md)。用户可协助真实终端技术操作，整体体验归最终验收。

上一批交付：[批次06](.scratch/ruocun-next24h/batch-06.md)，[固定包证据](.scratch/ruocun-next24h/evidence/batch-06/integration/README.md)。70/71真实依赖已补齐，本批未提前结题；其它未选票等待后续排程。

上一批交付见[批次07](.scratch/ruocun-next24h/batch-07.md)及[固定产物证据](.scratch/ruocun-next24h/evidence/batch-07/integration/README.md)。

当前交付见[批次08](.scratch/ruocun-next24h/batch-08.md)及[固定产物证据](.scratch/ruocun-next24h/evidence/batch-08/integration/README.md)。

## 项目定位

RuoCun 是以 Python 实现、优先支持 Windows Terminal 的终端编码助手。
用户个人维护本项目，主要用于学习有代表性的主流 harness 设计，重视清晰职责与低维护复杂度。沙箱讨论已收口：保持现有实现，暂不做 Docker 或 Windows 沙箱改造，见[最终决定](docs/adr/0019-learning-oriented-sandbox-goal.md)。
账户、环境开关和扩展使用若存原生入口。当前配置边界见[ADR-0018](docs/adr/0018-native-configuration.md)，功能范围见[ADR-0014](docs/adr/0014-terminal-and-scope.md)。

项目名称统一使用 RuoCun。
Python 包名和命令名采用 ruocun，作为技术标识。

## 已确定目标

1. Codex 完成编码和测试；用户负责决策与体验验收。
2. 将 DAO 的 TypeScript 实现迁移为 Python，复现 ADR-0010 与 ADR-0014 所保留的功能、完整终端体验和关键运行行为。
3. 尽量保持原目录、模块职责和主要调用关系。
4. 核心实现全部使用 Python，允许替换语言绑定的底层依赖。外部 Hooks、MCP 等扩展按其声明的命令和协议运行。
5. Windows优先验收保留能力；本次不提供Windows系统级定时、自动防休眠或系统桌面通知。OS沙箱按ADR-0008沿用DAO能力，Windows明确不支持。
6. 配置使用若存原生入口，Skills、Hooks、MCP 等保留各自的扩展格式和协议。
7. 旧DAO会话无需迁移；保留自身正常会话与普通子代理恢复。跨重启分模型费用不保证完整，特殊fork现场材料不足时拒绝继续，具体边界按ADR-0010。
8. Linux/macOS 保留跨平台设计，实机验收后续进行。
9. 工程交付按当前范围的功能、模块、测试、文档和发布配套衡量；仅交标准Python包，不交Windows独立程序，升级采用人工停进程/备份/安装方式。保留CI和完整文档，不交成套真实模型成绩或原量化性能保证。

## 项目边界

- 参考项目：D:\java supplement\Firstcode\dao-code
- 目标项目：D:\java supplement\Firstcode\RuoCun
- DAO 参考目录保持只读。
- RuoCun 使用独立 Git 仓库。
- 保留来源代码必要的版权、许可及归属声明。
- 迁移按已纳入 Git 的规格、决策地图和任务票推进。
- 已确认行为差异：MCP工具请求可能已执行但结果不明时停止自动重放、保留未决；连接与能力发现仍可重连，见ADR-0003。
- 来源优先：不确定机制先查冻结DAO入口/源码/测试并最小适配；OS沙箱沿用其默认可选、macOS/Linux支持、Windows不支持边界，停止额外原生组件/VM评估，见[ADR-0008](docs/adr/0008-source-first-sandbox-parity.md)。已确认差异决定继续有效。
- 自动验收默认只以DAO已有测试的语义迁移与通过为基线，不主动扩建额外测试门槛；已有证据、最小缺陷复验和必要工程检查分别记录，见[ADR-0009](docs/adr/0009-source-test-baseline.md)。
- 用户已逐项批准R1、R3、W3、W5、W6、D2、D3、V1、V2的范围缩减，及Q1/Q2执行减负；未选项目继续保留。范围排除不等于实现或测试通过，定义和依赖变化统一见ADR-0010；本次不构成恢复开发授权。

## 术语

- 功能兼容：对照已登记基线的输入、输出和可观察行为。
- 扩展兼容：配置结构、发现规则、覆盖顺序、事件与协议语义兼容。
- 平台补齐：为原版的平台缺口提供符合目标行为的 Windows 实现。
- 自动验证：Codex 执行并记录的检查与测试。
- 体验验收：用户对真实终端交互和使用流程作出的确认。
- 冻结参考快照：同时固定来源提交、工作区差异和相关未跟踪源码的可校验归档，是迁移统一参照。
- 迁移决策地图：索引迁移前的决策及其依赖；完成意味着足以编写完整迁移规格。
- 工程代理规则：供 Codex 开发时读取的 AGENTS.md。
- 产品扩展规则：由 RuoCun 程序加载的配置和扩展文件。
- Shell 沙箱：若存对 Shell 命令及其子进程施加的可选系统限制；独立文件工具和扩展入口不因此自动进入该限制。
- 工作树隔离：子代理使用独立的同机 Git 工作目录组织改动；它本身不提供 OS 沙箱或远端运行。
- 模型投影：本次请求使用的系统指令、摘要及近期消息；压缩、清空、回退只改变投影。
- 原文归档：按执行范围保存的已接纳、已脱敏消息及协议/图片元数据；通过不可变身份和来源链回查，不重放历史操作。

## 记录入口

- 工作流：[docs/agents/](docs/agents/)
- 架构决定：[docs/adr/](docs/adr/)
- DeepSeek风格压缩与原文归档：[ADR-0020](docs/adr/0020-compaction-transcript-archive.md)、[B规格](.scratch/deepseek-compaction-20261113/spec.md)、[执行记录](.scratch/deepseek-compaction-20261113/execution.md)。
- 迁移基线：[baseline.md](docs/migration/baseline.md)
- 模块对应：[module-map.md](.scratch/ruocun/module-map.md)
- 验收矩阵：[acceptance-matrix.md](.scratch/ruocun/acceptance-matrix.md)
- 完整迁移规格：[spec.md](.scratch/ruocun/spec.md)
- 实施进度与接续：[implementation.md](.scratch/ruocun/implementation.md)
- 冲刺批次、文件归属与检查点：[sprint-48h.md](.scratch/ruocun/sprint-48h.md)；规则：[ADR-0006](docs/adr/0006-batched-sprint-workflow.md)
- 当前范围与执行减负：[ADR-0010](docs/adr/0010-selected-scope-and-lean-workflow.md)；覆盖旧规则中冲突的部分，不改既有通过结果。
- 已确认实现任务：[issues/](.scratch/ruocun/issues/)；依赖图：[dependencies.md](.scratch/ruocun/dependencies.md)
- 当前决策地图：[RuoCun 迁移决策地图](.scratch/ruocun-discovery/map.md)
- 统一参考快照：[快照说明与复现方法](.scratch/ruocun-discovery/reference/README.md)
- 初始迁移盘点票：[01-baseline-inventory.md](.scratch/ruocun-migration/issues/01-baseline-inventory.md)

## 当前阶段

迁移决策地图和冻结参考快照已建立，首轮四份只读研究及取消/崩溃恢复最小实验已收录；继续完成其它前置实验和技术路线收口。
完整行为规格、805个参考文件的拟对应表及全量验收案例已建立；用户已于2026-11-05一次确认pytest、统一验收驱动、Ruff、mypy、build五项新增入口，后续直接采用。尚未关闭的地图票保持原有依赖和状态。
用户已确认84张任务拆分并授权完整实施，任务02–85已发布；集成分支为integration/ruocun-migration，起始基线和接续位置见实施进度。
按前置依赖推进参考对照及技术验证，再解锁产品实现；实验结果与产品自动测试、真实模型和终端体验验收分别记录。
运行时与数据/扩展兼容路线已收录为[ADR-0005](docs/adr/0005-runtime-storage-compatibility.md)，各任务直接引用唯一契约，恢复增强按ADR-0010收缩。D12中的Windows独立产物路线已由D2移出本轮；标准Python包安装、内部runner/恢复、人工升级说明及保留范围的最终验收仍须完成。沙箱范围按ADR-0008。

正式任务03完成后曾由WorkBuddy接续；用户于2026-11-10改由Codex接手。既定目标、分工、验收和本地Git授权沿用。当前状态、未完成候选和下一张票读取[实施进度](.scratch/ruocun/implementation.md)，原WorkBuddy接续记录保留在[指南](docs/agents/workbuddy.md)。

## 已确认的验收时点

用户要求人工体验集中最终整体验收（ADR-0004），Codex先持续完成实现和自动验证；未人工验收项如实待验，不重复逐票请求用户操作。真实模型凭据和费用仍遵守既有授权范围。

48小时冲刺、Session／费用保存点及其后的暂停与恢复保留在[实施进度](.scratch/ruocun/implementation.md)历史记录。当前执行以本文顶部的连续计划为准。77/78自动技术出口与人工出口按ADR-0006分别记录，真实产品证据仍pending；最终完整交付保留人工验收。

原 84 张票保留历史编号。按[当前范围](docs/adr/0014-terminal-and-scope.md)核对排除名单、状态及依赖，再消费 frontier。
