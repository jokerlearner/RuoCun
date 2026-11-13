# N1 计划硬门与 N2 搜索工具独审

## 固定范围与验证方式

计划接缝固定 `faa46c2a9ce4cf735b5d3a23caad7a2cc86eee8b`，搜索初候选固定 `f06f4bf4f2b7434e276d49df2c67e2cdabfe3427`。两者对应父提交的 diff 均非空；产品从固定提交合入独审 worktree，独审未写产品。最终源指纹见同目录 binding JSON。

本次为源码导入定向验证，复用私有既有 Python 3.11 环境及已核纯 Python mypy；外层白名单启动器、tools.run、合成 HOME/config/TEMP、仓库外 basetemp。未构建新版包、未把仍装 N0 的纯产品环境冒充 N1/N2 新版安装；没有重复全量或扩故障矩阵。下述原始命令均 joined，exit=0、敏感扫描 false；真实/付费模型 API 0。

## 计划模式与授权接缝

optional authorize、permission_mode、api_tools 保持旧调用缺省兼容。每请求重新取得 API 工具表；模型同批调用 EnterPlanMode 后，后续 write/exec/mcp__ 在权限回调及 intent/dispatch 前再作硬门判断。单纯策略返回 True 不能越过该门，下一请求也使用改变后的工具表。

授权回调异常时，尚未执行的调用均配对错误结果并逐次走保存；不会进入其 intent/handler，保留已经完成的前序结果。若配对保存本身失败，异常继续上抛，不以本分支的“已保存”结果掩盖未确认写入。可信 usage、取消/token 口与工具整批边界未改。

Conversation 的 policy_version/approval_ref 只新增实例默认值，不改 Checkpoint/schema。旧调用仍以既有 mvp-adr11 与 text-confirmed/read-only 标记；组合入口可显式使用 gate-approved，避免把策略允许写成用户文字确认。

只复同一新增接缝用例 `test_plan_switch_in_batch_blocks_write_before_dispatch_and_trims_next_api`，**1 passed in 0.32s**，见 `raw/n1-review-plan-seam-01`。本切片无剩余阻断，可供入口装配消费；这不是完整入口及 09/11 整票验收。

## 搜索初审

ListDir 保留冻结来源的单层 scandir、UTF16 字典序、目录后缀、500 项截断、空目录/不存在/非目录行为及区外批准；不递归链接。Glob/Grep 继续使用既有 approvedPath/walker，未增加外部路径读取口，未写 readFiles/readMeta；目录枚举/搜索命中不伪装成已读事实。

filesReport 只投影调用方给定读取事实，保持输入顺序、相对路径、根目录回退及前 50 项文字，不读文件、不修改账本、不假称恢复了跨进程 read-map；实际入口读事实收集仍另审。Grep 新显示长度、列号及截断使用 UTF16，匹配本身仍是已批准的 Python 标准 re 差异，没有新增正则依赖。

冻结来源三工具的中英描述使用独立 Node 字面量求值，17 个字段用只记录 Zod shape 的本地 stub 求值；只执行已读的 metadata 表达式，不加载冻结产品模块。它们与 fixture 的源 SHA/完整字符串/API shape 全部一致；现有产品断言再核对唯一批准的 Grep Python 正则说明替换。见 `verify-n2-source.cjs` 和 `raw/n2-review-descriptors-node-01`，Node v24.15.0。

原 Glob 12 + 原 Grep 17 + ListDir 原来源 6 + 必要显示/schema/files 3，共 **38 passed in 0.41s**，见 `raw/n2-review-search-source-01`；四产品源文件 mypy **通过**，见 `raw/n2-review-search-mypy-01`。

初审找到一处原 MVP 遗留的来源差异：匹配长度 499/500 UTF16 单元且有 match_context 时 cap=0；冻结 JS `before.slice(-0)` 保留 before，而 Python 的 `if cap else ''` 丢弃它。这不属于已批准的正则语法差异；root 已明确沿源，交原 Grep 作者最小回修、复用原 snippet fixture。初审通过不跳过该收口，后续结果记于下节。

## 搜索收口

作者固定回修 `b2cce79adbcf5d89c5e91a6ce8a852c3f17cb3ef`，独审只 cherry-pick 该单提交（本树 `b1e42b6`），没有消费其普通入口 WIP。产品只移除零配额时的 before 丢弃条件，保持来源 `slice(-0)`；原同一 UTF16/snippet fixture 增补已发现边界的断言，作者保留 red→green 原回执。

独立只复该受影响用例 **1 passed in 0.13s**，见 `raw/n2-review-snippet-zero-02`；没有重跑 38 项或扩排列。源码/工程剩余模块阻断 **0**，19 搜索切片可供 root 注册消费。完整普通入口、统一固定产物/安装与 19 整票状态仍由后续实际证据决定；本报告不改任务状态或人工体验。
