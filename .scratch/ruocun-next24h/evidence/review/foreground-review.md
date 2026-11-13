# 14 前台输出与整树取消独审

受审候选为 `84e59a9`、普通入口回调 `74d31bf` 与 CLIXML 范围修复 `270a7cc`，独审树 `4b48eba`。14 模块与普通入口接缝可集成，剩余审查阻断 0。

stdout/stderr 使用独立解码器，原始字节及诊断保留在 ForegroundResult。实际输出解码使用 BOM 与 UTF8/OEM 行内候选，非法或不完整字节明确转义。PowerShell CLIXML 仅在实际 PS 的 stderr 适用，普通 native stdout 的同名字面文本按原文保留。任意一行混用多种未知编码仍不能可靠自动判定，此候选未宣称覆盖该输入。

读取线程只把回调排入原事件循环，handler 固定本次 signal 与观察者，返回前等待进程树与 reader 收口。两个流分别发送空字符串 EOF。runtime 另以当前调度 generation 过滤取消后的输出，并各自保留账号 key 的可能前缀，完成匹配后整体脱敏。最终结果与 live 输出共同沿现有脱敏展示路径，未改已批准的执行计划。

独立复跑候选原定向与普通 TTY，共 **47 passed in 20.29s**。包含实际中文 argv/env、cmd 文件与管道、UTF8/OEM 原始字节、PS5.1 可读错误流、真实子孙进程取消后句柄与持续写文件稳定、回调数量稳定、既有安装调用方。7 个受影响源码 mypy 与定向 Ruff 通过，实际回执均 exit 0、scan_hit=false。

单一普通入口 [shell-stream-runtime.py](shell-stream-runtime.py) 沿既有 TTY 注入复核。实际 Python 命令尚未退出时，live 文本已进入 broker 输出；stdout/stderr 各拆两片的合成 key 均完整替换为 REDACTED，两流没有共用 pending 文本。正常退出观察到双流 EOF。随后真实命令派生持续写 ticks 的子进程，Esc 后本轮 paused，文件大小和回调数量稳定且没有新模型轮。CLIXML 范围修复后复跑同一场景通过。

所有验证采用明确白名单与合成 HOME/config/TEMP，独审源码和锁定依赖，使用真实自有进程并完成收口。pwsh、Linux/macOS 实机及最终真实 Windows Terminal 用户体验仍未验。15 的 runner/重连与 16/17 的后台恢复继续各自验收。
