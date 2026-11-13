# 07 — 保存一次会话并拒绝并发owner写入

Type: task
Mode: AFK
Status: resolved
Assignee: /root/sprint07
Branch: impl/07-store
Worktree: .worktrees/wb-i07
Parent: [完整迁移规格](../spec.md)
Blocked by: [04 — 用兼容账户配置完成首轮流式对话](04-chat.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

对话commit→退出→重启读回；WAL/FULL/修复运行库、epoch、文件占用/坏库拒绝有真实证据。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-591](../module-map.md#mm-591)、[MM-593](../module-map.md#mm-593)、[MM-595](../module-map.md#mm-595)、[MM-597](../module-map.md#mm-597)、[MM-600](../module-map.md#mm-600)、[MM-601](../module-map.md#mm-601)、[NEW-03](../module-map.md#新增适配层候选位置)。

## 共享接口与并行

接口领域：存储。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [REC-01](../acceptance-matrix.md#rec-01) — 权威恢复数据：本票路径覆盖的子案例满足“SQLite权威；JSON/events.jsonl不被当等价真相；正常重启聊天与状态连续”。
- [x] [REC-02](../acceptance-matrix.md#rec-02) — schema/损坏：本票路径覆盖的子案例满足“既有v2语义作为内部baseline；新字段/版本须明确迁移；未来/损坏拒绝，不静默空会话”。
- [x] [REC-03](../acceptance-matrix.md#rec-03) — 事务与配置：本票路径覆盖的子案例满足“消息/background/revision/delivered原子；run/event原子；失败保留原错，不伪造成功”。
- [x] [REC-09](../acceptance-matrix.md#rec-09) — owner 与进程身份：本票路径覆盖的子案例满足“canonicalcwd+host/boot/pid/start；旧writer fencing；查询失败不冒充死亡；跨host不自动接管”。
- [x] [REC-12](../acceptance-matrix.md#rec-12) — 原子文件与权限：本票路径覆盖的子案例满足“持久确认边界真实；私密文件/能力受限；失败不吞；无实证不承诺断电不丢”。
- [x] [REC-15](../acceptance-matrix.md#rec-15) — SQLite运行库修复门禁：本票路径覆盖的子案例满足“有官方WAL修复或可审计backport；探针3.45.1不合产品门禁，普通压力通过不证明已修复”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

最终实现候选`6a4228d`（来源关联最小修复`f9c9b5a`），独立复核`67f969a`，主协调仅合入后续D13领取文档为`f2d3d52`后快进接收，产品字节与复验点一致。见[来源映射与实现](../evidence/07-store/sprint-session/README.md)、[独立复核及原失败](../integration-evidence/sprint07/README.md)。独立既有真实存储12项、原5关联回修5项、平台9及20回归通过；必要Ruff/mypy43/build/offline4、仓库外纯wheel两进程保存恢复与实际SQLite3.54.1清单匹配。实现者固定全量387 passed/3 deselected，不冒充独立者全量亲跑；已按ADR-0009收口。主db/业务状态只读不写，WAL/SHM协调文件物理维护如实记录。真实模型/WT/独立账户/断电/其它平台/standalone/性能未验；未清理历史探针/异常对象。

## Comments

- 2026-11-10冲刺接收：独立复核67f969a允许本票接收；主协调合入D13领取文档为f2d3d52（无产品变化）后ff-only接收并resolved，正式完成6/84。已确认真实错误按已有复现闭环，测试按ADR-0009收口；未验范围保持。后继08/28释放，58私密端口前置已满足。

- 2026-11-10 19:01:22 +08:00：用户正式启动冲刺，主协调接管并将本票交/root/sprint07在原impl/07-store、wb-i07接续。原未提交test_session_identity.py、失败探针和异常对象保留。使用diagnosing-bugs先建立隔离可判别复现，再修复并TDD，禁止重跑已停止的relative_handle_probe。产品/平台条件和独立复核未通过前不结题。

- 2026-11-10：用户指定改由 Codex 接手；保留 WorkBuddy 原分支、worktree 和未提交成果，在原票继续，须完成实现、隔离验证及独立集成复核后才能结题。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-05：主代理确认前置 [04](04-chat.md) 已 resolved 并集成至 `dbdd0bc`，按 `issue_graph.py` 真实 frontier 将本票由 blocked 释放为 ready-for-agent。接口领域与共享 client/session 契约由主代理统筹；05/06 均涉及 `src/ruocun/client/client.py`，并行时须按主代理分派的边界避免各自重定义。

- 2026-11-10：05 已 resolved 并集成至 `637fc37`，共享 client 契约（含 05 新增的 `chunks` 消费与 Responses 路由分支）已稳定。主代理按 `issue_graph.py` 真实 frontier 与 implement-spec Step 6 的并发精神，将 06/07/58 作为**同一批并行**领取，各自独立分支/worktree（impl/07-store / .worktrees/wb-i07），起点为含本批领取记录的集成 tip。共享文件边界由主代理统筹：`cli.py` 只允许各自追加一个独立的显式 demo 分发分支、不得改写既有分支；06 不改 `types.py`/`responses.py`/`sse.py` 与 `session/`，07 不改 `client/`，58 不改 `client/` 与 `session/`；若必须改变共享接口，先向主代理报告具体契约差异，不在多个分支各自重定义。实现与独立 merger 分别派发，人工体验按 ADR-0004 集中最终验收。
