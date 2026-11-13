# 批次 05 子代理专属 MCP 接缝独立复核

候选 `2a34cedf`（含专属 MCP factory、配置摘要/目录恢复和新 owner 重绑）。只修改独审证据，白名单合成 HOME、用户自定义代理定义、独立 stdlib stdio 服务和回环 HTTP 模型，无付费或真实模型调用。

该候选的 `tests/test_b05_agent_mcp.py` 实际只有 **1 项**，独立执行 **1 passed in 3.97s**。真实 SQLite 下调用写入子作用域 journal，原父 registry 不留子专属 MCP；正常子结束对端记录 stdin EOF。构建新 owner 后关闭旧 owner 的连接，新 owner 仍可真实调用；准备好的 transport 在已取消父上下文导致 launch 被拒绝时关闭，manager connectedCount 为零。[来源接缝回执](raw/b05-review-agent-mcp/command.json)

新增的[普通 CLI 探针](b05-agent-mcp-cli.py) 直接读取用户代理 Markdown 的 `mcpServers` 引用，并经 root 装配的工厂初始化同名服务器：父第一轮 TodoWrite+Agent，子第一轮真实 echo，子第二轮完成，父第二轮接收到确切子结果再完成。实际模型次序为父→子→子→父，共 **4 次请求**；stdio 对端真实 tools/call 恰一，父连接与子专属连接都记录 stdin EOF。证明普通入口确实使用专属工厂，而非仅在直接注入的源码夹具成立。[普通入口回执](raw/b05-review-agent-mcp-cli/command.json)

同一探针用独立合成会话调用 crash 工具：服务器先写 effect 一再退出，父进程退出 **74**，没有返回父模型继续生成。显式重开原会话并发送另一代理任务，仍退出 74、无新模型请求，effect 仍为一。该未知场景只有父首次与子首次 **2 个模型请求**。未将来源成功用例误报成未知路径已验，也没有用 readOnlyHint 给重放许可。

源码复核：选名配置深复制并保留 cwd/env；恢复材料绑定 mcpConfigDigest，重绑前核精确 schema 及可见目录。新 registry 使用新 handlers；原 owner 的 close 不关闭新 owner。准备失败、launch 拒绝、正常子结束及控制器退出沿各自 finally 收口，清理一个 continuation 失败时仍继续 drain task owners。后续 `2a2d9026` 只向同一来源用例补 unknown/no-parent 断言与证据，未作为本报告独立跑过的版本。

两回执退出 0，敏感值扫描无命中。当前子专属 MCP 已审范围无阻断；完整 54 的 HTTP/SSE 断线、错误分类及日志脱敏由其最终候选另行审查。没有全量、构包或体验代验。
