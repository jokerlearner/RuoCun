# 批次05 会话、监控与 MCP

用户选择 A，确认固定交付 26、46、51、52、53、54 六票。用户已明确授权开始实施。计划基线 `c389d734`，集成分支 `integration/ruocun-migration`，开始时进度 47/79；本批六票定向技术验收完成后为 53/79。

接续先核对 Git 状态，再按[规格](../ruocun/spec.md)、逐票条件及[里程碑规则](../../docs/adr/0015-batch-validation-and-packaging.md)领取任务。下表分支在启动时从包含本计划的主线提交创建，复用既有工作树、负责人和私有环境。

| 负责人 | 任务与次序 | 文件归属与计划分支 |
| --- | --- | --- |
| `/root/n24_terminal` | 46 与 26，先完成 Monitor 的执行接口，再接会话切换保护。两票之间无新增硬依赖 | `tools/monitor.py`、`agent/tasks.py`、会话列表/导出/清理模块及对应来源测试。`codex/b05-runtime`，工作树 `D:/java supplement/Firstcode/RuoCun/.worktrees/b04-agents` |
| `/root/n24_permissions` | 51 → 52、53 → 54 | `mcp/`、MCP 合成服务及对应来源测试。52、53共用 `mcp/mcp.py`，由本负责人依次集成。`codex/b05-mcp`，工作树 `D:/java supplement/Firstcode/RuoCun/.worktrees/b04-hooks` |
| `/root/n24_review` | 定向复核执行、权限、持久化及恢复边界 | 审查与合成回执。`codex/b05-review`，工作树 `D:/java supplement/Firstcode/RuoCun/.worktrees/b04-review` |
| 主协调 | 普通入口接线、共享契约和批末交付 | `agent/runtime.py`、`tools/types.py`、工具注册/搜索、配置与依赖锁、`session/conversation.py`、`durable_store.py` 等公共存储及公共记录 |

实现负责人需要调整公共文件时，先交最小接口与调用位置，由主协调写入。两条开发线并行，独审消费固定候选与已有回执。

| 票 | 开始条件 | 本票交付出口 |
| --- | --- | --- |
| [26](../ruocun/issues/26-sessions.md) | 11 已完成 | 继续/切换/分支/命名/导出与清理走真实会话；分支只复制聊天所需状态，活动 owner、后台运行和可恢复材料得到保护；切换与49的 Hooks 生命周期正确衔接 |
| [46](../ruocun/issues/46-monitor.md) | 45 已完成 | Monitor 按行批量推送 stdout，超时、persistent、TaskStop 和重开按真实执行器判定；停止结果由实际进程终态支持 |
| [51](../ruocun/issues/51-mcpstdio.md) | 09 已完成 | 普通模型入口实际调用本地 stdio MCP 工具并收到结果，配置、cwd/env、Windows命令启动及单服务失败隔离有证据 |
| [52](../ruocun/issues/52-mcphttp.md) | 51 独审集成 | Streamable HTTP、SSE、headers、配置覆盖/禁用和关闭取消按冻结来源；兼容差异按既有 D09 研究核实 |
| [53](../ruocun/issues/53-mcpcaps.md) | 51 独审集成，21 已完成 | 前5工具可见、其余搜索激活，resources/prompts、能力变更、elicitation及 `/mcp` 路由沿来源实际接线 |
| [54](../ruocun/issues/54-mcprecovery.md) | 52、53 独审集成，17 已完成 | 远端执行后断线保持未决；重开和更换工具调用ID仍受未决约束，显式恢复决定与旧证据可追溯 |

MCP 的[未知结果处理](../../docs/adr/0003-mcp-unknown-outcome-no-replay.md)从51首次发送工具请求起生效，54汇总跨传输及恢复出口。连接和能力发现可按既有策略重连；可能已执行的工具请求保留未决，进入现有恢复流程。配置来源、SDK选型与协议边界读取[D09唯一契约](../ruocun-discovery/research/09-storage-extension-route.md)，依据冻结源码和已有实验解决事实问题。

接缝检查点依次为51的客户端及执行契约、26/46的真实运行与会话保护、52/53的协议与注册、54的未知结果恢复。每项保留候选提交、直接相关的 DAO 来源测试及独审结果。遇到已确认的缺陷，沿能复现该缺陷的用例修复。

六票收口时集中运行一次默认全量、Ruff、Mypy、构包与隔离安装，并绑定产物、成员字节及回执。中间阶段使用源码定向验证。模型和外部服务验证使用合成进程与回环服务，沿既有费用授权。日常更新逐票状态和本文件，模块对应表与验收矩阵在交付时汇总。人工体验按77/78既有出口执行。

