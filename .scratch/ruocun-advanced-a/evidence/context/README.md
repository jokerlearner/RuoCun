# A03 上下文模块候选

实现 `f65d2bc`，合入主协调 `fa5815ac0202418b98ad184c8fd6eef9734f688e` 后的源码提交为 `03517be6dda482f9bd0bddbc8bb930967ba8aa4e`。只新增本票三份产品文件、三份独有测试及本目录；未改 Session、唯一 StoragePort、主循环或 CLI。原 28/29 整票与人工状态不由此结题。

## 可消费 API

- `agent.compact.estimateTokens(messages) -> int`：来源 chars/3 粗估，字符串按 JS UTF-16 代码单元；图片固定 100 字符，assistant 工具函数名与参数参与估算。
- `shouldCompact(messages, maxTokens, ratio=.85) -> bool`：含边界的 `>=` 比较。
- `async compactMessages(messages, {"summarize": async_callback}, pinned=None) -> list`：返回候选列表，不修改原上下文。系统锚同引用、整段无 tail；旧摘要原样拼接新增摘要；可选活任务清单重新注入；摘要回调收到图片占位后的系统及全部对话。摘要模型、流、取消、用量、持久化与消息确认由主协调接线。
- `stripImagesFromMessages(messages) -> list`：图片替换为 `[image]`，相邻占位去重，未改变的消息沿用引用。
- `session.context_window.parseContextWindow(argument) -> float`：K/M/纯数字 K，非法格式或低于 1K 抛带来源提示的 `ValueError`。模型默认值复用已有 `config.profiles.contextWindowFor`；入口维护手动锁与环境，不新增持久窗口字段。
- `session.cache_audit`：`CacheAuditInput` / `CacheAuditEvent` / `CacheAuditSink` 类型，`createCacheAuditSink(sessionDir, env=None).record(input)`、`divergence(a,b)`、`formatCacheReport(events, ttlMs=300000)`。旁路 `cache.jsonl`、按 agent/subId/depth 分桶、前缀变化/delta、main/distill 前缀比较、开关和报告均沿来源。偏移和哈希采用 UTF-16。调用方应提供显式 env；仅查询 AUDIT/CACHE_AUDIT 开关，不枚举环境材料。

## 来源及差异

来源只读冻结目录为 `../b01-tools/.cache/frozen`（相对本 worktree），快照 `dao-f17e189-7ac654a0dc06`。源码和测试 SHA-256 见 [validation.json](validation.json)。本票迁移 `src/agent/compact.ts`、`src/session/cache_audit.ts`；窗口解析提取自 `src/index.ts:2251–2266`，开关提取自 `src/session/audit_switch.ts` 并复用既有 D09 原生优先别名。

明确未决差异：ADR-0012 Q2 尚待用户选择，故摘要异常目前原样透传，取消同样透传；**没有实现或默认启用来源的失败硬截断**。冻结 compact.test.ts 的 1 条硬截断断言未迁移为通过，原来源文件未改。摘要结果与已确认输入账本、未决工具及原子保存的安全接线由主协调负责。

缓存 JSON 使用 ASCII 转义编码以安全承载 JS 字符串的孤立 UTF-16 surrogate，解析后字段/文本不变；不要求与来源日志字节相等。窗口仍是来源进程级状态，未擅加会话 DB 字段。本票不实现预算/轮数/effort/status 命令，不调用真实模型。

## 验证

全程外层 `ruocun-sprint-launch-01a1c4bc.ps1` → `tools/run.py` 白名单环境、合成 HOME/config/session；固定 CPython 3.11，私有 `.venv`，18 包锁 `requirements-dev-win311.lock` 和只读 wheelhouse。全部过程回执的敏感匹配均为 false。

- 来源断言先 red 再 green：compact 成功/空操作相关 9 条、cache_audit 8 条，共 17 条。另 7 项是窗口提取、UTF-16、图片和未决失败策略的必要 Python 适配确认；合并运行 **24 passed**。没有新增压力/竞态矩阵。
- red 为缺模块/导出，以及 pin、system-only、prior-only、旧摘要增量、delta、关闭开关、main/distill 比较的真实断言失败；对应 green 与原始输出见 [red-green.txt](red-green.txt)，完整命令和输出 hash 见 [validation.json](validation.json)。
- 审阅时减少缓存 UTF-16 处理的 Python 整数列表占用，行为不变；仅复跑受影响缓存 8 条，**8 passed**。未因纯 Ruff 排版重跑 24 条。
- 定向 Ruff：6 文件通过；mypy：3 产品文件通过。首次 Ruff 的 import 排版失败保留在回执中。
- 最终合并源码已重新构建固定 `py311-none-win_amd64` wheel 并非 editable 安装。69 个包文件的源码/wheel/实际安装 SHA-256 一致，wheel SHA-256 `8f5c6a1d5e9fb32e79bb119361f2f13bcda79b0545d2853ca0171c65aacea8a2`。绑定脚本首次因当前尚未生成自身回执报错，修正为略过未结束回执后成功；失败回执保留，不属产品失败。

所有自身工程进程已退出；合成状态/原始回执、私有环境和不可变候选 wheel 保留于本 worktree 的 `.cache`/`.venv`，未删除历史材料。全量回归由主协调最终候选执行一次；真实模型、Windows Terminal 与人工体验均未验。
