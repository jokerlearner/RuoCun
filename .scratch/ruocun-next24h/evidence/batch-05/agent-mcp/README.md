# 子代理专属MCP接缝

基线9ed05e72，产品5af4b613，依赖registry精确MCP visibility恢复7dea752f。来源 runAgent.ts:301–323 在普通工具裁剪后按agentDef.mcpServers引用全局配置，缺名跳过，连接失败不阻塞子代理；SubagentStart前初始化、SubagentStop后finally关闭。本轮仅现有AgentDefinition支持的字符串引用，不补内联配置解析或新传输。

AgentMcpRuntime复用既有McpManager，独立子registry/cwd/env和生命周期；factory绑定已选全局配置快照，子ctx不继承可递归派发的factory。fork exact使用原冻结父工具集合，不附加专属server。前台journal拒绝、后台launch/handoff/continue拒绝、未激活continuation.close等均释放已准备资源。

转后台和TaskSend重开在新owner新registry重建独立连接，原owner关闭后新handler仍能实际调用。重建保留精确已激活专属工具，先核全专属server schemas。恢复普通入口由主协调连接后校验已保存toolRoster，使用registry.restoreMcpVisibility精确激活存在名称。resource.definition_digest只hash解析后的专属配置和cwd（包含command/args/声明env、headers/url等实际配置），不序列化秘密值、不把无关父env波动纳入；主协调在recovery_material内绑定mcpConfigDigest并核旧材料兼容，后续固定集成复验另记。

## 定向证据

- raw/b05-agent-mcp-red：旧主线无agent_mcp装配的真实红。
- raw/b05-agent-mcp-exact-rule：真实stdio、子SQLite scope、缺名/坏server隔离、父子池独立、新owner重建后关闭旧owner仍能调用；parent取消在launch前拒绝并关闭。1 passed。
- raw/b05-agent-mcp-neighbors：原有同步子scope、后台父回执后写入/停止、显式continuation三个用例通过。
- raw/b05-agent-mcp-unknown-final：扩展同一实际接缝；无父journal身份时已连接资源也关闭。真实MCP crash执行后断线，远端effects只1，child tool保持started未配对、agent run unknown、父turn outcome_unknown/blocked，未自动重放。1 passed。

夹具早期写了未支持的工具名通配权限规则mcp__dedicated__*而被正确拒绝（无child intent），改成既有冻结精确名allow后执行；未改权限产品来绕过。实际日志均为合成值、scan_hit=false，通过tools/run.py白名单启动。无外网模型、无费用、无全量或构包。ruff及4模块mypy均通过；普通runtime组合和独审由主协调另记。

## 已装配元数据复验

合入主线2a34cedf（本树merge8637418b）后，仅复用本票同一test_b05_agent_mcp.py，`raw/b05-agent-mcp-integrated` 为1 passed、scan_hit=false。主线agentRecoveryMaterial现保存mcpConfigDigest；prepare_continuation先核定义/配置摘要、再连接实际服务、再恢复可见目录并校验toolRosterDigest，拒绝或未领走的预备连接由组合根关闭。本条只确认上述同一来源/生命周期探针在新装配源码下继续通过，不另称完整CLI恢复矩阵或独审已通过。

## Windows隔离树收尾顺序

收口源码核对发现：专属MCP服务以隔离树为cwd，须在Git移除目录之前关闭其连接。前台在完成journal.finish并保留完整toolRoster之后close，再finishAgentWorktree；后台在Stop和末次子保存之后close，再按原材料cleanup/publish。finally依旧幂等兜底，避免提前close让恢复目录被存空。`raw/b05-agent-mcp-close-order`复用同一来源探针1 passed；未另称已做新的真实Git/MCP组合实机体验。
