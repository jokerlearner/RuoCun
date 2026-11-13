# 原模块 → RuoCun 模块对应表

Status: maintained
更新：2026-11-12。本文是唯一权威对应表；各行保留来源及拟实施位置，最终交付的实际证据按下方汇总和责任票读取。当前状态读取[实施进度](implementation.md)。

本表在里程碑汇总，日常实施变化读取任务票及[当前批次](../ruocun-next24h/plan.md)。更新节奏见[ADR-0015](../../docs/adr/0015-batch-validation-and-packaging.md)。

当前范围排除NotebookEdit、自定义Markdown模板和组合插件。相关来源模块、来源测试与交叉索引继续保留。MM-447/448中原生固定命令的语义和测试继续对应70及相关任务。Skills、Hooks、代理继续从各自保留的配置来源加载。完整TUI继续交付。[ADR-0014](../../docs/adr/0014-terminal-and-scope.md)

## 最终交付核对

2026-11-13新增B方案不改原805项来源计数；新增对应见下表，实际状态和固定候选见[执行记录](../deepseek-compaction-20261113/execution.md)。

| 固定DeepSeek来源/若存既有权威 | Python位置 | 适配 |
| --- | --- | --- |
| compaction-basic/config、token-meter | agent/compaction_policy.py、context_runtime.py | 最终请求估价、小窗口余量与实际输出cap |
| compaction-basic/region、tool-pairing | agent/compact.py | 按调用ID配对保尾、系统/Hook/Todo保护 |
| tool-result-pruner、checkpoint/summarizer | agent/compact.py、resources/compact.zh.txt | 头尾裁剪、旧摘要重整、缩小门禁、原文引用 |
| session/surface概念；StoragePort事务 | session/archive.py、contract.py、durable_store.py、storage_worker.py | 原文/派生/投影同事务，主子范围及幂等回执 |
| Conversation/RunRecord恢复 | conversation.py、run_agent.py、tasks.py、resume_agent.py | 确认后换投影、恢复血缘、闭包及附件 |
| B新增查询/生命周期 | archive_command.py、tools/archive_read.py、log.py、upgrade.py、cleanup.py | 受限回查、分段导出、备份升级与共同清理 |

805 个来源成员与对应行、374 个验证资产及 215 个案例族均已和冻结清单及责任票复核。实际实现和验证以 [85 的范围记录](issues/85-delivery.md)、[责任覆盖索引](task-coverage.json)与[验收矩阵](acceptance-matrix.md)为入口。脚本的原路径、预期及拥有任务继续保存在 [D11 逐项清单](../ruocun-discovery/research/11-test-replay-gates.assets.json)，实际处置按 D11 分组核对。

| 来源脚本 | 本轮实际处置 |
| --- | --- |
| 5 个确定性脚本与 2 个 live 后台脚本 | 记忆、持久化、等待和恢复的保留断言走 Python 入口和离线协议回放。实况模型运行按 V1 保留来源。[运行时](../ruocun-next24h/evidence/batch-09/eval/n76/README.md) · [恢复](issues/17-recovery.md) · [记忆](../ruocun-next24h/evidence/batch-09/eval/n73/README.md) |
| 38 个模型专题与 3 个 VHS 演示 | 保留各自的轨迹/模型协议、源位置和缺失材料记录。专题付费评分按 V1 移出，演示中的终端及反思行为分别用实机和受控评估验证。[D11](../ruocun-discovery/research/11-test-replay-gates.md) · [实机](../ruocun-next24h/batch-final.md) · [反思](../ruocun-next24h/evidence/batch-09/eval/n74/README.md) |
| 4 个记忆/缓存/反思脚本和 1 个协议诊断 | 本地合成评估、脱敏报告及实际 SQLite 轨迹覆盖保留入口。[记忆与缓存](../ruocun-next24h/evidence/batch-09/eval/n73/README.md) · [反思](../ruocun-next24h/evidence/batch-09/eval/n74/README.md) · [轨迹](issues/72-evalrunner.md) |
| 3 个预览、1 个欢迎资源生成和 1 个版本同步 | 已安装产品的真实终端验收欢迎图、缩放和文字路径。随包保留冻结嵌入帧，原始 PNG/生成清单与独立授权缺口为 E-02。Python 包与 CLI 使用单源版本。[实机](../ruocun-next24h/batch-final.md) · [发布](../../docs/release/batch-09.md) |

## 批次06实际对应

保留原DAO模块、冻结来源及技能记录；行中原始文件对应持续可追溯。[批次记录](../ruocun-next24h/batch-06.md)

| 票/来源范围 | 实际位置 | 独立证据与边界 |
| --- | --- | --- |
| 33，MM-570–580/695 | `repomap/`、`tools/repo_map.py`；原WASM绑定由原生tree-sitter/grammar及loader替换 | [代码地图](../ruocun-next24h/evidence/review/b06-repomap-review.md)。7grammar实际解析，排名/预算/缓存及启动尾部注入；原WASM职责保留、依赖和MIT原文另记 |
| 55，MM-485/487/489/490/666 | `lsp/`、`tools/lsp.py`、运行时配置及资源收尾 | [LSP](../ruocun-next24h/evidence/review/b06-lsp-review.md)。窄协议/9操作/Windows位置与URI、取消/关闭；真实服务器只代表已测语言，未承诺任意server兼容 |
| 22/23，MM-647/649/651/711/740 | `tools/fetch_cache.py`、`fetch_extract.py`、`fetch_url.py`、`ssrf.py`、`web_search.py`、新增`web_network.py`复用httpx | [抓取](../ruocun-next24h/evidence/review/b06-webfetch-review.md) · [搜索](../ruocun-next24h/evidence/review/b06-websearch-review.md)。真实受控HTTP/TLS、抽取与回退、no-web无注册；保留源初始地址检查范围，不声称DNS/逐跳防护 |
| 25，MM-624/483 | `tools/config.py`、新增`config/settings_store.py`、`tools/schema.py` anyOf及普通入口 | [配置](../ruocun-next24h/evidence/review/b06-config-review.md)。项目??用户、私有用户写回、损坏/前置拒绝保原字节；不新增热重载，发布未知仍阻断 |

| 新适配ID | 文件 | 对应职责 |
| --- | --- | --- |
| NEW-B06-01 | `config/settings_store.py` | MM-624的原生私有设置读改写，复用既有路径锁与耐久发布 |
| NEW-B06-02 | `tools/web_network.py` | MM-651/740共用异步HTTP拥有者、整请求期限与取消，复用已锁httpx |
| NEW-B06-03 | `lsp/windows_job.py` | MM-485/D09 Windows双向协议进程绑定，复用既有Job结构，先绑定再恢复、关闭等待实际整树 |

## 批次05实际对应

保留冻结DAO文件对应及原来源记录；下列适配模块服务于同一职责。[批次记录](../ruocun-next24h/batch-06.md)

| 来源/范围 | 实际位置 | 证据与边界 |
| --- | --- | --- |
| 26，MM-392/595/600 | `session/log.py`、`session/prune.py`、`agent/cleanup.py`、`session/conversation.py`、`durable_store.py`、`agent/runtime.py` | [会话独审](../ruocun-next24h/evidence/review/b05-sessions-review.md) · [暂停补验](../ruocun-next24h/evidence/review/b05-caps-paused-review.md)。分支只复制聊天；附件所有者保留，清理失败留下现场 |
| 46，MM-424/676 | `tools/monitor.py`、`agent/monitor.py`、`agent/tasks.py`及执行权限/存储接线 | [Monitor独审](../ruocun-next24h/evidence/review/b05-monitor-review.md)。真实进程停止；owner丢失只保留历史、标记interrupted，不自动重启 |
| 51–53，MM-491/496/733 | `mcp/mcp.py`、`config/mcp_store.py`、`tools/registry.py`、`agent/runtime.py`及协议fixtures | [stdio独审](../ruocun-next24h/evidence/review/b05-mcp-cli-review.md) · [HTTP独审](../ruocun-next24h/evidence/review/b05-http-review.md) · [能力与命令独审](../ruocun-next24h/evidence/review/b05-caps-paused-review.md)。SDK1.30.0、私有原生配置写回；同名add沿来源不强制重连 |
| 54，MM-496/598；既有MM-366/420子MCP消费者 | `mcp/mcp.py`、`agent/agent_mcp.py`、`run_agent.py`、`resume_agent.py`、`tasks.py`、`runtime.py` | [断线独审](../ruocun-next24h/evidence/review/b05-mcp-recovery-review.md) · [子MCP独审](../ruocun-next24h/evidence/review/b05-agent-mcp-review.md)。实际连接摘要绑定恢复，断线保留unknown，未明确决定不重放；不承诺远端exactly-once |

## 批次03实际对应

| 来源/范围 | 实际位置 | 证据与边界 |
| --- | --- | --- |
| 28，MM-426/586/590/600 | `agent/loop.py`、`agent/context_runtime.py`、`session/session.py`、`session/cache_audit.py` | 普通查询、每请求归因、权限模式及费用/预算重开口径独审通过。[费用证据](../ruocun-next24h/evidence/n28-cost/README.md) |
| 29，MM-394/404/422 | `agent/context_runtime.py`、`agent/loop.py`、`agent/session_scheduler.py`、`agent/runtime.py`、`session/conversation.py` | 有界原模型重试、显式账户切换。压缩失败保留工具对、等待与事件，重开仍暂停。[独立复核](../ruocun-next24h/evidence/review/b03-model-recovery-review.md) |
| 45，MM-424/713/715/717/725 | `agent/tasks.py`、`tools/task_create.py`、`tools/task_get.py`、`tools/task_list.py`、`tools/task_update.py`、`agent/runtime.py` | 手工记录、查询、更新、停止及重开独审通过。[手工任务证据](../ruocun-next24h/evidence/batch-03/n45/README.md) |
| 47，MM-422/747 | `agent/session_scheduler.py`、`agent/runtime.py` | 普通会话定时、排队去重与关闭清理。旧定时器在错误后停止。[独立复核](../ruocun-next24h/evidence/review/b03-loop-review.md) |
| 67，MM-745/747/762 | `tui/app/agent_tasks_panel.py`、`tui/app/app.py`、`tui/foreground_registry.py`、`agent/input_broker.py`、`agent/tasks.py`、`agent/run_agent.py`、`tools/managed_shell.py`、`agent/runtime.py` | 面板、剪贴板和交接实机通过，隔离分支经独审。[67证据](../ruocun-next24h/evidence/batch-03/n67/README.md) · [实机复验](../ruocun-next24h/evidence/n18/wt/runs/20261111T101837Z-52f7cc/README.md) |

## 批次02实际对应

以下为本批实际位置，路径相对于src/ruocun。原逐文件索引仍定位冻结来源。逐票状态见[批次记录](../ruocun-next24h/batch-02.md)，早期候选另见[b02-r1构建](../ruocun-next24h/evidence/batch-02/integration/README.md)。

| 来源/范围 | 实际位置 | 证据与边界 |
| --- | --- | --- |
| MM-381/383/385、16 | agent/background_delivery.py、background_runtime.py、background_types.py、tools/task_wait.py | [16](../ruocun-next24h/evidence/n16-background/README.md)；固定run等待、事件事务与投递已独审，16 resolved |
| MM-598/602/668、17 | session/recovery.py、conversation.py、durable_store.py、storage_worker.py、agent/resume_agent.py | [17](../ruocun-next24h/evidence/n17-recovery/README.md)；查询、人工决定及普通代理显式继续，原转录与工具回执留存 |
| 65转录/语言/主题/宽度 | tui/app/app.py、types.py、markdown.py、theme.py、width.py、i18n/及agent/input_broker.py | [65](../ruocun-next24h/evidence/batch-02/n65/README.md)；实机缩放、草稿及深浅输入通过 |
| MM-763、64 | tui/image_paste.py、platform/windows/clipboard.py及helper、runtime多模态接线 | [64](../ruocun-next24h/evidence/batch-02/n64/README.md)；真实剪贴板到图像请求的PNG哈希一致 |
| MM-747/776/453/472、66 | tui/app/modals.py、onboarding/select.py、config/auth_wizard.py、validate_key.py与runtime动作 | [66](../ruocun-next24h/evidence/batch-02/n66/README.md)、[独审](../ruocun-next24h/evidence/review/b02-modals-notify-review.md)；用户在真实终端完成多选与账户Esc；删除当前账户沿ADR-0016 |
| MM-680/772/790、63 | tools/notify_user.py、tui/notifier.py、tab_attention.py及同owner队列 | [63](../ruocun-next24h/evidence/batch-02/n63/README.md)；终端渠道，批次03实机标题与焦点通过 |
| MM-767/768/770/792、68 | tui/welcome.py、banner.py、mascot.py、mascot_frames.py、maxim.py、taiji.py及data/laozi_maxims.py | [68实机](../ruocun-next24h/evidence/n18/wt/runs/20261111T092536Z-1592d0/README.md)；同reader探测、首帧原图与备用显示已验证 |
| MM-774/777/779/780/781/783、69 | tui/onboarding/onboarding.py、steps/及config/auth_wizard.py、agent/runtime.py | [独审](../ruocun-next24h/evidence/review/b02-onboarding-review.md)；首次账户、语言、信任在同一输入owner进入普通会话 |
| MM-366/374/388、39 | agent/agent_defs.py、agent_memory.py、bundled_agents.py及run_agent.py | [39](../ruocun-next24h/evidence/n39-agent-defs/README.md)；有效定义控制真实派发，权限和记忆目录独立复核 |
| MM-372/417/420/424/719/723、38/40 | agent/agent_lifecycle.py、resume_agent.py、run_agent.py、tasks.py及tools/task_output.py、task_stop.py | [40](../ruocun-next24h/evidence/n40-agent-background/README.md)；真实运行、取消、工具结果和继续使用持久运行身份 |
| MM-380/401/432、27/41 | agent/fork_agent.py、worktree.py、run_agent.py、tools/registry.py及session/checkpoint.py | [41独审](../ruocun-next24h/evidence/review/b02-fork-isolation-review.md)；精确父工具、影子检查点、同机Git工作树；失败拒绝按ADR-0017 |

来源断言实际按语义集中在tests/test_b02_*.py、tests/test_n17_recovery.py及对应既有后台测试，validate_key在tests/src/config/test_validate_key.py。每个来源文件的哈希和覆盖范围见对应证据，不据此把原测试全文件标为通过。

## 首版历史与阶段A覆盖

首版范围按[ADR-0011](../../docs/adr/0011-python-coding-mvp.md)，阶段A新增按ADR-0012及本节A证据。下表及各MM行中的“首版子集”仅表示七工具、前台文字审批、正常会话保存/重开；原805来源成员和82张完整迁移票保留，后置能力不计为完成。状态读取相应阶段实施进度，不直接消费旧任务图。

| 新增接线ID | 实际位置 | 职责与证据 |
| --- | --- | --- |
| NEW-MVP-01 | `src/ruocun/agent/runtime.py`、`src/ruocun/session/conversation.py` | 普通CLI组合根、七工具审批、StorageWorker检查点/意图/结果、正常重开；[M03](../ruocun-mvp/evidence/m03/README.md) |
| NEW-MVP-02 | `src/ruocun/platform/process_tree.py`、`src/ruocun/platform/windows/process_tree.py` | PowerShell方言、Job成员实际退出与输出回收；[M02](../ruocun-mvp/evidence/m02-shell/README.md) |
| NEW-MVP-03 | `hatch_build.py`、`src/ruocun/resources/runtime/` | Windows x64 wheel标签与原始SQLite固定归档；[产物绑定](../ruocun-mvp/evidence/m03/artifacts.json) |
| NEW-A-01 | `src/ruocun/skills/runtime.py`、`src/ruocun/agent/context_runtime.py`、`src/ruocun/agent/resources/compact.zh.txt` | 从冻结index拆出静态Skills启动装配、用量/窗口/摘要控制器；复用唯一Conversation/Session；[阶段A集成](../ruocun-advanced-a/evidence/integration/README.md)，最终r2自动出口已通过 |

阶段A沿ADR-0012接入项目指令、静态Skills和上下文管理；下列MM实际子路径与[A证据](../ruocun-advanced-a/evidence/integration/README.md)关联。普通入口与模块独审已通过，最终r2全量669项/固定产物/独审通过；不改变原票完整完成数。后续执行顺序见[20小时计划](../ruocun-next20h/plan.md)。

N0已补齐08：Read图片/完整中英metadata、Todo原提示、headless首批、真实SSE空截断通知和续写清洗；图片packet与批末user投递复用唯一StorageWorker，新增`session/messages.py`仅负责投影。固定70c7464/r2，90成员/687项/独审通过，见[N0集成](../ruocun-next20h/evidence/n0-integration/README.md)；权限、完整批调度与34控制仍待后续。

## N1及19模块接缝（普通入口在途）

09规则/审批/完整纯Python解析、前台scheduler、最小TTY broker、Skills控制及19搜索已通过[固定r1](../ruocun-next20h/evidence/n1-integration/README.md)的原CLI/受控TTY、全量与仓库外独审，09/11/19/34已resolved。下方逐模块早期“普通入口待验”指当时检查点；本批实际通过范围读取验收矩阵的N1/19子表。后台、动态Skills、安装与未验母族不据此标通过。测试位置按实际来源断言维护。

| 接线ID | 实际位置 | 职责与边界 |
| --- | --- | --- |
| NEW-N1-01 | `permissions/runtime.py`、`agent/input_broker.py`、`session/inputs.py` | 从index拆出的层级/模式装配、单输入owner、排队原文/正文快照；复用唯一Session/StorageWorker；[独审](../ruocun-next20h/evidence/review/n1-runtime-projection-review.md) |
| NEW-N1-02 | `skills/control.py`、`agent/files.py` | 原生禁用集/文字选择控制、当前已读文件纯查询；不冒充动态刷新或历史读图重建；[模块独审](../ruocun-next20h/evidence/review/n1-plan-n2-search-review.md) |

## 使用与来源

