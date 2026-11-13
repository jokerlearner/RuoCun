# Issue tracker: Local Markdown

本项目使用本地 Markdown 管理规格和任务。

## 文件约定

- 每个功能目录：.scratch/<feature>/
- 功能规格：.scratch/<feature>/spec.md
- 每张任务票：.scratch/<feature>/issues/<NN>-<slug>.md
- 每张任务票独立成文件，从 01 开始编号。
- 跨功能引用使用完整仓库相对路径。
- 讨论和补充决定追加到任务票的 ## Comments。
- .scratch/ 是正式工程记录，纳入 Git。

## 任务票字段

- Type: research / prototype / grilling / task
- Status: open / ready-for-agent / claimed / blocked / awaiting-user / resolved
- Blocked by: 前置任务路径；无则写 none
- 验收条件
- 验证证据
- 用户体验验收：pending / accepted / not-required
- Scope：未写为当前范围；`reduced`为按ADR-0010缩减后仍须实施，`excluded`为本轮移出。Scope与Status分开，excluded不等于resolved。

## 流转规则

- 规格清晰且前置条件满足后，标记 ready-for-agent。
- 实施前标记 claimed，记录负责分支。
- 缺少必要信息或外部条件时，标记 blocked 并写明原因。
- 需要用户决策或体验验收时，标记 awaiting-user。
- 满足本票全部完成条件后，标记 resolved。
- 自动测试通过与用户体验验收分别记录。
- 同一任务票由一个分支负责实施。

## 小批与验收出口

迁移批次遵循[ADR-0015](../adr/0015-batch-validation-and-packaging.md)及[当前批次](../../.scratch/ruocun-next24h/batch-02.md)。普通同领域5–8票按真实依赖分段连续实现、批末独审，逐票提交、留证、判定。关键接缝和跨负责人消费等待独审集成。复用已有工作会话和私有环境，按保存点增量交接。日常更新任务票和批次记录，公共对应表与验收矩阵在里程碑汇总。

[ADR-0014](../adr/0014-terminal-and-scope.md)列当前排除名单。保留其原编号、状态与来源，票和图同步登记 `excluded`。旧 `issue_graph.py` 尚未识别 `scope`，由主协调在派发前过滤排除名单并核对真实依赖。

派发批次时记录批次ID、票号、起点SHA、实现/审查负责人、绝对worktree目录、文件归属、接口和当前允许执行的票。时间、候选及复核证据在各票Comments中记录；公共汇总由主协调维护。

77/78的`Automatic exit`、`Automatic evidence`只汇总验收矩阵中的自动技术结果，当前初值为`pending`、`none`。自动通过且人工待验时可`awaiting-user`，HITL保持`pending`。任务图的`dependency_exits`是79/84目标出口声明；驱动尚未适配时仍按`deps`要求整票`resolved`，保持阻塞。85始终消费77/78完整结题和人工accepted，不消费自动出口替代体验。字段、证据与未来适配验证要求统一见ADR-0006；本轮不改变任何票的完成状态。

## 技能操作约定

- “发布到 issue tracker”：创建对应 Markdown 文件。
- “读取任务”：读取指定任务票及其前置任务。
- 使用 wayfinder 时：map.md 保存 Notes、Decisions-so-far、Fog；子票使用 open → claimed → resolved；解决后将结论和任务链接追加到 map.md。

## Wayfinding operations

- 地图：.scratch/<effort>/map.md，Labels: wayfinder:map；使用 Destination、Notes、Decisions so far、Not yet specified、Out of scope。
- 子票：.scratch/<effort>/issues/NN-<slug>.md；Parent 链接地图，Labels 只使用 wayfinder:research / wayfinder:prototype / wayfinder:grilling / wayfinder:task。
- 子票类型以 Labels 为准；Mode: AFK / HITL。Wayfinder 子票不使用 ready-for-agent 等分诊标记。
- 依赖：Blocked by 行用本目录内真实子票的标题链接；所有前置票 resolved 后才解除阻塞。
- 领取：先设置 Status: claimed 与 Assignee，并保存，再开始工作；开放且 Assignee: none 的子票才可领取。
- 解决：追加 ## Answer，保存依据和资产链接，设置 Status: resolved，再在地图 Decisions so far 追加标题链接和一句话摘要。
- Frontier：扫描子票，按文件编号取 open、未认领且全部依赖 resolved 的问题；ruocun-discovery 提供 frontier.py 查询和依赖图输出。
- 地图是索引；开放票通过子票查询，决策细节只放对应子票及资产。
- 研究分支保存在本地，不推送、不创建 PR、不合并；研究报告可由主会话收录到地图目录，并保留原分支和提交指针。
- HITL 原型等待用户真实反馈；代理不能代替用户完成体验验收。

## Git 与 worktree

规格、任务票、ADR、对应表和验收记录均提交到 Git。
创建后续 worktree 前，先提交其需要读取的工程记录。

本项目未配置 triage 标签映射；以上为任务流转状态。
