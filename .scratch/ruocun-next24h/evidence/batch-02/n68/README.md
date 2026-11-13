# 68 欢迎卡片与原始Sixel候选

65/63同负责人批内许可后实施68，仍claimed。69仅只读预备，用户要求当前构建收口后暂停时尚无69实现；本候选不解锁或启动69。没有构包、全量pytest、真实模型、用户窗口/剪贴板操作。

## 来源及资产

source.json保存15个冻结模块/测试哈希。MM-744 Welcome保留展示品牌“若存 Code”、固定短句、真实工作区/版本、footer开关、最大146列居中卡片和图像左上坐标；浅色或窄屏显示文本。MM-757/758/770/792及473保留原banner、品牌、太极背景色/低色简图、30条公有领域名句与可注入随机选择。旧buildWelcome入口仍按源DAO CODE词标，不与真实TUI新卡片混淆。

MM-768的599038字节TS资源由机器解析为6帧/10步时间线；产品JSON保留原header、6个PNG来源哈希、MIT、原source SHA及每帧解码字节SHA。未逐条模型改写Sixel。verify-static.py直接只读冻结ZIP，检查逐帧原值、timeline/image结构、完整来源header、原词标和名句数组与产品一致，resource-binding.json记录真实结果。首次绑定脚本因源banner的CRLF+末逗号解析失败，修正机器解析规则后通过，原失败保留；产品帧数据未更换。资源大小和源资产身份可供最终同包绑定核验。

## 实际产品接缝

InputBroker.show_welcome(info,skip_footer=False)在start后调用，由现有同一Reports/ParserGate读DA/cell/CPR，TerminalQueries只持串行查询与600ms预算，不持stdin/raw_mode。root只提供model/thinking/cwd/version/branch/obs字符串，不驱动动画。暗色、TTY、DA确认Sixel且cell有效才预留图框；超时、不支持、浅色、窄屏无图。

欢迎、标题、背景查询、图形与业务输出共用既有协调队列和run_in_terminal。单帧await实际flush完成；emit前复核epoch/generation，过期帧不写。待机首页才推进原动画时间线，输入/任务/后台/模态/失焦暂停；新视口在已有草稿时只补一张静帧。owned缩放和主题切换串行重测、重绘自有卡片/历史并更新epoch；shared终端不清用户scrollback。普通未测静态输出按源“未知几何”停图，避免猜坐标。关闭取消查询并收齐在途写、动画和resize，不新增reader/RawMode恢复者。

ptk适配的实际红因保留：Screen.height含HSplit剩余空白，不能作为动态区高度；误把dont_extend_height传HSplit时真实TypeError也保留。最终只给Input/Live/Modal的Window使用原生dont_extend_height，公开find_all_windows/visible_windows_to_write_positions量实际窗口。run_in_terminal擦除动态区时CPR位于静态卡之后，补回该已测行高提供原imageAnchor的“动态区之后”坐标；after_render保留稳定测量，避免擦屏瞬态0行反复使票据失效。未变化的100ms重绘不反复重启动画timer；静态行测量按历史/列宽/语言/展开状态缓存，避免每帧重放整段历史。

## 回执与边界

welcome-red真实缺模块→4来源用例green；motion-red真实缺模块→策略/锚点与背压/暂停/reset/epoch/关闭2例green（首版仍在写期间保留needsStill导致重复静帧，修正到源提交时点后绿）。已有输入/Reports受影响回归连同前6来源例在owner-regression共14项通过，此后按主协调要求不重复整组。

actual-owner这一个原有产品seam从布局/瞬态高度红收口为product-seam-stable绿；扩入同一来源主题/静帧路径后，发现100ms重绘反复取消250ms静帧调度，draft-still-diagnosis保留实证。最后product-seam-final-fixed一个seam通过：同reader分片probe→CPR定锚→真实原帧写入；paste内类似回包原样保留且不提交；窄屏文本降级、浅色/拉宽仍无图、暗色恢复给原草稿一张静帧后不推进动画；关闭释放查询/owner。全部为受控pipe和合成输出端口，不是Windows Terminal实际显示通过。

9源Ruff/mypy通过；后续实际owner收口只重受影响两源静态，save-static/save-mypy通过。原工程格式失败与所有诊断红均保留。tools/run始终明确环境白名单与合成HOME/config/temp，所有回执scan_hit=false。没有伪造所有断言先红的历史，也未把真实源失败、脚本失败或未验环境改写成成功。

