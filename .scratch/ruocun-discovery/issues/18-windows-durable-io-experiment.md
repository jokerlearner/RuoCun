# 用最小 Python 探针验证 Windows 持久文件与 IPC 权限

Labels: wayfinder:task
Mode: AFK
Status: resolved
Assignee: /root/fix_d18_pending_io
Branch: impl/d18-pending-io
Worktree: .worktrees/i18f
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [用最小 Python 实验验证取消与崩溃恢复契约](05-runtime-recovery-experiment.md), [查清 Windows 系统能力与隔离后端的可行边界](16-windows-capability-research.md)

## Question

Windows 上应如何替换持久收据、处理文件占用并界定落盘保证，以及如何给 runner 的具名管道和启动材料设置可实证的访问控制与握手时限？

## 依据与边界

[取消与崩溃恢复实验](../experiments/runtime/README.md) 实测：受占用文件替换被拒绝，关闭占用句柄后可替换；当前 os.open(directory)+fsync 路径返回 EACCES。标准库 AF_PIPE 的 DACL 可读回，含 Everyone/Anonymous 条目；HMAC 拒绝错误密钥不等于 ACL 已限制到目标身份。
本票使用独立目录、合成收据和私有管道，不变更真实配置或全局安全策略。

## 完成条件

- 比较有官方依据的 Windows 文件写入/替换/flush 路径，明确文件原子可见性、进程崩溃和断电持久性分别有哪些证据；没有断电实验不承诺断电保证。
- 对共享模式占用、临时访问拒绝与永久权限错误分别给出有界重试/报错方案；失败时保留旧有效收据，不把未完成文件视为终态。
- 读回实际文件/目录/管道 ACL，验证当前登录身份可用及非目标身份的处理；身份环境不可提供时明确保留未验，不能仅凭 SDDL 文本宣布跨账户阻断通过。
- 为管道端点和能力材料设置明确权限，验证错误密钥、无响应握手、连接中途关闭、陈旧 run/epoch、请求长度及资源释放；不假定 Listener 公共 API 自带认证超时。
- 记录锁定的 Python/Windows/绑定版本、脚本、原生错误码、输入输出和清理结果；用于运行时/持久化决策，不编写产品实现。

## Assets

- [取消与崩溃恢复实验及证据](../experiments/runtime/README.md)
- [最终实验实现与事实](../experiments/durable-io/README.md)，修正候选`1860c70ad6109dbd09ac80ac7a2a118d77818012`。
- [二次修正](../../ruocun/integration-evidence/d18q/README.md)与[最终独立复核](../../ruocun/integration-evidence/d18-accepted-review/README.md)，接收tip`b8583276a24d1d7c7afa0ed27e53590e5611619b`；所有早期不接收报告/失败保留。

## Comments

- 2026-11-05：由实际文件与具名管道实验形成的新前置问题；本轮仅建票，尚未执行。

- 2026-11-05：主代理按已满足前置领取，独立worktree验证持久文件与IPC权限；HMAC、ACL文本、跨账户实际访问分别留证。

- 2026-11-05：候选14fcde3经独立merger在3c8b969复验原6项通过，874原始文件及19轮快照吻合；但静态审查发现CancelIoEx失败、等待超时/异常时可能提前释放仍pending的OVERLAPPED/buffer/event。本轮未触发该异常，不把它写成真实驱动超时。保持claimed，交fresh修正代理；原候选、merge分支和独立证据保留，未接收入统一集成。复核指针见[首次复核](../../ruocun/integration-evidence/d18-first-review/README.md)。

## Answer

Windows持久文件/私有管道的最小事实已足够供D08/D09决定。四条发布路径成功但ReplaceFileW(backup)并发读可出现错误2/32，无半JSON；共享占用和ACL拒绝均可能是5，已验证已知暂拒有界重试、永久拒绝报错、失败保留旧回执。文件flush与原生目录RW句柄flush有本机证据，不承诺断电。

当前身份文件/目录/pipe可用，匿名token实际拒绝5；独立账户未验，同用户恶意进程仍在信任边界。私有认证/run/epoch、最大帧、握手期限、半帧断开有真实进程证据；4096仅为probe限制，产品须按自身契约处理来源65536及Unicode边界。

二次修正将所有权提前到原生提交前，未确认完成时禁止释放/复用；实际worker最外finally覆盖诊断异常。最终独立18项通过（9.79秒），23worker实际PID/创建时间/held handle退出和14管道重开返回2通过。旧874/19轮与各次归档原字节审计通过；绑定旧源码的历史审计在新实现拒绝与精确旧视图成功分别保存。注入异常不冒称真实驱动超时/Ctrl+C时序。

本票为技术收口，完整产品取消/恢复、独立账户、断电和最终WT仍在各自产品票。D08/D09可解除本前置，不复用探针分数为产品通过。

### pending所有权修正附录（2026-11-05）

修正分支`impl/d18-pending-io` quiet 合入`3c8b969`后，仅修standalone durable-io：未确认完成时保留全部原生材料并停止复用，最外层原生终止后由held handle监督确认真实退出；健康完成读回实际成功／995／109结果再释放。已执行red→green，原6+新增10全量16 passed。取消／wait／GOR异常的适配注入与真实OS完成证据分别保存，未声称真实驱动取消超时。原19轮874文件、m18归档和失败轮未改，统一状态由主代理处理。详细脚本、独立预期依据及清理回执见[pending修正证据](../../ruocun/integration-evidence/d18p/README.md)，交fresh merger复核。

### 提交窗口／诊断出口修正附录（2026-11-05）

先合入fresh review证据`8c0bc48`，保留其两个未接收发现及旧73候选。新增两条回归分别red→green：原生返回997后、应用获知结果之前的异常不再提前关闭event；pending worker诊断再次抛错由整个CLI最外层原生finally终止，不能进入Python shutdown，也不能靠测试wrapper代替目标保护。原16＋新2全量18 passed；按新AGENTS使用合成HOME／配置目录。取消、提交返回、诊断异常均按真实OS／适配边界注入区分，旧874／d18p／fresh review字节不改。详细证据及清理回执见[二次修正](../../ruocun/integration-evidence/d18q/README.md)，状态与最终接收仍由主代理／fresh merger处理。
