# ADR-0008：来源优先，沙箱沿用DAO已有平台能力

Status: Accepted
后续范围以[ADR-0010](0010-selected-scope-and-lean-workflow.md)的R1/R3/W3/W5/W6等逐项选择为准；本文件的来源优先与沙箱边界保持。
日期：2026-11-10
决定来源：用户明确“检查一下dao这个项目是如何做的沙箱，模仿他就行了，如果以后有不确定的问题，他是怎么做的，你去模仿就行了”。
Supersedes: ADR-0007的额外Windows隔离组件评估，以及原规格R-14/WIN-09中新增Windows原生OS沙箱的目标；其它Windows补齐和已确认差异继续有效。

## 2026-11-13 后续取舍

用户选择先将若存用于自己的可信项目，Windows 沙箱后置。日常 Windows 执行继续采用已交付的权限审批、进程树管理和恢复机制；Windows Sandbox、AppContainer 及其他 Windows 隔离后端列为后续候选，实施另行决定。

同轮用户批准主系统提示 A1–A5 适配。提示按真实平台说明区外读写授权和可选 Shell 沙箱，删除对所有平台笼统声称区外必被沙箱拒绝的描述。B1–B4 沿用原有语言接线、独立复核、双语重试次数及记忆开关规则。[适配决定与证据](../release/system-prompt-restore.md)

## 源码核对

活动DAO提交为`f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`；本次只读比较`src/tools/sandbox.ts`，与唯一冻结快照该成员SHA256完全相同：`2f5dbb56b15529eeaafe6fa8bd528c2e32b1e0d739412c913a78b2ebfa6ebb4f`。迁移依据仍是冻结快照，不用活动目录变更替换原基线。

| 来源位置 | 实际行为 |
| --- | --- |
| sandbox.ts:6–12 | DAO_SANDBOX严格等于1才启用；网络默认可用，DAO_SANDBOX_NO_NET=1才要求禁网 |
| sandbox.ts:41–42 | 未启用或本次disableSandbox时返回null，照常执行Shell |
| sandbox.ts:43–47 | macOS寻找sandbox-exec，生成Seatbelt配置；缺工具返回明确错误 |
| sandbox.ts:48–64 | Linux寻找bwrap，全盘只读、cwd可写、tmpfs临时目录；禁网开关增加--unshare-net；缺工具返回错误 |
| sandbox.ts:65 | Windows及其它未支持平台返回“当前平台不支持沙箱(仅 macOS/Linux)” |
| exec_shell.ts:185–189 / managed_shell.ts:176–178 | 显式启用但不可用时拒绝启动，并非把普通Shell称为已隔离 |

来源旧process_manager.ts:178–181存在错误结果退回普通Shell的分支；本项目R-16已有“请求沙箱但不可用时明确失败”的修正决定，继续保留并单列，不用“模仿”撤销既有修复。以上为源码核对，未宣称本轮实测macOS/Linux隔离。

## 决定

沙箱按上述来源能力迁移：可选、默认关闭、网络默认允许；支持macOS Seatbelt/Linux bubblewrap路由及原参数；Windows显式启用时清楚拒绝不支持，未启用时按普通受审批Shell运行。RuoCun/DAO开关名按ADR-0005既定兼容规则解析。

停止新增Windows PSEC、管理员驱动/service/WFP、VM宿主的研究或安装评估。D22以“调查收口、原严格A失败、额外目标被本决定替代”记录，不将原失败写为成功。60/61保留为来源沙箱兼容任务，改验收支持平台路由/开关和Windows不支持边界；78、发布和85据此验证诚实能力说明，不再要求原来源没有的Windows隔离后端。

命令审批、权限裁决、受管进程取消、工作区边界和其它既定Windows能力继续实施。Windows未提供OS沙箱不是“已经隔离”，不得以Job、审批或WSL结果代替。Windows原生OS沙箱不再是本轮完整交付条件。

## 后续不确定问题的默认处理

先查冻结DAO的实际入口、调用方和测试，复用已有模块职责、算法、参数和行为。能通过来源运行确认的事实由代理确认；不因缺少理解自行设计额外架构或扩大保证。TS/Python及平台绑定按实际需要做最小适配，并记录差异。

已确认规格/ADR的差异（包括MCP未知结果不重放、自身会话完整恢复）仍有效；发现来源缺陷或与明确目标的实质冲突时，说明证据和最小处理，不把已知错误默认为正确预期。只在确需改变这些明确目标时集中请用户决策。

## 影响与门禁

同步规格、60/61/78、WIN-09、模块对应和依赖图；去除D22对60及发布路线D12的旧新增目标依赖。各产品票状态仍按实际实现与测试，当前不因范围调整自动完成。Linux/macOS保留设计与后续实机验收状态，源码参数测试不等于平台实测。

已产生的D17/D20/D22失败资产、ADR-0007和独立复核保留为历史依据；未安装组件，未修改日常主机或活动DAO。当前进度以[实施记录](../../.scratch/ruocun/implementation.md)为准。

## 2026-11-13 调研与简化讨论收口

用户在核对 DAO 与若存设计一致后，确认保持本 ADR 的现有沙箱实现，暂不做 Docker 或 Windows 沙箱改造。最终决定见 [ADR-0019](0019-learning-oriented-sandbox-goal.md)；既有调研与候选留档，不再作为待选路线或实施待办。
