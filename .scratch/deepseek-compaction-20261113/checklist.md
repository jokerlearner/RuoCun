# DeepSeek 压缩策略与原文归档验收清单

状态：自动出口通过、用户体验待验；最终B-r3指纹、原失败及分段复用范围见[交付记录](delivery.md)。以下保留原规划细节，实际判定以末表为准。
日期：2026-11-13（Asia/Shanghai）。范围：用户已选方案 B，并于后续明确授权按spec进行TDD实施。
规格与任务入口：[spec.md](spec.md)、[plan.md](plan.md)、[task.md](task.md)；行为以规格的 AC01–AC16 为准。

## 验证原则与证据层级

- 遵守 ADR-0009：复用 DAO 迁移断言、固定 DeepSeek 来源测试语义和既有故障 seam；只补新能力必需的最小确认。
- 遵守 ADR-0015：定向回执绑定候选，持久化/恢复接缝独立复跑；固定交付产物集中构包，不逐票构包。
- 首选最高可用 seam：真实 CLI → 本地 HTTP/SSE fixture → 实际受控 SQLite → 关闭进程 → 新进程恢复/查询/导出。
- 模型边界仅返回合成确定响应，记录请求次数和消息；不 mock 被验收的 CLI、压缩入口、归档提交或查询处理器。
- 纯预算/切点算法用现有函数测试；原子回滚、取消等待与提交未知用既有 StorageWorker/SQLite 故障 seam 补足。
- 新测试文件名均为拟定名称，尚不存在；不能把本文条目当作已实现测试或已执行结果。
- 摘要语义质量和真实供应商缓存命中不由合成 fixture 证明；付费模型、量化性能和每票 Windows Terminal 验收不作默认交付门槛。
- 现有失败/已批准差异保留原证据；旧断言因 B 改变时标注替代 AC，不删除历史记录或把旧行为声称为通过。

## 环境与运行白名单

- E1：子进程从空环境构造，只继承所需 SYSTEMROOT、WINDIR、COMSPEC、PATH、PATHEXT；PATH 固定为批准工具链所需目录。
- E1：HOME、USERPROFILE、APPDATA、LOCALAPPDATA、ProgramData、TEMP、TMP 全部指向本案例合成目录；配置、会话、导出亦在其中。
- E1：只显式加入案例所需 RUOCUN_LANG、预算/压缩配置及合成模型地址；不得继承真实账户、代理、token、Hooks、MCP 或观察服务配置。
- E2：源码测试用 `python -I -X utf8` 和显式源码 loader；安装验证只用仓库外环境的已安装包，不借 tests 或源码兜底。
- E3：本地服务仅绑定 127.0.0.1 随机端口，密钥为明确合成值；日志仅保存经审查的参数、请求摘录、DB事实和哈希。
- E4：受控 SQLite 使用现有 `tests/fixtures/sqlite-dll-win-x64-3540100.zip` 及实际校验入口；未知平台保留 not-run，不伪装 Windows 通过。
- 现有用例若依赖父环境，执行前仅修正其启动白名单；不能因这里列了 E1 就宣称旧脚本已经隔离。

## C01 / AC01：完整请求预算与触发一致

- [x] 输入：相同消息配小/大窗口，分别加入较长系统提示、工具目录、输出预留和新增用户消息；参数取规格合法值与一个非法余量值。
- 可观察预期：自动、手动、服务端超限入口使用同一计量和策略；低于阈值无机会性裁剪；非法预算在发请求前明确拒绝。
- 核查：本地 HTTP 请求中的实际模型/工具与预算输入一致；粗估与供应商实际 usage 分列，不混报精确 token。
- 复用：`tests/test_advanced_context_runtime.py::test_source_environment_defaults_and_native_alias_precedence`、`tests/test_advanced_context_compact.py::test_compaction_only_at_or_over_threshold`。
- 来源：DeepSeek `compaction-basic.spec.ts` 的统一测量、request-envelope、输出预留和配置不变量用例。
- 最小新增：拟 `tests/test_deepseek_compaction_policy.py` 计量表；CLI 共用 C08 fixture 增加压力入口请求断言。
- 时机/环境：T02 定向，T04 接线，T06 组合复验；E1–E4。状态：已执行，结果与证据见末表。

