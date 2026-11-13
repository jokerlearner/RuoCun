# 最小开发工具链与实现03入口

日期：2026-11-05。任务：[D21](../issues/21-development-bootstrap-decision.md)。研究分支 `research/d21-bootstrap`，起点 `400112fc6341b84f17f22ae57b14660402042690`。本票只形成工程路线与官方元数据，不创建产品 `pyproject.toml`、`src/ruocun` 或产品测试；03当前仍是 blocked/未实施，状态由主会话收录。本研究依照 research 技能，由主会话委派本独立研究代理完成。

## 结论

实现03已有足够输入进入最小开发切片：**开发解释器固定 CPython 3.11.9 / Windows x64，构建后端 Hatchling 1.33.0，build 1.6.1，pytest 8.4.2；Ruff 0.17.3、mypy 2.4.1 采用本轮官方元数据核实的精确开发候选。** 保持已确认的五项入口，先使版本、帮助、资源和 offline 验收真实可运行。完整 TUI、产品 SQLite/恢复、平台沙箱和最终发布不成为这条不使用它们的启动路径的前置；所有对应任务及最终全量范围保持不变。[D21边界](../issues/21-development-bootstrap-decision.md)、[03任务](../../ruocun/issues/03-boot.md)、[规格T-N](../../ruocun/spec.md#t-03--已确认的新增测试入口)。

D07已经实际验证前三个工具，不需重跑分发探针。Ruff/mypy本票只取得 **metadata-only** 证据；这满足D21允许的“官方元数据或真实隔离安装”条件，不代表这两个命令已在此环境运行。补充安装尝试在启动PowerShell进程前被自动策略拒绝，原文仅给出 `blocked by policy`，没有更细原因；不推测原因，也未换等效方式重试。精确请求、错误原文摘录及工具截断说明保存在[未执行请求记录](21-development-bootstrap.attempt.json)，目标临时根后验不存在。03须读取该记录，评估合规的更窄执行方式，并实际安装/执行后才登记工具通过。

## 固定依据与实际边界

| 输入 | 已有事实 | 对03的作用与限度 |
| --- | --- | --- |
| [D07独立复核](../../../integration-evidence/d07/README.md)、[环境](../../../integration-evidence/d07/platform.json)、[hash锁](../experiments/distribution/requirements.lock) | Windows build26200，CPython3.11.9 x64；hash锁安装、sdist/direct wheel构建、5 passed/1 skipped、仓库外新venv18命令；onefile为ENV/未证实 | 可复用开发解释器与Hatchling/build/pytest pin及安装方法；不是03产品、完整包或其它Python版本通过 |
| [D19固定SQLite](../experiments/sqlite-runtime/README.md) | 官方3.54.1 x64 DLL + CPython3.11.9 stdlib sqlite3；明确实际DLL/source ID；原全局3.45.1未改 | 记录后续存储/发布需核对真实运行库。03版本/帮助/offline最小路径不导入sqlite3、不复制DLL，不要求先实现产品DB；进入存储功能后按D19候选与实际产品路径验证 |
| [D11研究](11-test-replay-gates.md)、[逐项清单](11-test-replay-gates.assets.json) | 215 test、58 scripts、16 task、85 fixture共374条，各有处置/入口/拥有任务；215是文件数，非case数 | 按功能逐项纳入，03只运行已实现切片。不能为最小工程删除其余资产或把技术probe继承为产品通过 |
| [来源oracle支撑](../../../tests/support/oracle/README.md) | 独立来源CLI/fake HTTP与12个驱动测试；其环境pytest9.2.0，Node22成功、Node24退出ENV分列 | 复用既有driver/独立预期；pytest8.4.2上的兼容须03实际回归，不能把另一环境结果冒充本锁结果 |

唯一源码参照是[冻结快照](../reference/README.md) `dao-f17e189-7ac654a0dc06`，不是活动DAO。直接读取ZIP中的 `package.json:24–44`（dev/build/test/typecheck/lint入口）、`vitest.config.ts:3–8`（node环境、setup、src/evals测试发现）、`tests/setup.ts:1–4`（默认中文）、`.github/workflows/ci.yml:9–24`（Ubuntu/Node20、22的lint/typecheck/test/build），据此保留职责并替换语言工具，不继承成Windows通过。读取 `src/version.ts:1–2`、`scripts/sync-version.mjs:1–14`：来源版本由package.json生成；`src/index.ts:216–220`有版本flag早退意图。本票不运行来源CLI。对应位置为[MM-305/MM-801/NEW-11](../../ruocun/module-map.md)。

## 开发pin、许可和锁策略

固定[机器可读pin及官方元数据摘录](21-development-bootstrap.pins.json)含每包精确版本、固定PyPI JSON URL、响应摘要、Requires-Python、依赖声明、选定wheel名称/摘要/上传时间/非yanked状态。五包许可均为MIT（pytest8.4.2使用旧`license`字段，其余为`license_expression`）。此处wheel摘要来自官方元数据，**本票没有下载wheel核验字节**；D07三个既有工具的实际安装证明另见上表。

| 用途 | 开发pin | 官方Python要求 / 本轮选定wheel | 证据 |
| --- | --- | --- | --- |
| 后端 | hatchling==1.33.0 | >=3.10；py3-none-any | [固定官方元数据](https://pypi.org/pypi/hatchling/1.33.0/json) + D07实际安装构建 |
| 前端 | build==1.6.1 | >=3.10；py3-none-any | [固定官方元数据](https://pypi.org/pypi/build/1.6.1/json) + D07实际构建 |
| 测试 | pytest==8.4.2 | >=3.9；py3-none-any | [固定官方元数据](https://pypi.org/pypi/pytest/8.4.2/json) + D07实际5passed/1skipped |
| lint | ruff==0.17.3 | >=3.7；py3-none-win_amd64 | [固定官方元数据](https://pypi.org/pypi/ruff/0.17.3/json)；metadata-only |
| 类型 | mypy==2.4.1 | >=3.10；cp311-cp311-win_amd64 | [固定官方元数据](https://pypi.org/pypi/mypy/2.4.1/json)；metadata-only |

这是首轮开发pin，**不是最终最低Python、补丁安全状态或全版本/平台支持声明**。不凭本机存在3.11.9就推荐用户全局安装或降级；03在专属venv使用该实际解释器并记录绝对路径/架构。最终范围由[D12](../issues/12-install-release-decision.md)验证收口。若03需限制未发布开发包metadata，先用`==3.11.*`明确本轮范围；不能把它写成最终产品支持范围或据此删去后续平台任务。

03采用两层记录：pyproject声明直接依赖/精确构建后端，专属Windows/CPython3.11开发锁固定传递依赖、环境marker和SHA256。D07锁是已验证的**实验锁输入**，不要整份复制进产品：其中PyInstaller、TUI依赖等并非03所需。已需的build/Hatchling/pytest传递版本与hash可沿用并重新检查兼容；Ruff无运行依赖，mypy2.4.1另外声明typing_extensions、mypy_extensions、pathspec、CPython上的librt及ast-serialize，完整声明见pin文件，不能只锁两个顶层名就声称可复现。03实际解析、核验所需wheel并补全开发锁，再在空venv按`--require-hashes`安装、执行`pip check`；本票pin JSON是选择证据，**不是完整可安装锁**。[pip hash安装约束](https://pip.pypa.io/en/stable/topics/secure-installs/)。

仅需要默认extras；不为03加mypy的dmypy/mypyc/report/faster-cache等可选依赖。首个offline切片无async代码，不额外引入async pytest插件；有实际异步模块时，由所属票固定插件与执行模式并验证，不能收集到async测试后静默跳过。构建默认使用PEP517隔离；03为`python -m build`提供已核验本地wheelhouse，使后端及其闭包在隔离构建环境离线安装。不要因前端环境已锁就假定隔离后端传递依赖自动锁定。[build职责](https://build.pypa.io/en/stable/)、[pip配置关闭/环境规则](https://pip.pypa.io/en/stable/topics/configuration/)。

## 产品包与开发支撑包

采用`src/ruocun/`标准布局，根pyproject明确只打包`src/ruocun`，console script指向轻量CLI `main`，`python -m ruocun`委托同一入口。版本/帮助路径只加载自身启动所需stdlib与包资源，避免提前初始化模型、扩展、TUI、凭据或存储。没有选择运行模式时，如实际agent路径尚未实现，明确非零退出和未实现说明，不能以固定成功回包冒充agent。[src布局避免源码遮蔽](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)、[Hatch显式文件选择](https://hatch.pypa.io/latest/config/build/)、[ENT-01](../../ruocun/acceptance-matrix.md#ent-01)。

版本文字只维护一处：建议`src/ruocun/version.py`中的`__version__`，Hatch的version path读取该文件生成distribution metadata；CLI与包公开版本读同一值，不再维护另一份手写pyproject version或同步脚本。03测试wheel METADATA、installed metadata、`--version`一致；首轮版本值由03记录为RuoCun自身开发版本，不能机械把DAO0.5.15当作RuoCun版本。[Hatch版本路径](https://hatch.pypa.io/latest/version/)、[MM-801](../../ruocun/module-map.md#mm-801)。

实际使用的帮助/语言等资源放在`src/ruocun/`内明确纳入wheel/sdist，以`importlib.resources.files()`读取；需要真实路径时使用其受控资源上下文，不能拼cwd或读取仓库外preview目录。03验证真实帮助资源，不能塞一个假的parser/grammar文件宣称parser完成。后续所有提示/技能/帧/parser/原生依赖仍按所属票补齐。[Python3.11资源API](https://docs.python.org/3.11/library/importlib.resources.html)、[R-15](../../ruocun/spec.md#r-15--安装打包与发布)。

NEW-11保持`tests/support/ruocun_acceptance/`。在`tests/support/`建立**独立开发支撑distribution**的pyproject，显式包含该包及实际需要的维护支撑，开发venv单独安装它；仓库外调用`python -m ruocun_acceptance offline`也应可导入。根产品wheel不能包含tests、该驱动、冻结参考或研究归档，也不能因驱动导入pytest而给产品增加pytest/Ruff/mypy/build运行依赖。开发editable安装可用于迭代，但不能当作独立安装证据。若适配已有oracle，不再靠仓库根`sys.path`或临时import源码逃过支撑包安装；保持旧driver及对应来源关系可追溯，实际适配由03/后续票扩展。[T-N2边界](../../ruocun/spec.md#t-03--已确认的新增测试入口)、[NEW-11](../../ruocun/module-map.md#新增适配层候选位置)。

## 五项入口的最小真实路径

| 入口 | 03必须交付 | 必须保留的失败边界 |
| --- | --- | --- |
| `python -m pytest` | 默认运行已迁移离线断言与工程安装边界；测试发现范围明确，不递归实验归档；严格注册marker | 源oracle/真实进程可另按显式层运行；live/HITL/install不混入默认。未收集测试保留pytest非零，不用忽略退出码制造green |
| `python -m ruocun_acceptance <suite>` | 七个名字均被CLI识别，只有有真实case与前提的套件才能执行成功；先使offline真实执行版本/帮助/资源/驱动失败传播等case | 缺实现/前提用非零退出、逐case `not-run`与原因；未知suite为参数错误非零。已运行case失败/取消/清理失败均传播，不把一项passed扩张为全suite |
| `python -m ruff check .` | 按下面维护边界配置，真实lint已维护文件，记录版本和exit | 不在质量命令里自动fix/format；不能为历史证据通过而改字节或全局忽略当前核心错误 |
| `python -m mypy` | 配置`files`为核心与明确类型支撑，让无参数命令有实际检查目标；python_version=3.11，核心strict，窄适配SDK | 不设全局ignore_errors/ignore_missing_imports，也不为类型方便缩窄协议接纳范围；新增支撑逐模块明确纳入 |
| `python -m build` | 从真实根包构建wheel/sdist，并由sdist重建；检查成员、metadata、入口、资源及许可 | build成功仅是构建结果；独立安装要另外执行，不能把发布/onedir/onefile或全量install写passed |

依据为[已确认五项入口](../../ruocun/issues/01-test-entrypoints.md)、[D11分层门禁](11-test-replay-gates.md#分层门禁与稳定回归集)。pytest空收集exit5是官方行为，不改为0。[pytest退出码](https://docs.pytest.org/en/stable/reference/exit-codes.html)。统一驱动不新建隐藏产品API；最小case通过真实CLI/模块入口观测外部结果。其证据至少记录case ID、输入与独立预期来源、实际argv/cwd/合成配置标识、退出/输出摘要、passed/failed/not-run/cancelled及清理结果。具体接口由03做最小实现，未来票兼容扩展，不在D21建立另一套产品状态表。

offline只验证已实施切片，不自动调用Node/npm、网络、付费模型、系统设置或来源全量构建。已有02的oracle driver可由独立oracle suite组织，缺Node/受控依赖应明确ENV/not-run非零；不能为让默认pytest离线而删除现有测试，03须将有来源执行前提的case明确分层/标记，保留纯分类/校验断言进入默认集合。runtime/protocol/live/terminal/install即使目前没有产品case，也保留suite名字和诚实状态；03的外部安装冒烟可先作为ENT-01/TEST-07工程证据，不冒充完整install套件已完成。[D11现有证据边界](11-test-replay-gates.md)、[现有oracle测试](../../../tests/test_source_oracle.py)。

## 维护范围及不可改写证据

Ruff对`src/ruocun`、正式迁移测试、`tests/support/ruocun_acceptance`及明确维护的oracle等支撑生效；初始可统一`E4/E7/E9/F/I`、target-version=py311、required-version精确匹配pin，配置文件对齐后再逐票扩展。为保持已确认`check .`，显式include维护路径，并使用extend-exclude及force-exclude保护`.scratch/`、`integration-evidence/`、`.worktrees/`、冻结参考、实验缓存、build/dist与venv。使用`--show-files`记录实际文件清单，确认未误排除核心/支撑；运行只读check。[Ruff配置](https://docs.astral.sh/ruff/configuration/)、[include/force-exclude/required-version](https://docs.astral.sh/ruff/settings/)。

mypy用显式files和排除规则纳入`src/ruocun`及已赋予类型的维护支撑，`tests/support/`作为明确包根处理，避免namespace路径产生同一模块多名字；不要借`mypy_path`依赖仓库源码来证明安装。测试代码可逐模块纳入严格检查；非typed旧oracle适配边界应记录，不能把旧文件排除变成迁移核心的长期免责。研究代码、冻结参考和原始证据不在产品质量维护范围，保留历史输入/结果hash；如将某实验代码迁成维护模块，复制到正式位置、保留来源并按新模块检查，不格式化原件。[mypy配置/files/exclude](https://mypy.readthedocs.io/en/stable/config_file.html)、[AGENTS证据规则](../../../AGENTS.md)。

## 03的TDD与仓库外验收顺序

1. 03独立worktree从已收录D21的集成提交开始。先读本报告/被拒请求记录和既有来源，建立合成HOME/USERPROFILE/AppData/TEMP与显式环境白名单，清除PYTHONPATH和账户变量；本次自有缓存、配置、wheelhouse可追溯。pip禁用真实配置（PIP_CONFIG_FILE指向os.devnull并明确index或no-index）；不更改系统/全局Python。继承语义只用合成父环境验证。[AGENTS](../../../AGENTS.md)、[D07环境与仓库外闭环](../../../integration-evidence/d07/README.md)。
2. 从ENT-01/TEST-07、来源版本入口与规格先写独立预期：未安装不能从外部导入/调用；版本一致；帮助可离线；资源可读；未知suite、未实现suite、case失败和空选择都非零。保存真实red；再建标准包、独立支撑包、入口和真实offline case得到green。不能只断言当前实现自己产生的字符串，也不能把本票的metadata查询算03的red/green。
3. 开发新venv按完整hash锁安装工具和开发支撑，再执行五项入口；lint/mypy用已知错误的小型合成fixture证明确实失败、修复后通过，这只证明工具生效，须与产品测试分列。现有oracle的pytest版本差异实际回归，结果或ENV如实记录；不凭D075passed继承03通过。
4. 构建产品wheel/sdist及支撑wheel，在**真正仓库外的另一个中文空格目录、新venv**做两组验证：纯产品环境只装产品wheel，关闭PYTHONPATH、不装开发工具也能版本/帮助/资源；另一个开发验证环境安装支撑wheel及其锁定依赖，cwd在仓库外实际运行offline。第二组不应从第一组借pytest，也不能通过editable/pth指向源树。
5. 检查产品与支撑模块的`__file__`、distribution metadata和wheel成员，确认均来自对应venv/site-packages；临时使产品源码不可访问，或在只有wheelhouse/fixture的独立目录执行并核对没有源路径注入。所有进程均通过同一显式allowlist启动，stdout/stderr仅保存合成输入，最后留退出/清理回执。纯产品环境内确认没有测试依赖；恢复临时移动源码并核对原字节。[规格T-06](../../ruocun/spec.md#t-06--windows终端与安装验收)。

03的成功只覆盖其实际子案例；例如版本/帮助不能宣称启动模型、SQLite恢复或用户终端体验已过。源故障、回归、已确认差异、ENV和未运行分列，不把安装缺依赖或策略拒绝当作测试green。

## 未决与交付状态

- 本票新增执行只有固定官方PyPI元数据读取与只读来源核对，未运行任何工具`--version`、隔离安装、产品测试、真实模型、Windows Terminal或系统能力实验。安装尝试未启动进程，未创建目标临时根、venv或wheelhouse；没有需要终止的本次工具子进程，没有改全局Python/系统设置。后续03仍须完成实际锁解析、wheel字节核验和五入口/TDD。
- D12仍受D09/D10约束，最终Python/OS/架构支持、完整runtime依赖与第三方许可、独立产物/安装升级回退由原票收口；D07 onefile继续ENV，不要求03绕过系统策略。Shell13、终端18仍受D10技术依赖约束；最终85仍须完整地图/功能/发布证据，不因D21删除任何任务。
- 人工体验按[ADR-0004](../../../docs/adr/0004-final-batch-human-acceptance.md)集中到77/78/85；本票不重复询问已确认入口或代填用户accepted。无新增用户取舍。本研究分支本地保留，不push、不建PR、不merge，报告与pin交主会话收录后才由其更新状态。
