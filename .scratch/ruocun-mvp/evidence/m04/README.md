# M04 首版独立复核

当前技术结论：M01/M02及M03产品独立审查通过，最终产物为`1ad72d6`的r2；仓库外七工具、拒绝、正常重开、版本/帮助、固定SQLite及SIGINT确认已通过。主协调负责最终全量、五入口和公共对应表/矩阵收口；真实模型及真实Windows Terminal体验仍待验，不标人工accepted。

审查者 `/root/mvp_review`，独立分支 `codex/mvp-review`；初始基线 `e672f7201a9db371c1bcf7b7cb22fa9cf5e707ab`。不编写产品或新测试，按 ADR-0009/0011读取冻结 DAO 来源并复跑既有断言。真实账户/模型费用调用0次；真实 Windows Terminal 视觉、缩放和人工体验未验。

证据最初保存在本审查树`integration-evidence/m04-review`，后按主协调要求迁至当前`evidence/m04`；历史raw中的argv按运行当时原样保留。仅移动本审查者新建证据，没有移动旧研究、探针或异常对象。

原始CRLF及pytest失败输出里的空白行按字节保留，不为格式检查改写日志；非raw证据单独执行Git空白检查。27份工程回执的敏感匹配均为false，常见凭据模式扫描0命中，见`scan-final.json`。

## M02：通过，可集成

候选 `8b76ee125f70496010b30bec618ac6bda34f9215`，独立合并点 `67565ec0fe1bc7fb886942a9b266ce20f9980c3f`（含先审 M03 的 `ec38bc8`，M03 本身尚未通过）。读取冻结 `exec_shell.ts`、`exec_shell.test.ts`、`safe_env.ts`及三个候选产品文件；来源归档 SHA256 已核对为 `1f8308959d8b9ac0783b6ce6ddbffe7a71cc60bc59332f309f0d62083efac078`。

Windows 受管树采用 suspended→Job→Resume，取消及父进程正常退出均回收所属子孙；Job计数及保留句柄均确认退出后才报告。来源环境脱敏、sleep/inline/数据库备份及pending写入护栏保持。后台、取消后不自动执行包管理修复、保留数据库备份的可见差异沿实现记录，不声称来源38项全部通过。未发现本子范围剩余阻断。

通过私有 CPython3.11.9 venv、外层清空环境启动器及 `tools/run.py`，合成HOME/config/TEMP；按18包哈希锁离线安装。独立构建 sdist→Windows wheel并非editable安装，三个M02文件的源码、wheel成员及实际安装字节一致，且与实现者候选provenance匹配，详见 `m02-provenance.json`。

既有两测试文件复跑 **28 passed in 91.32s**。真实取消的子/孙进程句柄均signaled，`wait_states_after_handler=[0,0]`，见 `m02-resources.json`；PID仅历史观察，不用于后续操作。命令全部joined，结束时自有工程进程0，见 `processes-after-m02.json`。

原始命令与输出保存于 `raw/review-m02-*`，工程回执全部exit0/scan_hit=false。准备环境的两份收据一并保留。原始字节使用 `raw/** -text`。

## M03：发现与返修中

最初候选 `ec38bc809108558c62976e21e1c865cc8ce8190b` 的只读审查发现：loop重建assistant丢失已有客户端所需 `reasoningContent`/`responseItems`，README账户示例缺 `version:2`，intent确认后缺取消检查。均已交回原实现者；`674a2bc` 已静态确认修正，等待集成产物复跑。未知slash命令本地拒绝随后由 `d31e5e4` 修正，待最终核查。

持久化读取实际StorageWorker/owner/revision契约，使用同一串行线程；意图确认在handler之前，已开始但异常的写/exec留下未决并停止；正常恢复只补消息配对且不重放。最终运行与安装证据待M01/M02完成后补充，不把只读流程核对或缺工具阶段的局部测试算为完整首版通过。

## M01：回修后通过，可集成

最初候选 `bc6161f4b7204bab88f001d442f0f9499ac5ed2c` 的独立已安装产品运行 **96 passed in 0.73s**。只读审查发现Windows junction可能被当普通目录递归；在仅含合成workspace/outside的最小确认中，`DirEntry.is_dir(follow_symlinks=False)=true`、`is_symlink=false`，无外部审批的Glob/Grep实际读出了outside标记，形成P1。原结果及脚本保留于 `raw/review-m01-junction-boundary-01` 和 `junction_boundary_confirmation.py`，未构建故障矩阵。

原负责人回修候选 `88fc474dd7dbf47b31c9fd882ed8ce03d6066fce`：唯一工具变化为递归时跳过Windows reparse目录，显式指定外部root仍需审批。复用同一确认，Glob/Grep均无匹配；受影响的两文件 **29 passed in 0.25s**。首次绿信号输出按系统编码写出，原字节保留；随后仅以`-X utf8`重跑同一确认，清晰结果见 `raw/review-m01-junction-fixed-utf8-01`。原96条其余部分不重复运行。

已绑定固定wheel SHA256 `cd5da4d3721cc0c12bb6dd1491029b5bfbe1c4ef2094589d6cbfb22cdc8de54a`，所有64个已跟踪包成员与审查源码逐字节一致，详见 `m01-fixed-provenance.json`；非editable安装成功。路径边界、读前保护、原子写、schema/registry、六工具子范围未发现剩余阻断。

## M03：完整入口首次运行的实际失败

