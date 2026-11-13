# 01 — 一次确认新增的 Python 测试与验收入口

Type: task
Status: resolved
Blocked by: none
用户体验验收：not-required（本票只确认开发入口，不替代产品体验验收）

## 规格与范围

[完整迁移规格](../spec.md) 的 T-03 集中列出全部新增入口：T-N1 pytest、T-N2统一高层验收驱动、T-N3 Ruff、T-N4 mypy、T-N5标准包build。
原CLI/协议/恢复脚本/评估/真实模型/Windows Terminal/安装等已确认语义入口沿用，不重新审批。

用户已一次确认采用上述全部入口；统一驱动组织oracle/offline/runtime/protocol/live/terminal/install套件，不增加产品业务或绕权限API。
依赖版本、终端/协议/平台库、构建后端等仍由对应地图票实证确定，不包含在本次入口确认中。

## 验收条件

- 用户对规格T-N表给出采用或调整意见，意见记入Comments及规格。
- 已确认入口和新增入口有明确区分；不会借本票反复确认已有范围。
- 若发生新的内部测试端口需求，先登记最高层边界及影响，不默认为已批准隐藏API。

## 验证证据

用户于2026-11-05对集中问题回复“全部采用（推荐）”，确认T-N1至T-N5及统一驱动全部子套件。
结论已同步规格、CONTEXT、对应表和验收矩阵；记录校验见同目录上级validation.json。
本票验收的是入口决定，不代表依赖已安装、入口已实现或产品测试通过。

## Comments

- 2026-11-05：根据用户“已确认的测试入口直接沿用；新增测试入口集中列出，供我一次确认”创建。本轮先完成规格和两个持续维护附件，再提出本次集中确认。
- 技能依据：[to-spec](C:/Users/PC/.codex/skills/to-spec/SKILL.md)：“Check with the user that these seams match their expectations.” 这仅要求确认新增入口；项目tracker要求前置满足后才标ready-for-agent，不能将尚有技术依赖的完整迁移误标为立即可实施。
- 2026-11-05：用户答复“全部采用（推荐）”。确认pytest、统一高层验收驱动（oracle/offline/runtime/protocol/live/terminal/install）、Ruff、mypy、build。无需再审批这五项入口；新的实质边界变化另行登记。本票完成，Status更新为resolved；地图中尚未关闭的技术依赖保持原状态。
