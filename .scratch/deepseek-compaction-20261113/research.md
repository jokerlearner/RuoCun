# DeepSeek Harness 压缩源码研究

核查日期：2026-11-13（Asia/Shanghai）。本轮只读研究官方源码及测试，**未移植、未修改 RuoCun 产品实现，也未运行 DeepSeek Harness 的测试或真实模型**。

官方仓库：`deepseek-ai/deepseek-harness`。通过 `git ls-remote … HEAD` 固定版本为 **`e8f7b93a344964de3dca1ace9e72b6e4d6de87cb`**。本文所有外链均固定到此提交；原始文件缓存在本目录的 `reference/`，`COMMIT.txt` 记录版本。

## 结论与本轮适配边界

值得参考的核心是：**统一测量请求预算 → 先做零模型工具结果裁剪 → 对工具配对完整的旧段生成结构化摘要 → 保留近期原文 → 验证实际缩小后提交**。旧摘要参与下一轮合并，不能无限追加。DeepSeek Harness 另用追加式事件日志保存原始内容，用 `surface`（模型当前可见视图）替换来缩小请求；因此“原文仍可恢复”来自存储架构，不能只靠裁剪函数实现。[预算][旧段选择][裁剪提交][摘要合并][会话架构]

**最小迁移应区分两件事：**

- 纯算法可小范围采用：头尾裁剪、预算公式、平衡切点、近期原文保留、旧摘要合并、缩小校验、有限重试。[预算][旧段选择][裁剪算法][摘要合并][缩小校验][压力重试]
- 可恢复裁剪还须先保证原文另行持久保存；DeepSeek Harness 的实现依赖事件引用、`surfaceOp=replace`、`sourceEventSeqs` 和视图回放。若只覆盖 RuoCun 的持久化消息数组，就不具备它的原文恢复能力。[裁剪提交][摘要提交][会话架构]

## 1. 请求预算：看完整请求，并给输出和压缩留空间

设 `W` 为模型上下文窗口，`O` 为本次请求预留的输出量，`B` 为额外安全余量。默认触发阈值为：

`T = floor(min(0.8 × W, W − O − B))`

近期原文预算默认 `R = floor(0.16 × (W − O))`，也可配置绝对 token 数。默认 `B=65536`，摘要输出上限默认也继承该值。配置必须满足正预算且 `R<T`，并可按 provider/model 精确覆盖。**不适合把 65536 无条件照搬给小窗口模型**；源码会拒绝没有剩余空间的配置。[默认配置][预算]

同一个 token-meter 决定触发、近期保留和缩小校验。这里也不是精确 tokenizer：基础文字估算仍用每 4 字符一个 token，含结构开销；图片另由路由估价。因此可以借鉴预算边界和统一计量，不能宣称它已解决中文 token 精度问题。[估算器]

## 2. 两阶段减量：先裁剪，再决定是否摘要

常规压力必须先达到阈值，才执行可选 tool-result-pruner；裁剪后重新测量，若已低于阈值，**不调用摘要模型**。否则选择旧段做摘要，每成功一轮重新测量，默认允许首次加一次额外压缩尝试，仍超限则报错。[压力重试][默认配置]

pruner 的具体算法是纯函数式内容变换：默认工具结果文本超过 **8192 个 Unicode 码点**时，保留前 **4096** 与后 **1024**，中间插入明确裁剪标记。跨多个 text block 计算总额度，保留非文本块及顺序，避免截断 UTF-16 代理对；不保证字素簇边界。[裁剪配置][裁剪算法]

**与“只清理很旧的工具结果”不同**：该版本扫描当前 surface 的所有工具结果，无年龄或近期轮保护，过大的最新结果也可能被裁剪。调用 ID、工具名等事件字段保持，只有 content 改变。原始结果仍在事件日志，由新结果引用并遮蔽。[裁剪提交]

