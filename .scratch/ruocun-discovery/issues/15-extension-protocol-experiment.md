# 用最小 Python 适配器验证扩展协议与兼容解析

Labels: wayfinder:task
Mode: AFK
Status: resolved
Assignee: /root/decision_15_extensions
Branch: impl/d15-extensions
Worktree: .worktrees/impl-d15-extensions
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [查清 SQLite、配置与扩展兼容契约](03-data-extension-research.md)

## Question

Python 候选 SDK 和解析器能否保留冻结版本实际使用的 MCP/LSP/Hooks 协议及配置接纳语义？哪些默认行为需要自有适配层，足以据此确定兼容边界和锁定依赖？

## 依据与边界

本问题由 [SQLite、配置与扩展兼容契约研究](../research/03-data-extension.md) 的协议事实和 E4—E8 候选实验收敛而来。
只制作选择路线所需的小探针及固定输入，实验保存在 discovery/experiments/extensions/；不实现整套产品扩展系统。
来源 fixture 仅在从 [冻结快照](../reference/README.md) 恢复的独立可写实验副本运行。

## 完成条件

- 使用受控 fixture，验证候选 Python MCP SDK 的 stdio、Streamable HTTP、旧 SSE 握手、env/header、tools/resources/prompts、elicitation、listChanged、关闭和重连默认行为；记录锁定的 major 与精确版本。
- 用副作用计数器检查断线重试，区分请求失败与服务端结果未知；未覆盖的协议场景明确保留状态。
- 使用最小 Hook helper 验证 UTF-8 stdin/env/cwd、JSON/text 输出、code 0/2/其它、超时和 updatedInput；不扩大到来源未实现的所有 Hook 类型。
- 用受控 LSP Content-Length server 验证分片/合帧、请求关联、初始化/文件同步、emoji 的 UTF-16 位置及中文/空格 Windows URI，再选择是否需要 SDK 或小型协议适配层。
- 选取配置、frontmatter、参数展开的代表性边界，比较缺失/null/空串、字段保留、同名覆盖、CRLF/LF；完整回归集由后续测试门禁票定义。
- 先依据用户已确认目标设计双品牌目录/变量的对照输入；具体别名和写入规则由兼容决策票确定，不擅自修改真实配置或凭据。
- 记录命令、版本、输入输出、来源对照结果和待决定事项；没有执行的项目不记为通过。

## Assets

- [SQLite、配置与扩展兼容契约研究](../research/03-data-extension.md)

## Comments

- 2026-11-05：只读研究揭示 SDK 默认值、协议分帧和解析语义需要实测，建成明确前置任务；本轮尚未执行。

- 2026-11-05：主代理按已满足的前置领取，分派给/root/decision_15_extensions；用户已授权独立worktree及已确认入口上的TDD。

## Answer

[扩展实验](../experiments/extensions/README.md)已接收：候选30b9299，独立merge6945f41，复验11 passed、来源805及旧144raw字节一致、helper残留0。明确SDK env/elicitation默认差异、来源断线副作用2次及Hook超时晚副作用；未验场景单列，未宣布产品兼容通过。用户已确认结果不明停止重放，见[ADR-0003](../../../docs/adr/0003-mcp-unknown-outcome-no-replay.md)。其它兼容路径/依赖仍由09票收口。
