# D18 首次独立复核未接收

候选：`14fcde35586374480c8ac917a2cfb4dce638e8e3`，分支`impl/d18-io`。
独立merge：`75265981726fb7ea2f29b646f9960fa7a2120b8c`。
报告提交：`3c8b969170f942da98cd17c4f421dd2f26e8d8ce`，本地分支`merge/d18-io`、worktree`.worktrees/m18`。

该提交中的`.scratch/ruocun/integration-evidence/d18/README.md`保存完整报告；同目录归档134文件，SHA256为`d306080b1a76567988920c282de66c69b8488d49d5ee160ba59c17e018f25704`。分支保留，修正分支应带入这些原始材料。

原6项独立复测通过（5.21秒），874原始文件和19轮快照校验通过。静态审查发现：已经pending的管道I/O在取消失败、取消等待超时或wait异常时，会展开局部OVERLAPPED/buffer并关闭event，缺少确认完成前的资源所有权。未在本轮真实驱动中触发该异常。

本次不接收为D18技术完成；保留原证据，交独立修正代理并再次独立复核。不能把原测试绿替代异常路径的资源安全。
