# 确定安装、打包与发布配套

Labels: wayfinder:research
Mode: AFK
Status: resolved
Assignee: /root/release_route
Branch: codex/sprint-release-route
Worktree: .worktrees/sprint-release-route
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [查清终端与 Windows 缺口、测试资产及交付候选](04-terminal-platform-delivery-research.md), [验证 Python 安装与打包的最小闭环](07-python-distribution-experiment.md), [确定终端框架与 Windows 平台适配方案](10-terminal-windows-decision.md), [确定持久化与外部扩展的兼容边界](09-storage-extension-decision.md)

## Question

根据终端技术及分发实验，RuoCun 应如何安装、构建、升级和发布，哪些产物及文档是完整交付所必需的？

## Answer

采用[发布路线](../research/12-install-release-route.md)，研究提交`b6de69a2155363c39cb8d330c4985763505c9404`已由主协调只收录报告并核对现有工程/实验，未整分支合并。定案为标准wheel/sdist及Windows x64 console onedir，沿Hatchling/build/已验证PyInstaller路线；保留当前3.11.* metadata，3.11.9仅验证基线；固定SQLite3.54.1实际组合及资源/依赖/许可清单，用户级版本化payload及同版本内部角色。onefile/其它架构和Linux/macOS实机保持未验，不扩成额外逐patch/故障排列门槛。沙箱按ADR-0008，不等待额外原生组件/VM；自动测试按ADR-0009。此处resolved仅表示路线收口，79–83产品构建安装/角色、最终WT和用户交付均仍按实际状态。

## 依据与边界

2026-11-10：主协调核对决策frontier仅本票可领取，全部现有前置resolved后派独立研究代理收口；按来源优先和ADR-0008整理发布路线，不新增产品能力、安装组件或调用付费模型。

当前以用户最新[ADR-0008](../../../docs/adr/0008-source-first-sandbox-parity.md)为准：沙箱按DAO能力，不新增Windows后端，ADR-0007额外组件评估被替代。本票D22旧前置已移除，保留其它已验证运行时/打包前置；不再等待虚拟机或驱动安装。

用户于2026-11-10接受[ADR-0007](../../../docs/adr/0007-windows-sandbox-prerequisite.md)：完整OS隔离可有管理员预装原生强制层，先在可回滚环境验证。主程序安装与隔离组件安装、普通用户日常运行分别验收；组件版本/签名/hash/许可、升级卸载/故障拒绝仍须实证，本票不因此解除D22及产品沙箱门禁。

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 确定 Python 版本范围、包管理/锁定、质量检查、测试和构建入口。
- 区分 Python 包安装与独立可执行分发，记录选择和支持条件。
- 说明 Windows x64/其他架构、Linux/macOS 的构建与实机验收状态。
- 纳入资源/原生依赖、许可归属、版本/变更日志、安装与故障排查。
- 此票产出发布方案，不创建远程仓库或执行公开发布。

## Assets

待执行后链接研究报告、实验材料或决定依据。

## Comments

- 2026-11-05：建图时建立；前置票闭合后领取，本轮尚未执行。

- 2026-11-05：最小开发工具链已拆为独立21，只解锁实现03，不替代本票的完整发布/平台范围；本票D09/D10前置保持，最终85经D14/D13仍须本票关闭。

- 2026-11-05：D10公共路线收口，完整安全后端及安装许可/原生组件范围的剩余问题由22承接，故新增该真实前置；不把已知不合格PSEC打成正式支持后端。
