# 终端输入与普通入口独审

候选 `31bc718`、回执固定 `d16d70f` 及共享接线 `a58197f` 已独立应用至 `d7370f0`，并包含先前已审的排队清理修复。当前受审产品接缝剩余阻断 0，18 仍为 claimed。

逐项对照冻结 `src/tui/app/App.tsx:483–491,1102–1125,1295–1357`，文本粘贴规范化裸 CR/CRLF、超过 280 个 UTF16 单位或 6 行折叠、显式 Enter 才展开提交、Esc 优先取消排队且保留当前轮、暂停后仅空草稿回填、Down 清空回填、2 秒双 Ctrl+C 退出的语义均落实。组合字、国旗和 ZWJ 的光标删除复用当前锁定 wcwidth 的 grapheme API。

普通 runtime 将 `escape` 接同一 broker，审批由原独立答案缓冲与审批锁串行接收。没有新增终端 reader。状态监听从同一 scheduler 读出状态与排队数量。取消仍走已有调度器和当前事件，输出仍走同一 broker 输出锁。审批界面优先消费 Esc/Ctrl+C，保留原用户草稿。

独立复跑原 `test_n24_terminal_input.py`、`test_n1_input_broker.py`、`test_n1_runtime_tty.py` 与 `test_n1_session_scheduler.py`，**16 passed in 5.67s**。受影响产品与新来源测试 Ruff 通过，broker、runtime、tui 共 4 源文件 mypy 通过。见 `raw/n24-review-terminal*` 的实际回执，均 exit 0、scan_hit=false。

命令继续使用明确白名单与合成 HOME/config/TEMP，从独审树加载源码，根 venv 提供锁定依赖，使用 `-I -B`。此次没有修改产品或扩建测试。真实 Windows Terminal 的 IME 候选、连续缩放、可见 scrollback、退出 mode/cursor 恢复，以及图片粘贴等后续子路径按原票保留待验。本受控 TTY 结果不能供 18 整票结题或替代 77 人工体验。
