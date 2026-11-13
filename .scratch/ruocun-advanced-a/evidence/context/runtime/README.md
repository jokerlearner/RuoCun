# A03 普通入口上下文控制器

基线 `c06d75e61f62a70f1394f0f8cf17e6691ed7290d`，已合入稳定 `facc7dd77dab05b3023d481c38c857f74d4d00f2`。只新增 `agent/context_runtime.py`、九节摘要资源和本票测试/证据；旧 compact 模块及测试仅将“Q2未决”描述改成已确认保留停止，无行为修改。未改 root 的 loop/runtime/Session/Conversation/CLI/共享类型。

## 接口

`ContextManager(session, journal, ctx, options, env, notify, *, request=None, cache_sink=None)`：

- journal 只消费已审 `save(session)`、`replace_context(session, messages)`、`redact(text)`；正式入口传现有 Conversation，不建第二份 Session/DB。
- request 为同步 `(StreamChatOptions, ResilientContext) -> ResilientResult`；控制器用 `asyncio.to_thread` 调用，未注入时复用 `streamChatResilient(..., env=env)`。env 是入口的同一个可写映射，命令只写原生 RUOCUN 键，不修改主机全局环境或数据库。
- `context_window` 是进程级窗口；无手动锁时随当前 Session.model 联动默认目录。`max_turns` 保留来源 Number||Infinity，`budget_hard` 仅严格 `1`；有效正有限 MAX_BUDGET 赋 Session.budgetCNY。
- `should_compact()` 保留来源库按当前消息粗估、85%含边界的接口。普通入口的回合间及轮内触发均按冻结 index.ts:1554/1573/1870/1895，实际采用 `(session.lastPromptTokens or 0) >= manager.context_window * .85`；分类粗估不替代 API 实际值。在已完成工具配对的安全边界调用 `await manager.compact()`。
- `compact() -> str` 生成候选，成功后只调用 Conversation.replace_context，由已审实现完成“提交确认→交换”。notify 输出一条来源样式的已压缩/无需压缩提示，并返回同文本。
- `await command(line) -> str | None` 只处理 cost/usage/context/context-window/status/effort/compact；未知命令 None；`/compact` 成功返回空字符串表示已处理，避免重复输出 notify。查询不追加用户输入、不提交 checkpoint。
- options 保持调用方引用；`options['tools']` 供 `/context` 的工具定义粗估，ctx.skills 供目录描述统计。摘要请求移除 tools/parallelToolCalls，不会执行模型返回的工具。

root 接线顺序：先 await command，结果非 None 则按已处理命令消费；其它文本沿既有输入账本接纳。进入主轮后使用上述窗口/预算/压缩回调；CompactionFailed 停止该轮，InterruptedError 走取消出口。不要在未决工具上压缩，不因 failed command 重放原工具。

## 来源与明确差异

只读冻结 `dao-f17e189-7ac654a0dc06`：index.ts:1061–1062（预算）、1432–1527（窗口/摘要/熔断）、1968–2038（context）、2242–2282（effort/window/status）；agent/loop.ts:194（轮数），commands/commands.ts:61（cost）。沿既有 D09 原生优先别名、profiles.contextWindowFor、getAgentModel、formatTodos 和 compactMessages。

九节 COMPACT_INSTRUCTION 从 index.ts:1452–1468 的真实模板提取；JS cooked 字符串的 CRLF 按运行时规则转 LF，无插值/转义展开，资源 SHA-256 `329afeb2b7415551cd56f5f81518228e0238d329cb7d90cd0adcf063623787ee`，详见 [来源指纹](compact-instruction-source.json)。默认摘要模型为当前主模型，SUMMARY_MODEL 可显式覆写；extra 恰为 thinking disabled / temperature 0。只保留 `<摘要>` 文本；无标签时保留正文并剥离已闭合 `<分析>` 块。没有新增摘要质量评分。

ADR-0012 的用户决定替代来源硬截断：摘要失败、partial、取消均不替换原模型上下文，原已确认输入账本由 Conversation 保持。空文本/空摘要块判为无效并停止，是本控制器相对来源 `(摘要为空)` 占位的具体实现差异，不声称用户逐项确认过该细节。

已收到的摘要 usage 在请求线程结束后回到业务循环按实际摘要模型记一次，onUsage 与返回 usage 不重复累计。失败/取消也保存原上下文和新增累计 token；摘要草稿不进入主对话。审计只传来源 summary 的空 sys/tools/tail，日志无摘要正文。连续三次摘要失败打开默认五分钟冷却，超时允许试探，成功复位；用户取消不计模型故障。无可摘要消息仍沿 compactMessages 无操作返回。

R1：token 标签明确可能含历史，费用和预算明确仅本次进程、历史费用不完整。文字 `/context` 保留窗口/API实测/分类/15%预留等关键内容，分类标粗估并将既有摘要计入历史；不移植完整 TUI 图条、MCP及插件行。保留所选命令范围，未扩其它命令。

## 验证

沿 tdd 技能及 ADR-0009：入口代码没有独立 DAO Vitest 控制器测试，本次为来源提取断言和必要 Python 接线确认，**不冒充新增九条 DAO 原测试通过**。首个缺模块、窗口/effort命令、摘要成功、失败/partial/空摘要、请求异常后 usage 保留、取消和报告查询均保留真实 red→green。中途绿色候选暴露窗口 env 写成科学记数法的来源差异，已按 String(number) 的普通整数形式修正，失败保留。

最终定向 `tests/test_advanced_context_runtime.py` **9 passed**；新产品文件 mypy 通过，相关四文件 Ruff 通过。摘要资源在实际非 editable wheel 安装中加载，hash 与冻结模板一致。没有堆追加故障/竞态/冷却排列矩阵。全量回归由主协调在最终候选统一执行。

工程进程均外层清空环境启动器→tools/run.py、固定私有 Python 3.11 与18包锁、合成 HOME/config/temp，真实模型 API 0 调用。原始失败与命令回执留在本 worktree `.cache/sprint-root/raw/`；验证摘要及最终源码/wheel/installed 绑定随本目录保存。真实模型、Windows Terminal、人工体验、最终普通 CLI 整批出口不由本票局部结果推定通过。

固定产品提交 `2d0b2169a2bcc9d1b6bd49edead421598afd59fd` 的同一 wheel 已非 editable 安装；86 个包文件均完成源码=wheel=实际安装 SHA-256 绑定，wheel SHA-256 `96baaedf38441075ca64c4e7cfe37c311909cdee3aed7d1dc4d81aaadc36998f`。见 [candidate-binding.json](candidate-binding.json)、[command-index.json](command-index.json) 和 [red-green.txt](red-green.txt)。绑定成功回执单列 [bind-receipt.json](bind-receipt.json)，不会把正在执行尚未落盘的自身回执伪造进索引。私有环境、不可变 wheel 与合成状态保留，本次进程均已归并退出。

独审后的文字修正：`/context` 末句明确“自动压缩阈值85%；触发按上次主模型API用量，分类估算不代替实际值。”root 普通入口的两处消费已统一采用上次主模型 API 用量；原 should_compact 粗估库接口、九项断言及历史产物绑定均保留。此提交仅修正文案与说明，按主协调要求未扩测或重建产物；以上绑定属于其明确记录的前一产品提交，最终集成产物由主协调统一绑定。
