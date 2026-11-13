# D17 独立合并复核

日期：2026-11-05；分支 `merge/d17-windows`；worktree `.worktrees/m17`。本目录仅交付技术实验复核证据，不变更 D17 状态、公共地图、对应表、验收矩阵或产品目标。

统一交付位置为 `.scratch/ruocun/integration-evidence/d17/`。材料先提交于根 `integration-evidence/d17/`（`a1b5b4d`、`78bb177`），后按协调要求用经绝对路径与 reparse point 核验的原生 `Move-Item -LiteralPath` 整体移动；移动后原 19 项指纹无变化。历史 raw/压缩包中的绝对路径保留，未来入口改为向上寻找 AGENTS.md 定位仓库，未重复系统场景，见 `relocation-audit.json`。

## 结论与执行状态

原候选 `dc049ed0acf19e4f3adbc983d18a8cc2d17a44db` 的 105 个文件在提交前进行了当前敏感环境值静默扫描，未发现命中；`windows/manifest.json` 所列 104 项原始字节 SHA-256 全部匹配。原源码、断言、raw 和原 manifest 未改。

本轮只执行一次十项系统测试，轮次 `m17d898598bfc`，耗时 85.08 秒。十项都出现通过进度点；随后**独立审计入口**在 `pytest_sessionfinish` 调用当前 pywin32 不提供的 `win32gui.GetClassInfo`，抛出 `AttributeError`，因此 **pytest 最终 exit=1，本轮不称为完整的“10 passed”回归**。原始失败输出及当时实际执行的审计代码在主压缩包内保留。没有为得到绿色结果再次触发任何系统任务、系统凭据或隔离实验。

后续仅修复附加审计入口，并对本轮已产生的 JSON、精确对象名和 PID 进行只读补审计。`GetClassInfoW` 的不存在类查询实际返回 1411；这只是修复后的只读路径验证，不是重新执行整个测试套件。未来完整复跑入口已经更新，但本轮不宣称其完整运行已验证。

## 实际观测

| 场景 | 本轮证据及解释边界 |
| --- | --- |
| Job | 三代实际运行，允许 outside 写入和宿主 TCP/UDP v4/v6，取消后 ActiveProcesses=0、心跳停止；Job 是生命周期机制。 |
| AppContainer | app-none/app-net 各三代；workspace/tmp 可写、outside 读成功/写拒绝。outside 可读来自私有实验总根的继承 RX ACE，不外推整机读取兼容性。宿主 v4/v6 loopback 拒绝，而自身 loopback 两组都成功。无网络能力拒绝微软外网，有能力 TCP/HTTPS 成功；未配置全局豁免。 |
| restricted token | Python 在恢复线程后以 `-1073741502 / 0xC0000142` 初始化失败，0 个 worker，不能称其隔离已验证。 |
| Task Scheduler | 近未来真实时间触发成功；修改后回执含版本 1、2。最终配置 Parallel/PT0S/两项电池 false/StartWhenAvailable true/WakeToRun false。手动 `.Run()` 并发对照分别为 Parallel 两次重叠、IgnoreNew 一次、Queue 两次顺序；PT3S 提前终止 40 秒 worker。真实时间触发与手动并发是两类证据。 |
| 凭据与唤醒 | 合成凭据边界、profile 编码和精确删除完成；固定线程嵌套生命周期断言完成。服务拒绝、跨用户/登录 session、物理睡眠/电池切换仍未验。 |
| 剪贴板 | CREATE_ONLY 私有窗口站创建返回 5，未调用 EmptyClipboard；交互剪贴板 sequence/格式不变。文字/RGBA/DIB/尺寸写入分支未执行。未读取或保存用户内容。 |
| 通知 | 原生字段提交和 shell callback 有记录；owner window 隐藏、probe cleanup=true。`displayed=not-observed`，不等于画面验收。 |
| cron | 原十项中的 matcher 检查完成；仍是 numeric 五字段实验子集，不是完整方言或持久 dispatcher。 |

新 PSEC 线索及实验 20 位于集成分支；本轮没有运行 PSEC。已有 Query/version 只读成功不能外推为 D17 文件、网络或工具链兼容已补齐。Windows 全功能和终端体验仍按 ADR-0004 在最终产品验收确认。

## 原始字节与环境适配

测试、venv 和依赖安装从 `safe-python.ps1` 提供的显式环境白名单启动；原 subprocess/native 创建调用继承的是已经净化的父环境。没有把宿主 `os.environ` 作为 pytest 参数、诊断或日志保存。原 `run.py` 的直接启动方式仅作为历史入口，本轮未调用它；后续采用本目录的白名单入口。

