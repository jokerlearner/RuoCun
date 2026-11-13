# 51 Stdio MCP

冻结参考 dao-f17e189-7ac654a0dc06，src/mcp/mcp.ts:19–89,137–224、src/mcp/mcp.test.ts:12–26、src/mcp/mcp.connect.test.ts:12–88。执行边界沿 ADR-0003 和 D09。

- loadMcpConfig 按传入文件顺序整项覆盖 server，坏文件跳过。管理器显式传完整父环境再叠加声明 env，工作根、command 和 argv 都由配置与运行上下文取得。三个真实定向用例核对 inherited 与 configured 合成变量、中文参数、隔离坏服务和 Windows 中文空格 cmd。
- MCP 工具使用 network、原 inputSchema、suggest，固定SDK的类型校验与模型请求schema分离。API保留 $schema、nullable及额外字段。输出从实际 wire 保留text与非text JSON，只按冻结源的 content 输出。SDK自带outputSchema再次验证不参与工具输出裁决。
- 显式 JSON-RPC error 回包作为已确认错误；已进入 send_request 后的断线、超时和取消保留未知。readOnlyHint 不改变持久副作用分类，远端先写副作用再退出的fixture只记录一次效果。连接与工具发现隔离失败，工具请求不透明重连重放。
- SDK为 mcp==1.30.0，公共 send_request 显式60秒deadline，进度不会重置超时。Session与transport在同一拥有者任务进入/退出，实际 Windows服务HANDLE在close返回时已signaled，原stdio日志确认stdin-eof。配置类型、传输和闭包在本票先覆盖stdio，HTTP与完整能力分别归52/53。
- 原模块不存在时定向测试红。Windows cmd的额外列表引号包装先失败，改为固定SDK原生启动后绿。3项定向通过，Ruff与Mypy通过。新下载pydantic_core2.50.4被本机应用控制阻断，沿已有D15固定2.50.2及pydantic2.14.2后通过，精确wheel摘要见sdk.json。私装Mypy本机同样被阻断，最终使用根已验Mypy并指定私有SDK环境检查。
- 普通模型入口及持久化组合由主协调验证。工程命令使用tools/run.py白名单合成HOME，无外部服务或模型调用，没有构包。
