# 02 — 依赖查询区分历史任务与当前交付范围

Type: task
Status: open
Assignee: none
Blocked by: none
用户体验验收：not-required

来源：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md) 与 [ADR-0014](../../../docs/adr/0014-terminal-and-scope.md)。本工程票不计入产品任务，工具适配待实施。

## 已确认的适配范围

- `issue_graph.py`当前忽略scope，原84票计数及frontier不能直接用于缩减后的派发。
- 识别图和票中一致的 `excluded` 标记。当前排除 20、37、50、75、80。它们保留原状态，退出可派发 frontier。分别报告原始历史数、当前有效数、排除数及真实完成数。
- 保留已收录的自动出口证据、Git/hash/矩阵检查、其它硬依赖及85人工门禁；scope未知、重复或图/票不一致时对相关任务明确阻塞。
- 外部前件仍按图；普通批内连续实施许可由主协调按ADR-0010记录，不能用新状态字符串绕过关键接缝或把候选对外放行。
- 沿既有工具与验证入口做最小适配，定向复用既有工具用例验证当前范围过滤与真实计数。

适配前主协调按当前 ADR 显式过滤并记录，再核对保留票的真实前置。