本轮若直接采用裁剪算法，建议保留明确“中间内容已省略”的标记，并给原文持久化位置或历史索引。若尚未提供此位置，就须如实称为有损裁剪，不能声称可重新读取。

## 3. 旧段选择：按 token 保留近期原文，切点不拆工具组

`selectCompactableRange()` 保留首个 system 节点；从尾部累加消息 token，达到近期预算后找到候选边界。若边界跨越未完成的工具调用/结果组，就向更早位置移动，使整组留在近期原文中；不能安全压缩时返回空。[旧段选择]

边界判断基于当前模型视图中的工具调用/结果内容，不依赖用户整轮边界。一个长用户回合里已经闭合的早期工具步可以压缩。其当前实现用未完成工具调用**数量**检查平衡，不应描述成完整的调用 ID 验证器；RuoCun 迁移时可按自身消息契约维护 pending ID 集合。[工具平衡]

被服务端确认上下文超限时，路径使用 `retainTokens=0` 强制选更大的旧段，但算法仍至少留下尾部一个节点，并向前调整保留完整的最新工具组；不是清空近期历史。[溢出选择][旧段选择][溢出配对测试]

## 4. 摘要结构与抑制膨胀

摘要指令要求固定八节：原始请求与意图、关键技术概念、文件和代码、错误与修复、未完成工作、当前工作、下一步、关键背景。保留精确路径、命令、错误与必要原话；输出置于 `<compacted-summary>` 标记内。[摘要合并]

有旧 checkpoint 时，指令明确要求**合并仍有效的事实、去掉过期内容，形成单份摘要，不逐字转抄旧摘要**。这与 RuoCun 当前“原样旧摘要＋新增摘要”的策略有实质差异。此约束是模型指令；源码没有对八个标题作完整结构解析校验。[摘要合并]

此外有确定性硬门槛：**含包装的新摘要估算 token 必须严格少于被替换段**；空文本、只有 reasoning、图片输出、摘要达到 max-tokens 的不完整输出均拒绝。它没有保证一轮必定降至压力阈值，后者由重新测量和有限重试负责。[缩小校验][摘要输出校验][压力重试]

## 5. 失败、提交与并发：不能泛称“全流程原子回滚”

压缩先检查合法区间和压缩锁，记录 start，再异步生成摘要。生成后复核视图稳定，才同步追加 summary 记录及 replacement，最后记录 end。摘要异常或并发视图变化会记录失败，正常摘要失败时原模型视图保持。[事务流程][摘要提交][失败与并发测试]

自动路径要求整个 surface 稳定；手动路径可仅要求选中区间仍连续、内容与估价未变，允许区间外新增消息。手动压缩还有 flush 持久化确认。[事务流程][稳定检查]

**重要边界**：裁剪是先行独立提交，后续摘要失败不撤销已完成裁剪；提交/持久化阶段本身失败也不是所有事件都回滚。RuoCun 已有“摘要失败保留原上下文并停止”的 ADR，应保留这个产品决定，不能照搬 DeepSeek Harness 的“预先压力压缩失败仅告警继续”行为。[溢出重试][压力入口]

## 6. 超限重试：必须证明视图真的变小

只对标准 `CONTEXT_WINDOW_EXCEEDED` 做专门恢复，并尊重取消；默认最多一次溢出恢复重试，与普通网络重试预算独立。执行裁剪/压缩后，只有 `surface.replaceGeneration` 确实增加才允许重新请求；仅返回“成功”对象而没替换视图不能重试。先行裁剪成功、后来摘要失败时，已有持久减量也可成为重试依据；取消始终阻止重试。[溢出重试][无进展测试]

这一设计可以迁移为“提交后的上下文版本/摘要＋裁剪前后 token”证明，无须复制整个插件框架。但不能仅凭异常捕获就不断重发相同超长请求。

## 7. 原始转录与模型视图是两条路径

