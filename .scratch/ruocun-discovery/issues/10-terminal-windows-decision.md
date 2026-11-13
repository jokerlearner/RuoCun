# 确定终端框架与 Windows 平台适配方案

Labels: wayfinder:research
Mode: AFK
Status: resolved
Assignee: /root/decision_10_platform
Branch: research/d10-platform
Worktree: .worktrees/r10
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [查清终端与 Windows 缺口、测试资产及交付候选](04-terminal-platform-delivery-research.md), [用最小 Python 实验验证取消与崩溃恢复契约](05-runtime-recovery-experiment.md), [用真实 Python 终端实验确定输入与渲染路线](06-python-terminal-prototype.md), [用最小 Python 探针验证 Windows 平台能力](17-windows-capability-experiment.md), [用最小 Python 实验验证原生 ProcessContainer 隔离](20-windows-psec-experiment.md)

## Question

实际 Python 终端证据支持哪一条输入/渲染路线？哪些 Windows 原生适配需要独立边界，系统定时、进程树、凭据、通知和终端模式应如何补齐？

## 依据与边界

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 使用真实终端原型结果选择或淘汰候选，列出仍未覆盖的终端环境。
- 逐项确定输入所有权、粘贴/终端报告隔离、中断/取消、缩放和退出恢复的责任。
- 说明 Windows Task Scheduler 等系统能力的映射及不能等价的语义。
- 对 OS 文件/网络隔离、凭据、唤醒锁、文本/图片剪贴板及通知分别确定平台端口和验收边界；不把 Job Object 当 OS 沙箱。
- 明确 Windows 默认 Shell、环境探测与权限解析/分类使用的方言及兼容名称，覆盖引号、管道、中文和取消语义。
- 给出 Linux/macOS 平台接口与延后实机验收项。
- 可运行原型与技术证据不足时保持阻塞；剩余人工体验按ADR-0004集中最终，不代填体验通过。

## Assets

待执行后链接研究报告、实验材料或决定依据。

- [PSEC固定来源与本机只读能力线索](../research/psec-lead/README.md)：来自本地研究分支3577c25，未选型、未运行隔离工作负载。
- [终端、实际Shell与公共Windows端口路线](../research/10-terminal-windows-route.md)，研究提交`ec1483b4737c1b4b49629fcb7725c96acfef46fe`，本地分支保留不合并。
- 完整沙箱的精确剩余问题独立移交[受限token/PSEC组合验证](22-windows-token-psec-experiment.md)，不从本票解决推定完整Windows隔离完成。

## Comments

- 2026-11-05：建图时建立；前置票闭合后领取，本轮尚未执行。

- 2026-11-05：AppContainer候选边界促成新的PSEC最小验证前置20；只读导出/版本查询成功不替代实证。按ADR-0004，D06剩余人工不再阻塞本票，原“体验未确认保持阻塞”只适用于最终产品体验门禁，不恢复逐票请求。

- 2026-11-05：D20已独立收录为“调查完成/完整后端不满足”，前置均resolved，领取平台路线研究。PSEC WRITE_DAC实质失败和AppContainer非等价必须直接处理；需要新实验/外部条件或范围取舍时给具体最小方案，不默认接受弱边界。

## Answer

后续范围修订：用户于2026-11-10明确沙箱模仿DAO，按ADR-0008保留可选Seatbelt/bwrap与Windows不支持边界；本节后续涉及22/额外Windows后端门禁的内容是旧范围记录，不再要求。公共终端/系统能力路线保持。

公共平台部分技术收口：固定ptk3.0.52/Rich14.1.0/wcwidth0.9.4内联单输入/协调输出，实际cmd默认、PS5.1/pwsh/Bash分别用真实方言parser和不可变执行计划；保留Bash外部名、原固定prompt并提供必要真实平台信息。定时短dispatcher/manifest、准确凭据来源、固定线程power、原生通知及clipboard端口/跨平台延迟绑定已明确。

本研究没有新系统实验；17本地链接与diff检查通过。59须先实测精确S4U文件/凭据/TCP/HTTPS子路径，不能从文档先替用户淘汰或选Password/service。最终人工仍77/78/85集中。

原题中的完整沙箱问题现已精确为22的最小A/B/C验证：当前PSEC真实WRITE_DAC目标FAIL，不选完整backend；公开API分别存在不证明组合支持。22与12/60/61/78/85保留真实门禁，地图整体尚未完成。13/18只需本票已定的公共路由，不再等待它们未使用的完整沙箱实现；无功能/安全范围减少。
