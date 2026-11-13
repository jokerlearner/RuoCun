# 用最小 Python 探针验证 Windows 平台能力

Labels: wayfinder:task
Mode: AFK
Status: resolved
Assignee: /root/decision_17_windows
Branch: impl/d17-windows
Worktree: .worktrees/i17
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [查清 Windows 系统能力与隔离后端的可行边界](16-windows-capability-research.md)

## Question

哪些 Windows 后端能够在当前支持环境中实际补齐既定功能，并具备可验证的权限、失败、取消和清理语义，从而支持平台路线定案？

## 依据与边界

以平台后端研究选出的最小候选为输入，探针保存到 discovery/experiments/windows/。
使用实验目录、合成凭据和独立命名的临时系统任务，记录其标识与清理；操作前后保留当前剪贴板状态。
本票不实现产品平台层，也不代替真实 Windows Terminal 和用户体验验收。

## 完成条件

- 对隔离候选分别验证实验根内外文件读写、真实本地回环网络、子进程继承、取消和清理；允许与拒绝用实际尝试证明，不能用 Job 创建成功当文件/网络隔离通过。
- 对当前 Windows edition 不具备的前提明确记录；不能用 WSL/Linux 容器结果替代本机能力结果。
- 系统定时探针覆盖创建/查询/修改/删除、实际触发、时区与路径引号；cron 映射的可支持范围需有依据。
- 读回定时任务最终配置，验证并发策略、时限/电池默认值及补触发语义；登录/网络测试按官方限制与实际 TCP/HTTPS、UNC/代理、凭据库访问分别记载，不外推未做的试验。
- 凭据探针验证写入/读取/删除、拒绝或服务不可用、不同 profile 隔离和失败兜底；只用合成值，日志脱敏。
- 唤醒锁验证持有线程、释放和嵌套生命周期；文本/图片剪贴板验证中文、RGBA、尺寸限制和失败回退；通知失败及不弹多余窗口可观察。
- 记录环境、API/依赖版本、执行脚本和每个能力的结果，保留不能等价部分供平台决策票处理。

## Assets

- [Windows 系统能力与隔离后端的可行边界及 11 组探针设计](../research/16-windows-capabilities.md)
- 实际脚本、输出和清理证据待执行后链接。

- [候选实现与限定结果](../experiments/windows/README.md)，候选`dc049ed0acf19e4f3adbc983d18a8cc2d17a44db`。
- [独立复核及原始证据](../../ruocun/integration-evidence/d17/README.md)，接收tip`41a7981a5a1afdaee154ca0265e92e6dfeaf72fa`；其审计入口错误及未验边界原样保留。

## Comments

- 2026-11-05：为真实 Windows 缺口建立最小验证入口；本轮尚未执行。

- 2026-11-05：已满足前置，主代理领取交fresh实验子代理。自动实证优先；人工体验依ADR-0004集中最终，未验如实保留。

## Answer

本票最小系统能力调查技术收口，不能读作Windows产品功能完成。候选两轮专用10项通过；独立一轮10个用例执行完成后附加审计hook报错，pytest整体exit=1，**不记独立全绿**。随后仅修正审计并对已记录对象只读核查；原104项hash一致、无敏感环境值匹配，候选字节未改。具体身份、环境适配字节差异、清理和未独立核查类别见复核报告。

AppContainer有私有根文件限制、三代继承/Job取消和外部网络开关实证，宿主回环/自身回环、广泛主机读取和工具链尚非等价；write-restricted初始化失败。定时真实触发/配置读回/手动并发、合成凭据、固定线程唤醒及通知API/callback有各自限定证据；clipboard写入、真实服务拒绝和最终画面等未验如实交产品门禁。

不采用任何隐含沙箱降级，新[原生ProcessContainer实验](20-windows-psec-experiment.md)承接准确前置。剩余人工按ADR0004统一最终77/78/85。系统对象与进程已按所列证据清理；私有磁盘目录删除被自动审查以blocked by policy拒绝，目录保留，未换工具绕过。
