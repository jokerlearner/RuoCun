# 终端、Windows 平台、验证资产与交付候选研究

日期：2026-11-05
任务：[04 — 查清终端与 Windows 缺口、测试资产及交付候选](../issues/04-terminal-platform-delivery-research.md)
类型：只读研究与后续实验设计；没有产品实现、来源测试结果或用户体验验收结果。

## 1. 结论与证据边界

1. 原版是 **inline Ink TUI + 应用状态机 + 独立终端协议适配 + Sixel 欢迎图层**。保留终端原生滚动、选择与交互语义，需要把这些职责一起对照，不能只换输入框。快照 `src/tui/app/run.tsx:10-14`、`src/tui/app/App.tsx:1295-1357`、`src/tui/mascot.ts:90-104`。
2. **建议先验证 prompt_toolkit，Rich 只作内容格式化层**。Textual 是完整 TUI 对比候选，但其当前官方文档明确说 Windows 不支持 inline；改用全屏会影响原版操作体验，不能默认为等价迁移。[Textual inline 官方限制](https://textual.textualize.io/guide/app/#run-inline)
3. Windows 已有欢迎屏固化、CRLF 粘贴归一化、CIM 进程身份、托管配置路径、剪贴板复制和通知分支；仍缺系统定时、系统凭据库、唤醒锁、剪贴板图片和 OS 沙箱平台实现。另有 runner IPC、负 PID 取消、Shell 探测、落盘权限等**静态平台风险**；本轮没有运行它们，不能称 Windows 实测失败。
4. 静态枚举快照 805 文件，发现 **215 个 `*.test.*` 文件、58 个 scripts 文件、16 个实际 task.json 评估任务**。应复用数据和行为断言，语义重写语言绑定测试；专题 `replay` 常会调用真实模型，不能因名字含 replay 就当确定性离线回放。第 5 节和附录给完整清单。
5. npm 发布、Bun 独立产物、实际 Windows 功能验收是三个层次。现有 CI 为 Ubuntu；发布也在 Ubuntu 交叉编译 Windows x64，并未执行 Windows TUI 或全功能检查。快照 `.github/workflows/ci.yml:9-24`、`.github/workflows/release.yml:12-35`。
6. 后续最小实验应同时覆盖真实 Python + Windows Terminal 交互、原生进程与 IPC、wheel 安装、Windows 独立打包。**只提出实验，本轮未安装候选库、未启动来源产品、未运行来源测试、未执行任何 TUI。** Linux/macOS 保留设计与后续实机验收，不降低 Windows 全功能目标。

唯一源码来源为 [dao-f17e189-7ac654a0dc06](../reference/README.md)，基准提交 `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`，完整树 SHA-256 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`。读取目录为 `D:/java supplement/Firstcode/RuoCun/.worktrees/reference-dao-f17e189-7ac654a0dc06/source`；下文所有 `src/...:行号`、`scripts/...:行号` 等均指该快照的原始文件，不指活动 dao-code。文件数量来自只读路径枚举，不是通过用例数量。

标记规则：**静态事实**可由冻结源码确认；**官方声明**来自当日读取的一手文档或库官方源码；**建议**是迁移设计候选；**待实验**必须有后续运行证据。遵循 ADR-0001/0002、CONTEXT.md 和验收矩阵；不重问核心 Python、Windows 优先、扩展兼容、自身会话完整恢复等既定目标。

## 2. 终端职责与真实输入链路

| 层 | 快照中的职责与入口 | Python 需要保留的行为 |
| --- | --- | --- |
| 启动/模式选择 | `src/index.ts:378` 创建 readline；交互入口导入及调用 `runInkApp`（`src/index.ts:139`、`src/index.ts:1908`）。 | TTY TUI、非 TTY/脚本入口分开；重定向输出不得混入图形控制序列。 |
| 能力/主题 | `src/tui/capabilities.ts:9-29` 依据 TTY、NO_COLOR、FORCE_COLOR、COLORTERM、TERM 和列数决定颜色层级；`src/tui/background.ts:27-71` 的 OSC 11 探测临时占用真实 stdin，默认 250 ms，清理时恢复 raw 并 pause。 | 不能用 Windows Terminal 名字替代实测协议能力；启动早期输入和迟到 OSC 回包也须验证。主题探测必须与后续唯一输入所有者有明确交接。 |
| 图形入口和输入所有权 | `src/tui/app/run.tsx:25-49` 仅深色、truecolor、双 TTY、未跳 banner、非屏幕阅读器时启用 terminal reports；该适配器成为真实 stdin 唯一 reader，Ink 读代理流。 | 支持图形、无图形、无响应三条路径。普通文本不能被探测吞掉，协议回包不能进入草稿。 |
| 报告/焦点过滤 | `src/tui/terminal_reports.ts:24-35`、`src/tui/terminal_reports.ts:71-146` 按字节区分 DA、cell size、CPR、focus 与普通输入；paste 内报告形状的文本不作为报告处理。 | 拆包 UTF-8、拆包 CSI、迟到回包、F3/CPR 歧义、paste marker 拆包须有协议测试。 |
| 查询/流控/清理 | `src/tui/terminal_reports.ts:24-29`：query 600 ms、常态 Esc 80 ms、报告片段 2000 ms；`src/tui/terminal_reports.ts:207-245` 串行查询和 raw generation；`src/tui/terminal_reports.ts:251-261` 只关闭自己的代理，保留真实 stdin。 | Python 适配可换实现，保留查询有界、取消安全、背压、raw 不被旧查询回滚、退出恢复终端的契约。 |
| 编辑/模态/排队 | `src/tui/app/App.tsx:216` text+cursor 单状态；`src/tui/app/App.tsx:869-1090` 多种选择器/审批/询问优先；`src/tui/app/App.tsx:1194-1292` busy 排队、历史、编辑、补全。 | 所有输入最终汇入同一个调度入口；模态优先级、草稿、cursor、历史不得被流式输出或后台更新重置。 |
| 粘贴/附件 | `src/tui/app/App.tsx:1295-1357`：usePaste 不自动提交，按模态路由；图片路径读取与 5 MB magic-byte 识别；普通大段折叠。 | 粘贴是文本/附件事件而不是逐个 Enter；显示占位符与提交的全文分离，图片读取失败退回原文本。 |
| 滚动/流式渲染 | `src/tui/app/App.tsx:189-208`、`src/tui/app/App.tsx:1364-1369`、`src/tui/app/App.tsx:1451-1487`：Static 历史与受屏高限制的动态预览；Windows 从首帧固化 welcome。 | 历史留在终端原生 scrollback，动态预览可裁剪但完整事件/最终答案不丢；显示重建不能重跑任务。 |
| resize | 本地 Ink patch 清除旧动态帧物理行；App 对专属 viewport 再做合并重建，见第 3 节。 | 狭窄/矮窗口、连续缩放、宽字符 reflow、流式/模态/草稿并发必须真实验证。 |

### 2.1 不可省略的交互语义

- **Esc 有上下文顺序**：先由模态处理；普通运行/等待状态若有未消费排队输入，第一次只清排队，下一次才 abort 当前回合并 pause scheduler；输入框空时回填上一条提交，已有新草稿不覆盖。`src/tui/app/App.tsx:977-981`、`src/tui/app/App.tsx:1043`、`src/tui/app/App.tsx:1102-1119`。不能把所有 Esc 一律映射退出。
- **Ctrl+C 为两次退出确认**，2 秒窗口；`run.tsx` 明确关闭 Ink 自带 Ctrl+C 直接退出，避免两套机制争抢。`src/tui/app/App.tsx:1121-1126`、`src/tui/app/run.tsx:12-14`、`src/tui/app/run.tsx:47-50`。另外进程 SIGINT/SIGTERM 处理会清理资源，不能混同 UI 键事件：`src/index.ts:177-195`。
- **Ctrl+B** 仅 busy 时尝试转后台；没有可转前台调用则返回 0，静默。转移后解绑原 abort、把生命周期交给后台管理者。`src/tui/app/App.tsx:1150-1156`、`src/tools/exec_shell.ts:246-253`。**Ctrl+T** 运行/等待期间只读查看任务，关闭不取消；**Ctrl+G** 导航历史；**Ctrl+O** 展开最近可展开项并影响后续显示；**Shift+Tab** 切权限模式。`src/tui/app/App.tsx:1093-1100`、`src/tui/app/App.tsx:1128-1192`。
- **busy 时 Enter 排队**，scheduler 存在时直接 `submit(ev)`；旧路径 `queueSteering` 在工具轮边界消费，不需等整轮结束。粘贴展开在提交前完成，队列的可视状态与调度状态需对照。`src/tui/app/App.tsx:1194-1220`；现有回归断言 `src/tui/app/App.test.tsx:1353-1424`。
- **粘贴归一化**：CRLF 与裸 CR 转 LF；超过 280 个 JS UTF-16 code units 或去末尾换行后超过 6 行折为占位符，提交再展开；少量单/多行均不自动提交。`src/tui/app/App.tsx:1342-1357`、`src/tui/app/App.tsx:288-327`。Python 的 `len(str)` 与 JS `.length` 对非 BMP 字符不同，应明确阈值计量并登记差异，不能悄悄改变边界。
- **中文宽字符不是完整 Unicode 编辑支持**：`displayWidth` 以码点范围粗计 1/2 列，combining mark、variation selector、ZWJ 不特殊处理；编辑左右/删除则按 JS 字符串索引 ±1。`src/tui/width.ts:1-26`、`src/tui/app/App.tsx:1241-1260`。现有 width 测试主要是 ASCII/CJK/空串/补齐（`src/tui/width.test.ts:4-23`），不能证明 IME composition、emoji grapheme、候选窗或光标实机正确。建议 Python 明确区分内容、grapheme、显示 cell，补齐 Windows 中文体验。
- **退出清理必须区分正常退出、显式中断和保留后台**：入口保存/关闭 scheduler/MCP/LSP/store，finally 根据 keepBackgroundOnExit detach/reset。`src/index.ts:2673-2692`；不要为了“杀干净”让保留后台和自身会话恢复失效。强制终止进程无法指望 finally 执行，应单列可恢复性实验，而非承诺任意强杀都能原地恢复终端模式。

## 3. 本地 Ink、品牌和 mascot 覆盖层

这些均已在冻结快照，不是可丢弃的未跟踪草稿；迁移应记录对应模块和行为。快照清单见 reference manifest，当前来源说明明确将本地源码和未跟踪源码都纳入参照。

| 覆盖层 | 静态事实 | 迁移/证据处理 |
| --- | --- | --- |
| `patches/ink+7.0.5.patch:5-21` | width 增减都处理；以当前宽度 hard-wrap 旧动态帧，按重排后的物理行数 eraseLines，reset log 缓存；原条件只处理变窄。 | 不能把 patch 本身移植到 Python；要保留“缩放后无旧帧残影、不擦错行”的验收。它不独自解决应用 Static、Sixel 或 IME。 |
| `src/tui/brand.ts:1-3` | 展示名“若存 Code”、固定短句；注释明确仅展示层，命令/包/配置/模型身份原约定。 | RuoCun/ruocun 已由 ADR 确定；显示品牌与兼容配置命名分开登记，不从这两行推导所有运行时路径都该改名。 |
| `src/tui/Welcome.tsx:18-43`、`src/tui/Welcome.tsx:46-120` | 卡片最大 146 列居中，Sixel 留白须满足左右布局，窄窗降为文本；订阅 resize；固定短句/真实 cwd/分支/版本。 | 不支持图形/探测失败必须可读，不能把图片当启动依赖。 |
| `src/tui/app/App.tsx:204-208` | Windows 静态欢迎屏是默认行为；代码注释将它归因于 ConPTY 前端残影。 | 注释是来源开发者的原因说明，不作为本轮重现实测。 |
| `src/tui/app/App.tsx:1380-1414` | 仅 ownedViewport 做 200 ms 合并重建，等待 render flush，清专属屏幕与 scrollback，Static key 递增；generation 淘汰迟到结果。共享终端不走这条全清屏。 | 两种 viewport 必须分场景。不能把所有用户终端都当作可清 scrollback 的专属窗口。 |
| `src/tui/app/run.tsx:16-58` | 可选诊断只记布尔/计数/几何；启用报告后 probe 再创建 motion；exit/finally dispose，并 flush 最后一笔输出。 | 保留诊断脱敏与资源生命周期；图形控制不进入业务 transcript。 |
| `src/tui/mascot.ts:36-58`、`src/tui/mascot.ts:69-141` | 只在空闲首页且无草稿/焦点丢失/模态/后台任务时推进动画；flush 后 CPR 定锚，拒绝屏外或不可知几何；独立 stdout 单笔 save-cursor→定位→Sixel→restore-cursor，最多一图在途。 | 与普通渲染器要有串行输出/flush 协议；不能另开线程无锁写终端。探测失败停图，不猜坐标。 |
| `src/tui/mascot.ts:144-197`、`src/tui/app/App.tsx:1420-1443` | resize 暂停、重新 probe 后等待新 epoch；Static 测量未知时抑制猜测；modal/background 等独立 pause 条件保留。 | 单测可重写，但实际缩放和 Sixel 残影只能靠真实前端验证。 |
| `src/tui/mascot_frames.ts:1-11`、`scripts/generate-mascot-data.mjs:9-55` | 已内嵌 Sixel 帧及来源 PNG SHA；生成器校验 256×244 不透明整矩形、背景、六帧 ID、hash 和时序，默认依赖快照外预览 manifest，写回 TS 数据。 | 运行时帧和时序可作为数据转换后复用并保留 provenance；源码内“已验收”注释只代表来源记录。本轮未取得外部 PNG/manifest 或验收日志，不把可再生性/原图授权状态视为已核实；正常构建无需重新生成。 |
| `src/tui/tab_attention.ts:18-65` | 任务标题前置、展示名后缀，标题去控制字符并截短；OSC 0/ST，push/pop title，开启 focus；黄/绿状态只改标签，不响铃；dispose 恢复。 | 标题/焦点与桌面通知不同；支持与否按真实终端测试，不用标题状态代替任务完成证据。 |

覆盖层已有相关 `Welcome`、`App`、`Onboarding`、`tab_attention`、`terminal_reports`、`mascot` 测试。`src/tui/app/App.test.tsx:1-49` 使用 ink-testing-library、mock deps/motion；它们是交互状态的有价值断言，仍不是 Windows Terminal 验收录像。`src/tui/terminal_reports.test.ts:31-224` 覆盖分片、延迟、Unicode、粘贴、Esc、raw 和 dispose；`src/tui/mascot.test.ts:49-257` 覆盖锚点、backpressure、旧 epoch、失败探测与卸载。

## 4. Windows：已补齐、明确空缺与静态风险

### 4.1 已存在的平台分支

| 能力 | 快照证据 | 本轮能/不能确定的事 |
| --- | --- | --- |
| 进程身份 | `src/session/process_identity.ts:11-30`、`src/session/process_identity.ts:35-74`：PowerShell CIM 查 boot/CreationDate UTC ticks，隐藏窗口，10 s 上限；host+boot+pid+start 防 PID 复用；拒绝非法 PID，权限错误不冒充死亡。 | Windows 已有实现，不再称“全部缺失”。`src/session/process_identity.test.ts:7-56` 是 Windows-only 测试，在 Ubuntu skip；本轮未运行，仍待真实身份/权限/重启实验。 |
| TUI/粘贴 | Windows 默认 Static welcome；CRLF/CR 粘贴归一化。 | 逻辑已在源码，IME、宽字符、连续 resize 仍待真实前端。 |
| 通知 | `src/tui/notifier.ts:51-56` 用 Windows Forms NotifyIcon BalloonTip，保持 PowerShell 5 s 后 dispose；`src/tui/notifier.test.ts:62` 检查脚本文本含延时。 | 有 best-effort 实现，不能说没有 Windows 通知。未保证 toast、通知中心留存、点击回到正确 tab、勿扰模式或系统关闭通知时行为。 |
| 其它适配 | `src/permissions/settings.ts:67-70` Windows managed-settings 路径；`src/index.ts:2301` 复制文本选 `clip`。 | 路径/命令存在不等于 ACL、Unicode clipboard 和端到端兼容均已验收。 |

### 4.2 需要实现或单独证明的平台能力

| 域 | 源码事实 | 风险/建议（不是本轮实测结论） |
| --- | --- | --- |
| 系统定时 | `src/schedule.ts:5-25`、`src/schedule.ts:29-52` 只读写 crontab，POSIX 单引号，`cd && dao >> "$HOME/.dao/schedule.log"`；read 任何错误当空列表。 | **明确无 Windows 后端。** 建议保留 schedule 模块和 CLI 语义，在 Windows 对接 Task Scheduler；不要用会话内 `/loop` 替代系统定时。[Task Scheduler 官方](https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page) 的 trigger/action 是底层能力，不等价任意五字段 cron。设计需说明 cron 映射/dispatcher、时区、DST、休眠漏触发、并发、身份及升级后 exe 路径。 |
| 进程树取消 | `src/tools/exec_shell.ts:193-211`、`src/tools/process_manager.ts:41-48` 负 PID 组信号失败退为 child.kill；`src/tools/shell_runner.ts:74-88` 负 PID SIGTERM catch 后无 child fallback。 | **静态高风险**：Node 官方明确 Windows 用 PID 杀进程组会报错；child fallback 也不能据此证明所有后代结束。[Node 22 process.kill](https://nodejs.org/docs/latest-v22.x/api/process.html#processkillpid-signal)。建议 Python Windows 原生 Job Object 管理受管命令树，温和取消与超时强制收口分层，必须实测孙进程/管道继承/owner 退出；Job Object 不等于文件/网络沙箱。[Job Objects 官方](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) |
| runner IPC | `src/tools/managed_shell.ts:17-29` 构造 tmpdir/`/tmp` 下 filesystem endpoint，限制 104 bytes；`src/tools/managed_shell.ts:89-96` 将字符串传 createConnection；`src/tools/shell_runner.ts:178-195` 传 server.listen 并 unlink。 | **静态平台风险**来自实际 Node IPC path 契约，而非 `.sock` 后缀：官方 Windows 本地 IPC 使用 `\\?\pipe\`/`\\.\pipe\` named pipe 命名空间，生命周期也不同。[Node 22 net IPC](https://nodejs.org/docs/latest-v22.x/api/net.html#identifying-paths-for-ipc-connections)。Python 候选为受 ACL/随机 capability 保护的 named pipe，或显式认证的 loopback transport；保留 token/runId/epoch 与恢复语义，不直接照搬 Unix pathname。Python asyncio Windows 不提供 create_unix_server/add_signal_handler 等接口：[官方平台差异](https://docs.python.org/3.13/library/asyncio-platforms.html#windows)。 |
| 凭据 | `src/config/keychain.ts:16-57` 仅 darwin/linux；`src/config/credential.ts:33-45` 失败回落 inline key；`src/config/profiles_store.ts:33-38` chmod 0600 失败可忽略。 | **明确无 Windows 系统凭据适配。** 用同一 KeychainPort 语义接 Windows Credential Manager（Python ctypes/pywin32/keyring 后端候选，未选定）；以 profile/account 分隔、拒绝时有界、失败不误报保存成功。[CredWriteW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credwritew)、[CredReadW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credreadw)。0600 是 Unix 权限数字，不能当作 Windows ACL 证明；要检查真实用户权限与 fallback 明文行为。 |
| 唤醒锁 | `src/tui/wakelock.ts:5-17` 只启动 caffeinate/systemd-inhibit；`src/index.ts:1524-1534` 每轮 acquire/finally release。 | **明确无 Windows 实现。** 候选 `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)`，释放须在同一持有线程正确配对，嵌套任务引用计数；默认不请求屏幕常亮，不擅自使用媒体 away mode。该 API 不可阻止用户主动休眠：[官方说明](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate)。 |
| 剪贴板图片 | `src/tui/imagePaste.ts:1-8` 非 macOS 返回 null，`src/tui/app/App.tsx:1303-1313` 空 paste 只在 macOS 读图片。 | **明确无 Windows 图片 clipboard 读取。** 图片文件路径附件是另一条已实现入口；需 Python 平台适配并测试中文/空格路径、RGBA、空剪贴板、超 5 MB 和失败不丢文本。 |
| OS 沙箱 | `src/tools/sandbox.ts:41-65` 仅 Seatbelt/bwrap，Windows 启用时返回“不支持”。 | **明确平台缺口。** Windows 进程 Job、权限审批、只读文件工具检查均不能宣称等价 OS 文件/网络隔离。应另列 Windows 隔离后端研究/原型，确定能复现的约束，不把 WSL 或 Linux 容器通过当成本机全功能通过。 |
| Shell/环境探测 | `src/tools/exec_shell.ts:185-189` 默认 shell:true；`src/env_snapshot.ts:15-31` 用 POSIX `v=$(...)`、head、`2>/dev/null`，`src/env_snapshot.ts:97-103` 同样负 PID；doctor 使用 `command -v`（`src/index.ts:2086-2095`）。 | **静态语义不匹配风险**：Node Windows 默认 shell 是 ComSpec，不是 Bash/PowerShell。[Node shell requirements](https://nodejs.org/api/child_process.html#shell-requirements)。Python 应用 subprocess argv 原生探测，明确 Shell 方言、编码和 .cmd/扩展启动契约；权限分析不能拿 Bash parser 当作 PowerShell 语义解释器。 |
| 隐藏窗口/退出 | `src/tools/managed_shell.ts:195-199`、`src/tools/shell_runner.ts:116-121` detached 启动，未显式 windowsHide；身份查询则明确隐藏。 | Node 官方 Windows detached 可能有独立 console。[Node detached](https://nodejs.org/api/child_process.html#optionsdetached)。Python 中区分交互前台、受管后台、跨 owner 存活 runner；按场景选择 flags/stdio/Job，实际观察有无多余窗口。不能全局 KILL_ON_JOB_CLOSE 破坏 keep-background。 |
| 落盘/恢复 | `src/session/durable_file.ts:4-27`、`src/session/durable_file.ts:31-55` 临时文件 fsync、rename、父目录打开/fsync；runner start claim 也 fsync 目录（`src/tools/shell_runner.ts:98-105`）。 | **可移植性待证明**：目录 handle、ACL、文件被占用、rename 原子性与同步保证按 Windows 原生语义实现；本轮未执行，不能仅因 POSIX 形式断言一定失败。验收含断电级承诺边界、异常退出、receipt 附件丢失、PID 重用及绝不重复启动。 |
| 通知载荷/恢复焦点 | `src/tui/notifier.ts:55-56` 将 JSON.stringify 结果拼进 PowerShell `-Command`；`src/tui/tab_attention.ts:24-65` 只有标题协议。 | **静态注入/转义风险**：JSON 双引号不是 PowerShell literal；`$变量`、`$(表达式)` 在 PowerShell 双引号中仍展开。[PowerShell 引号规则](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules)。候选原生通知调用或固定脚本+数据通道；至少用无副作用字面载荷验证。toast/点击激活正确窗口或 tab 若纳入期望，另做原型；不得把 BalloonTip 单测当作已达成。 |

Windows shell 进程的 SIGTERM、CTRL_BREAK、普通 `terminate()` 不是同义操作。Python 官方说明 Windows terminate 用 TerminateProcess，kill 是其别名，控制事件需要 CREATE_NEW_PROCESS_GROUP；这只是设计依据，不能推出后代已全部退出。[Python subprocess](https://docs.python.org/3/library/subprocess.html#subprocess.Popen.send_signal)

## 5. 原验证资产：复用方式与完整盘点

### 5.1 分类原则

| 分类 | 可继承对象 | 不能继承的结论 |
| --- | --- | --- |
| D — 可复用数据 | JSON/JSONL gold、任务输入、工作区样本、前后文本、协议样本、帧/时序/来源 hash、语言资源；复制/转换保留来源与许可。 | fixture 正确性、金标质量、脱敏和许可证仍需核查；旧报告分数不是 RuoCun 分数。 |
| R — 可跨语言回放 | 把输入/事件与预期输出提取成语言无关 trace；跨 CLI 驱动进程、模拟 HTTP/SSE/MCP 服务；业务结果以规范化 JSON/文本/文件状态断言。 | 导入 TS 私有类、prototype monkeypatch 或硬编码旧 session 格式的脚本不能直接变成 Python 测试。 |
| S — 需语义重写 | Vitest/React/Ink 测试、JS Date/path/UTF-16 行为、真实进程/FIFO/Unix socket、TypeScript 编译与 ESLint、Bun 自启动检测。 | 逐行翻译或测试数量相同不等于行为完整；要覆盖正/反/取消/错误和真实 OS 资源。 |
| P — 保留评估协议 | 模型质量、反思/记忆 judge、Terminal-Bench/SWE-bench、真实 cache/memory、题目 A/B/多采样/超时口径、隐藏测试/双轨/费用与轨迹归档。 | 非确定性 rerun、历史成绩、LLM 自述、预览图不能成为确定性工程门禁或产品验收。 |

### 5.2 单测资产

Vitest 配置的 environment 为 `node`，setup 为 `tests/setup.ts`，include 覆盖 `src/**/*.test.ts(x)` 和 `evals/**/*.test.mjs/ts`：`vitest.config.ts:3-8`。setup 默认中文：`tests/setup.ts:1-4`。静态计数为 **src 203 + evals 12 = 215 文件**；其中 evals 是 memory 10、reflect 1、score 1。不是 215 个 test case，也不表示本轮有任何通过项。

| src 域 | 测试文件数 | 迁移重点/分类 |
| --- | ---: | --- |
| agent | 37 | 调度、background、wait、恢复、反思/压缩/预算、子代理/工作树；D/R 抽状态轨迹，S 重写并发/取消，P 分离模型质量。 |
| tools | 56 | 文件、搜索、Shell、process manager、managed runner、MCP/LSP 工具、任务与权限门控；D/R 输入输出与文件状态，S Windows 资源生命周期。 |
| tui（含 app/onboarding） | 25 | welcome/render/theme/width、terminal reports/mascot、模态、粘贴、排队/中断、resize；R 事件、S 组件与协议单测，再加真实终端验收。 |
| permissions | 15 | 路径/规则优先级/Bash AST/安全与分类；D 语料，S 方言及 OS 路径行为。 |
| memory | 11 | 存储、衰减、GC、图与 frontmatter/injection；D 样本，S 语义。 |
| config | 10 | profile/credential/gateway/account/auth；R 端口，S 原生凭据。 |
| skills | 9 | 发现、解析、信任/安装/选择；D 文本与目录样本，R/S 行为。 |
| session | 8 | durable store/SQLite/lease/事件恢复/process identity；S 真实文件/进程与故障注入；自身会话完整恢复必验。 |
| mcp、obs、repomap | 各 4 | MCP 连接/重连/扩展，观测脱敏/生命周期，代码地图；R 协议，S 库绑定。 |
| client、commands、lsp | 各 3 | 流式/provider/请求参数，命令边界，LSP manager/config；D/R HTTP/协议 fixture，S 适配。 |
| approval、hooks | 各 2 | 并发审批、事件匹配/超时、执行权限；R/S。 |
| 根文件和其它 | 7 | env_snapshot、plugins、project_doc、repl、schedule、i18n、prompt/system_prompt；D/R 规范化语料，S 平台实现。 |

附录 A 精确列出 215 个相对路径，避免仅靠代表文件遗漏。原测试大量 fixture 在测试函数内创建临时目录、mock stream/client、事件数组，不能只搬独立 fixtures 文件夹；例如 `src/tui/app/App.test.tsx:20-49` 是 mock AppDeps/motion；`src/tui/terminal_reports.test.ts:150-224` 是合成字节流；`src/tools/managed_shell.test.ts:29-137` 则明确用真实进程验证 durable 边界。Windows-only 身份测试应纳入 Windows CI，不能接受在 Linux skip 后宣称覆盖。

### 5.3 独立 fixture 与任务

- **memory**：extract 9 个目录，每个 conversation.jsonl+gold.json，共 18 文件；recall 8 个目录，context.json+store Markdown，共 53 文件；`_synthetic` 也会跑。schema/金标来源和人审/脱敏局限：`evals/memory/README.md:34-56`。D 复用数据；R 复用输入/输出 schema；S 重写 extractor/recall adapter 和统计；P 保留 judge K 次多数票，空票不自动满分。不能把 injection A/B 的 judge 模拟当真正多轮 memory_read 回合。
- **reflect**：6 个目录、12 文件，3 报警+3 正控；conversation JSONL+gold 的 expectOnTrack/expectFlag。`evals/reflect/README.md:7-43`。D/R 保留；P 保留报警 P/R/F1 与 advisory 命中率；既有 grade.test 是纯计算 S。
- **MCP**：`src/mcp/__fixtures__/fake-mcp-server.mjs:1-17` 是真实 stdio 进程，默认 echo，rich 模式加 resource/prompt/elicitation，跨重启计数触发一次崩溃。保留它作为外部 Node server 可以验证“Python 核心兼容外部命令”，也可再写 Python fixture 交叉验证；生产不因此依赖 Node。LSP `src/lsp/testfixtures/sample.ts:1-19` 是输入数据，可保留语言与语义，勿把它改成 Python 后丢 TS LSP 场景。
- **evals/tasks**：10 个 OSS task、4 个 double（01、02、06、L1）、2 个 local（04、05），另有 90 模板；16 个 task.json 及 workspace/tests/check 脚本清单见附录。来源 README 任务表未列 06，但文件真实存在，以枚举为准。JS/Python 任务工作区与外部验证命令是被测编码任务，不随 RuoCun 语言改变；可保持原语言 verifier。D/R/P 保留任务、base/fix SHA、隐藏 tests、fail2pass+pass2pass、checkpoint 权重。`evals/run.mjs:87-125`、`evals/run.mjs:179-231`、`evals/run.mjs:276-299`；weighted completion 与 horizon 数学实现：`evals/score.mjs:5-70`，纯逻辑 S 或独立跨语言 oracle。
- **素材完整性**：快照不含被忽略的运行产物、下载数据、模型凭据、完整依赖；不能据脚本路径假设历史会话/PNG/容器/评测结果原始日志全在。`evals/memory/BASELINE.md`、`evals/terminal-bench/results.html`、`solutions-reference.md` 等是历史/参考资产，不是当前通过证明。

### 5.4 scripts 的真实性质（58 文件，附录 B 全列）

| 组 | 文件/入口与证据 | 迁移处置 |
| --- | --- | --- |
| 确定性语义与运行时探针 | `verify-memory.ts`、`verify-persistence-runtime.ts`、`verify-background-wait.mjs`、`verify-background-recovery.ts`、`verify-recovery-entrypoints.mjs`。前者临时记忆算法；persistence 验 WAL/FULL、commit/rollback/重开（`scripts/verify-persistence-runtime.ts:5-25`）。wait 注入 fake HTTP/SSE，但使用真实 Bash/FIFO/进程（`scripts/verify-background-wait.mjs:1-57`）。 | D/R 提取 trace 和断言；S 用 Windows 原生 worker/pipe/event 替代 mkfifo、Bash、preload。不得把 fake-model CLI smoke 写成真实模型验收。recovery-entrypoints 的 legacy DAO 导入断言不属于“迁移旧 DAO 会话”的要求，应改成 RuoCun 自身保存/恢复场景（`scripts/verify-recovery-entrypoints.mjs:12-18`）。 |
| live 后台/恢复 | `verify-background-wait-live.mjs`、`verify-background-recovery-live.mjs`，真实 CLI/HTTP，加载 active profile、在 prototype/fetch 上埋观察；wait-live 还要求特定 GLM profile（`scripts/verify-background-wait-live.mjs:1-4`、`scripts/verify-background-wait-live.mjs:29-39`、`scripts/verify-background-wait-live.mjs:68-87`）。 | P 保留协议、预算、事件顺序、恢复不重复启动证据；R/S 去 TS prototype 和 Unix endpoint，明确模型/provider/版本/任务提交条件。 |
| 专题 introspect/replay | async-taskgroup、FEAL、model-extraction、openssl、write-compressor、largest-eigenval、fasttext、TuneMJCF、ARS、video、grep 等 38 文件（附录 B 的模型专题组）。`streamChat` 调真实模型、VERIFY_N 多采样；部分还接真实工具，部分只让模型解释某轨迹。 | 主要 P，能提取的 JSON/文本为 D/R；不能把模型自述当因果证明。大量 `/Users/...`、`/private/tmp/...`、`/tmp/*sysprompt` 不在快照：如 `scripts/introspect-feal-brute-force-full-space.ts:25-35`、`scripts/verify-installwindows-candidate-replay.ts:10-16`。先材料化可分发 fixture，检查提示是否泄漏标准答案，再做候选 A/B。`installwindows` 系列是 QEMU 安装 Windows 任务的模型轨迹，不是 DAO 在 Windows 宿主功能测试。 |
| 真网络记忆/缓存 | `accept-memory.sh`、`accept-cache.sh`、`debug-distill.ts`、`verify-reflect.ts`。shell 脚本显式真 key/费用/人或模型判读（`scripts/accept-memory.sh:1-13`、`scripts/accept-cache.sh:1-9`）。 | P 保留冷/热 cache 与跨会话记忆问题，S 改 Python 编排；旧 memory 脚本仍预期退出蒸馏（`scripts/accept-memory.sh:17-22`），当前入口注释说退出不再蒸馏（`src/index.ts:2683`），存在漂移，不能直接当现行 oracle。 |
| 调试/预览/资源/发布 | `dump-harness-wire.ts`、三个 preview/welcome、三个 VHS `.tape`、`generate-mascot-data.mjs`、`sync-version.mjs`。 | harness 数据可 R；预览/VHS 保留视觉脚本的意图（有 POSIX `/tmp` 场景和清理命令，不直接执行）；mascot D+S；版本同步由 Python package metadata 单源替代。 |

专题组 38 文件都静态检出 `streamChat` 调用入口；分类和精确路径见附录 B，不以命名猜测全部可离线执行。

### 5.5 评估工具与外部运行环境

| 资产组（附录 C 列全） | 快照证据 | 分类及边界 |
| --- | --- | --- |
| 核心 task runner | `evals/run.mjs:35-43` 锁 tsx/index，RUNS 默认 3、timeout、模型；`evals/run.mjs:74-80` AUTO_APPROVE；`evals/run.mjs:251-257` 归档轨迹/diff/双轨日志。 | R/S 替换 Python CLI 入口，P 保留多次稳定成功、环境无效/跳过、费用/工具数/时间与 trace；不要将工具数用文本箭头计数视为稳定协议。 |
| horizon/score | `evals/score.mjs:5-70`；`evals/README.md:115-124` 读 meta 拟合。 | D/R 公式/样本，S 重写纯函数、退化样本和阈值；P 保留 p50/p80 口径与不确定性，少量样本不作可靠委托结论。 |
| trace 物化/HTML | `evals/materialize-trace.mjs:1-12`、`evals/materialize-trace.mjs:133` 读取 state 和各 trace；`evals/render-trace.mjs:20-38`、`evals/render-trace.mjs:71-77` 使用 viewer template。 | 旧内部 session→trace 是 S；若抽象 JSON schema 固定，可 R 继续用 HTML 模板。用户会话/请求/工具输出须先脱敏，旧 DAO session 无需兼容。 |
| memory eval | run/extract/recall/injection_ab/report + lib/{creds,judge,metrics,redact,transcript,types}；`evals/memory/README.md:7-27`、`evals/memory/README.md:47-56`。 | D/R fixtures，S 指标/报告/适配，P 真模型 judge 与 proxy 局限；纯单测进 CI，真实跑批单列。 |
| reflect eval | run/grade、fixtures；`evals/reflect/README.md:20-31`。 | D/R/S 纯输入/评分，P 真模型结果；有正控，不能只测召回。 |
| Docker 资源 | 5 Dockerfiles（node、python、python-ds、java、cpp）；`evals/docker/README.md:5-13`、`evals/docker/README.md:29-63` host-agent+bind mount、测试断网/降权/限额、缺 Docker 跳过；tag 未 digest 固定。 | D/P 保留工具链及验证协议；Windows 宿主挂载/中文路径另测；容器测试不等于 Windows 原生进程/终端；真正复现需记录 digest 与依赖锁。 |
| SWE-bench | adapter.mjs/adapter_v2.mjs/container_helper.py；v2 要显式 harness venv 路径、Linux x64 binary，容器运行/取 diff/取 trace，最后交官方 harness（`evals/swebench/adapter_v2.mjs:26-42`、`evals/swebench/adapter_v2.mjs:82-128`）。 | P 保留 external dataset/ref/prediction 和官方 verifier；S/R 包装入口；两版保留审计关系。不会因工具已有 Python 文件就自动满足核心 Python 迁移。 |
| Terminal-Bench/Harbor | `evals/terminal-bench/agent/harbor_dao_agent.py:50-84` 装 Linux 双架构 binary，`evals/terminal-bench/agent/harbor_dao_agent.py:107-145` --eval/yolo 与独立 20 s snapshot；脚本 build Linux x64/arm64（`evals/terminal-bench/agent/build-binaries.sh:11-13`）；split/meta/overrides、结果聚合/图表/诊断/批处理。 | P 保留 task/version/timeout/verifier、资源与失败归因；D 任务标签，R/S 改安装为 Python/standalone。README 提到的旧 dao_code_agent.py 不在快照，不能伪造复用。历史 70/89 等仅来源历史叙述；held_out 曾参与统一迭代（`evals/terminal-bench/README.md:118-136`），不能宣传为严格未见验证集。 |

## 6. npm、构建、安装、CI 与发布

`package.json:24-44` 的 20 个 script 完整对应如下。

| script | 当前命令/性质 | Python 对应建议 |
| --- | --- | --- |
| dev | tsx src/index.ts | `python -m ruocun`（开发 venv） |
| build | tsc -p tsconfig.build.json | typecheck 与 wheel build 分开，不把编译当功能验证 |
| postinstall | patch-package | 目标不照搬；终端依赖适配/补丁纳入固定版本与安装产物验证 |
| bundle | sync-version + bun build --compile | Windows 原生 standalone build |
| bundle:install | cp 到 ~/.local/bin + codesign | macOS 专用便利脚本；Windows 安装器另做 |
| start | node dist/index.js | 安装后的 ruocun entry point |
| preview:welcome / preview:taiji / preview:ink | 三个 tsx 预览 | Python 显示探针，真实 Terminal 截图 |
| test / test:watch | vitest run / vitest | pytest/async 集成测试 |
| typecheck / typecheck:eval | tsc 两套配置 | Python 类型检查；评估依赖分组 |
| prepublishOnly | npm run build | build artifact 校验与干净安装门禁 |
| verify:mem | verify-memory.ts | 确定性记忆语义探针 |
| accept:mem / accept:cache | Bash 真网络脚本 | 单独 live eval 协议与费用记录 |
| debug:distill / debug:harness-wire | tsx 调试脚本 | 脱敏诊断和协议导出，不进普通安装必跑路径 |
| lint | eslint . | Python lint/format 检查（例如 Ruff） |

静态发布事实：

- npm bin 是 dao→dist/index.js，Node >=20，files 白名单只有 dist/README/CHANGELOG/LICENSE（`package.json:10-23`）。`build` 不触发 sync-version；sync-version 由 bundle 调用（`package.json:26-29`、`scripts/sync-version.mjs:1-13`）。release workflow 直接 bun build，未调用 sync-version（`.github/workflows/release.yml:22-30`），版本一致性要另验。
- **local patch 的交付不能默认成立**：postinstall 是 patch-package，但 patch-package 仅 devDependency，files 白名单不含 patches（`package.json:14-20`、`package.json:27`、`package.json:79-92`）。这是需用最终 npm tarball/干净生产安装证明的问题；本轮未 npm pack、未安装，不能断言线上安装一定失败或补丁已生效。Python 对应必须检查最终 wheel/exe，不能只测源码 checkout。
- `better-sqlite3` 为 Node native dependency（`package.json:69`）；Bun 用内置 SQLite、Node 动态 require 外部驱动（`src/session/sqlite.ts:12-22`）。Python 可换标准库 sqlite3，但需迁移事务、WAL、超时、锁/故障/恢复语义，而非继承“已打包可用”的假设。
- CI 只有 Ubuntu × Node20/22，npm ci→lint→typecheck→test→build（`.github/workflows/ci.yml:9-24`）。没有 Windows job、macOS job、真实终端体验、干净产物安装、typecheck:eval 或 live eval 步骤。release 为 v* tag，Ubuntu 下载 Bun 后五目标交叉编译，再上传 GitHub Release；无产物运行门禁/签名或 checksum 步骤（`.github/workflows/release.yml:3-35`）。未发现 npm publish CI。
- `install.sh:10-20` 只接 Darwin/Linux；Windows 提示 npm 全局安装或 exe 手工下载。`install.sh:23-39` 下载 latest，chmod、macOS 去 quarantine、移动到 ~/.local/bin；脚本中没有校验和核验。快照无 `.ps1/.cmd/.bat` 原生安装脚本。Python Windows 用户安装、升级、PATH、卸载和非管理员权限流程需有独立配套。
- qemu-startup workflow 是一次 Linux 原生 x86_64 Docker/QEMU 一次性诊断，不涉及 DAO 或模型；不能当 Windows 或产品回归 CI（`.github/workflows/qemu-startup-native-probe.yml:1-15`、`.github/workflows/qemu-startup-native-probe.yml:23-48`）。

## 7. Python 终端候选：官方依据与选择条件

当日读取的一手文档页面版本标识包括 prompt_toolkit 3.0.52、Rich 14.1.0、PyInstaller 6.22.3。官网 stable/main 会变化；这些是研究时内容，**不是已安装/锁定/实测的依赖组合**。后续原型必须记录实际 lock、Python/终端/OS 版本和依赖源码提交，不能只写“最新版支持”。

| 候选 | 官方能力证据 | 与目标的关系与未证实事项 |
| --- | --- | --- |
| prompt_toolkit 主交互 | [官方首页](https://python-prompt-toolkit.readthedocs.io/en/stable/) 声明 Windows、中文双宽、多行编辑/补全；[asyncio](https://python-prompt-toolkit.readthedocs.io/en/stable/pages/advanced_topics/asyncio.html) 提供 run_async；[异步 prompt](https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html#prompt-in-an-asyncio-application) 提供 prompt_async+patch_stdout；[键绑定超时](https://python-prompt-toolkit.readthedocs.io/en/stable/pages/advanced_topics/key_bindings.html#timeouts) 说明 Esc/多键歧义。 | 优先探针：可围绕 inline 输入和异步 transcript 组织，保留目录职责；要实际验证低延迟 token 输出、历史 scrollback、不自动提交粘贴、IME、modal、光标和 Sixel。仅 patch_stdout 的打印示例不证明适合高频逐 token 图形渲染。 |
| prompt_toolkit Windows 后端 | [官方 input defaults](https://raw.githubusercontent.com/prompt-toolkit/python-prompt-toolkit/master/src/prompt_toolkit/input/defaults.py) 在 win32 选 Win32Input；[win32 reader](https://raw.githubusercontent.com/prompt-toolkit/python-prompt-toolkit/master/src/prompt_toolkit/input/win32.py) 探测 VT input，并在 VT/native console reader 间选择，使用 ReadConsoleInputW、surrogate 处理/粘贴识别；[output defaults](https://raw.githubusercontent.com/prompt-toolkit/python-prompt-toolkit/master/src/prompt_toolkit/output/defaults.py) 选 Windows VT/Win32/ConEmu 输出。 | “原生 Windows 输入适配”并不必然要求另写全部 Win32 parser；先观察所选后端与缺口。若框架吞/泄露 DA/CPR 等，围绕同一输入 owner 写适配或向上游修复；禁止再加第二 reader 抢 stdin。 |
| Textual 主交互 | [Requirements](https://textual.textualize.io/getting_started/#requirements) 声明 Python>=3.9 和 Windows Terminal；[Paste](https://textual.textualize.io/events/paste/)、[Resize](https://textual.textualize.io/events/resize/) 有事件；[Windows driver 官方源码](https://raw.githubusercontent.com/Textualize/textual/main/src/textual/drivers/windows_driver.py) 管理 writer/input 线程和 bracketed paste，配套 [win32.py](https://raw.githubusercontent.com/Textualize/textual/main/src/textual/drivers/win32.py) 保存/恢复 ConsoleMode。 | 完整组件/布局/模态有利，但 [Windows inline 不支持](https://textual.textualize.io/guide/app/#run-inline) 是当前与原体验的明确差距。只做对比探针，不以全屏替换后就宣布兼容；额外自写 Windows inline driver 是实质工作。 |
| Rich 内容层 | [Introduction](https://rich.readthedocs.io/en/stable/introduction.html) 声明 Windows Terminal/Windows、Markdown/表格/语法高亮；[Live](https://rich.readthedocs.io/en/stable/live.html) 提供动态显示/可选 alternate screen、默认重定向 stdout/stderr。 | Rich 本身不提供与 DAO 等价的编辑、按键、排队、模态状态机；作为格式化/渲染资源候选。建议只让主框架拥有刷新/光标，Rich 产出段或离屏内容，避免 ptk/Live/Sixel 三套独立刷新相互擦写。该组合为设计建议，尚未证明混用兼容。 |
| 自建原生 Win32 输入层 | 微软 [SetConsoleMode](https://learn.microsoft.com/en-us/windows/console/setconsolemode) 区分 VT input、processed Ctrl+C、window-input resize 事件；[低层输入](https://learn.microsoft.com/en-us/windows/console/low-level-console-input-functions) 明确 INPUT_RECORD；[经典 API 与 VT](https://learn.microsoft.com/en-us/windows/console/classic-vs-vt) 推荐新开发优先 VT。 | 作为必要缺口的窄平台层，ctypes/pywin32 均可候选；输出优先 VT，输入用框架现有 adapter 或单一原生 reader。简单 getwch/readline 不足以证明 paste framing、CPR、焦点、resize、IME 都正确。保存原始 mode，嵌套/异常/退出恢复；不从终端名称推定全部模式已启用。 |

自动测试候选：[prompt_toolkit create_pipe_input+DummyOutput](https://python-prompt-toolkit.readthedocs.io/en/stable/pages/advanced_topics/unit_testing.html)；[Textual run_test/Pilot](https://textual.textualize.io/guide/testing/) 明确是 headless，可模拟按键/resize。它们适合验证状态和协议，不显示真实终端，不覆盖中文 IME 候选窗、ConPTY 前端残影/滚动或真实窗口缩放。Python 默认 Windows Proactor 支持 subprocess，但不能直接套 POSIX add_reader/add_signal_handler；让框架适配 input 与 asyncio task 共存，禁止为解决键盘而全局换成不支持 subprocess 的 Selector loop。[Python asyncio 平台文档](https://docs.python.org/3.13/library/asyncio-platforms.html#windows)

建议保留 `tui/app` 的业务状态、`terminal_reports` 的报告/能力协议、`mascot` 的图形生命周期、工具/runner 的 OS 层边界。平台后端可替换，不把框架 Key、Widget 或 Console handle 泄漏给 agent/scheduler。先通过下一节探针，再形成具体依赖 ADR。

## 8. 最小真实 Python Windows Terminal 实验（仅设计）

### 8.1 材料与执行边界

后续建立单独实验票/分支，编写最小 Python harness，**不移植业务、不安装/运行来源 TUI**。同一事件模型先接最小可行的 prompt_toolkit 路线；只有仍有多个可行候选时才接同一脚本对比，不强制运行官方已经排除的 Windows inline 路线；输出固定 SSE-like token 序列和 synthetic tool 事件，worker 用真实 Python 进程；第一阶段无 API key、无外网、无真实用户文件。实验必须是真 Windows Terminal 可见窗口，用户亲自使用中文 IME，Codex 负责日志/自动断言/截图整理，用户给体验验收。当前研究不能代用户确认。

环境记录：Windows edition/build、Windows Terminal package version、PowerShell 5.1/7 或 cmd profile、Python exact version/arch、venv 与依赖 lock hash、键盘/IME 名称及版本、字体/字号、DPI/缩放、多屏、终端大小/颜色主题、WT paste warning/快捷键设置、WT_SESSION（脱敏）、输入/输出 backend。先验一个主平台组合，再按支持范围补其它组合；Linux/macOS 后续实机，均保留 pending。

探针设计：UI 单一输入/输出所有者，固定欢迎区/scrollback+streaming preview+编辑区+审批/任务面板，内存 scheduler 与显式状态日志；三层日志分别记录 raw 协议（仅合成输入且显式启用）、标准事件及业务接收全文 hash/长度/顺序。真实个人输入/凭据不写 raw 日志。`events.jsonl` 含 monotonic timestamp、seq、source、transition、task/run ID、mode、geometry、state hash；画面截图/视频不能替代业务内容一致性 hash，日志也不能替代画面。

### 8.2 场景、输入、期望与证据

| ID | 实际操作/输入 | 期望结果 | 必存证据 |
| --- | --- | --- | --- |
| WT-01 中文 IME | 用户用拼音真实组合输入“若存测试：中文光标与候选窗”，选词、翻页、未上屏时 Esc；中间插入/删除，再输入 `A中B`、全角标点、`e`+组合重音、`𠮷`、emoji/ZWJ。 | 组合态不重复提交，不把候选操作当退出/排队；上屏后内容准确，cursor/删除按约定单位；候选窗位置可用，宽字符无断裂。IME 的 Esc 先由输入法处理，只有应用收到的 Esc 才驱动状态机。 | 用户操作录像（含候选窗）、最终文本/码点 hash、事件顺序、显示截图；逐项体验反馈。 |
| WT-02 单/多行粘贴 | WT 真实 paste：短单行、6 行、7 行、280/281 边界（含非 BMP）、LF/CRLF/裸 CR/尾随换行；粘到行中间与询问模态。 | 不因换行自动提交；归一化和折叠阈值与已决定契约一致；显示可预览，显式 Enter 后全文 hash 完整；模态 focus 正确。 | 合成输入文件 hash、paste event 次数/长度、提交 hash、前后草稿截图。 |
| WT-03 大段/突发 | 64 KiB、1 MiB 合成中英代码多行，含“看起来像 `ESC[6;10;10t`/CPR”的文本；快速连续两次 paste，paste 期间 token 输出。 | 无截断/粘连/自动 Enter，payload 不误当报告；响应可接受、内存有界；占位符顺序和展开准确。字符与真实控制字节分开两组，真实报告字节在协议层合成测试，不将任意控制载荷直接投到用户终端。 | 每段长度/hash、事件边界、耗时/峰值内存、录像；未完成 paste 的超时/退出策略日志。 |
| WT-04 流式期间排队 | 固定每 30 ms 输出中英 token，共 20 s；用户输入两条并 Enter，第三条保留为草稿，工具边界开放消费。 | 输出不覆盖输入；队列 FIFO/边界消费一次；草稿 cursor 不丢；通知/模态出现时输入正确路由。 | token/event seq、scheduler 队列前后快照、接收 hash、输入响应时间与录像。 |
| WT-05 Esc/Ctrl+C | 有排队时 Esc 一次清队列、再一次中断；waiting 时 Esc pause，新输入恢复；审批/选择器 Esc；Ctrl+C 一次、隔 >2 s、2 s 内两次；Ctrl+D 空/非空。 | 与原优先级相符；中断不当“完成”；不覆盖新草稿；Ctrl+C 自定义逻辑无系统抢先；正常退出返还 shell。 | abort/queue/pause/exit 状态、退出码、用户动作录像、资源清单；所有路径都做 mode restore 比对。 |
| WT-06 前后台 | 真实长 worker 前台时 Ctrl+B；无可转调用；Ctrl+T 查看/关闭；后台完成/失败；退出 keep-background 后新 owner 恢复。 | 转换一次，前台恢复响应；旧 abort 不再认领；任务 ID/输出/取消状态一致；离线完成 receipt 导入一次，不重启副作用。 | worker start side-effect counter、任务/runner 身份、持久事件、前后台画面和恢复记录。 |
| WT-07 终端报告/焦点/图层 | DA/cell/CPR 有响应、无响应、迟到/分片、焦点切走回来；浅/深主题、窄窗、无图协议/屏幕阅读器模式；Sixel 支持时加载内嵌六帧。 | 回包不入草稿；普通 UTF-8/按键不丢；能力不确定即文本 fallback；动画只空闲首页推进，typing/任务/modal/blur 暂停；不干扰中文输入。 | probe raw/标准事件（合成）、timeout、frame/anchor 计数、截图/视频；fallback 明确记录。 |
| WT-08 连续缩放 | 在空闲有草稿、长历史、streaming、审批和 Sixel 五状态，各做宽度 160→80→40→120→160、行数 40→12→30；拖边连续缩放至少 20 s，并改字号/最大化还原；共享 shell 与专属 viewport 分开。 | 无重复欢迎屏/残影/丢行；草稿/cursor/队列/任务不重置；共享 shell 不清旧 scrollback；专属重建只一次生效、迟到 epoch 丢弃，长文本可滚动选中。 | 操作录像、每个稳态 screenshot、geometry/epoch/flush/frame 日志、任务 starts=1 与提交 hash；用户视觉确认。 |
| WT-09 退出恢复 | `/exit`、Ctrl+C 二次、Ctrl+D、可控异常、worker 错误、窗口关闭；另测 Task Manager 强杀后的重启恢复。退出后在原 shell 输入中文/方向键/粘贴、resize。 | 可捕获退出路径恢复原 ConsoleMode、光标/颜色、paste/focus/title；不残留 observer/线程/后台意外窗口；强杀路径按实际记录残留与恢复手段，不伪造 finally 保障。 | 父 launcher 在子启动前/后 GetConsoleMode 的 in/out bitset、截图、子进程/handle/唤醒锁清单、强杀后的自身会话恢复证据。 |

性能门槛作为原型建议：正常键入/独立 Esc 的 p95 响应目标 <150 ms；大段 paste 后 1 s 内恢复可交互；缩放停止后 500 ms 内稳定。它们不是已有 DAO 保证，低于目标要记录环境与原因再决定数值。先保证内容和状态正确，再评估主观流畅性；不能只测吞吐忽略 IME。

### 8.3 必须另做的真实 Windows 系统探针

1. **进程树/IPC**：Python 父→Shell→子→孙三层，分别 CPU 等待/输出/继承 pipe/忽略温和取消；有界 cancel→force，查询所有已记录 PID+creation time 与输出止写。覆盖前台、后台、runner owner 崩溃/恢复、stale capability/epoch、IPC 中途断开/重连与附件缺失；退出保持后台与显式中断分别验。Windows Job/pipe 的 ACL 与 handle 继承要实证，不能用 `taskkill` 成功文本替代身份核实。
2. **系统定时**：以普通用户创建、list、删除、真实触发一次；cwd/命令路径含空格中文，触发输出计数+时间+版本写实验目录；重复触发、升级改路径、注销/重启/休眠错过触发按设计分别验。无真实邮件/消息或业务副作用。
3. **凭据/通知/唤醒锁**：用 test-only 假秘密做写/取/删、权限拒绝与文件 fallback（证据只 hash/状态，绝不 dump secret）；通知显示中文/引号/美元字面量、系统关闭通知后的退化及点击行为；锁 acquire/release/异常/并发引用计数、真实系统状态查询，长时间休眠体验另由用户参与。测试结束删除自身创建的凭据/任务并留清理结果。
4. **持久化/文件/Shell/扩展**：NTFS 中文/空格路径、文件占用、rename/SQLite WAL/并发 owner/fault injection；明确 PowerShell/cmd/Bash 方言各自调用方式、编码与审批；外部 hook/MCP/LSP 命令可继续非 Python，检查 `.cmd/.bat`、stdio/HTTP、超时/进程树，符合 ADR 的核心 Python边界。

本节是终端/平台最小风险探针，不取代 AC-01～AC-15 的 Windows 全功能矩阵。probe 通过只准写对应场景；自动测试、真实前端与用户体验分别记结果。

## 9. Python 工具链与交付实验（仅候选）

建议首轮用 CPython 3.12/3.13 x64 两个可明确记录的解释器组合评估依赖，最终最低版本写 ADR；不因官方首页标低版本就承诺全依赖支持。`src/ruocun` 保持模块职责；pyproject metadata + console script `ruocun = ruocun...:main`，一个版本来源；开发依赖锁定；pytest/async 测试、Ruff、mypy/pyright 任选一致门禁。uv 可管理 venv/跨平台锁和工具安装，**仅开发/分发工具，不进入产品核心逻辑**。[uv 项目锁](https://docs.astral.sh/uv/guides/projects/#uvlock)、[uv tool](https://docs.astral.sh/uv/guides/tools/)

| 路线 | 官方依据 | 建议顺序 |
| --- | --- | --- |
| wheel + sdist（标准路线） | [PyPA 打包](https://packaging.python.org/en/latest/tutorials/packaging-projects/) 区分 build frontend/backend，Hatchling/Setuptools 等均可；[console scripts](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#creating-executable-scripts) 支持 Windows 命令。 | 优先，先选简洁 backend（Hatchling 候选），用标准 `python -m build` 或 `uv build`；开发锁与包运行依赖分清。纯 Python 核心不表示其所有依赖均无平台二进制；最终 wheel tag 按实际依赖/内容确定。 |
| PyInstaller onedir→onefile | [官方 operating mode](https://pyinstaller.org/en/stable/operating-mode.html) 将 interpreter/依赖一起封装，要求在目标 OS/Python/arch 构建，建议先 onedir；onefile 临时解包、启动成本和强杀残留需测。 | 第二路线：在 Windows 原生 runner 构建 console 程序，不用 `--windowed`；先 onedir 排资源/动态导入，再 onefile。不能沿用 Bun 的 Ubuntu 交叉编译作为 Windows Python 发布方案。 |
| Nuitka standalone→onefile | [官方手册](https://nuitka.net/user-documentation/user-manual.html) 有平台/compiler/数据文件要求；Windows 可用 MSVC 等。 | 备选，只有 PyInstaller 存在已证明的阻碍或启动/体积需求值得编译成本时做对比。编译不改变核心 Python 的实现归属，也不免除动态扩展、资源和实机验证。 |

**PKG-W1：最小 wheel 探针。** 后续创建 `ruocun-probe` 临时包（不得冒充产品成品），包含 console entry、非 TTY JSON 模式、终端 probe、中文 locale/Markdown 与帧时序资源、sqlite3 建库/commit/rollback/重开、平台 adapter、self-spawn internal runner 和一个外部 stdio fixture。构建 wheel/sdist，列出 archive 成员/metadata/entry points/license/依赖与 SHA-256；从 sdist 再构建 wheel；在仓库外新 venv、中文+空格路径安装 wheel，移走源码并关闭 PYTHONPATH 后调用命令，验证版本/资源/SQLite/runner 与 WT-01～09 核心路径。再用 uv tool/pipx 类隔离安装探针，检查 PATH、升级/重装/卸载和保留用户数据。用本地 wheelhouse 做一次 `--no-index` 干净安装，明确哪些是必须随包提供的资源；没有开发依赖、外部 preview 目录、Node/Bun 时仍可启动。

**PKG-W2：最小独立打包探针。** 同一 Python probe 在 Windows 构建 onedir，再 onefile；普通用户、无 Python/Node 的干净 Windows 测试用户或 VM，安装路径包含中文空格、cwd 为其它目录，实际 WT 启动。测试控制台 stdin/out 可用、VT/input backend、Ctrl+C 不被 bootloader/入口抢走、所有资源/动态依赖/SQLite 可加载、通知和原生 DLL/权限、退出/异常/强杀后临时文件和模式状态。runner 采用明确的内部参数再入同一 exe，不能假设冻结后的 `sys.executable -m ruocun` 仍是 Python 解释器；记录 PID/creation time、入口模式、start counter、receipt/附件、一轮 owner 退出后恢复与取消，排除递归拉起主 TUI。onefile 父进程退出与解包目录生命周期要实测，避免 runner 依赖已清理的资源。

**PKG-W3：交付门禁建议。** Windows CI 运行本机单测/协议/真实进程/干净 wheel 安装及本机 standalone 冒烟；真实 Windows Terminal/IME/连续 resize 由有桌面环境的 HITL 实验记录，不能由 GitHub headless runner 代替。之后 Ubuntu/macOS 的逻辑检查、构建可以开始，但平台状态继续区分“构建成功/自动验证/实机体验”。成品需版本、commit/lock/OS/arch、hash manifest、来源 MIT/第三方许可、资源 provenance、release notes、安装升级卸载说明、数据路径/恢复说明与失败回滚记录；本研究不执行上传/发布。

## 10. 需要收敛的后续决定（不改变既定目标）

1. **终端依赖 ADR**：以 WT 探针确认 prompt_toolkit 是否能满足 inline、原生滚动/选择、中文 IME 和 Sixel；失败证据决定是否补窄 adapter/上游修复或研究 Textual Windows inline。未验证前不锁死最终依赖，也不以全屏替代擅改体验。
2. **Windows 系统适配 ADR**：runner 的 IPC（named pipe/认证 loopback）、Job 生命周期与 keep-background、credential backend、Task Scheduler cron 语义、OS 隔离能力分别落成具体方案和独立实验票。不是“Windows 做不做”的问题。
3. **分发基线**：默认 wheel+sdist 与 Windows x64 standalone 双路线；Windows ARM64、最低 Python/OS 版本、签名与安装渠道在最小包探针后按实际用户环境选定。Linux/macOS 实机后续，不能预填通过。
4. **资产继承**：把旧脚本中不可恢复的个人 trace 材料化为脱敏 fixture；区分研发集/历史结果/最终验收集，避免把 benchmark 演化期结果或未隔离 held_out 当独立泛化证明；旧 DAO session 兼容测试不强行纳入已排除的迁移目标。

本报告完成只读调查与实验设计；所有产品实现、自动测试、真实终端和用户体验均仍待后续票提供证据。

## 附录 A：215 个测试文件（静态完整路径枚举）

以下路径来自冻结快照，仅说明文件存在；按目录分组，执行范围仍由 vitest.config.ts 规定。

### evals/memory（4）

```text
extract.test.ts
injection_ab.test.ts
recall.test.ts
report.test.ts
```

### evals/memory/lib（6）

```text
creds.test.ts
judge.test.ts
metrics.test.ts
redact.test.ts
transcript.test.ts
types.test.ts
```

### evals/reflect（1）

```text
grade.test.ts
```

### evals（1）

```text
score.test.mjs
```

### src/agent（37）

```text
agent_defs.test.ts
agent_handoff.test.ts
agent_hooks.test.ts
agent_lifecycle.test.ts
agent_memory.test.ts
agent_prompt.test.ts
agent_summary.test.ts
agent_tools.test.ts
background_runtime.test.ts
background_wait.integration.test.ts
bundled_agents.test.ts
cache_audit_integration.test.ts
cache_prefix.test.ts
cleanup.test.ts
compact.test.ts
deck_bridge.test.ts
deck_cli.integration.test.ts
deck_messages.test.ts
fork_agent.test.ts
longtask_eval.test.ts
loop.test.ts
loop_advisor.test.ts
loop_durable.test.ts
reflect_cadence.test.ts
reflect_persist.test.ts
reflect_pipeline.test.ts
reflect_prompts.test.ts
reflect_result.test.ts
resume_agent.test.ts
resume_durable.test.ts
runAgent.test.ts
session_scheduler.test.ts
tasks.test.ts
turn_budget.test.ts
turn_health.test.ts
unified_reflect.test.ts
worktree.test.ts
```

### src/approval（2）

```text
stdin_prompt.test.ts
store.test.ts
```

### src/client（3）

```text
client.test.ts
responses.test.ts
sse.test.ts
```

### src/commands（3）

```text
builtin.test.ts
commands.test.ts
custom.test.ts
```

### src/config（10）

```text
auth_wizard.test.ts
credential.test.ts
env_file.test.ts
migrate_dirs.test.ts
model_selection.test.ts
profiles.test.ts
profiles_store.test.ts
trust.test.ts
update_check.test.ts
validate_key.test.ts
```

### src（5）

```text
env_snapshot.test.ts
plugins.test.ts
project_doc.test.ts
repl.test.ts
schedule.test.ts
```

### src/hooks（2）

```text
hooks.test.ts
integration.test.ts
```

### src/i18n（1）

```text
i18n.test.ts
```

### src/lsp（3）

```text
client.test.ts
config.test.ts
manager.test.ts
```

### src/mcp（4）

```text
mcp.connect.test.ts
mcp.http.test.ts
mcp.manager.test.ts
mcp.test.ts
```

### src/memory（11）

```text
audit.test.ts
consolidate.test.ts
distill.test.ts
frontmatter.test.ts
gc.test.ts
hash.test.ts
inject.test.ts
memory_audit.test.ts
store.test.ts
types.test.ts
validate.test.ts
```

### src/obs（4）

```text
attrs.test.ts
backend.test.ts
init.test.ts
wrap.test.ts
```

### src/permissions/bash（1）

```text
bash_ast.test.ts
```

### src/permissions（14）

```text
bash_preprocess.test.ts
bash_safety.test.ts
classifier.test.ts
classifier_model.test.ts
dangerous_patterns.test.ts
engine.test.ts
gate.test.ts
identity.test.ts
integration.test.ts
perm_audit.test.ts
rules.test.ts
sanitize.test.ts
secrets.test.ts
settings.test.ts
```

### src/prompt（1）

```text
system_prompt.test.ts
```

### src/repomap（4）

```text
extract.test.ts
graph.test.ts
index.test.ts
render.test.ts
```

### src/session（8）

```text
audit_switch.test.ts
cache_audit.test.ts
checkpoint.test.ts
cost.test.ts
durable_store.test.ts
log.test.ts
process_identity.test.ts
session.test.ts
```

### src/skills（9）

```text
adapt.test.ts
bundled.test.ts
convert.test.ts
discover.test.ts
install.test.ts
skill_audit.test.ts
skills.test.ts
toggle.test.ts
usage.test.ts
```

### src/tools（56）

```text
agent.test.ts
ask_user.test.ts
diagnostics.test.ts
diff_hunk.test.ts
edit_file.test.ts
edit_mismatch.test.ts
enter_worktree.test.ts
exec_shell.test.ts
exec_shell_ctl.test.ts
execute.test.ts
execute_durable.test.ts
exit_worktree.test.ts
fetch_cache.test.ts
fetch_extract.test.ts
fetch_url.test.ts
file_lock.test.ts
file_search.test.ts
fs_atomic.test.ts
glob.test.ts
grep_files.test.ts
list_dir.test.ts
lsp.test.ts
managed_shell.test.ts
memory_read.test.ts
memory_write.test.ts
message_parent.test.ts
monitor.test.ts
notebook_edit.test.ts
notify_user.test.ts
output.test.ts
paths.test.ts
plan_mode.test.ts
process_manager.test.ts
read_file.test.ts
registry.test.ts
repo_map.test.ts
sandbox.test.ts
schedule_tool.test.ts
schema.test.ts
skill_install.test.ts
spill.test.ts
ssrf.test.ts
task_create.test.ts
task_get.test.ts
task_list.test.ts
task_output.test.ts
task_send.test.ts
task_stop.test.ts
task_update.test.ts
todo_write.test.ts
tool_audit.test.ts
tool_search.test.ts
tools_for_mode.test.ts
walk.test.ts
web_search.test.ts
write_file.test.ts
```

### src/tui（16）

```text
Welcome.test.tsx
background.test.ts
banner.test.ts
capabilities.test.ts
foreground_registry.test.ts
markdown.test.ts
mascot.test.ts
maxim.test.ts
notifier.test.ts
render.test.ts
spinner_words.test.ts
tab_attention.test.ts
taiji.test.ts
terminal_reports.test.ts
theme.test.ts
width.test.ts
```

### src/tui/app（4）

```text
App.test.tsx
format.test.ts
multi_select.test.tsx
tail.test.ts
```

### src/tui/onboarding（2）

```text
Onboarding.test.tsx
Select.test.tsx
```

### src/tui/onboarding/steps（3）

```text
KeyStep.test.tsx
TrustStep.test.tsx
steps_select.test.tsx
```


## 附录 B：58 个 scripts 文件与分类

D/R/S/P 含义见 5.1；有“live”或 streamChat 的脚本即使名为 replay，也不自动视为离线确定性测试。

### 确定性语义/真实进程探针（D/R/S）：5 文件

```text
scripts/verify-background-recovery.ts
scripts/verify-background-wait.mjs
scripts/verify-memory.ts
scripts/verify-persistence-runtime.ts
scripts/verify-recovery-entrypoints.mjs
```

### 真实模型后台/恢复验收协议（R/S/P）：2 文件

```text
scripts/verify-background-recovery-live.mjs
scripts/verify-background-wait-live.mjs
```

### 真实模型记忆/缓存/反思（D/R/S/P）：4 文件

```text
scripts/accept-cache.sh
scripts/accept-memory.sh
scripts/debug-distill.ts
scripts/verify-reflect.ts
```

### 预览/演示/调试/资源/版本（D/R/S）：9 文件

```text
scripts/demo-reflect.tape
scripts/demo.en.tape
scripts/demo.tape
scripts/dump-harness-wire.ts
scripts/generate-mascot-data.mjs
scripts/preview-taiji.ts
scripts/preview-welcome.ts
scripts/sync-version.mjs
scripts/welcome-ink.tsx
```

### 真实模型专题诊断/重放（以 P 为主，材料可 D/R）：38 文件

```text
scripts/introspect-cancel-async-tasks-taskgroup-dismissed.ts
scripts/introspect-feal-brute-force-full-space.ts
scripts/introspect-model-extraction-relu-logits-untested-branch.ts
scripts/introspect-openssl-selfsigned-cert-pip-vs-stdlib.ts
scripts/introspect-write-compressor-encoder-decoder-asymmetry.ts
scripts/introspect-write-compressor-restart-without-run.ts
scripts/verify-ars-introspect.ts
scripts/verify-autotune-preference.ts
scripts/verify-cancel-async-tasks-taskgroup-replay-v2.ts
scripts/verify-cancel-async-tasks-taskgroup-replay.ts
scripts/verify-cold-start-dim.ts
scripts/verify-exec-shell-no-extra-params.ts
scripts/verify-exec-shell-timeout-introspect.ts
scripts/verify-extreme-value-probe.ts
scripts/verify-fasttext-dim-introspect.ts
scripts/verify-feal-emptyretry-toolchoice-replay.ts
scripts/verify-feal-sufficiency-clarify-replay.ts
scripts/verify-grep-only-matching-replay.ts
scripts/verify-installwindows-candidate-replay.ts
scripts/verify-installwindows-introspect.ts
scripts/verify-installwindows-qemuversion-replay.ts
scripts/verify-largest-eigenval-checkpoint-replay.ts
scripts/verify-largest-eigenval-introspect.ts
scripts/verify-largest-eigenval-round4-replay.ts
scripts/verify-largest-eigenval-tier2-replay.ts
scripts/verify-model-extraction-groundtruth-peek-replay.ts
scripts/verify-model-extraction-relu-logits-untested-branch-replay.ts
scripts/verify-openssl-selfsigned-cert-dep-minimization-replay.ts
scripts/verify-train-fasttext-autotune-introspect.ts
scripts/verify-train-fasttext-timeout-replay.ts
scripts/verify-tunemjcf-candidate-replay.ts
scripts/verify-tunemjcf-introspect.ts
scripts/verify-videoprocessing-introspect.ts
scripts/verify-write-compressor-hard-block-rewrite.ts
scripts/verify-write-compressor-missing-dep-default-replay.ts
scripts/verify-write-compressor-missing-dep-hard-block-replay.ts
scripts/verify-write-compressor-oracle-search-replay.ts
scripts/verify-writecompressor-introspect.ts
```


## 附录 C：独立评估、任务、fixture 清单

下列运行工具、任务验证器、Docker 配套和 fixture 目录均来自同一快照；历史报告单独识别，不能转换为本轮验收结果。

### 评估工具/环境/历史参考文件

```text
evals/README.md
evals/docker/README.md
evals/docker/cpp.Dockerfile
evals/docker/java.Dockerfile
evals/docker/node.Dockerfile
evals/docker/python-ds.Dockerfile
evals/docker/python.Dockerfile
evals/horizon.mjs
evals/materialize-trace.mjs
evals/memory/.gitignore
evals/memory/BASELINE.md
evals/memory/README.md
evals/memory/extract.ts
evals/memory/injection_ab.ts
evals/memory/lib/creds.ts
evals/memory/lib/judge.ts
evals/memory/lib/metrics.ts
evals/memory/lib/redact.ts
evals/memory/lib/transcript.ts
evals/memory/lib/types.ts
evals/memory/recall.ts
evals/memory/report.ts
evals/memory/run.ts
evals/memory/tsconfig.json
evals/reflect/README.md
evals/reflect/grade.ts
evals/reflect/run.ts
evals/reflect/tsconfig.json
evals/render-trace.mjs
evals/run.mjs
evals/score.mjs
evals/swebench/.gitignore
evals/swebench/adapter.mjs
evals/swebench/adapter_v2.mjs
evals/swebench/container_helper.py
evals/terminal-bench/.gitignore
evals/terminal-bench/README.md
evals/terminal-bench/agent/batch_by_memory.py
evals/terminal-bench/agent/build-binaries.sh
evals/terminal-bench/agent/dao-code-setup.sh.j2
evals/terminal-bench/agent/diagnose_failure.py
evals/terminal-bench/agent/harbor_dao_agent.py
evals/terminal-bench/collect_results.py
evals/terminal-bench/collect_results_pro_default.py
evals/terminal-bench/extract_solutions.py
evals/terminal-bench/gen_case_studies.py
evals/terminal-bench/gen_index.sh
evals/terminal-bench/gen_quant_summary.py
evals/terminal-bench/gen_results_html.py
evals/terminal-bench/gen_results_html_pro_default.py
evals/terminal-bench/gen_results_md.py
evals/terminal-bench/gen_task_status.py
evals/terminal-bench/gen_timeline.py
evals/terminal-bench/results.html
evals/terminal-bench/run-pro-full.sh
evals/terminal-bench/solutions-reference.md
evals/terminal-bench/split.json
evals/terminal-bench/status.sh
evals/terminal-bench/summarize.py
evals/terminal-bench/task_meta.json
evals/terminal-bench/task_overrides.json
evals/terminal-bench/watch-result.sh
evals/trace-viewer-template.html
```

### 16 个任务与模板

| task 目录 | kind | checkpoint 数 | 独立验证文件（相对该目录） |
| --- | --- | ---: | --- |
| `evals/tasks/01-parse-query` | double | 0 | `tests/fail2pass.mjs`、`tests/pass2pass.mjs` |
| `evals/tasks/02-dedupe` | double | 0 | `tests/fail2pass.mjs`、`tests/pass2pass.mjs` |
| `evals/tasks/04-plan-blocks-write` | local | 0 | `check.mjs` |
| `evals/tasks/05-pathescape` | local | 0 | `check.mjs` |
| `evals/tasks/06-axis-limit-guard` | double | 0 | `tests/fail2pass.mjs`、`tests/pass2pass.mjs` |
| `evals/tasks/L1-nodeps-toolkit` | double | 5 | `tests/arrays.mjs`、`tests/dates.mjs`、`tests/no-deps.mjs`、`tests/objects.mjs`、`tests/strings.mjs` |
| `evals/tasks/t1-valibot-mastercard` | oss | 0 |  |
| `evals/tasks/t10-semver-subset-prerelease` | oss | 0 |  |
| `evals/tasks/t2-valibot-intersect-frozen` | oss | 0 |  |
| `evals/tasks/t3-datefns-zh-month` | oss | 0 |  |
| `evals/tasks/t4-estoolkit-omitby` | oss | 0 |  |
| `evals/tasks/t5-estoolkit-uniqwith` | oss | 0 |  |
| `evals/tasks/t6-sqlglot-comment-on` | oss | 0 |  |
| `evals/tasks/t7-sqlglot-sqlite-autoinc` | oss | 0 |  |
| `evals/tasks/t8-hono-cookie-dup` | oss | 0 |  |
| `evals/tasks/t9-hono-compress` | oss | 0 |  |

模板：`evals/tasks/90-oss-template/task.template.json`；所有 task 目录的 workspace 文件都是待修复/实现任务数据，保留原语言及路径：

```text
evals/tasks/01-parse-query/workspace/qs.mjs
evals/tasks/02-dedupe/workspace/dedupe.mjs
evals/tasks/06-axis-limit-guard/workspace/axisConfig.mjs
evals/tasks/L1-nodeps-toolkit/workspace/README.md
evals/tasks/L1-nodeps-toolkit/workspace/package.json
evals/tasks/L1-nodeps-toolkit/workspace/src/arrays.mjs
evals/tasks/L1-nodeps-toolkit/workspace/src/dates.mjs
evals/tasks/L1-nodeps-toolkit/workspace/src/index.mjs
evals/tasks/L1-nodeps-toolkit/workspace/src/objects.mjs
evals/tasks/L1-nodeps-toolkit/workspace/src/strings.mjs
```

### 独立 fixture 文件（85 个）

```text
evals/memory/fixtures/extract/_synthetic/conversation.jsonl
evals/memory/fixtures/extract/_synthetic/gold.json
evals/memory/fixtures/extract/bubble-fyuu/conversation.jsonl
evals/memory/fixtures/extract/bubble-fyuu/gold.json
evals/memory/fixtures/extract/bubble-m94s/conversation.jsonl
evals/memory/fixtures/extract/bubble-m94s/gold.json
evals/memory/fixtures/extract/canvas-j98j/conversation.jsonl
evals/memory/fixtures/extract/canvas-j98j/gold.json
evals/memory/fixtures/extract/canvas-vo1k/conversation.jsonl
evals/memory/fixtures/extract/canvas-vo1k/gold.json
evals/memory/fixtures/extract/media-4qsj/conversation.jsonl
evals/memory/fixtures/extract/media-4qsj/gold.json
evals/memory/fixtures/extract/note-gyy4/conversation.jsonl
evals/memory/fixtures/extract/note-gyy4/gold.json
evals/memory/fixtures/extract/slide-mxk0/conversation.jsonl
evals/memory/fixtures/extract/slide-mxk0/gold.json
evals/memory/fixtures/extract/slide-yah0/conversation.jsonl
evals/memory/fixtures/extract/slide-yah0/gold.json
evals/memory/fixtures/recall/_synthetic/context.json
evals/memory/fixtures/recall/_synthetic/store/a.md
evals/memory/fixtures/recall/_synthetic/store/b.md
evals/memory/fixtures/recall/_synthetic/store/c.md
evals/memory/fixtures/recall/bubble/context.json
evals/memory/fixtures/recall/bubble/store/卡通动物角色点击游戏技术选型-swiftui-spritekit-ios-原生-目标.md
evals/memory/fixtures/recall/bubble/store/泡泡机应用项目-ipad-ios-原生应用-swiftui-spritekit-泡.md
evals/memory/fixtures/recall/bubble/store/泡泡机应用项目-users-user-daoproject-game-使用.md
evals/memory/fixtures/recall/bubble/store/泡泡机应用项目已通过子代理驱动开发完成全部-9-个-task-11-11-单元测试.md
evals/memory/fixtures/recall/bubble/store/用户正在开发一个给2岁孩子玩的-ipad-益智游戏-卡通动物角色主题的点击探索游戏-.md
evals/memory/fixtures/recall/canvas/context.json
evals/memory/fixtures/recall/canvas/store/canvasapp-新增-6-种贴纸-小鸭-fluent-duck-noto.md
evals/memory/fixtures/recall/canvas/store/canvasapp-画布应用-是面向-2-岁儿童的-ipad-涂鸦-app-.md
evals/memory/fixtures/recall/canvas/store/canvasapp-贴纸图片位于-canvasapp-resources.md
evals/memory/fixtures/recall/canvas/store/canvasapp-贴纸图片加载的坑已修复-stickermanager-r.md
evals/memory/fixtures/recall/canvas/store/canvasapp-贴纸栏改为每个变体独立展示-每种上限-3-个-不再点击切.md
evals/memory/fixtures/recall/canvas/store/canvasapp-音效用-avaudioengine-程序合成-pcm-波.md
evals/memory/fixtures/recall/i18n-cross-project/context.json
evals/memory/fixtures/recall/i18n-cross-project/store/avaudioengine-start-crash.md
evals/memory/fixtures/recall/i18n-cross-project/store/cli-highlight-plaintext.md
evals/memory/fixtures/recall/i18n-cross-project/store/dao-diff-render.md
evals/memory/fixtures/recall/i18n-cross-project/store/no-ai-commit-signature.md
evals/memory/fixtures/recall/i18n-cross-project/store/spritekit-emoji-render.md
evals/memory/fixtures/recall/i18n-cross-project/store/swiftui-gesture-scrollview.md
evals/memory/fixtures/recall/i18n-cross-project/store/tsx-vs-esbuild.md
evals/memory/fixtures/recall/i18n-cross-project/store/verify-with-evidence.md
evals/memory/fixtures/recall/i18n-cross-project/store/xcode-clean-build.md
evals/memory/fixtures/recall/media/context.json
evals/memory/fixtures/recall/media/store/adapting-superpowers-to-dao.md
evals/memory/fixtures/recall/media/store/created-12-dao-skills.md
evals/memory/fixtures/recall/media/store/dao-builtin-debug-simplify.md
evals/memory/fixtures/recall/media/store/gitignore-excludes.md
evals/memory/fixtures/recall/media/store/skill-loading-needs-exploration.md
evals/memory/fixtures/recall/note/context.json
evals/memory/fixtures/recall/note/store/dataflow-no-debounce.md
evals/memory/fixtures/recall/note/store/note-app-swiftui-appkit.md
evals/memory/fixtures/recall/note/store/plaintext-content-storage.md
evals/memory/fixtures/recall/note/store/removed-format-command.md
evals/memory/fixtures/recall/note/store/scenephase-force-save.md
evals/memory/fixtures/recall/slide/context.json
evals/memory/fixtures/recall/slide/store/ios-agent-技能发现-关键索引站和-github-仓库格局.md
evals/memory/fixtures/recall/slide/store/slide-game-实现完成状态.md
evals/memory/fixtures/recall/slide/store/slide-game-项目-2岁儿童-ipad-滑滑梯游戏.md
evals/memory/fixtures/recall/slide/store/slide-game-项目完成状态-14-commit-编译-运行验证通过.md
evals/memory/fixtures/recall/slide/store/stickpng-等免费png站对卡通配角图覆盖不足.md
evals/memory/fixtures/recall/user-level/context.json
evals/memory/fixtures/recall/user-level/store/copyright-personal-use.md
evals/memory/fixtures/recall/user-level/store/credentials-in-tool.md
evals/memory/fixtures/recall/user-level/store/incremental-visual-delivery.md
evals/memory/fixtures/recall/user-level/store/search-skills-before-dev.md
evals/memory/fixtures/recall/user-level/store/tsx-vs-esbuild.md
evals/memory/fixtures/recall/user-level/store/user-profile-kid-ipad-games.md
evals/memory/fixtures/recall/user-level/store/verify-with-evidence.md
evals/reflect/fixtures/c1-cc-sysprompt-assertion/conversation.jsonl
evals/reflect/fixtures/c1-cc-sysprompt-assertion/gold.json
evals/reflect/fixtures/c2-mem-layer-assertion/conversation.jsonl
evals/reflect/fixtures/c2-mem-layer-assertion/gold.json
evals/reflect/fixtures/c3-commit-unknown-changes/conversation.jsonl
evals/reflect/fixtures/c3-commit-unknown-changes/gold.json
evals/reflect/fixtures/c4-i18n-continue-ontrack/conversation.jsonl
evals/reflect/fixtures/c4-i18n-continue-ontrack/gold.json
evals/reflect/fixtures/c5-project-status-qa-ontrack/conversation.jsonl
evals/reflect/fixtures/c5-project-status-qa-ontrack/gold.json
evals/reflect/fixtures/c6-verify-honest-ontrack/conversation.jsonl
evals/reflect/fixtures/c6-verify-honest-ontrack/gold.json
src/lsp/testfixtures/sample.ts
src/mcp/__fixtures__/fake-mcp-server.mjs
```