普通runtime接线、真实Windows Terminal的Sixel显示/尺寸/模态/退出残留、其它平台实际CPR仍由主协调集中登记；未知几何安全停图不代表图形实际验收。用户完整主题、IME与主观体验仍另列。此候选保持claimed，交主协调集成/独审，不自行resolved。

## Windows Terminal 用户反馈修复

`20261111T075358Z-ea4e4c` 的用户反馈是欢迎文字正常、未见形象、输入框文字过淡。原启动记录有 `WT_SESSION` 和初始 console mode，缺少列数、DA、cell、CPR 回执，无法辨别该窗口实际经过哪条图形降级分支。源码能分别重现 80 列无 Sixel 图框、浅色跳过探测、无有效探测或光标回包时无图。草稿和模态输入原先只指定文字颜色，浅色 `#1a1e26` 仍可能落在终端深色底；现使用既有语义色 `ink` 与 `panel`，不改终端配置。

欢迎卡片使用同一冻结第 0 帧的静态单元格图，暗色原 Sixel 通路仍用原帧和锚点。Sixel 图框里的静态图约束在完整单元格内；回包有效后原图覆盖静态图。无图形回包、浅色和普通窄窗仍有形象。静态资源 `mascot-static.json` 的 SHA-256 为 `62b0f5879e66584a6730636979dd41650988d65deb11bf151c75feadc92ec09d`，由本目录 `derive-static-mascot.py` 对同包冻结 Sixel 资源解码并按面积平均取样，无新依赖。第 0 帧 SHA-256 为 `7ea19dad5ab8132068c4e17ee062162f5d4b3ba9b7edec877e55522261b67d4b`。

80 列重绘用例进一步捕获旧 `shortcuts.print_formatted_text` 在现有 `run_in_terminal` 内再次异步排队，导致重绘完成时静态图和文字都尚未真正写出。改用同一 prompt_toolkit 同步 renderer 后，卡片在原 owner 锁和完成回执内写出。`n68-input-contrast-red` 和 `n68-static-mascot-red` 保存合成红回执，`n68-static-mascot-diag` 保存输出排序红回执。`n68-static-mascot-final` 通过当前欢迎套件 9 项，涵盖原 Sixel 定锚、80 列静态图、回包样式粘贴不误提交、主题与草稿、输入配色；Ruff 和定向 Mypy 均通过。全部由白名单合成 launcher 运行。该次未操作用户的真实窗口，新版实际可见性和缩放仍待复测。

用户下一轮反馈确认输入框两种主题都清楚，欢迎形象可见但辨识度不足。锁定的 prompt_toolkit 3.0.52 在 Windows VT 输出后端默认使用 24 位色，既有 `WT_SESSION` 也会在后端报告真彩时提升欢迎色彩，旧实机回执缺少后端类、列数和回包，无法确定是哪条渲染分支。Windows Terminal v1.24.12741.0 的 DA 带 Sixel 能力值 4，字符单元查询返回 `CSI 6;高;宽 t`，锁定的 Win32 VT reader 把输入字符交给已有 ParserGate。复现用例回放该版本 DA 和 20×10 单元回包，旧产品仍因 `26+79` 列宽限制无法在 80×24 容纳原图。现仅实况布局使用紧凑阈值并为输入与状态至少预留五行，卡片和锚点共享该布局。原 256×244 Sixel、回包判据、reader 与提交生命周期沿用。[Microsoft Terminal 固定版本实现](https://github.com/microsoft/terminal/blob/v1.24.12741.0/src/terminal/adapter/adaptDispatch.cpp#L1359-L1389) [字符单元查询](https://github.com/microsoft/terminal/blob/v1.24.12741.0/src/terminal/adapter/adaptDispatch.cpp#L3223-L3261)

备用图以同一第 0 帧机器生成 104×96 RGB 样本，每格用两个颜色显示四个象限，在 80×24 可使用 32×14 格（64×28 个取样位置）；随可用窗口收放。新资源 SHA-256 为 `25a64a00ec828c4d6766837d5b948272a171d886be9779733b4485dfd507c28f`。Windows Terminal 真彩提升保留显式 `FORCE_COLOR`、`COLORTERM` 和后端色深覆盖；`NO_COLOR` 走无 ANSI 静态图。`n68-hd-mascot-red` 的两个现有反馈点均失败，`n68-hd-mascot-green` 欢迎套件 9 项通过，Ruff 与定向 Mypy 均通过，尚待真实终端对清晰度复测。
