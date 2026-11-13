# 摘要原始前缀复用交付

日期：2026-11-13（Asia/Shanghai）。状态：实现、自动验证、独立复核及现用渠道真实指标通过；固定候选包已生成，日常入口未切换，未Git提交。

**B 方案已经实现。在三组预登记的现用硅基流动 DeepSeek-V4.1-Flash 对照中，新摘要首请求的加权缓存命中率为98.2162%，超过本轮90%门槛；固定B-r3旧摘要控制器三次均为0%。**这是特定受控长历史的摘要结果，不能解释成所有请求、任意任务或服务端缓存淘汰后的永久命中保证。

## 实现与对齐

1. 摘要输入改为原始消息的连续旧前缀，保留原始图片、工具正文、Hook、Todo和次序。候选裁剪仍可避免摘要；确需摘要时不使用裁剪重排版代替原文。原始输入超过实际预算时停止，保留原投影，不静默降级。
2. 同模型摘要复用本次有效请求的连接、工具顺序和定义、thinking/effort，末尾增加摘要指令。移除主轮强制工具选择和extra输出覆盖，保持摘要输出cap；显式异模型配置继续尊重，不保证主模型KV复用。
3. 摘要独立单次调用，不接入工具执行器；返回工具调用即失败。取消/截断/空/未缩小/保存未确认仍停止，原文不替换，用量只计一次。
4. 归档来源覆盖实际完整输入；重叠锚点按身份去重、raw_seq排序，保证多次摘要及分支回查顺序。目标模型预览摘要读当前旧system，最终候选单独发布新system，避免来源记错。
5. 摘要审计使用经脱敏的实际最终请求维度。原生DeepSeek官方Chat带工具时重放已有非工具回合reasoning；本次真实指标来自硅基流动，不能当作官方端点实测。

借鉴来源是[DeepSeek Harness e8f7b93摘要入口](https://github.com/deepseek-ai/deepseek-harness/blob/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb/packages/compaction/compaction-basic/src/summarizer.ts#L127-L162)。本次原始连续前缀和模式继承的约束比上游注释更明确；上游也可能因裁剪、图片投影或模型默认设置改变前缀，不能称其天然保证命中。

## 真实 API 结果

渠道为用户确认的`api.siliconflow.cn`，模型`deepseek-ai/DeepSeek-V4.1-Flash`；使用原配置原生只读凭据，材料全部合成，不读取真实会话。每臂独立系统标识、相同700条语料；seed→main→固定等待4秒→首次摘要。三轮顺序预先登记，第三轮含合成图片。没有重复发同一摘要直到变热。

| 首次摘要 | 固定B-r3旧控制器/选区 | 新产品路径 |
| --- | ---: | ---: |
| 第1组 | 0 / 28250，0% | 28032 / 28559，98.1547% |
| 第2组 | 0 / 28250，0% | 28032 / 28559，98.1547% |
| 第3组，含图片 | 0 / 28274，0% | 28288 / 28766，98.3383% |
| 加权 | 0% | **98.2162%** |

表中为供应商hit/prompt。新三次均压缩成功，最终wire消息连续前缀、工具及模式相等，估价覆盖率约99.29%；这个估价不是精确tokenizer。旧请求不等值，不能把其“摘要指令之前的输入占比”叫作真实共同前缀覆盖。

主要对照：[预登记方法和源码绑定](evidence/baseline-evaluation-1/manifest.json)、[全部18条指标](evidence/baseline-evaluation-1/results.json)。旧控制器/选择器逐字节来自当前已部署B-r3 wheel，实际执行旧`compact()`；共享HTTP客户端、Session、预算依赖与内存journal，**不是整个旧安装的持久会话运行**。

第一阶段另有27条预登记请求，新首摘要三次98.1616%、98.1616%、98.3452%，加权98.2231%，与同渠道的DeepSeek设计对应参考请求一致。[阶段一方法](evidence/live-evaluation-1/manifest.json)、[阶段一指标](evidence/live-evaluation-1/results.json)。其中reference不是实际运行上游Harness；手写old仅是近似，旧产品结论以上述固定B-r3对照为准。

探测2次＋阶段一27次＋固定旧新对照18次，共47次，全部完成、无自动重试。冷启动和主请求的低/零命中全部保留，未计入“首摘要”指标，也未删掉。全部用量按[硅基流动公开峰价](https://www.siliconflow.cn/pricing)（每百万输入未命中¥2、命中¥0.04、输出¥8）保守估算**¥1.57135704**；低于本轮¥2上限，**不是实际账户扣费账单**。

观察到新摘要生成约12.14、21.12、13.48秒，旧约5.72、6.17、6.58秒；新路径保留了思考模式，输出量也不同，不能据此声称更快或把这些数值推广到真实任务。输入缓存收益和生成时间分别看待。

## 自动与包验证

- [g5](evidence/g5/command.json)：138项直接相关回归实际通过。全仓[Ruff](evidence/rf3/command.json)、[Mypy284源文件](evidence/my4/command.json)通过；本轮没有重复运行整个历史全量。
- 独立复核：[iv2](evidence/iv2/command.json)81项通过；[iv3](evidence/iv3/command.json)真实async取消探针通过；[iv4](evidence/iv4/command.json)21项通过。与g5有重叠，不相加冒充唯一测试数。
- [pi2](evidence/pi2/command.json)：实际仓外解释器的CLI两次压缩、重启原文回查、离线旧会话升级及Todo回归，共3项通过。原pi1单页假设失败完整保留；新适配器只按next_offset继续公开CLI分页，原内容与请求数断言保持。
- [基线绑定](evidence/baseline-binding.json)：对比已部署B-r3，314产品成员仅compact.py、context_runtime.py、client.py、archive.py四项不同，其余310项一致；已有工作区改动未被回退。
- [构包](evidence/build1/command.json)与[仓外安装绑定](evidence/package-binding.json)通过。固定wheel路径`dist/summary-prefix-b1/ruocun-0.1.0.dev0-py311-none-win_amd64.whl`，SHA256 **469ae14a9655dbf63e17f506a349c373e4c64aaff476d32dd4cd611757cf6504**；314产品成员在源码、wheel、仓外安装中逐字节相等，pip check通过。

## 失败与限制

红测、类型检查失败、旧单页假设等原始证据均保留；修正与复验见[任务票](issues/01-summary-prefix.md)。未以fixture命中证明供应商收益，也未以真实命中证明长期任务质量或摘要语义完全正确。模型/工具改变、冷启动、服务端缓存未持久化或淘汰仍可能降低命中；[DeepSeek官方缓存规则](https://api-docs.deepseek.com/guides/kv_cache/)本身为best effort。

当前桌面「若存 Code」仍使用B-r3；本轮没有停止用户进程、改配置/凭据/真实会话、切换日常入口或Git提交。Windows Terminal视觉/缩放状态沿既有记录，不把此次无头CLI测试冒充人工体验。