安装上述完整候选后，`review-m03-loop-product-01`为 **1 failed / 8 passed**：8条循环来源语义通过，七工具/正常重开确认尚未发HTTP即因`AtomicFileError`退出71。`review-cli-cancel-01`同样在请求前退出，SIGINT未发出，因此此回执不能证明取消失败或通过。

最小合成异常栈 `review-m03-storage-start-trace-01` 显示：StorageWorker factory→DurableStore.open_or_claim→PrivateDirectory.__enter__:414固定ancestor→_open_directory_pin:378，Win32 2。合成HOME只存在`.ruocun/runtime`，`sessions/<scope>`父目录尚未创建；这与运行库或已有DACL拒绝不同。已反馈主协调在组合根准备父层，07叶子未修改，未运行旧探针。原失败及最小栈均保留，等待原负责人回修同一product确认。

## M03最终回修与r2独立运行

`3184953`只在组合入口调用既有`ensure_private_dir`准备会话的两层父目录，对既有ACL只核验，未改07叶子。安装该版本后真实localhost请求已到达，隔离子进程中的线程`signal.raise_signal(SIGINT)`触发实际runtime handler，CLI退出130、信号后0.031秒返回、保存revision3。不能把程序内SIGINT适配确认说成真实Terminal按键体验。

`1c6b2e1`收口NaN/Infinity等非标准JSON的历史清洗。最终Spec轴发现来源同批Bash失败屏障遗漏，交回原负责人以`1ad72d6`回修，并沿原`execute.test.ts`单条断言复验；识别实际`[exit N,运行…]`格式、跳过后续write/exec且配齐结果，read/plan仍可用。最终独立既有`test_mvp_loop.py` **9 passed in 0.28s**。

最终不可变产物：

| 对象 | SHA256 |
| --- | --- |
| Windows wheel | `802e22a52be3b24917460d81353dca50a8ae736e70da5ab2449a3b20abaa8ad7` |
| sdist | `8bc8fbf93119a058154eb9971e0479719ceb651a577f19b7d7ee38fb111a7434` |

两产物由主协调从`1ad72d6f06f499b50bfaacfd22daf3140f40f44f`构建，独审复制后自行核对hash；所有64个跟踪源码/资源成员均与wheel及仓库外实际安装逐字节一致，见`final-r2-provenance.json`。仓库外解释器为`C:\Users\PC\AppData\Local\Temp\ruocun-mvp-review-01a1c4bc-m04\venv\Scripts\python.exe`，仅安装pip/setuptools/ruocun，没有pytest、mypy、ruff等开发包，不借源码导入路径。

复用既有`test_mvp_product.py`函数，在仓库外合成workspace/HOME完成七工具、写入拒绝以及退出后第二进程正常恢复；断言保持原样，必要PATHEXT从合成父环境传入。`--version`、`--help`都退出0。实际SQLite版本3.54.1，gate=met，VFS=win32，DLL SHA256=`4b59d3cded9dc1608544160f3b4b10ac974c6ac0d6ffc23064e5f4c8dbd05aea`，source ID与官方固定记录一致；完整manifest在`raw/review-outside-r2-product-01/stdout.bin`。

本独审的产品启动均为安装解释器`python -m ruocun`；未把生成的`ruocun.exe`控制台launcher启动算为通过。主协调另报其中文空格Temp安装路径中的launcher被本机应用控制以WinError4551拒绝，属于其ENV记录；本独审没有运行该launcher，也没有关闭或绕过主机策略。当前独审支持的实际入口以模块启动为准。

最后为覆盖规格1的普通多轮交互，主协调只在同一既有product函数末尾补两轮stdin与`/exit`确认，产品和r2产物不变。独审在相同纯产品环境复用该函数的新尾段，七工具、拒绝、正常重开及同进程两个交互轮次全部通过，非主线程为空；测试来源文件的实际SHA256与完整manifest保存在`raw/review-outside-r2-multiturn-01/stdout.bin`。这项管道输入确认不冒充真实Terminal体验。

同一仓库外r2安装再次运行SIGINT最小确认，CLI退出130、信号后0.031秒、保存revision3，见`raw/review-outside-r2-cancel-01`。过程只使用localhost合成服务；命令子进程joined，合成服务线程结束，产品确认后的非主线程为空，最终自有路径工程进程0，见`processes-final.json`。工作树、私有venv、产物、合成状态和失败材料保留。

## Standards

按`code-review`技能，从固定基线`01e4606bc8fbb4f2df3394b7bc8926ad015be721`对完整首版并行执行规范轴；首审产品候选`0c3c726`，M03返修继续核查至`1ad72d6`。产品层硬性规范违例0，smell判断项0。两个交付文档收尾项中，`docs/development.md`的SQLite历史范围已由`1ad72d6`修正；公共module-map/acceptance-matrix的首版局部覆盖与证据待主协调补齐，不把旧82票虚标resolved。

## Spec

规格轴只发现同批exec失败屏障1项P2，已由`1ad72d6`回修并经同一轴只读确认；最终9条循环来源语义复验通过，剩余产品阻断0。七工具注册、审批、intent-before-effects、消息配对、未决恢复阻断、取消、费用说明和包资源无新增确定问题。未运行或未提供的真实模型/终端体验保持待验。

两轴汇总：Standards产品问题0（公共记录待收口）；Spec剩余问题0（原1项已修）。没有将两轴合并或以一轴掩盖另一轴。
