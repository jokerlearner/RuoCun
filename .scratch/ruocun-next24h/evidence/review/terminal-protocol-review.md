# 终端协议与粘贴上限独审

独立应用 `2a6b05d`（集成 `5f19cf9`）与 `5c6dc64`（集成 `b4651ff`），审查树为 `4a9667d`。本子路径可集成，剩余审查阻断 0。18 整票仍等待所需真实 Terminal 项目。

ParserGate 沿 D06 原 `protocol.py:136–168` 在同一输入对象的锁版本 VT parser slot 前过滤，保持原 raw mode 与唯一 reader。产品自己的 renderer 等待 CPR 时交还合法 CPR，非等待时滤除非按键回包。定时 tick 沿 D06 `terminal_app.py:438–448` 推动原 flush_keys 与 key_processor。退出先取消并 await expiry 任务，再恢复原 parser slot、dispose 报告状态，原 broker 继续负责释放其持有的 input。

paste 在完整 END 前由同一路 Reports 暂存。编码计数使用最多 4096 码点片段，实际 8 MiB UTF8 字节为单次上限。跨限立即清空该次暂存，继续吞至本次 END，内部 CR、Esc 与命令文字不交按键层。可见拒收提示由同一 broker 更新，原草稿与确认队列保留。已闭合且在上限内的 paste 才一次交原 ptk parser，后续正常输入恢复。此具体平台边界按 D10 登记。

独立复跑既有 reports、terminal_input、input_broker、runtime_tty、session_scheduler 五文件，**21 passed in 5.82s**。包含原 1 MiB 样本、实际 8 MiB 多字节边界、跨限拒收、分片 END、原草稿保留和内嵌控制键不执行。4 个受影响源码 mypy 与定向 Ruff 通过，所有回执 exit 0、scan_hit=false。

产品 Git blob 为 terminal_reports.py `3718e61dfe88ac99a3c50b7daabe6af8a74d7d52`、input_broker.py `327b3c902050d0b856d2196dea46038393861516`。白名单合成环境与独审源码加载方式沿此前记录。此次未修改产品、未增加验证矩阵，也未将受控 pipe/TTY 结果记作真实 IME、连续缩放或用户体验。
