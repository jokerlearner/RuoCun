# 79 — 构建并在隔离环境安装完整wheel/sdist

Type: task
Mode: AFK
Status: resolved
Assignee: codex/b09-package
Parent: [完整迁移规格](../spec.md)
Blocked by: [71 — eval及禁用开关贯穿启动/文件访问/恢复](71-isolation.md), [33 — 模型按预算读取和刷新代码图](33-repomap.md), [78 — 本轮Windows能力及不支持边界最终验证](78-wincaps.md), [23 — 模型搜索网页并返回受限结果](23-websearch.md), [56 — 外部Deck面板控制同一持久会话](56-deck.md), [68 — 欢迎Sixel/终端回包与文本降级稳定](68-welcome.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

从sdist重建本轮标准Python包，在兼容Python环境仓库外/无PYTHONPATH安装，保留范围内资源/许可/SQLite可用；源码移走仍可按本轮R1/R3恢复契约运行。D2不再交付Windows独立程序；标准包的runner/helper同版本角色和后台生命周期仍须验证，不把开发仓库可运行当作已独立安装。

范围依据：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)。79本身仍在范围内，W3/W5/W6的能力报告和保留功能据实验证；V1/V2移出的评分/量化保证不作为本票通过条件。

标准包验收覆盖保留工具和完整TUI的资源及入口。NotebookEdit、自定义Markdown命令与组合插件按新决定登记为范围移出。[ADR-0014](../../../docs/adr/0014-terminal-and-scope.md)

## Context pointers

本票对78消费[自动技术出口](../../../docs/adr/0006-batched-sprint-workflow.md)，图中`dependency_exits.wincaps=automatic`及硬边保留。自动证据工具已集成c366fc7，但本轮scope排除/缩减尚待工具适配，恢复前不能直接消费旧frontier派发；78仍pending/none。只有本轮真实产品证据经独立核验且其它前置满足，才可消费技术出口；人工待验继续单列。本轮不构建产品或改写验证结果。

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-305](../module-map.md#mm-305)、[MM-579](../module-map.md#mm-579)、[MM-768](../module-map.md#mm-768)、[MM-017](../module-map.md#mm-017)。

## 共享接口与并行

接口领域：工程。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [PKG-01](../acceptance-matrix.md#pkg-01) — 标准包/源码包：本票路径覆盖的子案例满足“名称/版本/依赖/entrypoint/license/资源完整；移走源仓库仍可启动并做自身恢复”。
- [x] [PKG-05](../acceptance-matrix.md#pkg-05) — 资源与许可：本票路径覆盖的子案例满足“全部随包可读、hash/provenance与许可齐全；缺外部PNG生成源如实登记，不把注释当授权”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

[b09-r1 固定包](../../ruocun-next24h/evidence/batch-09/package/README.md)已构建并绑定。纯运行环境在仓外从实际 console-script 启动，正常退出保留后台后，以 `python -m ruocun --continue` 恢复同一运行、读出原日志并真实取消。默认 runner 和 IPC helper 的身份、版本、签名和清理经独审核对。17 项代表资源和许可匹配实际 wheel，原外部 PNG 缺口按 E-02 记录。[仓外回执](../../ruocun-next24h/evidence/batch-09/n79-probe/README.md) · [独审](../../ruocun-next24h/evidence/batch-09/n79-probe/review/README.md) · [自动前置](../evidence/b09-automatic/README.md)

最终 b09-r3 在另一全新仓外纯环境按锁安装，使用模块入口创建、分离、接管并取消同一真实 Shell，验证随包 SQLite、runner/helper 和资源清理。R1 直接 console 入口成功与本机随后 WinError 4551 分别归档。[最终固定包](../../ruocun-next24h/evidence/batch-09/package-r3/README.md) · [最终仓外回执](../../ruocun-next24h/evidence/batch-09/n79-probe/README.md#最终候选复验)

## Comments

- 2026-11-10：D2下79是本轮唯一标准包产物交付前置，80本轮移出；包资源/真实SQLite/仓库外运行及后台角色验收保留，原有自动证据要求不放宽。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
