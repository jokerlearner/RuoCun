# 主系统提示恢复与待选适配

2026-11-13 用户决定采用 A1–A5，B1–B4 沿用旧规则，Windows 沙箱后置。A1–A5 已应用到两份主模板、正式入口能力附录和 Skill 附录。[Windows 沙箱范围决定](../adr/0008-source-first-sandbox-parity.md)

适配前曾按用户要求恢复提交 `00a1c78d` 的两份主系统提示资源，当时中文为 334 行、英文为 345 行，原始字节与该提交一致。随后按 A1–A5 修改相应位置。视觉能力、反思、无人值守和长任务指令的动态正文按旧版执行。

保留当前的长任务头部识别常量，用于读取已有会话。恢复两种反思示例占位符的替换，避免模板标记进入模型请求。

[中文模板](../../src/ruocun/prompt/resources/system_prompt.zh.txt) · [英文模板](../../src/ruocun/prompt/resources/system_prompt.en.txt) · [组装入口](../../src/ruocun/prompt/system_prompt.py)

## 已恢复的执行约束

旧模板本身包含集中澄清、180 秒耗时预评估、后台禁止轮询、TaskWait 单独调用、未知结果禁止重放、取消后确认退出、持久化兼容、独立 verify 和交付证据检查。恢复时按原句保留。英文还包含同工具、来源和参数连续失败两次后换方法的条款。

## 已批准并实施的事实适配

以下五项均按用户选择采用。

| 编号 | 原文或现象 | 若存当前事实及建议 | 取舍 |
| --- | --- | --- | --- |
| A1 | 旧中文 275 行、英文 285 行断言工作区外路径会被沙箱拒绝。冻结参考与若存实际都支持审批区外访问，Windows 都没有 OS 沙箱。 | 按实际权限处理区外访问，说明 Windows 没有 OS 沙箱，macOS/Linux 的后端可选。同步修正能力附录里笼统的“无 OS 沙箱”。 | 已采用。纠正提示与两者实现之间的偏差，增加平台说明。 |
| A2 | 模板建议编辑 notebook 时使用 NotebookEdit，并用 cron_*、lsp、config 等名称指代工具。 | 以注册目录为准，使用 CronCreate/CronList/CronDelete、LSP、Config、Monitor 及规划工具的实际名称。NotebookEdit 仅在实际可用时使用。 | 已采用。减少无效查询和调用。 |
| A3 | 模板将命令工具统称 Bash。 | 增加 Windows 默认 cmd，调用 PowerShell、pwsh 或 Bash 时显式指定解释器的说明。 | 已采用。统一平台说明。 |
| A4 | 模板只说明自动压缩，未交代摘要失败。 | 写明异常、空摘要或保存未确认时保留原上下文并停止本轮，修复后重试。 | 已采用。主模板补齐已确认并已实现的兜底。 |
| A5 | Skill 的加载结果仍附带“完整 TUI 后置”，与完整终端交付不符。 | 修改为支持完整终端交互，仍按实际可用工具执行。 | 已采用。修改 Skill 工具附录。 |

[A1 平台后端](../../src/ruocun/platform/sandbox.py) · [A1 区外权限](../../src/ruocun/permissions/runtime.py) · [A2 注册目录及 A3 能力附录](../../src/ruocun/agent/runtime.py) · [A3 命令工具](../../src/ruocun/tools/exec_shell.py) · [A4 压缩控制](../../src/ruocun/agent/context_runtime.py) · [A5 技能附录](../../src/ruocun/tools/skill.py)

### A1 源码核对

本轮重新读取冻结归档中的实现。DAO 的 `src/tools/sandbox.ts` SHA-256 为 `2f5dbb56b15529eeaafe6fa8bd528c2e32b1e0d739412c913a78b2ebfa6ebb4f`，与当前本机参考目录的同文件一致。第 42 行只在 `DAO_SANDBOX=1` 且未请求绕过时进入隔离，第 65 行对 Windows 等未支持平台返回错误。macOS 使用 sandbox-exec，Linux 使用 bubblewrap，网络默认允许，需独立开关才禁网。两个实现的平台边界相同。[既有来源决定](../adr/0008-source-first-sandbox-parity.md)

