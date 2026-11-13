# RuoCun

始终使用中文交流。

排程、启动和接续读取[下一轮 24 小时计划](.scratch/ruocun-next24h/plan.md)和[实施进度](.scratch/ruocun/implementation.md)。

## 协作方式

- 开发代理（Codex/WorkBuddy）负责既定任务的编码、调试、自动测试和交付证据。
- 用户负责需求与架构取舍、范围变更及体验验收。
- 已确定范围内的实施由开发代理连续完成。
- 需要改变既定目标或关键行为时，先提交具体方案供用户决策。

## 开始工作

1. 读取根目录 [CONTEXT.md](CONTEXT.md)。
2. 按 [docs/agents/domain.md](docs/agents/domain.md) 读取相关 ADR。
3. 读取当前任务票、规格及对应的迁移和验收记录。
4. 检查当前分支、Git 状态和已有改动。

安排迁移批次、并行实施、独立复核或接续冲刺时，读取 [48小时冲刺计划](.scratch/ruocun/sprint-48h.md)；当前执行授权和停止边界以 [实施进度](.scratch/ruocun/implementation.md) 为准。

领取和验收任务时读取[当前范围](docs/adr/0014-terminal-and-scope.md)及[批次与验证规则](docs/adr/0010-selected-scope-and-lean-workflow.md)。依赖工具尚不识别 `scope` 时，派发前按当前范围显式过滤。

选择批次、接续上下文、验证和构包时点时，按[里程碑执行规则](docs/adr/0015-batch-validation-and-packaging.md)组织普通同领域5–8票，增量交接并复用已绑定证据。高风险接缝独立复核后供下游消费。

使用 WorkBuddy 接续时，读取 [docs/agents/workbuddy.md](docs/agents/workbuddy.md) 和项目内的 [ruocun-workflow](.codebuddy/skills/ruocun-workflow/SKILL.md)；规则仍以本文件及既有项目记录为准。

## 实施与交付

- 参考 DAO 用于读取、运行对照和分析；项目产物写入 RuoCun。
- 参考 DAO 目录保持只读；需要产生运行产物的对照在独立临时副本中进行。
- 修改前确认对应模块的职责、调用关系和兼容要求。
- 日常变化更新任务票和批次记录，关键行为决定及时记录。模块对应表与验收矩阵在里程碑统一汇总。
- 分别记录实现状态、自动测试结果和用户体验验收结果。
- 测试与复核按 [ADR-0009](docs/adr/0009-source-test-baseline.md)：以DAO已有测试语义迁移为基线，保留已有证据，修复已确认缺陷，不主动堆叠额外测试。
- 测试、构建和验收进程从明确的环境白名单启动，HOME、配置和会话指向合成工作区；需要继承环境的契约用合成父环境验证。
- 日志、异常和pytest参数只保存经审查的合成值；提交及展示失败日志前检查秘密泄漏。发现敏感材料时先隔离、脱敏并保留处理说明。
- Windows 终端体验需要真实 Windows Terminal 操作与缩放验证；无头测试或 PTY 结果只能作为部分证据。
- 使用 worktree 时，从已包含项目记录的提交创建；当前任务的代码和记录一同提交。

## Agent skills

### Issue tracker

采用本地 Markdown；规格和独立任务票位于 .scratch/<feature>/。
读取 [docs/agents/issue-tracker.md](docs/agents/issue-tracker.md)。

### Domain docs

采用 single-context：根目录 CONTEXT.md 与 docs/adr/。
读取 [docs/agents/domain.md](docs/agents/domain.md)。
