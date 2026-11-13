# T02 策略实现保存点

日期：2026-11-13。产品保存点为当前工作区文件，未提交 Git；T03/T04 集成与独审尚未完成。

## 实际交付

- `compaction_policy.py`：公开 `resolveCompactionBudget`、`CompactionBudget`、`estimateRequestTokens`。预算按计划公式，默认输出真实cap使用W/4，显式输出不缩小，原生参数校验并拒绝冲突/非有限值；最终Chat/Responses请求体支持工具schema和图片估价。
- `compact.py`：公开纯候选 `buildCompaction`、兼容 `compactMessages`。候选返回messages、origins、带old_indices/new_index/kind/archive_id的replacements，以及统一口径的before/after/status；无文件/数据库写入。
- `measureMessages` 是可选最终wire计量回调；保留尾部、选段和摘要缩小比较使用同一回调，尾部扣除固定工具开销。
- 8192/4096/1024普通工具文字裁剪支持多个text block统一预算，保持非文字块及工具/图片字段；TaskWait和显式protectedIndices不裁剪。
- 先在副本裁剪，足够时跳过摘要；否则按裁剪后价格选择完整配对近期尾部，旧摘要重整、Hook保护及最新Todo钉住。
- 空摘要、没有安全旧区段及未缩小候选拒绝；摘要回调异常透传，原消息不修改。输出finish_reason/取消/持久化确认由T04控制器处理。
- 摘要资源改为八节中文单份摘要，明确旧摘要合并、证据/授权限制和归档ID由程序生成。

## 红绿与检查

按公开policy/candidate接口完成11个增量循环，证据目录从`t02-01-budget-red/green`至`t02-11-remeasure-red/green`，其中`t02-08-source-adaptation-*`记录旧来源断言与确认新行为的差异。

最终定向：**22 passed**（`t02-11-remeasure-green/stdout.txt`）。Ruff四文件通过（`t02-final-ruff`）；mypy两源通过（`t02-final-mypy`）；所改既有文件diff空白检查通过。

`t02-04-meter-green`的首次失败是测试把600中文字的chars/3量级误设为大于300，修正为独立阈值大于200；原失败保留，复跑通过位于`green-r2`。

## 来源与边界

原DAO“全部历史替换”和“旧摘要原样拼接”六处来源断言按已确认B方案改为新策略差异，测试名称有confirmed_policy标记；短fixture改为足够长的合成材料以通过严格缩小门禁，不声称原行为未改变。

固定DeepSeek Harness MIT来源为`e8f7b93a344964de3dca1ace9e72b6e4d6de87cb`，详细对照见上级research.md。中文估价仍为启发式，固定图片估价不代表真实多模态tokenizer；没有真实模型质量结论。

本保存点未修改`context_runtime.py`、`loop.py`、`runtime.py`、session、client或runtime测试。下一步由root将候选转换为已冻结ArchiveRewrite，并完成最终wire计量、真实入口和持久化集成。
