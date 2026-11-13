# 开发与启动子路径

当前按[ADR-0011](adr/0011-python-coding-mvp.md)实现纯Python编码首版；普通入口由`cli.py`接入`agent/runtime.py`，不再返回任务03的“尚未实现69”。缺账户以71退出；未知参数由argparse拒绝，未支持的slash命令明确拒绝。实际交付状态读取[首版记录](../.scratch/ruocun-mvp/spec.md)，用法见[README](../README.md)。产品版本仍来自`version.py`，`ruocun`与`python -m ruocun`共用入口。

## 固定开发环境

首轮是 Windows x64 / CPython 3.11.9，项目 metadata 暂限3.11系列；这不是最终最低Python或跨平台支持承诺。直接工具 pin 在 `requirements-dev.in`；`requirements-dev-win311.lock` 最初为18包闭包，N1以`-r requirements-runtime-win311.lock`增加已批准文字输入的两个运行包，总20包，原工具版本不变。各wheel已对照官方PyPI SHA256，包含Windows/3.11的colorama等依赖。其它平台或解释器须另验，不能复用此锁宣称通过。

开发工具为 Hatchling1.33.0、build1.6.1、pytest8.4.2、Ruff0.17.3、mypy2.4.1。mypy的默认 CPython 依赖包含 librt、ast-serialize、typing_extensions、mypy_extensions 与 pathspec；没有安装可选 faster-cache、报告或 mypyc extras。N1产品运行依赖固定prompt_toolkit3.0.52和wcwidth0.9.4，仅最小TTY输入，不加Rich/完整TUI；原无产品依赖结果保留在N0及更早固定产物。支撑distribution仍无运行依赖，详见[新增运行闭包](../.scratch/ruocun-next20h/evidence/n1-tooling/README.md)。

所有工程进程通过 `tools/run.py` 逐条启动：明确 argv、清空父环境、合成 HOME/AppData/TEMP、禁用用户 pip 配置及 pytest 插件自动加载，保留命令/退出和原始输出。它只用于无真实账户/秘密参数的工程命令，每次 `--label` 必须唯一；不会自动重试失败命令。输出先静默检查当前敏感环境值，仅显示是否命中。`-I` 会忽略 PYTHONUTF8，因此隔离 Python 子进程显式传 `-X utf8`。

批次02当前产品直接依赖prompt_toolkit3.0.52、Rich14.1.0、wcwidth0.9.4，运行锁闭包共6项；上文N1无Rich约定为历史记录，当前安装使用requirements-runtime-win311.lock。Rich用于离屏Markdown/语法着色，终端输入与输出仍由同一个owner管理。

完整pytest的临时根必须显式放在仓库外的专用合成目录，否则“无Git目录”来源夹具会继承RuoCun的.git，改变测试前提。使用本轮独立名称；不要复用未审查的目录。纯安装下的runner夹具用同包`-m ruocun`入口，源码专用loader只在真实源码模式使用。

在仓库根使用实际3.11.9解释器创建 `.venv`。下例 `$bootPy` 是固定路径变量；运行记录位于忽略的 `.cache/boot/raw`：

```powershell
$bootPy = 'C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe'
& $bootPy -I -X utf8 tools/run.py --label setup-venv -- $bootPy -I -X utf8 -m venv 'D:\java supplement\Firstcode\RuoCun\.venv'
$devPy = 'D:\java supplement\Firstcode\RuoCun\.venv\Scripts\python.exe'
& $bootPy -I -X utf8 tools/run.py --label wheels -- $devPy -I -X utf8 -m pip download --index-url https://pypi.org/simple --only-binary=:all: --require-hashes -r requirements-dev-win311.lock --dest .cache/wheels
& $bootPy -I -X utf8 tools/run.py --label install-tools -- $devPy -I -X utf8 -m pip install --no-index --find-links .cache/wheels --require-hashes -r requirements-dev-win311.lock
& $bootPy -I -X utf8 tools/run.py --label install-product --wheelhouse .cache/wheels -- $devPy -I -X utf8 -m pip install --no-deps .
& $bootPy -I -X utf8 tools/run.py --label install-support --wheelhouse .cache/wheels -- $devPy -I -X utf8 -m pip install --no-deps tests/support
```

按实际 checkout 修改绝对路径。产品与 `tests/support` 是两个独立 distribution；安装/交付确认不设置PYTHONPATH、不借sys.path源码导入、不依赖editable。开发期受影响源码定向可在隔离解释器显式指定本树src，回执标为“源码定向”，不替代最终固定wheel/仓库外安装。根 wheel 只含 `ruocun`、自身元数据与必要许可；支撑 wheel 包含 `ruocun_acceptance` 和已维护 `oracle`，不会给产品附加 pytest 或来源材料。

