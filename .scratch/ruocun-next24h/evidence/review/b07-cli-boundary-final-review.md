# 70 CLI 与命令边界最终独审

固定候选 `fd4ebe65` 在已批准范围内通过独审，可供 71 消费。前一份独审保留 `3779c8fc` 的 5 项通过回执与问题首次复现。本次沿用这些结果，另复核修复和进度提醒的实际调用。

| 独立回执 | 实际结果 |
| --- | --- |
| `raw/b07-review-native-terminator-green/` | `f55a8eaa` 使用原探针。`--` 后的权限字样完整进入提示，权限模式为空且 allow 列表为空。 |
| `raw/b07-review-cli-meta-secret-green/` | `f55a8eaa` 使用原探针。`--` 后的 `--version` 进入普通入口，重复 `--api-key` 的第二个值未进入提示。 |
| `raw/b07-review-overlapping-options-red/`、`raw/b07-review-overlapping-options-green/` | 相同探针从 `f55a8eaa` 红转 `fd4ebe65` 绿。权限选项前置时，后面的 `trust` 不触发工作区信任。权限选项紧接 `--api-key` 时，key 正确识别且未进入提示。 |
| `raw/b07-review-progress-loop/` | `1cd85cc5` 来源调用用例独立 1 passed in 0.23s。第五次读取前的请求消费已保存提示，提示追加在第四个工具结果配对之后，notice 在保存确认之后。总计 6 个模型请求、5 个读取，无交互提问。 |

原 `--` 兼容回归涉及现有 `/session` 入口，沿主协调真实 6 项回执复用。`d22c2395` 对照冻结 Node 的 11 个合成参数排列，保留来源的大小写、未知参数和已知值全局过滤。RuoCun 延续原生 `--` 结束选项能力，冻结 DAO oracle 仍记录其原本将 `--` 纳入提示的结果。凭据过滤保护每个显式 `--api-key` 值，首个值决定当前临时账户。工作区信任要求原始首项是 `trust`，与冻结 `src/index.ts:222` 一致。

只读查询与变更按原运行边界处理。既有终端用例在请求活跃时证实查询不触发取消，账户切换、MCP 变更、权限更新与会话操作的实际分支先经过 `pause_settled`。退出先关闭输入所有者并等待调度收尾，再停止本地 Agent 和 Monitor。`/quit --keep-background` 的保留参数只传给 managed Shell，未确认与未授权执行仍由该 manager 原有认证、持久状态和恢复规则处理。已确认 durable Shell 的跨进程生命期沿 15/67 原实证复用，此轮普通用例覆盖退出路由和其接线。

独立回执均使用白名单环境、合成 HOME 和凭据，秘密扫描未命中。第 71 票的 eval 消费者、最终固定包及真实 Windows Terminal 体验各有后续出口。
