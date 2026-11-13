# N1 普通入口独审

初候选 `43ba2c4f01a31c97a23bca959b170f1594909aa8`，基线 `c72099f52073c9692b74d99c726b925e26477c23`，四项源码/资源/fixture diff 非空，固定提交合入独审 worktree。只复原 CLI 与唯一受控 TTY fixture，不重复已审规则、AST、存储、scheduler/broker 或搜索矩阵，不建环境、不构包。实际新版固定产物与纯安装仍留统一出口。

## 已核对的接线

- run_turn 内逐工具用同一 Task 的原 raw JSON 调用 PermissionRuntime.authorize，随后记录 intent、派发同一已验证参数；未在父 Task 预裁后让子 Task 继承最后一次 ContextVar 许可。真实默认 B、native/显式兼容层级及 native-only 记忆/删除目标沿已审模块消费。
- 每请求 API 工具表与逐调用 plan 硬门读取实时模式，EnterPlanMode 后同批写/执行仍受硬门；intent 使用 permissions-v1/gate-approved，不冒称用户文字确认。
- scheduler 每 run 的 Event/generation 连接到已审 request token；可信返回、usage、完整工具 pair 与图片批末保存沿原完成口。命令变更先 pause→settled，队列消费仅在完整工具/模型边界进行；压缩不在飞行请求中异步换投影。
- 接纳把用户命令与当时 Skill 正文同 ack 保存；恢复消费持久快照，不重读磁盘。拒收先不 ack，broker 恢复原文及编辑中草稿；/files 只投影实际 readMeta/readFiles，不制造读取事实。TTY 专用 simplify 沿批准的内置正文优先规则。
- 单 broker owner 承担输入/审批/选择，关闭先排入 scheduler.close 使当轮 Event 失效，再关闭 broker 唤醒审批/输入，等待自然完成与输出任务后关 Conversation；不 Task.cancel 模型/工具轮次。headless/pipe 不调用 stdin 审批，pipe 顺序 finished 后再读下一行。
- Windows 父 PROGRAMDATA 在 applyDotenv 前固定 ProgramData，权限装配读取该 canonical 键；两个 fixture 均明确使用合成父目录，项目 .env 不能改址。trust 子命令不取模型凭据或请求模型。

独立原 CLI + 唯一受控 TTY **2 passed in 14.63s**，见 `raw/n1-review-runtime-entry-01`。父进程加载本次固定 src，CLI 子进程显式绑定其实际包根，没有借私有环境旧 N0 安装假验新版；TTY 只在模型边界注入响应。所有验证沿私有 Python3.11/白名单启动器/tools.run、合成 HOME/config/TEMP、仓库外 basetemp；exit0、scan false、API 0。该证据不能代替真实 Windows Terminal/resize 或最终 wheel 安装。

## 初审发现

1. 查询类 context/status/effort 分支无论 mutating 与否都赋 active=mutating、finally active=False，会覆盖正在运行轮次的 active=True。查询后外部 SIGINT 误走 KeyboardInterrupt 退出分支，不能继续按当前 Event 取消。已交唯一 runtime 作者最小修正。
2. PermissionRuntime.isMutatingCommand 对 /permissions add|remove 仅认动词；缺 kind/规则的纯用法错误会先 pause_settled，丢弃已确认排队输入，然后才反馈错误。与同一 fixture 已确认的无效 effort/context-window 不应暂停相同，已交 root 分配唯一写者最小补齐，不扩用例矩阵。

初候选功能断言通过不关闭这两项。收口候选、受影响 fixture 及最终指纹将在后续段记录。

查询 active 问题由唯一作者以 `3b8d1540bb1f5fe0de5e106976cbbf5dd66ebf93` 最小关闭：只在真正 mutating 的上下文命令分支维护 active，查询/错误反馈不覆盖运行轮次。独审只 cherry-pick 该单提交（本树 37c1004），同一受控 TTY fixture 真实捕获注册的 SIGINT handler，确认查询后设置旧 Event、迟到 delta 不显示、新 run 使用独立 Event、可信 usage 与工具 pair 保留。受影响用例独立 **1 passed in 3.15s**，回执 `raw/n1-review-runtime-sigint-02`；原 CLI 未受影响，不重复运行。

补充静态观察：旧 Read 在线程内更新全局 readMeta/readFiles，忙时 /files 直接遍历 dict 有并发变更风险。已交 root，由 root 关闭 worker/main 状态更新接缝，不扩压力矩阵；此项只作为静态风险，未以合成故障测试冒称已经复现。正式小候选及原受影响断言另记。

权限命令分类由原单文件作者以 `11f0ac639826885b173c87d7b40a48e18bee5a18` 关闭；独审只 cherry-pick 该单提交（本树 87ca326），helper 与 command 共用相同的合法 kind/非空 rule 语法前提。只复原 mode/分类 fixture **1 passed in 0.12s**，见 `raw/n1-review-permissions-syntax-03`。没有写 runtime/TTY 的共有文件；实际入口同 fixture 将由其唯一作者增补已发现的纯用法错误路径确认。