区外访问另由应用权限系统处理。冻结 `src/tools/paths.ts:32–39` 把区外路径交审批；`src/tools/read_file.ts:45–50` 调用外部读取授权；`src/tools/paths.ts:49–53` 把写路径裁决交权限系统。因此，旧模板中的笼统禁止描述与参考项目自身的运行行为也存在偏差。

审批控制是否允许一次工具调用。OS 沙箱通过系统机制约束被启动的命令及后代进程。macOS/Linux 的现有配置主要限制区外写入，仍允许读取大量系统文件；启用写入沙箱并不等于区外文件不可见。实际保护范围取决于启用状态、平台和参数。

源码中的 OS 包装作用于 Shell 子进程，不能扩展解释为主程序的所有 Read/Write、Hooks 或 MCP 都已隔离。Windows 受管进程的 Job Object 用于进程树管理和取消回收，不能提供目录或网络隔离。

失败兜底有一处可具体比较。DAO 的前台 `exec_shell.ts:185–186` 和耐久后台 `managed_shell.ts:176–178` 会在请求的沙箱不可用时失败；旧 `process_manager.ts:178–181` 分支则可能回退普通 Shell。若存 `sandboxExecutionPlan` 在沙箱返回错误时统一抛出 `SandboxUnavailable`。这是源码分支核对结果，不能据此宣称若存在所有安全方面更强。

## 沿用旧规则的决定

| 编号 | 现状 | 本轮决定 | 代价 |
| --- | --- | --- | --- |
| B1 | 主提示组装函数支持 lang，但正式入口没有传入该值，能力附录也固定中文。 | 沿原接线。 | 正式入口默认使用中文主模板。 |
| B2 | 原文要求跨 3 文件、后端/API 或基础设施变更派 verify，再抽跑 2–3 条命令。 | 按原文执行。 | 严格逐次复核增加模型调用和时间。 |
| B3 | 英文明确相同方法连续失败两次后换工具、来源或协议，中文没有固定次数。 | 保留原双语差异。 | 中文与英文的重试次数引导不同，未知结果仍不得自动重放。 |
| B4 | 原文要求自动记下可复用经验和修正过时记忆。--no-memory 关闭启动注入等流程，记忆读写工具仍可注册并受权限控制。 | 沿原开关和权限语义。 | 关闭启动注入后，模型仍可能通过已授权工具读写记忆。 |

[B1 正式入口](../../src/ruocun/agent/runtime.py) · [B2/B3 原模板](../../src/ruocun/prompt/resources/system_prompt.en.txt) · [B4 记忆工具](../../src/ruocun/tools/memory_write.py)

## A1–A5 验证

适配后中文模板 336 行、英文模板 347 行。主线的 CLI 对话接线、上下文控制和压缩测试通过 30 项；独立复核的提示组装和 Skill 工具测试通过 30 项。两组均使用白名单合成环境，退出码 0，日志扫描无命中。Ruff 与差异格式检查通过。

独立复核确认 B1 的正式入口调用、B4 的记忆工具注册和 B2/B3 的相关模板条款与适配前一致。回执分别位于 `.cache/prompt-adaptation/raw/a1-a5-entry/` 和 `.cache/prompt-a-adaptation-review/raw/independent-a-review/`。

本次交付为源码与决定记录更新，正式安装包留待后续集中构建。

## 适配前恢复证据

模板摘要和行数见 `.cache/prompt-restore/restored.json`，本轮前的相关文件存于 `.cache/prompt-restore/before/`。恢复后的源码通过 47 项提示组装、CLI 对话接线、长任务和上下文控制检查；16 种语言、交互和反思开关组合均没有未替换占位符，Ruff 与差异格式检查通过。独立复核确认模板字节、动态正文和待选清单与源码相符。本轮使用合成输入。正式安装版本应在用户选择适配内容后绑定新的交付候选。
