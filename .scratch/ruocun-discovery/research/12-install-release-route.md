# D12：安装、构建与发布路线

后续范围修订：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)按D2仅交标准Python包，Windows独立程序移出；D3改为人工停进程/备份/安装更新，不承诺自动跨版本迁移/失败回退。下文独立产物及旧升级要求保留为研究历史，标准包、CI、资源许可和完整文档仍有效。

日期：2026-11-10。任务：[D12](../issues/12-install-release-decision.md)。研究分支 `codex/sprint-release-route`，工作树 `.worktrees/sprint-release-route`，起点 `30897bbcbbefb0ba7b0364a6ad99a9d855a1a6b1`；领取记录已在起点提交。本文按 research 技能由独立研究代理完成，供主协调收录；只新增本报告，不修改产品、公共状态、规格、对应表或验收矩阵，不安装依赖、不运行历史探针、不调用模型、不发布远程产物。

## 1. 推荐定案

**采用两类产物：标准 wheel/sdist；Windows x64 的原生 console onedir 压缩包。首个发布验证配置固定为已实测的 CPython 3.11.9 x64、官方 SQLite 3.54.1 x64 DLL 与该解释器标准库 sqlite3 的实际组合。** 沿用 Hatchling 1.33.0 / build 1.6.1 与已确认的五项工程入口；Windows 独立程序先沿用 D07 已验证的 PyInstaller 6.22.3 / hooks-contrib 2026.9。onefile 不作为本轮必交形式，原失败与系统策略 4551 的 ENV/未证实状态保留。[D07实验](../experiments/distribution/README.md)、[D07独立复核](../../../integration-evidence/d07/README.md)、[D19候选](../experiments/sqlite-runtime/README.md)、[D21](21-development-bootstrap.md)

这足以关闭“发布路线缺少技术选择”的问题，**不表示最终产品、所有平台或79–83已通过**。79–83仍逐票完成实际产品构建、干净安装、原生角色生命周期、恢复、升级卸载、资源与许可门禁；85仍等待77/78人工accepted及其它既定完成条件。[R-15/T-06](../../ruocun/spec.md)、[ADR-0006](../../../docs/adr/0006-batched-sprint-workflow.md)、[79](../../ruocun/issues/79-wheel.md)–[83](../../ruocun/issues/83-docsrelease.md)

沙箱采用[ADR-0008](../../../docs/adr/0008-source-first-sandbox-parity.md)：默认关闭、网络默认允许，仅macOS Seatbelt/Linux bubblewrap有来源后端；Windows显式请求时返回不支持。发行说明必须呈现这个真实边界。D22原严格A仍FAIL，额外Windows隔离后端目标已被替代，D12不再等待驱动、service、VM或管理员组件；其它Windows能力、审批、取消、持久恢复门禁继续存在。

上述均是既定范围内、由源码和现有实证足以决定的工程选择，**本报告未发现必须再询问用户的新范围取舍**。用户保留最终真实终端和安装体验验收。按用户最新要求，测试沿DAO已有测试语义迁移，加必要构建、安装与角色可运行证据；不增加特别多额外测试、逐patch穷举或新矩阵门槛。真实未验范围据实标记，既有性能阈值保留，未测不声称。

## 2. 唯一来源与DAO核对

