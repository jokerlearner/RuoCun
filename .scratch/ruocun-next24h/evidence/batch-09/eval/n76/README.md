# 76 · 离线运行时与协议验收

产品验证基线 e9b6290c，评估工作树合并点 1b3c63af。Windows x64 CPython 3.11，原测试通过 tools/run.py 白名单运行，HOME、配置、会话、进程信号和本地服务均使用合成隔离环境。

| 回执 | 结果 | 来源与实际覆盖 |
| --- | --- | --- |
| runtime-offline-core | 32通过 | 冻结 verify-background-wait.mjs 和 verify-background-recovery.ts 的等待零轮询、一次启动与一次投递语义，复用 n16_wait_loop、n16_background_storage、n15_managed_shell、n17_recovery。普通 CLI 的代理等待、显式 checkpoint 恢复、fork 与消息交接复用 b02_agent_background_entry、n40_agent_tasks、n41_fork_core。Monitor 的进程终态与旧 owner 丢失，manual 不启动执行，loop 退出后不继续发请求分别复用 b05_monitor、n45_manual_tasks、b03_loop_entry。 |
| runtime-wait-modes | 9通过 | 冻结 background_runtime.test.ts 的 any/all、无关正常完成、失败/取消/注意请求唤醒、准备和保存间隙及末尾资源释放。 |
| runtime-offline-protocol | 18通过 | 普通 CLI 的已信任 Hook、生命周期和变参接线，MCP stdio/HTTP/SSE、资源/工具发现与子代理扩展，断线后的未知结果不重放，LSP UTF-16 与取消，Deck 重连，eval 恢复不重新读取禁用磁盘通道。 |

合计59通过，三个运行返回0，敏感扫描均未命中。检查了运行目录归属的 Python、Shell 和 Node 进程，结束后匹配0。既有用例保留其来源红绿记录，本批复跑覆盖组合接线。真实模型行为、真实供应商等待和终端体验按范围留待独立验证。

## R3 安装包定向复验

固定产品 8e7760cea9ad7fa7b500fccd32984f5c9813f930，wheel SHA-256 764d9f908c583de07f32f48f0618b74c0c82f273ec02ae672496efb00aedb81d。实际加载 R3 QA 环境 Lib/site-packages/ruocun。309 个已加载包成员逐字节匹配 R3 发布清单。运行器未向 sys.path 加入源码目录。

- runtime-r3-core 5通过。实际安装包覆盖普通 CLI 代理恢复和等待唤醒、等待零模型轮询及用户唤醒、未知工具结果显式恢复且不重放、Monitor 正常与失主收口。
- runtime-r3-protocol 5通过。安装包普通入口验证会话 Hooks、MCP HTTP/SSE 断线后未知结果不重放、LSP UTF-16 同步与取消、Deck 重连。
- 安装包未直接运行把源码目录形状写入夹具的旧 n15 选择器。保留上面的源码环境59项，以及安装线对仓外 Shell runner/helper 的独立证据。R3 定向两组和安装字节绑定均返回0、敏感扫描未命中。
