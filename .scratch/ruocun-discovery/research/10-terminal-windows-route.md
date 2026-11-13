# D10：终端与 Windows 平台路线

后续范围修订：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)取消本轮Windows系统级定时、防自动休眠与系统桌面通知；终端提示/安全标题和其它保留能力继续实现。下文相关原生后端为历史研究路线，不构成当前实施要求；沙箱另沿ADR-0008。

日期：2026-11-05。研究分支 `research/d10-platform`，起点 `455090b13b9dd96c3caee17254560a39fb04db2f`。本报告仅供主会话收录；不修改公共任务状态、DAG、规格、对应表或验收矩阵，不 push、PR 或 merge。

## 1. 可以定案的部分与仍有门禁的部分

**采用 prompt_toolkit 3.0.52 + Rich 14.1.0 + wcwidth 0.9.4 的内联路线；Win32Input/VT 为唯一输入 owner，统一队列为唯一终端输出 owner。Windows 默认 Shell 明确为 cmd 方言，保留外部工具名 Bash；实际 PowerShell/pwsh/Bash 调用按各自方言分析。Credential Manager、Task Scheduler、固定线程唤醒锁、原生剪贴板和原生 balloon 通知均有可实施端口。完整 Windows 沙箱尚未闭合，继续 fail-closed。**

这里“采用”是技术路线，不是产品实现或最终验收通过。D06 第一组用户反馈、自动实验与产品 WT/WIN 的通过状态分别保留。完整 D10 如要求“全部平台技术前置已验证”仍不能关闭；主会话可收录本报告已定子结论，解除只依赖这些子结论的13/18技术 gate，同时给60/61/78及最终交付保留精确安全门禁。不要为解锁普通终端和 Shell 审批而删除沙箱要求，也不要让已知失败后端成为默认后端。

| 领域 | 本次结论 | 后续门禁 |
| --- | --- | --- |
| 终端 | 采用 D06 已运行的固定组合与单 owner 适配；Rich 只格式化内容 | 18/65—68产品路径；77真实 WT 与人工体验 |
| Shell/环境 | cmd 为 Windows 默认；真实方言、引擎版本和包装链可审计；审批绑定最终命令 | 13/14/15真实 argv、编码、取消和恢复；不依赖沙箱后端先完成 |
| 凭据 | 窄 Credential Manager 绑定；**来源映射唯一引用 D09** | 58错误/超时/文件 fallback、78组合验收 |
| 系统定时 | Task Scheduler 每分钟短 dispatcher + 版本化私有 manifest；当前分钟匹配、合法相邻轮可重叠 | 59先验InteractiveToken及最小S4U能力；真正注销场景留78隔离身份/VM |
| 电源/通知/剪贴板 | 固定线程 SetThreadExecutionState、原生 balloon、Win32格式读取/文本写入 | 62—64实际系统路径与最终画面；剪贴板写测需可恢复合成会话 |
| OS 沙箱 | AppContainer 与当前 PSEC 都不选为完整后端；严格请求明确拒绝 | 第7节的最小验证或外部 native 后端前提；60/61/78/85继续 blocked |
| Linux/macOS | 保留同一能力端口，后端延迟导入，实机 pending | 不以设计/CI/WSL通过填写 Windows 或其它平台实机通过 |

## 2. 依据、来源与证据限度

已读 AGENTS、CONTEXT、docs/agents、全部5份 ADR、D10及D06/17/20、规格R-13/R-14/R-16、WT-01..09/WIN-01..11、13/18/58—68/78及其MM条目；采用[研究04](04-terminal-platform-delivery.md)、[研究16](16-windows-capabilities.md)、[PSEC固定线索](psec-lead/README.md)、[D08](08-python-runtime-route.md)、[D09](09-storage-extension-route.md)。D08/09与ADR-0005的运行时、IPC、三epoch和持久数据契约在原位置维护，本报告不另造公共schema。

