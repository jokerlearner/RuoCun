# 任务03：可安装启动子路径与开发工程

实现分支 `impl/03-boot`，独立 worktree `D:\java supplement\Firstcode\RuoCun\.worktrees\i03`。起点 clean `455090b`；交付前 fast-forward 合入正式集成 `255af6950bbcc3dcd6f08a6a26956a8110d11b7a`，仅规格/实施进度文档变化，没有本票实现输入变化。公共任务状态、地图、module-map 和验收矩阵由主代理维护，本分支不代填。

本票只覆盖 ENT-01/TEST-07 的版本、帮助、资源、包和工程入口子路径。自动通过不表示完整 Agent、所有启动参数、SQLite/恢复、TUI、发布、真实模型或最终 Windows Terminal 体验通过。

## 已实现与来源

- `src/ruocun` 是标准 src 布局轻量包；console `ruocun` 与 `python -m ruocun` 共用入口。RuoCun 自身开发版本为 `0.1.0.dev0`，唯一产品版本来源 `version.py`，Hatchling 动态生成 metadata，包公开版本与 CLI 一致。
- 版本 `--version/-v` 优先于帮助和其它 token。直接读取冻结 `package.json`、`version.ts`、`scripts/sync-version.mjs`、`index.ts:200–220,280–345` 与测试配置；来源有版本早退分支与意图，**没有发现 `--help/-h` 专门早退**。本地帮助是 ENT-01/R-15/D21 要求驱动的明确差异，通过真实 `importlib.resources` 读取 `help.zh-CN.txt`。没有构造假的 parser/grammar 资源。
- 普通运行暂以69说明 Agent 尚未实现；这只是任务03的阶段边界。没有用 argparse 默认拒绝未知产品 token，没有将未知 token 的失败固化成来源 oracle；后续04仍须实现来源 prompt/flag 消费语义。
- 根产品 wheel 无第三方运行依赖，仅有 `ruocun`、必要资源和 distribution 元数据/许可。`tests/support` 是独立 `ruocun-dev-support` distribution，包含 `ruocun_acceptance` 和原 `oracle` 支撑，产品不附加测试工具。MIT 及原版权、NOTICE 原文进入产品 wheel，支撑包也保留 MIT。
- 旧 oracle 测试从已安装 `oracle.driver` 导入，取消按文件动态导入。driver 的显式 `--source-root` 接受冻结参考根，默认 cwd，不再以安装包 `__file__` 猜仓库；guard 作为支撑包资源安装。source cache 从已有锁定材料复制到本票自有 `.cache/oracle`，每轮重新验证冻结805成员并构建；活动 DAO 未读取或改写。

## 实际环境与锁

Windows build26200；CPython3.11.9 x64（MSC 1938/AMD64），解释器 `C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe`。开发 metadata 暂限3.11系列，不表示最终最低版本或其它平台实机支持。

Hatchling1.33.0、build1.6.1、pytest8.4.2、Ruff0.17.3、mypy2.4.1 全部实际安装/运行。`requirements-dev-win311.lock` 是18包 Windows/CPython3.11 激活闭包，每个 wheel 字节对照官方固定版本 PyPI 元数据验证 SHA256，随后在空 venv `--require-hashes` 离线安装，`pip check` 通过。未复制 D07 中不需要的 PyInstaller/TUI 依赖，未将 D21 pin JSON 冒充完整锁。闭包明细、依赖 marker/许可/URL/字节 hash 见 [wheels.json](wheels.json)。wheelhouse 留在忽略的 `.cache/wheels`，按锁可重新下载；隔离 build 只从这份经核验的单版本闭包安装后端依赖。

所有测试、构建、安装和工具子进程由 [tools/run.py](../../../../tools/run.py) 逐条从明确环境白名单启动。HOME/USERPROFILE/AppData/TEMP、pip cache 合成，PIP_CONFIG_FILE=NUL，没有 PYTHONPATH、真实账户变量、用户 pip 配置或自动 pytest 插件。隔离 Python 显式 `-X utf8`。只向日志保存合成输入；当前真实敏感环境值仅本地用于静默扫描，不记录名称或值。

D21 的复合 PowerShell Temp helper 被拒记录已读取；没有重放、翻译重试其复合 helper 或目标。此次执行的是逐条可审查的本票标准工程命令，未遇自动审批拒绝，没有更改安全策略或重试被拒操作。

## 红绿与最终入口

全部实际 argv/cwd/退出与原始 stdout/stderr 见 [commands.json](commands.json) 和 [raw.zip](raw.zip)。这里的 passed 只指实际子路径。

| seam / 入口 | 实际结果 | 证据 label |
| --- | --- | --- |
| 已安装版本 | 未安装时真实 `No module named ruocun` red；普通包安装后 green | `04-red-version` → `09-green-version` |
| 帮助与资源 | 未实现帮助 red；安装真实资源并明确 UTF8 后 green | `10-red-help` → `14-green-help` |
| 开发期 offline 驱动 | 未安装支撑模块 red；实际 CLI/资源/失败边界4个 case green | `13-red-offline` → `19-green-default`；最终 `61-final-offline` |
| 默认 `python -m pytest` | **25 passed / 3 deselected**；保留来源纯分类9项，3个需Node材料的真实来源CLI用 oracle marker 分层 | `56-final-pytest` |
| 原 oracle 完整回归 | 新 pytest8.4.2 / Node22.23.4，实际 **12 passed / 39.77s**；本票独立缓存、真实冻结CLI/fake本地SSE及deadline清理 | `24-oracle12`；raw `oracle/` |
| `python -m ruff check .` | exit0；`--show-files` 包含产品、正式测试、oracle/acceptance支撑及工具，不触碰研究/冻结/旧证据 | `50-final-ruff`、`62-ruff-files` |
| `python -m mypy` | strict，**11 source files**，exit0；仅产品、明确类型的 acceptance 与 tools；不全局忽略错误，也未为typing改变旧oracle协议宽容边界 | `51-final-mypy` |
| `python -m build` | 真正隔离构建 sdist，然后从 sdist 重建 wheel；独立 direct wheel 字节相同；支撑 wheel/sdist 单独构建 | `48-final-build`、`49-final-build-support`、`52-final-direct` |
| 工具有效性 | 合成 Ruff `print(undefined_name)` 和 mypy `-> int` 返回 `'bad'` 都 exit1；修正后均 exit0。它们是工具有效性证据，不混算产品测试 | `40/41` red → `42/43` green |
| 安装闭包 | 最终 `pip check` exit0，所有闭包 wheel 重新核验 | `63-final-pip-check`、`59-final-audit` |