## C02 / AC02：近期尾部、控制前缀与工具配对

- [x] 输入：旧对话、旧摘要、Todo、必要控制消息，以及一个 assistant 发出两个调用并含全部结果的近期工具组。
- 可观察预期：按预算保留近期原文，切点向前调整保住完整工具组；call ID 与 result ID 配对，不丢首条系统提示及 Todo。
- 核查：无可安全压缩区时不发摘要请求、不提交空候选；不假定摘要永远位于下标 1。
- 复用：`tests/test_advanced_context_compact.py` 的 system-anchor、pinned-task、system-only；`tests/test_n17_recovery.py::test_repair_preserves_assistant_known_result_and_explicit_unknown_without_replay`。
- 来源：DeepSeek `compaction-basic.spec.ts` 的 retention-cut/pairing；`compaction-loop-repro.spec.ts` 的 balanced-cut。
- 最小新增：在拟 policy 测试迁移一个多调用切点案例；新保尾断言明确替代原“全部变单摘要且无尾部”断言。
- 时机/环境：T02，T04 后由 C08 请求快照确认；E1–E4。状态：已执行，结果与证据见末表。

## C03 / AC03：先裁剪工具正文且原文可查

- [x] 输入：一个超过裁剪阈值的普通文本工具结果、一个短结果及一个 TaskWait/后台控制结果，包含 Unicode 头尾标识。
- 可观察预期：只有压力确认后裁剪；保留工具身份、头尾、明确省略标记与有效归档引用，控制结果保持原值。
- 核查：裁剪单独解除压力时摘要请求数为 0；仍需摘要而摘要失败时，裁剪候选和原文引用都不提前提交。
- 复用：`tests/test_n16_background_storage.py::test_ready_wait_ack_requires_its_message_and_consumes_only_own_run` 的控制结果边界。
- 来源：DeepSeek `tool-result-pruner.spec.ts` 的 head/tail、non-text-order、引用原文、一次收敛及 replay 用例。
- 最小新增：拟 policy 测试迁移头尾/非文本块断言；拟 `tests/test_deepseek_compaction_entry.py` 断言真实 CLI 裁剪与按引用读回全文。
- 时机/环境：T02 算法，T03–T05 引用闭合后，T06 CLI；E1–E4。状态：已执行，结果与证据见末表。

## C04 / AC04：摘要重整、缩小校验与有界恢复

- [x] 输入：连续两次压缩；第二次含旧摘要和新增事实；fixture 另返回空摘要、finish_reason=length 与不缩小摘要。
- 可观察预期：最新上下文只有一份整体摘要，旧有效事实参加重整，不无限追加 `[本次补充]`；含包装候选严格缩小。
- 核查：坏摘要、请求失败/取消均保留原投影并停止；超限恢复仅在已确认减量后有限重试，普通网络重试预算保持独立。
- 复用：`tests/test_advanced_context_runtime.py` 的 failed/partial/empty、request-exception、cancelled-summary；原旧摘要逐字追加断言登记为 B 差异。
- 来源：DeepSeek basic 的 non-shrinking-summary、empty/reasoning/image-output、bounded-retries；loop-repro 的独立重试预算。
- 最小新增：复用 ContextManager seam 迁移缺失输出门槛；C08 fixture 覆盖第二次重整及一次标准超限恢复，不枚举所有排列。
- 时机/环境：T02，T04，T06；E1–E4。状态：已执行，结果与证据见末表。

## C05 / AC05：归档与投影替换同事务

