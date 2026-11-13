# 57 可选观测与审计候选

固定核心 `21ab60f4`，HTTP/完整记忆报告 `c7bc5451`，隐式环境隔离 `41ebadfa`，会话关闭 `6709ae11`。普通运行的 main/child turn、每次模型、每个真实工具 handler 及各审计 Sink 接线由 root 独立提交。本材料不自行标任务通过。

来源 source-binding.json 绑定冻结 DAO 原版 obs/attrs/backend/init/wrap 和对应测试、memory_audit。源保留 turn/LLM/TOOL 类型、Laminar 属性、token/缓存 tag、cache_low/tool_error/reflect_fired、session/任务/run/callid 关联、关闭透传与失败旁路。缓存数据来自合成服务 usage，并非真实供应商命中率。

## Python 出口及明确平台差异

`observationScope(*, sessionId=None, identity=None, depth=None, taskId=None, runId=None, toolCallId=None)` 以 ContextVar 继承未指定字段；跨 await/asyncio.to_thread 保留关联。`spanScope(name, *, spanType='DEFAULT', input=None, metadata=None)` 配对 start/activate/end，所有观察操作隔离故障，业务体只执行一次，原异常和结果保留。`wrapRequest` 包同步 request/streamChatResilient，完整 usage 回调链不改；Python client 原接口为同步结果，非 TS async generator。普通 dispatcher 采用真实 handler scope；`wrapToolExec` 另保留源批次时长近似语义，不同时双计。

`await initObs(on, *, environ=None, redact=None, warn=None)` 默认关闭，不导入可选 SDK；`flushObs(timeoutMs=2000)` 有界刷新，`closeObs(timeoutMs=2000)` 有界关闭 provider/Session，采用 daemon 线程而非默认 executor，观测阻塞不延长 asyncio.run 的 executor 收尾。关闭不是确认远端入库。

最初 lmnr==0.7.42（官方 Apache2）必需的 grpcio cygrpc DLL 被当前 Windows 应用程序控制策略阻止，保留 raw/b07-57-sdk-init-diagnosis 红回执；未修改策略、安装系统组件或绕过。经主协调确认改官方 OpenTelemetry HTTP exporter，使用 Laminar 同源属性和其可接收的 OTLP HTTP 协议。默认从原 gRPC localhost:8001 改为 `http://localhost:8000/v1/traces`；兼容 `LMNR_BASE_URL`、`LMNR_HTTP_PORT`、`LMNR_PROJECT_API_KEY`，`LMNR_GRPC_PORT` 不再控制此 HTTP 出口。此差异不声称是原 grpc 实机通过。

SDK 动态可选三项锁定为 opentelemetry-api/sdk/exporter-otlp-proto-http==1.45.2，16项 cp311 Windows wheel 闭包/官方 URL/hash/许可记录在 dependency-closure.json 和 requirements-observation-win311.lock。不依赖 lmnr/grpc，不自动 instrumentation、不安装全局 tracer provider。

启用时还显式核这三项版本和 opentelemetry-exporter-http-transport/otlp-common==0.66b2；未装或不匹配安全降级。关闭时不查询 SDK 版本。固定版本门禁确保下面的私有 header seam 不被未经验证的新 SDK 结构静默替换。

SDK1.45.2 会自行合并进程 OTEL headers，即使 headers={}；本适配固定版本窄口在首span前替换 header map，仅留下协议头和明确 LMNR key。Resource 直接构造，独立 Requests Session 禁止 trust_env，显式 HTTP transport 禁用隐式证书/provider入口，固定压缩/采样器/队列参数。SDK 原始响应/异常日志只留固定安全提示，不回显 collector 内容。传入 redactor 与通用 secret 筛选在观察副本上执行，不改变原模型/工具参数。

## 实际回执

- tests/test_b07_obs.py 的四个压缩源案例：attrs/cache；关闭时 identity 透传、usage 回调、真父子和脱敏；observer exit 抛错不重执业务、flush 有界；关闭不导 SDK/初始化失败安全降级。与记忆报告/旧维护合计12项 passed。
- `real_export.py` 从普通官方可选闭包真实编码并发送 OTLP protobuf 到127.0.0.1受控接收器。real-export.json 记录3个实际 spans、相同 trace/正确 parent、token/tag、三个事件、会话/任务/run字段。业务 request/tool 各一次，合成私密内容不在 wire。
- 同一脚本以合成 parent OTEL resource/header/cert/provider/proxy 验证不继承；第二个 provider 无 LMNR key，真实请求没有环境 authorization/x-parent。接收器返回400并回显合成私密文本时，业务仍成功且只执行一次，SDK日志未泄漏该文本。
- 两次 close 后对应 OtelBatchSpanRecordProcessor 线程均结束，无默认 executor 阻塞；SDK Session 与 provider 在同一 shutdown 路径配对关闭。`raw/b07-57-close-real-export` 是最后该脚本回执；root 可在同一私有可选环境直接执行复核，不需再安装/开新窗口。
- 6个产品文件 Ruff/Mypy 0；最后 close 窄改5文件静态0。未全量、未打包、未使用外网模型或真实付费观测平台。

真实 SDK 编码、HTTP接收及失败行为已确认；未部署完整 Laminar 服务/UI、未证明其远程认证或入库、未替代最终包与77/78体验验收。本地 JSONL 报告与可选远端 trace 分开记录。

官方参考：[OpenTelemetry HTTP exporter](https://opentelemetry-python.readthedocs.io/en/latest/exporter/otlp/otlp.html)、[Laminar Python](https://github.com/lmnr-ai/lmnr-python)、[SDK PyPI](https://pypi.org/project/opentelemetry-sdk/1.45.2/)。具体版本支持以已下载官方 wheel 的真实代码和 hash 为准。
