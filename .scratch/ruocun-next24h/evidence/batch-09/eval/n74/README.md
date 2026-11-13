# 74 · 反思评估

来源为冻结 DAO evals/reflect/grade.ts、grade.test.ts、run.ts，以及六个原样保留的用例。通过产品 unified_reflect 的 fork 调用和真实本地 SSE 验证反思与独立评审请求。评审按语义 rubric，工程不比较 advisory 字符串。

- 源评分模块尚不存在时为红灯。实现后五条源评分断言通过。
- 六个冻结用例实际通过 CLI 批处理，包含三个通过、两个失败和一个无效。漏报与误报均进入报警 P/R/F1，JSON 缺 onTrack 的结果记录为无效，没有把产品兜底默认值算作在轨。有效样本 P/R/F1 各为 0.5，数值来自刻意设计的合成响应。
- 最终显式 pytest 六项通过，Ruff、Mypy 通过。配置用合成账户，报告未出现该密钥。实际费用和真实模型质量均未验证。

独审回修复用同一 SSE 场景。NaN 在反思协议校验层即判无效。确有合成密钥的 advisory 在交给语义 judge 之前替换为 [REDACTED]，JSON 与 Markdown 报告均无明文。红绿回执见 reflect-constant-red、reflect-constant-green。
