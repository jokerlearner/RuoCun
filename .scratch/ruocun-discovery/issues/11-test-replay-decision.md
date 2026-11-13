# 确定测试、回放与评估的复用门禁

Labels: wayfinder:research
Mode: AFK
Status: resolved
Assignee: /root/decision_11_test_gates
Branch: research/d11-test-gates
Worktree: .worktrees/r11
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [查清完整功能、模块职责与运行时调用链](02-function-runtime-research.md), [查清 SQLite、配置与扩展兼容契约](03-data-extension-research.md), [查清终端与 Windows 缺口、测试资产及交付候选](04-terminal-platform-delivery-research.md), [用最小 Python 适配器验证扩展协议与兼容解析](15-extension-protocol-experiment.md)

## Question

如何把来源测试意图、协议 fixture、回放脚本和评估工具转为 Python 迁移的验证门禁，既覆盖行为等价性，又区分自动测试、真实终端体验和真实模型评估？

## 依据与边界

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 将每类来源测试/脚本映射到直接复用、适配回放、语义重写或评估协议保留。
- 给出测试入口、环境和是否依赖网络/模型/系统功能。
- 明确 Windows 必验清单、稳定回归集和跨平台后续矩阵。
- 保留评估样本来源、判定协议和答案隔离，不复述历史成绩为 RuoCun 成绩。
- 对来源已有缺陷区分静态可疑、实测行为和文档承诺；经过核验后再确定测试 oracle 与差异处理，不能直接复制缺陷为正确性标准。
- 按 TUI、非 TTY 和 headless/CLI 入口分别登记命令能力、大小写与路由；菜单可见项、动态扩展和固定实现分别建立 oracle，入口统一不能被当作无记录的机械迁移。
- 规定失败、不支持、跳过和未验证的记录方法。

## Assets

已确认输入：[完整规格的测试决定](../../ruocun/spec.md#t-03--已确认的新增测试入口)、[已解决的入口确认票](../../ruocun/issues/01-test-entrypoints.md)。
- [完整复用门禁](../research/11-test-replay-gates.md)、[374项逐资产清单](../research/11-test-replay-gates.assets.json)、[静态校验](../research/11-test-replay-gates.validation.json)。
- 本地研究分支`research/d11-test-gates`，提交`8db1064e83bacce15195c93f1a2328b5ccdf8062`；主代理收录资产，未合并/推送研究分支。

## Comments

- 2026-11-05：建图时建立；前置票闭合后领取，本轮尚未执行。
- 2026-11-05：用户一次确认pytest、统一验收驱动（oracle/offline/runtime/protocol/live/terminal/install）、Ruff、mypy、build全部五项入口。后续直接采用，无需重复询问。此决定不关闭本票的协议实验前置或其它复用门禁，本票Status仍为open。

- 2026-11-05：D15已resolved，前置全部满足，主代理领取交fresh只读研究代理。研究分支本地保留、不合并，报告由主代理收录；入口确认及人工最终集中验收不重问。

## Answer

已明确D/R/S/P处置、入口/环境/责任任务与放行规则。374资产涵盖215测试、58脚本、16任务和85独立fixture；来源805成员字节校验、各资产拥有任务/锚点完整。52固定命令、49菜单、11非TTY与动态发现分别建立oracle。

沿用已确认五入口与统一验收驱动；离线、协议、真实进程/存储、Windows、终端、live和安装分层留证。Node22局部来源通过、Node24环境失败、D15实测反例、ADR0003差异和静态疑点分列，不能互相替代。

评估保留RUNS默认3与实际有效timeout（源全局默认180000ms，16任务无各自timeout字段）；fix对象/refs/历史答案也从agent材料隔离。缺外部材料、live预算和最终77/78/85人工是后续执行条件，不是本票未答问题。未运行产品/真实模型/来源全套，不将资产清单记作产品测试通过。
