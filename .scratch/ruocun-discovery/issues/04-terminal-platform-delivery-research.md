# 查清终端与 Windows 缺口、测试资产及交付候选

Labels: wayfinder:research
Mode: AFK
Status: resolved
Assignee: Codex/platform-research
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [冻结可复现参考快照](01-reference-snapshot.md)

## Question

冻结快照的终端输入、粘贴、中断、缩放与渲染由哪些层负责？Windows 有哪些实际缺口？原测试、回放、评估和发布资产如何服务 Python 迁移，哪些终端及分发路线值得最小验证？

## 依据与边界

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 对照 TUI、stdin/终端报告、本地 Ink patch、通知/焦点/唤醒锁、进程与系统定时、凭据等 Windows 相关入口。
- 按可直接复用数据、可跨语言回放、需语义移植、仅保留评估协议分类原测试/脚本/评估工具。
- 给出原 npm scripts、CI、构建、安装和发布的真实入口与平台限制。
- 以当前官方资料比较至少 prompt_toolkit、Textual/Rich 和 Windows 原生输入适配的候选关系；支持声明不视为实测通过。
- 提出 Python 工具链与打包候选，给出实际 Windows Terminal 与分发最小实验方案。

## Assets

- [终端、Windows 平台、验证资产与交付候选研究](../research/04-terminal-platform-delivery.md)
- 本地研究分支：research/ruocun-platform；提交：1d844fd07756b2c98503a45f50f33b4b2c7c5c1f。

## Comments

- 2026-11-05：建图时先认领，委派本地独立 research 分支进行只读调查。
- 2026-11-05：研究报告已本地提交并由主会话收录；没有安装或运行候选库、来源测试或 TUI。

## Answer

已登记内联终端、输入所有权、粘贴/中断/缩放与图形层的来源行为，并区分 Windows 已实现分支、明确缺口和静态平台风险。
报告给出 215 个测试文件、58 个脚本、16 个实际评估任务及 85 个独立 fixture 的完整清单与复用分类，列明真实发布和 CI 限制。
prompt_toolkit 为优先最小实验候选，Rich 为内容层候选；Textual 的 Windows inline 限制来自官方资料，尚无任何候选实机验收结果。
OS 隔离等 Windows 系统缺口已形成 [查清 Windows 系统能力与隔离后端的可行边界](16-windows-capability-research.md) 和 [用最小 Python 探针验证 Windows 平台能力](17-windows-capability-experiment.md)。
