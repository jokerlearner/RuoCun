# 71 eval 与恢复隔离独审

固定候选 `4d258e33` 通过独审。实现为 `30d78b0d` 与 `02ac776d`，验证分别来自 `d01e11c3`、`1056703f`、`4d258e33`。复验使用 Windows 白名单、合成 HOME、合成凭据与回环服务，三个原回执秘密扫描均未命中。

| 独立回执 | 验证结果 |
| --- | --- |
| `raw/b07-review-eval-entry/` | 1 passed in 3.73s。普通入口在三种开关组合下都真实 Read。无禁用时载入项目指令、磁盘与嵌套技能、自定义 Agent、记忆、Hook 和 MCP。`--eval` 保留内置 Skills 与 Hook，关闭上述磁盘注入、Web 工具和 MCP。显式叠加 `--no-skills --no-hooks` 后内置 Skills 与 Hook 也关闭。 |
| `raw/b07-review-eval-mcp-recovery/` | 1 passed in 16.19s。原 54 HTTP 用例扩展真实 CLI、回环 MCP 和 SQLite。对已确认会话恢复时重建首 system，保留已配对工具和其它历史，模型只新增一次请求，MCP 目录和协议均未恢复。未知写入会话在 eval 重开仍返回 74，模型和 MCP 请求数无增量，原 SQLite 工具记录逐条相同，真实外部 effect 保持 1。 |
| `raw/b07-review-eval-queued/` | 1 passed in 3.33s。真实 SQLite 旧队列在普通 CLI 加 `--eval --continue` 重开，旧磁盘技能投影从执行路径移出，模型请求为 0。原输入 ID、原 payload 与用户、助手历史保留，队列状态持久为 discarded。 |

冻结 `src/index.ts:293–328` 确认 eval 关闭磁盘 Skills、自定义 Agent 和命令、记忆启动注入、MCP、项目指令与 Web。现范围已交付的内置 Skills、Hook 和显式记忆工具依照来源保留相应开关行为。源代码在启用 `--no-memory` 时仍执行启动记忆 GC，并保留 MemoryRead 和 MemoryWrite，eval 的隔离因此是通道隔离。显式 `--no-skills` 关闭内置与磁盘注入，原范围外插件功能沿已定范围记录。

冻结来源 `src/index.ts:1169` 在启动过滤后仍安装文件访问动态发现回调，造成已禁用的磁盘技能可在 Read 后重新出现。候选把文件访问与安装后的动态接入绑定同一禁用策略，普通 Read 保持工作。恢复旧队列时，当前启用的内置投影可通过现有解析重算，禁用且无可用投影时用现有 SQLite 丢弃状态保存原记录。原未知工具 journal 继续决定恢复阻断。

真实 MCP 和队列的红色回执、候选来源差异保存在 `batch-07/n71-recovery/`。本记录证明第 71 票的自动技术出口，最终固定包和真实 Windows Terminal 体验归各自里程碑。