统一驱动识别 oracle/offline/runtime/protocol/live/terminal/install 七个名字。当前其它六 suite 没有接入产品 case，逐项 `not-run` + 原因且非零；未知 suite、空选择、缺少解释器及真实 case 失败都非零。现有来源 oracle 独立回归仍是 source 结果，不把其 passed 写成产品 oracle suite 可用。

来源 Node24 的历史 native exit/UV_HANDLE_CLOSING 继续为 ENV、原始02证据未改且本票不重跑；Node22的12项驱动结果不扩大为完整215来源文件或产品 Agent 通过。旧02的6文件190断言是历史来源证据，本票没有重跑为新分数。

失败过程也原样保留：`05` 暴露 PIP_FIND_LINKS 含空格被拆分，改为 file URI；`06` 表明 editable 另需未锁的 editables，随即采用普通 wheel 安装，不扩运行依赖；`07` 仍是安装未成功而失败。`12` 暴露 `-I` 忽略 PYTHONUTF8，显式 `-X utf8` 后修正；`16/17` 暴露原始字节 CRLF 与独立预期 LF 差异，驱动仅在文本判断中规范 CRLF，保留原始字节和 hash。带 green 字样的中间 label 不能覆盖其真实非零退出。

## 仓库外安装与真实失败

真正仓库外根为 `C:\Users\PC\AppData\Local\Temp\RC03-1105 中文 空格`。最终成品分别装入新空 `product-final` 和 `support-final` venv：前者只装产品 wheel，后者只装产品 + 支撑 wheel；均 `--no-index --no-deps`，没有 pytest/Ruff/mypy/build/Hatchling。cwd 在外部目录，`-I` 下 `sys.path` 没有 Firstcode 源树，没有指向源树的 editable/pth，实际模块 `__file__` 全来自对应 site-packages。未隐藏产品源码，采用独立目录 + 无源路径注入的验收方式。

最终真实 console `ruocun.exe -v` exit0，独立支撑 `python -m ruocun_acceptance offline --python <product-final解释器>` **4 case passed**；版本、帮助、资源和未实现阶段边界都由已安装产品执行。见 raw `60/61/64/65`，不能用纯头部检查替代安装结果。

另在本票先前的新 `product` venv 中将合成安装副本的 `help.zh-CN.txt` 暂移到同目录 `help.zh-CN.missing`，调用真实 `--help` exit70，支撑调用该解释器 exit1；报告准确为 version/unimplemented passed、help/resource failed，保存子进程实际退出与原始输出。缺资源时 `--version` 仍 exit0。随后原路径恢复，SHA256 前后一致：`95f6e17fb6e25e9922348b1b0f3ef29de0038fc51b093891068d9289895d4748`。原源码、冻结证据、用户配置和系统库未移动或修改。

驱动对子进程 deadline/KeyboardInterrupt 实现了结束与等待、后续case记not-run；本票未另做统一驱动的 KeyboardInterrupt 故障注入，明确保留未验。原来源 oracle 的 stall/deadline 取消和服务清理已由12项回归真实验证，两者不混为产品取消通过。

## 封存与清理

[artifacts.json](artifacts.json) 保存成品成员、metadata、工具版本、产物/锁 hash。最终产品 wheel SHA256 `feeb2e2d77d3aaeede79681536f90a8955faef8fbc68d054928626ab84e99a8c`；sdist `bbb07014c9458d555b301b3cd732e45379083447cbf62e354b295ce025146d3d`；支撑 wheel `96b7fead643bd4fd021caf700df0ae3ac878fc1b5e9cab03ebda7e4e3f820769`。三个小型成品另封于 [artifacts.zip](artifacts.zip)，逐成员清单见 [artifact-archive.json](artifact-archive.json)；本地 dist/缓存仍保留。

[raw-manifest.json](raw-manifest.json) 绑定 raw.zip **270成员**，包括66条顶层工程命令、3轮来源CLI raw、外部成功/失败case和质量绿色fixture；原始压缩成员解包到内存逐个核验。生成器 [seal.py](seal.py) 只读取和封存，不重放命令。源码/配置字节输入见 [inputs.json](inputs.json)，汇总与同步范围见 [result.json](result.json)。全部版本化新增路径不超过150字符；ZIP保留长raw路径而不扩大checkout路径。

记录的顶层命令均已 join，来源 CLI 子进程退出、本地server关闭，资源已原路径原字节恢复。专属 venv、wheelhouse、来源cache、外部安装fixture和raw保留供复核；没有递归清理、扫描/终止其它任务进程或清除别的 worktree。付费调用0。没有真实模型、最终Windows Terminal、独立安装器/升级卸载、其它平台或完整业务验收。

[scan.json](scan.json) 对本轮代码、证据及ZIP原成员静默扫描当前真实敏感环境值，结果无命中；不保存变量名/值。正式任务结题与公共状态仍交主代理独立验收。
