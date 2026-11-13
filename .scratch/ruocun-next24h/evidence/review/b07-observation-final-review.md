# 57 最终独审 gate

结论：当前批准范围内 57 无独审阻断，可供 70/71 消费。候选共享接线 `81d98caf`，来源接口 `1521ea81`、实际子 cache/记忆消费者 `9d4f0c76`，HTTP 环境隔离 `e885c68a`，真实 session close `ad36474c`（作者 `e6326b89`），最后私有 SDK 版本门禁 `1da9e684` + `5f2ef7a8`。本报告只提交独立证据，不自行更改任务状态。

独立证据按增量复用：

- `b07-observation-shared-review.md`：共享风险六项，6 passed in 3.69s。
- `b07-observation-agent-review.md`：变化后的实际 Agent 主→子→父入口，1 passed in 3.77s，子 task/run 来源与 cache.subId/depth 已核；没有重跑前六项。
- 本次原 SDK 默认关闭/安全降级单例，1 passed in 0.12s，回执 `raw/b07-review-obs-version-off/`。off 在 importlib.metadata 和可选 SDK 之前返回；开启后缺包或版本不符只按异常类名安全降级。
- 本次 `raw/b07-review-obs-real-http/` 实际官方 SDK 导出回执：exit 0、3 spans、正确 parentage、secret_absent、single_business_execution。stderr 空，sensitive_match=false。复制原单脚本到同深度 `sdk/real_export.py`，实际 source 绑定本 review 树 src，原作者结果未覆盖。结果 `sdk/real-export.json` 和当前源码 SHA 绑定 `sdk/source-binding-review.json` 可核。

真实 HTTP 观察行为：官方 OpenTelemetry protobuf 编码到自己拥有的 localhost collector，turn/llm.call/tool.Read 恰三个 span、同 trace、父 span 身份正确；导出含实际合成模型用量与 cache_low/tool_error/reflect_fired 三事件。原 business request/tool 各一次、业务字节不被脱敏改写，合成秘密不在 wire。合成 parent OTEL resource/headers/certs/client provider/proxy 没有被隐式采用；第二个无 LMNR key 的 provider 不继承 authorization/x-parent，collector 实际返回 400/合成私密 body 时业务仍成功一次、SDK日志不回显私密值。两次 close 后 OTel processor 线程已退出，backend 关闭。

最后版本门禁只新增前置条件，未改上述成功路径；按 ADR-0015 不重复 collector。只读实际 SDK 环境版本回执 `raw/b07-review-obs-installed-versions/` 核五项与门禁完全一致：API/sdk/proto-http 1.45.2、otlp-common/http-transport 0.66b2；完整可选 16 wheel 闭包沿作者 `batch-07/n57/requirements-observation-win311.lock` 和 `dependency-closure.json` 绑定证据复用。私有 exporter._client headers 窄口实际 owner 也已纳入门禁，不能任意 SDK 版本静默使用该适配。

普通接口已补齐版本 metadata、status/welcome 开启/关闭/降级区别及 endpoint、非空纠偏 reflect_fired 事件。关闭源码从 root session finally 进入 closeObs，先解绑 backend，再 daemon bounded provider.shutdown/finally session.close；保留业务异常与结果，不以观测失败重新执行副作用。/audit 六报告只读、不额外暂停，scope 与全局 skills 汇总语义沿来源；此前报告列出的接口缺口均已收口。

明确来源差异：原 Node Laminar gRPC localhost:8001 的 Python lmnr/grpcio 在当前机器被应用控制拒绝，原失败证据保留，没有修改系统策略。经主协调批准改官方 OTLP HTTP，默认 localhost:8000/v1/traces，保持 Laminar span/usage/关联属性和 LMNR base/http/key，LMNR_GRPC_PORT 不控制本出口。动态可选依赖，不做全局自动 instrumentation；关闭默认不导入它。该差异按绑定来源记录，未冒称原 gRPC 路径已实机通过。

未部署完整 Laminar 服务/UI，未证明远端认证或入库；本地 HTTP 确认与远程产品体验分开。所有运行白名单、合成 HOME/环境/输入与本地 collector，无真实/付费模型、全量或构包。后续唯一里程碑包验收与用户体验由主协调执行，不在此虚标。
