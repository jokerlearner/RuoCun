# 10 实际 Edit / Write 崩溃恢复

本片从已确认的源行为候选 `2fcdbf1` 运行。用合成工作区、官方 SQLite DLL 固定归档和真实
Conversation/StorageWorker。模型响应以脚本传给现有 run_turn request 参数，读取、权限裁决、
Edit/Write handler 和持久化均走产品代码。Journal 包装器定位意图/结果确认前后，真实
atomicWrite 返回后的测试包装器定位文件副作用。父进程读取已发布的切点标记后终止并等待
自己启动的子进程，再以三个独立进程重开同一会话。

| 切点 | 实际工具 | 文件字节 | 三次恢复的状态 |
| --- | --- | --- | --- |
| intent 前 | Write | 原内容 | 无工具记录，补未执行配对 |
| intent 确认后 | Edit | 原内容 | outcome_unknown，禁止继续 |
| 文件原子替换后 | Write | 新内容 | outcome_unknown，禁止继续 |
| result 提交前 | Edit | 新内容 | outcome_unknown，禁止继续 |
| result 确认后、消息配对前 | Write | 新内容 | result_committed，补齐同一结果配对 |

每个恢复过程核对文件原始字节和独立派发/写入计数。未知结果换调用 ID 仍拒绝新意图。
result 确认后场景在第三次重开先验证单一已补配对，再将同一调用 ID 和最终参数送入真实
前台循环，取得已提交结果，派发/原子写入各保持一次。intent 前场景在第三次重开通过
源 execute_durable 的 SQLite query_only 断言验证真实意图提交错误，派发数保持零。
prehook 属于后续 Hook 路径，证据仅覆盖当前前台文件操作。

`n2-edit-recovery-first` 与 `n2-edit-recovery-green` 各 5 项通过。后者包含上述重复调用
和 SQLite 拒绝验证。五个初始子进程均已终止并回收，15 个重开进程均正常退出。定向 Ruff
通过。源码由白名单启动器显式导入本树，子进程消费与 pytest 相同的包路径。固定归档、
产品接缝、fixture 和原始输出 hash 见 `recovery.json`。本片不涉及模型 API 或发布包构建。
