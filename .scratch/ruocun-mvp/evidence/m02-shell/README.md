# M02 前台Shell候选证据

基线：`e672f7201a9db371c1bcf7b7cb22fa9cf5e707ab`。本记录随候选代码一同提交；尚待独立复核，不提前结题。

冻结来源：`dao-f17e189-7ac654a0dc06/source.zip`，SHA-256与源文件、候选源码、实际安装文件及wheel字节绑定见[provenance.json](provenance.json)。原始`exec_shell.ts`、`exec_shell.test.ts`和`safe_env.ts`保留在[raw/source](raw/source)，不是从Python实现倒推的预期。D17/IPC已验证Job路线只读参考，没有重新运行历史探针。

实现导出`execShellTool`（Bash，exec/required）与`cleanupDbBackups`。handler为`async(args, ToolContext)->str`，使用共享Event。Windows argv固定系统Windows PowerShell 5.1，`-NoLogo -NoProfile -NonInteractive -InputFormat Text -OutputFormat Text -EncodedCommand`；输入命令按UTF-16LE编码，控制台及原生子进程管道使用UTF-8。命令语法为PowerShell；保留七工具首版的command/description/background字段，不支持旧沙箱绕过参数。

受管树以`CREATE_SUSPENDED`启动，进入带`KILL_ON_JOB_CLOSE`的Job后才恢复；helper及工程子进程均隐藏窗口。Event取消时终止Job，绑定成员句柄并等待signaled及Job空，再返回中断。正常Shell退出也回收遗留子孙，避免后台泄漏及继承输出管道悬挂。stdout/stderr分开收集，共10MiB内存上限；超过上限终止命令并提示；超过16000字符的结果保留头尾并落盘到工作目录`.ruocun/spill`。来源环境敏感变量过滤保留。

## 来源断言与差异

| 来源位置 | 本票对应与结果 |
| --- | --- |
| exec_shell.test.ts:13–21、30–33、42–60 | stdout/exit、非零退出反馈、早退保留pending、取消，已迁移 |
| exec_shell.test.ts:64–81 | 父Shell退出、孙进程继承管道不永久阻塞；在Windows适配文件复用相同独立预期 |
| exec_shell.test.ts:158–223 | sleep阈值、短sleep/复合命令、内联小文件阻止、连续三次提示及reset，已迁移；Windows复合命令仅改方言分隔符 |
| exec_shell.test.ts:227–274 | 崩溃文字/退出码重置headless计划，137不重置、非headless/无gate正常，已迁移 |
| exec_shell.test.ts:279–354 | 主数据库/边车执行前备份、保留首次副本、无引用不备份、内联路径/扩展名前缀，已迁移；Windows盘符和引号空格做必要适配 |
| exec_shell.test.ts:382–386 | 名称、exec、required，已迁移 |
| 后台、后台反馈清空与Ctrl+B用例 | ADR-0011后置，background=true明确拒绝并且不清空pending，不运行来源后台断言 |
| exec_shell.test.ts:84–142包管理自动恢复 | 首版取消后不暗跑新Shell副作用，输出需另行审批`dpkg --configure -a`；主协调已确认必要可见差异。不声称来源自动恢复/重试两例通过 |
| exec_shell.test.ts:359–379备份清理 | 首版保留备份并在创建回执提示人工清理。仅靠路径无法证明当前文件仍归本进程所有；不递归扫删用户备份，不声称来源删除用例通过 |

`test_exec_shell.py`为25项来源迁移/已确认差异用例；`test_exec_shell_windows.py`含来源继承管道适配，以及新增的真实子孙退出、保留用户备份两项首版必要确认。共28项Python用例，不等同于来源38项全通过，也不等同于完整Shell/后台框架通过。

## 实际结果

| 检查 | 结果/原始记录 |
| --- | --- |
| 首轮red→green | 缺少exec_shell导入失败→前台最小断言通过；[raw/m02-red-foreground](raw/m02-red-foreground)、[raw/m02-green-foreground](raw/m02-green-foreground) |
| 来源护栏red→green | 15 failed/10 passed→25 passed；[raw/m02-red-guards](raw/m02-red-guards)、[raw/m02-green-guards](raw/m02-green-guards) |
| Windows已捕获缺陷复验 | 首次继承管道检查发现Job计数归零但进程对象尚未signaled，原失败保留；绑定成员句柄并等待后同一复现3 passed。[raw/m02-windows-adapter](raw/m02-windows-adapter)、[raw/m02-windows-treefix](raw/m02-windows-treefix) |
| 最终定向回归 | **28 passed in 92.26s**；[raw/m02-final-tests](raw/m02-final-tests) |
| 定向Ruff/mypy | exit 0；mypy 3源文件；[raw/m02-final-ruff](raw/m02-final-ruff)、[raw/m02-final-mypy](raw/m02-final-mypy)。初次mypy的POSIX平台类型错误保留 |
| 标准包构建/安装绑定 | wheel和sdist构建exit 0；非editable安装，三个产品文件与wheel/源码逐字节相同，hash见provenance；[raw/m02-final-build](raw/m02-final-build) |
| 最终字节收尾 | 去掉Windows叶子文件末尾多余空行后重新构建、直接安装最终wheel；同一Windows适配三例3 passed in 4.40s；[raw/m02-final-build-r2](raw/m02-final-build-r2)、[raw/m02-final-wheel-install](raw/m02-final-wheel-install)、[raw/m02-final-wheel-smoke](raw/m02-final-wheel-smoke)。28项行为回归前后仅此空白字节变化，最终hash以provenance为准 |
| 证据收录 | 首次在回归尚运行时收录提前失败，只读证据缺失，没有产品行为变化；失败保留[raw/m02-capture](raw/m02-capture)。随后重试成功 |

所有运行使用本worktree私有311 venv、固定18包hash闭包、清空环境的外层启动器及`tools/run.py`；HOME/配置/tmp/cwd/命令均为合成范围。各`command.json`的`sensitive_match=false`。原始字节通过本目录`.gitattributes`的`raw/** -text`保留。

取消最小确认在返回后观察Python子进程和孙进程保留句柄均为signaled；最终一组为PID54964/56632，`wait_states_after_handler=[0,0]`，所属进程仍运行列表为空。此处是历史观察身份，不用于后续按PID杀进程。已启动命令均joined，未创建后台runner。raw/resource-receipt-*保存真实观察。

未验：真实账户/付费模型0次；Windows Terminal视觉/缩放和人工体验not-run；Linux/macOS仅保留进程组实现设计，未实机验证；完整后台/持久runner/沙箱/Hook恢复框架均不属于本票。主协调负责审批、registry/loop/CLI、公共对应表MM-636/MM-637及TOOL-Bash首版部分状态，不能将母案例族标全量通过。
