# 12 前台工具批

冻结源及原始记录摘要见 `source.json`。批审批接缝的单独验证见 `approval.md`。Python 3.11 私有 venv 通过外层白名单启动器显式导入源码，pytest、Ruff 和 mypy 均为定向检查。无真实或付费模型调用。

| 来源 | 对应验证 |
| --- | --- |
| `src/tools/execute.ts:33–34,230–279` 与 `execute.test.ts:127–165` | `test_source_read_group_cap_and_write_barriers_keep_results_in_request_order` 验证 8 个在途调用、写独占、完成顺序与交付顺序不同、读错误隔离、TodoWrite 修改原上下文 |
| `src/tools/execute.ts:239–257`，RUN-05 | `test_source_all_settled_drains_started_tools_before_propagating_storage_failure` 验证结果提交失败时等待在途工具落下自己的结果，下一屏障不进入 intent |
| `src/tools/execute.ts:90–105` 与 `src/agent/loop.ts` 图片投影、模型请求 | `test_real_read_images_commit_in_call_order_before_publishing_batch_boundary` 用真实 Read 读取合成 PNG/JPEG/文本，核对同一最终 raw、结果图槽、按调用顺序投影和已保存边界 |
| `src/tools/execute.test.ts:171–187` | 原 `test_failed_exec_skips_later_effects_in_same_batch` 追加后续 Write 与 Read，验证失败后跳过 Bash/Write、保留 Read |
| 09 规划入口和 10 REC-05 | 原 plan 组内用例改用预批，同批进入 plan 后写仍被即时硬门挡住。原 5 个真实 Edit/Write 恢复子例回归，保留已知结果复用及未知结果停机 |

- `n2-batch-executor-red01` 原顺序派发峰值 1，来源要求 8，1 failed。
- `n2-batch-executor-green03` 原 loop、权限装配、图片持久化及本票定向，34 passed。
- `n2-batch-recovery01` 原 REC-05，5 passed。
- `n2-batch-executor-ruff01` 保留首次导入格式失败，`n2-batch-executor-ruff03` 和 `n2-batch-executor-mypy02` 通过，mypy 3 个源文件。
- 合入稳定主线 `f2c5998` 后，本票源文件与测试字节一致。 `n2-batch-executor-merged01` 加入已有 Read 图片直接断言，共 37 passed，`n2-batch-executor-merged-mypy01` 通过 3 个源文件。

独审回修复用原 allSettled 用例。旧单调用审批接口的首个审批异常与后续已派发 Read 的结果保存失败同批发生。旧版会吞掉后者，`n2-batch-settle-priority-red01` 未抛预期的 StoreError。修复后先收齐在途回执，再传播存储异常，保留已提交的另一结果，跳过下一写屏障，且没有生成错误的未执行配对。`n2-batch-settle-priority-green01` 为本票 4 项通过，同一源文件的 Ruff/mypy 通过。

## S-05 冻结失败文本 oracle

`n2-batch-s05-oracle01` 仅从经 archive 校验的两个冻结文件提取 formatter 和 predicate，在既有 Node 上对合成退出状态求值。原测试的 `[exit 1]` 可识别，但冻结实际 formatter 的 `[exit 1,运行 0s]` 和 `[已中断,运行 0s]` 未识别，零退出仍判成功。RuoCun 保留既有修正，实际格式触发失败屏障。此回执只确认源文本与判定差异及本票屏障语义，未运行故障命令或验收冻结 UI/审计。

工具持久化沿用 RuoCun 的 write/exec 副作用标记。plan 工具沿来源参加安全组，并在原 ToolContext 应用会话内状态。批次统一由业务任务保存原序消息，工具各自的 intent/result 等待存储回执。普通入口、打包和独审由集成验证。
