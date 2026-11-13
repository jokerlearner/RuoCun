# 15 Windows IPC 模块独审

受审候选 `ee00955`、内部角色分派 `7d6defa` 与 owner 退出修复 `cdba19b`，独审树 `5eae20b`。当前 transport 模块可供 runner 集成，15 完整启动、授权、收据与恢复仍待整合复核。

实际管道使用当前 SID 独占 DACL，读取并严格核对；首实例、拒远端与不继承句柄由创建参数落实。每连接随机挑战，请求和响应分别用 capability HMAC 绑定版本与对应正文。客户端核 OS server PID，server 核 OS client PID 与 owner 的一层或两层父链、实际创建时间。中间祖先进程未另作映像签名验证，结论限定为已实现的 OS ancestry 边界。

绝对三秒期限覆盖公开操作，取消预留时间沿已批准 D18 路线，没有延长期限。原生提交前强持有 OVERLAPPED、buffer、event 与 handle；ERROR_IO_PENDING 后仅在实际完成核实后解除持有。若完成未确认，helper 最外层 finally fail-stop，controller 持实际进程 HANDLE 等待退出，未确认则保留句柄并阻止竞争 transport。异常返回本身没有被用作原生 I/O 已停止的证据。

候选自行复现的 owner 死亡后旧 helper 留存，已通过持有实际 owner HANDLE 并核创建时间修复。空闲 connect 的确认取消完成后检查 owner 存活，再退出并释放端点。若仍有未确认 pending，继续走 helper fail-stop，未提前释放其原生 I/O 材料。

独立原四项通过；补丁后复跑同文件最终 **5 passed in 7.24s**。实际覆盖 SID DACL、匿名拒绝 5、Unicode 帧往返、错误 HMAC/server PID 后继续服务、首实例冲突、精确关闭后端点不存在 2，以及 owner 退出后真实 helper HANDLE signaled。997 后提交边界中断复用 D18 原复现，证明 buffer/OVERLAPPED 保持到 helper 自身 fail-stop，controller 仍存活。它没有被描述为真实坏驱动已验。

另 [ipc-role-entry.py](ipc-role-entry.py) 复用原实际往返用例，将 helper_command 改为显式 source override 的 `cli.main` 内部角色分派，实际通过。此结果属于 source CLI 角色接线，实际默认 `python -I -m ruocun` 与固定包安装由最终仓外出口验证。

IPC 单模块 mypy 与受影响文件 Ruff 通过。初次把尚未到达的 shell_runner 角色模块一同纳入 CLI mypy 时出现两项缺模块/Any 返回错误，原回执保留，未虚填整体 CLI 静态通过。所有实际命令白名单、合成 HOME/config/TEMP，scan_hit=false。回执仅含经核对的安全结果，没有 capability 原值。