迁移唯一参照为[冻结快照](../reference/README.md) `dao-f17e189-7ac654a0dc06`，基准提交 `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`，805成员源码树SHA256 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`。下表 `src/...` 等路径和行号均指ZIP原始成员，不以供应商后来目录或活动DAO改动替换冻结输入。本轮仅对sandbox额外只读比较活动文件。

| 冻结来源 | 实际机制 | RuoCun处理 |
| --- | --- | --- |
| `package.json:10–23,26–29,38,67–77` | npm命令为`dao→dist/index.js`，Node>=20；build为tsc；bundle另走Bun compile；文件白名单含dist、README、CHANGELOG、LICENSE；SQLite/TUI/parser是实际依赖 | 保留标准包和独立形态两条职责，以Python工具替换语言绑定；检查最终产物成员和真实依赖 |
| `scripts/sync-version.mjs:1–14`、`src/version.ts:1–2` | bundle前从package.json生成静态版本 | RuoCun继续用已落地的`version.py`单源，构建metadata/CLI/内部角色均核对；不把DAO0.5.15当作RuoCun版本 |
| `.github/workflows/ci.yml:9–24` | Ubuntu × Node20/22，lint/typecheck/test/build | 保留质量职责，补Windows本机构建/安装证据；该来源CI不证明Windows支持 |
| `.github/workflows/release.yml:13–35` | Ubuntu上Bun五目标交叉构建后上传；此入口直接bun build，没有调用sync-version，也没有产物运行/hash门禁 | 可沿用发布清单组织方式，RuoCun逐本机产物验收；版本/hash/运行门禁由79–83落实 |
| `src/tools/managed_shell.ts:176–195` | 请求沙箱失败即抛错；source/Node/bundle分支选进程入口，再用`--dao-shell-runner`明确角色自spawn | 标准包与冻结exe分别选择同版本内部角色入口；禁止冻结exe当通用解释器 |
| `src/tools/shell_runner.ts:119–123` | runner按manifest的spawnSpec或普通Shell启动命令 | 保留执行权威runner与controller的生命周期分离，不因UI退出重跑副作用 |

### ADR-0008沙箱独立核验

本轮直接从ZIP成员流计算 `src/tools/sandbox.ts` SHA256为 `2f5dbb56b15529eeaafe6fa8bd528c2e32b1e0d739412c913a78b2ebfa6ebb4f`；活动 `D:/java supplement/Firstcode/dao-code/src/tools/sandbox.ts` 同hash。活动DAO HEAD仍为 `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`。与ADR-0008记录的hash和行为一致；本轮没有运行DAO或声称平台隔离实测通过。

| 正确来源行号 | 核对结果 |
| --- | --- |
| `sandbox.ts:6–12` | `DAO_SANDBOX`、`DAO_SANDBOX_NO_NET`各自严格等于`"1"`才生效 |
| `sandbox.ts:15–20` | 只在固定四个目录查后端可执行文件，并非任意PATH发现 |
| `sandbox.ts:23–34,43–47` | macOS默认allow，收紧写入到cwd/临时目录/指定设备；可选deny network；缺sandbox-exec明确错误 |
| `sandbox.ts:41–42` | 未开启或本次disableSandbox时返回null |
| `sandbox.ts:48–64` | Linux bwrap以全盘ro-bind、cwd bind、tmpfs/proc/dev、die-with-parent包装；可选unshare-net；缺bwrap明确错误 |
| `sandbox.ts:65` | Windows及其它平台返回“当前平台不支持沙箱(仅 macOS/Linux)”；文件共66行 |
| `exec_shell.ts:185–189`、`managed_shell.ts:176–179` | 明确请求但不可用时拒绝执行 |
| `process_manager.ts:178–181` | 旧分支把error退回普通Shell；R-16/ADR-0008已保留修正，不能把它复制成隔离成功 |

ADR-0008的Windows“68”、Linux“49–66”等行号需要主协调更正；行为及hash不冲突。开关解析沿[D09](09-storage-extension-route.md#原生路径兼容source-map与写回)的RUOCUN优先、DAO fallback及“键存在/空值”契约，不另造通用bool解析。

## 3. 支持范围与最低版本

| 维度 | 初始发布验证配置 | 已有证据及限制 |
| --- | --- | --- |
| OS/架构 | Windows x64；先验当前Windows 11 build26200环境 | D07/D19/03实测；这不是已证明的最低Windows版本，不能写Windows10/任意Windows11均已支持 |
| 验证解释器 | **CPython 3.11.9 x64** | 该精确解释器与stdlib `_sqlite3.pyd`、固定DLL已验；PyPy、3.11其它patch、3.12+均没有本轮实测证明 |
| Python范围metadata | **保留当前`Requires-Python ==3.11.*`**；Windows wheel采用平台标签 | 版本声明与实测清单分开；3.11系列声明不是每个patch都实测的承诺，不收窄为3.11.9或新增逐patch穷举要求。pip版本字段不能表达实现/CPU位数，SQLite初始化仍核对真实组合 |
| wheel标签 | 内置x64 SQLite DLL后采用`py3-none-win_amd64`，不得保留`any` | D07已实际生成此标签及`Root-Is-Purelib:false`；wheel不携带宿主stdlib `_sqlite3.pyd`，实际解释器绑定仍须逐组合核对 |
| 独立程序 | Windows本机构建的console onedir；不要求用户预装Python/Node/Bun | D07只屏蔽PATH、宿主仍有Python；80仍须在干净普通用户/无Python及Node环境验证完整产物 |
| Windows ARM64/x86 | 不发布未测架构产物 | ARM64本机仿真、交叉编译或x64可执行启动都不等于原生ARM64通过 |
| Linux/macOS | 保留跨平台模块/CI设计，**实机pending** | 不提供冒用Windows DLL的跨平台wheel；以后逐OS/arch选择已修复SQLite组合、锁和原生产物，再实机验证 |

最低Python声明沿当前3.11系列，实测基线为CPython3.11.9；最低OS兼容范围尚未建立。以单机成功推导更低OS或其它CPU均已通过没有依据；82的支持矩阵先如实列实际环境和pending，不把“未逐patch测”变成新增安装拒绝条件。未来确需扩到其它Python系列/原生架构时再用实际产品构建安装证据说明，不为可查工程事实反复向用户询问。[D07平台](../../../integration-evidence/d07/platform.json)、[D21](21-development-bootstrap.md)、[03独立复核](../../ruocun/integration-evidence/03-boot/r2/README.md)、[82](../../ruocun/issues/82-crossci.md)

## 4. 工具链、锁与标准包入口

沿用当前src布局、console script `ruocun = ruocun.cli:main`、`python -m ruocun`同一入口、Hatchling动态读取`src/ruocun/version.py`。当前产品`pyproject.toml`运行依赖仍为空，README/开发文档主要描述03最小启动；它们不是完整产品的依赖/能力清单。后续已实现的提示、配置、Chat/Responses演示等须按实际产品状态更新，禁止直接把实验包或开发闭包当最终产品包。[当前pyproject](../../../pyproject.toml)、[版本](../../../src/ruocun/version.py)、[CLI](../../../src/ruocun/cli.py)、[开发说明](../../../docs/development.md)

保留三个分别可审计的依赖集合：

1. **产品运行集合**：pyproject列实际直接依赖，Windows/CPython3.11.9运行锁固定全部传递依赖、wheel选择、SHA256及markers；附离线wheelhouse清单。沿D10已选TUI组合 `prompt_toolkit==3.0.52 / rich==14.1.0 / wcwidth==0.9.4`；D07同时实测Pygments2.21.0、markdown-it-py4.2.0、mdurl0.1.2。MCP沿D09的`mcp==1.30.0`与实际闭包；真正parser/grammar和其它模块依赖在所属产品票实施后汇入。不能只锁这几个顶层名或加入合成grammar宣称闭包完整。
2. **开发集合**：沿用已实装的`requirements-dev-win311.lock`18包，含Hatchling1.33.0、build1.6.1、pytest8.4.2、Ruff0.17.3、mypy2.4.1及真实传递依赖。新增产品/测试需要的依赖时重新审查完整闭包；不把本文件复制成用户运行依赖。
3. **冻结构建集合**：从D07精确PyInstaller6.22.3 / hooks-contrib2026.9及其hash锁起步，使用独立构建venv，从最终wheel安装后冻结。按产品新增原生/动态依赖审查收集规则，不把完整源码checkout或开发工具收进成品。

依据：[当前开发锁](../../../requirements-dev-win311.lock)、[D07锁](../experiments/distribution/requirements.lock)、[D10终端组合](10-terminal-windows-route.md#31-框架与依赖边界)、[D09外部扩展](09-storage-extension-route.md#外部扩展实际子集与适配义务)。锁的维护原则沿现有`tools/lock.py`/开发说明：官方固定元数据与实际wheel字节校验、空venv `--require-hashes`、`pip check`；没有扩展到本轮安装执行。

五项入口继续为`python -m pytest`、`python -m ruocun_acceptance <suite>`、`python -m ruff check .`、`python -m mypy`、`python -m build`。构建采用PEP517隔离，后端闭包来自已核验wheelhouse；build默认sdist→wheel，另做direct wheel对比。产品与`tests/support`支撑distribution分别安装，支撑/pytest/oracle/冻结源码/研究材料不进入用户wheel。已有[03独立证据](../../ruocun/integration-evidence/03-boot/r2/README.md)证明该组织可行，但只覆盖03路径。

79的可执行顺序为：新构建环境安装锁→五入口及实际已实现suite→`python -m build`→direct wheel对比→列metadata/entrypoint/资源/许可/原生成员与hash→仓库外中文空格新venv离线安装→移走源码/关闭PYTHONPATH→完整CLI/恢复/扩展/角色验证。所有命令通过现有受审工程runner逐条启动，合成HOME/config/session/TEMP、明确环境白名单；build、install、runtime、live、HITL证据分列。[开发入口](../../../docs/development.md)、[79完成条件](../../ruocun/issues/79-wheel.md)

## 5. SQLite、资源与许可随包交付

### 固定SQLite及payload

Windows x64采用官方 `https://www.sqlite.org/2026/sqlite-dll-win-x64-3540100.zip`，与CPython3.11.9标准库绑定组合。固定ZIP SHA3-256 `c2d09c8babb9399277055c057c97a53f1ffd7c5f11d0c1f2118ffdfa39f2daa4`、ZIP SHA256 `f436f53ad8f965af43f3817b42c99c0689e6787f6b7ace208fe38dab7ffc4971`、DLL SHA256 `4b59d3cded9dc1608544160f3b4b10ac974c6ac0d6ffc23064e5f4c8dbd05aea`；source ID为 `2026-10-16 14:45:20 555e07ef33f69a0957d24d8e555b702464a131d6f1607f4c3c1e4551e8e6ca76`。供应源和修复依据沿[候选回执](../experiments/sqlite-runtime/candidate.json)与其保存的官方页面，不改成“任意较新版本”。没有签名验证或独立可重现编译证明。

