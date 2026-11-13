# 15 — Shell转后台后可重连、读输出和停止

Type: task
Mode: AFK
Status: resolved
Assignee: Codex N24-B/A
Parent: [完整迁移规格](../spec.md)
Blocked by: [14 — 前台Shell输出及整个受管进程树可取消](14-shell.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

独立runner、ACL/token/run/epoch、start.claim/grant、detach与owner强杀后接管；真实close才终止。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-668](../module-map.md#mm-668)、[MM-704](../module-map.md#mm-704)、[MM-639](../module-map.md#mm-639)、[MM-640](../module-map.md#mm-640)、[NEW-02](../module-map.md#新增适配层候选位置)。

## 共享接口与并行

接口领域：平台/存储/调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TOOL-BashOutput](../acceptance-matrix.md#tool-bashoutput) — BashOutput：本票路径覆盖的子案例满足“按后台 Shell id 增量读日志并节流；不是阻塞等待；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-KillShell](../acceptance-matrix.md#tool-killshell) — KillShell：本票路径覆盖的子案例满足“请求终止已启动 Shell，取消请求不等于退出确认；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [REC-10](../acceptance-matrix.md#rec-10) — runner握手与启动认领：本票路径覆盖的子案例满足“start.claim排他，可能grant后保守unknown；接管不重启副作用；终态receipt身份校验”。
- [x] [WIN-02](../acceptance-matrix.md#win-02) — 受管进程树：本票路径覆盖的子案例满足“身份核验、有限force收口、真实close才canceled；keep-background独立生命周期，无多余可见窗口”。
- [x] [WIN-03](../acceptance-matrix.md#win-03) — IPC与ACL：本票路径覆盖的子案例满足“已认证且最小访问范围可实证；HMAC不替代ACL，进程身份/句柄继承可查”。
- [x] [RUN-10](../acceptance-matrix.md#run-10) — 取消终态：本票路径覆盖的子案例满足“先canceling，真实close/受管后代止写后canceled；未知保持unknown；不回滚已发生副作用”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

独立runner、普通入口、持久关联、同run接管和真实取消已集成。来源及必要平台回执见[实现记录](../../ruocun-next24h/evidence/n15-managed-shell/README.md)，真实owner强杀与失败保留见[源码独审](../../ruocun-next24h/evidence/review/managed-shell-review.md)。固定N24-r2的168成员严格绑定、纯安装默认模块角色及真实接管/停止见[纯安装独审](../../ruocun-next24h/evidence/review/pure-r2-review.md)。r1全量的4项夹具路径失败修正后原4项通过，1445项旧通过按ADR-0015及纯换行证明复用。本票Windows路径resolved，16/17及整体体验继续按各票验收。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-11：14独审及普通入口已通过并集成，领取15。B独占managed_shell/runner/poll/kill及必要进程接缝，A独占Windows私有认证IPC，root独占唯一存储、公共入口与上下文接线。完成状态等待实际detach/reconnect/停止与独审。
