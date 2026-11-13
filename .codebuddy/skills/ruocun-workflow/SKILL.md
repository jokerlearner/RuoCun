---
name: ruocun-workflow
description: 接手 RuoCun 的既定迁移任务、按依赖图实施、验证并集成，或保存开发交接时使用。
---

# RuoCun 迁移工作流

这是开发工具的项目级技能。规则的唯一入口是仓库根目录 `AGENTS.md`；规格与状态的入口是 `.scratch/ruocun/implementation.md`。本文件不定义产品的 Skills 加载行为。

当前启动、计时和停止边界统一读取`implementation.md`，模板和技能本身不构成启动授权；用户新指令及其记录优先于编制阶段的历史快照。

## 接手

1. 读取 `AGENTS.md`、`CONTEXT.md`、`docs/agents/issue-tracker.md`、`docs/agents/domain.md` 和 `implementation.md`。先核对用户本轮授权及当前启动/停止边界，再确认仓库根目录、分支、Git 状态、HEAD 和已有 worktree；保留已有改动。启动或恢复后续产品实施须有用户明确指令。
2. 读取 [ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)、当前任务票，以及规格/对应表/矩阵的相关条目；按票引用读取冻结源码及来源测试。只在当前记录不足时展开历史。冻结快照在 `.scratch/ruocun-discovery/reference/README.md`，活动DAO保持只读。

不确定设计先按[ADR-0008](../../../docs/adr/0008-source-first-sandbox-parity.md)核对DAO实际源码/调用方/测试并最小适配；已确认差异继续保留。沙箱当前按来源能力，不再派发额外Windows后端或组件/VM评估。

测试和独立复核按[ADR-0009](../../../docs/adr/0009-source-test-baseline.md)收口：优先迁移/运行DAO已有测试，不另堆故障/竞态/组合验证；已确认缺陷仅做必要回修与已有复现确认。此规则覆盖原参考及通用票据的额外扩测要求，保留源码、已有测试和失败证据。
3. 查询实现和决策图时分别记录状态。`issue_graph.py`已支持自动出口，但未识别ADR-0010的scope；恢复派发前先适配或由主协调显式过滤75/80并记录，未经范围过滤的旧frontier不能直接消费。图/票范围不一致时先处理相关项，不能虚标完成。
4. 首次在新工具接手时，依照 `docs/agents/workbuddy.md` 核实独立子代理、独立上下文、分支、worktree、后台运行和结果回收能力。能够实际派发并核对工作目录后才算具备能力；缺少能力时说明缺项及手动独立任务方案，保留用户的隔离要求。

完成条件：已核对本轮授权和停止边界、真实 frontier、集成 tip、对应原版与测试来源，以及本工具真实具备的执行方式。缺项只阻塞依赖该能力或入口的票；其它前置已满足的独立工作可按当前授权继续。

## 实施

明确获准启动后，按ADR-0010及[48小时计划](../../../.scratch/ruocun/sprint-48h.md)实施，再读取 [implement-spec](references/implement-spec/SKILL.md)。项目适配覆盖原参考的逐票fresh及旧ADR-0006中冲突规则；原参考、来源和许可保持。没有专用Skill工具时直接读取并记录适配方式；缺能力只阻塞依赖它的工作。

- 统一集成分支沿用 `integration/ruocun-migration`。普通同领域2–3票可连续实现、批末独立审查；逐票提交和证据保留。主协调记录普通批内许可、前件可运行候选SHA及来源测试结果；批内候选不对外解锁，也不提前resolved。关键存储/权限/取消/恢复与共享运行契约仍先独审集成再供下游使用。
- 同领域跨批可复用负责人、worktree及私有venv，每批核对基线、锁版本和Git状态，合并接续并保留已有候选。审查者使用独立worktree，可复用其独立环境；并行代理不共用可写venv，合成HOME/配置/会话仍按批隔离。
- 77/78的自动技术出口与79/84的消费边只按ADR-0006处理；驱动尚未适配并独立验证时，仅相关消费边沿用resolved门禁保持阻塞，不由主代理手工放行；其它独立工作按当前授权继续。85始终等待完整验收。
- 并发上限为主协调+2实现+1独立审查共4槽。主协调统筹文件归属与审查队列，优先08及其主链；减少普通任务等待，关键依赖保留。
- 实现者读取 [tdd](references/tdd/SKILL.md) 及其附件；沿用用户已确认的五项入口与既有语义 seam，见规格 T-03、任务 01，只有新增入口才集中询问。每条行为从独立预期开始，red → 最小实现 → green，逐条推进。
- 测试与构建遵守 `AGENTS.md` 的环境白名单、合成 HOME/配置及日志脱敏规则。真实模型、自动测试、真实终端、用户体验分别记证据；外部凭据和费用只有明确授权后才使用。
- 开发按受影响DAO测试/定向静态检查，集成检查点及交付候选跑保留范围已迁移全量。固定普通候选的一套产物可经源码/hash绑定后供独审复用；产品变化使旧产物失效，工程入口/资源/依赖/平台库变化和最终交付重新构建安装。V1成套live评分与V2量化性能保证已移出，本轮不恢复这些门禁。
- 实现者在自己的 worktree 修改与验证，合入最新集成分支，提交后给出 SHA、证据、未完成项与资源状态。主代理维护公共任务状态、对应表和矩阵。
- 独立 merger 使用另一 worktree 合入候选并验证。失败退回修复，保留原失败证据；通过后主工作区集成并记录实际验收范围。
- 每批只写来源/差异、逐票修改范围、实际命令结果和未验项；票引用同一回执，公共表更新相关行。75/80仍是未完成的历史排除项，其余缩减票还须实现准确能力反馈。

完成条件：每票全部条件具备对应证据、独立集成验证通过、公共记录已随提交保存。阶段性成功仅关闭本票对应路径。冲刺自动交付出口与最终用户体验出口按ADR-0006和计划分别记录；人工未验不回填accepted，完整交付门禁仍按规格和任务85判断。

## 按需参考

- 调查无法从现有记录判断的事实：读取 [research](references/research/SKILL.md)，优先源码、来源测试和官方文档，将可复用结论保存到现有研究目录。
- 设计共享接口：读取 [codebase-design](references/codebase-design/SKILL.md)，沿用 ADR-0005 的唯一 StoragePort 等契约。
- 新的领域取舍：读取 [domain-modeling](references/domain-modeling/SKILL.md)，沿用本项目单一 CONTEXT 与 ADR 约定；已确认目标不重复讨论。
- 修改代理文档或技能：读取 [writing-for-agents](references/writing-for-agents/SKILL.md)。
- 全规格完成后：读取 [code-review](references/code-review/SKILL.md)，固定起始基线见 `implementation.md`，覆盖已提交、未提交和新增文件；修复后再核对完整矩阵。
- 需要换会话：读取 [handoff](references/handoff/SKILL.md)，更新 Git 中的项目进度，在操作系统临时目录保存交接文档并给出接续入口。

本技能及原始参考的来源与许可见 [SOURCES.md](SOURCES.md)。
