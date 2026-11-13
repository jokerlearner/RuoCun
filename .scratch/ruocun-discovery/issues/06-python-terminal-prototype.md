# 用真实 Python 终端实验确定输入与渲染路线

Labels: wayfinder:prototype
Mode: AFK
Status: resolved
Assignee: /root/decision_06_terminal
Branch: impl/d06-terminal
Worktree: .worktrees/i06
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [查清终端与 Windows 缺口、测试资产及交付候选](04-terminal-platform-delivery-research.md)

## Question

哪条 Python 终端路线能在真实 Windows Terminal 中满足冻结快照的输入、粘贴、中断、缩放和长时间输出行为，同时保持可迁移的模块边界？

## 依据与边界

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 根据研究报告为满足既定体验的可行候选建立最小 Python 交互程序；记录候选库和版本。优先验证最小可行路线，有多个仍可行的候选时用同一操作脚本对照；官方平台限制已排除的路线不强行开展重复实验。
- 在真实、可见的 Windows Terminal 中运行；普通 PowerShell/测试 runner/PTY 不能替代该项证据。
- 用户参与中文 IME 的组合输入、候选确认和撤销；验证中文宽字符、emoji、光标和选区。
- 覆盖单行/多行/大段粘贴、bracketed paste、粘贴中包含转义文本及流式输出期间输入排队。
- 覆盖保留内联 scrollback/原生选择、文本与图片路径附件、图形能力有/无/探测失败三条路径；剪贴板图片底层能力与平台探针票衔接。
- 覆盖 Esc、Ctrl+C、前后台切换和工具运行中取消；确认程序退出后终端模式恢复。
- 覆盖窗口连续变窄/变宽、自动换行、滚动、焦点切换、终端报告回复与用户输入隔离。
- 保存可运行 Python 文件、依赖锁定、操作脚本、屏幕证据和自动检查结果；两类证据分别标记。
- 给用户展示可操作原型，并记录真实体验反馈；HITL 反馈发生前保持 open/claimed，不由代理代填验收。

## Assets

待执行后链接研究报告、实验材料或决定依据。

## Comments

- 2026-11-05：建图时建立；前置票闭合后领取，本轮尚未执行。

- 2026-11-05：主代理按已满足前置领取，交fresh子代理准备真实Python终端原型及可操作HITL材料；用户IME/体验反馈前不标resolved。

## 验收时点调整

用户2026-11-05要求先持续实施，人工体验集中最终验收，见[ADR-0004](../../../docs/adr/0004-final-batch-human-acceptance.md)。本票技术原型/自动验证及已取得反馈可独立收口，剩余原完成条件中的人工操作转实现77/78/85，不缩范围、不宣称HITL全通过。已取得第一组中文IME/emoji、流式队列草稿、缩放历史反馈“正常”；其余待最终验收。候选ad48d6c待fresh merger验证后再关闭技术票。

## Answer

按ADR-0004完成技术收口，原型ad48d6c经fresh merger接收b114609，独立14passed、依赖lock/代码绑定/源码契约/真实worker父子与两个句柄退出已核。[技术报告](../experiments/terminal/README.md)、[独立复核](../../ruocun/integration-evidence/d06/README.md)。已启动真实WT的run20261105T070656Z-49da20，用户针对第一组请求回复“正常”；本次只保留文字反馈与启动记录，不据未记录的操作推定全量通过。其余人工集中77/78/85。完整mascot/持久runner/系统图片clipboard仍由产品票实现，D06解决不代表产品UI或HITL全通过。