- [x] 输入：待压缩原文、候选摘要及预期 revision；分别执行正常提交与既有 `_put_meta` 确认回滚 seam。
- 可观察预期：成功后同一事务出现归档原文/元数据、摘要引用和新 checkpoint；回滚后上述结果均不出现，旧投影保持。
- 核查：摘要计算期间投影或模型改变则拒绝过时候选；只检查旧段不足以证明整个自动候选仍有效。
- 复用：`tests/test_advanced_conversation.py::test_compact_projection_keeps_acknowledged_input_ledger_after_reopen`、`tests/test_n16_background_storage.py::test_confirmed_save_rollback_unstages_and_retries_same_message_once`。
- 来源：DeepSeek basic 的失败不改 surface、并发 surface 变化拒绝；RuoCun 同事务原文归档为方案 B 的必要工程确认。
- 最小新增：拟 `tests/test_deepseek_compaction_archive.py` 扩展现有真实 SQLite seam，单个成功/确认回滚对照，不新建存储框架。
- 时机/环境：T03 持久化独审，T04 集成，T06 重开确认；E1–E4。状态：已执行，结果与证据见末表。

## C06 / AC06：幂等、取消等待与提交未知

- [x] 输入：同 operation ID 重复提交同候选、同 ID 不同摘要；已受理提交时取消等待；提交后丢确认一次。
- 可观察预期：同内容返回同 revision/归档引用且无重复；异内容拒绝；取消等待不等于 SQLite 回滚。
- 核查：未知确认在当前进程保留未决并停止；新进程按操作记录核实已提交结果，不重发摘要或重放工具副作用。
- 复用：`tests/test_session_recovery.py::test_checkpoint_operation_is_idempotent_and_survives_restart`、`test_cancelling_wait_does_not_cancel_accepted_checkpoint`。
- 故障复用：`tests/test_n17_recovery.py::test_recovery_commit_ack_unknown_remains_distinct_and_reconciles_once` 的 `_atomic` 后抛 CommitUnconfirmedError seam。
- 最小新增：拟 archive 测试仅将该 seam 绑定压缩归档事务，核对归档计数/引用；不扩掉电、随机竞态或压力矩阵。
- 时机/环境：T03–T04 高风险独审，T06 新进程核实；E1–E4。状态：已执行，结果与证据见末表。

## C07 / AC07：归档查询与受限读取

- [x] 输入：两次压缩归档、一个有效引用、缺失引用、区外/其他会话引用，以及超出单次输出上限的原段。
- 可观察预期：规格规定的列表/读取入口返回批次、摘要关联和可定位原文；限制分页/范围输出，拒绝跨会话越权与路径穿越。
- 核查：用户查询处理器本身不写归档或 checkpoint、不重新执行历史工具；模型 ArchiveRead 沿正常 intent/result/checkpoint 记录，可推进 revision，并发后台推进也不算查询副作用。摘要所带引用能用公开入口真实读回。
- 复用：`tests/test_b05_sessions.py` 普通 session 命令入口；`tests/test_b07_audit_command.py` 会话选择目录边界。
- 来源限制：DeepSeek replay 只作引用/回放依据，不冒充已有公开关键词查询测试；RuoCun 查询是 B 的新增能力。
- 最小新增：拟 entry 文件扩展同一个 CLI fixture，校验查询输出与 SQLite 原段相符，不直接调用内部读函数替代入口验收。
- 时机/环境：T05，T06；E1–E4。状态：已执行，结果与证据见末表。

## C08 / AC08：两进程恢复与完整导出

- [x] 输入：进程一执行普通工具往返并至少压缩两次后退出；进程二以会话 ID 继续、查询原段并导出。
- 可观察预期：重开恢复同一摘要和近期尾部；完整历史导出包含被压缩 assistant/工具原文，顺序正确且无重复摘要替代原文。
- 核查：记录两进程 HTTP 请求、会话 ID、DB revision/归档条数与导出文件哈希；原始输入账本仍存在，工具执行次数不增加。
- 复用最高 seam：`tests/test_b05_sessions.py::test_source_session_commands_switch_branch_and_continue_through_normal_entry`，已有真实 CLI、本地 SSE、多进程和 Markdown 导出。
- 补充：`tests/test_session_recovery.py::test_committed_message_survives_process_restart`；DeepSeek basic/pruner 的 replay-identical 语义。
- 最小新增：拟 entry 文件沿该结构形成共享集成案例，同时消费 C01–C04/C07 的请求与产物断言，避免每项新起一套框架。
- 时机/环境：T06；E1–E4。状态：已执行，结果与证据见末表。

