# 查清 Windows 系统能力与隔离后端的可行边界

Labels: wayfinder:research
Mode: AFK
Status: resolved
Assignee: Codex/windows-capability-research
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [查清终端与 Windows 缺口、测试资产及交付候选](04-terminal-platform-delivery-research.md)

## Question

冻结版本明确缺少的 Windows OS 沙箱、系统定时、凭据、唤醒锁和剪贴板图片，分别有哪些可由 Python 对接的 Windows 后端？尤其 OS 文件/网络隔离应如何界定实际能力，避免把进程树管理当成隔离？

## 依据与边界

来自 [终端、Windows 平台、验证资产与交付候选研究](../research/04-terminal-platform-delivery.md) 已能精确表述的平台缺口。
核心 Python、允许替换底层语言绑定、Windows 补齐及 Linux/macOS 后续实机验收均已确定，不重新询问。
只读调查 Windows 官方 API、平台/版本前提及可行第三方后端，不安装、运行探针或变更系统配置。

## 完成条件

- 对照来源 sandbox 的文件/网络限制和审批语义，区分 Job Object、restricted token、AppContainer、Windows Sandbox/容器及其它有依据的后端能提供的边界。
- 记录系统版本/edition、权限/虚拟化或外部依赖条件，不将“未实现”替换成宣称支持。
- 为 cron 到 Task Scheduler 的触发语义、时区/DST、漏触发、并发和升级后路径给出候选及必须验证的范围。
- 明确凭据、唤醒锁、文本/图片剪贴板和通知的 Python 端口候选、错误和生命周期。
- 提出最小原生 Python 实验场景、环境隔离和恢复步骤，供系统能力探针票执行。
- 仅在事实证明既定目标存在新的范围冲突时向用户提问，其余记录证据和方案。

## Assets

- [终端、Windows 平台、验证资产与交付候选研究](../research/04-terminal-platform-delivery.md)
- [Windows 系统能力与隔离后端的可行边界](../research/16-windows-capabilities.md)
- 本地研究分支：research/ruocun-windows-capabilities；提交：1a6329dad33e3a6ea3703a5f15b6273ab74afbfb。

## Comments

- 2026-11-05：首轮研究将 Windows OS 隔离与其它平台缺口从笼统适配中分离，先认领后委派新的本地只读研究分支。
- 2026-11-05：官方依据和冻结源码研究已完成并收录，没有运行系统探针、安装依赖或修改系统设置。

## Answer

已区分 Job 进程治理、restricted token/ACL、AppContainer 及基础设施隔离候选；原生后端可研究，但等价边界仍待真实文件/网络尝试验证。
系统定时需要显式 cron 方言、重叠/漏触发、登录身份和升级路径；凭据、唤醒锁、剪贴板与通知有对应 Python 端口候选。
报告给出 11 组探针的输入、预期与清理，并记录旧后台路径的静态 fail-open 差异。候选前提尚未构成需要改变既定目标的新范围冲突；平台路线须等待探针后收口。