DAO唯一来源为[冻结快照](../reference/README.md) `dao-f17e189-7ac654a0dc06`，基准 `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`，805文件源码树 SHA-256 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`。本轮读取已解包只读快照的sandbox、schedule、env_snapshot、safe_env及Bash权限代码，结合研究04的终端原文定位；没有读取活动DAO作为新基准。下文 `src/...` 均指该快照。

| 已有资产 | 本报告实际采用的结论 | 明确不能外推 |
| --- | --- | --- |
| [D06原型](../experiments/terminal/README.md)、[独立复核](../../ruocun/integration-evidence/d06/README.md)；候选ad48d6c、接收b114609、独立14 passed | 组合可运行、单Win32Input/VT链、同队列输出、真实worker退出；已取得第一组反馈“正常” | 不扩成全部IME、粘贴、焦点、图形、终端恢复或最终UI已通过；原README的历史pending/未选型由后续票及本报告收口，不改旧字节 |
| [D17实验](../experiments/windows/README.md)、[独立复核](../../ruocun/integration-evidence/d17/README.md) | Job三代/取消、有限AppContainer、真实定时触发/配置/手动并发、合成凭据和线程锁、通知API/callback有各自证据 | 独立十项执行后审计hook报错，整体exit=1，不写独立全绿。clipboard写入未跑；服务拒绝、注销网络凭据、真实通知画面等未验 |
| [D20实验](../experiments/psec/README.md)、[独立复核](../../ruocun/integration-evidence/d20/README.md)；接收9465be7 | ctypes/PSEC1.1实际宿主Python/Git/Windows PS、三代数据写边界、net/no-net及宿主/自身/后代回环、Job/owner退出 | **11 passed/1 xfailed中的xfail是外部RO实际WRITE_DAC/DACL变更成功，严格目标FAIL。** owner crash的PSEC服务端teardown未独立query；不写“后端通过” |

本轮只读研究、官方网页/源码查证并写文档；没有新模型请求、真实秘密、隔离工作负载、全局ACL/防火墙/组件变更、驱动或软件安装。主会话提供的WindowsSandbox.exe缺失、HypervisorPresent=true、hns/vmcompute运行只作为能力线索，不是本轮测量或可用后端证明。

## 3. 终端：选择、所有权与产品交接

### 3.1 框架与依赖边界

固定D06的 `prompt_toolkit==3.0.52 / rich==14.1.0 / wcwidth==0.9.4` 作为首个产品组合；发布时由D12验证实际CPython/standalone及锁文件，升级库必须重验窄适配而非自动追latest。用 `Application(full_screen=False)` 保留原生scrollback/选择；不引入第二套Rich Live、readline、msvcrt reader或独立探测reader。Textual全屏替代不采用，来源内联体验保持。[D06输入/输出依据](../experiments/terminal/README.md#实验边界和官方依据)、[prompt_toolkit固定Win32源码](https://github.com/prompt-toolkit/python-prompt-toolkit/blob/3.0.52/src/prompt_toolkit/input/win32.py)。

保留Windows支持subprocess的Proactor路径；ptk输入事件进入D08同一asyncio业务循环，不全局换Selector来迁就stdin。Rich渲染到StringIO/segments，终端writer串行输出；颜色、非TTY、屏幕阅读器及图形探测失败各有纯文本路径。[Python Windows asyncio](https://docs.python.org/3.11/library/asyncio-platforms.html#windows)、[Rich capture](https://rich.readthedocs.io/en/stable/console.html#capturing-output)。

### 3.2 单 owner 的具体责任

| 责任 | 采用路线 | 失败/关闭边界 |
| --- | --- | --- |
| 真实输入/ConsoleMode | ptk Win32Input/VT唯一读取；raw/cooked由框架持有。启动时登记mode，退出后比较原值 | VT后端不满足时拒绝该TUI路径并给文本说明，不悄悄换成未验native fallback。正常/可控异常配对恢复；强杀不能承诺finally |
| 协议过滤 | `terminal_reports.py`的窄ParserGate接在同一VT parser前，区分普通键、paste和DA/cell/CPR/focus；保留D06已核slot契约 | 私有slot变化在启动检查失败，不能继续吞字节。回包有界查询、分片与迟到缓冲；paste内相似序列一律按内容保留 |
| 应用输入 | 单路由依次处理模态/审批/问题→快捷键→编辑/提交；UI事件只提交scheduler，不直接改执行状态 | 不给审批框另开stdin；关闭面板只关闭视图，不取消任务；输入获接受后按D08/D09持久确认，不能因UI关闭丢已接受队列 |
| 输出/图形 | 一个协调队列经ptk `run_in_terminal`暂停绘制后输出；普通渲染、标题、focus开关、查询和Sixel都排队 | 图形单帧在途、有背压、flush后CPR定锚，未知几何停图；不绕过队列直接stdout。关闭需收齐在途写和取消查询 |
| resize | 记录geometry与render epoch，重算活动区物理行；丢弃旧epoch图形/锚点，草稿和历史独立于显示帧 | 共享终端不清用户scrollback；owned终端只按来源确认策略重建自有视口；不能用全清屏掩盖重排错误 |
| 窗口焦点/attention | 同一链读取focus，标题经去控制字符与长度限制后更新 | 通知和标题是不同端口；不能用focus=false推断OS窗口隐藏或已看见通知 |

协议预算沿冻结来源：query 600ms、普通Esc歧义80ms、报告片段2000ms；取消/关闭使query失效且不回滚新raw代次。ptk自身可能使用CPR的非Windows输出后端也必须进入同一链，后续Linux/macOS不能复制一个独立CPR reader。参考 `src/tui/terminal_reports.ts` 与[固定ptk parser](https://github.com/prompt-toolkit/python-prompt-toolkit/blob/3.0.52/src/prompt_toolkit/input/vt100_parser.py)、[run_in_terminal](https://github.com/prompt-toolkit/python-prompt-toolkit/blob/3.0.52/src/prompt_toolkit/application/run_in_terminal.py)。

### 3.3 粘贴、Unicode、取消与退出

- 文本paste事件不自动提交；CRLF/CR→LF，超过280个**JS UTF-16单位**或去末尾换行后超过6行折叠，Enter才展开。提交保留来源trim与占位展开顺序，140个emoji与再加1字的边界用D06 fixture继承。未闭paste/超长输入有显式有界缓冲或私有spill，不能把paste超时后的内容变成按键/Enter执行，也不能静默截断；资源上限及拒收反馈由18用实际压力证据登记，D06的1MiB样本不证明无限大小安全。图片路径只是路径数据，读取失败保持原文本，绝不执行路径。
- 内容索引、grapheme和终端cell分开。D06码点编辑不能直接声称满足组合字符/ZWJ原子删除；18在既定Unicode平台修正范围内补分段和光标映射，不拿Python `len`替代UTF-16折叠阈值。wcwidth负责显示列不等于grapheme编辑器。真实IME composition由终端/系统处理，组合期Esc/候选确认仍属77最终实机。
- Esc先让模态消费；非模态有队列先明确清队列，再次Esc才暂停当前回合。Ctrl+C保留2秒内双按退出；Ctrl+B交接同一Shell run后才解除旧前台取消域。Ctrl+T/G/O与Shift+Tab语义保留，记录WT截获冲突。取消按D08请求→执行器真实停止→结果提交分开；不能从ptk事件返回推断Job已空。
- 正常/可控异常关闭顺序：停止接收新输入→业务/保留后台交接→失效query/动画代次→收齐终端队列→关闭focus/paste/光标/颜色并恢复title/mode→回到调用shell。非TTY只输出可读文本。强杀/关闭窗口/注销有单独恢复说明和会话恢复记录；不把launcher补救后的mode相等写成应用自行恢复通过。

这些是R-13与D06已运行方向的产品化要求；18最小产品先接真实scheduler和Shell，65—68补内容、模态、任务和mascot，77/78/85统一最终人工。尚未取得的操作反馈不重问、不代填。

## 4. Shell：实际方言、权限分析、元数据与提示词

### 4.1 默认与兼容名称

**Windows默认保持cmd语义**，以已解析的绝对 `ComSpec` cmd.exe（缺失时System32/cmd.exe）构造 `/d /s /c`；不用PATH/cwd找同名cmd。若ComSpec指向其它解释器，须识别实际引擎并明确报不支持/请求显式修正，不能给PowerShell套cmd开关。保留工具外部名、schema及规则兼容名 `Bash`，不把名为Bash理解为一律Bash语法。来源 `src/tools/exec_shell.ts` 的shell:true在Windows原本走ComSpec；Python也明确使用ComSpec/System32搜索。[Python subprocess](https://docs.python.org/3.11/library/subprocess.html)。

`/d`禁止AutoRun、`/s`有特定首尾引号处理；cmd的`%VAR%`、可选延迟`!VAR!`、`^`、`&/&&/||/|`及括号不是POSIX语法。首版不擅改用户请求的扩展开关；把有效开关记入执行计划。具体Windows原生命令行拼接由专用cmd适配生成，`shlex.quote`、POSIX单引号、一般C argv quoting均不能充当cmd字符串转义。[cmd官方参数和引号规则](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmd)。

| 实际引擎 | 执行与身份 | 权限parser/降级 |
| --- | --- | --- |
| cmd.exe | 固定绝对EXE、开关、原始command和cwd；`.bat/.cmd`显式视为cmd解释；不得当普通exe安全argv | Python实现保守cmd词法/确定静态子集；无官方完整AST可依赖。多轮展开、CALL、FOR、动态变量/命令、未知转义或嵌套语法→unknown→ask；headless按原ask不可交互策略拒绝 |
| Windows PowerShell 5.1 | 明确 `powershell.exe`，区分`-Command/-EncodedCommand/-File`及版本；受管内部解析helper用`-NoProfile -NonInteractive` | 同一引擎的 `System.Management.Automation.Language.Parser.ParseInput` 只解析数据，输出AST/tokens/errors；不执行输入。动态调用、脚本块/变量/别名不能可靠解出时ask，不以AST存在当安全证明 |
| PowerShell 7/pwsh | 明确绝对pwsh与版本，不和5.1合并；native argument passing/重定向模式保留实际值 | 用实际pwsh版本parser；不能用5.1 AST输出或Bash规则替代。helper缺失/超时/输出不合法均unknown，不改由模型猜allow |
| Git Bash/其它bash | 显式执行已安装的绝对bash及其开关，区分Git/MSYS与WSL；不自动安装、不静默把Windows路径换WSL路径 | 沿MM-529/531—537已有Bash AST/预处理路线；实际Bash语法才用Bash parser。解析失败和动态嵌套仍ask |
| native argv探测 | doctor/env用明确argv启动已解析的exe；`.cmd`探测需走cmd专用路径 | 不经任意shell字符串拼接；执行失败、not-found、timeout分开，探测不运行profile、别名、任意项目脚本 |

PowerShell parser是公开API，但解析不等于静态确定执行效果；其参数/表达式模式和`$()`等需实际识别。[Parser.ParseInput](https://learn.microsoft.com/en-us/dotnet/api/system.management.automation.language.parser.parseinput)、[PowerShell parsing](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing)。`-EncodedCommand`必须按该引擎UTF-16LE契约解码再展示和分析；不把base64当不可见授权载荷。`-File`执行文件及其参数与`-Command`并不相同；Python内部helper传数据走stdin/受控文件，不把JSON插进`-Command`。[Windows PowerShell CLI](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_powershell_exe?view=powershell-5.1)。

### 4.2 一个不可变执行计划贯穿审批与启动

13/14在现有权限seam中使用**同一份内部计划**，概念字段包括实际EXE/版本、dialect及解析版本、完整包装链、原始command、最终native command line/argv、cwd、有效环境来源及输出codec、是否batch、sandbox请求/策略标识、取消方式。它不是新外部工具参数，也不是第二套持久schema；runner记录仍按D08/D09的版本化manifest扩展，由唯一类型声明导入。

PreToolUse最终参数确定后才计划/裁决；被修改的参数必须重新判。审批显示真实解释器、完整嵌套命令和实际可影响文件/网络的部分。`cmd→powershell -EncodedCommand→script`逐层识别；`powershell→cmd /c`同理；无法确定则整体ask。已有deny/危险强确认不能因为外层换壳、包装器、环境赋值或分类器意见变allow。Bash兼容规则只在可证明对应实际命令时适用，不能拿`Bash(cat:*)`给PowerShell别名/重定义函数自动放行。不能把“复杂就ask”泛化成在所有工具前新增全局信任gate。[R-08/R-14；任务13 PERM-03；冻结 `src/permissions/bash_preprocess.ts`、`bash_safety.ts`]

执行计划一经批准只执行该计划；引擎/脚本/参数/环境/工作目录变更使批准失效。文件身份/哈希能记录具体版本，但不夸大为抵抗同用户恶意并发替换的完备安全边界。权限分析和OS沙箱仍独立；未启用沙箱按来源普通执行，已请求strict而后端不可用则在业务启动前失败，只有现有`dangerouslyDisableSandbox`明确审批路径才可单独绕过，不能从失败自动降级。

### 4.3 编码、环境、提示词和取消

Unicode EXE/cwd/env均用Win32 W接口；stdout/stderr先保留bytes并增量解码，分cmd内建输出、native输出及PS文本/CLIXML，codec/解码异常可诊断，不能统一`errors=ignore`。cmd `/u`不是任意子工具都UTF-16的保证；若采用UTF-8会话设置，必须在私有child控制台/环境内完成并逐个工具验证，不改全局code page。14至少覆盖中文空格路径、单双引号、`% ! ^ $`、换行、管道、重定向、`.cmd`及5.1/pwsh差异。

环境继承严格引用[D09环境边界](09-storage-extension-route.md#环境别名与凭据范围)：产品普通Shell/runner沿safe_env脱敏继承，Hooks/MCP维持其已定兼容契约；工程测试始终白名单+synthetic HOME。env_snapshot/doctor保持一次启动收集与固定前缀缓存纪律，用argv探测版本/Git信息，先判实际可执行文件类型，不把原POSIX `v=$(...) / head / command -v`送cmd。

固定prompt文字、工具名和原安全语义保持。只在现有Environment/平台信息位置追加真实OS、默认Shell绝对路径/方言/版本、可用显式解释器及正确路径/引用提示；不要批量把所有“Bash”改“PowerShell”，也不要把固定prompt里的示例当实际Shell选择器。执行反馈中的方言与这份环境信息一致。此必要平台信息属于R-16允许的真实环境差异，纳入prompt oracle与WIN-01，不以迁移名义改策略语气。

取消沿D08：进程先suspended创建→关联Job→确认成功再恢复；runner持Job及身份句柄，UI退出保留后台时不关闭最后Job handle。温和停止仅在实际console/process-group契约成立时使用控制事件，不承诺通用POSIX SIGTERM；无共享console或工具不响应时有界强停Job，再等实际树/输出关闭才canceled。错误和超时未确认保持unknown。主UI不AttachConsole切到child控制台抢输入；如需私有console控制helper，隐藏且独立于UI输入owner，14用真实子孙进程验证。[D08取消契约](08-python-runtime-route.md#6-取消与退出契约)、[Windows Job](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)。

## 5. Task Scheduler：可实施默认与需要决定的身份边界

### 5.1 选短dispatcher，不展开任意cron为大量OS触发器

Windows `schedule.py`仍拥有add/list/remove和Schedule外部schema，NEW-05只管OS注册/查询。每用户一个私有RuoCun任务：对齐分钟的TimeTrigger/PT1M无限重复，补登录触发仅用于下一次当前分钟检查；启动同版本安装产物的内部dispatcher角色。dispatcher很短，只匹配当前分钟、认领due记录、启动独立headless run后退出，不能调用TUI或依赖主会话常驻。子任务有各自run/Job/日志和未知保护；一条慢业务不阻下一分钟。

Windows方言明确为经典五字段 `分 时 日 月 周`：支持数值、`*`、列表、合法升序范围、正步进及英文月/星期名称；周日0/7归一。DOM/DOW均受限时OR，均命中只一次。严格拒绝秒/年字段、`L/W/#/?`、宏、随机/`~`扩展及越界，不截断或近似。来源仅粗regex后交给宿主crontab，没有统一宿主方言；这是Windows适配的明确方言选择，不声称复现所有Cronie扩展。[Cronie一手手册，固定38773f4](https://github.com/cronie-crond/cronie/blob/38773f4347bd86a5de089b21e924fa735ba45712/man/crontab.5)。既有来源对照样本完整迁移，D17 numeric matcher只是局部实验，不可直接当产品parser。

