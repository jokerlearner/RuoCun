# 阶段 A r2 独立 Spec 复核

固定候选 `bccbb57062a5518aad8ee4882eae4a1eef3429e6`，仅审查 `03893b3..bccbb57` 的产品/测试差异及原三项 P2；未重新展开完整审查，未写产品/测试，未调用真实 API。

1. **Unicode P2：关闭。** 规格 `spec.md:11` 的静态 Skills 可用性缺陷已修复。`client/client.py:421`、`client/resilient.py:478`、`session/contract.py:228`、`session/durable_store.py:144–146` 在 JSON 序列化后的 UTF-8 边界转义代理项，原目录按 UTF-16 单元截断的行为保留。普通合法 Unicode 字节不变；持久摘要与数据库 JSON 采用相同转换，未发现相关不一致。现有产品 fixture 已加入 219 普通字符后接 emoji 的原复现输入。

2. **兼容来源诊断 P2：关闭。** D09:127 的生效/覆盖状态现在来自真实装配结果：`agent/runtime.py:127–130` 使用 profile selection；`skills/runtime.py:105–123` 依据 realpath/name 覆盖后的原对象计算生效、覆盖、禁用与 paths 未匹配；`project_doc.py:30–45` 报告实际注入、重复或空内容。`runtime.py:284–285` 输出这些状态并优先保留读取错误。去重、优先级及扫描范围没有因诊断改变。

3. **未确认保存成功标记 P2：关闭。** `agent/runtime.py:365–369` 先检查 blocked，仅显示“最后确认保存点”和“当前保存结果未确认”后停止；当前保存成功标记位于未阻塞分支，符合规格第4条及 D09:77 的确认边界。

本次限定 diff 新发现：0。执行证据由主审查者在绑定 r2 的仓库外固定安装中复跑既有产品、ledger 及同一 Unicode 单例；本报告不冒称已独立执行这些命令。Standards 轴不在本报告内，真实模型/Terminal/人工体验仍 pending。