- 行为契约见 [完整规格](spec.md)，产品状态见 [验收矩阵](acceptance-matrix.md)。
- 完整迁移历史范围见ADR-0006/0010及[批次](sprint-48h.md)；当前首版由ADR-0011及顶部覆盖表限定，评估工程、CI与完整文档等整块后置。805来源成员与MM ID保持，职责/验收差异在对应行记录，不把范围移出写成产品通过。旧完整范围中R1/R3/W3/W5/W6/D2/D3/V1/V2的决定仍保留。
- 唯一来源：[冻结快照说明](../ruocun-discovery/reference/README.md)。基准 SHA `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`，v0.5.15，含全部 12 个本地修改和 8 个未跟踪文件；805 个文件的逐文件 SHA/模式/状态以归档 manifest 为准。
- 源码树 SHA-256 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`。所有“原路径”均指 ZIP 成员，不指活动 DAO 目录，也不要求缓存目录存在。
- 先用既有 reference_tool 校验/解包；运行 oracle 时另建受控可写副本、独立 Git fixture、合成配置与会话根，避免继承上层仓库或真实用户 HOME。
- MM ID 稳定保留。拆合时保留原行并补实际目标、理由/ADR、任务、关联案例、实现状态及证据；不得只删原行以消除遗漏。新文件用 NEW ID。下表只提供初始对应，未来不能反向生成覆盖手工维护状态。
- S=Python 语义改写，D=数据直接复用，R=协议/回放适配，P=真实模型或外部评估协议。转换前保留来源版权；测试样例中 TS/JSON/外部命令作为数据不违反核心 Python 要求。
- 主包采用既有拟定的 `src/ruocun` 布局；TS camelCase/大写组件转换为 snake_case 是允许差异，职责及外部工具名/字段/事件名保持原协议大小写。目录调整须维护下表。

## 主要调用关系索引

| 链 | 主要关系与所有权 |
| --- | --- |
| C0 | CLI 组合根 → 配置/信任/扩展/提示组装 → Session/权限/运行时/持久化 → scheduler → TUI、REPL 或一次性入口 |
| C1 | 单输入 owner → 提交/命令 → 查询或 pause/settled → scheduler；普通输入只在安全边界合并 |
| C2 | scheduler → runTurn → 模型流 → assistant 意图保存 → dispatcher → 工具结果保存 → 后续模型请求 |
| C3 | TaskManager/ProcessManager → BackgroundRuntime → run+event 事务 → inbox → 消息+delivered 同事务 → acknowledge → scheduler |
| C4 | registry/动态激活 → 参数解析 → prehook 最终参数 → 身份/权限/审批 → handler → journal；外部扩展走相同边界 |
| C5 | 输入解码/终端回包分离 → 业务事件；唯一渲染 owner → transcript/输入/模态/图形；退出恢复终端 |
| C6 | 文件/记忆/代码图/环境结果 → 验证与预算 → 固定前缀或安全边界尾部注入；不插断工具对 |
| C7 | 标准Python包安装与内部角色入口 → 同版本runner；Windows系统定时按W3不支持，来源其它平台路径保留；平台实现不穿透业务模块 |

## 目录职责


| 原目录 | 拟目标 | 职责 | 主要关系 | 案例族 |
| --- | --- | --- | --- | --- |
| src/agent/ | src/ruocun/agent/ | 运行、调度、后台与子代理 | 入口 → scheduler → loop → client/dispatcher；后台事件经事务进入边界 | RUN / BG / REC |
| src/approval/ | src/ruocun/approval/ | 人工审批端口 | PermissionGate → TUI 或 stdin prompt → 决定存储 | PERM |
| src/client/ | src/ruocun/client/ | 模型协议与流 | loop → 统一模型事件 → Chat/Responses transport | WIRE |
| src/commands/ | src/ruocun/commands/ | 命令解析与模板 | TUI/REPL → 查询或 pause/settled → handler/prompt | CMD |
| src/config/ | src/ruocun/config/ | 账户、凭据、信任、模型配置 | 入口 → 分资源 loader → provider/platform adapter | CFG |
| src/data/ | src/ruocun/data/ | 静态文化与界面资源 | TUI 内容层读取；无任务状态所有权 | UI |
| src/hooks/ | src/ruocun/hooks/ | Hook 发现、匹配与运行 | 入口/dispatcher/agent lifecycle → 命令协议 → 有限输出语义 | EXT |
| src/i18n/ | src/ruocun/i18n/ | 中英文与语言状态 | 配置 → 文案及工具描述；保持键和占位符 | UI |
| src/lsp/ | src/ruocun/lsp/ | 语言服务器协议 | LSP tool → manager → 按扩展名惰性 stdio JSON-RPC | EXT |
| src/mcp/ | src/ruocun/mcp/ | MCP 扩展与生命周期 | 入口 → manager → registry；工具经统一裁决和协议调用 | EXT |
| src/memory/ | src/ruocun/memory/ | 长期记忆与上下文注入 | 启动加载/验证 → 固定注入；反思蒸馏 → Markdown store | MEM |
| src/obs/ | src/ruocun/obs/ | 观测与审计包装 | turn/stream/tool → 可选后端；关闭后业务路径等效 | OBS |
| src/permissions/ | src/ruocun/permissions/ | 分层规则、安全与权限门 | 身份/最终参数 → deny/ask/allow → 审批 → 执行 | PERM |
| src/prompt/ | src/ruocun/prompt/ | 系统提示模板 | 组合根汇集稳定前缀/模型/技能/记忆 → 模型请求 | PROMPT |
| src/repomap/ | src/ruocun/repomap/ | 代码图与预算裁剪 | 文件扫描 → parser → 排名/裁剪 → 工具或安全边界注入 | MAP |
| src/session/ | src/ruocun/session/ | 会话与持久化 | 消息/工具/运行事件 → 单写事务 → owner/recovery；工作区检查点独立 | REC |
| src/skills/ | src/ruocun/skills/ | 技能加载、发现、安装、适配 | loader/文件访问 → 元信息目录 → Skill 按需正文；调用审计 | EXT |
| src/tools/ | src/ruocun/tools/ | 工具定义、注册和执行支撑 | loop → registry → prehook/gate → handler → journal/结果 | TOOL |
| src/tui/ | src/ruocun/tui/ | 终端状态、输入与输出适配 | 单输入 owner → 业务事件 → scheduler；渲染 owner → 终端 | UI |


## 语言绑定与平台替换边界

| 来源依赖/机制 | 允许替换及必须保持 | 决策依赖 |
| --- | --- | --- |
| Node/Bun、TS/React/Ink | 全部核心用 Python；异步任务/模块关系保留；inline scrollback、输入和模态行为按真实终端验收 | 地图 06/08/10 |
| Zod/schema 转换 | Python 校验器可替换；保留发给模型的 schema、默认/缺省/枚举/错误语义及 registry 可见性 | 地图 15/11 |
| TS MCP SDK、vscode-jsonrpc | 锁定的 Python SDK/适配层；仅承诺参考实际接线协议及已确认 Windows 补齐 | 地图 15/09 |
| better-sqlite3/bun:sqlite | 含 WAL 修复的 SQLite 运行库和窄驱动；事务/owner/journal 保留；不承诺旧 DAO DB 导入 | 地图 18/19/08/09 |
| web-tree-sitter/WASM | Python parser/native binding 或等效适配；多语言符号、排名/预算/缓存按 oracle 校验 | 地图 13 |
| POSIX 信号、Unix socket、目录 fsync/chmod | Windows 进程树/认证 IPC/持久文件与 ACL 适配；不能以 Job 对象代替 OS 文件/网络沙箱 | 地图 17/18 |
| keychain/security/secret-tool、crontab、唤醒锁、剪贴板 | 保留Windows原生凭据与图片/文本clipboard；W3/W5移出Task Scheduler/Windows防休眠补齐，准确呈现不支持；来源其它平台对应保留未验 | 地图16/17/12；ADR-0010 |
| Bun 单文件交叉编译、npm 安装 | D2只交Python wheel/sdist；资源/SQLite/runner真实可用，D3手工停进程/一致备份/更新，不承诺自动迁移回退；独立产物保留来源记录但本轮移出 | 地图07/12；ADR-0010 |
| Ink 本地补丁、内嵌 Sixel | 补丁行为转 Python 渲染测试；内嵌帧/时序可转数据并保留 hash 来源；原图未收齐不得声称可重生成 | 地图 06/10/12 |


## 43 个工具的逐项对应

默认 42 个；LSP 按配置注册为第 43 个。no-web/eval 去掉两项 Web 工具；延迟集合 16 个（不含 LSP 时 15 个）；具体 API schema 按冻结定义/转换结果建立 golden，不从描述重新发明。MCP 动态工具另见 EXT 案例。

| 案例 | 外部名 | 能力/审批 | 可见性 | 源码 → Python | 责任 |
| --- | --- | --- | --- | --- | --- |
| TOOL-Read | Read | read / auto | 常驻 | `src/tools/read_file.ts` → `src/ruocun/tools/read_file.py`；MM-691 | 文本带行号、offset/limit、图片；二进制/大文件护栏，记录编辑前读取元信息 |
| TOOL-ListDir | ListDir | read / auto | 常驻 | `src/tools/list_dir.ts` → `src/ruocun/tools/list_dir.py`；MM-664 | 路径目录列表 |
| TOOL-Glob | Glob | read / auto | 常驻 | `src/tools/file_search.ts` → `src/ruocun/tools/file_search.py`；MM-655 | 文件/路径 glob，修改时间排序；实际导出变量名 fileSearchTool |
| TOOL-Grep | Grep | read / auto | 常驻 | `src/tools/grep_files.ts` → `src/ruocun/tools/grep_files.py`；MM-661 | 正则、内容/文件模式、上下文、分页、跨行、类型等 |
| TOOL-Write | Write | write / required | 常驻 | `src/tools/write_file.ts` → `src/ruocun/tools/write_file.py`；MM-742 | 全文创建/覆盖，读前检查、mtime/size 漂移、锁与原子替换 |
| TOOL-Edit | Edit | write / required | 常驻 | `src/tools/edit_file.ts` → `src/ruocun/tools/edit_file.py`；MM-631 | old/new string，唯一匹配或 replace_all，锁与 diff |
| TOOL-NotebookEdit | NotebookEdit | write / required | 来源延迟注册 | `src/tools/notebook_edit.ts` → `src/ruocun/tools/notebook_edit.py`（历史目标），MM-678 | ipynb 单元格编辑。本轮移出注册表 |
| TOOL-Bash | Bash | exec / required | 常驻 | `src/tools/exec_shell.ts` → `src/ruocun/tools/exec_shell.py`；MM-637 | 前台命令、显式后台、沙箱开关、进程转后台；前台当前无超时参数 |
| TOOL-BashOutput | BashOutput | read / auto | 常驻 | `src/tools/exec_shell_poll.ts` → `src/ruocun/tools/exec_shell_poll.py`；MM-640 | 按后台 Shell id 增量读日志并节流；不是阻塞等待 |
| TOOL-KillShell | KillShell | exec / auto | 常驻 | `src/tools/exec_shell_kill.ts` → `src/ruocun/tools/exec_shell_kill.py`；MM-639 | 请求终止已启动 Shell，取消请求不等于退出确认 |
| TOOL-WebFetch | WebFetch | network / suggest | 常驻 | `src/tools/fetch_url.ts` → `src/ruocun/tools/fetch_url.py`；MM-651 | URL 抓取、纯文本/按 prompt 抽取、缓存与 SSRF 检查；no-web 时不注册 |
| TOOL-WebSearch | WebSearch | network / suggest | 常驻 | `src/tools/web_search.ts` → `src/ruocun/tools/web_search.py`；MM-740 | DuckDuckGo HTML 搜索，结果上限；no-web 时不注册 |
| TOOL-AskUserQuestion | AskUserQuestion | read / auto | 常驻 | `src/tools/ask_user.ts` → `src/ruocun/tools/ask_user.py`；MM-623 | 询问、选项/多选，由上下文提供 UI |
| TOOL-TodoWrite | TodoWrite | plan / auto | 常驻 | `src/tools/todo_write.ts` → `src/ruocun/tools/todo_write.py`；MM-729 | 整表替换的扁平清单，无独立 task id |
| TOOL-MemoryRead | MemoryRead | read / auto | 常驻 | `src/tools/memory_read.ts` → `src/ruocun/tools/memory_read.py`；MM-670 | 取记忆正文 |
| TOOL-MemoryWrite | MemoryWrite | plan / auto | 常驻 | `src/tools/memory_write.ts` → `src/ruocun/tools/memory_write.py`；MM-672 | 五种类型、三作用域、重要度/来源，或明确删除 |
| TOOL-Skill | Skill | read / auto | 常驻 | `src/tools/skill.ts` → `src/ruocun/tools/skill.py`；MM-705 | 按名加载技能正文 |
| TOOL-SkillInstall | SkillInstall | exec / required | 延迟 | `src/tools/skill_install.ts` → `src/ruocun/tools/skill_install.py`；MM-707 | Git/本地技能安装 |
| TOOL-Agent | Agent | plan / auto | 常驻 | `src/tools/agent.ts` → `src/ruocun/tools/agent.py`；MM-621 | 单/多任务、同步/后台、fork/worktree/model/plan；继续代理由 TaskSend/recovery 路径处理 |
| TOOL-TaskSend | TaskSend | plan / auto | 常驻 | `src/tools/task_send.ts` → `src/ruocun/tools/task_send.py`；MM-721 | 向代理追加指令，已结束任务的恢复转交 ctx.resumeAgent |
| TOOL-MessageParent | MessageParent | plan / auto | 延迟 | `src/tools/message_parent.ts` → `src/ruocun/tools/message_parent.py`；MM-674 | 子代理发送进展或 attention 给父 |
| TOOL-TaskWait | TaskWait | read / auto | 常驻 | `src/tools/task_wait.ts` → `src/ruocun/tools/task_wait.py`；MM-726 | 对当前会话后台代理或 Shell 的 any/all 事件等待；单独调用，不等待手工/前台任务 |
| TOOL-TaskCreate | TaskCreate | plan / auto | 常驻 | `src/tools/task_create.ts` → `src/ruocun/tools/task_create.py`；MM-713 | 只建手工任务记录，不启动进程 |
| TOOL-TaskList | TaskList | read / auto | 常驻 | `src/tools/task_list.ts` → `src/ruocun/tools/task_list.py`；MM-717 | taskManager 当前/含已结束清单；不是 Shell 统一清单 |
| TOOL-TaskGet | TaskGet | read / auto | 常驻 | `src/tools/task_get.ts` → `src/ruocun/tools/task_get.py`；MM-715 | taskManager 单任务详情 |
| TOOL-TaskOutput | TaskOutput | read / auto | 常驻 | `src/tools/task_output.ts` → `src/ruocun/tools/task_output.py`；MM-719 | 代理转录增量，WeakMap 游标；手工任务无转录 |
| TOOL-TaskUpdate | TaskUpdate | plan / auto | 常驻 | `src/tools/task_update.ts` → `src/ruocun/tools/task_update.py`；MM-725 | 手工任务描述/状态/结果 |
| TOOL-TaskStop | TaskStop | exec / auto | 常驻 | `src/tools/task_stop.ts` → `src/ruocun/tools/task_stop.py`；MM-723 | 代理 abort→canceling→执行器确认 canceled，手工任务直接取消 |
| TOOL-NotifyUser | NotifyUser | plan / auto | 延迟 | `src/tools/notify_user.ts` → `src/ruocun/tools/notify_user.py`；MM-680 | W6只提供终端内提示，准确说明未发桌面通知；schema/描述的能力差异单列 |
| TOOL-SendUserMessage | SendUserMessage | plan / auto | 常驻 | `src/tools/send_message.ts` → `src/ruocun/tools/send_message.py`；MM-703 | 用户可见消息、附件路径、normal/proactive 状态 |
| TOOL-EnterPlanMode | EnterPlanMode | plan / auto | 延迟 | `src/tools/plan_mode.ts` → `src/ruocun/tools/plan_mode.py`；MM-687 | 切换只读规划 |
| TOOL-ExitPlanMode | ExitPlanMode | plan / auto | 延迟 | `src/tools/plan_mode.ts` → `src/ruocun/tools/plan_mode.py`；MM-687 | 提交方案并退出规划，由上下文处理批准 |
| TOOL-EnterWorktree | EnterWorktree | write / suggest | 延迟 | `src/tools/enter_worktree.ts` → `src/ruocun/tools/enter_worktree.py`；MM-635 | 当前代理进入隔离树，记录 previousCwd；不允许叠加进入 |
| TOOL-ExitWorktree | ExitWorktree | write / suggest | 延迟 | `src/tools/exit_worktree.ts` → `src/ruocun/tools/exit_worktree.py`；MM-645 | keep/remove，丢弃有改动或新增提交需 discard_changes；恢复 cwd |
| TOOL-Monitor | Monitor | exec / required | 延迟 | `src/tools/monitor.ts` → `src/ruocun/tools/monitor.py`；MM-676 | 后台监控命令，stdout 按行批量通知，persistent/超时与 TaskStop |
| TOOL-Config | Config | plan / auto | 延迟 | `src/tools/config.ts` → `src/ruocun/tools/config.py`；MM-624 | 配置读取或写用户 settings，含权限模式/主题/检查点及通用点路径 |
| TOOL-Schedule | Schedule | exec / required | 延迟 | `src/tools/schedule_tool.ts` → `src/ruocun/tools/schedule_tool.py`；MM-700 | W3：Windows明确不支持系统级定时；来源其它平台add/list/remove语义保留未验 |
| TOOL-CronCreate | CronCreate | exec / required | 延迟 | `src/tools/cron_tools.ts` → `src/ruocun/tools/cron_tools.py`；MM-625 | W3：Windows创建明确不支持；其它平台来源持久创建语义保留未验 |
| TOOL-CronDelete | CronDelete | exec / required | 延迟 | `src/tools/cron_tools.ts` → `src/ruocun/tools/cron_tools.py`；MM-625 | W3：Windows删除明确不支持；来源其它平台清单序号删除语义保留未验 |
| TOOL-CronList | CronList | read / auto | 延迟 | `src/tools/cron_tools.ts` → `src/ruocun/tools/cron_tools.py`；MM-625 | W3：Windows查询准确不支持，不以空表冒充成功；其它平台清单语义保留未验 |
| TOOL-ToolSearch | ToolSearch | read / auto | 常驻 | `src/tools/tool_search.ts` → `src/ruocun/tools/tool_search.py`；MM-733 | 搜索激活 MCP 和延迟内置工具；无 MCP 也注册 |
| TOOL-RepoMap | RepoMap | read / auto | 延迟 | `src/tools/repo_map.ts` → `src/ruocun/tools/repo_map.py`；MM-695 | 获取/刷新代码地图 |
| TOOL-LSP | LSP | read / auto | 延迟、条件注册 | `src/tools/lsp.ts` → `src/ruocun/tools/lsp.py`；MM-666 | 9操作：goToDefinition/findReferences/hover/documentSymbol/workspaceSymbol/goToImplementation/prepareCallHierarchy/incomingCalls/outgoingCalls |

## 52 个固定 slash 名字的逐项对应

入口能力按参考保留：基础9表示 model/plan/clear/compact/cost/lang/help/exit/quit；REPL 加 recovery/resume 共11。argv prompt 不具完整 slash 路由。别名也是独立验收入口。动态命令和 core skills 不混入固定52。

| 案例 | 名字 | 来源入口 | 行为 | 源码 → Python |
| --- | --- | --- | --- | --- |
| CMD-model | /model | 基础9+TTY | 模型查询/切换、provider/账户约束及持久化 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-plan | /plan | 基础9+TTY | 进入/退出只读规划；实际可用工具裁剪 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-clear | /clear | 基础9+TTY | 清空当前上下文，保留明确的会话生命周期处理 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-compact | /compact | 基础9+TTY | 主动压缩、工具消息配对及可恢复检查点 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-cost | /cost | 基础9+TTY | 用量、缓存与费用统计 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-lang | /lang | 基础9+TTY | 中英文查询/切换与存储 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-help | /help | 基础9+TTY | 对应入口实际可用命令及帮助 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-exit | /exit | 基础9+TTY | 正常收尾、保存、释放终端与执行资源 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-quit | /quit | 基础9+TTY | 退出别名；显式 keep-background 时仅保留受支持后台执行 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-skills | /skills | TTY | 列表/选择器、单项禁用及 bundled 批量控制 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-context | /context | TTY | 上下文组成/预算显示 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-context-window | /context-window | TTY | 查询、K/M 解析/设置、手动锁定窗口 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-tasks | /tasks | TTY | TaskManager 当前运行项；不假装包含全部 Shell | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-mcp | /mcp | TTY | 列表、重连、开关与 add | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-diff | /diff | TTY | 工作区 Git 未提交差异 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-doctor | /doctor | TTY | 账户/依赖/环境自检与平台诊断 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-memory | /memory | 普通文字入口 | 查看、审核、删除记忆 | `src/index.ts` → `src/ruocun/agent/runtime.py` / `src/ruocun/memory/command.py`；审核MM-498 |
| CMD-permissions | /permissions | TTY | 规则/模式显示；编辑分支遮蔽另列 SOURCE-CANDIDATE | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-session | /session | TTY | 当前会话身份、保存与状态 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-audit | /audit | TTY | 记忆/反思/工具/权限/缓存/技能审计查询 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-resume | /resume | TTY+REPL特接 | 列表/显式会话切换、活 owner 与运行代理保护 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-branch | /branch | TTY | 复制聊天分支；不重复启动原后台副作用 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-rename | /rename | TTY | 会话标题保存及重启一致性 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-rewind | /rewind | TTY | 按用户消息截断；显式 code 时关联工作区检查点 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-export | /export | TTY | 会话 Markdown 导出与路径显示 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-Config | /Config | TTY | 保留大写入口的配置显示 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-effort | /effort | TTY | 思考强度查询/设置并应用后续请求 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-status | /status | TTY | 运行状态/模式/预算显示 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-plugin | /plugin | 来源TTY | 已安装插件清单。本轮范围移出 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-hooks | /hooks | TTY | 实际载入 Hook 清单 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-agents | /agents | TTY | 内置/自定义代理定义清单 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-files | /files | TTY | 已读文件与上下文信息 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-copy | /copy | TTY | 复制末条回答，Unicode 和空回答处理 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-btw | /btw | TTY | 备注注入而不立即请求模型 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-account | /account | TTY | 账户列表/选择/新增/删除/切换 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-accounts | /accounts | TTY | 账户别名入口 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-bypass | /bypass | TTY | 显式放行模式与状态一致性 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-yolo | /yolo | TTY | 放行别名与可见模式 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-mode | /mode | TTY | 模式查询/切换；plan 不混入 auto/bypass 循环 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-goal | /goal | TTY | 长任务开启/关闭、目标提示与边界 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-task | /task | TTY | 长任务别名入口 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-coordinator | /coordinator | TTY | 合并后的长任务别名入口 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-restore | /restore | TTY | 工作区恢复前先建自动快照 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-recovery | /recovery | TTY+REPL特接 | 未决查询/resolve/decide/continue，决定持久化 | `src/index.ts` → `src/ruocun/__main__.py` (MM-483)；`src/commands/commands.ts` → `src/ruocun/commands/commands.py` (MM-448) |
| CMD-simplify | /simplify | TTY builtin | 内置简化 prompt 展开 | `src/commands/builtin.ts` → `src/ruocun/commands/builtin.py` (MM-446)；`src/index.ts` → `src/ruocun/__main__.py` (MM-483) |
| CMD-remember | /remember | TTY builtin | 内置记忆 prompt 展开 | `src/commands/builtin.ts` → `src/ruocun/commands/builtin.py` (MM-446)；`src/index.ts` → `src/ruocun/__main__.py` (MM-483) |
| CMD-review | /review | TTY builtin | 内置审查 prompt 展开 | `src/commands/builtin.ts` → `src/ruocun/commands/builtin.py` (MM-446)；`src/index.ts` → `src/ruocun/__main__.py` (MM-483) |
| CMD-init | /init | TTY builtin | 内置项目初始化 prompt 展开 | `src/commands/builtin.ts` → `src/ruocun/commands/builtin.py` (MM-446)；`src/index.ts` → `src/ruocun/__main__.py` (MM-483) |
| CMD-batch | /batch | TTY builtin | 内置并行任务/worktree prompt 展开 | `src/commands/builtin.ts` → `src/ruocun/commands/builtin.py` (MM-446)；`src/index.ts` → `src/ruocun/__main__.py` (MM-483) |
| CMD-skillify | /skillify | TTY builtin | 内置技能提取 prompt 展开 | `src/commands/builtin.ts` → `src/ruocun/commands/builtin.py` (MM-446)；`src/index.ts` → `src/ruocun/__main__.py` (MM-483) |
| CMD-theme | /theme | App | 会话主题切换，不改变调度器状态 | `src/tui/app/App.tsx` → `src/ruocun/tui/app/app.py` (MM-747) |
| CMD-loop | /loop | App | 整数 s/m/h 周期排队、off 取消与退出清理 | `src/tui/app/App.tsx` → `src/ruocun/tui/app/app.py` (MM-747) |


## 提示、模型及外部格式的定位

下列原路径用于精确建立文本/请求/格式 oracle；规格正文不重复文件清单。系统提示、子代理/反思/压缩/内置命令/技能模板、工具描述、权限分类器和提示注入边界均在保持范围内。


| 契约 | 冻结来源 → 拟目标 |
| --- | --- |
| 系统/长任务及运行时提示 | `src/prompt/system_prompt.ts` → `src/ruocun/prompt/system_prompt.py` (MM-566)；`src/agent/loop.ts` → `src/ruocun/agent/loop.py` (MM-404)；`src/index.ts` → `src/ruocun/__main__.py` (MM-483) |
| 子代理/内置代理/反思/压缩 | `src/agent/agent_prompt.ts` → `src/ruocun/agent/agent_prompt.py` (MM-376)；`src/agent/bundled_agents.ts` → `src/ruocun/agent/bundled_agents.py` (MM-388)；`src/agent/reflect_prompts.ts` → `src/ruocun/agent/reflect_prompts.py` (MM-413)；`src/agent/compact.ts` → `src/ruocun/agent/compact.py` (MM-394) |
| 内置命令/技能与自适配 | `src/commands/builtin.ts` → `src/ruocun/commands/builtin.py` (MM-446)；`src/skills/bundled.ts` → `src/ruocun/skills/bundled.py` (MM-606)；`src/skills/adapt.ts` → `src/ruocun/skills/adapt.py` (MM-604)；`src/skills/convert.ts` → `src/ruocun/skills/convert.py` (MM-608) |
| schema/可见性/执行 | `src/tools/types.ts` → `src/ruocun/tools/types.py` (MM-736)；`src/tools/registry.ts` → `src/ruocun/tools/registry.py` (MM-693)；`src/tools/tools_for_mode.ts` → `src/ruocun/tools/tools_for_mode.py` (MM-735)；`src/tools/execute.ts` → `src/ruocun/tools/execute.py` (MM-642) |
| 模型路由/参数/usage | `src/config/profiles.ts` → `src/ruocun/config/profiles.py` (MM-464)；`src/config/model_selection.ts` → `src/ruocun/config/model_selection.py` (MM-462)；`src/client/client.ts` → `src/ruocun/client/client.py` (MM-439)；`src/client/responses.ts` → `src/ruocun/client/responses.py` (MM-441)；`src/client/types.ts` → `src/ruocun/client/types.py` (MM-444) |
| 配置/凭据/信任/项目指令 | `src/config/profiles_store.ts` → `src/ruocun/config/profiles_store.py` (MM-466)；`src/config/credential.ts` → `src/ruocun/config/credential.py` (MM-455)；`src/config/env_file.ts` → `src/ruocun/config/env_file.py` (MM-457)；`src/config/trust.ts` → `src/ruocun/config/trust.py` (MM-468)；`src/project_doc.ts` → `src/ruocun/project_doc.py` (MM-564) |
| 扩展发现与协议 | `src/skills/skills.ts` → `src/ruocun/skills/skills.py` (MM-616)；`src/skills/discover.ts` → `src/ruocun/skills/discover.py` (MM-610)；`src/plugins.ts` → `src/ruocun/plugins.py` (MM-562)；`src/agent/agent_defs.ts` → `src/ruocun/agent/agent_defs.py` (MM-366)；`src/commands/custom.ts` → `src/ruocun/commands/custom.py` (MM-450)；`src/hooks/hooks.ts` → `src/ruocun/hooks/hooks.py` (MM-477)；`src/mcp/mcp.ts` → `src/ruocun/mcp/mcp.py` (MM-496)；`src/lsp/config.ts` → `src/ruocun/lsp/config.py` (MM-487)；`src/lsp/client.ts` → `src/ruocun/lsp/client.py` (MM-485) |
| 恢复/持久执行/内部角色 | `src/session/durable_store.ts` → `src/ruocun/session/durable_store.py` (MM-593)；`src/session/log.ts` → `src/ruocun/session/log.py` (MM-595)；`src/session/recovery.ts` → `src/ruocun/session/recovery.py` (MM-598)；`src/session/process_identity.ts` → `src/ruocun/session/process_identity.py` (MM-597)；`src/session/durable_file.ts` → `src/ruocun/session/durable_file.py` (MM-591)；`src/tools/managed_shell.ts` → `src/ruocun/tools/managed_shell.py` (MM-668)；`src/tools/shell_runner.ts` → `src/ruocun/tools/shell_runner.py` (MM-704) |


环境变量词汇定位清单（源码词法全集，含传给扩展的变量和诊断词；实际读取/产生/仅文案须逐处 oracle 分类，不据此承诺每个词都是可用开关）：

`AGENT_DECK_HOME`、`CLAUDE_PLUGIN_ROOT`、`CLAUDE_PROJECT_DIR`、`DAO_ADVISE_GAPS`、`DAO_AUDIT`、`DAO_AUTO_APPROVE`、`DAO_CACHE_AUDIT`、`DAO_CHECKPOINT`、`DAO_CHECKPOINT_MAX_MS`、`DAO_CHECKPOINT_TIMEOUT_MS`、`DAO_CLASSIFIER_MODEL`、`DAO_CLEANUP_DAYS`、`DAO_COMPACT_COOLDOWN_MS`、`DAO_CONSOLIDATE_MODEL`、`DAO_CONTEXT_WINDOW`、`DAO_DEBUG_MEMORY`、`DAO_DEBUG_REFLECT`、`DAO_DEBUG_TUI`、`DAO_DECK`、`DAO_DECK_MANAGED`、`DAO_DIAGNOSTICS`、`DAO_DIAGNOSTICS_CMD`、`DAO_DISTILL_FORK`、`DAO_EMPTY_MAX_RETRIES`、`DAO_EMPTY_RETRY_MAX_TOKENS`、`DAO_EXPLORE_MODEL`、`DAO_FAIL_STREAK`、`DAO_FETCH_EXTRACT_MODEL`、`DAO_HARD_RETRY_DELAY_MS`、`DAO_HOOK_EVENT`、`DAO_LANG`、`DAO_MASCOT_DIAGNOSTICS`、`DAO_MAX_BUDGET`、`DAO_MAX_BUDGET_HARD`、`DAO_MAX_CONTINUE`、`DAO_MAX_OUTPUT_TOKENS`、`DAO_MAX_PARALLEL_AGENTS`、`DAO_MAX_TURNS`、`DAO_MEMORY_AUDIT`、`DAO_NOTIFY_MIN_MS`、`DAO_NO_CHECKPOINT`、`DAO_NO_CLEANUP`、`DAO_NO_MEMORY`、`DAO_NO_NOTIFY`、`DAO_NO_UPDATE_CHECK`、`DAO_NO_WAKELOCK`、`DAO_OBS_CACHE_LOW_FLOOR`、`DAO_OBS_CACHE_LOW_RATE`、`DAO_OWNED_TERMINAL`、`DAO_PERM_AUDIT`、`DAO_PLUGIN_ROOT`、`DAO_PRICE_FLASH_INPUT_HIT`、`DAO_PRICE_FLASH_INPUT_MISS`、`DAO_PRICE_FLASH_OUTPUT`、`DAO_PRICE_INPUT_HIT`、`DAO_PRICE_INPUT_MISS`、`DAO_PRICE_OUTPUT`、`DAO_PROVISIONAL_DAYS`、`DAO_RATE_LIMIT_MAX_RETRIES`、`DAO_RATE_LIMIT_WAIT_MS`、`DAO_REASONING_EFFORT`、`DAO_REFLECT`、`DAO_REFLECT_EVERY`、`DAO_REFLECT_MAX_INTERVAL`、`DAO_REFLECT_SYNC`、`DAO_REFOCUS_EVERY`、`DAO_REPEAT_ERR`、`DAO_REPO_MAP_TOKENS`、`DAO_SANDBOX`、`DAO_SANDBOX_NO_NET`、`DAO_SKILL_AUDIT`、`DAO_STREAM_IDLE_MS`、`DAO_SUBAGENT_MAX_TURNS`、`DAO_SUMMARY_MODEL`、`DAO_THEME`、`DAO_TOOL_AUDIT`、`DAO_TOOL_NAME`、`DAO_TRUST`、`DAO_UPDATE_URL`、`DAO_USE_KEYCHAIN`、`DAO_VERBS`、`LMNR_BASE_URL`、`LMNR_GRPC_PORT`、`LMNR_HTTP_PORT`、`LMNR_PROJECT_API_KEY`。


## 已确认测试资产与入口定位

全部 215 个 `.test.` 文件、58 个 scripts 文件及评估/fixture 均在逐文件表中；测试资产分类与限制沿用 [终端/测试/交付研究](../ruocun-discovery/research/04-terminal-platform-delivery.md)。保留语义入口，不要求 TS 测试直接在 Python 上执行。


| 既有 npm 入口 | 冻结命令 | 迁移处理 |
| --- | --- | --- |
| dev | `tsx src/index.ts` | 保留用途，按平台与 D/R/S/P 分类适配；发布/联网显式执行 |
| build | `tsc -p tsconfig.build.json` | 对应已确认的规格T-N入口；独立程序及其它衍生命令仍按路线票确定 |
| postinstall | `patch-package` | 保留用途，按平台与 D/R/S/P 分类适配；发布/联网显式执行 |
| bundle | `node scripts/sync-version.mjs && bun build ./src/index.ts --compile --outfile dao` | 来源命令保留记录；D2移出本轮独立产物，Python标准包build/安装继续 |
| bundle:install | `npm run bundle && cp dao "$HOME/.local/bin/dao" && codesign --force --sign - "$HOME/.local/bin/dao" && echo "已安装 → $HOME/.local/bin/dao"` | 保留用途，按平台与 D/R/S/P 分类适配；发布/联网显式执行 |
| start | `node dist/index.js` | 保留用途，按平台与 D/R/S/P 分类适配；发布/联网显式执行 |
| preview:welcome | `tsx scripts/preview-welcome.ts` | 保留用途，按平台与 D/R/S/P 分类适配；发布/联网显式执行 |
| preview:taiji | `tsx scripts/preview-taiji.ts` | 保留用途，按平台与 D/R/S/P 分类适配；发布/联网显式执行 |
| preview:ink | `tsx scripts/welcome-ink.tsx` | 保留用途，按平台与 D/R/S/P 分类适配；发布/联网显式执行 |
| test | `vitest run` | 对应已确认的规格T-N入口；独立程序及其它衍生命令仍按路线票确定 |
| test:watch | `vitest` | 对应已确认的规格T-N入口；独立程序及其它衍生命令仍按路线票确定 |
| typecheck | `tsc --noEmit` | 对应已确认的规格T-N入口；独立程序及其它衍生命令仍按路线票确定 |
| typecheck:eval | `tsc --noEmit -p evals/memory/tsconfig.json` | 对应已确认的规格T-N入口；独立程序及其它衍生命令仍按路线票确定 |
| prepublishOnly | `npm run build` | 对应已确认的规格T-N入口；独立程序及其它衍生命令仍按路线票确定 |
| verify:mem | `tsx scripts/verify-memory.ts` | 保留用途，按平台与 D/R/S/P 分类适配；发布/联网显式执行 |
| accept:mem | `bash scripts/accept-memory.sh` | 保留用途，按平台与 D/R/S/P 分类适配；发布/联网显式执行 |
| accept:cache | `bash scripts/accept-cache.sh` | 保留用途，按平台与 D/R/S/P 分类适配；发布/联网显式执行 |
| debug:distill | `tsx scripts/debug-distill.ts` | 保留用途，按平台与 D/R/S/P 分类适配；发布/联网显式执行 |
| debug:harness-wire | `tsx scripts/dump-harness-wire.ts` | 保留用途，按平台与 D/R/S/P 分类适配；发布/联网显式执行 |
| lint | `eslint .` | 对应已确认的规格T-N入口；独立程序及其它衍生命令仍按路线票确定 |


确定性恢复与等待脚本、真实模型 live 脚本、记忆/缓存/反思验收及评估 runner 的路径与 Python 对应在下表逐项列出。专题脚本即使名字含 replay，也按实际联网路径分类。


## A · 产品源码与源码内 fixture（234）

| ID | 原路径 | 拟目标/保留位置 | 职责/关系 | 处理/允许差异 | 关联案例族 | 状态/证据 |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="mm-366"></a>MM-366 | `src/agent/agent_defs.ts` | `src/ruocun/agent/agent_defs.py` | 运行、调度、后台与子代理；agent_defs；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 39定义现已消费mcpServers字符串引用；专属连接在子registry初始化/关闭，fork保持精确父工具；见本页批次05表。 |
| <a id="mm-368"></a>MM-368 | `src/agent/agent_handoff.ts` | `src/ruocun/agent/agent_handoff.py` | 运行、调度、后台与子代理；agent_handoff；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 38/40已接入子结果审查与后台运行取消，见本页批次02表；43增加代理消息接缝；[代理消息独审](../ruocun-next24h/evidence/review/b04-agent-messages-review.md) |
| <a id="mm-370"></a>MM-370 | `src/agent/agent_hooks.ts` | `src/ruocun/agent/agent_hooks.py` | 运行、调度、后台与子代理；agent_hooks；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 49独立子代理生命周期及回执；[子代理生命周期](../ruocun-next24h/evidence/n49-agent-lifecycle/README.md) |
| <a id="mm-372"></a>MM-372 | `src/agent/agent_lifecycle.ts` | `src/ruocun/agent/agent_lifecycle.py` | 运行、调度、后台与子代理；agent_lifecycle；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 40已实现后台运行终态与未知副作用边界，见本页批次02表；49验证停止Hook与已确认取消终态；[子代理生命周期](../ruocun-next24h/evidence/n49-agent-lifecycle/README.md) |
| <a id="mm-374"></a>MM-374 | `src/agent/agent_memory.ts` | `src/ruocun/agent/agent_memory.py` | 运行、调度、后台与子代理；agent_memory；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 39已注入角色长期记忆，工作树运行沿原项目记忆根 |
| <a id="mm-376"></a>MM-376 | `src/agent/agent_prompt.ts` | `src/ruocun/agent/agent_prompt.py` | 运行、调度、后台与子代理；agent_prompt；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-378"></a>MM-378 | `src/agent/agent_summary.ts` | `src/ruocun/agent/agent_summary.py` | 运行、调度、后台与子代理；agent_summary；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-380"></a>MM-380 | `src/agent/agent_tools.ts` | `src/ruocun/agent/agent_tools.py` | 运行、调度、后台与子代理；agent_tools；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 现有裁剪在 `agent/run_agent.py`，精确快照在 `tools/registry.py`，39/41定向验证通过 |
| <a id="mm-381"></a>MM-381 | `src/agent/background_delivery.ts` | `src/ruocun/agent/background_delivery.py` | 运行、调度、后台与子代理；background_delivery；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-383"></a>MM-383 | `src/agent/background_runtime.ts` | `src/ruocun/agent/background_runtime.py` | 运行、调度、后台与子代理；background_runtime；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-384"></a>MM-384 | `src/agent/background_test_helpers.ts` | `tests/support/background.py` | 运行、调度、后台与子代理；background_test_helpers；C2/C3 | S：测试辅助，不计产品功能实现 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-385"></a>MM-385 | `src/agent/background_types.ts` | `src/ruocun/agent/background_types.py` | 运行、调度、后台与子代理；background_types；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-388"></a>MM-388 | `src/agent/bundled_agents.ts` | `src/ruocun/agent/bundled_agents.py` | 运行、调度、后台与子代理；bundled_agents；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 38/39/40已绑定内置角色与真实模型、权限、背景选择 |
| <a id="mm-392"></a>MM-392 | `src/agent/cleanup.ts` | `src/ruocun/agent/cleanup.py` | 运行、调度、后台与子代理；cleanup；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 26已实现受控SQLite封存、身份核验后删除；保护活动/未决/附件及留存运行的工作树。见本页批次05表。 |
| <a id="mm-394"></a>MM-394 | `src/agent/compact.ts` | `src/ruocun/agent/compact.py` | 运行、调度、后台与子代理；compact；C2/C3 | S：成功压缩沿来源；ADR-0012失败/空摘要保留上下文停止，账本独立保留 | RUN / BG / REC | 批次03：成功压缩、失败保留与等待保存独审通过；反思另验。 |
| <a id="mm-396"></a>MM-396 | `src/agent/deck_bridge.ts` | `src/ruocun/agent/deck_bridge.py` | 运行、调度、后台与子代理；deck_bridge；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 56真实Deck协议/普通入口 |
| <a id="mm-399"></a>MM-399 | `src/agent/deck_messages.ts` | `src/ruocun/agent/deck_messages.py` | 运行、调度、后台与子代理；deck_messages；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 56真实Deck协议/普通入口 |
| <a id="mm-401"></a>MM-401 | `src/agent/fork_agent.ts` | `src/ruocun/agent/fork_agent.py` | 运行、调度、后台与子代理；fork_agent；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 41已实现当前进程fork消息与精确父工具目录 |
| <a id="mm-404"></a>MM-404 | `src/agent/loop.ts` | `src/ruocun/agent/loop.py` | 运行、调度、后台与子代理；loop；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 批次03：普通入口有界原模型重试、显式换账户、部分输出及持续不可用停止独审通过；其他来源分支见逐票。；44通过普通循环接续工具轮；[普通入口](../ruocun-next24h/evidence/batch-04/ordinary/README.md) |
| <a id="mm-408"></a>MM-408 | `src/agent/reflect_cadence.ts` | `src/ruocun/agent/reflect_cadence.py` | 运行、调度、后台与子代理；reflect_cadence；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n42/README.md) |
| <a id="mm-410"></a>MM-410 | `src/agent/reflect_persist.ts` | `src/ruocun/agent/reflect_persist.py` | 运行、调度、后台与子代理；reflect_persist；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n42/README.md) |
| <a id="mm-413"></a>MM-413 | `src/agent/reflect_prompts.ts` | `src/ruocun/agent/reflect_prompts.py` | 运行、调度、后台与子代理；reflect_prompts；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n42/README.md) |
| <a id="mm-415"></a>MM-415 | `src/agent/reflect_result.ts` | `src/ruocun/agent/reflect_result.py` | 运行、调度、后台与子代理；reflect_result；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n42/README.md) |
| <a id="mm-417"></a>MM-417 | `src/agent/resume_agent.ts` | `src/ruocun/agent/resume_agent.py` | 运行、调度、后台与子代理；resume_agent；C2/C3 | S：保留普通checkpoint恢复；R3特殊工具/提示现场不足明确拒绝，不降为普通agent | RUN / BG / REC | 17/40普通代理显式继续已验证；R3特殊fork缺现场明确拒绝 |
| <a id="mm-420"></a>MM-420 | `src/agent/runAgent.ts` | `src/ruocun/agent/run_agent.py` | 运行、调度、后台与子代理；runAgent；C2/C3 | S：当前fork/exactTools、权限与worktree边界沿来源；R3仅移出补足所有重启特殊现场的保证 | RUN / BG / REC | 38/39/40/41、43/49已落地；本批补专属MCP创建、转后台新owner重绑、拒绝与结束关闭、恢复摘要核对。见本页批次05表。 |
| <a id="mm-422"></a>MM-422 | `src/agent/session_scheduler.ts` | `src/ruocun/agent/session_scheduler.py` | 运行、调度、后台与子代理；session_scheduler；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 批次03：普通/loop、关闭清理及等待暂停后重开已独审。 |
| <a id="mm-424"></a>MM-424 | `src/agent/tasks.ts` | `src/ruocun/agent/tasks.py` | 运行、调度、后台与子代理；tasks；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 40/41、43、45、67已落地；46增加真实Monitor运行/停止、输出事件及owner丢失后保留历史、不重启。见本页批次05表。 |
| <a id="mm-426"></a>MM-426 | `src/agent/turn_budget.ts` | `src/ruocun/agent/turn_budget.py` | 运行、调度、后台与子代理；turn_budget；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-428"></a>MM-428 | `src/agent/turn_health.ts` | `src/ruocun/agent/turn_health.py` | 运行、调度、后台与子代理；turn_health；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n42/README.md) |
| <a id="mm-430"></a>MM-430 | `src/agent/unified_reflect.ts` | `src/ruocun/agent/unified_reflect.py` | 运行、调度、后台与子代理；unified_reflect；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n42/README.md) |
| <a id="mm-432"></a>MM-432 | `src/agent/worktree.ts` | `src/ruocun/agent/worktree.py` | 运行、调度、后台与子代理；worktree；C2/C3 | S：Python 对应，接口/行为保留；依赖允许替换 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-434"></a>MM-434 | `src/approval/stdin_prompt.ts` | `src/ruocun/approval/stdin_prompt.py` | 人工审批端口；stdin_prompt；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-436"></a>MM-436 | `src/approval/store.ts` | `src/ruocun/approval/store.py` | 人工审批端口；store；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-437"></a>MM-437 | `src/approval/types.ts` | `src/ruocun/approval/types.py` | 人工审批端口；types；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-439"></a>MM-439 | `src/client/client.ts` | `src/ruocun/client/client.py` | 模型协议与流；client；C2 | S：Python 对应，接口/行为保留；依赖允许替换 | WIRE | 04本票路径已实现；[04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；提交 9c7c43e/2b896f1/df552f4/dbdd0bc；其余子案例未验 ；06公开重试/取消/fallback路径已实现并独立通过（daf2f5d），见[06复核](integration-evidence/sprint06/README.md)；全族仍按各票验收 |
| <a id="mm-441"></a>MM-441 | `src/client/responses.ts` | `src/ruocun/client/responses.py` | 模型协议与流；responses；C2 | S：Python 对应，接口/行为保留；依赖允许替换 | WIRE | 05本票路径已实现；[05实现证据](evidence/05-responses/README.md)、[05独立复核](../../integration-evidence/05-responses/README.md)；提交 2884cac/b0b5052；非流式兜底与其余子案例未验 |
| <a id="mm-443"></a>MM-443 | `src/client/sse.ts` | `src/ruocun/client/sse.py` | 模型协议与流；sse；C2 | S：Python 对应，接口/行为保留；依赖允许替换 | WIRE | 04本票路径已实现；[04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；提交 9c7c43e/2b896f1/df552f4/dbdd0bc；其余子案例未验 |
| <a id="mm-444"></a>MM-444 | `src/client/types.ts` | `src/ruocun/client/types.py` | 模型协议与流；types；C2 | S：Python 对应，接口/行为保留；依赖允许替换 | WIRE | 04本票路径已实现；[04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；提交 9c7c43e/2b896f1/df552f4/dbdd0bc；其余子案例未验 |
| <a id="mm-446"></a>MM-446 | `src/commands/builtin.ts` | `src/ruocun/commands/builtin.py` | 命令解析与模板；builtin；C1 | S：Python 对应，接口/行为保留；依赖允许替换 | CMD | 44的六条内置命令已接线；[冻结提示对照](../ruocun-next24h/evidence/batch-04/n44/README.md) |
| <a id="mm-448"></a>MM-448 | `src/commands/commands.ts` | `src/ruocun/commands/catalog.py` 与 `src/ruocun/agent/runtime.py` | 命令解析与模板；commands；C1 | S：保留原生固定命令解析及保留分支，插件和自定义模板分支按ADR-0014移出 | CMD | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n70/catalog/README.md) |
| <a id="mm-450"></a>MM-450 | `src/commands/custom.ts` | `src/ruocun/commands/custom.py`（历史目标） | 命令解析与模板；custom；C1 | 本轮范围移出（37） | CMD | 保留来源记录；产品未实施 |
| <a id="mm-451"></a>MM-451 | `src/commands/scheduling.ts` | `src/ruocun/agent/session_scheduler.py` 与 `src/ruocun/agent/runtime.py` | 命令解析与模板；scheduling；C1 | S：Python 对应，接口/行为保留；依赖允许替换 | CMD | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n70/catalog/README.md) |
| <a id="mm-453"></a>MM-453 | `src/config/auth_wizard.ts` | `src/ruocun/config/auth_wizard.py` | 账户、凭据、信任、模型配置；auth_wizard；C0 | S：Python 对应，接口/行为保留；依赖允许替换 | CFG | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-455"></a>MM-455 | `src/config/credential.ts` | `src/ruocun/config/credential.py` | 账户、凭据、信任、模型配置；credential；C0 | S：Python 对应，接口/行为保留；依赖允许替换 | CFG | 04本票路径已实现；[04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；提交 9c7c43e/2b896f1/df552f4/dbdd0bc；其余子案例未验；58补齐系统凭据/私有原子保存，[独审](../ruocun-next24h/evidence/review/credentials-review.md)通过 |
| <a id="mm-457"></a>MM-457 | `src/config/env_file.ts` | `src/ruocun/config/env_file.py` | 账户、凭据、信任、模型配置；env_file；C0 | S：Python 对应，接口/行为保留；依赖允许替换 | CFG | 04本票路径已实现；[04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；提交 9c7c43e/2b896f1/df552f4/dbdd0bc；其余子案例未验 |
| <a id="mm-458"></a>MM-458 | `src/config/keychain.ts` | `src/ruocun/config/credential.py`、`src/ruocun/platform/windows/credentials.py` | 账户、凭据、信任、模型配置；keychain；C0 | S：Python 对应，接口/行为保留；依赖允许替换 | CFG | 58系统窄端口与普通keyRef入口已接；[真实新UUID及普通入口独审](../ruocun-next24h/evidence/review/credentials-review.md)通过 |
| <a id="mm-460"></a>MM-460 | `src/config/migrate_dirs.ts` | `src/ruocun/config/migrate_dirs.py` | 账户、凭据、信任、模型配置；migrate_dirs；C0 | S：Python 对应，接口/行为保留；依赖允许替换 | CFG | 04本票路径已实现；[04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；提交 9c7c43e/2b896f1/df552f4/dbdd0bc；其余子案例未验 |
| <a id="mm-462"></a>MM-462 | `src/config/model_selection.ts` | `src/ruocun/config/model_selection.py` | 账户、凭据、信任、模型配置；model_selection；C0 | S：Python 对应，接口/行为保留；依赖允许替换 | CFG | 04本票路径已实现；[04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；提交 9c7c43e/2b896f1/df552f4/dbdd0bc；其余子案例未验 |
| <a id="mm-464"></a>MM-464 | `src/config/profiles.ts` | `src/ruocun/config/profiles.py` | 账户、凭据、信任、模型配置；profiles；C0 | S：Python 对应，接口/行为保留；依赖允许替换 | CFG | 04本票路径已实现；[04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；提交 9c7c43e/2b896f1/df552f4/dbdd0bc；其余子案例未验 |
| <a id="mm-466"></a>MM-466 | `src/config/profiles_store.ts` | `src/ruocun/config/profiles_store.py` | 账户、凭据、信任、模型配置；profiles_store；C0 | S：Python 对应，接口/行为保留；依赖允许替换 | CFG | 04本票路径已实现；[04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；提交 9c7c43e/2b896f1/df552f4/dbdd0bc；其余子案例未验；58补齐系统凭据/私有原子保存，[独审](../ruocun-next24h/evidence/review/credentials-review.md)通过 |
| <a id="mm-468"></a>MM-468 | `src/config/trust.ts` | `src/ruocun/config/trust.py` | 账户、凭据、信任、模型配置；trust；C0 | S：Python 对应，接口/行为保留；依赖允许替换 | CFG | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-470"></a>MM-470 | `src/config/update_check.ts` | `src/ruocun/config/update_check.py` | 账户、凭据、信任、模型配置；update_check；C0 | S：Python 对应，接口/行为保留；依赖允许替换 | CFG | 未开始；产品证据无 |
| <a id="mm-472"></a>MM-472 | `src/config/validate_key.ts` | `src/ruocun/config/validate_key.py` | 账户、凭据、信任、模型配置；validate_key；C0 | S：Python 对应，接口/行为保留；依赖允许替换 | CFG | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-473"></a>MM-473 | `src/data/laozi-maxims.ts` | `src/ruocun/data/laozi_maxims.py` | 静态文化与界面资源；laozi-maxims；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-475"></a>MM-475 | `src/env_snapshot.ts` | `src/ruocun/env_snapshot.py` | 环境探测与边界注入；C0 | S：Python 对应，接口/行为保留；依赖允许替换 | PROMPT | 04本票路径已实现；[04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；提交 9c7c43e/2b896f1/df552f4/dbdd0bc；其余子案例未验 |
| <a id="mm-477"></a>MM-477 | `src/hooks/hooks.ts` | `src/ruocun/hooks/hooks.py` | Hook 发现、匹配与运行；hooks；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | EXT | 48命令、匹配与工具权限边界；[工具Hook独审](../ruocun-next24h/evidence/review/b04-hook-tool-review.md) |
| <a id="mm-480"></a>MM-480 | `src/i18n/i18n.ts` | `src/ruocun/i18n/i18n.py` | 中英文与语言状态；i18n；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-481"></a>MM-481 | `src/i18n/messages/en.ts` | `src/ruocun/i18n/messages/en.py` | 中英文与语言状态；en；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-482"></a>MM-482 | `src/i18n/messages/zh.ts` | `src/ruocun/i18n/messages/zh.py` | 中英文与语言状态；zh；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-483"></a>MM-483 | `src/index.ts` | `src/ruocun/__main__.py`、`src/ruocun/cli.py`、`src/ruocun/agent/runtime.py`、`src/ruocun/resources/help.zh-CN.txt` | 组合根/CLI/入口与收尾；C0/C1 | S：保留版本/帮助；ADR-0011仅逐轮文字、普通prompt与--continue；后置参数/命令明确拒绝 | ENT | 既有首版、终端及代理/Hooks入口保留；本批接会话命令、Monitor、MCP传输/搜索/命令及未决保护。见本页批次05表；完整体验仍归77/78。；批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n70/catalog/README.md) |
| <a id="mm-485"></a>MM-485 | `src/lsp/client.ts` | `src/ruocun/lsp/client.py` | 语言服务器协议；client；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | EXT | 55本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-lsp-review.md) |
| <a id="mm-487"></a>MM-487 | `src/lsp/config.ts` | `src/ruocun/lsp/config.py` | 语言服务器协议；config；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | EXT | 55本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-lsp-review.md) |
| <a id="mm-489"></a>MM-489 | `src/lsp/manager.ts` | `src/ruocun/lsp/manager.py` | 语言服务器协议；manager；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | EXT | 55本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-lsp-review.md) |
| <a id="mm-490"></a>MM-490 | `src/lsp/testfixtures/sample.ts` | 冻结TS样例复用，见`.scratch/ruocun-next24h/evidence/n55-real-server/`准备收据和验证脚本 | 语言服务器协议；sample；C4 | D：保留 TS 语言样例，作为数据而非核心实现 | EXT | 55本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-lsp-review.md) |
| <a id="mm-491"></a>MM-491 | `src/mcp/__fixtures__/fake-mcp-server.mjs` | `tests/support/mcp_server.py`、`tests/support/mcp_http.py`、`tests/support/mcp_caps.py` | MCP 扩展与生命周期；fake-mcp-server；C4 | S/R：协议服务端 fixture 改写；保留协议输出 | EXT | 51–54协议fixture已迁移为`tests/support/mcp_server.py`、`mcp_http.py`及`mcp_caps.py`，真实CLI断线副作用验证。见本页批次05表。 |
| <a id="mm-496"></a>MM-496 | `src/mcp/mcp.ts` | `src/ruocun/mcp/mcp.py` | MCP 扩展与生命周期；mcp；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | EXT | 51–54已实现stdio/HTTP/SSE、能力发现/更新、搜索激活、配置命令及未知结果停止自动重放（ADR-0003）。见本页批次05表。 |
| <a id="mm-498"></a>MM-498 | `src/memory/audit.ts` | `src/ruocun/memory/audit.py` | 长期记忆与上下文注入；audit；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MEM | 30已实现/独审；审核：保留来源审计及锁定/只读状态；[证据](../ruocun-next20h/evidence/n4-shared/README.md)；批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n57/README.md) |
| <a id="mm-500"></a>MM-500 | `src/memory/consolidate.ts` | `src/ruocun/memory/consolidate.py` | 长期记忆与上下文注入；consolidate；C6 | S：Python 对应；原门控和请求；写回保来源和locked | MEM | 32原生门控合并、确认后软取代、未知同名保留原字节已独审；[证据](../ruocun-next20h/evidence/n4-shared/README.md#32普通入口) |
| <a id="mm-502"></a>MM-502 | `src/memory/distill.ts` | `src/ruocun/memory/distill.py` | 长期记忆与上下文注入；distill；C6 | S：保留两种源请求和候选过滤 | MEM | 32实际已保存轨迹和固定模型响应已独审；冻结普通入口无直接蒸馏调度，42反思后置；[证据](../ruocun-next20h/evidence/n4-shared/README.md#32普通入口) |
| <a id="mm-504"></a>MM-504 | `src/memory/frontmatter.ts` | `src/ruocun/memory/frontmatter.py` | 长期记忆与上下文注入；frontmatter；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MEM | 30已实现/独审；Markdown解析与写前往返保护；[证据](../ruocun-next20h/evidence/n4-shared/README.md) |
| <a id="mm-506"></a>MM-506 | `src/memory/gc.ts` | `src/ruocun/memory/gc.py` | 长期记忆与上下文注入；gc；C6 | S：原留存/过期阈值；锁定优先保护 | MEM | 32真实启动GC及未知仅计已确认项已独审；[证据](../ruocun-next20h/evidence/n4-memory-gc/README.md) |
| <a id="mm-508"></a>MM-508 | `src/memory/hash.ts` | `src/ruocun/memory/hash.py` | 长期记忆与上下文注入；hash；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MEM | 30已实现/独审；冻结内容哈希；[证据](../ruocun-next20h/evidence/n4-shared/README.md) |
| <a id="mm-510"></a>MM-510 | `src/memory/inject.ts` | `src/ruocun/memory/inject.py` | 长期记忆与上下文注入；inject；C6 | S：Python 对应，保留全文/索引和项目筛选 | MEM | 31单次快照与真实恢复/禁用已独审；[证据](../ruocun-next20h/evidence/n4-shared/README.md#31普通入口) |
| <a id="mm-512"></a>MM-512 | `src/memory/memory_audit.ts` | `src/ruocun/memory/memory_audit.py` | 长期记忆与上下文注入；memory_audit；C6 | S：保留32实际维护相关事件与开关；其它事件后续 | MEM | 32蒸馏/合并审计子路径已独审；实际合并回执落盘；[证据](../ruocun-next20h/evidence/n4-shared/README.md#32普通入口)；批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n57/README.md) |
| <a id="mm-514"></a>MM-514 | `src/memory/store.ts` | `src/ruocun/memory/store.py` | 长期记忆与上下文注入；store；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MEM | 30已实现/独审；三域原生持久写、兼容只读、坏原件保留；[证据](../ruocun-next20h/evidence/n4-shared/README.md) |
| <a id="mm-516"></a>MM-516 | `src/memory/types.ts` | `src/ruocun/memory/types.py` | 长期记忆与上下文注入；types；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MEM | 30已实现/独审；五类型及原默认值；[证据](../ruocun-next20h/evidence/n4-shared/README.md) |
| <a id="mm-518"></a>MM-518 | `src/memory/validate.ts` | `src/ruocun/memory/validate.py` | 长期记忆与上下文注入；validate；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MEM | 30已实现/独审；来源、变更与失效判定；[证据](../ruocun-next20h/evidence/n4-shared/README.md) |
| <a id="mm-520"></a>MM-520 | `src/obs/attrs.ts` | `src/ruocun/obs/attrs.py` | 观测与审计包装；attrs；C2 | S：Python 对应，接口/行为保留；依赖允许替换 | OBS | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n57/README.md) |
| <a id="mm-522"></a>MM-522 | `src/obs/backend.ts` | `src/ruocun/obs/backend.py` | 观测与审计包装；backend；C2 | S：Python 对应，接口/行为保留；依赖允许替换 | OBS | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n57/README.md) |
| <a id="mm-523"></a>MM-523 | `src/obs/index.ts` | `src/ruocun/obs/__init__.py` 与 `src/ruocun/agent/runtime.py` | 观测与审计包装；index；C2 | S：Python 对应，接口/行为保留；依赖允许替换 | OBS | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n57/README.md) |
| <a id="mm-525"></a>MM-525 | `src/obs/init.ts` | `src/ruocun/obs/init.py` | 观测与审计包装；init；C2 | S：Python 对应，接口/行为保留；依赖允许替换 | OBS | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n57/README.md) |
| <a id="mm-527"></a>MM-527 | `src/obs/wrap.ts` | `src/ruocun/obs/wrap.py` | 观测与审计包装；wrap；C2 | S：Python 对应，接口/行为保留；依赖允许替换 | OBS | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n57/README.md) |
| <a id="mm-528"></a>MM-528 | `src/permissions/audit.ts` | `src/ruocun/permissions/audit.py` | 分层规则、安全与权限门；audit；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 已接来源分类/审计与普通入口；[模块与TTY独审](../ruocun-next24h/evidence/review/permissions-review.md)通过，固定包出口待验 |
| <a id="mm-529"></a>MM-529 | `src/permissions/bash/ast.ts` | `src/ruocun/permissions/bash/ast.py` | 分层规则、安全与权限门；ast；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-531"></a>MM-531 | `src/permissions/bash/bash_ast.ts` | `src/ruocun/permissions/bash/bash_ast.py` | 分层规则、安全与权限门；bash_ast；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-532"></a>MM-532 | `src/permissions/bash/bash_parser.ts` | `src/ruocun/permissions/bash/bash_parser.py` | 分层规则、安全与权限门；bash_parser；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-533"></a>MM-533 | `src/permissions/bash/parser.ts` | `src/ruocun/permissions/bash/parser.py` | 分层规则、安全与权限门；parser；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-535"></a>MM-535 | `src/permissions/bash_preprocess.ts` | `src/ruocun/permissions/bash_preprocess.py` | 分层规则、安全与权限门；bash_preprocess；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-537"></a>MM-537 | `src/permissions/bash_safety.ts` | `src/ruocun/permissions/bash_safety.py` | 分层规则、安全与权限门；bash_safety；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-539"></a>MM-539 | `src/permissions/classifier.ts` | `src/ruocun/permissions/classifier.py` | 分层规则、安全与权限门；classifier；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 已接来源分类/审计与普通入口；[模块与TTY独审](../ruocun-next24h/evidence/review/permissions-review.md)通过，固定包出口待验 |
| <a id="mm-541"></a>MM-541 | `src/permissions/classifier_model.ts` | `src/ruocun/permissions/classifier_model.py` | 分层规则、安全与权限门；classifier_model；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 已接来源分类/审计与普通入口；[模块与TTY独审](../ruocun-next24h/evidence/review/permissions-review.md)通过，固定包出口待验 |
| <a id="mm-543"></a>MM-543 | `src/permissions/dangerous_patterns.ts` | `src/ruocun/permissions/dangerous_patterns.py` | 分层规则、安全与权限门；dangerous_patterns；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-545"></a>MM-545 | `src/permissions/engine.ts` | `src/ruocun/permissions/engine.py` | 分层规则、安全与权限门；engine；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-547"></a>MM-547 | `src/permissions/gate.ts` | `src/ruocun/permissions/gate.py` | 分层规则、安全与权限门；gate；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-549"></a>MM-549 | `src/permissions/identity.ts` | `src/ruocun/permissions/identity.py` | 分层规则、安全与权限门；identity；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-552"></a>MM-552 | `src/permissions/perm_audit.ts` | `src/ruocun/permissions/perm_audit.py` | 分层规则、安全与权限门；perm_audit；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 已接来源分类/审计与普通入口；[模块与TTY独审](../ruocun-next24h/evidence/review/permissions-review.md)通过，固定包出口待验 |
| <a id="mm-554"></a>MM-554 | `src/permissions/rules.ts` | `src/ruocun/permissions/rules.py` | 分层规则、安全与权限门；rules；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-556"></a>MM-556 | `src/permissions/sanitize.ts` | `src/ruocun/permissions/sanitize.py` | 分层规则、安全与权限门；sanitize；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 已接来源分类/审计与普通入口；[模块与TTY独审](../ruocun-next24h/evidence/review/permissions-review.md)通过，固定包出口待验 |
| <a id="mm-558"></a>MM-558 | `src/permissions/secrets.ts` | `src/ruocun/permissions/secrets.py` | 分层规则、安全与权限门；secrets；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 已接来源分类/审计与普通入口；[模块与TTY独审](../ruocun-next24h/evidence/review/permissions-review.md)通过，固定包出口待验 |
| <a id="mm-560"></a>MM-560 | `src/permissions/settings.ts` | `src/ruocun/permissions/settings.py` | 分层规则、安全与权限门；settings；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | PERM | 本批适用规则/模式/审批或解析模块已实现并独审；普通入口/固定产物待验，classifier/其它后继未据此完成；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-562"></a>MM-562 | `src/plugins.ts` | `src/ruocun/plugins.py`（历史目标） | 插件发现/安装/删除；C4 | 本轮范围移出（50） | EXT | 保留来源记录；产品未实施 |
| <a id="mm-564"></a>MM-564 | `src/project_doc.ts` | `src/ruocun/project_doc.py` | 用户及祖先项目指令发现；C0 | S：RUOCUN原生名称及D09显式兼容；工程AGENTS不自动加载 | CFG | 已实现；7项来源/适配及模块独审通过，普通入口已定向接通；[A证据](../ruocun-advanced-a/evidence/integration/README.md)；最终r2自动出口已通过 |
| <a id="mm-566"></a>MM-566 | `src/prompt/system_prompt.ts` | `src/ruocun/prompt/system_prompt.py` | 系统提示模板；system_prompt；C0/C2 | S：Python 对应，接口/行为保留；依赖允许替换 | PROMPT | 04本票路径已实现；[04实现证据](evidence/04-chat/README.md)、[04独立复核](../../integration-evidence/04-chat/README.md)；提交 9c7c43e/2b896f1/df552f4/dbdd0bc；其余子案例未验；44中英文长任务指令；[冻结提示对照](../ruocun-next24h/evidence/batch-04/n44/README.md) |
| <a id="mm-568"></a>MM-568 | `src/repl.ts` | `src/ruocun/agent/runtime.py` | 非 TTY 输入和基础命令；C1 | S：Python 对应，接口/行为保留；依赖允许替换 | ENT | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n70/catalog/README.md) |
| <a id="mm-570"></a>MM-570 | `src/repomap/extract.ts` | `src/ruocun/repomap/extract.py` | 代码图与预算裁剪；extract；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MAP | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-572"></a>MM-572 | `src/repomap/graph.ts` | `src/ruocun/repomap/graph.py` | 代码图与预算裁剪；graph；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MAP | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-574"></a>MM-574 | `src/repomap/index.ts` | `src/ruocun/repomap/index.py` | 代码图与预算裁剪；index；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MAP | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-575"></a>MM-575 | `src/repomap/languages.ts` | `src/ruocun/repomap/languages.py` | 代码图与预算裁剪；languages；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MAP | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-576"></a>MM-576 | `src/repomap/loader.ts` | `src/ruocun/repomap/loader.py` | 代码图与预算裁剪；loader；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MAP | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-578"></a>MM-578 | `src/repomap/render.ts` | `src/ruocun/repomap/render.py` | 代码图与预算裁剪；render；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MAP | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-579"></a>MM-579 | `src/repomap/wasm-assets.ts` | `src/ruocun/repomap/loader.py`及版本锁中的原生grammar | 代码图与预算裁剪；wasm-assets；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MAP | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-580"></a>MM-580 | `src/repomap/wasm.d.ts` | `src/ruocun/repomap/loader.py`及版本锁中的原生grammar | 代码图与预算裁剪；wasm.d；C6 | S：Python 对应，接口/行为保留；依赖允许替换 | MAP | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-582"></a>MM-582 | `src/schedule.ts` | `src/ruocun/schedule.py` | 系统定时平台路由与准确能力说明；C7 | S：W3取消Windows Task Scheduler/dispatcher，Windows明确不支持；来源其它平台cron语义保留未验 | WIN | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n59/README.md) |
| <a id="mm-584"></a>MM-584 | `src/session/audit_switch.ts` | 各审计 sink 的 `resolve_env` 开关 | 会话与持久化；audit_switch；C3 | S：Python 对应，接口/行为保留；依赖允许替换 | REC | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n57/README.md) |
| <a id="mm-586"></a>MM-586 | `src/session/cache_audit.ts` | `src/ruocun/session/cache_audit.py` | 会话与持久化；cache_audit；C3 | S：来源审计/报告，main tail为空、msgs单独hash；summary不记录正文 | REC | 已实现/模块独审，main/summary已接线；[A证据](../ruocun-advanced-a/evidence/integration/README.md)；最终r2自动出口已通过 |
| <a id="mm-588"></a>MM-588 | `src/session/checkpoint.ts` | `src/ruocun/session/checkpoint.py` | 会话与持久化；checkpoint；C3 | S：Python 对应，接口/行为保留；依赖允许替换 | REC | 未开始；产品证据无 |
| <a id="mm-590"></a>MM-590 | `src/session/cost.ts` | `src/ruocun/session/cost.py` | 会话与持久化；cost；C3 | S：本进程分模型计价沿来源；R1移出历史费用完整连续，重启新费用/预算口径明确 | REC | 来源内存计价已实现，20条冻结价格；19项来源测试及[独立复核](integration-evidence/session-cost/README.md)通过；28统计范围/命令接线未完成 |
| <a id="mm-591"></a>MM-591 | `src/session/durable_file.ts` | `src/ruocun/session/durable_file.py` | 会话与持久化；durable_file；C3 | S：Python 对应，接口/行为保留；依赖允许替换 | REC | 07保存/恢复子路径已实现；实际拆分见[来源映射](evidence/07-store/sprint-session/README.md)，[独立复核](integration-evidence/sprint07/README.md)；完整列表/session成本等后续票保持未验 |
| <a id="mm-593"></a>MM-593 | `src/session/durable_store.ts` | `src/ruocun/session/durable_store.py` | 会话与持久化；durable_store；C3 | S：Python 对应，接口/行为保留；依赖允许替换 | REC | 07保存/恢复子路径已实现；实际拆分见[来源映射](evidence/07-store/sprint-session/README.md)，[独立复核](integration-evidence/sprint07/README.md)；完整列表/session成本等后续票保持未验；批次02增强候选见本页细分出口 |
| <a id="mm-595"></a>MM-595 | `src/session/log.ts` | `src/ruocun/session/log.py` | 会话与持久化；log；C3 | S：Python 对应，接口/行为保留；依赖允许替换 | REC | 07原保存/恢复保留；26已实现同cwd未完成筛选、显式ID、列表/命名/分支/清空/Markdown导出和受控清理。见本页批次05表。 |
| <a id="mm-597"></a>MM-597 | `src/session/process_identity.ts` | `src/ruocun/session/process_identity.py` | 会话与持久化；process_identity；C3 | S：Python 对应，接口/行为保留；依赖允许替换 | REC | 07保存/恢复子路径已实现；实际拆分见[来源映射](evidence/07-store/sprint-session/README.md)，[独立复核](integration-evidence/sprint07/README.md)；完整列表/session成本等后续票保持未验 |
| <a id="mm-598"></a>MM-598 | `src/session/recovery.ts` | `src/ruocun/session/recovery.py` | 会话与持久化；recovery；C3 | S：Python 对应，接口/行为保留；依赖允许替换 | REC | 17原显式恢复保留；54接MCP未知结果跨重开阻挡，原ID与换ID均不自动重放；子代理绑定实际连接配置摘要。见本页批次05表。 |
| <a id="mm-600"></a>MM-600 | `src/session/session.ts` | `src/ruocun/session/session.py` | 会话与持久化；session；C3 | S：保留消息/model/mode/title及四累计token恢复；R1不补齐历史分模型费用，准确标记重启统计/预算口径 | REC | 07、28已完成；26补标题与任务摘要分离、聊天分支、清空及暂停保存，分支不复制执行账本；R1费用口径保持。见本页批次05表。 |
| <a id="mm-601"></a>MM-601 | `src/session/sqlite.ts` | `src/ruocun/session/sqlite.py` | 会话与持久化；sqlite；C3 | S：Python 对应，接口/行为保留；依赖允许替换 | REC | 07保存/恢复子路径已实现；实际拆分见[来源映射](evidence/07-store/sprint-session/README.md)，[独立复核](integration-evidence/sprint07/README.md)；完整列表/session成本等后续票保持未验 |
| <a id="mm-602"></a>MM-602 | `src/session/tool_execution.ts` | `src/ruocun/session/tool_execution.py` | 会话与持久化；tool_execution；C3 | S：Python 对应，接口/行为保留；依赖允许替换 | REC | 未开始；产品证据无 |
| <a id="mm-604"></a>MM-604 | `src/skills/adapt.ts` | `src/ruocun/skills/adapt.py` | 技能加载、发现、安装、适配；adapt；C4/C6 | S：Python 对应，接口/行为保留；依赖允许替换 | EXT | 36来源外来正文结构识别已独审；原文保留；[证据](../ruocun-next20h/evidence/n3-install-shared/README.md) |
| <a id="mm-606"></a>MM-606 | `src/skills/bundled.ts` | `src/ruocun/skills/bundled.py`、`src/ruocun/skills/control.py` | 技能加载、发现、安装、适配；bundled；C4/C6 | S/D：冻结8core运行时正文/元信息完整保留 | EXT | 8core已实现/独审TS运行时golden及安装字节一致；[A证据](../ruocun-advanced-a/evidence/integration/README.md)；34选择/禁用写入模块现已另行独审；实际路由与最终包仍待收口 |
| <a id="mm-608"></a>MM-608 | `src/skills/convert.ts` | `src/ruocun/skills/convert.py` | 技能加载、发现、安装、适配；convert；C4/C6 | S：Python 对应，接口/行为保留；依赖允许替换 | EXT | 36原生缓存/回退与实际普通入口合成辅助响应已独审；[证据](../ruocun-next20h/evidence/n3-install-shared/README.md) |
| <a id="mm-610"></a>MM-610 | `src/skills/discover.ts` | `src/ruocun/skills/discover.py` | 技能加载、发现、安装、适配；discover；C4/C6 | S：Python 对应，接口/行为保留；依赖允许替换 | EXT | 35已实现并独审；启动paths、嵌套/禁用、真实文件去重、完整工具批后目录确认和实际调用；[普通入口](../ruocun-next20h/evidence/n3-shared/README.md)；批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n71-entry/README.md) |
| <a id="mm-612"></a>MM-612 | `src/skills/install.ts` | `src/ruocun/skills/install.py` | 技能加载、发现、安装、适配；install；C4/C6 | S：Python 对应，接口/行为保留；依赖允许替换 | EXT | 36完整本地资源、Git argv、同名回滚/未知保留及Windows路径边界已独审；[证据](../ruocun-next20h/evidence/n3-install-shared/README.md) |
| <a id="mm-614"></a>MM-614 | `src/skills/skill_audit.ts` | `src/ruocun/skills/skill_audit.py` | 技能加载、发现、安装、适配；skill_audit；C4/C6 | S：Python 对应，接口/行为保留；依赖允许替换 | EXT | 35已实现并独审；实际loaded/轮号、坏行容错及仅LF，普通入口实际落盘；[审查](../ruocun-next20h/evidence/review/n3-skills-entry-review.md) |
| <a id="mm-616"></a>MM-616 | `src/skills/skills.ts` | `src/ruocun/skills/skills.py` | 技能加载、发现、安装、适配；skills；C4/C6 | S：来源frontmatter子集、slug/namespace/覆盖及调用标记；D09原生/兼容顺序 | EXT | 静态加载已实现/模块独审；启动装配及普通入口定向通过；[A证据](../ruocun-advanced-a/evidence/integration/README.md)；35运行时发现尚未实现 |
| <a id="mm-619"></a>MM-619 | `src/skills/usage.ts` | `src/ruocun/skills/usage.py` | 技能加载、发现、安装、适配；usage；C4/C6 | S：Python 对应，接口/行为保留；依赖允许替换 | EXT | 35已实现并独审；计数/衰减与原生私有skill-state写入，坏原件/未知保留；[入口证据](../ruocun-next20h/evidence/n3-shared/README.md) |
| <a id="mm-621"></a>MM-621 | `src/tools/agent.ts` | `src/ruocun/tools/agent.py` | 工具定义、注册和执行支撑；agent；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 43批量并发、按原序收结果和排队取消；[代理消息独审](../ruocun-next24h/evidence/review/b04-agent-messages-review.md) |
| <a id="mm-623"></a>MM-623 | `src/tools/ask_user.ts` | `src/ruocun/tools/ask_user.py` | 工具定义、注册和执行支撑；ask_user；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 已集成普通问答/用户消息；[来源与普通TTY独审](../ruocun-next24h/evidence/review/user-tools-review.md)通过 |
| <a id="mm-624"></a>MM-624 | `src/tools/config.ts` | `src/ruocun/tools/config.py` | 工具定义、注册和执行支撑；config；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 25本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-config-review.md) |
| <a id="mm-625"></a>MM-625 | `src/tools/cron_tools.ts` | `src/ruocun/tools/cron_tools.py` | 工具定义、注册和执行支撑；cron_tools；C4 | S：W3保留定义/来源其它平台语义，Windows系统定时准确不支持，不改成会话loop | TOOL | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n59/README.md) |
| <a id="mm-627"></a>MM-627 | `src/tools/diagnostics.ts` | `src/ruocun/tools/diagnostics.py` | 工具定义、注册和执行支撑；diagnostics；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 未开始；产品证据无 |
| <a id="mm-629"></a>MM-629 | `src/tools/diff_hunk.ts` | `src/ruocun/tools/edit_file.py` | 工具定义、注册和执行支撑；diff_hunk；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 10适用来源差异/展示已实现并独审；[来源证据](../ruocun-next20h/evidence/n2-editjournal/source.md) |
| <a id="mm-631"></a>MM-631 | `src/tools/edit_file.ts` | `src/ruocun/tools/edit_file.py` | 工具定义、注册和执行支撑；edit_file；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 10完整前台Edit路径与真实恢复已独审；[来源](../ruocun-next20h/evidence/n2-editjournal/source.md)、[恢复](../ruocun-next20h/evidence/n2-editjournal/recovery.md)；35成功访问回调已接 |
| <a id="mm-633"></a>MM-633 | `src/tools/edit_mismatch.ts` | `src/ruocun/tools/edit_file.py` | 工具定义、注册和执行支撑；edit_mismatch；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 10适用来源匹配、UTF16边界和差异诊断已实现并独审；[来源证据](../ruocun-next20h/evidence/n2-editjournal/source.md) |
| <a id="mm-635"></a>MM-635 | `src/tools/enter_worktree.ts` | `src/ruocun/tools/enter_worktree.py` | 工具定义、注册和执行支撑；enter_worktree；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 未开始；产品证据无 |
| <a id="mm-637"></a>MM-637 | `src/tools/exec_shell.ts` | `src/ruocun/tools/exec_shell.py` | 工具定义、注册和执行支撑；exec_shell；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m02-shell/README.md)；完整源文件其余能力未宣称通过；13/14实际方言与前台实时输出/取消[独审](../ruocun-next24h/evidence/review/foreground-review.md)通过，15后台进行；批次02增强候选见本页细分出口 |
| <a id="mm-639"></a>MM-639 | `src/tools/exec_shell_kill.ts` | `src/ruocun/tools/exec_shell_kill.py` | 工具定义、注册和执行支撑；exec_shell_kill；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 15本票路径已集成并独审；见N24 runner与纯安装证据，16/17范围按后票 |
| <a id="mm-640"></a>MM-640 | `src/tools/exec_shell_poll.ts` | `src/ruocun/tools/exec_shell_poll.py` | 工具定义、注册和执行支撑；exec_shell_poll；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 15本票路径已集成并独审；见N24 runner与纯安装证据，16/17范围按后票；批次02增强候选见本页细分出口 |
| <a id="mm-642"></a>MM-642 | `src/tools/execute.ts` | `src/ruocun/tools/execute.py`、`src/ruocun/tools/tool_batch.py`、`src/ruocun/agent/loop.py` | 工具定义、注册和执行支撑；execute；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 12前台安全批/屏障/预批及故障保真已独审；[批与普通入口](../ruocun-next20h/evidence/n2-shared/README.md)；Hook/network母路径后置；批次02增强候选见本页细分出口 |
| <a id="mm-645"></a>MM-645 | `src/tools/exit_worktree.ts` | `src/ruocun/tools/exit_worktree.py` | 工具定义、注册和执行支撑；exit_worktree；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 未开始；产品证据无 |
| <a id="mm-647"></a>MM-647 | `src/tools/fetch_cache.ts` | `src/ruocun/tools/fetch_cache.py` | 工具定义、注册和执行支撑；fetch_cache；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 22本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-webfetch-review.md) |
| <a id="mm-649"></a>MM-649 | `src/tools/fetch_extract.ts` | `src/ruocun/tools/fetch_extract.py` | 工具定义、注册和执行支撑；fetch_extract；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 22本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-webfetch-review.md) |
| <a id="mm-651"></a>MM-651 | `src/tools/fetch_url.ts` | `src/ruocun/tools/fetch_url.py` | 工具定义、注册和执行支撑；fetch_url；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 22本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-webfetch-review.md) |
| <a id="mm-653"></a>MM-653 | `src/tools/file_lock.ts` | `src/ruocun/tools/paths.py` | 工具定义、注册和执行支撑；file_lock；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-655"></a>MM-655 | `src/tools/file_search.ts` | `src/ruocun/tools/glob_files.py` | 工具定义、注册和执行支撑；file_search；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 保留本票来源语义已实现并模块独审；Grep沿已批准Python re差异；注册/普通入口/固定产物待验；[19证据](../ruocun-next20h/evidence/n2-search/README.md) |
| <a id="mm-657"></a>MM-657 | `src/tools/fs_atomic.ts` | `src/ruocun/tools/paths.py` | 工具定义、注册和执行支撑；fs_atomic；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-659"></a>MM-659 | `src/tools/glob.ts` | `src/ruocun/tools/glob.py` | 工具定义、注册和执行支撑；glob；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-661"></a>MM-661 | `src/tools/grep_files.ts` | `src/ruocun/tools/grep_files.py` | 工具定义、注册和执行支撑；grep_files；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 保留本票来源语义已实现并模块独审；Grep沿已批准Python re差异；注册/普通入口/固定产物待验；[19证据](../ruocun-next20h/evidence/n2-search/README.md) |
| <a id="mm-662"></a>MM-662 | `src/tools/lang.ts` | `src/ruocun/tools/lang.py` | 工具定义、注册和执行支撑；lang；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 未开始；产品证据无 |
| <a id="mm-664"></a>MM-664 | `src/tools/list_dir.ts` | `src/ruocun/tools/list_dir.py` | 工具定义、注册和执行支撑；list_dir；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 保留本票来源语义已实现并模块独审；Grep沿已批准Python re差异；注册/普通入口/固定产物待验；[19证据](../ruocun-next20h/evidence/n2-search/README.md) |
| <a id="mm-666"></a>MM-666 | `src/tools/lsp.ts` | `src/ruocun/tools/lsp.py` | 工具定义、注册和执行支撑；lsp；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 55本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-lsp-review.md) |
| <a id="mm-668"></a>MM-668 | `src/tools/managed_shell.ts` | `src/ruocun/tools/managed_shell.py` | 工具定义、注册和执行支撑；managed_shell；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 15本票路径已集成并独审；见N24 runner与纯安装证据，16/17范围按后票；批次02增强候选见本页细分出口 |
| <a id="mm-670"></a>MM-670 | `src/tools/memory_read.ts` | `src/ruocun/tools/memory_read.py` | 工具定义、注册和执行支撑；memory_read；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 30已实现/独审；常驻只读工具、实际读回；[证据](../ruocun-next20h/evidence/n4-shared/README.md) |
| <a id="mm-672"></a>MM-672 | `src/tools/memory_write.ts` | `src/ruocun/tools/memory_write.py` | 工具定义、注册和执行支撑；memory_write；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 30已实现/独审；plan/auto常驻，独占持久意图；持久字段凭据检查；[证据](../ruocun-next20h/evidence/n4-shared/README.md) |
| <a id="mm-674"></a>MM-674 | `src/tools/message_parent.ts` | `src/ruocun/tools/message_parent.py` | 工具定义、注册和执行支撑；message_parent；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 43普通托管子代理主动可见，父入口仍延迟；[代理消息独审](../ruocun-next24h/evidence/review/b04-agent-messages-review.md) |
| <a id="mm-676"></a>MM-676 | `src/tools/monitor.ts` | `src/ruocun/tools/monitor.py` | 工具定义、注册和执行支撑；monitor；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 46已接来源schema、按行输出、persistent/超时、TaskStop及真实进程终态；见本页批次05表。 |
| <a id="mm-678"></a>MM-678 | `src/tools/notebook_edit.ts` | `src/ruocun/tools/notebook_edit.py`（历史目标） | 工具定义、注册和执行支撑；notebook_edit；C4 | 本轮范围移出（20） | TOOL | 保留来源记录；产品未实施 |
| <a id="mm-680"></a>MM-680 | `src/tools/notify_user.ts` | `src/ruocun/tools/notify_user.py` | 工具定义、注册和执行支撑；notify_user；C4 | S：W6终端内提示与安全标题；准确说明未发桌面通知，能力描述差异记录 | TOOL | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-682"></a>MM-682 | `src/tools/output.ts` | `src/ruocun/tools/output.py` | 工具定义、注册和执行支撑；output；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 未开始；产品证据无 |
| <a id="mm-684"></a>MM-684 | `src/tools/paths.ts` | `src/ruocun/tools/paths.py` | 工具定义、注册和执行支撑；paths；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-685"></a>MM-685 | `src/tools/pkg_mgr_pattern.ts` | `src/ruocun/tools/pkg_mgr_pattern.py` | 工具定义、注册和执行支撑；pkg_mgr_pattern；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 未开始；产品证据无 |
| <a id="mm-687"></a>MM-687 | `src/tools/plan_mode.ts` | `src/ruocun/tools/plan_mode.py` | 工具定义、注册和执行支撑；plan_mode；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 当前原生模式/规划工具已实现并独审；API裁剪和loop硬门模块通过，普通入口待最终验；MCP未完成 |
| <a id="mm-689"></a>MM-689 | `src/tools/process_manager.ts` | `src/ruocun/tools/process_manager.py` | 工具定义、注册和执行支撑；process_manager；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 未开始；产品证据无 |
| <a id="mm-691"></a>MM-691 | `src/tools/read_file.ts` | `src/ruocun/tools/read_file.py` | 工具定义、注册和执行支撑；read_file；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-693"></a>MM-693 | `src/tools/registry.ts` | `src/ruocun/tools/registry.py` | 工具定义、注册和执行支撑；registry；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-695"></a>MM-695 | `src/tools/repo_map.ts` | `src/ruocun/tools/repo_map.py` | 工具定义、注册和执行支撑；repo_map；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-696"></a>MM-696 | `src/tools/safe_env.ts` | `src/ruocun/tools/safe_env.py` | 工具定义、注册和执行支撑；safe_env；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 未开始；产品证据无 |
| <a id="mm-698"></a>MM-698 | `src/tools/sandbox.ts` | `src/ruocun/platform/sandbox.py` | 工具定义、注册和执行支撑；sandbox；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 60/61 Windows与WSL实测，macOS参数验证 |
| <a id="mm-700"></a>MM-700 | `src/tools/schedule_tool.ts` | `src/ruocun/tools/schedule_tool.py` | 工具定义、注册和执行支撑；schedule_tool；C4 | S：W3保留来源平台路由/schema，Windows系统定时准确不支持 | TOOL | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n59/README.md) |
| <a id="mm-702"></a>MM-702 | `src/tools/schema.ts` | `src/ruocun/tools/schema.py` | 工具定义、注册和执行支撑；schema；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-703"></a>MM-703 | `src/tools/send_message.ts` | `src/ruocun/tools/send_message.py` | 工具定义、注册和执行支撑；send_message；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 已集成普通问答/用户消息；[来源与普通TTY独审](../ruocun-next24h/evidence/review/user-tools-review.md)通过 |
| <a id="mm-704"></a>MM-704 | `src/tools/shell_runner.ts` | `src/ruocun/tools/shell_runner.py` | 工具定义、注册和执行支撑；shell_runner；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 15本票路径已集成并独审；见N24 runner与纯安装证据，16/17范围按后票 |
| <a id="mm-705"></a>MM-705 | `src/tools/skill.ts` | `src/ruocun/tools/skill.py` | 工具定义、注册和执行支撑；skill；C4 | S：来源按名/slug/namespace加载正文与资源根；附准确阶段能力提示 | TOOL | 已实现/模块独审；普通CLI模型调用及手动正文已定向通过；[A证据](../ruocun-advanced-a/evidence/integration/README.md)；最终r2自动出口已通过 |
| <a id="mm-707"></a>MM-707 | `src/tools/skill_install.ts` | `src/ruocun/tools/skill_install.py` | 工具定义、注册和执行支撑；skill_install；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 36SkillInstall实际审批、完整配对后同会话刷新已独审；[证据](../ruocun-next20h/evidence/n3-install-shared/README.md) |
| <a id="mm-709"></a>MM-709 | `src/tools/spill.ts` | `src/ruocun/tools/spill.py` | 工具定义、注册和执行支撑；spill；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-711"></a>MM-711 | `src/tools/ssrf.ts` | `src/ruocun/tools/ssrf.py` | 工具定义、注册和执行支撑；ssrf；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 22本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-webfetch-review.md) |
| <a id="mm-713"></a>MM-713 | `src/tools/task_create.ts` | `src/ruocun/tools/task_create.py` | 工具定义、注册和执行支撑；task_create；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 45：普通入口注册，真实SQLite建记录和重开已独审。 |
| <a id="mm-715"></a>MM-715 | `src/tools/task_get.ts` | `src/ruocun/tools/task_get.py` | 工具定义、注册和执行支撑；task_get；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 45：普通入口注册，手工任务详情已独审。 |
| <a id="mm-717"></a>MM-717 | `src/tools/task_list.ts` | `src/ruocun/tools/task_list.py` | 工具定义、注册和执行支撑；task_list；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 45：普通入口注册，运行项和含结束项查询已独审。 |
| <a id="mm-719"></a>MM-719 | `src/tools/task_output.ts` | `src/ruocun/tools/task_output.py` | 工具定义、注册和执行支撑；task_output；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 40已接入TaskOutput转录增量，见本页批次02表 |
| <a id="mm-721"></a>MM-721 | `src/tools/task_send.ts` | `src/ruocun/tools/task_send.py` | 工具定义、注册和执行支撑；task_send；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 43活跃追加和有授权的结束续跑；[代理消息独审](../ruocun-next24h/evidence/review/b04-agent-messages-review.md) |
| <a id="mm-723"></a>MM-723 | `src/tools/task_stop.ts` | `src/ruocun/tools/task_stop.py` | 工具定义、注册和执行支撑；task_stop；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 40已接入TaskStop与同一执行器取消确认，见本页批次02表 |
| <a id="mm-725"></a>MM-725 | `src/tools/task_update.ts` | `src/ruocun/tools/task_update.py` | 工具定义、注册和执行支撑；task_update；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 45：普通入口注册，手工更新及真实执行状态保护已独审。 |
| <a id="mm-726"></a>MM-726 | `src/tools/task_wait.ts` | `src/ruocun/tools/task_wait.py` | 工具定义、注册和执行支撑；task_wait；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-727"></a>MM-727 | `src/tools/todo_store.ts` | `src/ruocun/tools/todo_store.py` | 工具定义、注册和执行支撑；todo_store；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-729"></a>MM-729 | `src/tools/todo_write.ts` | `src/ruocun/tools/todo_write.py` | 工具定义、注册和执行支撑；todo_write；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-731"></a>MM-731 | `src/tools/tool_audit.ts` | `src/ruocun/tools/tool_audit.py` | 工具定义、注册和执行支撑；tool_audit；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n57/README.md) |
| <a id="mm-733"></a>MM-733 | `src/tools/tool_search.ts` | `src/ruocun/tools/tool_search.py` | 工具定义、注册和执行支撑；tool_search；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 原生deferred搜索保留；53补MCP前5可见、其余搜索激活和恢复精确工具可见性；见本页批次05表。 |
| <a id="mm-735"></a>MM-735 | `src/tools/tools_for_mode.ts` | `src/ruocun/tools/tools_for_mode.py` | 工具定义、注册和执行支撑；tools_for_mode；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 当前原生模式/规划工具已实现并独审；API裁剪和loop硬门模块通过，普通入口待最终验；MCP未完成 |
| <a id="mm-736"></a>MM-736 | `src/tools/types.ts` | `src/ruocun/tools/types.py` | 工具定义、注册和执行支撑；types；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 当前前台类型与图片/审批/模式/搜索接缝已实现并独审；其它高级字段仍后置；[共享证据](../ruocun-next20h/evidence/n1-shared/README.md)；批次02增强候选见本页细分出口 |
| <a id="mm-738"></a>MM-738 | `src/tools/walk.ts` | `src/ruocun/tools/glob.py` | 工具定义、注册和执行支撑；walk；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-740"></a>MM-740 | `src/tools/web_search.ts` | `src/ruocun/tools/web_search.py` | 工具定义、注册和执行支撑；web_search；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 23本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-websearch-review.md) |
| <a id="mm-742"></a>MM-742 | `src/tools/write_file.ts` | `src/ruocun/tools/write_file.py` | 工具定义、注册和执行支撑；write_file；C4 | S：Python 对应，接口/行为保留；依赖允许替换 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-744"></a>MM-744 | `src/tui/Welcome.tsx` | `src/ruocun/tui/welcome.py` | 终端状态、输入与输出适配；Welcome；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-745"></a>MM-745 | `src/tui/app/AgentTasksPanel.tsx` | `src/ruocun/tui/app/agent_tasks_panel.py` | 终端状态、输入与输出适配；AgentTasksPanel；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 67：受控输入owner的只读代理面板通过，真实终端见批次证据。 |
| <a id="mm-747"></a>MM-747 | `src/tui/app/App.tsx` | `src/ruocun/tui/app/app.py` | 终端状态、输入与输出适配；App；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 18文本输入接缝已集成，真实WT五项及退出已核；完整渲染/IME/图片按后票；批次02增强候选见本页细分出口 |
| <a id="mm-749"></a>MM-749 | `src/tui/app/format.ts` | `src/ruocun/tui/app/format.py` | 终端状态、输入与输出适配；format；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-751"></a>MM-751 | `src/tui/app/run.tsx` | `src/ruocun/tui/app/run.py` | 终端状态、输入与输出适配；run；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 18文本输入接缝已集成，真实WT五项及退出已核；完整渲染/IME/图片按后票 |
| <a id="mm-753"></a>MM-753 | `src/tui/app/types.ts` | `src/ruocun/tui/app/types.py` | 终端状态、输入与输出适配；types；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 18文本输入接缝已集成，真实WT五项及退出已核；完整渲染/IME/图片按后票；批次02增强候选见本页细分出口 |
| <a id="mm-755"></a>MM-755 | `src/tui/background.ts` | `src/ruocun/tui/background.py` | 终端状态、输入与输出适配；background；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-757"></a>MM-757 | `src/tui/banner.ts` | `src/ruocun/tui/banner.py` | 终端状态、输入与输出适配；banner；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-758"></a>MM-758 | `src/tui/brand.ts` | `src/ruocun/tui/brand.py` | 终端状态、输入与输出适配；brand；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-760"></a>MM-760 | `src/tui/capabilities.ts` | `src/ruocun/tui/capabilities.py` | 终端状态、输入与输出适配；capabilities；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-762"></a>MM-762 | `src/tui/foreground_registry.ts` | `src/ruocun/tui/foreground_registry.py` | 终端状态、输入与输出适配；foreground_registry；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 67：组合Shell及Agent所有权交接，按各分支记录自动与真实终端结果。 |
| <a id="mm-763"></a>MM-763 | `src/tui/imagePaste.ts` | `src/ruocun/tui/image_paste.py` | 终端状态、输入与输出适配；imagePaste；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-765"></a>MM-765 | `src/tui/markdown.ts` | `src/ruocun/tui/markdown.py` | 终端状态、输入与输出适配；markdown；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-767"></a>MM-767 | `src/tui/mascot.ts` | `src/ruocun/tui/mascot.py` | 终端状态、输入与输出适配；mascot；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-768"></a>MM-768 | `src/tui/mascot_frames.ts` | `src/ruocun/tui/mascot_frames.py` | 终端状态、输入与输出适配；mascot_frames；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 最终包资源与 77 自动出口已验，真实终端体验待最终批次。外部 PNG 与独立授权状态见[材料记录](../../docs/release/batch-09.md#第三方组件与终端资源) |
| <a id="mm-770"></a>MM-770 | `src/tui/maxim.ts` | `src/ruocun/tui/maxim.py` | 终端状态、输入与输出适配；maxim；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-772"></a>MM-772 | `src/tui/notifier.ts` | `src/ruocun/tui/notifier.py` | 终端状态、输入与输出适配；notifier；C5 | S：W6保留终端注意提示/安全标题，移出桌面通知发送与窗口实现 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-774"></a>MM-774 | `src/tui/onboarding/Onboarding.tsx` | `src/ruocun/tui/onboarding/onboarding.py` | 终端状态、输入与输出适配；Onboarding；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 未开始；产品证据无 |
| <a id="mm-776"></a>MM-776 | `src/tui/onboarding/Select.tsx` | `src/ruocun/tui/onboarding/select.py` | 终端状态、输入与输出适配；Select；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-777"></a>MM-777 | `src/tui/onboarding/run.tsx` | `src/ruocun/tui/onboarding/run.py` | 终端状态、输入与输出适配；run；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 未开始；产品证据无 |
| <a id="mm-779"></a>MM-779 | `src/tui/onboarding/steps/KeyStep.tsx` | `src/ruocun/tui/onboarding/steps/key_step.py` | 终端状态、输入与输出适配；KeyStep；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 未开始；产品证据无 |
| <a id="mm-780"></a>MM-780 | `src/tui/onboarding/steps/LanguageStep.tsx` | `src/ruocun/tui/onboarding/steps/language_step.py` | 终端状态、输入与输出适配；LanguageStep；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 未开始；产品证据无 |
| <a id="mm-781"></a>MM-781 | `src/tui/onboarding/steps/ProviderStep.tsx` | `src/ruocun/tui/onboarding/steps/provider_step.py` | 终端状态、输入与输出适配；ProviderStep；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 未开始；产品证据无 |
| <a id="mm-783"></a>MM-783 | `src/tui/onboarding/steps/TrustStep.tsx` | `src/ruocun/tui/onboarding/steps/trust_step.py` | 终端状态、输入与输出适配；TrustStep；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 未开始；产品证据无 |
| <a id="mm-786"></a>MM-786 | `src/tui/render.ts` | `src/ruocun/tui/render.py` | 终端状态、输入与输出适配；render；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-788"></a>MM-788 | `src/tui/spinner_words.ts` | `src/ruocun/tui/spinner_words.py` | 终端状态、输入与输出适配；spinner_words；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-790"></a>MM-790 | `src/tui/tab_attention.ts` | `src/ruocun/tui/tab_attention.py` | 终端状态、输入与输出适配；tab_attention；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-792"></a>MM-792 | `src/tui/taiji.ts` | `src/ruocun/tui/taiji.py` | 终端状态、输入与输出适配；taiji；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-794"></a>MM-794 | `src/tui/terminal_reports.ts` | `src/ruocun/tui/terminal_reports.py` | 终端状态、输入与输出适配；terminal_reports；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 18文本输入接缝已集成，真实WT五项及退出已核；完整渲染/IME/图片按后票；批次02增强候选见本页细分出口 |
| <a id="mm-796"></a>MM-796 | `src/tui/theme.ts` | `src/ruocun/tui/theme.py` | 终端状态、输入与输出适配；theme；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-797"></a>MM-797 | `src/tui/tips.ts` | `src/ruocun/tui/tips.py` | 终端状态、输入与输出适配；tips；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 批次02候选已落地；实际范围与证据见本页批次02表，整票/实机仍单列 |
| <a id="mm-798"></a>MM-798 | `src/tui/wakelock.ts` | `src/ruocun/tui/wakelock.py` | 终端状态、输入与输出适配；wakelock；C5 | S：W5不补Windows防休眠锁，准确呈现无保证；来源其它平台路由/资源语义保留未验 | UI | 批次07本路径技术与独审通过。[证据](../ruocun-next24h/evidence/batch-07/n62/README.md) |
| <a id="mm-800"></a>MM-800 | `src/tui/width.ts` | `src/ruocun/tui/width.py` | 终端状态、输入与输出适配；width；C5 | S：Python 对应，接口/行为保留；依赖允许替换 | UI | 18文本输入接缝已集成，真实WT五项及退出已核；完整渲染/IME/图片按后票；批次02增强候选见本页细分出口 |
| <a id="mm-801"></a>MM-801 | `src/version.ts` | `src/ruocun/version.py` | 产品版本标识；C0/C7 | S：RuoCun自身版本单源，distribution/CLI一致 | PKG | RuoCun 0.1.0.dev0 固定候选的包元数据、仓外 CLI 版本与产品源码一致。[发布记录](../../docs/release/batch-09.md) |

## B · 既有测试（215）

| ID | 原路径 | 拟目标/保留位置 | 职责/关系 | 处理/允许差异 | 关联案例族 | 状态/证据 |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="mm-117"></a>MM-117 | `evals/memory/extract.test.ts` | `tests/evals/memory/test_extract.py` | 来源测试/评估断言；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | TEST | 未开始；产品证据无 |
| <a id="mm-190"></a>MM-190 | `evals/memory/injection_ab.test.ts` | `tests/evals/memory/test_injection_ab.py` | 来源测试/评估断言；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | TEST | 未开始；产品证据无 |
| <a id="mm-192"></a>MM-192 | `evals/memory/lib/creds.test.ts` | `tests/evals/memory/lib/test_creds.py` | 来源测试/评估断言；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | TEST | 未开始；产品证据无 |
| <a id="mm-194"></a>MM-194 | `evals/memory/lib/judge.test.ts` | `tests/evals/memory/lib/test_judge.py` | 来源测试/评估断言；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | TEST | 未开始；产品证据无 |
| <a id="mm-196"></a>MM-196 | `evals/memory/lib/metrics.test.ts` | `tests/evals/memory/lib/test_metrics.py` | 来源测试/评估断言；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | TEST | 未开始；产品证据无 |
| <a id="mm-198"></a>MM-198 | `evals/memory/lib/redact.test.ts` | `tests/evals/memory/lib/test_redact.py` | 来源测试/评估断言；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | TEST | 未开始；产品证据无 |
| <a id="mm-200"></a>MM-200 | `evals/memory/lib/transcript.test.ts` | `tests/evals/memory/lib/test_transcript.py` | 来源测试/评估断言；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | TEST | 未开始；产品证据无 |
| <a id="mm-202"></a>MM-202 | `evals/memory/lib/types.test.ts` | `tests/evals/memory/lib/test_types.py` | 来源测试/评估断言；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | TEST | 未开始；产品证据无 |
| <a id="mm-204"></a>MM-204 | `evals/memory/recall.test.ts` | `tests/evals/memory/test_recall.py` | 来源测试/评估断言；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | TEST | 未开始；产品证据无 |
| <a id="mm-206"></a>MM-206 | `evals/memory/report.test.ts` | `tests/evals/memory/test_report.py` | 来源测试/评估断言；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | TEST | 未开始；产品证据无 |
| <a id="mm-223"></a>MM-223 | `evals/reflect/grade.test.ts` | `tests/evals/reflect/test_grade.py` | 来源测试/评估断言；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | TEST | 未开始；产品证据无 |
| <a id="mm-230"></a>MM-230 | `evals/score.test.mjs` | `tests/evals/test_score.py` | 来源测试/评估断言；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | TEST | 未开始；产品证据无 |
| <a id="mm-365"></a>MM-365 | `src/agent/agent_defs.test.ts` | `tests/src/agent/test_agent_defs.py` | 运行、调度、后台与子代理；agent_defs.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-367"></a>MM-367 | `src/agent/agent_handoff.test.ts` | `tests/src/agent/test_agent_handoff.py` | 运行、调度、后台与子代理；agent_handoff.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-369"></a>MM-369 | `src/agent/agent_hooks.test.ts` | `tests/src/agent/test_agent_hooks.py` | 运行、调度、后台与子代理；agent_hooks.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-371"></a>MM-371 | `src/agent/agent_lifecycle.test.ts` | `tests/src/agent/test_agent_lifecycle.py` | 运行、调度、后台与子代理；agent_lifecycle.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-373"></a>MM-373 | `src/agent/agent_memory.test.ts` | `tests/src/agent/test_agent_memory.py` | 运行、调度、后台与子代理；agent_memory.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-375"></a>MM-375 | `src/agent/agent_prompt.test.ts` | `tests/src/agent/test_agent_prompt.py` | 运行、调度、后台与子代理；agent_prompt.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-377"></a>MM-377 | `src/agent/agent_summary.test.ts` | `tests/src/agent/test_agent_summary.py` | 运行、调度、后台与子代理；agent_summary.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-379"></a>MM-379 | `src/agent/agent_tools.test.ts` | `tests/src/agent/test_agent_tools.py` | 运行、调度、后台与子代理；agent_tools.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-382"></a>MM-382 | `src/agent/background_runtime.test.ts` | `tests/src/agent/test_background_runtime.py` | 运行、调度、后台与子代理；background_runtime.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-386"></a>MM-386 | `src/agent/background_wait.integration.test.ts` | `tests/src/agent/test_background_wait.integration.py` | 运行、调度、后台与子代理；background_wait.integration.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-387"></a>MM-387 | `src/agent/bundled_agents.test.ts` | `tests/src/agent/test_bundled_agents.py` | 运行、调度、后台与子代理；bundled_agents.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-389"></a>MM-389 | `src/agent/cache_audit_integration.test.ts` | `tests/src/agent/test_cache_audit_integration.py` | 运行、调度、后台与子代理；cache_audit_integration.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-390"></a>MM-390 | `src/agent/cache_prefix.test.ts` | `tests/src/agent/test_cache_prefix.py` | 运行、调度、后台与子代理；cache_prefix.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-391"></a>MM-391 | `src/agent/cleanup.test.ts` | `tests/test_b05_sessions.py` | 运行、调度、后台与子代理；cleanup.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 26按来源语义迁移受控清理/保留子案例；SQLite封存与工作树保护已独审，具体范围见本页批次05表。 |
| <a id="mm-393"></a>MM-393 | `src/agent/compact.test.ts` | `tests/src/agent/test_compact.py` | 运行、调度、后台与子代理；compact.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-395"></a>MM-395 | `src/agent/deck_bridge.test.ts` | `tests/src/agent/test_deck_bridge.py` | 运行、调度、后台与子代理；deck_bridge.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-397"></a>MM-397 | `src/agent/deck_cli.integration.test.ts` | `tests/src/agent/test_deck_cli.integration.py` | 运行、调度、后台与子代理；deck_cli.integration.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-398"></a>MM-398 | `src/agent/deck_messages.test.ts` | `tests/src/agent/test_deck_messages.py` | 运行、调度、后台与子代理；deck_messages.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-400"></a>MM-400 | `src/agent/fork_agent.test.ts` | `tests/src/agent/test_fork_agent.py` | 运行、调度、后台与子代理；fork_agent.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-402"></a>MM-402 | `src/agent/longtask_eval.test.ts` | `tests/src/agent/test_longtask_eval.py` | 运行、调度、后台与子代理；longtask_eval.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-403"></a>MM-403 | `src/agent/loop.test.ts` | `tests/test_mvp_loop.py` | 运行、调度、后台与子代理；loop.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 首版前台子集已实现；失败屏障已回修；r2全量601项及独审通过；体验pending；[首版证据](../ruocun-mvp/evidence/m03/README.md)；其余后置 |
| <a id="mm-405"></a>MM-405 | `src/agent/loop_advisor.test.ts` | `tests/src/agent/test_loop_advisor.py` | 运行、调度、后台与子代理；loop_advisor.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-406"></a>MM-406 | `src/agent/loop_durable.test.ts` | `tests/src/agent/test_loop_durable.py` | 运行、调度、后台与子代理；loop_durable.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-407"></a>MM-407 | `src/agent/reflect_cadence.test.ts` | `tests/src/agent/test_reflect_cadence.py` | 运行、调度、后台与子代理；reflect_cadence.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-409"></a>MM-409 | `src/agent/reflect_persist.test.ts` | `tests/src/agent/test_reflect_persist.py` | 运行、调度、后台与子代理；reflect_persist.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-411"></a>MM-411 | `src/agent/reflect_pipeline.test.ts` | `tests/src/agent/test_reflect_pipeline.py` | 运行、调度、后台与子代理；reflect_pipeline.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-412"></a>MM-412 | `src/agent/reflect_prompts.test.ts` | `tests/src/agent/test_reflect_prompts.py` | 运行、调度、后台与子代理；reflect_prompts.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-414"></a>MM-414 | `src/agent/reflect_result.test.ts` | `tests/src/agent/test_reflect_result.py` | 运行、调度、后台与子代理；reflect_result.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-416"></a>MM-416 | `src/agent/resume_agent.test.ts` | `tests/src/agent/test_resume_agent.py` | 运行、调度、后台与子代理；resume_agent.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-418"></a>MM-418 | `src/agent/resume_durable.test.ts` | `tests/src/agent/test_resume_durable.py` | 运行、调度、后台与子代理；resume_durable.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-419"></a>MM-419 | `src/agent/runAgent.test.ts` | `tests/src/agent/test_run_agent.py` | 运行、调度、后台与子代理；runAgent.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-421"></a>MM-421 | `src/agent/session_scheduler.test.ts` | `tests/test_n1_session_scheduler.py` | 运行、调度、后台与子代理；session_scheduler.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 已迁移前台适用来源/必要R2断言并独审；后台等待原案例留后继；普通入口待验 |
| <a id="mm-423"></a>MM-423 | `src/agent/tasks.test.ts` | `tests/src/agent/test_tasks.py` | 运行、调度、后台与子代理；tasks.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-425"></a>MM-425 | `src/agent/turn_budget.test.ts` | `tests/src/agent/test_turn_budget.py` | 运行、调度、后台与子代理；turn_budget.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-427"></a>MM-427 | `src/agent/turn_health.test.ts` | `tests/src/agent/test_turn_health.py` | 运行、调度、后台与子代理；turn_health.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-429"></a>MM-429 | `src/agent/unified_reflect.test.ts` | `tests/src/agent/test_unified_reflect.py` | 运行、调度、后台与子代理；unified_reflect.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-431"></a>MM-431 | `src/agent/worktree.test.ts` | `tests/src/agent/test_worktree.py` | 运行、调度、后台与子代理；worktree.test；C2/C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | RUN / BG / REC | 未开始；产品证据无 |
| <a id="mm-433"></a>MM-433 | `src/approval/stdin_prompt.test.ts` | `tests/test_n1_permissions_approval.py` | 人工审批端口；stdin_prompt.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-435"></a>MM-435 | `src/approval/store.test.ts` | `tests/test_n1_permissions_approval.py` | 人工审批端口；store.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-438"></a>MM-438 | `src/client/client.test.ts` | `tests/src/client/test_client.py` | 模型协议与流；client.test；C2 | S：按语义迁移断言；D/R 复用数据/协议记录 | WIRE | 未开始；产品证据无 |
| <a id="mm-440"></a>MM-440 | `src/client/responses.test.ts` | `tests/src/client/test_responses.py` | 模型协议与流；responses.test；C2 | S：按语义迁移断言；D/R 复用数据/协议记录 | WIRE | 未开始；产品证据无 |
| <a id="mm-442"></a>MM-442 | `src/client/sse.test.ts` | `tests/src/client/test_sse.py` | 模型协议与流；sse.test；C2 | S：按语义迁移断言；D/R 复用数据/协议记录 | WIRE | 未开始；产品证据无 |
| <a id="mm-445"></a>MM-445 | `src/commands/builtin.test.ts` | `tests/src/commands/test_builtin.py` | 命令解析与模板；builtin.test；C1 | S：按语义迁移断言；D/R 复用数据/协议记录 | CMD | 未开始；产品证据无 |
| <a id="mm-447"></a>MM-447 | `src/commands/commands.test.ts` | `tests/src/commands/test_commands.py` | 命令解析与模板；commands.test；C1 | S：迁移保留命令的断言，单列插件和自定义模板移出分支 | CMD | 未开始；产品证据无 |
| <a id="mm-449"></a>MM-449 | `src/commands/custom.test.ts` | `tests/src/commands/test_custom.py`（历史目标） | 命令解析与模板；custom.test；C1 | 本轮范围移出（37） | CMD | 保留来源测试；未运行 |
| <a id="mm-452"></a>MM-452 | `src/config/auth_wizard.test.ts` | `tests/src/config/test_auth_wizard.py` | 账户、凭据、信任、模型配置；auth_wizard.test；C0 | S：按语义迁移断言；D/R 复用数据/协议记录 | CFG | 未开始；产品证据无 |
| <a id="mm-454"></a>MM-454 | `src/config/credential.test.ts` | `tests/src/config/test_credential.py` | 账户、凭据、信任、模型配置；credential.test；C0 | S：按语义迁移断言；D/R 复用数据/协议记录 | CFG | 未开始；产品证据无 |
| <a id="mm-456"></a>MM-456 | `src/config/env_file.test.ts` | `tests/src/config/test_env_file.py` | 账户、凭据、信任、模型配置；env_file.test；C0 | S：按语义迁移断言；D/R 复用数据/协议记录 | CFG | 未开始；产品证据无 |
| <a id="mm-459"></a>MM-459 | `src/config/migrate_dirs.test.ts` | `tests/src/config/test_migrate_dirs.py` | 账户、凭据、信任、模型配置；migrate_dirs.test；C0 | S：按语义迁移断言；D/R 复用数据/协议记录 | CFG | 未开始；产品证据无 |
| <a id="mm-461"></a>MM-461 | `src/config/model_selection.test.ts` | `tests/src/config/test_model_selection.py` | 账户、凭据、信任、模型配置；model_selection.test；C0 | S：按语义迁移断言；D/R 复用数据/协议记录 | CFG | 未开始；产品证据无 |
| <a id="mm-463"></a>MM-463 | `src/config/profiles.test.ts` | `tests/src/config/test_profiles.py` | 账户、凭据、信任、模型配置；profiles.test；C0 | S：按语义迁移断言；D/R 复用数据/协议记录 | CFG | 未开始；产品证据无 |
| <a id="mm-465"></a>MM-465 | `src/config/profiles_store.test.ts` | `tests/src/config/test_profiles_store.py` | 账户、凭据、信任、模型配置；profiles_store.test；C0 | S：按语义迁移断言；D/R 复用数据/协议记录 | CFG | 未开始；产品证据无 |
| <a id="mm-467"></a>MM-467 | `src/config/trust.test.ts` | `tests/test_n1_permissions_trust.py` | 账户、凭据、信任、模型配置；trust.test；C0 | S：按语义迁移断言；D/R 复用数据/协议记录 | CFG | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-469"></a>MM-469 | `src/config/update_check.test.ts` | `tests/src/config/test_update_check.py` | 账户、凭据、信任、模型配置；update_check.test；C0 | S：按语义迁移断言；D/R 复用数据/协议记录 | CFG | 未开始；产品证据无 |
| <a id="mm-471"></a>MM-471 | `src/config/validate_key.test.ts` | `tests/src/config/test_validate_key.py` | 账户、凭据、信任、模型配置；validate_key.test；C0 | S：按语义迁移断言；D/R 复用数据/协议记录 | CFG | 未开始；产品证据无 |
| <a id="mm-474"></a>MM-474 | `src/env_snapshot.test.ts` | `tests/src/test_env_snapshot.py` | 工程支撑；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | PKG | 未开始；产品证据无 |
| <a id="mm-476"></a>MM-476 | `src/hooks/hooks.test.ts` | `tests/src/hooks/test_hooks.py` | Hook 发现、匹配与运行；hooks.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 未开始；产品证据无 |
| <a id="mm-478"></a>MM-478 | `src/hooks/integration.test.ts` | `tests/src/hooks/test_integration.py` | Hook 发现、匹配与运行；integration.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 未开始；产品证据无 |
| <a id="mm-479"></a>MM-479 | `src/i18n/i18n.test.ts` | `tests/src/i18n/test_i18n.py` | 中英文与语言状态；i18n.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-484"></a>MM-484 | `src/lsp/client.test.ts` | `tests/test_b06_lsp.py`、`.scratch/ruocun-next24h/evidence/n55-real-server/exercise.py` | 语言服务器协议；client.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 55本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-lsp-review.md) |
| <a id="mm-486"></a>MM-486 | `src/lsp/config.test.ts` | `tests/test_b06_lsp.py` | 语言服务器协议；config.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 55本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-lsp-review.md) |
| <a id="mm-488"></a>MM-488 | `src/lsp/manager.test.ts` | `tests/test_b06_lsp.py` | 语言服务器协议；manager.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 55本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-lsp-review.md) |
| <a id="mm-492"></a>MM-492 | `src/mcp/mcp.connect.test.ts` | `tests/test_n51_mcp.py`、`tests/test_n53_mcp_caps.py`、`tests/test_n54_mcp_recovery.py` | MCP 扩展与生命周期；mcp.connect.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 51/53/54按来源语义迁移连接、能力及副作用断线子案例；已独审，具体范围见本页批次05表，不声称源文件全部排列通过。 |
| <a id="mm-493"></a>MM-493 | `src/mcp/mcp.http.test.ts` | `tests/test_n52_mcp_http.py` | MCP 扩展与生命周期；mcp.http.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 52按来源及固定SDK差分迁移HTTP/SSE子案例，4项独审通过；具体范围见本页批次05表。 |
| <a id="mm-494"></a>MM-494 | `src/mcp/mcp.manager.test.ts` | `tests/test_n51_mcp.py`、`tests/test_n53_mcp_caps.py`、`tests/test_n54_mcp_recovery.py` | MCP 扩展与生命周期；mcp.manager.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 51/53/54按来源语义迁移manager子案例及ADR-0003差异；具体范围见本页批次05表，不声称原透明重放语义通过。 |
| <a id="mm-495"></a>MM-495 | `src/mcp/mcp.test.ts` | `tests/test_n51_mcp.py`、`tests/test_n53_mcp_caps.py` | MCP 扩展与生命周期；mcp.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 51/53按来源语义迁移配置和能力子案例；具体范围见本页批次05表，不据此标整个来源测试文件通过。 |
| <a id="mm-497"></a>MM-497 | `src/memory/audit.test.ts` | `tests/src/memory/test_audit.py` | 长期记忆与上下文注入；audit.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MEM | 未开始；产品证据无 |
| <a id="mm-499"></a>MM-499 | `src/memory/consolidate.test.ts` | `tests/src/memory/test_consolidate.py` | 长期记忆与上下文注入；consolidate.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MEM | 未开始；产品证据无 |
| <a id="mm-501"></a>MM-501 | `src/memory/distill.test.ts` | `tests/src/memory/test_distill.py` | 长期记忆与上下文注入；distill.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MEM | 未开始；产品证据无 |
| <a id="mm-503"></a>MM-503 | `src/memory/frontmatter.test.ts` | `tests/src/memory/test_frontmatter.py` | 长期记忆与上下文注入；frontmatter.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MEM | 未开始；产品证据无 |
| <a id="mm-505"></a>MM-505 | `src/memory/gc.test.ts` | `tests/src/memory/test_gc.py` | 长期记忆与上下文注入；gc.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MEM | 未开始；产品证据无 |
| <a id="mm-507"></a>MM-507 | `src/memory/hash.test.ts` | `tests/src/memory/test_hash.py` | 长期记忆与上下文注入；hash.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MEM | 未开始；产品证据无 |
| <a id="mm-509"></a>MM-509 | `src/memory/inject.test.ts` | `tests/src/memory/test_inject.py` | 长期记忆与上下文注入；inject.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MEM | 未开始；产品证据无 |
| <a id="mm-511"></a>MM-511 | `src/memory/memory_audit.test.ts` | `tests/src/memory/test_memory_audit.py` | 长期记忆与上下文注入；memory_audit.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MEM | 未开始；产品证据无 |
| <a id="mm-513"></a>MM-513 | `src/memory/store.test.ts` | `tests/src/memory/test_store.py` | 长期记忆与上下文注入；store.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MEM | 未开始；产品证据无 |
| <a id="mm-515"></a>MM-515 | `src/memory/types.test.ts` | `tests/src/memory/test_types.py` | 长期记忆与上下文注入；types.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MEM | 未开始；产品证据无 |
| <a id="mm-517"></a>MM-517 | `src/memory/validate.test.ts` | `tests/src/memory/test_validate.py` | 长期记忆与上下文注入；validate.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MEM | 未开始；产品证据无 |
| <a id="mm-519"></a>MM-519 | `src/obs/attrs.test.ts` | `tests/src/obs/test_attrs.py` | 观测与审计包装；attrs.test；C2 | S：按语义迁移断言；D/R 复用数据/协议记录 | OBS | 未开始；产品证据无 |
| <a id="mm-521"></a>MM-521 | `src/obs/backend.test.ts` | `tests/src/obs/test_backend.py` | 观测与审计包装；backend.test；C2 | S：按语义迁移断言；D/R 复用数据/协议记录 | OBS | 未开始；产品证据无 |
| <a id="mm-524"></a>MM-524 | `src/obs/init.test.ts` | `tests/src/obs/test_init.py` | 观测与审计包装；init.test；C2 | S：按语义迁移断言；D/R 复用数据/协议记录 | OBS | 未开始；产品证据无 |
| <a id="mm-526"></a>MM-526 | `src/obs/wrap.test.ts` | `tests/src/obs/test_wrap.py` | 观测与审计包装；wrap.test；C2 | S：按语义迁移断言；D/R 复用数据/协议记录 | OBS | 未开始；产品证据无 |
| <a id="mm-530"></a>MM-530 | `src/permissions/bash/bash_ast.test.ts` | `tests/test_n1_permissions_bash_ast.py` | 分层规则、安全与权限门；bash_ast.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-534"></a>MM-534 | `src/permissions/bash_preprocess.test.ts` | `tests/test_n1_permissions_safety.py` | 分层规则、安全与权限门；bash_preprocess.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-536"></a>MM-536 | `src/permissions/bash_safety.test.ts` | `tests/test_n1_permissions_safety.py` | 分层规则、安全与权限门；bash_safety.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-538"></a>MM-538 | `src/permissions/classifier.test.ts` | `tests/src/permissions/test_classifier.py` | 分层规则、安全与权限门；classifier.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 未开始；产品证据无 |
| <a id="mm-540"></a>MM-540 | `src/permissions/classifier_model.test.ts` | `tests/src/permissions/test_classifier_model.py` | 分层规则、安全与权限门；classifier_model.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 未开始；产品证据无 |
| <a id="mm-542"></a>MM-542 | `src/permissions/dangerous_patterns.test.ts` | `tests/test_n1_permissions_safety.py` | 分层规则、安全与权限门；dangerous_patterns.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-544"></a>MM-544 | `src/permissions/engine.test.ts` | `tests/test_n1_permissions_engine.py` | 分层规则、安全与权限门；engine.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-546"></a>MM-546 | `src/permissions/gate.test.ts` | `tests/test_n1_permissions_gate.py` | 分层规则、安全与权限门；gate.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-548"></a>MM-548 | `src/permissions/identity.test.ts` | `tests/test_n1_permissions_identity.py` | 分层规则、安全与权限门；identity.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-550"></a>MM-550 | `src/permissions/integration.test.ts` | `tests/src/permissions/test_integration.py` | 分层规则、安全与权限门；integration.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 未开始；产品证据无 |
| <a id="mm-551"></a>MM-551 | `src/permissions/perm_audit.test.ts` | `tests/src/permissions/test_perm_audit.py` | 分层规则、安全与权限门；perm_audit.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 未开始；产品证据无 |
| <a id="mm-553"></a>MM-553 | `src/permissions/rules.test.ts` | `tests/test_n1_permissions_rules.py` | 分层规则、安全与权限门；rules.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-555"></a>MM-555 | `src/permissions/sanitize.test.ts` | `tests/src/permissions/test_sanitize.py` | 分层规则、安全与权限门；sanitize.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 未开始；产品证据无 |
| <a id="mm-557"></a>MM-557 | `src/permissions/secrets.test.ts` | `tests/src/permissions/test_secrets.py` | 分层规则、安全与权限门；secrets.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 未开始；产品证据无 |
| <a id="mm-559"></a>MM-559 | `src/permissions/settings.test.ts` | `tests/test_n1_permissions_settings.py` | 分层规则、安全与权限门；settings.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | PERM | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-561"></a>MM-561 | `src/plugins.test.ts` | `tests/src/test_plugins.py`（历史目标） | 工程支撑；C7 | 本轮范围移出（50） | PKG | 保留来源测试；未运行 |
| <a id="mm-563"></a>MM-563 | `src/project_doc.test.ts` | `tests/src/test_project_doc.py` | 工程支撑；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | PKG | 未开始；产品证据无 |
| <a id="mm-565"></a>MM-565 | `src/prompt/system_prompt.test.ts` | `tests/src/prompt/test_system_prompt.py` | 系统提示模板；system_prompt.test；C0/C2 | S：按语义迁移断言；D/R 复用数据/协议记录 | PROMPT | 未开始；产品证据无 |
| <a id="mm-567"></a>MM-567 | `src/repl.test.ts` | `tests/src/test_repl.py` | 工程支撑；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | PKG | 未开始；产品证据无 |
| <a id="mm-569"></a>MM-569 | `src/repomap/extract.test.ts` | `tests/test_b06_repomap.py` | 代码图与预算裁剪；extract.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MAP | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-571"></a>MM-571 | `src/repomap/graph.test.ts` | `tests/test_b06_repomap.py` | 代码图与预算裁剪；graph.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MAP | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-573"></a>MM-573 | `src/repomap/index.test.ts` | `tests/test_b06_repomap.py` | 代码图与预算裁剪；index.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MAP | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-577"></a>MM-577 | `src/repomap/render.test.ts` | `tests/test_b06_repomap.py` | 代码图与预算裁剪；render.test；C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | MAP | 33本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-repomap-review.md) |
| <a id="mm-581"></a>MM-581 | `src/schedule.test.ts` | `tests/src/test_schedule.py` | 工程支撑；C7 | S：按语义迁移断言；D/R 复用数据/协议记录 | PKG | 未开始；产品证据无 |
| <a id="mm-583"></a>MM-583 | `src/session/audit_switch.test.ts` | `tests/src/session/test_audit_switch.py` | 会话与持久化；audit_switch.test；C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | REC | 未开始；产品证据无 |
| <a id="mm-585"></a>MM-585 | `src/session/cache_audit.test.ts` | `tests/src/session/test_cache_audit.py` | 会话与持久化；cache_audit.test；C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | REC | 未开始；产品证据无 |
| <a id="mm-587"></a>MM-587 | `src/session/checkpoint.test.ts` | `tests/src/session/test_checkpoint.py` | 会话与持久化；checkpoint.test；C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | REC | 未开始；产品证据无 |
| <a id="mm-589"></a>MM-589 | `src/session/cost.test.ts` | `tests/test_context_cost.py` | 会话与持久化；cost.test；C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | REC | 来源9项语义迁移并独立通过；[逐项来源/结果](evidence/28-context/session-cost/README.md) |
| <a id="mm-592"></a>MM-592 | `src/session/durable_store.test.ts` | `tests/src/session/test_durable_store.py` | 会话与持久化；durable_store.test；C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | REC | 未开始；产品证据无 |
| <a id="mm-594"></a>MM-594 | `src/session/log.test.ts` | `tests/test_b05_sessions.py` | 会话与持久化；log.test；C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | REC | 26按来源语义迁移列表/未完成筛选、分支与导出子案例，4项独审通过；07已有存储证据保留，不声称所有来源组合通过。 |
| <a id="mm-596"></a>MM-596 | `src/session/process_identity.test.ts` | `tests/src/session/test_process_identity.py` | 会话与持久化；process_identity.test；C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | REC | 未开始；产品证据无 |
| <a id="mm-599"></a>MM-599 | `src/session/session.test.ts` | `tests/test_context_session.py` | 会话与持久化；session.test；C3 | S：按语义迁移断言；D/R 复用数据/协议记录 | REC | 来源10项语义迁移并独立通过；[逐项来源/结果](evidence/28-context/session-cost/README.md) |
| <a id="mm-603"></a>MM-603 | `src/skills/adapt.test.ts` | `tests/src/skills/test_adapt.py` | 技能加载、发现、安装、适配；adapt.test；C4/C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 未开始；产品证据无 |
| <a id="mm-605"></a>MM-605 | `src/skills/bundled.test.ts` | `tests/src/skills/test_bundled.py` | 技能加载、发现、安装、适配；bundled.test；C4/C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 未开始；产品证据无 |
| <a id="mm-607"></a>MM-607 | `src/skills/convert.test.ts` | `tests/src/skills/test_convert.py` | 技能加载、发现、安装、适配；convert.test；C4/C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 未开始；产品证据无 |
| <a id="mm-609"></a>MM-609 | `src/skills/discover.test.ts` | `tests/src/skills/test_discover.py` | 技能加载、发现、安装、适配；discover.test；C4/C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 未开始；产品证据无 |
| <a id="mm-611"></a>MM-611 | `src/skills/install.test.ts` | `tests/src/skills/test_install.py` | 技能加载、发现、安装、适配；install.test；C4/C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 未开始；产品证据无 |
| <a id="mm-613"></a>MM-613 | `src/skills/skill_audit.test.ts` | `tests/src/skills/test_skill_audit.py` | 技能加载、发现、安装、适配；skill_audit.test；C4/C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 未开始；产品证据无 |
| <a id="mm-615"></a>MM-615 | `src/skills/skills.test.ts` | `tests/src/skills/test_skills.py` | 技能加载、发现、安装、适配；skills.test；C4/C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 未开始；产品证据无 |
| <a id="mm-617"></a>MM-617 | `src/skills/toggle.test.ts` | `tests/src/skills/test_toggle.py` | 技能加载、发现、安装、适配；toggle.test；C4/C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 未开始；产品证据无 |
| <a id="mm-618"></a>MM-618 | `src/skills/usage.test.ts` | `tests/src/skills/test_usage.py` | 技能加载、发现、安装、适配；usage.test；C4/C6 | S：按语义迁移断言；D/R 复用数据/协议记录 | EXT | 未开始；产品证据无 |
| <a id="mm-620"></a>MM-620 | `src/tools/agent.test.ts` | `tests/src/tools/test_agent.py` | 工具定义、注册和执行支撑；agent.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-622"></a>MM-622 | `src/tools/ask_user.test.ts` | `tests/src/tools/test_ask_user.py` | 工具定义、注册和执行支撑；ask_user.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-626"></a>MM-626 | `src/tools/diagnostics.test.ts` | `tests/src/tools/test_diagnostics.py` | 工具定义、注册和执行支撑；diagnostics.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-628"></a>MM-628 | `src/tools/diff_hunk.test.ts` | `tests/src/tools/test_diff_hunk.py` | 工具定义、注册和执行支撑；diff_hunk.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-630"></a>MM-630 | `src/tools/edit_file.test.ts` | `tests/test_mvp_edit_file.py` | 工具定义、注册和执行支撑；edit_file.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-632"></a>MM-632 | `src/tools/edit_mismatch.test.ts` | `tests/src/tools/test_edit_mismatch.py` | 工具定义、注册和执行支撑；edit_mismatch.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-634"></a>MM-634 | `src/tools/enter_worktree.test.ts` | `tests/src/tools/test_enter_worktree.py` | 工具定义、注册和执行支撑；enter_worktree.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-636"></a>MM-636 | `src/tools/exec_shell.test.ts` | `tests/src/tools/test_exec_shell.py` | 工具定义、注册和执行支撑；exec_shell.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m02-shell/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-638"></a>MM-638 | `src/tools/exec_shell_ctl.test.ts` | `tests/src/tools/test_exec_shell_ctl.py` | 工具定义、注册和执行支撑；exec_shell_ctl.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-641"></a>MM-641 | `src/tools/execute.test.ts` | `tests/test_mvp_loop.py` | 工具定义、注册和执行支撑；execute.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版前台子集已实现；失败屏障已回修；r2全量601项及独审通过；体验pending；[首版证据](../ruocun-mvp/evidence/m03/README.md)；其余后置 |
| <a id="mm-643"></a>MM-643 | `src/tools/execute_durable.test.ts` | `tests/src/tools/test_execute_durable.py` | 工具定义、注册和执行支撑；execute_durable.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-644"></a>MM-644 | `src/tools/exit_worktree.test.ts` | `tests/src/tools/test_exit_worktree.py` | 工具定义、注册和执行支撑；exit_worktree.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-646"></a>MM-646 | `src/tools/fetch_cache.test.ts` | `tests/test_n22_web_fetch.py` | 工具定义、注册和执行支撑；fetch_cache.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 22本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-webfetch-review.md) |
| <a id="mm-648"></a>MM-648 | `src/tools/fetch_extract.test.ts` | `tests/test_n22_web_fetch.py` | 工具定义、注册和执行支撑；fetch_extract.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 22本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-webfetch-review.md) |
| <a id="mm-650"></a>MM-650 | `src/tools/fetch_url.test.ts` | `tests/test_n22_web_fetch.py` | 工具定义、注册和执行支撑；fetch_url.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 22本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-webfetch-review.md) |
| <a id="mm-652"></a>MM-652 | `src/tools/file_lock.test.ts` | `tests/src/tools/test_file_lock.py` | 工具定义、注册和执行支撑；file_lock.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-654"></a>MM-654 | `src/tools/file_search.test.ts` | `tests/test_mvp_glob.py` | 工具定义、注册和执行支撑；file_search.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-656"></a>MM-656 | `src/tools/fs_atomic.test.ts` | `tests/src/tools/test_fs_atomic.py` | 工具定义、注册和执行支撑；fs_atomic.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-658"></a>MM-658 | `src/tools/glob.test.ts` | `tests/test_mvp_glob.py` | 工具定义、注册和执行支撑；glob.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-660"></a>MM-660 | `src/tools/grep_files.test.ts` | `tests/test_mvp_grep_files.py` | 工具定义、注册和执行支撑；grep_files.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-663"></a>MM-663 | `src/tools/list_dir.test.ts` | `tests/test_n2_search_tools.py` | 工具定义、注册和执行支撑；list_dir.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-665"></a>MM-665 | `src/tools/lsp.test.ts` | `tests/src/tools/test_lsp.py` | 工具定义、注册和执行支撑；lsp.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-667"></a>MM-667 | `src/tools/managed_shell.test.ts` | `tests/src/tools/test_managed_shell.py` | 工具定义、注册和执行支撑；managed_shell.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-669"></a>MM-669 | `src/tools/memory_read.test.ts` | `tests/src/tools/test_memory_read.py` | 工具定义、注册和执行支撑；memory_read.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-671"></a>MM-671 | `src/tools/memory_write.test.ts` | `tests/src/tools/test_memory_write.py` | 工具定义、注册和执行支撑；memory_write.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-673"></a>MM-673 | `src/tools/message_parent.test.ts` | `tests/src/tools/test_message_parent.py` | 工具定义、注册和执行支撑；message_parent.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-675"></a>MM-675 | `src/tools/monitor.test.ts` | `tests/test_b05_monitor.py` | 工具定义、注册和执行支撑；monitor.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 46来源输出/取消/超时语义与必要owner丢失复验已独审；实际普通CLI和进程证据见本页批次05表。 |
| <a id="mm-677"></a>MM-677 | `src/tools/notebook_edit.test.ts` | `tests/src/tools/test_notebook_edit.py`（历史目标） | 工具定义、注册和执行支撑；notebook_edit.test；C4 | 本轮范围移出（20） | TOOL | 保留来源测试；未运行 |
| <a id="mm-679"></a>MM-679 | `src/tools/notify_user.test.ts` | `tests/src/tools/test_notify_user.py` | 工具定义、注册和执行支撑；notify_user.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-681"></a>MM-681 | `src/tools/output.test.ts` | `tests/src/tools/test_output.py` | 工具定义、注册和执行支撑；output.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-683"></a>MM-683 | `src/tools/paths.test.ts` | `tests/test_mvp_paths.py` | 工具定义、注册和执行支撑；paths.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-686"></a>MM-686 | `src/tools/plan_mode.test.ts` | `tests/test_n1_permissions_plan.py` | 工具定义、注册和执行支撑；plan_mode.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-688"></a>MM-688 | `src/tools/process_manager.test.ts` | `tests/src/tools/test_process_manager.py` | 工具定义、注册和执行支撑；process_manager.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-690"></a>MM-690 | `src/tools/read_file.test.ts` | `tests/test_mvp_read_file.py` | 工具定义、注册和执行支撑；read_file.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-692"></a>MM-692 | `src/tools/registry.test.ts` | `tests/test_mvp_registry.py` | 工具定义、注册和执行支撑；registry.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-694"></a>MM-694 | `src/tools/repo_map.test.ts` | `tests/src/tools/test_repo_map.py` | 工具定义、注册和执行支撑；repo_map.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-697"></a>MM-697 | `src/tools/sandbox.test.ts` | `tests/src/tools/test_sandbox.py` | 工具定义、注册和执行支撑；sandbox.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-699"></a>MM-699 | `src/tools/schedule_tool.test.ts` | `tests/src/tools/test_schedule_tool.py` | 工具定义、注册和执行支撑；schedule_tool.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-701"></a>MM-701 | `src/tools/schema.test.ts` | `tests/test_mvp_registry.py` | 工具定义、注册和执行支撑；schema.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-706"></a>MM-706 | `src/tools/skill_install.test.ts` | `tests/src/tools/test_skill_install.py` | 工具定义、注册和执行支撑；skill_install.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-708"></a>MM-708 | `src/tools/spill.test.ts` | `tests/src/tools/test_spill.py` | 工具定义、注册和执行支撑；spill.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-710"></a>MM-710 | `src/tools/ssrf.test.ts` | `tests/test_n22_web_fetch.py` | 工具定义、注册和执行支撑；ssrf.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 22本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-webfetch-review.md) |
| <a id="mm-712"></a>MM-712 | `src/tools/task_create.test.ts` | `tests/src/tools/test_task_create.py` | 工具定义、注册和执行支撑；task_create.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-714"></a>MM-714 | `src/tools/task_get.test.ts` | `tests/src/tools/test_task_get.py` | 工具定义、注册和执行支撑；task_get.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-716"></a>MM-716 | `src/tools/task_list.test.ts` | `tests/src/tools/test_task_list.py` | 工具定义、注册和执行支撑；task_list.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-718"></a>MM-718 | `src/tools/task_output.test.ts` | `tests/src/tools/test_task_output.py` | 工具定义、注册和执行支撑；task_output.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-720"></a>MM-720 | `src/tools/task_send.test.ts` | `tests/src/tools/test_task_send.py` | 工具定义、注册和执行支撑；task_send.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-722"></a>MM-722 | `src/tools/task_stop.test.ts` | `tests/src/tools/test_task_stop.py` | 工具定义、注册和执行支撑；task_stop.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-724"></a>MM-724 | `src/tools/task_update.test.ts` | `tests/src/tools/test_task_update.py` | 工具定义、注册和执行支撑；task_update.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-728"></a>MM-728 | `src/tools/todo_write.test.ts` | `tests/test_mvp_todo_write.py` | 工具定义、注册和执行支撑；todo_write.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-730"></a>MM-730 | `src/tools/tool_audit.test.ts` | `tests/src/tools/test_tool_audit.py` | 工具定义、注册和执行支撑；tool_audit.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-732"></a>MM-732 | `src/tools/tool_search.test.ts` | `tests/src/tools/test_tool_search.py` | 工具定义、注册和执行支撑；tool_search.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 未开始；产品证据无 |
| <a id="mm-734"></a>MM-734 | `src/tools/tools_for_mode.test.ts` | `tests/test_n1_permissions_plan.py` | 工具定义、注册和执行支撑；tools_for_mode.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 本批对应来源断言已迁移并模块独审；普通入口/整票及母族未据此通过；[N1证据](../ruocun-next20h/evidence/review/README.md) |
| <a id="mm-737"></a>MM-737 | `src/tools/walk.test.ts` | `tests/test_mvp_glob.py` | 工具定义、注册和执行支撑；walk.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-739"></a>MM-739 | `src/tools/web_search.test.ts` | `tests/test_n23_web_search.py` | 工具定义、注册和执行支撑；web_search.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 23本票路径已实现，来源语义及普通入口独审通过，具体子范围见本页批次06表；[独审](../ruocun-next24h/evidence/review/b06-websearch-review.md) |
| <a id="mm-741"></a>MM-741 | `src/tools/write_file.test.ts` | `tests/test_mvp_write_file.py` | 工具定义、注册和执行支撑；write_file.test；C4 | S：按语义迁移断言；D/R 复用数据/协议记录 | TOOL | 首版子集已实现并独立复核；[来源、差异及证据](../ruocun-mvp/evidence/m01/README.md)；完整源文件其余能力未宣称通过 |
| <a id="mm-743"></a>MM-743 | `src/tui/Welcome.test.tsx` | `tests/src/tui/test_welcome.py` | 终端状态、输入与输出适配；Welcome.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-746"></a>MM-746 | `src/tui/app/App.test.tsx` | `tests/src/tui/app/test_app.py` | 终端状态、输入与输出适配；App.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-748"></a>MM-748 | `src/tui/app/format.test.ts` | `tests/src/tui/app/test_format.py` | 终端状态、输入与输出适配；format.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-750"></a>MM-750 | `src/tui/app/multi_select.test.tsx` | `tests/src/tui/app/test_multi_select.py` | 终端状态、输入与输出适配；multi_select.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-752"></a>MM-752 | `src/tui/app/tail.test.ts` | `tests/src/tui/app/test_tail.py` | 终端状态、输入与输出适配；tail.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-754"></a>MM-754 | `src/tui/background.test.ts` | `tests/src/tui/test_background.py` | 终端状态、输入与输出适配；background.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-756"></a>MM-756 | `src/tui/banner.test.ts` | `tests/src/tui/test_banner.py` | 终端状态、输入与输出适配；banner.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-759"></a>MM-759 | `src/tui/capabilities.test.ts` | `tests/src/tui/test_capabilities.py` | 终端状态、输入与输出适配；capabilities.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-761"></a>MM-761 | `src/tui/foreground_registry.test.ts` | `tests/src/tui/test_foreground_registry.py` | 终端状态、输入与输出适配；foreground_registry.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-764"></a>MM-764 | `src/tui/markdown.test.ts` | `tests/src/tui/test_markdown.py` | 终端状态、输入与输出适配；markdown.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-766"></a>MM-766 | `src/tui/mascot.test.ts` | `tests/src/tui/test_mascot.py` | 终端状态、输入与输出适配；mascot.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-769"></a>MM-769 | `src/tui/maxim.test.ts` | `tests/src/tui/test_maxim.py` | 终端状态、输入与输出适配；maxim.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-771"></a>MM-771 | `src/tui/notifier.test.ts` | `tests/src/tui/test_notifier.py` | 终端状态、输入与输出适配；notifier.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-773"></a>MM-773 | `src/tui/onboarding/Onboarding.test.tsx` | `tests/src/tui/onboarding/test_onboarding.py` | 终端状态、输入与输出适配；Onboarding.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-775"></a>MM-775 | `src/tui/onboarding/Select.test.tsx` | `tests/src/tui/onboarding/test_select.py` | 终端状态、输入与输出适配；Select.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-778"></a>MM-778 | `src/tui/onboarding/steps/KeyStep.test.tsx` | `tests/src/tui/onboarding/steps/test_key_step.py` | 终端状态、输入与输出适配；KeyStep.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-782"></a>MM-782 | `src/tui/onboarding/steps/TrustStep.test.tsx` | `tests/src/tui/onboarding/steps/test_trust_step.py` | 终端状态、输入与输出适配；TrustStep.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-784"></a>MM-784 | `src/tui/onboarding/steps/steps_select.test.tsx` | `tests/src/tui/onboarding/steps/test_steps_select.py` | 终端状态、输入与输出适配；steps_select.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-785"></a>MM-785 | `src/tui/render.test.ts` | `tests/src/tui/test_render.py` | 终端状态、输入与输出适配；render.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-787"></a>MM-787 | `src/tui/spinner_words.test.ts` | `tests/src/tui/test_spinner_words.py` | 终端状态、输入与输出适配；spinner_words.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-789"></a>MM-789 | `src/tui/tab_attention.test.ts` | `tests/src/tui/test_tab_attention.py` | 终端状态、输入与输出适配；tab_attention.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-791"></a>MM-791 | `src/tui/taiji.test.ts` | `tests/src/tui/test_taiji.py` | 终端状态、输入与输出适配；taiji.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-793"></a>MM-793 | `src/tui/terminal_reports.test.ts` | `tests/src/tui/test_terminal_reports.py` | 终端状态、输入与输出适配；terminal_reports.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-795"></a>MM-795 | `src/tui/theme.test.ts` | `tests/src/tui/test_theme.py` | 终端状态、输入与输出适配；theme.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |
| <a id="mm-799"></a>MM-799 | `src/tui/width.test.ts` | `tests/src/tui/test_width.py` | 终端状态、输入与输出适配；width.test；C5 | S：按语义迁移断言；D/R 复用数据/协议记录 | UI | 未开始；产品证据无 |

## C · 脚本（58）

| ID | 原路径 | 拟目标/保留位置 | 职责/关系 | 处理/允许差异 | 关联案例族 | 状态/证据 |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="mm-307"></a>MM-307 | `scripts/accept-cache.sh` | `evals/memory/accept.py`、`evals/memory/cache.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 73 实际缓存请求及缺数处理已验。[证据](../ruocun-next24h/evidence/batch-09/eval/n73/README.md) |
| <a id="mm-308"></a>MM-308 | `scripts/accept-memory.sh` | `evals/memory/accept.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 73 跨两持久会话实际注入和召回已验。[证据](../ruocun-next24h/evidence/batch-09/eval/n73/README.md) |
| <a id="mm-309"></a>MM-309 | `scripts/debug-distill.ts` | `scripts/debug_distill.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-310"></a>MM-310 | `scripts/demo-reflect.tape` | `docs/acceptance/demo-reflect.tape` | 验证/工程/来源材料；C7 | R/S：保留操作意图；Windows 场景改写，不直接执行 POSIX 清理命令 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-311"></a>MM-311 | `scripts/demo.en.tape` | `docs/acceptance/demo.en.tape` | 验证/工程/来源材料；C7 | R/S：保留操作意图；Windows 场景改写，不直接执行 POSIX 清理命令 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-312"></a>MM-312 | `scripts/demo.tape` | `docs/acceptance/demo.tape` | 验证/工程/来源材料；C7 | R/S：保留操作意图；Windows 场景改写，不直接执行 POSIX 清理命令 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-313"></a>MM-313 | `scripts/dump-harness-wire.ts` | `scripts/dump_harness_wire.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-314"></a>MM-314 | `scripts/generate-mascot-data.mjs` | `scripts/generate_mascot_data.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-315"></a>MM-315 | `scripts/introspect-cancel-async-tasks-taskgroup-dismissed.ts` | `scripts/introspect_cancel_async_tasks_taskgroup_dismissed.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-316"></a>MM-316 | `scripts/introspect-feal-brute-force-full-space.ts` | `scripts/introspect_feal_brute_force_full_space.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-317"></a>MM-317 | `scripts/introspect-model-extraction-relu-logits-untested-branch.ts` | `scripts/introspect_model_extraction_relu_logits_untested_branch.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-318"></a>MM-318 | `scripts/introspect-openssl-selfsigned-cert-pip-vs-stdlib.ts` | `scripts/introspect_openssl_selfsigned_cert_pip_vs_stdlib.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-319"></a>MM-319 | `scripts/introspect-write-compressor-encoder-decoder-asymmetry.ts` | `scripts/introspect_write_compressor_encoder_decoder_asymmetry.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-320"></a>MM-320 | `scripts/introspect-write-compressor-restart-without-run.ts` | `scripts/introspect_write_compressor_restart_without_run.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-321"></a>MM-321 | `scripts/preview-taiji.ts` | `scripts/preview_taiji.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-322"></a>MM-322 | `scripts/preview-welcome.ts` | `scripts/preview_welcome.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-323"></a>MM-323 | `scripts/sync-version.mjs` | `scripts/sync_version.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-324"></a>MM-324 | `scripts/verify-ars-introspect.ts` | `scripts/verify_ars_introspect.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-325"></a>MM-325 | `scripts/verify-autotune-preference.ts` | `scripts/verify_autotune_preference.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-326"></a>MM-326 | `scripts/verify-background-recovery-live.mjs` | `scripts/verify_background_recovery_live.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 本轮付费 live 未运行；76 对应离线恢复与防重放语义已验。[离线证据](../ruocun-next24h/evidence/batch-09/eval/n76/README.md) |
| <a id="mm-327"></a>MM-327 | `scripts/verify-background-recovery.ts` | `scripts/verify_background_recovery.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-328"></a>MM-328 | `scripts/verify-background-wait-live.mjs` | `scripts/verify_background_wait_live.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 本轮付费 live 未运行；76 对应离线等待与取消语义已验。[离线证据](../ruocun-next24h/evidence/batch-09/eval/n76/README.md) |
| <a id="mm-329"></a>MM-329 | `scripts/verify-background-wait.mjs` | `scripts/verify_background_wait.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-330"></a>MM-330 | `scripts/verify-cancel-async-tasks-taskgroup-replay-v2.ts` | `scripts/verify_cancel_async_tasks_taskgroup_replay_v2.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-331"></a>MM-331 | `scripts/verify-cancel-async-tasks-taskgroup-replay.ts` | `scripts/verify_cancel_async_tasks_taskgroup_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-332"></a>MM-332 | `scripts/verify-cold-start-dim.ts` | `scripts/verify_cold_start_dim.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-333"></a>MM-333 | `scripts/verify-exec-shell-no-extra-params.ts` | `scripts/verify_exec_shell_no_extra_params.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-334"></a>MM-334 | `scripts/verify-exec-shell-timeout-introspect.ts` | `scripts/verify_exec_shell_timeout_introspect.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-335"></a>MM-335 | `scripts/verify-extreme-value-probe.ts` | `scripts/verify_extreme_value_probe.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-336"></a>MM-336 | `scripts/verify-fasttext-dim-introspect.ts` | `scripts/verify_fasttext_dim_introspect.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-337"></a>MM-337 | `scripts/verify-feal-emptyretry-toolchoice-replay.ts` | `scripts/verify_feal_emptyretry_toolchoice_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-338"></a>MM-338 | `scripts/verify-feal-sufficiency-clarify-replay.ts` | `scripts/verify_feal_sufficiency_clarify_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-339"></a>MM-339 | `scripts/verify-grep-only-matching-replay.ts` | `scripts/verify_grep_only_matching_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-340"></a>MM-340 | `scripts/verify-installwindows-candidate-replay.ts` | `scripts/verify_installwindows_candidate_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-341"></a>MM-341 | `scripts/verify-installwindows-introspect.ts` | `scripts/verify_installwindows_introspect.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-342"></a>MM-342 | `scripts/verify-installwindows-qemuversion-replay.ts` | `scripts/verify_installwindows_qemuversion_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-343"></a>MM-343 | `scripts/verify-largest-eigenval-checkpoint-replay.ts` | `scripts/verify_largest_eigenval_checkpoint_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-344"></a>MM-344 | `scripts/verify-largest-eigenval-introspect.ts` | `scripts/verify_largest_eigenval_introspect.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-345"></a>MM-345 | `scripts/verify-largest-eigenval-round4-replay.ts` | `scripts/verify_largest_eigenval_round4_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-346"></a>MM-346 | `scripts/verify-largest-eigenval-tier2-replay.ts` | `scripts/verify_largest_eigenval_tier2_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-347"></a>MM-347 | `scripts/verify-memory.ts` | `scripts/verify_memory.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-348"></a>MM-348 | `scripts/verify-model-extraction-groundtruth-peek-replay.ts` | `scripts/verify_model_extraction_groundtruth_peek_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-349"></a>MM-349 | `scripts/verify-model-extraction-relu-logits-untested-branch-replay.ts` | `scripts/verify_model_extraction_relu_logits_untested_branch_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-350"></a>MM-350 | `scripts/verify-openssl-selfsigned-cert-dep-minimization-replay.ts` | `scripts/verify_openssl_selfsigned_cert_dep_minimization_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-351"></a>MM-351 | `scripts/verify-persistence-runtime.ts` | `scripts/verify_persistence_runtime.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-352"></a>MM-352 | `scripts/verify-recovery-entrypoints.mjs` | `scripts/verify_recovery_entrypoints.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-353"></a>MM-353 | `scripts/verify-reflect.ts` | `scripts/verify_reflect.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-354"></a>MM-354 | `scripts/verify-train-fasttext-autotune-introspect.ts` | `scripts/verify_train_fasttext_autotune_introspect.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-355"></a>MM-355 | `scripts/verify-train-fasttext-timeout-replay.ts` | `scripts/verify_train_fasttext_timeout_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-356"></a>MM-356 | `scripts/verify-tunemjcf-candidate-replay.ts` | `scripts/verify_tunemjcf_candidate_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-357"></a>MM-357 | `scripts/verify-tunemjcf-introspect.ts` | `scripts/verify_tunemjcf_introspect.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-358"></a>MM-358 | `scripts/verify-videoprocessing-introspect.ts` | `scripts/verify_videoprocessing_introspect.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-359"></a>MM-359 | `scripts/verify-write-compressor-hard-block-rewrite.ts` | `scripts/verify_write_compressor_hard_block_rewrite.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-360"></a>MM-360 | `scripts/verify-write-compressor-missing-dep-default-replay.ts` | `scripts/verify_write_compressor_missing_dep_default_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-361"></a>MM-361 | `scripts/verify-write-compressor-missing-dep-hard-block-replay.ts` | `scripts/verify_write_compressor_missing_dep_hard_block_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-362"></a>MM-362 | `scripts/verify-write-compressor-oracle-search-replay.ts` | `scripts/verify_write_compressor_oracle_search_replay.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-363"></a>MM-363 | `scripts/verify-writecompressor-introspect.ts` | `scripts/verify_writecompressor_introspect.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-364"></a>MM-364 | `scripts/welcome-ink.tsx` | `scripts/welcome_ink.py` | 验证/工程/来源材料；C7 | S/R/P：保留验收/评估意图；详见研究脚本分类，live 显式联网 | PKG/TEST | 未开始；产品证据无 |

