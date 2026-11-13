# 24 权限分类器候选

基线为 `1271687`，实现分支为 `codex/n24-permissions`。本候选保留 claimed，整票等待主协调接入产品、独审与集成。

分类器从冻结 `src/permissions/classifier.ts` 与 `index.ts:993–1035` 迁移。完整中英文提示保留来源文字，转录只含用户文本和工具调用。Stage 1 使用 64 tokens 与 stop，只有明确 no 才批准，其余送 4096 tokens 的 Stage 2。用户自然语言规则、动态模型与账号选择、辅助模型失败回退缓存按来源保留。API 异常向 Gate 传播，转人工或 headless 拒绝。分类拒绝计数与熔断使用既有 Gate，实际通知由主协调在正常工具批路径消费。

硬规则和危险调用继续先裁决。Windows 待审批 Shell 尚缺 13 的实际方言判定，跳过分类器并保持人工确认，独立于危险标记。来源已有同步/AST快捷路径仍等待13核对。

权限 Runtime 新增 bindClassifier 和 bindAudit。会话 trace 记录 rule/classifier/human，工作区写和执行日志记录最终准驳。审计采用原 best-effort 语义和 AUDIT/PERM_AUDIT 开关，已知会话凭据红线由绑定的 redact 回调处理，叠加冻结秘密指纹。permissions/secrets.py 复用既有 memory/secrets.py 的同一冻结实现。

验证遵循 ADR-0009，迁移 classifier、classifier_model、secrets、sanitize、perm_audit 来源断言，复用原 Gate/Runtime/权限测试。新增三文件只补本票来源断言与 Python 接线，未构造压力或排列测试。

- classifier-red 为缺模块导入失败，classifier-green1 为通过。
- audit-red 为缺模块导入失败，audit-green1 为通过。
- runtime-red 为缺 bindClassifier 接线失败，runtime-green1 为 30 通过。
- mypy1 的4项类型错误已修，mypy2及最终验证通过。
- 最终 permissions-reuse-final 为 117 通过，mypy-reuse-final 与 ruff-reuse-final 均通过。

命令与 stdout/stderr 保留在 raw。所有验证经 tools/run.py 白名单环境、合成 HOME/配置/临时目录启动，源码从当前 worktree/src 加载。命令回执秘密扫描为 false，日志人工核对只含合成值。冻结来源与候选文件 SHA-256 见 manifest.json。正常产品入口整合、独审和用户体验均待实际结果。
