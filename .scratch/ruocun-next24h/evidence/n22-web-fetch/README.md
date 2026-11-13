# 22 WebFetch

来源：冻结 `dao-f17e189-7ac654a0dc06` 的 `src/tools/fetch_url.ts`/`.test.ts`、`fetch_cache.ts`/`.test.ts`、`fetch_extract.ts`/`.test.ts`、`ssrf.ts`/`.test.ts`；普通辅助模型接线依据`src/index.ts:1074–1096,1131–1132`。产品按既有MM-647/649/651/711放在fetch_cache/fetch_extract/fetch_url/ssrf.py，未另造第二个WebFetch模块。中英描述从冻结字符串逐段精确迁移，保留schema/可见性、network/suggest、max_chars与prompt。

逐纵切红绿：cache模块缺失→15分钟TTL/50项FIFO；ssrf缺失→来源10拒绝/3允许URL；resolveExtractModel缺失→原override/官方同族便宜档/网关与inherit；工具缺失→去script/style/标签和有限entity、缓存截断前原文、默认不抽取、有prompt抽取、提取失败或未绑定保持原文。最终6项来源定向用例通过，另包含来源非2xx不缓存/超时/英文错误，以及一个独立真实HTTP重定向、缓存不重发、响应体未结束时取消并收口的必要运行确认。Ruff/Mypy通过。raw均经tools/run.py白名单合成环境，scan_hit=false，无外部模型/付费或系统安装、无全量/构包。

网络使用已有固定httpx，async拥有请求/响应体与client，30秒整请求deadline和ctx.signal；不新增依赖。测试通过来源fetchImpl端口把允许的合成主机映射到本测试独占回环server，未关闭产品的初始SSRF检查，也未把直接抓取127当允许。UTF8文本解码沿fetch Response.text语义，输出截断按JS UTF16单位。HTTP非2xx不缓存，提取在缓存之后每次独立发生，失败不丢已抓原文。

明确保留来源边界：SSRF基于初始URL的主机名和字面IP，不解析DNS、不逐跳重查重定向，不宣称DNS重绑定或重定向内网已拦截。HTTP默认跟随最多20次重定向；HTML按源简单正则，不执行JS。max_chars限制返回值，源未对下载体积设额外上限，本实现不添加隐含下载截断。URL解析窄适配Node URL对IP数字形式/IPv6/IDNA的规范化以供来源地址判定，非额外DNS策略。

主协调注入ToolContext.fetchImpl/extractFromPage，普通账户辅助模型/usage和no-web组合入口另由其集成验证；本候选不将该未消费端口或23搜索当本票普通入口已通过。Status保持claimed，待独审与主协调验收。
