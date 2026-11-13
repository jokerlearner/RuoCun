# 批次 06 第 25 票独立复核

最终窄候选 `36f8fe7f`，含初版 `0e0bf85d` 与 null/数组读取修正 `c6367fb0`。只提交独审证据；白名单合成 HOME、私密用户配置、真实普通 CLI/SQLite、回环模型，无真实凭据或付费请求。

[普通 CLI 探针](b06-config-cli.py) 实际三次模型请求：ToolSearch 激活 Config，下一请求显示原 string/boolean/number 的 anyOf schema，随后项目 false/0 返回原值、项目 null 回用户值。四个配置写入（权限模式、通用点路径、theme、checkpoint）均进入下一模型请求的确认结果；真实原生 settings.json 保留无关字段，项目文件字节不变。独立只读真实 SQLite 工具账本确认四写全为 **result_committed**。[最终普通入口回执](raw/b06-review-config-cli-journal-r2/command.json)

同进程 `/Config` 仍显示实际 auto 模式，显式重开原会话后显示 plan；查询不增加模型请求。没有热重载权限/检查点或让 settings.theme 覆盖启动探测，保持冻结调用时机。普通源码路径确实绑定 Conversation journal，未用 fake journal 或只凭“已设置”文案判成功。

初次普通入口已通过；补账本回读后，检查器用 SQLite context manager 却未显式 close，所有功能断言通过但临时 DB 清理失败，实际记红。改为 closing 保证关闭只读连接后，同一场景最终退出 0、正常清理，未改产品。[原入口](raw/b06-review-config-cli/command.json) · [检查器清理失败](raw/b06-review-config-cli-journal/command.json)

原来源单条 `tests/test_b06_config.py` 在 `c6367fb0` 独跑 **1 passed in 0.27s**。覆盖项目/用户读取、已知值校验、通用点路径、坏 JSON 原字节保留及原生目标；独审读源发现的 user null/undefined 混淆和数组索引差分已由该窄修补齐，并在同一来源用例核 user null 返回字符串 null、items.0 可读。[来源回执](raw/b06-review-config-source/command.json)

独立[保存拒绝探针](b06-config-preservation.py) 验证非对象父节点拒绝、旧字节保留。非私密既有 settings 文件初始读校验确定拒绝，却因 AtomicFileError 不在 catch 中，被真实 executeToolBatch 包成 UnknownToolOutcome；原红已复现，不能把此已知零写入当成发布后未决。主协调 `36f8fe7f` 仅在初始读取/值准备 try 中转换为 ToolRejected，最终同批处理探针返回可配对 Error，旧文件字节保持。PrivateDirectory/atomic_publish 发布域仍在 try 外，不能吞掉发布后未知回执。[实际批处理红](raw/b06-review-config-prewrite-red/command.json) · [修后同探针绿](raw/b06-review-config-prewrite-green/command.json)

源码核查 anyOf 只补既有 schema 子集：各分支实际校验，bool 不作为 number 接纳，Config 的 object/null 写值不合法。整段设置 RMW 使用既有进程内路径锁；读取既有文件先 verify_private_file，发布在 PrivateDirectory 稳定命名空间中进行。未因未证实假设添加并发文件编辑矩阵，也不宣称提供外部编辑器的 CAS 或跨进程互斥。既有 ToolBatch 根据 persistentEffect 处理未确认发布/结果保存，沿已有日志语义保留未知，不主动重放。

所有保存的回执敏感值扫描无命中；失败如实保留。本票已审范围无阻断，可供后继消费。没有全量、构包或用户体验代验。
