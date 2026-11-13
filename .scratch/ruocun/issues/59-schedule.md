# 59 — 系统定时来源路由与Windows不支持边界

Type: task
Mode: AFK
Status: resolved
Scope: reduced
Assignee: /root/n24_permissions
Branch: codex/b07-platform
Parent: [完整迁移规格](../spec.md)
Blocked by: [14 — 前台Shell输出及整个受管进程树可取消](14-shell.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

按W3取消Windows Task Scheduler/dispatcher补齐：Windows的系统级Schedule/Cron入口明确报告本轮不支持，不创建任务或以会话内loop冒充；会话内loop若保留，只在程序运行时有效。保留来源其它平台的crontab路由及参数/权限语义，平台实机结果单列未验。

范围依据：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)。取消后端不代表本票完成；不支持分支、工具定义、CLI路由和支持说明仍待实现验证。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-582](../module-map.md#mm-582)、[MM-625](../module-map.md#mm-625)、[MM-700](../module-map.md#mm-700)、[NEW-05](../module-map.md#新增适配层候选位置)。

## 共享接口与并行

接口领域：平台。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WIN-06](../acceptance-matrix.md#win-06) — 系统定时：Windows明确不支持，不向系统注册定时任务；会话内loop不冒充系统定时；支持平台与未验状态准确说明。
- [x] [TOOL-Schedule](../acceptance-matrix.md#tool-schedule) — Schedule：保留来源schema及支持平台add/list/remove路由；Windows准确拒绝不支持，失败形成可配对结果，不以空清单/成功返回伪装已执行。
- [x] [TOOL-CronCreate](../acceptance-matrix.md#tool-croncreate) — CronCreate：支持平台保留来源持久定时语义及schema；Windows明确不支持，不创建本地替代调度或返回成功。
- [x] [TOOL-CronDelete](../acceptance-matrix.md#tool-crondelete) — CronDelete：支持平台保留来源按清单序号删除；Windows明确不支持，失败结果可配对。
- [x] [TOOL-CronList](../acceptance-matrix.md#tool-cronlist) — CronList：支持平台保留OS任务清单；Windows明确不支持，不用空清单表示查询成功。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

[本票独审](../../ruocun-next24h/evidence/review/b07-reflection-platform-final-review.md)与[集中交付](../../ruocun-next24h/evidence/batch-07/integration/README.md)已通过。

实现候选已完成，等待主协调普通入口与独审。见[59来源与边界证据](../../ruocun-next24h/evidence/batch-07/n59/README.md)：4项来源/必要实际确认及Ruff/Mypy通过。Windows实际动作明确拒绝、后端零调用；其它平台仅合成命令端口验证，真实系统crontab与实机触发未验。读失败不覆盖旧表、写入结果未知不重放；不自行resolved。

## Comments

- 2026-11-10：用户按表缩减W3；本轮Windows系统定时后端移出，来源其它平台路径及显式不支持行为仍是本票交付，状态和未验结果不变。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-12：用户授权启动[批次07](../../ruocun-next24h/batch-07.md)，已核真实前置，本票claimed，尚无通过结论。
