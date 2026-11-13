# N24 共享接缝

18 的 WT-04 要求 Esc 先处置等待输入，再暂停活动轮。现有调度器新增 `clear_pending()`，在同一控制锁内持久化队列处置，保留当前运行信号。保存失败则失效活动代际并暂停，继续保留原错误。

复用既有公开调度器与 QueueStore 接缝，补一条必要产品接线断言。`n18-clear-pending-red` 因缺少方法失败，`n18-clear-pending-green` 的同文件 8 项通过。命令由 `tools/run.py` 使用白名单环境和合成目录启动，实际加载当前 src。真实模型与 Terminal 未执行。