唯一入口作者以 `02a62b040d7e7a6ac273b892f981e0b8a94dcdaf` 只补 /files 的保守 tuple/set 快照，并在同一 TTY fixture 的既有无效命令片段追加 `/permissions add`。独审只 cherry-pick 该单提交（本树 7dab864）；缺参数命令处理后队列仍为 queued、原 Event 未取消，随后同一 SIGINT/新 Event/审批/完整 pair/可信 usage 流程保留。该受影响同一 TTY 用例独立 **1 passed in 2.98s**，见 `raw/n1-review-runtime-syntax-04`；没有重跑原 CLI 或扩用例数量。初审两项问题关闭，当前入口模块可供 root 消费；Read 的 worker/main 根因小片另待 root 固定后独审，不把未来实现先写为通过。

普通入口实际产品/资源/fixture 文件逐项绑定固定提交，详见 `n1-ordinary-runtime-binding.json`；产品字节完全一致，测试/文档的 Git LF 与 Windows CRLF checkout 转换单列，不暗中忽略产品差异。独审未写产品、未更新父票状态；真实 Terminal/resize、最终产物/纯安装与整票仍待后续出口。

## Read 业务线程归属接缝

root 固定 `d5c53b7c9bd9d35b5cfd4b1521a6c6990ae384f5`，独审只 cherry-pick 该单提交（本树 46a43ba）。Read 的 worker 浅上下文持有新的 readFiles/readMeta/currentImageData 槽，原文本/图片逻辑只填本次局部结果；await 完成后实际业务 loop 更新共享状态，不复制/覆盖其它已读基线。读前 stat、错误不登记文本基线、offset 越界仍登记真实读取、图片不冒充文本基线及现有图槽行为保持。原读取记录 fixture 直接约束共享 set/dict 写入线程，未建压力测试。

路径分类 I/O offload 后，审批 callback 仍在调用方实际 Task，保持本调用 ContextVar once 不跨 Task。初审另指出一个新 await 引入的取消窗口：分类 I/O 等待期间 Event 已取消，返回后应先检查 Event，再进入区外批准 callback；否则先前 cancel_approval 无 Future 可取消，旧 run 可能在取消后新建审批等待。已交 root 最小收口，不扩排列。

独立复原 Read/Image/paths/Write/Edit 五文件 **42 passed in 0.52s**，仅两个改动产品源文件 mypy **通过**；回执 `raw/n1-review-read-owner-05`、`raw/n1-review-read-owner-mypy-05`。

取消窗口由 root 固定 `606c4a8657161d274b6314684e1974bff4a0426a` 关闭；独审只 cherry-pick 该单提交（本树 9da15ba），分类 await 后先检查 Event 再允许审批。沿原授权区外读取同一 fixture 受控令分类返回前设置 Event，root 保留 red→green；独审只复该受影响项 **1 passed in 0.16s**，见 `raw/n1-review-read-cancel-06`，未重复 42 项。普通入口、/files 快照、Read 业务线程应用与取消后不新建审批的关键接缝剩余阻断 **0**，可供 root 统一固定产物消费。

## 固定模块收口

最后只读核对 help `3fa3c9b8693d09286e2a02a54a8be42c11a89c57` 与 README `e4f60a1a1359859eba0747b80577159f29da0e11`：明确暂停会持久丢弃尚未消费队列、只读查询不暂停、技能开关重启、专用 simplify 例外、plan/权限命令语法、原生/兼容只读与 files 的本进程范围。README 去掉旧七工具/逐项 stdin 审批/不支持压缩等时态，同时保留完整迁移、真实模型/Terminal/resize 待验边界。未把文字更新当作新增产品测试通过。

root 最终固定产品/测试源 `a7d803ce64f214ba7d757c134bbf0d80526d2dbb` 已合入独审树；十项实际产品/资源/文档/fixture 字节与该单一提交绑定，原修复 refs 也完整保留。新增 help 仅文字，不重复模块验证。此处交付模块独审证据，统一 build/固定 wheel/纯安装与整票自动出口待 root 实际执行后再报，不提前改变 09/11/34/19 状态或人工 pending。

## 工程绑定旁审

先只读核主线 c766579 的 n1-integration/bind.py；固定归档、动态产品成员、direct/sdist-wheel、实际安装依赖与已审官方 SQLite ZIP 方向正确，且明确不产生功能通过结论。发现 tracked 漏 hatch_build.py 后 root 以 `49862ce82aeebd11de1b68cb16d72d83fb1d9b0c` 补固定 hook/工作树/sdist 字节，并补 README/pyproject/两锁及 wheel metadata/成员双核；已独立只读确认最小 diff，未运行 binder 或构建。
