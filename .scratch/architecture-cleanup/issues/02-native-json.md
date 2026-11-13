# 02 原生 JSON 读保护与共同发布

- Type: task
- Status: resolved
- Blocked by: none
- Scope: current
- Assignee: config implementation
- 分支：integration/ruocun-migration（当前工作树独占文件）
- 用户体验验收：not-required（保持行为内部重构）

规格与验收：[spec.md](../spec.md) 的 F2、AC2。
范围：settings_store.py、mcp_store.py、profiles_store.py 及必要的原生 JSON 内部 module。
保持账户版本与字段、设置文件锁、MCP 文件白名单、POSIX 及异常语义。
验证证据：[交付记录](../README.md)。改前/改后29项分别通过，独立复跑、两轴审查、构包及新包仓外安装通过。
