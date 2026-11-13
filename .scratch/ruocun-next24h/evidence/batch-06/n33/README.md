# 33 RepoMap 候选

基线179d5692，冻结dao-f17e189-7ac654a0dc06。source-bindings.json绑定全部repomap源码/测试及RepoMap工具。沿原语言映射、定义/引用提取、相对import/名字依赖边、damping .85的30轮PageRank、UTF16字符/3预算与120余量、折叠签名、2048默认、4000源码文件和512KiB单文件上限、mtime+size缓存，不以正则替代语法树或缩减语言。

D13语言绑定落实为tree-sitter 0.25.2及6个独立官方grammar分发（typescript含TSX；另javascript/python/go/rust/java），7grammar均实际加载。精确版本、官方PyPI文件URL与SHA256见dependencies.json，默认无其它传递依赖；requires中的core/docs/tests均extra，不启用。licenses保留实际wheel的METADATA与许可原文，均MIT。未采用强依赖额外C#/YAML/template grammar的language-pack，未改变所需语言覆盖。Python本机绑定替代原loader/wasm-assets职责，进程级懒加载，失败缓存None；缓存不持有AST节点。共享Parser在Python worker线程中持锁，避免并发刷新切换language。

公开入口：async buildRepoMap(root,tokenBudget=None,*,environ=None,signal=None)返回RepoMapResult(text,fileCount,truncated)；repoMapTokenBudget(environ=None)保留DAO环境兼容并优先RUOCUN；wrapRepoMapNotice。repoMapTool为deferred/read/auto，无新ToolContext字段，读取cwd/workspaceRoot、notificationEnv及signal。refresh沿原实现每次重新遍历但复用未变mtime+size结果，不额外清缓存。

原index.ts904–913在启动后台构建，budget=0跳过，完成后notice加入尾部system队列，失败静默，无默认timeout，不受--eval/--no-project-instructions控制。普通入口由主协调接此契约。为Python executor退出收口，signal在walk、逐文件、AST节点和图阶段检查；取消抛InterruptedError，未返回半张地图，根关闭后不得注入。无主历史或配置写入。

## 现有来源与最小平台回执

- extract-red：缺实现红；extract-green-graph-red：TS原定义/常量/import断言绿，graph缺模块红；first-green：两片绿。
- index-red：七grammar及graph/render已8 passed，index缺模块红；source-green：9 passed。TS、Python、Go、Rust、Java和TSX用原extract.test.ts语义；JS补必要原生grammar加载确认。graph、render、index来源断言紧凑组合，未另建测试框架。
- static-final：Ruff、mypy（8源文件）通过。
- platform：合成临时目录实际4001文件只覆盖4000且truncated，512KiB+1文件跳过，修改同长度文件后mtime刷新可见、已置位signal停止。此为票上限及线程关闭所需最小技术确认，不称额外来源测试通过。

原回执均raw下保留，scan_hit=false。产品测试/安装通过tools/run.py白名单、合成HOME及专属.cache/b06/venv，根纯包环境未改。依赖版本/轮子来自PyPI官方metadata并逐SHA验证；未跑全量、未构包、无付费模型。普通入口与独审另由主协调记录，不能凭此将33 resolved或代填体验。
