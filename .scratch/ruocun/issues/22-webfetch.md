# 22 — 模型按权限抓取URL并抽取内容

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_permissions
Branch: codex/b06-web
Parent: [完整迁移规格](../spec.md)
Blocked by: [09 — 按分层权限审批并完成一次文件写入](09-permissions.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

SSRF/重定向/缓存/超限及固定辅助模型抽取；成功与拒绝都有可比对结果。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-647](../module-map.md#mm-647)、[MM-649](../module-map.md#mm-649)、[MM-651](../module-map.md#mm-651)、[MM-711](../module-map.md#mm-711)。

## 共享接口与并行

接口领域：独立。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TOOL-WebFetch](../acceptance-matrix.md#tool-webfetch) — WebFetch：本票路径覆盖的子案例满足“URL 抓取、纯文本/按 prompt 抽取、缓存与 SSRF 检查；no-web 时不注册；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

[实现与来源红绿](../../ruocun-next24h/evidence/n22-web-fetch/README.md) · [独审](../../ruocun-next24h/evidence/review/b06-webfetch-review.md)。来源6项、普通真实GET/缓存/截断/当前账户抽取及失败回退已独审；--no-web无注册、无网页/抽取请求。SSRF仅源初始主机名与字面地址检查，未宣称DNS/逐跳防护或下载体积限制。主协调已验收，批末全量及安装另记。

实现候选完成，等待普通入口集成与独审。见[22证据](../../ruocun-next24h/evidence/n22-web-fetch/README.md)：6项来源定向及真实回环HTTP/响应体取消通过，Ruff/Mypy通过。冻结SSRF只检查初始hostname/literal、不做DNS或逐跳检查的边界保留；辅助模型与no-web的普通入口由主协调接线验收，不自行标整票完成。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-11：用户授权执行[批次06](../../ruocun-next24h/batch-06.md)，已核前置，领取本票；尚无通过结论。
