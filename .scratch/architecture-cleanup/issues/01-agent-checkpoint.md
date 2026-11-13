# 01 普通子代理检查点共同规则

- Type: task
- Status: resolved
- Blocked by: none
- Scope: current
- Assignee: checkpoint implementation
- 分支：integration/ruocun-migration（当前工作树独占文件）
- 用户体验验收：not-required（保持行为内部重构；不得冒充新增体验验收）

规格与验收：[spec.md](../spec.md) 的 F1、AC1。
范围：run_agent.py、tasks.py、resume_agent.py 及确有必要的内部 helper。
保持两个 owner、锁、身份字段差异、轮次语义、脱敏和持久化确认时点。
验证证据：[交付记录](../README.md)。改前/改后19项分别通过，独立高风险复跑与两轴审查通过；全量原失败及后续复验均保留。
