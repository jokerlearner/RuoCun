# 46 Monitor 候选

Monitor 的冻结来源为 `src/tools/monitor.ts`、`monitor.test.ts`、`agent/tasks.ts`。工具保持 exec/required、延迟声明、危险命令确认、stdout 按行合并及 persistent/超时参数。执行通过现有 ShellExecutionPlan 和受管进程树。Windows 使用原 Job 绑定、终止和进程句柄等待。取消先持久 `canceling`，实际返回后记录终态，来源发 kill 后立即 finish 的问题按已批准 D08 修正。

`TaskManager.launch_monitor` 以真实 kind=monitor 保存原 Monitor 授权及独立执行 signal，父工具回执保存后才运行命令。行事件以固定 run 和单调输出序号进入既有后台事件流。接到 owner 丢失的记录只读取历史，不创建新脚本。后台事件及 TaskStop 复用原接口，进程树异常或输出事件保存不明进入 unknown。

`b05-46-red` 保存缺少产品 Monitor 的红回执。`b05-46-green` 暴露 Windows CRLF 产生尾部回车，修正行归一。`b05-46-final` 使用受控 SQLite 和真实 Job，通过两行加未换行尾段、persistent 忽略显式1000ms超时、TaskStop 后心跳止写和普通1000ms超时。`b05-46-static` 与 `b05-46-mypy-final` 定向通过。普通入口、重开与独立审查结果另行补录。

## Owner 丢失后重开

`tests/test_b05_monitor.py::test_monitor_owner_loss_is_interrupted_without_restart` 真实启动受管Monitor并取得批量stdout事件后，由夹具仅退出自己的产品owner（`os._exit(0)`）；真实Job关闭使合成心跳停止。随后新进程打开同一受控SQLite，RecoveryController判interrupted，TaskManager只加载原run的monitor状态和已保存输出；前后两次等待均无新心跳，不创建第二个脚本。`raw/b05-46-owner-fixed` 为1 passed / 1 deselected，scan_hit=false。

初稿曾把批量消息误作单行比较而失败；按来源按行批量语义，改为检查该消息splitlines含实际合成行，未放宽运行身份/重启判定。产品候选9aadb49f，重开用例随954387e9（主线等价3eb29adc）交接；独审与普通CLI结果由主协调另记，不将本条等同会话退出后持续观察。
