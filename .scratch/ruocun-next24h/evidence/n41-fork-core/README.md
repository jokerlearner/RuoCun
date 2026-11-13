# 41 Fork 上下文与精确工具目录

- 冻结 DAO `f17e189`，`source.zip` SHA-256 为 `1f8308959d8b9ac0783b6ce6ddbffe7a71cc60bc59332f309f0d62083efac078`。依据 `src/agent/fork_agent.ts:18–25,47–141`、`src/agent/fork_agent.test.ts:65–93,127–168`、`src/tools/agent.ts:228–230`、`src/agent/resume_agent.ts:48–58`、`src/agent/runAgent.ts:179–191,261–264`。
- 保留来源的占位 user 文本。实际子请求沿来源清除未配对 assistant tool calls，不生成虚假的已执行工具结果。父消息深复制，子代理保留父系统提示、实际模型、权限模式和独立轮数预算。
- 父循环在本次真实模型请求发出前固定工具描述、schema、顺序和注册状态。Fork 使用独立执行池和相同 API 目录。后续父 registry 激活不影响子代理；保留 Agent schema，真实执行时由现有深度限制拒绝递归。普通空回答恢复仍沿来源既有收窄规则。
- 两项来源定向测试先因缺少 fork 模块报红，随后 2 通过。相邻同步子代理、定义和等待循环 11 通过。5 个源文件 mypy 通过，源与测试 Ruff 通过。测试以产品循环、注册、真实本地文件读取及合成模型边界验证，未发网络模型请求，未构包或跑全量。
- 本候选提供内核，普通 CLI 路由、前台及后台的持久 fork kind 和整票独审由协调者合并对应实现后验证。
