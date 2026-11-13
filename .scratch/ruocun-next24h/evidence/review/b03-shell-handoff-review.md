# 批次 03 第 67 票 Shell 交接独立复核

集成候选 `5e23f00`。按原 `tests/test_n15_managed_shell.py` 通过 4 项，耗时 33.93 秒。白名单进程使用合成 HOME、配置和会话，受控真实 Windows runner、认证 IPC、SQLite 和仓外临时目录。退出码 0，敏感值扫描无命中。[独立回执](raw/b03-review-detach/command.json)

原独立实现回执的红例是真实 runner 在认证 detach 响应和确认回写之间收到旧前台取消。候选的同一用例在收到旧信号后正常移交并退出前台，重开可读取同一个 run 的原回执，`cancel_requested` 为假，命令输出和单次写入一致，真实执行完成。[原红例](../batch-03/n67/raw/n67-detach-red/stdout.bin)

按照完整规格第 233 行核对控制权。旧前台信号和 Ctrl+B 获取同一 run 的控制锁。前台取消先获控制时，之后交接因取消状态被拒。交接先获控制时，先持久标记申请再发 IPC；确认后旧信号不再取消，重复交接也由同一状态检查拒绝。无可信交接结果时保留 unknown，旧前台取消分支不主动发控制。核对了真实取消收据与 runner 丢失的原用例。Ctrl+B 重复和交接失败由源码复核，本次未新增原生故障注入用例。

Shell 接缝无阻断。终端按键接线和 Windows Terminal 体验由对应候选另验。未修改产品，未构包。
