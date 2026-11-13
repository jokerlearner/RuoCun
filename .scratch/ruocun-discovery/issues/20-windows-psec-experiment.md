# 用最小 Python 实验验证原生 ProcessContainer 隔离

Labels: wayfinder:task
Mode: AFK
Status: resolved
Assignee: /root/decision_20_psec
Branch: impl/d20-psec
Worktree: .worktrees/i20
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [用最小 Python 探针验证 Windows 平台能力](17-windows-capability-experiment.md)

## Question

新查到的Windows原生PSEC/ProcessContainer能否在普通用户下保持所需文件与网络限制，并避免已实测AppContainer的主机工具/回环兼容边界，成为可交付的Python底层绑定候选？

## 依据与边界

沿用CONTEXT/规格及ADR-0004，不重问既定目标或逐票人工操作。
[固定来源与只读查询](../research/psec-lead/README.md)来自研究分支`research/d10-psec-lead`提交`3577c25`；Microsoft源码固定f4aa3fd。本机导出可用仅为调用前提，不是隔离通过。

只创建自己的合成目录/进程/安全环境，不安装服务驱动、不启用系统组件，不改全机ACL/防火墙、回环豁免或账户。若需要这些条件，保存具体方案供后续集中决定，不自行修改。所有子进程使用明确环境白名单，不记录真实秘密。

## 完成条件

- 使用Python窄绑定/允许替换的原生底层依赖构造最小安全环境；记录ABI、格式/版本、来源许可与绑定范围，不以Node/Rust业务代理核心。
- 真实Python及必要的主机工具读取可运行；允许根/临时目录可写，外部读/写/rename/delete/WRITE_DAC、reparse和继承handle边界分别有实际正反对照。
- 对联网/no-net分别实际尝试外部连接、宿主IPv4/IPv6 TCP/UDP回环、自身及后代回环，避免把“host基线也失败”当隔离通过；外网仅无认证合成请求，TLS不降级。
- 真实子孙进程继承限制，Job取消后PID/创建时间/持有句柄确认退出，再关闭安全环境；正常、失败和owner退出的资源所有权有回执。
- 不支持的API/请求在创建业务工作前明确失败，不回退普通Shell或较弱候选冒充成功。
- 以最小TDD保存red/green、精确脚本/依赖/OS/能力和原错误码；仅证明实际所测边界，未验列给D10/D12及产品60/61/78。

## Assets

- [只读能力线索](../research/psec-lead/README.md)。运行资产待领取后置于`experiments/psec/`。
- [真实Python PSEC实验](../experiments/psec/README.md)，候选`fc74e893ac8c8f699f6d84364ce040ae83d967d8`。
- [独立复核与已知安全目标失败](../../ruocun/integration-evidence/d20/README.md)，接收tip`9465be7c1743ff114d3194e1ced0df7afe096247`。

## Comments

- 2026-11-05：AppContainer独立实验提供有限候选，主代理补查Microsoft原生接口并只读确认可用，形成精确新前置。D17独立复核完成后领取，不提前关D10或缩小Windows范围。

- 2026-11-05：D17技术调查已收录，真实前置满足，领取最小原生隔离验证。仅限本票精确问题，不扩张成完整产品沙箱；不逐票请求用户操作。

## Answer

普通用户下纯Python ctypes/PSEC1.1能运行实际宿主Python/Git/PowerShell，并取得三代文件数据写限制、net/no-net、宿主及自身/父子回环、Job/owner退出证据。**当前RO策略仍允许WRITE_DAC及真实DACL修改，完整安全目标失败**；不是环境问题，不能把xfail算通过。严格入口在fixture/业务启动前fail-closed，未启用较弱回落。

独立最小一轮11 passed/1 xfailed（27.93秒），原75资产未改；27身份/8Job/3DACL样本及junction后审计通过，合成ACE已host读回并恢复原DACL。owner crash后PSEC服务端teardown无法独立query，仍未验。调查已回答，因此解决本票；这不是完整backend选定、产品或Windows安全通过。D10必须处理已知冲突，不能默认降级。
