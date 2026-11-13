# 批次 06 第 23 票独立复核

候选 `339e0a4d`，含 `b11cfa28` 搜索模块，独审树该模块字节与来源候选一致。按 ADR-0015 审已有来源两项及回执，不重复刚通过的 22 网络传输组。[原两项语义与实现回执](../n23-web-search/README.md)中最终实际为两项搜索加六项抓取 **8 passed in 2.10s**，不将其伪报为本次独跑八项。

源码核查保留 DDG query 编码、User-Agent、本轮信号、标题/URL/摘要格式、uddg 解码、结果上限及缺失摘要不挪用下一条；失败文字可配对，常驻 network/suggest。普通注册与 WebFetch 同受 no-web 控制，未增加搜索服务商或独立网络栈。

独立[普通 CLI 探针](b06-search-cli.py) 不注入 fetchImpl：仅将精确 html.duckduckgo.com 的 DNS 映射到独占 loopback，使用临时自签合成域名证书和 SSL_CERT_FILE，精确 NO_PROXY 避免旁路代理。自有 TLS 端点实际收到原 DDG Host、`/html/?q=C%2B%2B%20%E4%B8%AD%E6%96%87%20%2F%3F` 与 Mozilla/5.0，下一模型请求准确消费唯一结果标题、解码 URL 和摘要，没有第二项。正常搜索两次模型请求，追加 no-web 进程一次模型请求；网页搜索请求总数 **1**。no-web 请求中 WebSearch/WebFetch 两 schema 都不存在，未增加网络搜索。[普通入口绿回执](raw/b06-review-search-cli-tls/command.json)

初版合成 TLS 服务用动态端口，仅试图在 getaddrinfo 结果改端口；实际 AnyIO 先取解析 IP，再用原 HTTPS 端口 443 连接，故返回连接失败。这是无效夹具路由，不是产品问题。改为本地独占 127.0.0.1:443 监听，保持 HTTPS 原端口后同场景通过，结束关闭监听；未修改产品 transport、TLS 校验或 SSRF。[原夹具失败](raw/b06-review-search-cli/command.json)

回执均白名单、合成 HOME/账户/服务，敏感值扫描无命中，没有外网 DDG、付费模型、产品改动、全量或构包。23 已审范围无阻断，可供后继消费；不把受控 HTML 验证宣称成真实搜索站点长期兼容性已验。
