# N1 Bash纯Python叶子解析器候选

正式协作范围为09叶子 `permissions/bash/bash_parser.py`；公共Node类型由作者1小提交48c00ff提供（本树cherry-pick eabbe29），wrapper、安全walker、权限执行接线由作者1/root拥有。本候选不修改它们，不结09或11，不改变PowerShell5.1产品执行路线。

## API与来源

`parseSource(source:str, timeoutMs:float=50)->Node|None` 及 `SHELL_KEYWORDS` 由本模块导出。Node使用已共享可变dataclass的type/text/startIndex/endIndex/children；startIndex/endIndex始终UTF-8字节。异常、每128节点检查到超时或超过50,000节点均返回None，上层wrapper按其PARSE_ABORTED合同处理，不能变成固定fallback后自动放行。

只读唯一冻结 `dao-f17e189-7ac654a0dc06` 的 `src/permissions/bash/bash_parser.ts`。完整阅读并按函数流程迁移词法、语句/list/pipeline、重定向及heredoc、引用/展开、控制流、test和算术表达式。source-map.json列出原函数与Python位置；makeLexer/byteLengthUtf8收敛为Lexer/dataclass及UTF8计数，初始化兼容封装留给作者1wrapper，不引入异步初始化或第二Node类型。

必要Python适配：内部游标按代码点前进，字节表按UTF-8建立，Node文本按字节表对应的代码点片段恢复；LexSave用(i,b)tuple，不依赖JS打包整数。命令10,000限制按UTF-16计长由既有wrapper负责，不把Python len当作JS length。保留source string_content在换行处的字节gap、引用空白段省略和可变heredoc节点，供安全walker按原字段读取。Python递归异常同其它解析异常返回None，不提高进程递归上限。

产品不调用Node/WASM/系统Shell解析命令，不用shlex、固定fallback或新增第三方解析依赖。冻结源码注释提及3449 corpus，但快照无该材料；本候选没有创建或声称通过这种golden门禁。

## 定向验证与边界

开发沿私有Python3.11、白名单启动器→tools/run.py及显式src测试入口，合成HOME/config/temp。首轮缺模块red后，6个冻结bash_ast.test.ts已有命令的叶子Node接口检查green；增加2项必要Python适配确认：中文/emoji的UTF8位置及quote换行gap、原超时/节点帽。**8 passed**，Ruff两文件通过。原mypy编译扩展ENV不重探，交root/独审既有pure工具链实际检查，不回填类型通过。

这6项只确认叶子节点可消费形态，不冒充冻结源码有独立bash_parser.test.ts。真正bash_ast.test.ts的现有26命令/25pytest上层来源断言由作者1唯一迁移及组合运行，本候选未复制该测试文件、未扩安全矩阵；最终结果待其闭环及独审。8项通过也不是整个Shell语法的等价性证明。没有实际Shell命令执行、真实模型、付费API或Terminal体验验证。

command-index.json与raw/保留首red、所有green与首次Ruff unused-variable原失败，source-members.json绑定最终模块/测试/冻结parser/test字节；敏感扫描均false。未构建wheel，最终产物/安装/全量由root统一出口。

## 组合类型回修

作者1消费叶子后，唯一bash_ast来源25项与engine async必要项首次26通过，受影响合计162项通过；其既有pure mypy真实检查15文件仅报告本叶子4个类型错误，属于TS块域到Python函数域的名称复用及两处Optional推断，不属于ENV。现只将子shell语句列表更名subshellBody、为substring offset/length明确Node|None，不改解析分支；Ruff通过。最终mypy green由作者1/独审复核并保存其原始回执，本切片不把此前未执行回填为已过，也不为类型标注重复运行功能矩阵。
