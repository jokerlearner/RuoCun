# 45 手工任务记录

冻结 `src/agent/tasks.ts` 和 `src/tools/task_{create,get,list,update,stop}.ts` 对应手工记录。`TaskCreate` 与 `TaskUpdate` 保留 `plan/auto` 能力及冻结中英说明，用现有 `persistentEffect` 落工具意图。列表和详情是读操作，`TaskStop` 仍区分立即写入手工取消与执行器确认后台停止。`TaskUpdate` 拒绝手工结算真实执行任务，允许修改其描述；这条写入只允许同一 RunRef 的两个描述字段变化，保留原运行身份、状态、授权和转录。旧记录缺真实时间时明确显示未记录。

手工任务保存于本会话原 `RunRecord`，没有执行器和事件，也不会进入 `TaskWait`。冻结 `TaskUpdate` 工具说明关于完成通知与实际行为有出入，`tasks.ts` 及 `tasks.test.ts` 明确手工完成只改变记录。先确认 SQLite 保存再修改内存，未知保存结果阻止继续写。重开按最大已保存手工编号接续，保留原状态、描述、时间和结果。按 D08 §8 与冻结 `cancelAll`，正常关闭把仍运行的手工记录保存为 `canceled`，异常丢失执行 owner 只恢复记录。当前会话已有结果未确认时保留现场。

白名单 launcher 的 `n45-manual-red` 显示原模块缺少 `TaskCreate`。`n45-manual-green` 在受控 Windows SQLite 3.54.1 上通过 45 的工具路径、重开与正常关闭，以及 40 直接邻接回归，共 4 项。`n45-manual-final` 定向复核最后的提交内容。`n45-ruff-final`、`n45-mypy-final` 为定向静态回执。未使用真实模型或终端人工操作；普通入口注册、`/tasks` 接线和独审由主协调汇总。
