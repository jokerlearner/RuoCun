# 27 工作树和影子检查点独立核验

固定候选 `5b2792e`，独立工作树的 `src`、`tests` 与候选一致。核对 27 票 RUN-08/REC-13 子路径、冻结 `src/agent/worktree.ts`、`src/session/checkpoint.ts`、`src/index.ts` 的 rewind/restore 分支，以及 ADR-0009/0013/0015。

| 独立回执 | 实际结果 |
| --- | --- |
| `b02-review-worktree-guard` | 3 passed in 9.87s。真实合成 Git 仓库内，未提交改动及新提交均要求显式丢弃，已脱离分支的工作树即便传 discard 仍保留，影子恢复遇未管理的二进制目录内容拒绝覆盖并保留原字节。 |
| `b02-review-worktree-static` | Ruff 通过。 |
| `b02-review-worktree-types` | mypy 通过，6 源。 |

以上命令退出码均为 0，使用白名单、合成 HOME/TEMP，敏感扫描无命中。普通入口 `/rewind 2 code` → `/restore` → `/diff` 沿用主协调候选的 1 passed in 7.26s，原 Git HEAD/index 实际保持。影子 Git 超时后禁止同对象再执行沿用实现者 4 项定向回执；持久锁跨对象边界按下述源码核对。

普通入口从活动 `ctx.cwd` 生成获批 Bash 计划，实际派发验证计划和 cwd 相同，受管 runner 的清单继续携带该 cwd。恢复先暂停并等待前台落定，拒绝活动隔离工作树或仍在运行的后台任务。影子 Git 在独立对象、索引和引用中保存恢复前快照，经未管理路径检查后执行两树更新。Git 写结果不明时保留 `ruocun-operation.lock`，重新创建 Checkpointer 也需要取得同一独占锁才能写。普通入口保留未决 SQLite 工具意图，令会话阻塞以便核实。

27 接缝通过独立审查，可供 41 消费。41 的子代理隔离和集成验收仍由对应任务完成。
