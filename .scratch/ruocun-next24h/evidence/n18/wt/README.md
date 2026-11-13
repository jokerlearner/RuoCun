# N24 独立 Windows Terminal 技术窗口

最小复用 D06 的 `Open-Hitl.ps1` 启动方式和 `launch.py` 的 ConsoleMode 比较及补救顺序，实际子应用改为普通 `python -m ruocun`。本目录仅提供本轮受控产品窗口，不修改旧 D06 记录或 Terminal 设置。每次通过 `wt -w new` 新建独立窗口，由主协调 CUA 只输入合成聊天并操作该窗口。

当前源码技术取证在根目录执行以下入口。`-Source` 显式把该根的 src 加入已知 PYTHONPATH，并禁用用户 site，使用合成 HOME、配置、会话、工作目录与本地回环响应。后续固定安装复验去掉 `-Source`，`-Python` 指向已安装同一固定 wheel 的私有 Python，子应用使用 `-I`。

```powershell
& .scratch/ruocun-next24h/evidence/n18/wt/Open-Product.ps1 -Source
```

若上述后台调用创建的窗口未被统一CUA枚举，本轮只再试一次显式Normal路径（PowerShell 7.6.9已核支持所用参数）：

```powershell
& .scratch/ruocun-next24h/evidence/n18/wt/Open-Product.ps1 -Source -Normal
```

此路径通过`Start-Process -WindowStyle Normal`及`wt -w new`请求新独立窗口，标题为`RuoCun N24 Normal 技术确认`。外层启动逐项移除继承环境，再传固定系统项和独立合成HOME、AppData、临时目录；不改变调用者环境。它不证明窗口已经显示或可被CUA绑定，也不能预先解释此前未枚举的原因。启动后仍由主协调刷新真实窗口库存确认；不能绑定时沿本目录stop-file通道收尾，不继续制造窗口。

launcher捕获该新WT的`WT_SESSION`后，同样先清空自身`os.environ`并设为合成白名单，再运行Git、回环服务和产品；`start.json`中的`launcher_environment_cleared`记录此执行点。脚本语法检查通过；独立隐藏Python小进程确认`Start-Process -Environment`删除合成父secret变量、只保留所传7个变量、HOME指向合成目录，进程退出0、stderr为空。此项是环境机制检查，尚未运行Normal技术窗口。

可输入合成“开始流式”，服务以250毫秒间隔输出80个合成片段，约20秒。过程中编辑下一条草稿或显式Enter排队，观察状态、草稿与取消。输入“问答验证”进入同owner多选问答，输入“消息验证”产生带合成附件的用户可见消息。用 Esc、空 Ctrl+D、双 Ctrl+C 或 `/exit` 验实际产品收尾。窗口缩放与画面由主协调记录截图，不代填用户IME/候选窗体验。

每次在 `runs/<UTC-run>/` 写入 `start.json`、`requests.jsonl`、`launcher.json`。start记录真实 Git HEAD、源码工作树是否有改动、源文件摘要、实际 WT_SESSION、命令和环境白名单键。requests仅保存主协调输入的合成用户消息原文和SHA256。launcher记录产品退出码、mode before/after、`mode_equal_before_repair` 及补救后mode。实际合成 HOME/配置/SQLite 会话位于 `.cache/n24-wt/<UTC-run>/`。运行期间只在127.0.0.1绑定随机端口，所有响应本地生成，退出收口服务器。

此脚本只能从真实双TTY且含WT_SESSION的窗口运行。`tools/run.py` 会重定向产品输出，故可见窗口的子应用直接继承该新窗口的console句柄，环境仍逐项白名单构造。技术操作和自动状态证据不填写用户体验accepted。脚本当前仅完成语法检查，真实结果等待主协调实际启动取证。

若统一CUA无法枚举该测试窗口，主协调可按 `start.json` 的 `stop_request` 路径创建本次合成 `stop.request` 文件。launcher只对自身持有的产品子进程树执行精准终止，记录 `forced_stop: true`、`normal_exit_verified: false`、实际退出和强停后的mode比较，然后关闭回环服务。这个通道不执行文件内命令。它用于技术窗口异常收尾，结果不能填作产品正常退出或用户体验通过。旧版已经运行的launcher不具备该轮询通道，需要先核对独占产品真实PID及唯一合成配置路径，再按精准进程收尾记录外部强停。
