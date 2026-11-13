# 57 共享接线首轮独审

候选 `81d98caf939d6d2d92bbdda45c4cae8bfc0bb8ed`，含 tool_audit `7cf5921b`、obs `5f7427f8`。结论：此共享切片未发现业务重放阻断；不等于最终 57 gate。官方 SDK 出口因当前机器 grpc DLL 应用控制拒绝正在窄适配，等待固定候选，不通过假 backend 冒称真实 SDK 已通。

独立定向：obs wrapper 透传/归因/脱敏、observer fault/flush、tool trace 脱敏再截断与开关/IO 失败、audit 只读范围、ordinary obs entry，共 **6 passed in 3.69s**。回执 `raw/b07-review-obs-shared/`，白名单合成环境，`sensitive_match=false`。没有重跑旧 42 或全量、构包、外部付费调用。

事实与范围：

- SafeSpan、start/activate/end/event 的后端异常均在观测边界隔离，业务主体仅运行一次；原观测 activation 退出异常时业务 ValueError 仍原样传播且 calls=1。flush 使用 daemon 独占线程并有限等待，不让挂起 observer 进入 asyncio 默认 executor 退出等待。
- 关闭时包装返回原函数；initObs(False) 在动态 SDK import 前返回。后者本轮为源码核对，最终 SDK 候选还需核其具体可选依赖行为。
- 原普通 CLI 合成请求确实执行 Write 一次并收到最终回答；main turn 下两个 LLM span 和实际 tool handler span 关联、真实 session/toolCallId 一致，tool-trace 恰一条，flush 一次。这里是 **main turn→LLM/tool span** 父子关系，不声称该单例已执行实际 Agent 父→子→父。
- 子代理源码在 runPreparedAgent 增加独立 observationScope(identity=sub/depth/task/run)，使用已有 _AgentJournal.record 的真实 RunRef；child ctx 由 replace(parent_ctx) 保留同 ToolAudit sink，实际 model 包装保持业务请求端口。此部分为源码审查，没有额外增加代理模型矩阵。
- 观测只复制/脱敏输出，原模型与工具字节不改；tool args 先整串脱敏再按 UTF-16 截断，避免凭据在截断接缝留下前缀。trace IO/脱敏失败只放弃旁路，不重执行 handler。
- `/audit` 分支不经过 pause_settled，读取被约束在 session 根；坏行/不存在文件容错，六类报告均有真实函数。skills 按全部 session 汇总沿冻结 index.ts:2155，不冒称按选中单会话过滤。原 ordinary 用例在完成回合后调用 /audit，不把它当正在执行中未暂停的实测；不暂停结论还依赖明确代码分支核对。

已通知主协调的待收口来源接口：setObsMeta({version})、status/welcome 的 requested/on/endpoint，及非空 challenger/refocuser 返回后的 reflect_fired(kind/identity/depth) 事件。候选此时没有根调用；后两者应随最终接线或 70 的母入口明确覆盖，不提前声称完整来源一致。

需要最终独审的剩余范围：固定官方可选 OTLP HTTP/SDK 出口、local collector 真实导出及有界关闭，核原 Laminar grpc→当前 Python 出口适配的来源差异；消费前述必要接口修复。普通请求/工具执行结果及本六项不因纯 SDK 出口改动而重复全组。