## D · 评估、数据、文档、许可与发布配套（其余298）

| ID | 原路径 | 拟目标/保留位置 | 职责/关系 | 处理/允许差异 | 关联案例族 | 状态/证据 |
| --- | --- | --- | --- | --- | --- | --- |
| <a id="mm-001"></a>MM-001 | `.dao/settings.json` | `tests/fixtures/config/project_settings.json` | 验证/工程/来源材料；C7 | D/R：来源项目设置仅作受控fixture，不照抄为RuoCun权限默认值 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-002"></a>MM-002 | `.editorconfig` | `.editorconfig` | 验证/工程/来源材料；C7 | 按Python工程适配；保留正式.scratch记录与实验缓存的版本边界 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-003"></a>MM-003 | `.github/ISSUE_TEMPLATE/bug_report.yml` | `.github/ISSUE_TEMPLATE/bug_report.yml` | 验证/工程/来源材料；C7 | S：Python/Windows 本机构建与验收任务；保留已有贡献模板意图 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-004"></a>MM-004 | `.github/ISSUE_TEMPLATE/config.yml` | `.github/ISSUE_TEMPLATE/config.yml` | 验证/工程/来源材料；C7 | S：Python/Windows 本机构建与验收任务；保留已有贡献模板意图 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-005"></a>MM-005 | `.github/ISSUE_TEMPLATE/feature_request.yml` | `.github/ISSUE_TEMPLATE/feature_request.yml` | 验证/工程/来源材料；C7 | S：Python/Windows 本机构建与验收任务；保留已有贡献模板意图 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-006"></a>MM-006 | `.github/PULL_REQUEST_TEMPLATE.md` | `.github/PULL_REQUEST_TEMPLATE.md` | 验证/工程/来源材料；C7 | S：Python/Windows 本机构建与验收任务；保留已有贡献模板意图 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-007"></a>MM-007 | `.github/dependabot.yml` | `.github/dependabot.yml` | 验证/工程/来源材料；C7 | S：Python/Windows 本机构建与验收任务；保留已有贡献模板意图 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-008"></a>MM-008 | `.github/workflows/ci.yml` | `.github/workflows/ci.yml` | 验证/工程/来源材料；C7 | S：Python/Windows 本机构建与验收任务；保留已有贡献模板意图 | PKG/TEST | 批次09 Windows CI 与 POSIX 源码适配入口已交付，实际状态见[82 回执](../ruocun-next24h/evidence/batch-09/n82-ci/README.md) |
| <a id="mm-009"></a>MM-009 | `.github/workflows/qemu-startup-native-probe.yml` | `.github/workflows/qemu-startup-native-probe.yml` | 验证/工程/来源材料；C7 | S：Python/Windows 本机构建与验收任务；保留已有贡献模板意图 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-010"></a>MM-010 | `.github/workflows/release.yml` | `.github/workflows/package-candidate.yml` | 验证/工程/来源材料；C7 | S：保留标准Python包的Windows构建/验收配套；D2不生成独立exe，远程发布另需授权 | PKG/TEST | 批次09标准包手动候选任务已交付，托管运行待验。[82 回执](../ruocun-next24h/evidence/batch-09/n82-ci/README.md) |
| <a id="mm-011"></a>MM-011 | `.gitignore` | `.gitignore` | 验证/工程/来源材料；C7 | 按Python工程适配；保留正式.scratch记录与实验缓存的版本边界 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-012"></a>MM-012 | `.nvmrc` | `.python-version（具体版本待07/12票）` | 验证/工程/来源材料；C7 | 替换语言环境声明，不引入Node/Bun作为核心运行依赖 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-013"></a>MM-013 | `CHANGELOG.md` | `CHANGELOG.md` | 验证/工程/来源材料；C7 | 按RuoCun实际行为/入口重建并保留来源归属；原版历史版本与成绩仅作来源参考 | PKG/TEST | 批次09已记录本地技术候选。[更新日志](../../CHANGELOG.md) |
| <a id="mm-014"></a>MM-014 | `CODE_OF_CONDUCT.md` | `CODE_OF_CONDUCT.md` | 验证/工程/来源材料；C7 | 按RuoCun实际行为/入口重建并保留来源归属；原版历史版本与成绩仅作来源参考 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-015"></a>MM-015 | `CONTRIBUTING.md` | `CONTRIBUTING.md` | 验证/工程/来源材料；C7 | 按RuoCun实际行为/入口重建并保留来源归属；原版历史版本与成绩仅作来源参考 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-016"></a>MM-016 | `DAO.md` | `tests/fixtures/project_docs/DAO.md` | 验证/工程/来源材料；C7 | D/R：项目指令兼容fixture；不替代工程AGENTS，也不自动注入产品默认提示 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-017"></a>MM-017 | `LICENSE` | `LICENSE、NOTICE（来源说明）` | 验证/工程/来源材料；C7 | 保留上游 MIT 版权及许可；第三方和资源逐项溯源 | PKG/TEST | MIT 许可原文与 NOTICE 已验包，44 项运行依赖和帧材料边界见[发布记录](../../docs/release/batch-09.md#第三方组件与终端资源) |
| <a id="mm-018"></a>MM-018 | `README.md` | `README.md` | 验证/工程/来源材料；C7 | 按RuoCun实际行为/入口重建并保留来源归属；原版历史版本与成绩仅作来源参考 | PKG/TEST | 随包项目介绍保留，当前技术候选的用户入口见[中文文档](../../README.zh-CN.md) |
| <a id="mm-019"></a>MM-019 | `README.zh-CN.md` | `README.zh-CN.md` | 验证/工程/来源材料；C7 | 按RuoCun实际行为/入口重建并保留来源归属；原版历史版本与成绩仅作来源参考 | PKG/TEST | 批次09中文使用、安装与恢复文档已交付。[用户入口](../../README.zh-CN.md) |
| <a id="mm-020"></a>MM-020 | `SECURITY.md` | `SECURITY.md` | 验证/工程/来源材料；C7 | 按RuoCun实际行为/入口重建并保留来源归属；原版历史版本与成绩仅作来源参考 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-021"></a>MM-021 | `docs/MAINTAINER-SETUP.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-022"></a>MM-022 | `docs/README.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-023"></a>MM-023 | `docs/architecture/agent-deck.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-024"></a>MM-024 | `docs/architecture/memory.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-025"></a>MM-025 | `docs/architecture/models.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-026"></a>MM-026 | `docs/architecture/overview.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-027"></a>MM-027 | `docs/architecture/unified-reflector.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-028"></a>MM-028 | `docs/assets/demo-en.gif` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-029"></a>MM-029 | `docs/assets/demo-reflect.gif` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-030"></a>MM-030 | `docs/assets/demo.gif` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-031"></a>MM-031 | `docs/case-studies/minilang-cost.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-032"></a>MM-032 | `docs/case-studies/sql-engine-long-task.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-033"></a>MM-033 | `docs/cc-subagent-architecture-trd.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-034"></a>MM-034 | `docs/design/ideas/2026-06-29-knowledge-scope-tagging.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-035"></a>MM-035 | `docs/design/plans/2026-06-05-codeds-m1-walking-skeleton.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-036"></a>MM-036 | `docs/design/plans/2026-06-05-codeds-m2-tool-loop.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-037"></a>MM-037 | `docs/design/plans/2026-06-05-codeds-m3-approval-and-write-tools.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-038"></a>MM-038 | `docs/design/plans/2026-06-05-codeds-m4-tool-completion.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-039"></a>MM-039 | `docs/design/plans/2026-06-05-codeds-m5-prompt-modes-repl.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-040"></a>MM-040 | `docs/design/plans/2026-06-06-codeds-m6-memory-p1.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-041"></a>MM-041 | `docs/design/plans/2026-06-06-codeds-m7-compaction.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-042"></a>MM-042 | `docs/design/plans/2026-06-06-codeds-m8-subagent.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-043"></a>MM-043 | `docs/design/plans/2026-06-06-codeds-m9-tui.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-044"></a>MM-044 | `docs/design/plans/2026-06-07-codeds-memory-p2.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-045"></a>MM-045 | `docs/design/plans/2026-06-07-daocode-p1-welcome.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-046"></a>MM-046 | `docs/design/plans/2026-06-16-cache-audit.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-047"></a>MM-047 | `docs/design/plans/2026-06-16-subsystem-audit.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-048"></a>MM-048 | `docs/design/plans/2026-06-17-hook-cc-parity-p1-engine.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-049"></a>MM-049 | `docs/design/plans/2026-06-17-subagent-cc-parity-A.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-050"></a>MM-050 | `docs/design/plans/2026-06-17-subagent-cc-parity-B.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-051"></a>MM-051 | `docs/design/plans/2026-06-21-challenger-trigger-enhancement.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-052"></a>MM-052 | `docs/design/plans/2026-06-28-daoist-onboarding.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-053"></a>MM-053 | `docs/design/plans/2026-06-28-i18n-display-layer.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-054"></a>MM-054 | `docs/design/plans/2026-06-28-volcengine-provider.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-055"></a>MM-055 | `docs/design/plans/2026-06-29-i18n-mainloop.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-056"></a>MM-056 | `docs/design/plans/2026-06-29-memory-correction-loop.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-057"></a>MM-057 | `docs/design/plans/2026-06-29-user-profile-extraction-and-consolidation.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-058"></a>MM-058 | `docs/design/plans/2026-06-30-memory-effectiveness-eval.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-059"></a>MM-059 | `docs/design/plans/2026-07-14-qianfan-provider.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-060"></a>MM-060 | `docs/design/plans/2026-07-18-subagent-handoff-and-streaming.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-061"></a>MM-061 | `docs/design/specs/2026-06-07-daocode-interaction-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-062"></a>MM-062 | `docs/design/specs/2026-06-16-cache-audit-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-063"></a>MM-063 | `docs/design/specs/2026-06-16-subsystem-audit-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-064"></a>MM-064 | `docs/design/specs/2026-06-17-hook-cc-parity-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-065"></a>MM-065 | `docs/design/specs/2026-06-17-subagent-cc-parity-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-066"></a>MM-066 | `docs/design/specs/2026-06-21-challenger-trigger-enhancement-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-067"></a>MM-067 | `docs/design/specs/2026-06-25-unified-reflector-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-068"></a>MM-068 | `docs/design/specs/2026-06-25-unified-reflector-verification.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-069"></a>MM-069 | `docs/design/specs/2026-06-28-daoist-onboarding-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-070"></a>MM-070 | `docs/design/specs/2026-06-28-i18n-display-layer-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-071"></a>MM-071 | `docs/design/specs/2026-06-28-volcengine-coding-plan-provider-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-072"></a>MM-072 | `docs/design/specs/2026-06-29-memory-correction-loop.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-073"></a>MM-073 | `docs/design/specs/2026-06-29-user-profile-extraction-and-consolidation.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-074"></a>MM-074 | `docs/design/specs/2026-06-30-memory-effectiveness-eval.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-075"></a>MM-075 | `docs/design/specs/2026-07-14-qianfan-coding-plan-provider-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-076"></a>MM-076 | `docs/harness/README.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-077"></a>MM-077 | `docs/harness/memory.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-078"></a>MM-078 | `docs/harness/middleware.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-079"></a>MM-079 | `docs/harness/skills.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-080"></a>MM-080 | `docs/harness/subagents.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-081"></a>MM-081 | `docs/harness/system-prompt.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-082"></a>MM-082 | `docs/harness/tools.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-083"></a>MM-083 | `docs/harness/wire/middleware.wire.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-084"></a>MM-084 | `docs/harness/wire/skills.wire.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-085"></a>MM-085 | `docs/harness/wire/subagents.wire.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-086"></a>MM-086 | `docs/harness/wire/tools.wire.json` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-087"></a>MM-087 | `docs/superpowers/plans/2026-05-27-subagent-system.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-088"></a>MM-088 | `docs/superpowers/plans/2026-07-02-laminar-observability.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-089"></a>MM-089 | `docs/superpowers/plans/2026-07-06-memory-b1-b3.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-090"></a>MM-090 | `docs/superpowers/plans/2026-07-17-multimodal-image-input.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-091"></a>MM-091 | `docs/superpowers/plans/2026-07-18-rate-limit-account-switch.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-092"></a>MM-092 | `docs/superpowers/plans/2026-07-21-foreground-task-background-hotkey.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-093"></a>MM-093 | `docs/superpowers/plans/2026-07-21-long-task-progress-awareness.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-094"></a>MM-094 | `docs/superpowers/plans/2026-07-26-env-bootstrap-enrichment.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-095"></a>MM-095 | `docs/superpowers/plans/2026-08-15-checkpoint-scoped-add.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-096"></a>MM-096 | `docs/superpowers/specs/2026-05-27-subagent-system-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-097"></a>MM-097 | `docs/superpowers/specs/2026-07-02-laminar-observability-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-098"></a>MM-098 | `docs/superpowers/specs/2026-07-17-multimodal-image-input-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-099"></a>MM-099 | `docs/superpowers/specs/2026-07-18-rate-limit-account-switch-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-100"></a>MM-100 | `docs/superpowers/specs/2026-07-21-foreground-task-background-hotkey-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-101"></a>MM-101 | `docs/superpowers/specs/2026-07-21-long-task-progress-awareness-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-102"></a>MM-102 | `docs/superpowers/specs/2026-07-26-env-bootstrap-enrichment-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-103"></a>MM-103 | `docs/superpowers/specs/2026-08-01-webfetch-smart-extract-design.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 来源资料已保存在冻结归档；面向 RuoCun 的文档/配置按行为重建 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-104"></a>MM-104 | `eslint.config.js` | `pyproject.toml、Python 质量/测试配置` | 验证/工程/来源材料；C7 | 替换工程工具；新命令已确认，待工程配置；不保留 JS 核心 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-105"></a>MM-105 | `evals/README.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-106"></a>MM-106 | `evals/docker/README.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-107"></a>MM-107 | `evals/docker/cpp.Dockerfile` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-108"></a>MM-108 | `evals/docker/java.Dockerfile` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-109"></a>MM-109 | `evals/docker/node.Dockerfile` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-110"></a>MM-110 | `evals/docker/python-ds.Dockerfile` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-111"></a>MM-111 | `evals/docker/python.Dockerfile` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-112"></a>MM-112 | `evals/horizon.mjs` | `evals/horizon.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-113"></a>MM-113 | `evals/materialize-trace.mjs` | `evals/materialize_trace.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 72冻结资产与离线闭环 |
| <a id="mm-114"></a>MM-114 | `evals/memory/.gitignore` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-115"></a>MM-115 | `evals/memory/BASELINE.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-116"></a>MM-116 | `evals/memory/README.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-118"></a>MM-118 | `evals/memory/extract.ts` | `evals/memory/extract.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 73 冻结语义离线运行和独立评分通过。[证据](../ruocun-next24h/evidence/batch-09/eval/n73/README.md) |
| <a id="mm-119"></a>MM-119 | `evals/memory/fixtures/extract/_synthetic/conversation.jsonl` | `evals/memory/fixtures/extract/_synthetic/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-120"></a>MM-120 | `evals/memory/fixtures/extract/_synthetic/gold.json` | `evals/memory/fixtures/extract/_synthetic/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-121"></a>MM-121 | `evals/memory/fixtures/extract/bubble-fyuu/conversation.jsonl` | `evals/memory/fixtures/extract/bubble-fyuu/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-122"></a>MM-122 | `evals/memory/fixtures/extract/bubble-fyuu/gold.json` | `evals/memory/fixtures/extract/bubble-fyuu/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-123"></a>MM-123 | `evals/memory/fixtures/extract/bubble-m94s/conversation.jsonl` | `evals/memory/fixtures/extract/bubble-m94s/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-124"></a>MM-124 | `evals/memory/fixtures/extract/bubble-m94s/gold.json` | `evals/memory/fixtures/extract/bubble-m94s/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-125"></a>MM-125 | `evals/memory/fixtures/extract/canvas-j98j/conversation.jsonl` | `evals/memory/fixtures/extract/canvas-j98j/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-126"></a>MM-126 | `evals/memory/fixtures/extract/canvas-j98j/gold.json` | `evals/memory/fixtures/extract/canvas-j98j/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-127"></a>MM-127 | `evals/memory/fixtures/extract/canvas-vo1k/conversation.jsonl` | `evals/memory/fixtures/extract/canvas-vo1k/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-128"></a>MM-128 | `evals/memory/fixtures/extract/canvas-vo1k/gold.json` | `evals/memory/fixtures/extract/canvas-vo1k/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-129"></a>MM-129 | `evals/memory/fixtures/extract/media-4qsj/conversation.jsonl` | `evals/memory/fixtures/extract/media-4qsj/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-130"></a>MM-130 | `evals/memory/fixtures/extract/media-4qsj/gold.json` | `evals/memory/fixtures/extract/media-4qsj/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-131"></a>MM-131 | `evals/memory/fixtures/extract/note-gyy4/conversation.jsonl` | `evals/memory/fixtures/extract/note-gyy4/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-132"></a>MM-132 | `evals/memory/fixtures/extract/note-gyy4/gold.json` | `evals/memory/fixtures/extract/note-gyy4/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-133"></a>MM-133 | `evals/memory/fixtures/extract/slide-mxk0/conversation.jsonl` | `evals/memory/fixtures/extract/slide-mxk0/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-134"></a>MM-134 | `evals/memory/fixtures/extract/slide-mxk0/gold.json` | `evals/memory/fixtures/extract/slide-mxk0/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-135"></a>MM-135 | `evals/memory/fixtures/extract/slide-yah0/conversation.jsonl` | `evals/memory/fixtures/extract/slide-yah0/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-136"></a>MM-136 | `evals/memory/fixtures/extract/slide-yah0/gold.json` | `evals/memory/fixtures/extract/slide-yah0/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-137"></a>MM-137 | `evals/memory/fixtures/recall/_synthetic/context.json` | `evals/memory/fixtures/recall/_synthetic/context.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-138"></a>MM-138 | `evals/memory/fixtures/recall/_synthetic/store/a.md` | `evals/memory/fixtures/recall/_synthetic/store/a.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-139"></a>MM-139 | `evals/memory/fixtures/recall/_synthetic/store/b.md` | `evals/memory/fixtures/recall/_synthetic/store/b.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-140"></a>MM-140 | `evals/memory/fixtures/recall/_synthetic/store/c.md` | `evals/memory/fixtures/recall/_synthetic/store/c.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-141"></a>MM-141 | `evals/memory/fixtures/recall/bubble/context.json` | `evals/memory/fixtures/recall/bubble/context.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-142"></a>MM-142 | `evals/memory/fixtures/recall/bubble/store/卡通动物角色点击游戏技术选型-swiftui-spritekit-ios-原生-目标.md` | `evals/memory/fixtures/recall/bubble/store/卡通动物角色点击游戏技术选型-swiftui-spritekit-ios-原生-目标.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-143"></a>MM-143 | `evals/memory/fixtures/recall/bubble/store/泡泡机应用项目-ipad-ios-原生应用-swiftui-spritekit-泡.md` | `evals/memory/fixtures/recall/bubble/store/泡泡机应用项目-ipad-ios-原生应用-swiftui-spritekit-泡.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-144"></a>MM-144 | `evals/memory/fixtures/recall/bubble/store/泡泡机应用项目-users-user-daoproject-game-使用.md` | `evals/memory/fixtures/recall/bubble/store/泡泡机应用项目-users-user-daoproject-game-使用.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-145"></a>MM-145 | `evals/memory/fixtures/recall/bubble/store/泡泡机应用项目已通过子代理驱动开发完成全部-9-个-task-11-11-单元测试.md` | `evals/memory/fixtures/recall/bubble/store/泡泡机应用项目已通过子代理驱动开发完成全部-9-个-task-11-11-单元测试.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-146"></a>MM-146 | `evals/memory/fixtures/recall/bubble/store/用户正在开发一个给2岁孩子玩的-ipad-益智游戏-卡通动物角色主题的点击探索游戏-.md` | `evals/memory/fixtures/recall/bubble/store/用户正在开发一个给2岁孩子玩的-ipad-益智游戏-卡通动物角色主题的点击探索游戏-.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-147"></a>MM-147 | `evals/memory/fixtures/recall/canvas/context.json` | `evals/memory/fixtures/recall/canvas/context.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-148"></a>MM-148 | `evals/memory/fixtures/recall/canvas/store/canvasapp-新增-6-种贴纸-小鸭-fluent-duck-noto.md` | `evals/memory/fixtures/recall/canvas/store/canvasapp-新增-6-种贴纸-小鸭-fluent-duck-noto.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-149"></a>MM-149 | `evals/memory/fixtures/recall/canvas/store/canvasapp-画布应用-是面向-2-岁儿童的-ipad-涂鸦-app-.md` | `evals/memory/fixtures/recall/canvas/store/canvasapp-画布应用-是面向-2-岁儿童的-ipad-涂鸦-app-.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-150"></a>MM-150 | `evals/memory/fixtures/recall/canvas/store/canvasapp-贴纸图片位于-canvasapp-resources.md` | `evals/memory/fixtures/recall/canvas/store/canvasapp-贴纸图片位于-canvasapp-resources.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-151"></a>MM-151 | `evals/memory/fixtures/recall/canvas/store/canvasapp-贴纸图片加载的坑已修复-stickermanager-r.md` | `evals/memory/fixtures/recall/canvas/store/canvasapp-贴纸图片加载的坑已修复-stickermanager-r.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-152"></a>MM-152 | `evals/memory/fixtures/recall/canvas/store/canvasapp-贴纸栏改为每个变体独立展示-每种上限-3-个-不再点击切.md` | `evals/memory/fixtures/recall/canvas/store/canvasapp-贴纸栏改为每个变体独立展示-每种上限-3-个-不再点击切.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-153"></a>MM-153 | `evals/memory/fixtures/recall/canvas/store/canvasapp-音效用-avaudioengine-程序合成-pcm-波.md` | `evals/memory/fixtures/recall/canvas/store/canvasapp-音效用-avaudioengine-程序合成-pcm-波.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-154"></a>MM-154 | `evals/memory/fixtures/recall/i18n-cross-project/context.json` | `evals/memory/fixtures/recall/i18n-cross-project/context.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-155"></a>MM-155 | `evals/memory/fixtures/recall/i18n-cross-project/store/avaudioengine-start-crash.md` | `evals/memory/fixtures/recall/i18n-cross-project/store/avaudioengine-start-crash.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-156"></a>MM-156 | `evals/memory/fixtures/recall/i18n-cross-project/store/cli-highlight-plaintext.md` | `evals/memory/fixtures/recall/i18n-cross-project/store/cli-highlight-plaintext.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-157"></a>MM-157 | `evals/memory/fixtures/recall/i18n-cross-project/store/dao-diff-render.md` | `evals/memory/fixtures/recall/i18n-cross-project/store/dao-diff-render.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-158"></a>MM-158 | `evals/memory/fixtures/recall/i18n-cross-project/store/no-ai-commit-signature.md` | `evals/memory/fixtures/recall/i18n-cross-project/store/no-ai-commit-signature.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-159"></a>MM-159 | `evals/memory/fixtures/recall/i18n-cross-project/store/spritekit-emoji-render.md` | `evals/memory/fixtures/recall/i18n-cross-project/store/spritekit-emoji-render.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-160"></a>MM-160 | `evals/memory/fixtures/recall/i18n-cross-project/store/swiftui-gesture-scrollview.md` | `evals/memory/fixtures/recall/i18n-cross-project/store/swiftui-gesture-scrollview.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-161"></a>MM-161 | `evals/memory/fixtures/recall/i18n-cross-project/store/tsx-vs-esbuild.md` | `evals/memory/fixtures/recall/i18n-cross-project/store/tsx-vs-esbuild.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-162"></a>MM-162 | `evals/memory/fixtures/recall/i18n-cross-project/store/verify-with-evidence.md` | `evals/memory/fixtures/recall/i18n-cross-project/store/verify-with-evidence.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-163"></a>MM-163 | `evals/memory/fixtures/recall/i18n-cross-project/store/xcode-clean-build.md` | `evals/memory/fixtures/recall/i18n-cross-project/store/xcode-clean-build.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-164"></a>MM-164 | `evals/memory/fixtures/recall/media/context.json` | `evals/memory/fixtures/recall/media/context.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-165"></a>MM-165 | `evals/memory/fixtures/recall/media/store/adapting-superpowers-to-dao.md` | `evals/memory/fixtures/recall/media/store/adapting-superpowers-to-dao.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-166"></a>MM-166 | `evals/memory/fixtures/recall/media/store/created-12-dao-skills.md` | `evals/memory/fixtures/recall/media/store/created-12-dao-skills.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-167"></a>MM-167 | `evals/memory/fixtures/recall/media/store/dao-builtin-debug-simplify.md` | `evals/memory/fixtures/recall/media/store/dao-builtin-debug-simplify.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-168"></a>MM-168 | `evals/memory/fixtures/recall/media/store/gitignore-excludes.md` | `evals/memory/fixtures/recall/media/store/gitignore-excludes.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-169"></a>MM-169 | `evals/memory/fixtures/recall/media/store/skill-loading-needs-exploration.md` | `evals/memory/fixtures/recall/media/store/skill-loading-needs-exploration.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-170"></a>MM-170 | `evals/memory/fixtures/recall/note/context.json` | `evals/memory/fixtures/recall/note/context.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-171"></a>MM-171 | `evals/memory/fixtures/recall/note/store/dataflow-no-debounce.md` | `evals/memory/fixtures/recall/note/store/dataflow-no-debounce.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-172"></a>MM-172 | `evals/memory/fixtures/recall/note/store/note-app-swiftui-appkit.md` | `evals/memory/fixtures/recall/note/store/note-app-swiftui-appkit.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-173"></a>MM-173 | `evals/memory/fixtures/recall/note/store/plaintext-content-storage.md` | `evals/memory/fixtures/recall/note/store/plaintext-content-storage.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-174"></a>MM-174 | `evals/memory/fixtures/recall/note/store/removed-format-command.md` | `evals/memory/fixtures/recall/note/store/removed-format-command.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-175"></a>MM-175 | `evals/memory/fixtures/recall/note/store/scenephase-force-save.md` | `evals/memory/fixtures/recall/note/store/scenephase-force-save.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-176"></a>MM-176 | `evals/memory/fixtures/recall/slide/context.json` | `evals/memory/fixtures/recall/slide/context.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-177"></a>MM-177 | `evals/memory/fixtures/recall/slide/store/ios-agent-技能发现-关键索引站和-github-仓库格局.md` | `evals/memory/fixtures/recall/slide/store/ios-agent-技能发现-关键索引站和-github-仓库格局.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-178"></a>MM-178 | `evals/memory/fixtures/recall/slide/store/slide-game-实现完成状态.md` | `evals/memory/fixtures/recall/slide/store/slide-game-实现完成状态.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-179"></a>MM-179 | `evals/memory/fixtures/recall/slide/store/slide-game-项目-2岁儿童-ipad-滑滑梯游戏.md` | `evals/memory/fixtures/recall/slide/store/slide-game-项目-2岁儿童-ipad-滑滑梯游戏.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-180"></a>MM-180 | `evals/memory/fixtures/recall/slide/store/slide-game-项目完成状态-14-commit-编译-运行验证通过.md` | `evals/memory/fixtures/recall/slide/store/slide-game-项目完成状态-14-commit-编译-运行验证通过.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-181"></a>MM-181 | `evals/memory/fixtures/recall/slide/store/stickpng-等免费png站对卡通配角图覆盖不足.md` | `evals/memory/fixtures/recall/slide/store/stickpng-等免费png站对卡通配角图覆盖不足.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-182"></a>MM-182 | `evals/memory/fixtures/recall/user-level/context.json` | `evals/memory/fixtures/recall/user-level/context.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-183"></a>MM-183 | `evals/memory/fixtures/recall/user-level/store/copyright-personal-use.md` | `evals/memory/fixtures/recall/user-level/store/copyright-personal-use.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-184"></a>MM-184 | `evals/memory/fixtures/recall/user-level/store/credentials-in-tool.md` | `evals/memory/fixtures/recall/user-level/store/credentials-in-tool.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-185"></a>MM-185 | `evals/memory/fixtures/recall/user-level/store/incremental-visual-delivery.md` | `evals/memory/fixtures/recall/user-level/store/incremental-visual-delivery.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-186"></a>MM-186 | `evals/memory/fixtures/recall/user-level/store/search-skills-before-dev.md` | `evals/memory/fixtures/recall/user-level/store/search-skills-before-dev.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-187"></a>MM-187 | `evals/memory/fixtures/recall/user-level/store/tsx-vs-esbuild.md` | `evals/memory/fixtures/recall/user-level/store/tsx-vs-esbuild.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-188"></a>MM-188 | `evals/memory/fixtures/recall/user-level/store/user-profile-kid-ipad-games.md` | `evals/memory/fixtures/recall/user-level/store/user-profile-kid-ipad-games.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-189"></a>MM-189 | `evals/memory/fixtures/recall/user-level/store/verify-with-evidence.md` | `evals/memory/fixtures/recall/user-level/store/verify-with-evidence.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-191"></a>MM-191 | `evals/memory/injection_ab.ts` | `evals/memory/injection_ab.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 73 合成注入 A/B 实际执行。[证据](../ruocun-next24h/evidence/batch-09/eval/n73/README.md) |
| <a id="mm-193"></a>MM-193 | `evals/memory/lib/creds.ts` | `evals/memory/lib/creds.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-195"></a>MM-195 | `evals/memory/lib/judge.ts` | `evals/memory/lib/judge.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-197"></a>MM-197 | `evals/memory/lib/metrics.ts` | `evals/memory/lib/metrics.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-199"></a>MM-199 | `evals/memory/lib/redact.ts` | `evals/memory/lib/redact.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-201"></a>MM-201 | `evals/memory/lib/transcript.ts` | `evals/memory/lib/transcript.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-203"></a>MM-203 | `evals/memory/lib/types.ts` | `evals/memory/lib/types.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-205"></a>MM-205 | `evals/memory/recall.ts` | `evals/memory/recall.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 73 召回离线和跨会话普通入口通过。[证据](../ruocun-next24h/evidence/batch-09/eval/n73/README.md) |
| <a id="mm-207"></a>MM-207 | `evals/memory/report.ts` | `evals/memory/report.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 73 记忆、召回和缓存的脱敏报告已验证。[证据](../ruocun-next24h/evidence/batch-09/eval/n73/README.md) |
| <a id="mm-208"></a>MM-208 | `evals/memory/run.ts` | `evals/memory/run.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 73 入口、缓存及离线边界独审通过。[证据](../ruocun-next24h/evidence/batch-09/eval/n73/README.md) |
| <a id="mm-209"></a>MM-209 | `evals/memory/tsconfig.json` | `evals/memory/tsconfig.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-210"></a>MM-210 | `evals/reflect/README.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-211"></a>MM-211 | `evals/reflect/fixtures/c1-cc-sysprompt-assertion/conversation.jsonl` | `evals/reflect/fixtures/c1-cc-sysprompt-assertion/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-212"></a>MM-212 | `evals/reflect/fixtures/c1-cc-sysprompt-assertion/gold.json` | `evals/reflect/fixtures/c1-cc-sysprompt-assertion/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-213"></a>MM-213 | `evals/reflect/fixtures/c2-mem-layer-assertion/conversation.jsonl` | `evals/reflect/fixtures/c2-mem-layer-assertion/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-214"></a>MM-214 | `evals/reflect/fixtures/c2-mem-layer-assertion/gold.json` | `evals/reflect/fixtures/c2-mem-layer-assertion/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-215"></a>MM-215 | `evals/reflect/fixtures/c3-commit-unknown-changes/conversation.jsonl` | `evals/reflect/fixtures/c3-commit-unknown-changes/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-216"></a>MM-216 | `evals/reflect/fixtures/c3-commit-unknown-changes/gold.json` | `evals/reflect/fixtures/c3-commit-unknown-changes/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-217"></a>MM-217 | `evals/reflect/fixtures/c4-i18n-continue-ontrack/conversation.jsonl` | `evals/reflect/fixtures/c4-i18n-continue-ontrack/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-218"></a>MM-218 | `evals/reflect/fixtures/c4-i18n-continue-ontrack/gold.json` | `evals/reflect/fixtures/c4-i18n-continue-ontrack/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-219"></a>MM-219 | `evals/reflect/fixtures/c5-project-status-qa-ontrack/conversation.jsonl` | `evals/reflect/fixtures/c5-project-status-qa-ontrack/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-220"></a>MM-220 | `evals/reflect/fixtures/c5-project-status-qa-ontrack/gold.json` | `evals/reflect/fixtures/c5-project-status-qa-ontrack/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-221"></a>MM-221 | `evals/reflect/fixtures/c6-verify-honest-ontrack/conversation.jsonl` | `evals/reflect/fixtures/c6-verify-honest-ontrack/conversation.jsonl` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-222"></a>MM-222 | `evals/reflect/fixtures/c6-verify-honest-ontrack/gold.json` | `evals/reflect/fixtures/c6-verify-honest-ontrack/gold.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-224"></a>MM-224 | `evals/reflect/grade.ts` | `evals/reflect/grade.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 74 来源案例的反思正控、评分及无效输出分类通过。[证据](../ruocun-next24h/evidence/batch-09/eval/n74/README.md) |
| <a id="mm-225"></a>MM-225 | `evals/reflect/run.ts` | `evals/reflect/run.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 74 本地回环评估入口及脱敏报告通过，真实模型未验。[证据](../ruocun-next24h/evidence/batch-09/eval/n74/README.md) |
| <a id="mm-226"></a>MM-226 | `evals/reflect/tsconfig.json` | `evals/reflect/tsconfig.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-227"></a>MM-227 | `evals/render-trace.mjs` | `evals/render_trace.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 72冻结资产与离线闭环 |
| <a id="mm-228"></a>MM-228 | `evals/run.mjs` | `evals/run.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 72冻结资产与离线闭环 |
| <a id="mm-229"></a>MM-229 | `evals/score.mjs` | `evals/score.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 72冻结资产与离线闭环 |
| <a id="mm-231"></a>MM-231 | `evals/swebench/.gitignore` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-232"></a>MM-232 | `evals/swebench/adapter.mjs` | `evals/swebench/adapter.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-233"></a>MM-233 | `evals/swebench/adapter_v2.mjs` | `evals/swebench/adapter_v2.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-234"></a>MM-234 | `evals/swebench/container_helper.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-235"></a>MM-235 | `evals/tasks/01-parse-query/task.json` | `evals/tasks/01-parse-query/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-236"></a>MM-236 | `evals/tasks/01-parse-query/tests/fail2pass.mjs` | `evals/tasks/01-parse-query/tests/fail2pass.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-237"></a>MM-237 | `evals/tasks/01-parse-query/tests/pass2pass.mjs` | `evals/tasks/01-parse-query/tests/pass2pass.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-238"></a>MM-238 | `evals/tasks/01-parse-query/workspace/qs.mjs` | `evals/tasks/01-parse-query/workspace/qs.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-239"></a>MM-239 | `evals/tasks/02-dedupe/task.json` | `evals/tasks/02-dedupe/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-240"></a>MM-240 | `evals/tasks/02-dedupe/tests/fail2pass.mjs` | `evals/tasks/02-dedupe/tests/fail2pass.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-241"></a>MM-241 | `evals/tasks/02-dedupe/tests/pass2pass.mjs` | `evals/tasks/02-dedupe/tests/pass2pass.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-242"></a>MM-242 | `evals/tasks/02-dedupe/workspace/dedupe.mjs` | `evals/tasks/02-dedupe/workspace/dedupe.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-243"></a>MM-243 | `evals/tasks/04-plan-blocks-write/check.mjs` | `evals/tasks/04-plan-blocks-write/check.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-244"></a>MM-244 | `evals/tasks/04-plan-blocks-write/task.json` | `evals/tasks/04-plan-blocks-write/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-245"></a>MM-245 | `evals/tasks/05-pathescape/check.mjs` | `evals/tasks/05-pathescape/check.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-246"></a>MM-246 | `evals/tasks/05-pathescape/task.json` | `evals/tasks/05-pathescape/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-247"></a>MM-247 | `evals/tasks/06-axis-limit-guard/task.json` | `evals/tasks/06-axis-limit-guard/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-248"></a>MM-248 | `evals/tasks/06-axis-limit-guard/tests/fail2pass.mjs` | `evals/tasks/06-axis-limit-guard/tests/fail2pass.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-249"></a>MM-249 | `evals/tasks/06-axis-limit-guard/tests/pass2pass.mjs` | `evals/tasks/06-axis-limit-guard/tests/pass2pass.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-250"></a>MM-250 | `evals/tasks/06-axis-limit-guard/workspace/axisConfig.mjs` | `evals/tasks/06-axis-limit-guard/workspace/axis_config.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-251"></a>MM-251 | `evals/tasks/90-oss-template/task.template.json` | `evals/tasks/90-oss-template/task.template.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-252"></a>MM-252 | `evals/tasks/L1-nodeps-toolkit/task.json` | `evals/tasks/L1-nodeps-toolkit/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-253"></a>MM-253 | `evals/tasks/L1-nodeps-toolkit/tests/arrays.mjs` | `evals/tasks/L1-nodeps-toolkit/tests/arrays.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-254"></a>MM-254 | `evals/tasks/L1-nodeps-toolkit/tests/dates.mjs` | `evals/tasks/L1-nodeps-toolkit/tests/dates.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-255"></a>MM-255 | `evals/tasks/L1-nodeps-toolkit/tests/no-deps.mjs` | `evals/tasks/L1-nodeps-toolkit/tests/no_deps.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-256"></a>MM-256 | `evals/tasks/L1-nodeps-toolkit/tests/objects.mjs` | `evals/tasks/L1-nodeps-toolkit/tests/objects.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-257"></a>MM-257 | `evals/tasks/L1-nodeps-toolkit/tests/strings.mjs` | `evals/tasks/L1-nodeps-toolkit/tests/strings.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-258"></a>MM-258 | `evals/tasks/L1-nodeps-toolkit/workspace/README.md` | `evals/tasks/L1-nodeps-toolkit/workspace/README.md` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-259"></a>MM-259 | `evals/tasks/L1-nodeps-toolkit/workspace/package.json` | `evals/tasks/L1-nodeps-toolkit/workspace/package.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-260"></a>MM-260 | `evals/tasks/L1-nodeps-toolkit/workspace/src/arrays.mjs` | `evals/tasks/L1-nodeps-toolkit/workspace/src/arrays.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-261"></a>MM-261 | `evals/tasks/L1-nodeps-toolkit/workspace/src/dates.mjs` | `evals/tasks/L1-nodeps-toolkit/workspace/src/dates.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-262"></a>MM-262 | `evals/tasks/L1-nodeps-toolkit/workspace/src/index.mjs` | `evals/tasks/L1-nodeps-toolkit/workspace/src/index.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-263"></a>MM-263 | `evals/tasks/L1-nodeps-toolkit/workspace/src/objects.mjs` | `evals/tasks/L1-nodeps-toolkit/workspace/src/objects.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-264"></a>MM-264 | `evals/tasks/L1-nodeps-toolkit/workspace/src/strings.mjs` | `evals/tasks/L1-nodeps-toolkit/workspace/src/strings.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-265"></a>MM-265 | `evals/tasks/t1-valibot-mastercard/task.json` | `evals/tasks/t1-valibot-mastercard/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-266"></a>MM-266 | `evals/tasks/t10-semver-subset-prerelease/task.json` | `evals/tasks/t10-semver-subset-prerelease/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-267"></a>MM-267 | `evals/tasks/t2-valibot-intersect-frozen/task.json` | `evals/tasks/t2-valibot-intersect-frozen/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-268"></a>MM-268 | `evals/tasks/t3-datefns-zh-month/task.json` | `evals/tasks/t3-datefns-zh-month/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-269"></a>MM-269 | `evals/tasks/t4-estoolkit-omitby/task.json` | `evals/tasks/t4-estoolkit-omitby/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-270"></a>MM-270 | `evals/tasks/t5-estoolkit-uniqwith/task.json` | `evals/tasks/t5-estoolkit-uniqwith/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-271"></a>MM-271 | `evals/tasks/t6-sqlglot-comment-on/task.json` | `evals/tasks/t6-sqlglot-comment-on/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-272"></a>MM-272 | `evals/tasks/t7-sqlglot-sqlite-autoinc/task.json` | `evals/tasks/t7-sqlglot-sqlite-autoinc/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-273"></a>MM-273 | `evals/tasks/t8-hono-cookie-dup/task.json` | `evals/tasks/t8-hono-cookie-dup/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-274"></a>MM-274 | `evals/tasks/t9-hono-compress/task.json` | `evals/tasks/t9-hono-compress/task.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-275"></a>MM-275 | `evals/terminal-bench/.gitignore` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-276"></a>MM-276 | `evals/terminal-bench/README.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-277"></a>MM-277 | `evals/terminal-bench/agent/batch_by_memory.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-278"></a>MM-278 | `evals/terminal-bench/agent/build-binaries.sh` | `evals/terminal-bench/agent/build_binaries.py` | 验证/工程/来源材料；C7 | S/R/P：D2适配为标准Python包执行入口；外部评估工程保留，成套live成绩按V1移出 | PKG/TEST | 未开始；产品证据无；不重建独立exe门禁 |
| <a id="mm-279"></a>MM-279 | `evals/terminal-bench/agent/dao-code-setup.sh.j2` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-280"></a>MM-280 | `evals/terminal-bench/agent/diagnose_failure.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-281"></a>MM-281 | `evals/terminal-bench/agent/harbor_dao_agent.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-282"></a>MM-282 | `evals/terminal-bench/collect_results.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-283"></a>MM-283 | `evals/terminal-bench/collect_results_pro_default.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-284"></a>MM-284 | `evals/terminal-bench/extract_solutions.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-285"></a>MM-285 | `evals/terminal-bench/gen_case_studies.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-286"></a>MM-286 | `evals/terminal-bench/gen_index.sh` | `evals/terminal-bench/gen_index.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-287"></a>MM-287 | `evals/terminal-bench/gen_quant_summary.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-288"></a>MM-288 | `evals/terminal-bench/gen_results_html.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-289"></a>MM-289 | `evals/terminal-bench/gen_results_html_pro_default.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-290"></a>MM-290 | `evals/terminal-bench/gen_results_md.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-291"></a>MM-291 | `evals/terminal-bench/gen_task_status.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-292"></a>MM-292 | `evals/terminal-bench/gen_timeline.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-293"></a>MM-293 | `evals/terminal-bench/results.html` | `evals/terminal-bench/results.html` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-294"></a>MM-294 | `evals/terminal-bench/run-pro-full.sh` | `evals/terminal-bench/run_pro_full.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-295"></a>MM-295 | `evals/terminal-bench/solutions-reference.md` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-296"></a>MM-296 | `evals/terminal-bench/split.json` | `evals/terminal-bench/split.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-297"></a>MM-297 | `evals/terminal-bench/status.sh` | `evals/terminal-bench/status.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-298"></a>MM-298 | `evals/terminal-bench/summarize.py` | `参考归档（无需同名产品模块）` | 验证/工程/来源材料；C7 | 保留于冻结归档；评估文档按实际新入口更新，不照抄成绩 | PKG/TEST | 已冻结来源；非产品通过 |
| <a id="mm-299"></a>MM-299 | `evals/terminal-bench/task_meta.json` | `evals/terminal-bench/task_meta.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-300"></a>MM-300 | `evals/terminal-bench/task_overrides.json` | `evals/terminal-bench/task_overrides.json` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-301"></a>MM-301 | `evals/terminal-bench/watch-result.sh` | `evals/terminal-bench/watch_result.py` | 验证/工程/来源材料；C7 | S/R/P：Python 运行与评分适配；历史结果仅来源资料 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-302"></a>MM-302 | `evals/trace-viewer-template.html` | `evals/trace-viewer-template.html` | 验证/工程/来源材料；C7 | D/R：数据/模板候选复用；敏感、缺失外部材料及答案暴露须核验 | PKG/TEST | 72冻结资产与离线闭环 |
| <a id="mm-303"></a>MM-303 | `install.sh` | `scripts/install.py、scripts/install.ps1` | 验证/工程/来源材料；C7 | S：D2标准Python包，D3手工停进程/一致备份/安装更新/卸载；保护旧数据，不承诺自动跨版本迁移/失败回退 | PKG/TEST | 未开始；产品证据无；独立程序形态本轮移出 |
| <a id="mm-304"></a>MM-304 | `package-lock.json` | `Python 锁文件（格式待发布路线定案）` | 验证/工程/来源材料；C7 | 冻结上游锁用于 oracle 环境；Python 依赖另行锁定 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-305"></a>MM-305 | `package.json` | `pyproject.toml`、`tests/support/pyproject.toml`、`requirements-dev.in`、`requirements-dev-win311.lock`、`tools/run.py`、`tools/lock.py`、`tools/audit.py`、`docs/development.md` | 验证/工程/来源材料；C7 | 独立产品与开发支撑包，固定Windows311闭包，五项开发入口 | PKG/TEST | 03工程基线保留；批次09 Windows 固定构建、纯安装及 CI 通过相关技术核验。[发布记录](../../docs/release/batch-09.md) |
| <a id="mm-306"></a>MM-306 | `patches/ink+7.0.5.patch` | `src/ruocun/tui/ 的渲染适配与 tests/src/tui/` | 验证/工程/来源材料；C7 | S：迁移修复的可观察行为；Ink 补丁不作为 Python 依赖 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-802"></a>MM-802 | `tests/setup.ts` | `tests/conftest.py` | 验证/工程/来源材料；C7 | S：迁移测试环境初始化与隔离；不是运行时数据或核心 TS 依赖 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-803"></a>MM-803 | `tsconfig.build.json` | `pyproject.toml、Python 质量/测试配置` | 验证/工程/来源材料；C7 | 替换工程工具；新命令已确认，待工程配置；不保留 JS 核心 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-804"></a>MM-804 | `tsconfig.json` | `pyproject.toml、Python 质量/测试配置` | 验证/工程/来源材料；C7 | 替换工程工具；新命令已确认，待工程配置；不保留 JS 核心 | PKG/TEST | 未开始；产品证据无 |
| <a id="mm-805"></a>MM-805 | `vitest.config.ts` | `pyproject.toml、Python 质量/测试配置` | 验证/工程/来源材料；C7 | 替换工程工具；新命令已确认，待工程配置；不保留 JS 核心 | PKG/TEST | Python未开始；[02来源对照已运行](evidence/02-oracle/README.md) |

