# 批次 06 第 22 票独立复核

候选 `b1807861`，含 `3f1b8961` 来源模块。根运行依赖解释器、独审树显式源码、tools/run.py 白名单合成 HOME/工作区和模型；只提交证据，无产品或纯安装环境修改。

原 `tests/test_n22_web_fetch.py` 独立实际 **6 passed in 2.00s**。覆盖 15 分钟/50 项 FIFO 缓存、初始 SSRF 地址判定、endpoint/override/inherit 辅助模型、HTML 简单剥离和有限实体、截断前全文缓存、抽取与失败保全文、非2xx不缓存及错误语言。原必要真实 HTTP 用例证明重定向、命中缓存不重发，响应体未结束时用户取消使本地拥有请求收口。[来源回执](raw/b06-review-fetch-source/command.json)

[普通 CLI 探针](b06-webfetch-cli.py) 保留产品默认 fetchWeb 与 SSRF 路径，仅在来源加载器把精确合成 public-review.example 的 socket 解析映射到独占 loopback。请求仍带公共域名 Host，自有服务确认实际收到 GET。没有注入 ctx.fetchImpl 或产品 SSRF 绕过口，也不访问外网网页。

普通模型先请求无 prompt 的截断页，再用同 URL 抽取，最后让抽取服务返回 HTTP400。实际 **4 次主请求、2 次抽取请求、网页 GET 恰一次**；第二次抽取失败返回完整旧原文，证明缓存保留截断前内容。抽取请求到本进程配置的 endpoint/凭据，使用显式 synthetic-extract 模型；fetch-extract usage 在真实会话 cache.jsonl 中准确登记。追加普通 `--no-web` 进程，模型 schema 中不存在 WebFetch，无新增网页或抽取请求。[普通入口绿回执](raw/b06-review-webfetch-cli-no-proxy/command.json)

初轮公共域名收到 HTTP502，自有网页服务未收到请求；诊断细化确认失败发生在第一抓取，尚未抽取。只在合成环境增加精确 NO_PROXY=public-review.example,127.0.0.1 后同场景通过，属于测试路由/代理前提；没有修改产品网络或地址策略。对照证明需要指定本地路由，未据此断言某一具体系统代理注册项。原失败保留。[原环境失败](raw/b06-review-webfetch-cli/command.json) · [定位回执](raw/b06-review-webfetch-cli-diagnostic/command.json)

源码核查：抓取在整请求 30 秒期限内拥有 AsyncClient/GET/响应体，取消后等待本地异步请求结束；不声称取消能停止远端服务器。提取失败保留已抓原文，实际账户/会话模型在调用时选择，no-web 去注册并关闭抽取回调。schema/中英文描述、UTF16截断与固定来源一致。

明确保留来源 SSRF 范围：仅初始 URL 的主机名/字面地址，不解析 DNS 作安全判定、不逐跳重查重定向；本次 DNS 映射仅是实际 HTTP 的受控测试路由，不将其冒称内网地址已被产品允许或 DNS 重绑定防护已完成。简单 HTML 处理不执行 JS；max_chars 限制返回文本，不新增下载体积门槛。

所有回执敏感值扫描无命中。22 已审范围无阻断，可供后继消费；WebSearch/RepoMap/LSP 按各自候选另审。未全量、构包或代验体验。
