# 确定模块对应原则与迁移顺序

Labels: wayfinder:research
Mode: AFK
Status: resolved
Assignee: /root/module_route
Branch: codex/sprint-module-route
Worktree: .worktrees/sprint-module-route
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [确定 Python 并发、任务与恢复技术路线](08-python-runtime-decision.md), [确定持久化与外部扩展的兼容边界](09-storage-extension-decision.md), [确定终端框架与 Windows 平台适配方案](10-terminal-windows-decision.md), [确定测试、回放与评估的复用门禁](11-test-replay-decision.md), [确定安装、打包与发布配套](12-install-release-decision.md)

## Question

前置路线明确后，如何在尽量保持原目录、职责和调用关系的条件下确定 Python 模块对应、允许的适配层以及以行为闭环为单位的迁移顺序？

## 依据与边界

2026-11-10：D12路线已收录，主协调按实际frontier领取。按ADR-0008来源优先、ADR-0009来源测试基线收口已有映射与顺序；不重建84票、不新增产品架构或扩测门槛。

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 来源每个模块/顶层入口均有对应原则和归属。
- 区分机械语言转换、底层依赖替换、Windows 补齐与经确认的行为差异。
- 给出依赖图、最小可运行闭环、分阶段顺序及每阶段验证入口。
- 说明 TUI、运行时、存储、扩展和发布的集成时点及回归门禁。
- 顺序能够导出可执行规格和后续独立实施票，但本票不执行业务迁移。

## Assets

[研究报告](../research/13-module-sequence-route.md)已保存，来源提交`c3a0140225db2cf113fd42a72fed4d570d5bea55`。本次停止前仅收存报告，尚未完成主协调逐项核对收录，保持claimed；不派发D14，不增加产品完成数。报告中的起点状态属于研究时点，当前状态读取[实施进度](../../ruocun/implementation.md)。

## Answer

2026-11-12，主协调及独立审查复核冻结快照、逐文件对应和当前依赖。805 个来源成员仍逐一归属，保持现有 Python 模块与调用关系。语义改写、数据复用、协议回放和评估适配按报告中的 S/D/R/P 处理。并发、存储、配置、终端、测试和分发沿 D08–D12 已确定契约推进，缺失材料或未确认执行按责任票留证。

执行顺序以当前任务图为准。ADR-0010 移出独立程序与成套真实模型评分，81 直接依赖 79。ADR-0014 补充范围排除，ADR-0015 更新批次和验证节奏。报告中的双产物、旧边数和进度属于历史。当前 84 个历史产品编号中有 79 个有效任务，77/78 自动出口已经按实证发布，人工出口仍待验。已有路线足以接续 D14。产品通过数量由实施记录维护。[当前产品图](../../ruocun/dependencies.md) · [范围决定](../../../docs/adr/0014-terminal-and-scope.md) · [验收节奏](../../../docs/adr/0015-batch-validation-and-packaging.md)

## Comments

- 2026-11-05：建图时建立；前置票闭合后领取，本轮尚未执行。