采用主机当前本地时区墙上分钟：DST gap分钟不补，fold两次不同UTC分钟各可触发一次；手工时钟/时区回拨以持久的 `(schedule_id, UTC minute)` 防同一实际分钟重复。Windows使用动态时区API把UTC转换成本地分钟，不缓存当前固定offset冒充全年DST规则。[SystemTimeToTzSpecificLocalTimeEx](https://learn.microsoft.com/en-us/windows/win32/api/timezoneapi/nf-timezoneapi-systemtimetotzspecificlocaltimeex)。此为本产品明确语义，既非已完成Scheduler DST实证，也不把Cronie daemon所有特殊校时行为照搬。默认无历史catch-up：重启/恢复/登录时只算当前分钟，不追补关机/休眠/注销期间的旧分钟。过点的系统启动不能伪装为准时；receipt记录计划分钟、实际启动时间、时区及延迟。若未来需要补跑，另作显式策略，不默认执行积压副作用。

### 5.2 显式设置、回读与升级

| 设置 | 默认路线及理由 | 证据/测试 |
| --- | --- | --- |
| OS实例重叠 | dispatcher采用Parallel+短的本产品claim互斥；业务各轮允许重叠，不选Queue/StopExisting替换来源行为 | D17手动Parallel/IgnoreNew/Queue有对照；产品59验相邻真实分钟与claim竞争，不拿手动Run代替时间触发 |
| 时间/电池/睡眠 | 显式PT0S、DisallowStartIfOnBatteries=false、StopIfGoingOnBatteries=false、WakeToRun=false；StartWhenAvailable=false | D17读回过true补触发，本路线选择false须产品重读XML；不沿用系统默认72h/电池true。执行中唤醒锁与为定时唤醒系统是两件事 |
| 错过 | 不扫描旧分钟，不从“系统补触发”生成旧业务run | StartWhenAvailable=true有排队延迟、默认10分钟，不能承诺补齐每分钟。[官方说明](https://learn.microsoft.com/en-us/windows/win32/taskschd/tasksettings-startwhenavailable) |
| 任务action | Path/Arguments/WorkingDirectory分开；绝对稳定launcher+任务ID；无prompt/key内嵌、不依赖PATH或shell `>>` | 同版本内部角色打开日志；中文/引号/百分号/美元/换行prompt走manifest字节，不经cmd再解释。[ExecAction](https://learn.microsoft.com/en-us/windows/win32/taskschd/execaction) |
| 私有manifest | schema版本、稳定schedule_id/创建序、原cron/方言/zone、cwd、prompt、安装generation/角色入口、profile引用及原生兼容来源；无secret值 | 当前用户私有DACL/不可任意reparse；原子发布沿D09既有文件层。list/remove只操作本产品命名空间；拒绝/服务不可达不能冒充空列表 |
| claim/崩溃 | due意图、实际launch、run receipt分开；启动后回执丢失保持unknown，不自动再起同分钟任务 | 不承诺OS spawn与本地记录原子；独立dispatcher不能借session DB owner重放副作用 |
| 升级/回滚 | launcher稳定；版本目录并存，原子更新安装manifest；已启动runner固定旧版本，新due绑定新generation | 更新前暂停新claim、核验新角色/资源/SQLite组合，再切换并读回任务；失败回滚指针/任务而不重跑未决；卸载按显式选项停/移自己的任务，保留数据可追溯 |

### 5.3 登录策略：先验最小S4U路径，不让用户替我们查事实

建议先实现并验证普通用户 `InteractiveToken`：无需收集Windows密码，可覆盖已经登录及锁屏时的系统触发；注销后没有交互token，不执行，重新登录不追旧任务。它仍是会话外系统定时，不是RuoCun内存loop。**这只是已明确的无密码路径，不据此缩小完整WIN-06；S4U须先用实际路径判断，不能提前把选择Password/service的问题交用户。**

官方S4U无需存密码，文档有网络/加密文件访问限制；这不能直接推成普通TCP/HTTPS/API-key HTTP必然不可用。Password logon需要登录密码和相关登录权利。分别保存文档事实与实际能力，不把S4U当已支持或已完全淘汰。[logonType官方契约](https://learn.microsoft.com/en-us/windows/win32/taskschd/taskschedulerschema-logontype-simpletype)。

59承接一个最小S4U子案例，不另立巨大平台probe：普通权限注册精确UUID的一次性S4U任务，重用D17合成manifest worker，先查询最终logon type/privilege/result，再实际读取自有私有profile文件、精确合成Credential Manager target、TCP loopback nonce及微软无认证HTTPS（正常证书/hostname验证）。worker最早清理环境并把HOME/配置指向合成根，不把服务启动环境或秘密值落日志；仅状态/合成hash/错误码。InteractiveToken用同输入作正对照。拒绝注册/文件/EFS、网络、凭据库、代理/UNC各自分类，不以其中一个失败推定全部失败；不用模型或真实API key。删除任务和合成凭据并精确查询确认，无全局策略、账户或权限改动。

当前用户已登录时的S4U实际运行只证明该登录条件；真正注销、重启、跨session的profile/credential行为留78的一次性用户/VM。若最小S4U路径不满足在线任务或完整身份生命周期，才向主会话报告具体缺口：推荐由Windows Task Scheduler托管经用户交互录入的Password登录凭据，RuoCun不保存/记录密码；或设计专用service身份/凭据broker。真正需要保存Windows密码、安装service、调整支持范围时再集中请用户取舍。不要转SYSTEM、复用真实密码作probe或把API key塞任务参数。

## 6. 其它Windows端口及跨平台边界

### 6.1 凭据

选原生 `CredWriteW/CredReadW/CredDeleteW/CredFree` 窄绑定，Generic、本用户本机持久化，避免keyring自动选不明后端。TargetName大小写不敏感、blob长度上限及当前登录session的credential set都要按API处理。[CREDENTIALW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw)、[CredReadW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credreadw)。

**所有服务名、账户名、TargetName编码、旧keyRef精确只读路由、credentialOrigins及新写/删隔离的唯一依据是[D09“环境别名与凭据范围”](09-storage-extension-route.md#环境别名与凭据范围)。** 本报告不复制另一套映射。58用合成Profile/profile/Unicode和旧来源fixture验证。helper限时写结果不明时先查询对账，明确stored=system/file/not-found/refused/timeout-unconfirmed；不能因UI超时就报告未存并再写一份。明确失败按原格式file fallback，真实显示并私有DACL；不把chmod0600当Windows权限证明。

### 6.2 唤醒、通知、标题

NEW-06选D17已验证的固定长寿线程 `SetThreadExecutionState(ES_CONTINUOUS|ES_SYSTEM_REQUIRED)`，引用0→1申请、1→0在同线程释放；acquire失败不增成功计数。前台回合与独立runner各拥有自己生命周期，UI退出不释放仍归runner的后台锁。默认不请求屏幕常亮，不承诺拦住用户主动Sleep或所有Modern Standby/电池策略。[官方API](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate)。PowerRequest句柄路线保留为以后有证据的替换，不同时维护两套默认锁。

NEW-09选与来源对应的原生balloon：隐藏owner窗口+受监督消息循环，Shell_NotifyIconW add/modify/delete，Unicode载荷作为结构数据，绝不插进PowerShell命令。提交、callback、画面观察、关闭/失败分别记，Explorer重启重建自己的icon，退出清自己的线程/window/icon。关闭通知/勿扰时任务照常完成，不能把API成功标displayed。toast的AUMID/shortcut/激活/通知中心留存不属来源保证，本轮不引入SDK身份安装依赖。[Shell_NotifyIconW](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shell_notifyiconw)。标题/focus仍经终端writer的attention端口处理，按原任务状态去控制字符与恢复title，不等于桌面通知。

### 6.3 剪贴板

NEW-07采用Win32文本写入 `CF_UNICODETEXT`；图片读取优先已注册PNG，再DIBV5/DIB，必要解码库固定后由64验证。图片文件路径入口保持独立。所有格式先查尺寸/长度/stride/像素预算，再解码为PNG并按来源5MiB原始字节上限与magic/MIME验证；PNG大小小不证明解码尺寸安全。RGBA、24/32位、alpha/上下翻转、文件列表、无图/占用/畸形及超限各有fixture。GetClipboardData返回系统handle不释放，Open/Close严格配对并及时复制数据；文本失败或无图不吞已有草稿。[Clipboard formats](https://learn.microsoft.com/en-us/windows/win32/dataxchg/standard-clipboard-formats)、[GetClipboardData](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getclipboarddata)。

**输入事件不能靠猜。** WT的paste是终端action；它可截获快捷键，不能从Win32有图片推断应用会收到空paste事件。[WT actions](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/actions#paste)。64应在同一输入路由中实现明确的“从系统剪贴板附图”动作，推荐应用级Alt+V，沿当前草稿/问题框附件路径，只响应用户动作，不轮询clipboard、不自动提交；普通文本WT粘贴仍原样处理。具体按键若与环境冲突按最终77验收调整，不另建reader或新模型工具。该Windows适配需在产品操作说明/WT用例登记；若主会话要求沿用现有Ctrl+V手感，须先以真实WT事件证据证明可达，不能空实现成功。

D17没有执行clipboard写入，私有windowstation创建返回5且用户内容未读存。64自动写测在一次性用户会话/VM预置完整合成formats；普通主会话不能“备份文字”后EmptyClipboard冒充完整可恢复。清理检查sequence，用户已复制新内容不覆盖旧快照。最终主机实际附图与视觉请求字节核对按ADR-0004统一。

### 6.4 端口位置与其它OS

| 端口/职责 | Windows选择 | Linux/macOS保持边界 |
| --- | --- | --- |
| Process/Identity | NEW-01；Win32身份handle/创建时间+Job；取消/keep后台依D08 | POSIX身份/进程组各自实现；负PID不进Windows分支 |
| IPC/持久文件 | NEW-02/03；D08/D09唯一命名管道/helper及文件语义 | Unix socket/权限/原子发布各自实机，不能把Windows handle或NTFS假设放核心 |
| Credential | NEW-04；本节6.1+D09 | 来源macOS security/Linux secret-tool端口，保留有界错误及source map；未承诺跨OS搬秘密 |
| Schedule | NEW-05；本节5 | 来源系统crontab适配保留，明确宿主方言；不为了统一Windows dispatcher擅改原POSIX行为 |
| Power/Notification | NEW-06/09 | 来源caffeinate/systemd-inhibit及通知命令，实际可用性/进程生命周期分别验 |
| Clipboard | NEW-07 | macOS来源读取流程保留；Linux能力探测/不可用明确返回，不从Windows成功外推 |
| Sandbox | NEW-08；第7节仍blocked | 来源Seatbelt/bwrap各自平台支持/实测；WSL运行的是另一个guest，不替Windows后端 |
| Terminal | MM-747/751/794/800与65—68 | 同一UI语义、不同输入/输出backend延迟导入；其它平台CPR/信号/tty清理独立验 |

核心只import平台端口类型，由platform factory按OS延迟加载Win32绑定；缺功能返回明确的unsupported/unavailable/error能力结果，不在import阶段让Linux/macOS崩溃，也不把非关键best-effort端口成功与否冒充业务执行状态。

## 7. 沙箱：已知失败不选型，最小补救与外部候选

### 7.1 严格目标和当前可证明结论

来源 `src/tools/sandbox.ts` 是workspace/tmp可写、其它文件写受限、默认网络可用、显式no-net；Win32必须保持真实允许/拒绝、工具链、继承、取消、后台及失败语义。WRITE_DAC/WRITE_OWNER/owner、reparse和已授权handle是文件写边界的一部分，不能删掉以取得绿色。前台/durable/无store后台均拒绝不满足请求的后端，来源旧非durable fail-open分支作为R-16安全修正登记。

- **Job不是候选安全后端。** D17对照中能写outside并连回环，只证明治理功能。
- **D17 AppContainer不选完整后端。** 宿主loopback拒绝、自身loopback允许，工具/广泛主机读取有限；不能用全机ACL或loopback exemption悄悄修成另一套策略。
- **D20 PSEC1.1不选完整后端。** 数据写拒绝和no-net（含loopback）有实证，但RO元数据DACL可改，strict入口必须继续拒绝；owner crash服务状态仍未知。只读导出/version查询或11pass1xfail不能改变这个结论。

### 7.2 “PSEC叠受限token”有何官方依据、缺什么

一手固定为Microsoft MXC `f4aa3fd59306d140ccf7448e914306fc6cdb74d0`：PSEC通过 `CreateProcessW + PROC_THREAD_ATTRIBUTE_SECURITY_ENVIRONMENT` 启动；schema没有自定义primary token/WRITE_DAC mask字段，runner拒绝leastPrivilege模式，文档明确PSEC无LPAC token选项。[固定runner](https://github.com/microsoft/mxc/blob/f4aa3fd59306d140ccf7448e914306fc6cdb74d0/src/mxc-sdk/src/backends/process_container/common/base_container_runner.rs)、[固定schema说明](https://github.com/microsoft/mxc/blob/f4aa3fd59306d140ccf7448e914306fc6cdb74d0/docs/schema.md)、[已存PSEC wire schema](../experiments/psec/source/ProcessSecurityEnvironment.fbs)。LPAC和CreateRestrictedToken不是同一机制，因此“LPAC不支持”不能推导所有token组合不可能；反过来也不能据此声称有受支持修复。

`CreateRestrictedToken`和`CreateProcessAsUserW`是官方用户态API，调用自己primary token的受限版本有SE_ASSIGNPRIMARYTOKEN例外；WRITE_RESTRICTED只对写访问考虑restricting SIDs。[CreateRestrictedToken](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-createrestrictedtoken)、[CreateProcessAsUserW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessasuserw)。**本轮没有查到官方保证这个primary token与PSEC启动属性可组合、PSEC保留其限制、以及限制能覆盖所需owner/DACL和后代的契约。** 官方MXC已读固定入口不实现该组合。这是明确的证据缺口，不能写成“官方禁止”或“已支持”。

对象owner隐含WRITE_DAC，删除SeTakeOwnership/SeRestore等privilege不自动删除同用户owner身份。[Owner of a New Object](https://learn.microsoft.com/en-us/windows/win32/secauthz/owner-of-a-new-object)。所以“PSEC+删privilege”不是有依据的完整修复。加OWNER_RIGHTS ACE能改变具体文件的owner权限，但需要修改每个外部对象，不符合不改广泛宿主ACL、动态目录及竞争契约，不能作为默认路线。低IL/MIC先于DACL并有no-write-up，但不等于仅cwd可写，低IL外部对象仍要考虑；当前D20也未完整测token IL。[MIC](https://learn.microsoft.com/en-us/windows/win32/secauthz/mandatory-integrity-control)。

### 7.3 推荐的无安装最小验证任务（本轮不执行）

建议只新增一个精确前置“PSEC与受限primary token的兼容及owner元数据最小判别”，不要重做D17/D20全套。普通用户、明确白名单/synthetic HOME、仅自有root/workspace/tmp/outside，零真实配置/秘密、零全局ACL/设备/服务修改。保留原D20字节，新增窄启动适配和固定合成worker。

| 阶段 | 精确操作/证据 | 停止条件与下一步 |
| --- | --- | --- |
| A：先判启动兼容 | 独立受限token→`cmd /d /c exit 0`及实际Python；显式私有std handles/desktop，不把NUL或宿主设备ACL改宽。随后以CreateProcessAsUserW+原PSEC属性同样启动。查询实际worker TokenUser/Owner/Groups/RestrictedSids/Privileges/IntegrityLevel/MandatoryPolicy/AppContainer SID，比较请求与实际 | standalone仍0xC0000142或组合API失败/限制丢失即止，保存原Win32/NTSTATUS；不把结果解释成WRITE_DAC已阻止，不试遍无依据flag或系统补丁 |
| B：只判已知缺口 | host同脚本正对照；workspace允许数据写；outside自有同用户owner文件，分别仅请求WRITE_DAC、混合mask、WRITE_OWNER、实际加随机无效SID的FR ACE并host读回；原DACL/owner及时恢复。另测不同合成owner条件只在能合法自有创建范围内，不伪造其它账户 | 任一RO实际元数据变更成功即目标FAIL；strict仍拒绝。仅Open拒绝不代替真实API/host确认。不要通过改outside owner/DACL抹去原失败条件 |
| C：最少回归 | 仅A/B通过才验真实child继承token+PSEC、net/no-net一组宿主及自身loopback、工具Python/Git/PS、允许目录与junction、retained handle+Job收口/Close回执 | 若通过仅解锁产品60/61候选；仍需产品文件权限族、正常/持久后台/取消、安装产物和owner crash服务端契约，不直接关WIN-09 |

D17 restricted token初始化失败原因尚未定位，不能从0xC0000142单独断言是某个设备ACL、DLL或权限。阶段A只在自有根内使用明确资源；如诊断显示必须修改宿主设备/运行库ACL、安装辅助程序或增加全局权限，应停止并把精确对象/所需权限/一手依据交主会话集中决定，不能在用户机器上试授广权。

### 7.4 需要安装/组件的替代路线及推荐顺序

如果上面A/B否定最小组合，推荐下一步在可回滚VM评估 **Sandboxie Plus签名driver/service + WFP**，再决定是否引入产品外部底层依赖；这不是已选可交付后端。它最接近主机工具/路径语义；Python可持有业务与编排，native driver只负责OS强制边界。必须固定实际版本、安装包签名/hash和组件许可：core/Classic为GPLv3，SandMan/Plus另有自定义使用/分发条件，不能把Plus全体称GPL；按实际依赖逐项核定，商业使用/证书前提需准确说明。[固定LICENSE.Plus](https://github.com/sandboxie-plus/Sandboxie/blob/ac6900dc30c940ca57c4590494a816243fa3ce64/LICENSE.Plus)。管理员一次性安装与全局WFP启用需用户集中授权，不能暗装。

| 候选 | 一手能力依据 | 尚缺/为什么不直接选 |
| --- | --- | --- |
| Sandboxie Plus | ReadFilePath明确外部可读、不可写/删；OpenFilePath使允许目录直写。WFP由driver在v4/v6 ALE connect/receive层处理，另有loopback开关 | 需要规则优先级、执行自workspace新EXE、readonly WRITE_DAC/owner/reparse、持久runner/I/O/Job及故障fail-closed实测。默认copy-on-write外写成功不合本目标；单纯用户态Winsock hook可绕过，不接受。WFP全局启用及driver/service是安装前提 |
| Windows Sandbox/winapp | Microsoft VM隔离；CLI可start/exec/share/stop；winapp有guest agent和forwarded streams | 本机缺WindowsSandbox.exe，仅虚拟化/HNS服务不够；需启用可选组件/客户端、可能重启、guest工具链及映射/协议。wsb exec自身无I/O，winapp一次共享一个Sandbox、会增加guest bootstrap/firewall配置；guest路径/软件与host不同，不是默认host Shell等价 |
| Windows container/Hyper-V | 可提供Windows内核/namespace或VM边界 | 需要runtime/service、兼容Windows镜像、挂载/网络/工具链；不是本次最小host工具修补。仅容器运行成功仍不证明原生host路径/用户读取契约 |

Sandboxie一手固定docs `87c545edd04baf4a0709251239c5cd658061815c`：[ReadFilePath](https://github.com/sandboxie-plus/sandboxie-docs/blob/87c545edd04baf4a0709251239c5cd658061815c/docs/Content/ReadFilePath.md)、[OpenFilePath](https://github.com/sandboxie-plus/sandboxie-docs/blob/87c545edd04baf4a0709251239c5cd658061815c/docs/Content/OpenFilePath.md)、[WFP](https://github.com/sandboxie-plus/sandboxie-docs/blob/87c545edd04baf4a0709251239c5cd658061815c/docs/PlusContent/WFPSupport.md)。代码调查点为 `ac6900dc30c940ca57c4590494a816243fa3ce64`，不是已安装版本。其[Start CLI](https://github.com/sandboxie-plus/sandboxie-docs/blob/87c545edd04baf4a0709251239c5cd658061815c/docs/Content/StartCommandLine.md)的`/wait`只等待给到的进程handle而非整树，`/terminate`零退出也不证明停止，不能直接替换D08执行回执。

Windows VM路线依据：[Windows Sandbox CLI](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-cli)、[winapp Sandbox execution](https://learn.microsoft.com/en-us/windows/apps/dev-tools/winapp-cli/sandbox-execution)、[Windows containers系统要求](https://learn.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/system-requirements)。本报告没有安装这些后端，也不声称任一已满足完整目标。用户若不允许安装native组件且最小无安装候选失败，**完整Windows沙箱目标与可用环境将成为实际范围冲突**；由用户决定外部依赖/环境或目标调整，不能代理自行降级。

## 8. 实施交接、集中决策点与交付核查

| 实施任务/MM | 现在可采用的路线 | 保留证据门禁 |
| --- | --- | --- |
| 13；MM-529/531—537/543/637/685 | 第4节实际方言/保守parser/不可变计划，兼容Bash名和固定prompt | PERM-03、WIN-01真实语义；未知复杂ask；本身不以沙箱backend通过为前置 |
| 18；MM-747/751/753/794/800 | 第3节固定ptk/Rich、单owner、scheduler路由 | WT-01..05/09产品自动；77最终体验；不因暂未沙箱而阻塞不使用它的终端实现 |
| 58；MM-455/458+NEW-04 | 第6.1节+D09唯一凭据映射 | WIN-05/CFG-04；不得在并行分支重造provenance |
| 59；MM-582/625/700+NEW-05 | 第5节dispatcher/cron/manifest/升级、InteractiveToken与最小S4U子案例 | WIN-06；已登录S4U实证不代替注销后/跨session，缺口先验后报 |
| 60/61；MM-698+NEW-08 | 第7节strict reject及最小验证任务 | 元数据FAIL未修不能解锁完整后端；网络单项通过不能抵消文件失败 |
| 62—64；MM-798/680/772/790/763/691+NEW-06/07/09 | 第6节固定线程power、原生balloon、图片/文本clipboard | WIN-07/08/10；clipboard安全会话、真实画面、模型字节链留产品验证 |
| 65—68；MM-480—482/744—800相关UI条目 | 第3节职责与源资源provenance；Rich内容/ptk显示分离 | 全部WT；完整mascot/模型技能选择器不继承原型通过 |
| 78/85 | 普通用户完整组合与最终发行环境 | 登录/重启、权限/文件/网络、系统端口、终端体验均真实留证；未闭合不关票 |

建议主会话集中处理的事项：

1. 收录已定的终端/Shell/公共端口子结论，按实际依赖细化13/18 gate；完整sandbox另建精确前置并保留60/61/78/85阻塞。本分支不自行改DAG或关闭D10。
2. 同意先做第7.3节无安装最小token兼容/owner判别；若失败，再集中选择是否允许在VM安装Sandboxie签名driver/service+WFP评估，或接受更重的Windows VM后端调查。推荐前者顺序；没有推荐采用已知弱边界。
3. 59先验InteractiveToken与最小S4U的profile/CredRead/loopback/HTTPS，78补真正注销/重启。仅当这些证据表明必须Password登录、service安装或支持范围取舍时，再集中提交具体授权方案，不能让用户预先替我们判断S4U网络事实。
4. Windows系统附图采用明确应用动作（建议Alt+V）进入既有附件路径，最终快捷键体验按77集中；不要求用户替我们查WT事件事实或反复逐票验收。

本次文档核查实际完成：17个本地相对链接均存在；逐组与任务13/18/58—68/78的MM和WT/WIN定义核对；D06锁文件实际包含所选三版本；D06/17/20独立复核的通过/失败/未验口径核对；固定MXC、Sandboxie和Cronie来源指针核对；`git diff --check`通过，变更范围仅本文。未运行产品测试或重复系统probe。真正产品路径由各票TDD及独立复核承担。研究资产即使完整sandbox未闭合也可本地提交；最终提交SHA由交付回执给出。