为使 Task Scheduler 服务启动的 worker 在最早阶段也清理环境，执行源副本中仅 `task.py` 增加了环境清理前缀；Task Scheduler ExecAction 没有 per-action env 参数，不能声称在服务 CreateProcess 的时刻已向它传入白名单。实际执行副本中其原始正文还发生了 LF→CRLF 转换，规范化换行后的正文与原件一致。十项测试文件和另外九份源文件均字节一致，未改能力逻辑、测试期望或 OS 策略。主压缩包内的 `safe-source/environment-adaptation.json`、原始 hash、文本差异，以及本目录的 `m17d898598bfc-task-byte.diff` 和 verification JSON 明确区分这两份字节。

实际本轮白名单保存了 Windows 原生 profile 路径以查询当前用户的 Credential Manager/AppContainer；没有调用模型、产品配置或产品会话。合入最新 AGENTS 后，未来入口另加入合成 HOME/XDG 配置及数据目录；并改为保留 task.py 原始字节尾部。该后续入口修正没有冒充为已执行的本轮字节。

## 清理与证据

只读补审计：8 个精确凭据目标返回 1168；5 个任务查询不存在；2 个 profile 的注册表映射、API 返回目录及完整 package 目录不存在；1 个私有 desktop 和 1 个失败 windowstation 名返回 2；18 个记录进程均不存在/已退出。没有按裸 PID 杀进程。见 `m17d898598bfc-post-audit.json`。

首轮 hook 失败前未持久化 Job、通知图标和窗口类的精确名称，**这些类别没有独立名称级复查**；原探针记录的 `cleanup=true`、Job ActiveProcesses=0 和 pytest 进程退出仍作为其各自证据保留。补审计 `all_recorded_objects_absent=true` 只针对已记录对象，`all_object_types_independently_verified=false` 不得省略。初版补审计的图标空集合布尔值保留于 `post-audit-initial.json`，当前报告改为 null/未独立查询，避免空集合被误读为验证通过。

主压缩包保存 47 个报告/源码/失败输出，raw supplement 保存 259 个已有原始 JSON/TXT/XML（包含 worker 原报告），都带独立清单；所有压缩包 SHA-256 和逐项解压字节已核对。未覆盖任何原 raw。私有 runtime、venv、pip cache 的递归删除命令在执行前也被自动审批以 `blocked by policy` 拒绝，三目录保留，未改工具绕过，见 `cleanup-filesystem.json`。随后只读核对确认三个绝对目标均处于 m17 自有 run 根内，无 reparse point。i17/run 同样保持原状，未触碰。

## 合并记录

初始 clean，起点 `dbe47ef`。准备命令误写 `integration`，原输出 `merge: integration - not something we can merge`，不是源码冲突；随后候选 noff merge 为 `659b4d6`。按协调确认保留历史，再 quiet merge 正式 `integration/ruocun-migration` 的 `70b835a`，得到 `0cdb621`。交付前合入新 tip `6fbbda8`，得到 `742afe5`。该增量为 D11 收录、timeout 事实澄清、环境规则和协调记录，不触及 D17 业务脚本，因此只复核原 hash、压缩包与入口，不重复十项系统场景。

## 后续复跑

以下是未来完整复跑入口，会创建自己的系统实验对象；不是本次新增的一轮结果：

```powershell
$python = (Get-Command python).Source
$runRoot = Join-Path (Get-Location) ('.scratch/ruocun-discovery/experiments/windows/run/review' + [guid]::NewGuid().ToString('N'))
$venv = Join-Path $runRoot '.venv'
& ./.scratch/ruocun/integration-evidence/d17/safe-python.ps1 -Executable $python -m venv $venv
$replayPython = Join-Path $venv 'Scripts/python.exe'
& ./.scratch/ruocun/integration-evidence/d17/safe-python.ps1 -Executable $replayPython -m pip --isolated install --disable-pip-version-check --no-input --cache-dir (Join-Path $runRoot 'pip-cache') -r .scratch/ruocun-discovery/experiments/windows/requirements.lock
& ./.scratch/ruocun/integration-evidence/d17/safe-python.ps1 -Executable $replayPython ./.scratch/ruocun/integration-evidence/d17/review.py
```

`audit_existing.py`、`archive_existing.py`、`verify_artifacts.py` 只读取已有轮次，不触发能力探针。当前 review 入口新增 journal 逐次落盘对象名，修复 Win32 类查询绑定，并保留原 task.py 字节尾部；这些修正的语法/只读路径已检查，完整新一轮仍待以后必要时执行。