产品wheel/sdist显式包含本架构DLL及供应回执/归属；先绝对路径、限定搜索加载，再import `_sqlite3`。实际使用SQLite的UI/controller、runner/recovery分别核对runtime、source ID、DLL/驱动hash等既有清单；缺失、hash不符、先载旧库或runtime不符均明确失败，不静默用系统库。最终wheel/onedir在没有开发DLL路径时，复用已迁移来源存储/恢复测试与必要实际运行证据核对WAL/FULL/timeout和自身恢复，不为发布重复整个D19探针故障矩阵；D19实验本身不自动变成产品REC/PKG通过。[ADR-0005](../../../docs/adr/0005-runtime-storage-compatibility.md)、[D19分发门禁](../experiments/sqlite-runtime/README.md#分发及发布门禁交接)、[D09](09-storage-extension-route.md)

onedir须逐文件登记整个payload。D07真实清单包括`python311.dll`、`_sqlite3.pyd`、根`sqlite3.dll`与包内副本、`VCRUNTIME140.dll`、`libcrypto-3.dll`、`libssl-3.dll`、`libffi-8.dll`、wcwidth的`_wcwidth_c.pyd`及数据文件；最终产品按其**实际**成员补齐来源、版本、hash、许可。D07额外发现的根sqlite3.dll被明确pin为同一固定DLL；最终freezer依赖分析也须发现并核对所有副本，不能只核包内文件。[D07逐文件清单](../../../integration-evidence/d07/onedir-manifest.json)、[pin回执](../../../integration-evidence/d07/pin.json)

### 资源清单

| 资源/依赖 | 交付要求与失败边界 |
| --- | --- |
| 帮助、i18n、system/agent/reflect等提示、工具schema、冻结provider/模型定义 | 产品包内显式纳入；按实际loader读；缺资源报具体错误。模型ID/context/默认端点等保持冻结数据，不按供应商当前目录重写 |
| 8个core技能、bundled agents/commands等内置内容 | 保留实际正文、发现/同名覆盖和namespace语义；磁盘外部技能保留资源相对路径；安装不访问研究目录或preview路径 |
| 欢迎帧、Sixel/时序 | 保留已冻结嵌入内容与hash/provenance；快照外原PNG/manifest未收齐，不能声称可从源图重生成或已有独立素材授权 |
| parser/grammar/原生扩展与Unicode宽度表 | 以真实代码解析、动态加载和宽字符路径验证打包；D07的grammar.json是合成布局占位，不能成为产品parser证据 |
| 外部Hook/MCP/LSP与工具链 | RuoCun自带的协议客户端完整；用户声明的server命令/解释器按来源执行，缺依赖明确诊断；“主程序无需Node”不保证任意第三方扩展无需Node |

资源读取沿现有`importlib.resources`与所属模块职责；需要真实路径的原生loader/parser须保留资源的实际存活期，长存runner不能依赖controller已退出的临时资源上下文。最终wheel/sdist/onedir分别列清单并从实际安装位置读取，测试来源、配置、提示/技能和研究资料不能互相冒充。[R-12/R-13/R-15](../../ruocun/spec.md)、[PKG-05与E-02](../../ruocun/acceptance-matrix.md)、[D07资源边界](../experiments/distribution/README.md#d06-和资源边界)

### 许可与归属

保留根DAO MIT及原版权声明、NOTICE中的冻结来源和迁移关系；RuoCun版本与来源版本分开。每个实际携带组件记录名称、精确版本、用途、来源URL/归档hash、许可原文、安装路径和是否进入最终产物。D07已保存prompt_toolkit、Rich、wcwidth、Pygments、markdown-it-py（含上游markdown-it许可）、mdurl、CPython、PyInstaller及hooks的真实许可文件与hash，作为清单起点，不能代替完整产品许可审计。[LICENSE](../../../LICENSE)、[NOTICE](../../../NOTICE.md)、[D07许可索引](../experiments/distribution/pkg/src/ruocun_probe/licenses/index.json)

SQLite归属按D07登记的[官方Public Domain页面](https://www.sqlite.org/copyright.html)，保留来源、版本和下载回执。PyInstaller实际COPYING含GPL及bootloader exception、runtime hook规则，hooks-contrib也区分构建hook与runtime hook；随最终使用部分保留适用原文，不能只把freezer统称MIT或删去声明。冻结CPython/原生库/运行时payload也逐项保留相应声明，D07清单没有完成最终产品每个DLL的归属闭环，83须补齐。[PyInstaller原文](../experiments/distribution/pkg/src/ruocun_probe/licenses/l7.txt)、[hooks原文](../experiments/distribution/pkg/src/ruocun_probe/licenses/l8.txt)、[CPython原文](../experiments/distribution/pkg/src/ruocun_probe/licenses/python.txt)

## 6. 独立角色与Windows安装升级

### onedir构建与角色

沿D07从**已安装的最终wheel**构建原生console onedir，命令职责为`python -m PyInstaller --console --onedir`，产品专用spec/entry及collect/hidden-import规则由80在实际依赖清单上维护。不能照抄实验`--collect-all ruocun_probe`或从checkout偷偷找缺资源；输出后整目录封存、逐文件hash和总归档hash。D07的393文件/37,898,072字节仅是探针尺寸，不是最终产品指标。[D07构建脚本](../experiments/distribution/freeze.py)、[D07成品边界](../experiments/distribution/README.md)

| 角色 | 标准包入口 | 冻结产物必须验证 |
| --- | --- | --- |
| CLI/controller/UI | 安装venv的`ruocun`或`python -m ruocun` | console/中文输入/退出码/终端恢复及正确包版本 |
| 持久Shell runner | 同版本解释器+安装包的明确内部角色 | 同版本exe的明确角色再入；owner退出后继续、认领/接管/取消/receipt导入；不递归拉UI |
| 原生IPC transport helper | D08已选的专用受监督内部角色 | 只承载I/O材料；退出确认/端点换代；失败不杀执行权威runner，不加载另一份业务状态 |
| DNS helper | 当前`resilient.py:326–345`默认用`sys.executable -I -X utf8 -m ruocun.client._dns_helper` | 当前源码在frozen且没有resolver_command时明确报“尚未配置”；80必须绑定同版本exe的DNS内部角色并核对stdin/stdout有界协议、取消和退出，不调用宿主Python或退回无法取消的阻塞线程 |
| 系统定时dispatcher | 59/81安装策略规定的同版本可定位入口 | 安装路径、cwd、版本/manifest身份、升级后入口及旧任务诊断；不能把冻结exe当通用`python -m`解释器 |

持久runner、IPC helper和DNS helper寿命不同，仍使用原模块负责的角色/监督语义；这里只统一分发定位，不新增执行框架。入口在进入主UI、配置/模型初始化前分派内部角色，角色不列为用户业务命令。DNS仅解析角色不用SQLite；各角色按其真实职责加载资源并验证身份，不能由父进程清单替代子进程实际运行证明。[D08角色/IPC契约](08-python-runtime-route.md)、[R-15](../../ruocun/spec.md)、[当前DNS路径](../../../src/ruocun/client/resilient.py)、[DNS helper](../../../src/ruocun/client/_dns_helper.py)

D07对独立长存子进程采用`PYINSTALLER_RESET_ENVIRONMENT=1`，onedir三场景已验；本报告沿其固定[官方依据快照](../experiments/distribution/sources/pi-pitfalls.rst)，不机械清空所有产品子进程变量。原onefile共享解包清理失败仍为真实red，修正产物4551拒绝后未重试。若以后选择onefile，须另补独立解包/父退出/长runner/取消/重启/升级的产品实证；本轮onedir路线可独立完成。[D07独立角色复核](../../../integration-evidence/d07/README.md)

### 安装、升级、卸载与数据

初始独立分发推荐**普通用户的版本化onedir目录+稳定启动入口**：完整目录解压到用户可写安装根的`<version>/`，安装辅助脚本只管理本产品文件、稳定入口和可选用户PATH记录；系统定时使用59既定dispatcher/manifest，不直接固化临时构建路径。81实现并测试具体脚本和路径，发布包不依赖管理员隔离组件、全局Python修改或机器级PATH。标准包则安装到专用venv，离线wheelhouse为完整受支持闭包。[81](../../ruocun/issues/81-upgrade.md)、[D10定时策略](10-terminal-windows-route.md)、[R-15](../../ruocun/spec.md)

升级顺序：先在新版本目录校验清单并独立安装/冒烟，再切换稳定入口；活runner继续使用其原版本payload，旧目录保留至所有该版本自有角色退出、receipt处理完成。controller/runner/helper协议、receipt/schema和产品版本分别校验；版本不兼容明确诊断，不能偷偷重启副作用。回退入口不能解决已经升级的数据格式，数据迁移必须在排他owner及一致备份下完成；新版本已经写入/产生未知副作用时，不宣称可以盲目复制旧DB回滚。[D08/D09](09-storage-extension-route.md)、[REC-16](../../ruocun/acceptance-matrix.md)、[80/81](../../ruocun/issues/81-upgrade.md)

卸载保留原生用户`~/.ruocun`和项目`<cwd>/.ruocun`中的配置、记忆、自身会话、附件、receipt等用户数据；凭据按58已定原生身份处理，不删除DAO旧服务。清除运行程序/入口前识别仍存活的自有角色，明确等待/取消或保留其旧payload，禁止靠卸载误杀、删除未收据任务或跨品牌清理。DAO兼容来源只读；旧DAO会话不导入。备份通过SQLite一致快照/明确关闭后的完整材料，保留runner本地收据与附件，不把单拷活`session.db`称为恢复成功。[D09原生数据/只读source map](09-storage-extension-route.md)、[ADR-0005](../../../docs/adr/0005-runtime-storage-compatibility.md)、[81 PKG-04/REC-16](../../ruocun/issues/81-upgrade.md)

81按既有票据场景归并验证中文空格/PATH、安装升级失败保旧、备份恢复、runner版本/资源和卸载保留数据；用少量真实产品安装流程覆盖所需行为，不新增组合排列或穷举矩阵。D07的18命令只证明外置合成配置/DB字节保留，不证明产品schema迁移或真实runner升级。[D07独立安装](../../../integration-evidence/d07/README.md)

## 7. 79–83的明确出口

下表是既有任务完成条件的实施解释，不改变依赖或状态，也不以清单增加额外测试门槛；来源已有测试与必要真实构建安装流程可复用同一证据。每票仍按既有工作流独立复核、集成commit和对应记录。78→79只在ADR-0006及工具适配真正核验自动出口后消费，不用本研究绕过尚未满足的普通依赖。[任务图/执行规则](../../ruocun/sprint-48h.md)、[79](../../ruocun/issues/79-wheel.md)

| 票/案例 | 可执行出口 | 仍不能据此声称 |
| --- | --- | --- |
| **79 / PKG-01、05** | 完整产品wheel/sdist、sdist重建、版本/依赖/资源/原生/许可清单；仓库外新venv/无PYTHONPATH/源码不可访问；离线安装、实际SQLite与角色、扩展、自身正常/异常恢复通过 | 03最小帮助资源或D07合成grammar不代替完整产品；构建exit0不代替安装/恢复 |
| **80 / PKG-02、03** | Windows原生console onedir；干净普通用户/无Python及Node环境运行；资源、运行库和DNS/IPC/runner/dispatcher实际分派；复用已有角色/恢复语义测试，核对owner退出后资源仍可用与实际payload身份 | 屏蔽PATH不等于干净新机；onedir不证明onefile；自动内容不代替WT人工画面 |
| **81 / PKG-04、REC-16** | 用户级安装与稳定入口、版本化payload、升级/失败保旧/有界回退、数据一致备份恢复、活runner版本兼容、卸载保留原生数据与DAO只读边界 | pip探针原字节保留不等于产品schema或receipt可恢复 |
| **82 / WIN-11、PKG-06** | Windows本机五入口/实际支持组合安装冒烟；平台矩阵区分构建、自动、实机、人工；Linux/macOS延迟导入/构建设计检查可做，实机保持pending | Ubuntu/交叉构建/WSL不能填写Windows或macOS实机通过 |
| **83 / PKG-05、06** | 版本/commit/源码树/locks/构建OS-arch/实际runtime与逐文件hash；可重建步骤、许可/provenance、安装升级卸载/备份恢复/故障排查/平台与兼容差异文档、release notes齐全 | 无PNG原图不声称重生成；本地可重建不等于字节级可重现/签名验证；本轮不公开发布 |

83的交付清单至少包括标准wheel/sdist、Windows x64 onedir归档、完整运行wheelhouse清单/获取步骤、构建与原生payload清单、hash、依赖锁和许可原文、版本/CHANGELOG/release notes、安装/卸载/失败回退/恢复文档、已知差异与平台矩阵。冻结快照和测试支撑留开发仓库，不塞进用户产物；产物hash和证据commit绑定，最终签名、远程tag/publish等动作不由本研究执行。[83](../../ruocun/issues/83-docsrelease.md)、[R-15](../../ruocun/spec.md)

最终WT-01..09的IME、连续缩放、粘贴、焦点/图形和退出体验由77/78/85集中人工验收；性能沿ADR-0006的PKG-07四个子案例，不新增简化阈值。本报告没有任何产品自动通过、真实模型通过或用户accepted新增。[ADR-0004](../../../docs/adr/0004-final-batch-human-acceptance.md)、[ADR-0006](../../../docs/adr/0006-batched-sprint-workflow.md)

## 8. 收录时的文档冲突与本轮实际执行

以下是起点提交中的遗留文字，主协调应在公共收录时标为历史或改成现行契约，避免后续代理重新等待已撤销目标；原始失败实验不重写：

- ADR-0008的sandbox源码行号：改为本报告第2节核对结果；hash及行为保持。
- CONTEXT“当前阶段”末句仍有“完整Windows沙箱、发布…各自门禁”，需明确沙箱门禁现为DAO支持边界，Windows原生后端已被ADR-0008替代。
- D12“依据与边界”仍保留ADR-0007段称“不因此解除D22”，且Comments保留新增D22前置的旧结论；须明确其已被ADR-0008取代，实际Blocked by已移除D22。
- implementation第11行仍以“当前”叙述接受额外组件/等待回滚环境；历史接续段仍有“D12/60/61受D22真实结果约束”等旧态；顶部最新ADR-0008虽已覆盖，应避免这些旧句被误当当前授权。
- sprint计划第109行仍称`D22→D12→D13→D14`是现技术链、D22目标不可缩减，第163行仍称D22不通过阻塞60；应按ADR-0008区分历史失败与替代后的真实依赖。第9行新范围说明继续有效。
- ADR-0005末段、D08/D09/D10历史研究中“完整Windows沙箱尚未闭合/不降级”的旧限制应通过醒目替代指针解释，不改变历史证据。spec R-16尚有“完整沙箱由10/12收口”的旧待决措辞，D12收录后可同步实际路线。
- README/docs/development仍以03最小工程为主体；79–83按实际产品成熟度重写安装/能力状态，避免把开发metadata、18包开发锁、无runtime依赖的旧说明当完整发行支持矩阵。

本轮执行仅为Git身份/status核对、项目记录/当前产品文件读取、冻结ZIP成员流读取与sandbox SHA256、活动DAO该文件只读hash和HEAD核对，以及本报告写入。没有运行来源/产品/实验脚本、测试、build、pip、SDK或native工作负载，没有读取真实配置、会话、凭据或隔离日志。数据读取阶段使用PowerShell/.NET内存读取；来源核对与后续数据读取先清空进程环境并设固定白名单、合成HOME/USERPROFILE/TEMP，未借真实账户环境。未创建本次受管工作进程、安装目录或可清理运行产物。

验证限度：本报告复用D07/D19/03已有独立资产的明确范围，没有重跑它们，不能产生新的产品green。报告67个Markdown链接均完成相对文件存在性检查，缺失0；暂存报告`git diff --cached --check`通过，改动仅本文件。纯文档变更未运行产品测试。研究提交留本地，由主协调单独收录并更新D12/map/status，不整分支合并。