## C09 / AC09：旧会话与旧摘要兼容

- [x] 输入：用原版本结构构造的合成旧 DB、旧格式摘要且没有原文归档；另用一次既有事务回滚 seam 验升级失败。
- 可观察预期：按规格显式迁移版本，消息/输入/工具/后台状态保持；失败时不留下半套结构；严格 schema 校验继续有效。
- 核查：缺失的历史明示“此前未归档”，不凭摘要虚构原文；旧会话可续聊、再压缩并查询新增归档。
- 版本门禁：复用受控旧程序及合成新语义版本副本，核对旧程序拒绝打开 storage_version=3，前后会话业务数据不变；不对真实用户 DB 试跑旧二进制。
- 复用：`tests/test_session_recovery.py` 的重开与操作幂等；`tests/test_advanced_conversation.py` 的已确认输入账本断言。
- 现有边界：`src/ruocun/session/durable_store.py` 严格表结构与 user_version 验证；不能静默加表就宣称兼容通过。
- 最小新增：拟 archive 文件保存小型合成旧 DB fixture 和一条升级后重开断言；不读取用户真实会话，不创建历史版本大矩阵。
- 时机/环境：T03 迁移独审，T05 兼容出口，T06 CLI续聊；E1–E4。状态：已执行，结果与证据见末表。

## C10 / AC10：后台等待与迟到事件

- [x] 输入：一个持久 TaskWait、一个尚未投递的后台完成事件；在安全边界发生压缩，再投递并重开。
- 可观察预期：等待身份、pending event、长结果 spill 引用及 delivered 确认仍由原存储权威处理；结果恰好投递一次。
- 核查：裁剪不改控制正文，不消费他人 run；无模型轮询替代后台等待，压缩不自动重启已执行任务。
- 复用：`tests/test_n16_background_storage.py::test_persisted_wait_restores_and_event_wakes_without_model_poll`、`test_ready_wait_ack_requires_its_message_and_consumes_only_own_run`。
- CLI复用：`tests/test_b02_agent_background_entry.py::test_background_agent_reads_then_wakes_waiting_main_session` 的现有恢复分支。
- 最小新增：仅在上述真实等待/投递路径插入一次已批准压缩操作并加归档引用断言，不乘成每种后台模式全组合。
- 时机/环境：T04 控制边界，T06 组合复验；E1–E4。状态：已执行，结果与证据见末表。

## C11 / AC11：模型切换与目标窗口

- [x] 输入：较大窗口会话切至较小窗口，再以相同 model ID 切换不同 provider 容量；摘要期间变更一次目标。
- 可观察预期：用目标的窗口/预留重新检查；需要压缩时完成可确认减量后才接受切换；失败不落地不兼容模型。
- 核查：保留显式摘要模型设置；发出的下一请求消费已验证目标，旧请求 usage 不被当作新上下文总量。
- 复用：`tests/test_advanced_context_runtime.py::test_source_window_lock_effort_first_argument_and_queries_do_not_add_user`、`tests/test_context_session.py::test_set_model_keeps_messages`。
- 来源：DeepSeek basic 的 destination-window、proposed-output-reservation、same-model-provider-switch 和 failed-summary 拒绝切换。
- 最小新增：拟 policy 文件参数化容量解析；拟 entry fixture 记录切换前后 model/provider 请求，不需接真实供应商。
- 时机/环境：T02，T04，T06；E1–E4。状态：已执行，结果与证据见末表。

## C12 / AC12：图片与非文本内容

- [x] 输入：已交付的 Read 图片、近期用户图片及一条带非文本块的长工具结果；压缩、关闭、重开、读取原段。
- 可观察预期：计量使用明确图片估算；摘要可用占位文字，原文归档保留原支持的图片内容/附件引用及交付标记。
- 核查：重开不把已压缩图片再次注入近期上下文；裁剪不破坏非文本块顺序；缺失附件按已有保护停止。
- 复用：`tests/test_advanced_context_compact.py::test_image_placeholders_preserve_source_messages_and_deduplicate_adjacent_images`。
- 存储复用：`tests/test_n0_image_session.py::test_complete_image_result_reopens_once_and_compressed_history_does_not_reinject_old_records`；DeepSeek pruner 非文本顺序断言。
- 最小新增：在现有图片重开案例补归档读回/附件引用断言，不增加格式、尺寸或图像识别质量矩阵。
- 时机/环境：T03 归档表示，T05读取，T06；E1–E4。状态：已执行，结果与证据见末表。

