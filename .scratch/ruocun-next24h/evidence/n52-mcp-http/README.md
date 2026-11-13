# 52 HTTP/SSE

来源：冻结 dao-f17e189-7ac654a0dc06 `src/mcp/mcp.ts:19–43,147–204,323–405`，D09固定 `mcp==1.30.0`，ADR-0003不重放约束从51保持。配置覆盖的已绑定51用例继续复用。

四项来源定向用例使用独立stdlib回环服务，真实执行 Streamable HTTP 与 SSE initialize/list/call，URL优先于command、声明headers、session关闭（HTTP DELETE和SSE流实际结束）、跨源307、持久禁用/重开和禁用时reconnect。状态保存复用主协调提供的原生 `writeMcpState`。写入失败原样上抛，确认后才发布内存状态，不把失败当成功。

原实现只支持stdio时三个transport用例红（n52-http-red-r2）。接线后SSE因重复进入AsyncClient、307因固定SDK拒跟随仍红（n52-http-r1）；分别修正client factory生命周期和窄HTTP适配后绿。冻结TS SDK1.29.0真实双回环差分（source-redirect.py/.mjs）确认跨源307继续POST、Authorization剥离、普通自定义头保留；Python固定SDK1.30.0显式follow_redirects=False，故仅在自有HTTP client覆盖send跟随行为，沿httpx的跨源凭据剥离。

最终52四项加51原三项为7 passed，Ruff、Mypy通过。所有命令经tools/run.py合成白名单启动，raw的scan_hit=false；记录在raw子目录。声明headers所有非空值、敏感名称env值和URL凭据/查询值在manager错误/通知出口先脱敏，再调用会话脱敏。没有模型或外部服务、没有全量或构包。普通入口联调、独审与53能力出口分别记录，不以本回执替代。