本批主要代价是 MCP 的串行链及共享入口接线，整批交付时间取决于这条链的收口。范围限于上述六票。新增费用、系统安装或既定关键行为的变化集中提交用户决定，其余实现选择按已确认来源优先规则处理。

## 交付进度

26、46、51、52、53、54均已独审集成并结题，有效进度53/79。固定产品`c85b80d5`、标准包b05-r1已完成[集中交付](evidence/batch-05/integration/README.md)：唯一默认全量实际`1621 passed, 3 deselected in 737.20s`，Ruff、Mypy231源码、4项离线冒烟、纯安装及262成员严格字节绑定通过。定向和全量结果分别保留。

| 票/接缝 | 独立技术证据 | 实际出口与边界 |
| --- | --- | --- |
| 26 | [会话独审](evidence/review/b05-sessions-review.md)、[暂停补验](evidence/review/b05-caps-paused-review.md) | 普通入口切换、分支/命名/导出/清空，Hooks完整交接，活动owner拒绝；latest只挑未完成，已完成用显式ID；只读重开保留paused |
| 46 | [Monitor独审](evidence/review/b05-monitor-review.md) | 真实stdout/最终片段、persistent、超时和实际停止；owner丢失保留历史并标记interrupted，不重启命令 |
| 51 | [stdio独审](evidence/review/b05-mcp-cli-review.md) | 实际工具schema/调用、cwd/env、单服务失败隔离，未知结果自首次工具发送起保护 |
| 52 | [HTTP/SSE独审](evidence/review/b05-http-review.md) | 三传输、headers、重定向及绝对请求deadline；SDK1.30.0 |
| 53 | [能力/命令独审](evidence/review/b05-caps-paused-review.md) | 前5可见、搜索激活、resources/prompts、能力更新及普通/mcp列表/禁用/重连/写回；无UI elicitation拒绝 |
| 54 | [断线最终独审](evidence/review/b05-mcp-recovery-review.md) | RPC明确错误与真实断线分开；effect保持1，74/持久unknown，同会话换ID无重放；SDK日志脱敏 |
| 既有子代理MCP消费 | [子专属MCP独审](evidence/review/b05-agent-mcp-review.md) | 实际父→子→子→父4次请求；独立连接关闭、转交重绑/拒绝关闭；恢复核实际连接配置摘要及精确工具目录 |

执行仍为主协调＋两个实现＋一个独审四槽。MCP链按51→52/53→54依次复核；运行线先46再26。临时借用公共运行时/会话文件的归属已交回主协调。后段运行负责人补专属子MCP消费者，协议负责人完成54，独审复用固定来源及普通CLI探针，没有为每个小模块构包。

## 保留的取舍与发现

- 分支只复制聊天/model/mode/累计token及附件引用，不复制执行账本和后台副作用。清理先以SQLite事务封存执行权，再核文件身份后删除；任何活动/未决、附件拥有者及留存运行引用的工作树均保留。资料读不全或清理失败则留下现场，磁盘回收较保守。
- Monitor保留来源工具身份，执行相同Shell计划并叠加真实命令deny/危险与未知解析审批；TaskStop以实际进程退出及心跳停止证明，不凭取消文案判成功。
- MCP原生配置写回沿既有私有目录契约；声明同名add不强制重连旧holder、禁用同名add的瞬时连接沿冻结DAO保留，重启仍按禁用状态。恢复摘要取实际holder配置，不能用新声明假定旧连接已改变。
- 未决请求不自动重做；连接/能力发现仍可重连。子专属MCP按定义字符串引用创建，普通fork保持精确父工具集合。不会声称远端exactly-once或自动恢复所有特殊现场。
- 定向集成发现原有公开项目目录的维护stamp写入失败阻断启动。区分性探针确认后，仅让非必要cleanup保持best-effort，未放松原生配置ACL。原失败、诊断及两项原用例复验保留在集中证据。
- 依赖锁采用D09 SDK1.30.0及已验证Pydantic2.14.2/core2.50.2，运行闭包37项已核官方hash并在空环境安装、导入与pip check通过。未扩展系统安装或模型费用。

模块对应表、验收矩阵已在此里程碑汇总，原始来源/技能记录保留。真实Windows Terminal完整交互/缩放及用户体验仍由77/78验收，本批自动证据不代填；没有新增真实模型或性能对照成绩。
