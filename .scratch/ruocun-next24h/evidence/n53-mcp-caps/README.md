# 53 MCP 能力

来源为冻结 dao-f17e189-7ac654a0dc06 `src/mcp/mcp.ts:70–89,207–318,349–399`、`src/mcp/mcp.connect.test.ts:89–139`、`src/mcp/mcp.manager.test.ts:11–53`、`src/index.ts:2047–2076`。52的HTTP与禁用回执继续复用；registry前5可见/搜索由主协调51共享接缝提供，当前真实服务另核目录消费。

独立stdlib stdio服务实际提供6个普通工具和resources/prompts能力。产品注册10项，前5可见，late_tool经搜索激活。四个合成工具的描述、API schema、实时列表、文本/二进制资源及prompt role/非文本格式按冻结实现。read_resource沿原始字符串发送URI，不经Python SDK的AnyUrl规范化；局部参数端口仍由固定SDK完成request/response关联。get_prompt只接受字符串映射；额外字段不转发。未绑定elicitation显式decline，绑定后真实accept/content回灌。

同一个change工具先发三类list_changed再回工具结果；产品收到的正文仍是actual change result，随后目录移除echo/加入fresh，tools类通知发出。SDK reader仅排队，独立拥有者刷新任务取同connection请求锁，因此wire_result/wire_error槽不被并行list覆盖。关闭先停止接收刷新、排空已发发现请求、关闭session/transport；旧连接或关闭后的刷新不发布目录。发现失败保留上一个完整目录（来源先移除再发现会暂丢目录，本实现避免将失败当空目录）。

addServer采用同manager锁包住原生配置读取/整server合并/实际persist/内存发布；坏旧文件及保存失败不伪成功。按主协调确认的来源优先规则，保留源已知特殊边界：add禁用名仍连接，当前status有holder即显示连接；disabled文件不被add清除，因此重开仍禁用。同名已连接add不替换旧holder，需reconnect采用新配置。此项不泛化修改toggle/reconnect的禁用保护。compat配置仍只读，实际writer仅允许原生user路径。

两个来源定向用例先红（缺四个能力工具/无addServer），初接线因关闭时取消已发list请求而暴露SDK BrokenResourceError，改为先排空发现请求后同用例绿。最终53两项＋51/52七项共9 passed，无warnings，Ruff/Mypy通过。raw由tools/run.py白名单合成环境产生，scan_hit=false，命令及原红/绿均保存。普通/mcp入口、模型可见性和交互由主协调联调并独审；本候选不宣称54跨重开恢复已通过，无全量、构包、付费或真实模型调用。