## 新增适配层（候选位置）

NEW 行登记平台适配职责。路线见 D08–D12 和对应 ADR，实际后端、支持范围及验收证据以所属任务为准。

| ID | 候选路径 | 职责 | 案例 | 前置地图票 |
| --- | --- | --- | --- | --- |
| NEW-01 | src/ruocun/platform/windows/processes.py | 进程身份/受管树/温和取消与强制收口 | WIN-02 / REC-09 | 17/18 |
| NEW-02 | src/ruocun/platform/windows/ipc.py | 认证 IPC、ACL、断开重连与 epoch fencing | WIN-03 / REC-10 | 18/08 |
| NEW-03 | src/ruocun/platform/windows/durable_file.py及platform/file_contract.py | 私密目录/锚、替换与持久确认；不宣称断电保证 | WIN-04 / REC-12 | 07子路径已实现并独立通过；[证据](integration-evidence/sprint07/README.md)；最终产物/其它平台未验 |
| NEW-04 | src/ruocun/platform/windows/credentials.py | 系统凭据、profile 名编码、可见 fallback | WIN-05 | 17/09 |
| NEW-05 | 原拟src/ruocun/platform/windows/schedule.py；准确不支持路由归MM-582 | W3移出Windows Task Scheduler/dispatcher补齐；不以loop冒充系统定时 | WIN-06 | ADR-0010；59准确边界仍待实现/验收 |
| NEW-06 | 原拟src/ruocun/platform/windows/power.py；能力说明归MM-798 | W5移出Windows自动防休眠补齐，不宣称取得系统锁；正常取消/退出仍保留 | WIN-07 | ADR-0010；62准确边界未验 |
| NEW-07 | src/ruocun/platform/windows/clipboard.py | 图片/文本剪贴板与类型/大小验证 | WIN-08 | 17/10 |
| NEW-08 | 原拟src/ruocun/platform/windows/sandbox.py；按ADR-0008取消额外后端，Windows不支持分支归MM-698 | 来源平台能力与诚实拒绝；Job不冒充沙箱 | WIN-09 | 60/61来源平台路由已验，Windows明确拒绝启用 |
| NEW-09 | 原拟src/ruocun/platform/windows/notifications.py；终端提示归MM-772/680 | W6移出桌面窗口/通知发送，保留终端提示和安全标题且准确说明去向 | WIN-10 | ADR-0010；63保留路径未验 |
| NEW-10 | src/ruocun/platform/（公共端口及 posix 实现） | 业务只依赖能力契约；Linux/macOS 保留实现对应 | WIN-11 | 13 |
| NEW-11 | tests/support/ruocun_acceptance/、tests/test_acceptance.py、tests/test_acceptance_process.py | 统一开发期验收驱动，调用真实 CLI/协议/进程 | TEST-07 / T-N2 | 03完成offline4、逐例证据与失败/取消/清理边界；其余六suite非零not-run；[修复证据](evidence/03-boot/r2/README.md)，独立复核见03票 |

