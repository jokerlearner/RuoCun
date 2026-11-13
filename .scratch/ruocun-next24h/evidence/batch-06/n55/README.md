# 55 LSP 源码候选

基线179d5692及root共享lsp字段70b035c3（本树等价0a8447b2）。冻结源lsp/config、manager、client与九操作工具hash见source-bindings.json。仅替换vscode-jsonrpc语言绑定为D09窄asyncio JSON-RPC/Content-Length客户端，不自动安装任何语言服务器。

loadLspConfig(files)沿server名整项后覆盖、坏文件跳过；resolve按扩展名忽略大小写取首配置。LspManager(config,rootUri,*,environ=env).resolve(filePath)同步返回client/error并复用同语言实例；Python进程在首次实际操作懒启动。await disposeAll关闭全部客户端、未确认则保实例并报错。root负责配置来源顺序、ToolContext.lsp、注册和普通入口资源栈。lspTool为deferred/read/auto，九操作、schema/required/1-based位置沿来源，中英描述仅把实际配置路径.dao改.ruocun。

客户端使用UTF8字节Content-Length和单调request ID；读循环处理合包/分片，过期ID不配对后续请求。16KiB header、16MiB消息体先验上限，最多128个pending；无响应默认30秒，取消/超时发送$/cancelRequest，不自动重发。initialize声明默认UTF16；外部1-based UTF16行列统一减一，未换为Python码点列。中文/空格/盘符/UNC file URI按Windows路径解码。didOpen v1、mtime变更didChange全量v2；Location/Link、hover几种形状、层次/扁平符号及调用层级沿冻结formatter。

D09已批关闭修正：shutdown最多3秒→exit→短暂正常等待，再精确收口owned tree并等真实句柄，不因发出kill就宣称停止。Windows沿既有platform/windows/process_tree的Job结构与等待规则；CREATE_SUSPENDED启动，CPython3.11实际Popen handle先挂KILL_ON_JOB_CLOSE，再按该尚未恢复PID唯一初始线程Resume（失败只终止本次刚创建的进程）。正常父退出后也清理Job剩余子孙，POSIX保留进程组设计、未做其实机验收。所有close调用等待同一幂等任务；关闭失败不伪称已关闭。

## 当前已有回执

- config-red→config-green：来源配置覆盖/缺失/坏JSON、扩展名路由及同语言复用绿。
- protocol-green：复用D15独立fixture（tests/support/lsp_server.py仅整理格式），真实Windows子进程、中文emoji跨写入分片、两帧反序合包、1-based外部5→UTF16内部4、中文空格URI、v1→v2同步、超时cancel、shutdown后exit、真实process returncode=0；2 passed。
- static-final：Ruff、mypy7源模块通过。

真实第三方TypeScript语言服务器及冻结sample.ts九项调用由同批负责人B准备，独立证据在n55-real-server；当前本文件不预填通过。恶意header/声明超限/强停的必要技术收口与普通入口/独审核验另补，不以代表协议fixture代填真实server或整票完成。

本次使用tools/run.py白名单、合成HOME、专属private venv；无全量、构包、付费模型或系统安装。原DAO和历史D15证据保持只读。源无timeout/shutdown/Windows URI decode的已知缺口依D09修复，不伪称这些本来是源行为。

后续固定集成已完成，[独立复核](../../review/b06-lsp-review.md)通过；历史候选记录及原红保留，整票及里程碑结果读取[批次记录](../../../batch-06.md)。
