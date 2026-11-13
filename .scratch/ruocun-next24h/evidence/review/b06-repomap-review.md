# 批次 06 第 33 票独立复核

候选 `339e0a4d`，包含 `f31bdbbf` RepoMap 模块与普通启动接线。独审树 repomap/ 和工具模块与该源码候选无差异。只读核冻结绑定、实现与已有来源回执；无权限/持久化新增风险，沿 ADR-0015 复用原九项，不重复 grammar 整组。[实现者来源/平台回执](../batch-06/n33/README.md)

已复用的来源回执实际 **9 passed in 0.17s**；对应 TS/TSX/JS/Python/Go/Rust/Java 的 grammar、定义/引用/import 提取、图与 PageRank、渲染预算及缓存。独立最小平台回执记录 4001 个文件只取 4000 且 truncated、512KiB+1 跳过、mtime 改变后刷新及已置位信号取消，未扩为压力测试。版本、七个分发轮子（core 与六个语言包）、哈希及 MIT 原文均在原依赖/许可记录，TSX 与 TS 共用类型脚本分发，不混淆包数和语言数。

源码审查保留懒加载/失败缓存、Parser 锁、AST 不进入长期缓存、mtime+size、预算与限额，不用正则替代语法树。启动构建可选失败静默；正常工具调用仍实际给结果。扫描/提取/图检查信号，外层关闭先置 stop，再 await 实际后台任务，完成时复核 closing，不在会话关闭后注入新上下文。没有主历史替换或配置写入。

独立[普通 CLI 探针](b06-repomap-cli.py) 使用根已验 grammar：两个真实 Python 文件构成引用关系。普通 ToolSearch 激活 RepoMap 后，实际模型 schema 可见；启动地图恰一次出现在尾部 system，首个 system 消息未变化，`--no-project-instructions` 不误关闭地图。第二次模型请求前真实修改源文件，RepoMap(refresh=true,max_tokens=512) 输出原函数与新增 freshly_added，第三次请求准确消费结果，工具报告解析两文件。共 **3 个模型请求**，无 fake Parser 或地图注入。[普通入口回执](raw/b06-review-repomap-cli/command.json)

普通回执白名单合成 HOME/项目/回环模型，退出 0、敏感值扫描无命中。33 已审范围无阻断；没有重跑九项、全量、构包、真实模型或用户体验代验。
