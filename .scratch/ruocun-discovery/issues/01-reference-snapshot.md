# 冻结可复现参考快照

Labels: wayfinder:task
Mode: AFK
Status: resolved
Assignee: none
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: none

## Question

如何将更新后的 DAO 已提交内容、本地差异和未跟踪源码固定为后续迁移的唯一参照，且能在独立 worktree 中校验并恢复？

## 依据与边界

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 完整源码归档、逐文件清单、SHA-256、提交身份及 Git 差异均保存在本项目。
- 实际解包后逐文件校验，覆盖未跟踪源码。
- 参考目录保持只读；旧记录保留历史身份。
- 说明源码快照与依赖环境、运行数据之间的边界。

## Assets

- [快照材料与复现方法](../reference/README.md)

## Comments

- 2026-11-05：用户明确授权先固定参考快照，本轮完成该前置执行。

## Answer

已捕获提交 f17e189dc68a0a0a0b9937784e1b7ce29aed80eb 的当前工作区：
797 个已跟踪文件、12 个已跟踪修改、8 个未跟踪源码文件，共 805 个文件。
归档包含原始字节、逐文件哈希、HEAD/索引二进制补丁及 Git 状态。
源码树身份为 7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c。
快照只固定源码；依赖环境与运行数据边界见快照说明。

执行证据：捕获后已从归档实际恢复并核对 805 个文件的 SHA-256；从检查点提交创建独立 research worktree 后，再次通过全归档与逐成员校验。Git 的 -text 属性保证快照文件不会在 worktree 检出时被换行转换。
快照归档 SHA-256：1f8308959d8b9ac0783b6ce6ddbffe7a71cc60bc59332f309f0d62083efac078。