## C13 / AC13：子代理与会话分支

- [x] 输入：含压缩归档的父会话建立普通子代理和会话分支；分别查询自己的原文，再按规格处理源会话清理。
- 可观察预期：父子 tool scope、run 身份及上下文隔离；分支归档复制/引用策略闭合，不产生指向已删除源的悬空引用。
- 核查：父会话不承担子代理执行结果重放；特殊 fork 跨重启仍按原材料不足拒绝规则，不因归档存在放宽。
- 复用：`tests/test_n38_agent_sync.py` 同步子代理身份/未知结果；`tests/test_n41_fork_core.py` 原模型投影与工具目录契约。
- 分支复用：`tests/test_b05_sessions.py` 的 branch/reopen；`tests/test_b02_agent_background_entry.py` 的现有 fork 恢复拒绝分支。
- 最小新增：在现有分支案例补两个归档查询/生命周期断言；普通子代理只补一次隔离确认，不遍历所有代理模式。
- 时机/环境：T04，T05，T06；E1–E4。状态：已执行，结果与证据见末表。

## C14 / AC14：归档与会话生命周期清理

- [x] 输入：共享 CLI 案例中的压缩前后 clear/rewind，再覆盖一个可清理 closed 会话、一个保留中的 paused 会话及其归档/图片附件引用。
- 可观察预期：clear/rewind 后原文和边界可回看，当前投影不自动回灌被移除内容；归档与所属会话同生命周期，保留会话原文可查，封存失败保留现场，不单独删掉仍被引用的原段。
- 核查：若分支共用材料，按 C13 规则保护；不引入默认独立归档 GC，也不清理真实用户目录或历史实验材料。
- 复用：`tests/test_b05_sessions.py::test_source_session_selection_uses_saved_cwd_done_and_real_user_turns` 的 prune 对照。
- 现有保护：`src/ruocun/session/prune.py` 的身份核对/封存/删除；`test_cleanup_retains_clean_owned_worktree_named_by_retained_agent` 的引用保护。
- 最小新增：在现有清理案例补归档随会话删除或保留断言；不新建链接、竞态、磁盘故障排列矩阵。
- 时机/环境：T05，T06；E1–E4。状态：已执行，结果与证据见末表。

## C15 / AC15：固定独立包与来源归属

- [x] 输入：固定候选构出的 sdist/wheel，在仓库外合成 HOME 的安装环境执行 C08 精简入口及查询/导出。
- 可观察预期：从实际安装包载入压缩资源、归档schema和命令；资源/许可进入包，外部源码和测试目录不作运行依赖。
- 核查：包成员字节与候选绑定；DeepSeek MIT 来源及改写归属保留；不宣称通过未运行的上游整套 TypeScript 测试。
- 复用：`tests/test_package.py`、`tools/run.py` 白名单执行器及 `docs/release/batch-09.md` 的固定包/纯安装流程；历史 `tools/audit.py` 含旧无依赖断言，不直接作为本轮门禁。
- 最小新增：同一 C08 案例的 loader 切到已安装包；检查新增资源与归属成员，不无理由重复全部失败注入。
- 执行时机：T07 一次集中构包；所需静态检查、构建和已迁移全量按本批记录收口，修复后仅重跑受影响路径。
- 环境：E1、E3、E4及仓库外 E2；状态：已执行，结果与证据见末表。

## C16 / AC16：权限、脱敏与证据界限

