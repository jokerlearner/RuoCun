# 39 自定义代理定义候选

通过同一子执行器运行内置和磁盘代理。磁盘发现按冻结源码仅一级`.md`，从D09声明的兼容用户源、原生用户、兼容项目源、原生项目依次覆盖，随后填入未被覆盖的内置定义。`--no-skills`保留内置，禁用磁盘定义。沿用agents实际发现边界，无额外全局项目trust gate。文本解析保留name/body、工具白名单与`!`排除优先、`*`、完整模型ID与inherit、permissionMode、turn/effort、skills、memory、background/isolation、色标与提示。只识别冻结的SubagentStart/Stop命令和MCP字符串引用。当前声明Hook/MCP的角色提前报告对应运行能力尚未装配并拒绝派发。内联MCP内容不被解释为运行配置。

真实子派发采用最终定义的system/initial prompt、有效工具和计划限制、模型覆盖、轮数/effort及已加载的Skill正文。记忆目录根据user/project/local使用原生`.ruocun`路径。保留来源memory会找回Read/Write/Edit的定义级语义，父层硬限制、当前plan和外部路径审批仍生效。角色名称用于记忆路径前校验单一安全目录名。没有为记忆创建无审批的额外写入，实际Write工具创建目录并保存。定义规范SHA含有效配置字段和角色提示，留作后续继续执行时比较，不包含任何当前账户凭据。

38同步入口复用`prepareAgentRun`和`runPreparedAgent`。40可传独立取消Event、后台工具白名单、确认过的原cwd及恢复转录，选择本次独立Journal，并在模型业务轮前调用可等待的`on_boundary`。新接口不提供后台生命周期、继续授权或事件投递，交40/17原票。39同步路径对要求后台或工作树隔离的定义返回明确提示。普通CLI由root在启动时一次加载`loadAgentDefinitions`，将同一结果传给`agentCatalog(..., definitions=...)`与`createAgentRunner(..., definitions=..., user_root=...)`。

冻结解析红→绿及真实SQLite父子回合通过。通过实际模型请求边界确认同名覆盖、最终模型和调用级覆盖、已预载Skill、工具裁剪、父子模式、定义版本、实际记忆写入与plan下零写。用例同时确认声明Hook的角色零派发，子转录不含父会话正文。末轮复用38及普通父子入口既有回归，mypy、Ruff通过。仅合成输入及回环/注入响应，未重跑全量或构包。完整39状态等待root普通入口与独审。

## 子代理路径授权与记忆归属

独审发现子代理声明bypassPermissions时，区外文件回调误用子权限，导致父未授权的读取与写入实际成功。回修恢复冻结子上下文继承父审批回调的语义。子工具仍先用实际cwd解析绝对路径，随后按父路径授权裁决；每次工具派发用独立的父路径授权作用域，确保一次许可不会延续到其它子调用。子模式仍由子权限门执行。

同一用例也验证工作树切换后的长期记忆位置。实际执行目录保留子工作树，原生project/local agent memory继续由原项目workspaceRoot确定。真实SQLite及文件调用红→绿。首次明确允许的外部写入成功，后续同路径重新审批并被拒。普通区内文件写入实际工作树，父未批准的外部读取和写入均无效。4项39回归、mypy和Ruff通过。
