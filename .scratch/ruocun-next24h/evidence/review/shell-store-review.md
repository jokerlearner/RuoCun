# 15 runner 存储接缝独审

受审候选 `4269e1f`，独审树 `1a43486`。当前已实现存储模块与既有调用方的定向复核通过，runner/IPC 与恢复的产品整合继续待验。

prepare_shell 在同一原子事务中检查当前 owner 的已开始 Bash intent，把该 intent.run_ref 与唯一 RunRecord 关联。相同关联允许幂等重取，其它执行身份拒绝。commit_shell_run 沿同一 owner fencing，控制 epoch 不能降低，端点更换必须增 epoch，已确认 runner 身份与终态不能改回其它状态。worker 使用原单写线程并深拷贝新入参。

工具结果提交把对应 shell RunRecord 的真实 tool_result 一同保存。随后 runner 提交状态或恢复时，已有工具结果优先，不能以恢复确认文字覆盖。Conversation 的当前 ToolRef 使用任务局部 ContextVar，旧普通工具仍走原 intent/result 公共接口，没有强制要求所有工具都准备 runner。正常恢复配对与图片投递继续复用原实现，未知结果保持阻塞。

独立复跑新存储确认与原 Conversation/worker 四文件，**11 passed in 6.10s**。4 个源码 mypy 与定向 Ruff 通过，回执均 exit 0、scan_hit=false。没有新增验证矩阵或修改产品。

此候选尚未绑定最终 runner 调用。运行中返回稳定 task id 及重连后固定确认信息是已确认的工具结果语义，manager 在身份认证并核实 start/claim 后才给该确认，unknown 保持无结果。存储负责关联与 fencing，进程/文件事实核对归 manager。完整运行态迁移及确认来源结合后续实际调用复核，当前模块结果不代表 15 整票或后台恢复已通过。