- [x] 输入：带明确合成凭据标记的消息/工具原文、合法归档 ID、跨会话 ID和路径穿越串；查询、导出、审计并恢复。
- 可观察预期：归档沿现有 Conversation 脱敏入口，不保留新增明文秘密；工具/命令权限按规格，模型不能读取任意用户历史。
- 核查：归档查询无工具副作用；日志、pytest 参数和失败输出仅含审查后的合成值；图片不透明字节沿既有处理边界保留。
- 复用：`tests/test_advanced_conversation.py` 对不可完整保存输入的拒绝；`tests/test_n0_image_session.py` 图片与正文脱敏区分。
- 权限复用：`tests/test_n1_permissions_gate.py`、`tests/test_n1_permissions_plan.py` 的既有规则；只扩新增读取入口的必要断言。
- 最小新增：C07/C08 fixture 共享跨会话/脱敏断言，独审检查真实调用链；不读取、打印或复制本机真实配置与会话。
- 时机/环境：T03写入，T05读出，T06证据检查，T07安装独审；E1–E4。状态：已执行，结果与证据见末表。

## 验收追踪表

| 清单 | 规格 | 主要任务 | 入口/补充 seam | 状态 | 回执 |
|---|---|---|---|---|---|
| C01 | AC01 | T01、T02、T04、T06 | policy＋真实CLI请求 | 自动通过 | t02-summary、ctrl2、t04-child-summary、r3x |
| C02 | AC02 | T01、T02、T04、T06 | 配对/Hook/Todo＋CLI投影 | 自动通过 | reviewer-t02-policy、todo-final、r3x |
| C03 | AC03 | T02–T06 | 裁剪＋公开原文读取 | 自动通过 | reviewer-child-final、reviewer-t03-final-increment |
| C04 | AC04 | T02、T04、T06 | ContextManager＋SSE输出 | 自动通过 | ctrl2、r1r→r1g、r3x两次实际摘要 |
| C05 | AC05 | T03、T04、T06 | 真实SQLite＋已有回滚seam | 自动通过 | t03-delivery、reviewer-t03-final |
| C06 | AC06 | T03、T04、T06 | 幂等/丢ack/取消 | 自动通过 | reviewer-t03-final、reviewer-t03-upgrade-cancel、t04-child-summary |
| C07 | AC07 | T05、T06 | CLI公开查询与工具 | 自动通过 | r2-target、perm1g、reviewer-archive-deny、r3x |
| C08 | AC08 | T06 | 两进程＋完整/当前导出 | 自动通过 | reviewer-t06-final、reviewer-t06-installed、r3x |
| C09 | AC09 | T01、T03、T05、T06 | 旧writer/备份升级/新进程 | 自动通过 | t03-12-frozen-reader、reviewer-t03-final、r3x |
| C10 | AC10 | T04、T06 | TaskWait/后台仅一次投递 | 自动通过 | q1中已通过的N16组、t04-child-summary、f2原通过项 |
| C11 | AC11 | T02、T04、T06 | 容量策略＋实际切换请求 | 自动通过 | mr3、rv1r→rv1g、reviewer-route-export、ctrl2 |
| C12 | AC12 | T03、T05、T06 | 图片/元数据/附件闭包 | 自动通过 | t04-07-projection-green、reviewer-t03-lifecycle、f2原图片通过项 |
| C13 | AC13 | T04–T06 | fork/branch/子范围隔离 | 自动通过 | reviewer-child-final、reviewer-t03-lifecycle、r2-target |
| C14 | AC14 | T05、T06 | 边界/封存/清理 | 自动通过 | reviewer-t03-lifecycle、B05及f2原checkpoint/rewind通过项 |
| C15 | AC15 | T07 | B-r3固定wheel仓外纯安装 | 自动通过 | t07-r3-delivery、r3x、reviewer-r3-final-fingerprints |
| C16 | AC16 | T03、T05–T07 | 脱敏/权限/范围边界 | 自动通过 | reviewer-archive-deny、advanced_conversation/image组、r3x |

每份实际回执须填候选提交或工作区指纹、固定产物指纹（适用时）、命令、环境白名单版本、结果与保留失败路径。
最终分别报告：实现状态、自动验证、独立复核、真实模型质量、Windows Terminal体验；未执行项继续明确未验。
