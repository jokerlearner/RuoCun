# 验证含 WAL 修复的 SQLite 运行环境

Labels: wayfinder:task
Mode: AFK
Status: resolved
Assignee: /root/fix_d19_identity
Branch: impl/d19-sqlite-identity2
Worktree: .worktrees/i19
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [用最小 Python 实验验证取消与崩溃恢复契约](05-runtime-recovery-experiment.md)

## Question

能否在 Windows 的隔离 Python 环境中获得已修复官方 WAL-reset 问题的实际 SQLite 运行库，并用同一组事务/恢复探针及分发检查验证它，作为最终技术路线的候选？

## 依据与边界

[运行时探针](../experiments/runtime/README.md) 的实际 sqlite3.sqlite_version 为 3.45.1。
[SQLite 官方 WAL 文档](https://www.sqlite.org/wal.html) 说明该并发缺陷的修复在 3.51.3 及以后，并提供 3.44.6、3.50.7 的回移修复。是否含修复应核对具体版本/构建，不能仅用一个数值下限排除回移版本。
本轮未触发或重现该罕见缺陷，也未核实 DAO 的 Node/Bun 实际 SQLite 版本；本票不作原版受影响的断言。

## 完成条件

- 在项目隔离环境准备至少一个有官方依据的已修复候选；保留当前探针环境，不替换用户全局 Python。
- 记录 Python 解释器、实际 sqlite3 runtime、SQLite source id/compile options、连接/VFS与驱动；Python 版本号本身不能代替实际库版本。
- 复用本票来源的真实故障注入、owner/epoch、三次独立恢复进程及 WAL/FULL 检查；保留失败和能力差异。
- 验证正常并发读写与 checkpoint 边界；普通压力测试未触发已知罕见缺陷不构成已修复证据，修复依据来自版本/源码及构建来源。
- 说明标准库内置库、替代绑定或受控分发各自的部署影响，供后续路线决定；不在本票锁定最终产品依赖。
- 将 wheel/standalone 的实际运行库版本检查传递给发布门禁，防止构建环境与安装产物不同。

## Assets

- [取消与崩溃恢复实验及环境记录](../experiments/runtime/README.md)
- [SQLite 官方 WAL 文档](https://www.sqlite.org/wal.html)

## Comments

- 2026-11-05：本轮核验官方资料后建立；本票尚未执行，不把本机 3.45.1 当作已确认的产品依赖。

- 2026-11-05：主代理按已满足的前置领取，分派给/root/decision_19_sqlite；用户已授权独立worktree及已确认入口上的TDD。

- 2026-11-05：首次merger复核发现launcher/事务worker身份绑定证据不足，未接受合并；Status保持claimed，交fresh修正子代理补证与复测。候选b1b15b5和助手merge60404b8保留，复核记录见[首次复核](../../ruocun/integration-evidence/d19-first-review/README.md)。

- 2026-11-05：首次修正worktree在checkout历史长路径证据时触及Git Windows路径限制，尚未开始执行；保留该目录，改用较短的.worktrees/i19。修正票同时补独立worktree可读取性，不更改全局Git/Windows设置。

## Answer

[SQLite候选实验](../experiments/sqlite-runtime/README.md)最终0419c42经fresh merger接收为564f8ca：独立2passed、12/12、21恢复、35运行库清单、34受管进程/Job0。8次强杀对同句柄PID+创建时间与spawn/ready/runtime绑定，立即确认退出才恢复。原1033成员/原1029审计和身份red174已逐字节归档，长名worktree可checkout、最长相对路径146。原探针/全局3.45.1未改。仅确认官方3.54.1+stdlib为可验证候选，产品依赖/分发未定。[独立复核](../../ruocun/integration-evidence/d19-identity-review/README.md)。
