# N0 完整图片工具结果持久化

基线 `92ddc62`（已独审 ImageData / str|dict 接缝），本票仅修改 session 的 contract/storage_worker/durable_store/conversation，新增纯函数 messages.py 与独有必要测试。不改物理 schema、STORAGE_VERSION/USER_VERSION、主循环、工具执行器或客户端。关键存储接缝待独审后才供 root 消费；08及34未因此结题。

## API

- `ToolResult = str | dict[str, Any]` 在 contract 唯一声明；ToolRecord.result、StoragePort/worker/Conversation.intent 的复用返回和结果入参统一使用它。旧 str 原样保留，不把 dict 转成字符串或嵌进 content。
- worker 将可变结果纳入入队快照；intent 复用返回也 deepcopy，调用方不会修改 port 持有的对象。
- `Conversation.result(call_id, text, image_data: ImageData | None = None)`：无图仍存 str，有图存 role/tool_call_id/content/imageData 完整消息。durable_store 写入及读取验证 role=tool、ID匹配、content:str；imageData 如存在须恰有 base64/mediaType 两个 str 字段。journal拒绝 imageDelivered，标记只属于 checkpoint 投影。
- `flushReadImages(messages) -> list[ChatMessage]`：无待投递图返回原列表，有图返回deepcopy候选；仅扫描当前 history 的未标记 tool.imageData，合并为一个 user 图片消息，并在候选 tool 上置 imageDelivered=True。user 消息没有内部标记；说明文字逐字来自冻结 loop.ts。
- `Conversation.replace_context(..., reset_prompt: bool = True)`：原压缩默认语义不变；root图片批末使用 `await journal.replace_context(session, flushReadImages(session.messages), reset_prompt=False)`，提交确认后再交换，保留 lastPromptTokens/lastSentLength。无图可按返回值身份判断跳过提交。
- `Conversation.open` 先从 journal 补缺失工具配对，再独立flush当前history；一次 checkpoint 提交含图片和标记，确认后交换。即使图片tool pair已在checkpoint，也能补未投递图。压缩后history已无旧工具时不扫描旧record重新注图；journal结果始终不写投递标记。

## 来源与验证边界

只读冻结 `dao-f17e189-7ac654a0dc06` 的 tools/execute.ts:74–80 保留完整 imageData，agent/loop.ts:709–716 在工具批末集中注入 user 图片；D09的 ToolRecord 要求完整可配对ToolMessage。新增投递标记及原子恢复投影是落实已批准恢复契约的必要Python接线，不冒充DAO原有图片恢复测试。

白名单外层启动器→tools/run.py；固定私有 Python3.11 / 已有18包锁，合成HOME/config/temp。按root要求直接显式导入本worktree的src作定向验证；真实Conversation子进程按父进程实际载入的ruocun包定位导入根，开发时消费同一源码，最终wheel运行时消费同一安装包。没有重建wheel；最终固定产物由root统一构建。

- 新增必要确认3项通过：图片分组/候选标记、worker输入及返回快照、真实受控SQLite Conversation重开生命周期。后者覆盖已有未投递pair＋缺pair合批、旧str结果、重开不重复、压缩后不重注、reset_prompt=False保留主API统计，并最小确认错ID/错ImageData形状拒绝。
- red→green已保存：缺flush模块、可变入参被修改、旧result签名不接图片、错误工具消息未被拒绝；未扩故障/压力/排列矩阵。
- 既有test_session_worker.py与test_session_worker_independent.py源码定向回归9 passed；Ruff相关6文件通过。
- **mypy为ENV未通过**：本私有venv导入mypy编译扩展被Windows应用程序控制阻止，stderr完整保留。按root指示不探索替代入口、不新增安装、不移动DLL；由root/独审既有工具链复核，不回填类型通过。

本次真实模型/付费API调用0；人工与Windows Terminal未验。自身工程进程已归并退出，合成状态/原始失败留在本worktree `.cache/sprint-root/raw/n0-image-*`；产品候选先交独审，原始回执随后收录，不以局部结果推定整票完成。

产品候选 `ba4fa2e8087140ee391e53d2dfc81c2018f51f30` 已交root及advanced_review。随后仅将reopen用例的子进程导入根改为父进程实际载入包（源定向/最终安装验证两用），受影响既有用例复跑1 passed、测试Ruff通过，不增加独立案例数。原始命令、stdout/stderr见 [command-index.json](command-index.json) 和 raw/；源码与冻结成员指纹见 [source-members.json](source-members.json)。[source-pytest.py](source-pytest.py) 是本次显式源定向入口的原字节副本，不是新的测试框架或验收门槛。mypy ENV失败保留在 n0-image-types 原始stderr，不回填通过。

## 独审回修：图片字节碰巧匹配凭据

独审捕获 `_safe` 对 imageData.base64 与内联 data:image URL作文字替换会损坏图片。沿同一真实Conversation用例、同一合成图片，把secret设为既有base64串，先复现图片保真断言失败，再作窄修复：仅完整tool消息内、固定两字段且image媒体类型的ImageData按opaque数据deepcopy；仅type=image_url ContentPart内语法匹配的data:image/...;base64 URL保真，其它属性照常脱敏。普通文字、任意名base64字段及远程image_url仍递归脱敏，不跳过任意URL。

同一用例已验证journal ImageData、checkpoint图片URL与重开后原图均不变，同时普通文字、任意base64字段、远程URL继续出现[REDACTED]；受影响原用例复验 **1 passed**，相关两文件Ruff通过。没有新增测试案例/矩阵、schema、模型调用或wheel。mypy沿此前已记录ENV交root/独审既有链处理，不再尝试。原red/green/Ruff与本次文件指纹见 [opaque-fix.json](opaque-fix.json) 及对应raw/n0-image-opaque-*；旧source-members.json仍是前一候选的历史指纹，不覆盖。
