# 批次 05 第 51 票普通 CLI 独立复核

固定候选 `27e94cd4`，含锁定 SDK `c6130525` 和 Monitor 权限适配 `5ec6ebec`。独立树 `src`、`tests` 与候选相同，白名单合成 HOME、配置、SQLite 会话和回环模型，无外部模型调用。运行依赖解释器沿已验私环境，只执行程序。源码用例沿根开发环境运行。最终两次退出码 0，敏感值扫描无命中。

同一普通 CLI 探针在 `87f1fac4` 的失败为 `mcp_schema_visible=False`。候选读取合成用户 mcp.json，执行独立 stdio Protocol 服务。第一轮包含 TodoWrite 和 `mcp__synthetic__echo`，真实 schema 进入模型请求，MCP initialize/tools/list/tools/call 各一次，精确回执进入第二个模型请求。服务同时验证完整受控父环境与声明 env 覆盖。[探针](b05-mcp-cli.py) · [原红回执](raw/b05-review-mcp-cli-red/command.json) · [绿回执](raw/b05-review-mcp-cli-green/command.json)

同一脚本继续从原真实会话请求 effect，服务先写计数一再断线。普通 CLI 退出 74。新调用 ID 的重开请求保持未决，未发新模型/远端调用，effect 仍为一。符合 ADR-0003，未以连接恢复作为重放许可。探针复用 D15 独立 JSON-RPC 服务，未另用 SDK 生成服务端预期。

原 `tests/test_n51_mcp.py` 三项和 `tests/test_b05_monitor.py` 一项独立通过，共 4 项，6.58 秒。验证配置整服务覆盖、单服务失败隔离、schema/null/额外字段保留、未知工具不重放、真实 Windows .cmd 启动及持有服务器句柄确认退出。Monitor 原来源定向验证 stdout 批量及尾段、persistent、TaskStop 心跳止写及超时；权限源码核对保留原 Monitor 身份，并按同一最终 ShellExecutionPlan 约束 deny、危险和未知解析。46 普通入口和重开整票另验。[回执](raw/b05-review-mcp-monitor/command.json)

51 已审范围无阻断，可供 52、53 消费。HTTP/SSE、动态能力与全传输恢复按其票后续收口，本次未构包或进行终端体验。