同版本mypy编译扩展被Windows应用控制拦截时，可选已核验的官方2.4.1纯Pythonwheel，保持原类型检查命令。先按[供应源/摘要](../.scratch/ruocun-next20h/evidence/tooling/mypy-pure.json)下载并验hash，再用私有venv执行`pip install --no-deps --no-index --force-reinstall --require-hashes -r .scratch/ruocun-next20h/evidence/tooling/mypy-pure.lock`。根锁接受该版本两种已核验发行包；新wheelhouse按所选flavor放文件，保留原失败及实际使用版本/摘要，不修改系统控制策略。新生成锁时使用独立空wheelhouse，每包选一种发行包；其它已核验flavor摘要由上述供应记录维护。

完整重解析时，先审查 `requirements-dev.in`及其运行输入，在独立空wheelhouse按pin下载，以`tools/lock.py <wheelhouse> --output-lock <目标锁> --evidence-dir <本批证据目录>`核验官方元数据和字节；再在新空venv按hash安装和验证。使用显式输出保留03历史来源记录。仅增补已验运行包且原18包版本不变时，复用各自私有已验venv，按运行锁安装并pip check，记录包/锁hash与实际消费结果。本地wheelhouse不提交；构建find-links使用file URI，含空格路径不依赖环境字符串拆分。

## 五项入口

均通过上面的 runner 单条执行（`--label` 换为新的名字）：

```powershell
& $bootPy -I -X utf8 tools/run.py --label pytest -- $devPy -I -X utf8 -m pytest --basetemp 'C:/Users/PC/AppData/Local/Temp/ruocun-engineering-pytest'
& $bootPy -I -X utf8 tools/run.py --label offline -- $devPy -I -X utf8 -m ruocun_acceptance offline
& $bootPy -I -X utf8 tools/run.py --label ruff -- $devPy -I -X utf8 -m ruff check .
& $bootPy -I -X utf8 tools/run.py --label mypy -- $devPy -I -X utf8 -m mypy
& $bootPy -I -X utf8 tools/run.py --label build --wheelhouse .cache/wheels -- $devPy -I -X utf8 -m build
```

默认 pytest 发现正式 `tests/`，严格注册 marker，默认排除 oracle/live/terminal/install；来源纯归因9项仍在默认集合。需要显式 Node/npm 材料的3个来源CLI测试保留且另跑；空收集、用例失败和无前提不改写为通过。当前维护代码的 Ruff 规则为 E4/E7/E9/F/I，`--show-files` 可审查真实范围。mypy strict 检查产品、明确类型的 `ruocun_acceptance` 与 `tools`；旧 oracle 尚未完整类型化，保留原协议宽容边界并由12项行为回归覆盖。研究、冻结源码、原始证据不纳入代码格式改写范围。

统一驱动识别七个 suite：oracle/offline/runtime/protocol/live/terminal/install。当前 offline 真实调用已安装产品版本、帮助、资源及缺账户拒绝路径；`--python` 指定待测安装解释器，`--output` 必须为未存在的证据目录，`--case` 可显式选择子案例。目标失败/超时/取消及空选择返回非零并留逐 case 记录。其它六 suite 尚未接入产品案例，明确 `not-run`、原因与非零；独立 oracle 的来源通过不会冒充产品 suite 通过。

来源回归可用安装后的 `python -m oracle.driver --source-root <本只读参考根> --node <明确Node22路径> --cache <本票独立可写缓存> --output <新目录>`，或对 `tests/test_source_oracle.py` 执行 `-o addopts=--strict-markers`。runner 的 `--oracle-node` / `--oracle-cache` 只传显式合成工具链选择；参考读取以冻结805文件为准，缓存每轮校验后重新构建。参见 `tests/support/oracle/README.md`。Node22局部通过与Node24原生退出ENV分别留证；没有运行全量来源测试、真实模型或最终终端体验。

## 构建与独立安装边界

`tools/audit.py`及阶段A旧`bind.py`保留03/A/N0固定产物的无运行依赖断言和历史证据路径。N1已有两个运行依赖，使用[本批绑定脚本](../.scratch/ruocun-next20h/evidence/n1-integration/bind.py)及新目录核对固定git archive、sdist、direct wheel、实际安装与恰好两个运行依赖；不覆盖03/A/N0旧回执，不把旧脚本结果冒作新版验包。

默认 build 隔离构建 sdist，再从 sdist 构建 wheel；另做 direct wheel 字节对比。`tools/audit.py` 核对真实成员、metadata、资源、MIT/NOTICE、闭包 wheel 字节及产物SHA256。实际安装另在真正仓库外中文空格目录的两个新 venv 完成：纯产品只装产品 wheel，开发验证环境另装支撑 wheel；都不借源码路径或开发工具。CLI资源缺失要真实非零、支撑驱动传播失败，恢复后再次通过。

任务03历史证据位于`.scratch/ruocun/evidence/03-boot/`，当时只覆盖启动子路径。当前首版已接入固定SQLite运行库及普通会话，自动证据读取[首版任务](../.scratch/ruocun-mvp/spec.md)；后台生命周期、独立程序及高级迁移仍后置，其它平台实机与用户Windows Terminal体验未验。
