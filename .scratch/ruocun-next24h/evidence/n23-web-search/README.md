# 23 WebSearch

冻结来源：`dao-f17e189-7ac654a0dc06`的`src/tools/web_search.ts:1–87`及`web_search.test.ts:1–81`。沿既有MM-740导出webSearchTool，中英描述逐字迁移冻结字符串，query/max_results的required、整数上下限1–10、默认5、network/suggest和常驻语义保留。

原模块缺失时来源解析用例红；实现后按冻结DDG fixture精确返回标题/URL/摘要、uddg decodeURIComponent（保留+、坏编码保持原href）、协议相对链接、分块编号格式，max_results=1不混入第二项；第一项缺摘要时不会盗取下一条摘要，无结果返回固定中文占位。请求地址使用encodeURIComponent相同的query编码，User-Agent=Mozilla/5.0，显式传本轮signal。非2xx/超时/取消返回可配对的Error文字，英文分支按来源msg处理。

23两项及22原六项共8 passed；Ruff/Mypy通过。公共GET采用22已实际验证的httpx拥有者：30秒整请求deadline、同一signal取消及响应体/连接关闭，不另写网络栈、不新增依赖。22真实回环重定向/缓存/取消证据继续绑定，不再重复同一transport确认。WebSearch自身不缓存；不扩大成额外搜索提供商、DOM引擎或网络防火墙策略。来源HTML结构匹配边界保持，外部网页变化不冒称已实测。

命令经tools/run.py白名单合成HOME/配置启动，raw敏感扫描无命中，测试只用来源fetchImpl注入和受控回环，不调用DuckDuckGo外网或付费模型。本候选不替代主协调普通模型入口及no-web/eval配置接线验收；23保持claimed，独审/主协调决定整票状态，未运行全量/构包或最终终端体验。