| NEW-12 | src/ruocun/config/compat.py | D09 唯一兼容契约：compatibility.json source map 解析 + RUOCUN_/DAO_ 环境别名与逐变量谓词 | CFG-04/05/06/09 | 09；04本票路径已实现 |
| NEW-13 | src/ruocun/chat_demo.py | 一次性 prompt 首轮流式对话组合根（合成配置 + 本地合成 SSE 服务），显式 `--chat-demo` 入口 | CFG/WIRE 本票路径 | 04本票路径已实现；完整 Agent 仍 exit 69 |
| NEW-14 | tools/extract_prompt.py | 从冻结快照可复现地提取提示词文本资源（MIT 标注） | WIRE-01 / PROMPT | 04本票路径已实现 |
| NEW-15 | src/ruocun/prompt/resources/system_prompt.{zh,en}.txt | 冻结系统提示词文本资源，`*.txt -text` 字节保真 | WIRE-01 / PROMPT | 04本票路径已实现；请求 golden 已对照 |
| NEW-16 | src/ruocun/responses_demo.py | Responses 路由一次性演示组合根（合成配置 + 本地合成 HTTP/SSE 服务 + 两轮工具回合），显式 `--responses-demo` 入口 | WIRE-04 本票路径 | 05本票路径已实现；完整 Agent 仍 exit 69 |
| NEW-17 | tests/test_responses_{route,request,client,stream,path}.py | 由冻结 `responses.test.ts`/`client.test.ts` 断言改写的 48 条 Responses 桥回归 | WIRE-04 | 05本票路径已实现；6 处弱断言待后续独立 oracle 加强 |
| NEW-18 | src/ruocun/client/resilient.py | 冻结client.ts重试、错误分类、idle与fallback编排；公开streamChat调用，runStreamAttempt只承担单轮 | WIRE-07/08 | 06本票路径已实现并独立复核；[证据](integration-evidence/sprint06/README.md) |
| NEW-19 | src/ruocun/client/_dns_helper.py | 命名主机受监督解析子进程、请求取消后真实退出；不修改全局getaddrinfo | WIRE-07/08 / Windows适配 | 06本机产品路径已验；CPython私有连接工厂/其它平台/standalone仍保留后续限制 |

## 维护字段与核对门禁

每次迁移更新对应 MM/NEW 行：实际目标、保留/拆分/合并理由、任务/ADR、案例 ID、实现状态、提交 SHA、验证证据。目录级覆盖不能代替逐文件处理；源码内测试辅助不冒充新功能。所有 805 个快照成员恰好登记一次（工具/命令定位为交叉索引，不计重复成员）。215 个来源测试、58 个脚本、16 个 task.json、85 个独立 fixture 的发现口径沿用研究附录；未运行来源测试的行为仍需 oracle 验证。
