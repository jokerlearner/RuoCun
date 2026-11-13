# 54 未知结果与恢复

沿冻结 `src/mcp/mcp.connect.test.ts:70–86`、`src/mcp/mcp.manager.test.ts:56–77` 的先副作用后断线来源反例，采用已确认 ADR-0003 的目标：保持一次、保留未决，不透明重试。stdio普通模型入口与换ID重开证据复用[51独审](../review/b05-mcp-cli-review.md)，其来源effect=2与产品effect=1不互相替代；此处只补HTTP/SSE。

两个新增来源定向例都走普通CLI、真实SQLite会话、独立stdlib MCP回环与合成模型回环。先收到明确JSON-RPC error，工具结果已确认配对、错误正文脱敏、CLI正常结束；随后用明确原sessionID继续，远端写effect-count=1后仅HTTP503/断开SSE，不回RPC结果。CLI退出74，重开同会话并要求新工具ID时零新模型/远端调用，原工具journal为outcome_unknown、原计数仍1，没有新ID意图。原错误工具保持result_committed。运行时材料由metadata.py只读复核，结果在metadata.json。

确认并修复三处接缝：

- 固定SDK把HTTP实际传输异常交给message_handler，原回调只处理通知，或连接拥有者已终止但活动send_request仍等60秒。记录明确TransportError/HTTPStatusError/OSError/EOF或真实拥有者退出，唤醒唯一活动请求并Unknown；普通能力通知、解析兼容错误和无关handler错误不被当作连接死亡。每个connection仍串行请求，实际RPC回包优先，取消只结束本次等待；完整请求deadline仍60秒、不因进度重置。
- manager已有状态/通知脱敏不能覆盖SDK自己logger.exception的原始URL。原两CLI在全部持久恢复断言通过后，最后的日志秘密断言红。现在对已使用SDK/logger及httpx挂本manager拥有的过滤器，先展开并脱敏异常trace再交任何handler，保留异常类别和诊断；close后移除。声明headers、敏感名env、URL凭据及原始/解码query值仅在进程内登记，长值先替换，不持久写凭据。旧实际连接配置的秘密在manager生命周期内保留，避免同名add后旧holder日志泄漏。
- HTTP原拥有者以ExceptionGroup退出后，严格close仍可报告关闭未确认；普通runtime的finally曾将已知未决74覆盖为71。主协调`51908a95`保留已知Unknown状态并只显示异常类型；正常会话close失败仍上抛，不伪称资源已成功关闭。

首轮latest选到了新会话：26规定latest仅选择未完成会话，故这段是无效夹具诊断，不记产品回归。改明确原ID后，单HTTP基线`n54-baseline-http-red`确认真实effect=1且25秒测试上限超时；初窄修两传输`n54-cli-r2`完成全部恢复断言、只剩秘密日志红；拥有者退出补齐后`n54-http-owner-exit`复现finally覆盖74；最终`n54-cli-final`两例通过（21.83秒）。原51/52/53九项回归及Ruff/Mypy通过；`executionConfigDigest`另沿原53同名add用例确认实际holder配置SHA不会跟声明配置漂移，无新增故障排列。

`executionConfigDigest`只返回当前实际已连接holder.config的规范JSON SHA256，不返回配置或秘密。Connection保留配置深副本。该端口供子代理恢复绑定实际连接，专属子MCP和其生命周期由A/主协调另收口。

命令均经tools/run.py白名单、合成HOME与回环服务启动，raw的scan_hit=false。原红日志仅含明确合成凭据，作为脱敏缺陷反例保留；最终日志未出现该值。未运行付费/外部模型、全量或构包；不声明远端exactly-once、不自动授权重执行，不把自动结果当终端体验。独审及整票状态由主协调确认。