Session 是 append-only 事件日志；模型消息由 surface 的追加/替换关系派生。summary/prune 追加新事件并引用所有被遮蔽节点，旧原文事件不删除。人类转录也明确不应从已压缩 surface 渲染，否则会把历史抹去。[会话架构][原始转录][摘要提交][裁剪提交]

测试使用完整事件快照重建 Session，断言摘要后及裁剪后的模型消息与原会话完全一致，说明回放关系可恢复。**这证明回放能力，不等于已经提供按关键词检索原文的工具，也不等于所有历史自动再次注入模型。**[摘要回放测试][裁剪回放测试]

RuoCun 如希望近期先落地，可以保留当前消息存储接口，增加压缩前快照/归档及摘要中的索引引用；是否进一步引入完整事件溯源，需要另行架构取舍。

## 8. 建议的分批顺序

1. **第一批：确定性减量与有界摘要。**请求预算、先裁剪后测量、完整工具边界、近期原文、单份合并摘要、缩小/空文本/截断输出校验、有限重试。裁剪前先确保原内容有持久保存出口。[预算][裁剪算法][旧段选择][摘要合并][缩小校验]
2. **第二批：历史可回溯。**绑定会话、压缩批次、原文区间、摘要与原文归档；提供明确读取入口；在保存成功后才替换当前上下文。无需为采用头尾裁剪立即引入 DeepSeek Harness 全套事件与插件系统。[会话架构][摘要提交]
3. **继续保留若存已批准的停止行为。**不恢复 DAO 的摘要失败硬截断，也不自动套用 DeepSeek Harness 的失败后继续；小窗口余量、中文估算与结构化摘要语言需按若存当前模型能力适配。

## 许可与证据限制

固定版本根 LICENSE 为 **MIT，Copyright (c) 2026 DeepSeek**。复制或实质改写其代码/提示片段时，应按许可证保留版权与许可声明；独立实现公开算法时也应保留本报告来源，避免把来源设计写成若存原创。[许可]

本报告依据实际源码和测试断言作静态核查；未执行官方测试、未评估真实模型摘要质量、未证明默认比例对若存工作负载最优。官方当前默认摘要仍是单次模型调用；本轮没有证据支持宣称它已经提供分块递归摘要或精确 tokenizer。

[默认配置]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/config.ts#L19-L110
[预算]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/config.ts#L144-L215
[估算器]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/llm/token-meter/src/estimate.ts#L12-L61
[压力重试]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/index.ts#L315-L370
[裁剪配置]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-tool-result-pruner/src/config.ts#L6-L64
[裁剪算法]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-tool-result-pruner/src/index.ts#L63-L121
[裁剪提交]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-tool-result-pruner/src/index.ts#L124-L181
[旧段选择]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/region.ts#L107-L154
[工具平衡]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction/src/tool-pairing.ts#L28-L91
[溢出选择]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/index.ts#L292-L307
[溢出配对测试]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/tests/compaction-basic.spec.ts#L2175-L2193
[摘要合并]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/summarizer.ts#L21-L71
[缩小校验]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/region.ts#L410-L421
[摘要输出校验]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/summarizer.ts#L163-L220
[事务流程]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/region.ts#L173-L275
[稳定检查]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/region.ts#L430-L467
[摘要提交]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/region.ts#L470-L508
[失败与并发测试]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/tests/compaction-basic.spec.ts#L1209-L1291
[压力入口]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/index.ts#L155-L173
[溢出重试]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/index.ts#L213-L256
[无进展测试]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/tests/compaction-basic.spec.ts#L2196-L2213
[会话架构]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/core/session/src/index.ts#L548-L556
[原始转录]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/core/session/src/surface.ts#L77-L93
[摘要回放测试]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/tests/compaction-basic.spec.ts#L1027-L1064
[裁剪回放测试]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-tool-result-pruner/tests/tool-result-pruner.spec.ts#L269-L278
[许可]: https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/LICENSE#L1-L21
