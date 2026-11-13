# E01 最后收口：Session／费用基础

日期：2026-11-10。实现分支 `codex/e01-context`，起点 `12a4fa1ae201456dc97ee24f1ee8f1c31f309f86`。

用户要求“再完成一个小模块后保存进度并停止”；主协调选择当前 Session／费用基础为最后小模块。本提交仅交付来源内存 Session 和 cost；**28 整票仍未完成，保持 claimed**。公共任务、矩阵及对应表由主协调维护，本切片不修改。

## 实际范围

- `src/ruocun/session/session.py`：来源构造、系统消息、用户消息、model/mode、累计及按模型用量桶、最近主模型 prompt、lastSentLength、原缓存骤降监听/维度归因、费用/阈值查询、摘要、clear/setModel/toggleMode。
- `src/ruocun/session/cost.py`：20 条冻结价格数据，精确模型名→归一模型名→未知模型 pro/flash 回退；环境价格覆盖；按输入命中/未命中/输出估算；分模型汇总及人民币格式。
- `tests/test_context_session.py` / `tests/test_context_cost.py`：冻结来源的 10＋9 项既有测试语义迁移，没有新增故障/竞态/压力矩阵。

保留 camelCase 来源接口。`Session(systemPrompt, model, *, env=None)` 的可选 env 仅用于合成环境注入，未提供时费用查询按来源读取当前环境；没有价格快照。用量采用四个 camelCase 键的 `UsageTotals` 映射，消息仍使用既有宽松 ChatMessage。`addUsage(u, model=None)` 只累计来源字段；`cached_tokens` 归一仍属于已实现 client.normalizeUsage，不在 Session 重复处理。环境价格沿 D09：RUOCUN_ 同名键优先（包括空值），DAO_ 仅回退；已知价格不受环境覆盖。价格数据是冻结来源数据，未联网更新。

`clear()` 与来源一致重置消息、上下文计数、累计/分桶用量和最近命中统计，保留模式/模型/预算及前缀指纹字段。预算这里只实现 overBudget 查询与摘要；提醒一次/硬停属于 loop，本切片没有冒充完成该接线。

## 来源及校验

统一快照 `dao-f17e189-7ac654a0dc06`，基准 `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`。仅从 source.zip 解出四个来源成员读取；未写活动 DAO。各成员长度/sha256 与 manifest 一致，完整价格字典与冻结源码逐项一致，见 `source-validation.json`。

| 冻结成员 | SHA-256 |
| --- | --- |
| src/session/session.ts | 14c9aad3d94ef38c7f06b2c5854808e6d7d90eba82a34c44a4a0a2b85c59104b |
| src/session/session.test.ts | da9e746d0bdd3d59200e94ef5bb43a487a9dfbbb166d8ccd6eb464c6b4689722 |
| src/session/cost.ts | 38e9ca91cb239e57bf8d82891bf87db0251e3fc4c36e8ccca18b48d2dcecdcbe |
| src/session/cost.test.ts | 939d2e2b178237389149a0d4a7672075a96a7ed2bc16d1b7b713632676c85d99 |

来源版权与 MIT 许可见根目录 NOTICE.md／LICENSE。Session / cost 测试按来源顺序对应如下，逐项运行结果见 `raw/e01-source-green/stdout.bin`。

| 来源 it 描述 | Python test（对应文件内） |
| --- | --- |
| starts with the system prompt and given model | test_starts_with_system_and_given_model |
| appends user messages | test_appends_user_messages |
| clear resets to just the system prompt | test_clear_resets_to_system |
| setModel changes the model without touching messages | test_set_model_keeps_messages |
| toggleMode flips between normal and plan | test_toggle_mode |
| accumulates usage and computes cache hit ratio | test_accumulates_usage_and_cache_ratio |
| tolerates missing cache fields and empty sessions | test_missing_cache_and_empty_sessions |
| onCacheBust fires when a high cache-hit prefix suddenly collapses | test_cache_bust_fires_for_high_prefix_collapse |
| P1-47 归因：命中骤降时指出变化的前缀维度 | test_cache_bust_changed_prefix_dimension |
| onCacheBust does NOT fire on a healthy or first/small turn | test_first_small_and_healthy_calls_do_not_warn |
| 按命中/未命中/输出分别计价 | test_prices_hit_miss_output_separately |
| 未命中输入 = 总输入 - 命中 | test_miss_derived_from_prompt_minus_hit |
| env 覆盖价格 | test_env_overrides_fallback_prices |
| formatCNY 小额显示更多小数 | test_format_small_amount_with_more_decimals |
| 已知非 DeepSeek 模型走各自实价 | test_known_non_deepseek_model_prices |
| 网关模型名归一化匹配：去后缀＋小写 | test_gateway_names_normalize_case_dots_and_suffix |
| 网关模型名去双后缀 | test_gateway_double_suffix |
| GLM-5.3-Flash 轻量档 | test_glm_flash_tier |
| 未知模型退化到 pro/flash 启发式 | test_unknown_model_fallbacks |

## 自动证据

Windows x64 / CPython 3.11.9。公开工具沿 requirements-dev-win311.lock，独立 `.venv`，只读复用 wb-i06 已核验 wheelhouse。所有工程命令的外层 ProcessStartInfo 先清空环境并注入白名单，再调用 tools/run.py；runner 再清父环境并指向本批合成 HOME/AppData/TEMP，禁用户配置、pytest 自动插件与 PYTHONPATH。命令完整 argv、退出码及脱敏扫描结果保存在各 raw 子目录 command.json。

| 阶段/命令 | 实际结果 |
| --- | --- |
| pytest tests/test_context_session.py（实现前） | exit 2；ModuleNotFoundError: ruocun.session.session，保留 red |
| pytest tests/test_context_cost.py（实现前） | exit 2；ModuleNotFoundError: ruocun.session.cost，保留 red |
| wheel 安装后 pytest 两文件 -vv | exit 0；19 passed |
| Ruff check . | exit 0；All checks passed |
| mypy | exit 0；45 source files 无问题 |
| build（隔离构建 sdist→wheel） | exit 0；两个产物实际生成 |

没有调用模型/付费 API，没有修改真实账户配置。没有运行全量来源 Node 测试、全产品回归、性能、真实终端或跨重启费用恢复；19 项 Python 测试的通过仅证明本切片来源语义。

## 明确剩余与停止交接

28 剩余：完整 session 持久状态/分模型费用及跨两进程连续、历史缺省处理、cache_audit 落盘/报告、主/子轮数与预算提醒/硬停实际 loop 接线、effort/context-window/cost/status 命令及手动覆盖。29 不开工。没有改 Checkpoint、worker、存储摘要身份/事务、平台、client、loop 或公共状态。

资源：本批所有 runner 命令及构建子进程均已返回并回收；没有启动模型服务、网络 helper 或可视终端。`.venv`、`.cache`、dist 与合成 HOME/原始证据缓存保留供独立复核，没有清理历史对象。峰值内存及性能未测。本切片提交后停止新增实现，待主协调独立读取并重跑相同 19 项来源测试。
