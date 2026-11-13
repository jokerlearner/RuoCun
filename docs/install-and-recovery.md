# 安装、更新和恢复

当前安装产物面向 **Windows x64 / CPython 3.11**，实际验证使用 3.11.9。准备固定候选 wheel、同批运行锁及对应的离线 wheelhouse。用户侧验证和开发依赖各自使用独立 Python 环境。[产物与摘要](release/batch-09.md)

## 新装

在 PowerShell 设置三个实际绝对路径。使用空的虚拟环境目录，例如 `$env:LOCALAPPDATA\RuoCun\venv`。在运行下列命令前，按发布记录核对 wheel 与锁的 SHA-256。

```powershell
$venvPath = Join-Path $env:LOCALAPPDATA 'RuoCun\venv'
$wheel = 'C:\path\to\ruocun-0.1.0.dev0-py311-none-win_amd64.whl'
$runtimeLock = 'C:\path\to\requirements-runtime-win311.lock'
$wheelhouse = 'C:\path\to\wheelhouse'
py -3.11 -m venv $venvPath
$ruocunPython = Join-Path $venvPath 'Scripts\python.exe'
& $ruocunPython -I -X utf8 -m pip install --no-index --find-links $wheelhouse --require-hashes -r $runtimeLock
& $ruocunPython -I -X utf8 -m pip install --no-index --no-deps $wheel
& $ruocunPython -I -X utf8 -m pip check
& $ruocunPython -I -X utf8 -m ruocun --version
& $ruocunPython -I -X utf8 -m ruocun --help
```

从 Windows Terminal 启动 `& $ruocunPython -I -X utf8 -m ruocun --cwd 'D:\path\to\project'`。无可用账户时，由交互式向导输入服务商与密钥并确认项目授权。可用 `/doctor` 查看配置及平台能力。安装也注册了 `ruocun` 命令。验证机器的应用控制曾拦截中文路径下新生成的 `ruocun.exe`（WinError 4551），同一环境的 `python -m ruocun` 已实际验证。[Windows 安装与更新回执](../.scratch/ruocun-next24h/evidence/batch-09/n81-upgrade/README.md)

从自动化宿主拉起新 Windows Terminal 时，检查子进程是否继承了 `TERM=dumb` 或 `NO_COLOR`。前者会跳过欢迎形象，后者会禁用配色。用于图形界面的启动器可以在新窗口内移除这两项，并通过 `RUOCUN_OWNED_TERMINAL=1` 声明它创建的专属视口，使缩放后可以恢复原图。现有终端继续按共享视口启动。用 `/lang zh` 保存中文界面偏好。

## 手动更新与退回

1. 使用 `/tasks` 和受管后台工具确认活动任务已完成或明确停止。用 `/exit` 退出，确认本次控制器、runner 和 IPC helper 都已收尾。`/quit --keep-background` 会刻意留下受支持的后台 Shell。
2. 按原目录结构备份整个 `$HOME\.ruocun`，包含存在的会话数据库、SQLite 伴随文件、设置和运行目录。若用 `--config` 选择了其他配置文件，也单独备份。Windows Credential Manager 保存的 `keyRef` 引用与系统登录绑定，跨账户或跨机恢复时从向导重新录入密钥。若先前的账户来自外部配置，更新前在若存的 `/account` 中配置账户，更新后确认选中该账户。
3. 保留旧环境和旧包。按新装步骤在新 venv 安装已核对的候选，并执行 `pip check`。若原 venv 由你专用于 RuoCun，也可在更新锁定依赖后使用 `pip install --no-index --no-deps --force-reinstall <新wheel>` 换包。同为开发版 `0.1.0.dev0` 时用发布摘要区分包。
4. 若从旧storage1更新到B-r3/storage3，停全部旧进程并保留备份后，先在原工作区显式运行 `python -m ruocun --cwd <原工作区> --upgrade-session <会话ID>`；不自动升级活动或未确认会话。再用 `python -m ruocun --continue <会话ID>` 打开。恢复判断可用 `/recovery` 查询。旧操作结果不明时保留现场，按真实结果登记决定。旧程序会拒绝新格式，回退时需同时恢复原数据备份，不能只换回旧解释器。
5. 遇到损坏或不兼容配置，先保存原文件与出错回执，停止使用该配置进行写入。使用保留的旧包或旧环境，并把完整备份恢复到同一用户、同一位置。会话库损坏时保留原数据库及伴随文件。当前交付采用手动备份和手动恢复。

卸载前依第 1 步停进程，然后对实际安装解释器执行 `& $ruocunPython -I -X utf8 -m pip uninstall ruocun`。项目目录、用户数据和系统凭据分别管理。如需另行清理，先保留已核对的备份。

## 权限与扩展

- 用 `/permissions` 检查分层规则和当前模式。以 `/plan` 进入只读规划。交互审批和 `ruocun trust --cwd <目录>` 的项目授权各自生效。明确的拒绝和危险调用边界继续适用。
- 用 `ruocun Skill add <本地路径或Git地址> --project` 安装项目技能，`/skills` 管理和查看。用 `/hooks` 查看当前 Hooks，`/mcp` 管理外部服务。LSP 由用户或项目的 `lsp.json` 配置，语言服务器需单独安装。通过 `--no-skills`、`--no-hooks`、`--no-mcp`、`--no-web` 可按本次运行关闭对应通道。
- `/compact` 压缩失败会保留原上下文并停止本轮。已确认的工具结果不会自动重放。后台 Shell 支持接管同一次运行，只有存在完整检查点的后台子代理才可显式继续。指定隔离派发而工作树创建失败时会拒绝执行。
- Windows 系统级定时、防休眠后端和桌面通知已移出本次交付。`/loop` 是会话内调度，`NotifyUser` 提供终端内提醒。`RUOCUN_SANDBOX=1` 在 Windows 明确拒绝执行，Linux/macOS 各自使用可用的系统沙箱适配。`--eval` 管理评估输入和扩展通道，权限裁决另行生效。
- `/usage` 与 `/cost` 展示累计 token 和本次进程的费用。历史分模型费用覆盖有限。反思默认关闭，主动启用后会产生额外模型请求。

[范围与差异](adr/0010-selected-scope-and-lean-workflow.md) · [终端范围](adr/0014-terminal-and-scope.md) · [候选平台检查](release/batch-09.md)
