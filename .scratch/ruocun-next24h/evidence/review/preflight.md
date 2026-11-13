# N24 独审接线核对

基线为 `1271687`。本记录仅含只读源码核对，候选和实际复核回执待补。

24 的冻结来源为归档 `dao-f17e189-7ac654a0dc06/source.zip` 中的 `src/permissions/gate.ts`、`classifier.ts`、`classifier_model.ts`、`audit.ts`、`perm_audit.ts`、`sanitize.ts`、`secrets.ts`，以及 `src/index.ts:979–1048`、`src/agent/loop.ts:700–707`。

- `gate.ts:139–188` 的 auto 路径只将分类器 allow 自动通过，拒绝、异常和熔断均转人工。危险请求跳过分类器。3 次连续或 20 次累计拒绝触发熔断，30 分钟计时重置，通知消费一次。Python 基线的 gate 已具这些回调契约，生产 runtime 尚未接 classify/getMessages。
- `index.ts:993–1035` 的 Stage 1 使用 64 输出 token、温度 0、关闭 thinking 和 `</block>` stop，XML 解析为 no 时允许。其它结果进入 Stage 2，4096 输出 token、温度 0，仍只允许 block=no。请求用当前实际账号、端点和模型上下文，usage 记到实际分类模型，根会话传自身 messages。模型回退缓存按 `classifier_model.ts:18–36` 处理，context/rate limit 不触发主模型回退。
- `perm_audit.ts:23–32` 将最终裁决与 rule/classifier/human 来源写入会话审计，观测失败不打断主流程。`audit.ts:13–19` 的工作区裁决摘要也是 best-effort。秘密脱敏按原 secrets 规则，实参和持久化日志需分清，避免脱敏更改执行语义。
- D10 要求实际 Shell 方言未知或解析失败时人工确认。本轮 24 在 13 之前不能把未知方言交分类器猜测放行。

18 的 Python 基线已经在 `agent/runtime.py:286–355,511–512` 通过同一个 InputBroker 接用户输入和审批。`ask` 绑定当前取消事件并在取消或关闭后返回空答案。`approval/stdin_prompt.py` 在无交互时直接拒绝，审批答案由 broker 独立缓冲，用户草稿保留。终端改造应复用 `broker_factory`，保持唯一输入 owner 和审批锁。当前 Enter 提交、多行、Esc/Ctrl+C、Ctrl+D 行为位于 `agent/input_broker.py`，2 秒双 Ctrl+C 等原票完整行为仍待实现验证。

候选独审将复用来源与现有定向测试，并核对共享入口实际装配。真实 Windows Terminal 操作、缩放和用户体验仍按各自实际证据登记。
