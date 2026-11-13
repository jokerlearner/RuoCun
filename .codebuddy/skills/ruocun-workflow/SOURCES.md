# 来源、适配和许可

本包 `ruocun-workflow/SKILL.md` 是依据用户已确认的 RuoCun 工作流编写的项目接入层；项目规格、决定和状态仍由 Git 中原记录维护。

`references/` 从本机已安装技能复制以下 Markdown 与许可，原始正文保持字节一致：implement-spec、tdd、code-review、codebase-design、research、domain-modeling、writing-for-agents、handoff。复制于 2026-11-05；各文件 SHA-256 见 [reference-manifest.json](reference-manifest.json)。不包含全局设置、OpenAI 专用 agents/openai.yaml、安装器、凭据或其它个人资料。

来源为 [Matt Pocock skills](https://github.com/mattpocock/skills)。implement-spec 的本地安装记录固定到 revision `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d`、路径 `skills/engineering/implement-spec`；其它技能本地没有可核实的逐项安装 revision，因此只固定所携带文件的字节 hash，不推定全部来自同一提交。

保留各包现有 MIT LICENSE（Copyright (c) 2026 Matt Pocock）。implement-spec 本地未带 LICENSE，依据其固定来源提交的[仓库根许可](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/LICENSE)补齐同一 MIT 文本；包根也带该许可。保留项目既有 DAO 许可与 NOTICE，这些技能不是 DAO 产品资源。

## 工具适配

原技能中的 Skill tool、后台代理等是抽象工作流要求。在 WorkBuddy 中使用实际可用接口；没有技能调用工具时显式读取引用文件。不能假称调用过不存在的接口。原始参考中的自动派发要求仍须通过独立代理或明确的手动独立任务实现。

用户在当前项目已经确认了测试入口/语义边界、单一 CONTEXT、AGENTS、任务拆分、允许的本地提交合并及人工最终验收时点；本项目记录和用户授权优先于通用参考中的重复确认提示。新行为边界仍需按项目规定处理。

本包不修改全局 WorkBuddy 设置，不授予权限、不安装软件、不触发网络或模型调用。项目加载行为尚待用户客户端确认，文件读取方式可以直接使用。
