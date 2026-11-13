# 批次06 代码理解与联网

状态：approved / 五票技术、独审与集中交付完成。用户已选择A并明确「执行当前的计划」。范围固定33、55、22、23、25五票；起点`209a27d4`，分支`integration/ruocun-migration`，开始进度53/79，五票完成后58/79。未增加真实模型费用或系统安装授权。

先核前置、工作树和环境，再从包含本记录的提交建立本批分支，复用既有工作树和负责人。来源统一使用冻结`dao-f17e189-7ac654a0dc06`，参考目录只读。

| 负责人/分支 | 顺序与独占文件 | 交付出口 |
| --- | --- | --- |
| /root/n24_terminal；codex/b06-code；.worktrees/b04-agents | 33→55。`repomap/`、`lsp/`、`tools/repo_map.py`、`tools/lsp.py`及专属来源测试/fixture | 多语言符号/排名/2048预算、限额和缓存；LSP9操作、UTF16位置、Windows URI、同步、取消与真实进程关闭 |
| /root/n24_permissions；codex/b06-web；.worktrees/b04-hooks | 22→23，25的组合接线由主协调实现。`tools/web_fetch.py`、`tools/web_search.py`及专属网络模块/来源测试 | 抓取、抽取、缓存、地址安全/重定向、搜索与上限、网络失败/取消；普通入口真实消费结果 |
| 主协调 | 25及共享接线。`agent/runtime.py`、`cli.py`、`tools/types.py`、`tools/registry.py`、`tools/config.py`、配置写端口/运行依赖锁、公共记录 | Config读取/点路径写入/校验/保存，模式/主题/检查点按来源真实调用点生效；复用原生私有写端口 |
| /root/n24_review；codex/b06-review；.worktrees/b04-review | 独立代码审查及必要高风险复跑，独有证据 | 配置写入、网络地址安全、LSP生命周期、取消及普通入口接缝先审后供下游消费 |

线内顺序复用上下文，不添加33→55或22→23硬依赖。并行上限仍为主协调、两实现、一独审。公共文件只有一个写入者；实现负责人先交最小接口，主协调统一注册、注入和收尾。

按[D13](../ruocun-discovery/research/13-module-sequence-route.md)由33落实Python解析绑定/grammar及版本、许可与依赖锁，保留算法与语言覆盖。55按[D09](../ruocun-discovery/research/09-storage-extension-route.md)使用窄JSON-RPC/Content-Length客户端；原有协议fixture可复用，真实第三方语言服务器另在私有依赖环境验证，不能用fixture代填。普通选型自主处理；若必须缩减语言覆盖、改变关键行为或扩大系统安装/费用，先报告具体方案。

验证按[ADR-0009](../../docs/adr/0009-source-test-baseline.md)和[ADR-0015](../../docs/adr/0015-batch-validation-and-packaging.md)：逐票DAO来源语义红绿、已有缺陷最小复验，复用已绑定回执；高风险接缝独立复核。测试/构建用白名单环境、合成HOME/工作区、回环服务及模型；Web抽取模型不调用真实服务。中间源码定向验证，批末唯一默认全量、Ruff、Mypy、标准包/纯安装及成员字节绑定。77/78整体人工体验仍pending。

启动时补齐70对22、23、42的真实依赖：冻结index.ts的Web注册、--no-web/--eval和反思参数消费这些能力。71经70继承，保留其54直接前置；两票不纳入本批、不用参数存在或空注册证明功能通过。

## 检查点与进度

1. 接口就绪：每位实现者交来源位置、依赖与最小调用契约；前置已过才claimed，不虚填完成。
2. 定向候选：33/55和22/23逐票提交；主协调25候选与共享入口集成，独审按风险队列消费。
3. 里程碑：五票技术条件全部实际通过后冻结产品SHA，一次集中交付；若失败沿原复现修复，保留原失败和范围，未过项保持在途。

22、23、25、33、55均已独审结题，有效进度58/79。固定产品`0a0c1cea`的[b06-r1集中交付](evidence/batch-06/integration/README.md)通过：唯一默认全量实际`1641 passed, 3 deselected in 727.16s`，Ruff、Mypy254源码、4项离线冒烟、纯安装与285成员严格字节绑定通过；定向与全量分别记录。25实际来源、普通CLI及持久化回执见[独审](evidence/review/b06-config-review.md)。公共对应表与验收矩阵按里程碑汇总，日常更新逐票及本文件。

## 逐票出口

| 票 | 独审与实际范围 |
| --- | --- |
| 22 | [WebFetch](evidence/review/b06-webfetch-review.md)：真实受控GET、缓存保全文、模型抽取/400回退、no-web无请求；源初始地址检查范围保留 |
| 23 | [WebSearch](evidence/review/b06-websearch-review.md)：默认产品实际TLS搜索/编码/Host/UA、限制结果和下一模型消费；no-web无搜索 |
| 25 | [Config](evidence/review/b06-config-review.md)：实际四写journal确认、读取优先级/泛点路径、损坏/DACL前置拒写保原字节、当前无热载/重开生效 |
| 33 | [RepoMap](evidence/review/b06-repomap-review.md)：原7grammar与排名/缓存/预算回执复用、普通激活/真实编辑刷新、启动唯一尾system注入不改主前缀 |
| 55 | [LSP](evidence/review/b06-lsp-review.md)：协议/取消迟到/限长与挂住Job整树收口、普通配置/工具/切换；[真实TS](evidence/n55-real-server/README.md)源9操作+编辑同步，6个保留句柄确认退出 |

普通选型未提交额外用户决策：RepoMap用7个官方wheel覆盖全部原语言，运行闭包44项；LSP按D09窄协议并复用Windows Job，真实Node/TS服务器只在私有测试环境，不成为Python产品依赖。来源文案与Config实际project??user矛盾以实现为准；坏配置丢弃兜底按已有ADR-0013拒绝，不新增热重载。root统一公共接线，两个实现者各自小提交，独审复用同版本回执，批内未构包。

原红保留：Config导入/夹具父目录/错误收集路径及ACL前置分类、独审只读SQLite检查器未close、合成HTTP系统代理路由、HTTPS DNS端口、LSP非协议子stdin继承等分别解释，未把无效夹具或finally过早文字算通过。来源测试与必要实际技术项均按各报告真实范围登记，header/EOF只读审查和未测其它平台单列。没有调用真实/付费模型；77/78完整人工体验仍pending。
