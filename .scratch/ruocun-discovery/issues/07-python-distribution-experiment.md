# 验证 Python 安装与打包的最小闭环

Labels: wayfinder:task
Mode: AFK
Status: resolved
Assignee: /root/decision_07_distribution
Branch: impl/d07-distribution
Worktree: .worktrees/i07
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [查清终端与 Windows 缺口、测试资产及交付候选](04-terminal-platform-delivery-research.md)

## Question

在发布路线定案前，Python 包安装和独立分发候选能否在 Windows 上完成包含终端依赖、SQLite 与资源文件的最小安装、启动和卸载闭环？

## 依据与边界

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 先验证 wheel/sdist 在干净虚拟环境的安装、ruocun 命令、包资源和启动错误行为。
- 为有依据的独立分发候选制作最小 Python 探针，不提前编写产品功能。
- 用包含中文与空格的路径验证启动，记录 PATH、凭据后端和 SQLite/解析资源的查找。
- 验证升级/卸载对配置和 RuoCun 自身数据的保留约定；使用实验数据。
- 记录构建平台、Python 版本、架构、产物大小和依赖；交叉构建不记为其他平台实机验收。
- 对尚需最终 TUI 选型才能验证的部分保留明确条件。

## Assets

- [候选分发实验及证据](../experiments/distribution/README.md)，候选`fc2fd117576e8872cc1a9f5fd327464bf6f2710e`。
- [独立分发复核](../../../integration-evidence/d07/README.md)，接收tip`0ccebb07ccfb68b78e6f1c9bb956229f70816607`（此报告保留在根integration-evidence/d07，按实际路径引用）。

## Comments

- 2026-11-05：建图时建立；前置票闭合后领取，本轮尚未执行。

- 2026-11-05：按已满足前置领取。仅做隔离分发探针，默认真实人工体验按ADR-0004后置最终；终端自动候选与已修复SQLite技术输入已具备，不提前声明产品/干净VM验收。

## Answer

标准wheel/sdist及Windows onedir候选可供D12路线选择。独立环境按hash锁重新构建、sdist/direct wheel字节一致；5 passed/1 skipped，仓库外中文空格新venv的18命令覆盖离线安装、错误码、升级失败保旧、成功升级和卸载保留合成配置/DB。onedir实际父子固定SQLite运行库、资源/D06底层导入、worker/restart/协作取消通过，12个去重runtime由retained handle核对PID/创建时间并确认exit0。

onefile初始共享解包故障已留安全环境red；修正产物被系统策略4551拒绝，保持ENV/未证实，不绕过或把skip算green。D12可选已有证据的onedir，不要求未确定的onefile成为必选形态。Python仅实测3.11.9/x64，最低版本/OS和正式依赖仍由D12收口。

本票是分发最小闭环，不是完整产品包、无Python新机、产品schema升级/runner恢复、全扩展/parser或最终WT验收。早期敏感日志处理见本票报告及项目事件记录；明文未入Git。缓存和合成fixture保留复核，无活动受管进程。
