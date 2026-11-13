# Task03 独立 merger 复核

复核者 `/root/merge_03_boot`，独立 worktree `.worktrees/m03` / `merge/03-boot`。
从 clean `255af6950bbcc3dcd6f08a6a26956a8110d11b7a` 开始，quiet FF 正式集成后 no-ff 合入正式候选 `4a833cd703ae9c22669eb759ab2781139964afef`（首个 merge `3a2c7880044ae0983a292da8d3c9fa8d6220ac35`）。
随后 no-ff 同步只含 D10/D22 公共研究/门禁文档的正式集成 `46c8243`，该次 merge `c9f1c884865d993108c1443eabfd004f06abd9d6`。对候选的产品、测试、工具、构建/锁/配置、README、开发说明和原03证据差分为零，因此没有因无关文档重跑整条安装链。

**当前判定：未全部通过，不能关闭 Task03。** 已发现驱动等待发生 `OSError` 时的真实子进程清理及证据记账缺陷；产品代码和来源预期保持原样，交主代理处理。这里不是聊天/TUI/SQLite、正式发行或最终 Windows Terminal 体验通过。两个母案例只能按实际启动/工程子路径记录。

## 阅读与静态核查

已读 AGENTS、CONTEXT、ADR-0005、正式03票、规格 R-01/R-02/R-15/T-N、module-map/验收对应条目、D11报告与责任边界、D21报告/pins/原拒绝请求，以及原03 README/原始 red→green。直接读取唯一冻结 source.zip 的 package.json、version.ts、sync-version.mjs、index.ts:200–220/280–345、Vitest/setup/CI、Read工具与对应测试、plan模式测试契约；没有从活动DAO取得新版本。

逐个读新产品实现、acceptance/environment、oracle driver变更及全部正式测试、tools、锁和pyproject/构建配置、许可证与文档。版本优先分支符合来源意图；来源没有独立帮助早退，`--help/-h` 是 ENT-01/R-15/D21 明确要求的本地帮助增量。未知产品token没有被新解析器固化为拒绝。69只是尚未实现Agent的阶段边界，offline第四项只证明不会伪装成功。

## 独立自动结果

全部工程命令由既有 `tools/run.py` 逐条启动：明确allowlist、合成HOME/AppData/TEMP、自有pip cache、NUL配置、无PYTHONPATH/账户变量；Python隔离模式显式UTF8。仅最终静默扫描控制器读取当前敏感环境值用于本地匹配，不保存变量名/值，不产生测试/构建子进程。D21被拒的复合PowerShell helper没有重放、翻译或等效重试，本轮未遇自动审批拒绝。

| 检查 | 独立结果 | raw label |
| --- | --- | --- |
| 全新开发venv + wheelhouse | CPython3.11.9/x64，18个wheel从固定hash锁重新下载；逐wheel对官方固定PyPI JSON/字节hash、Windows/3.11/default-extra激活闭包及版本约束核对；本地 `--require-hashes` 安装 | 01–04，closure.json |
| 默认pytest | **25 passed / 3 deselected**，pytest8.4.2 | 09 |
| 来源oracle | **12 passed / 39.66s**，pytest8.4.2 / Node22.23.4；本次805源码字节核验和自有dist重build，来源/port分列 | 17–18、21 |
| Ruff | `ruff check .` exit0；show-files真实包含产品、全部正式测试、oracle/acceptance支撑及tools | 10、13 |
| mypy | strict，**11 source files**，exit0 | 11 |
| pip check | exit0 | 12 |
| build | PEP517隔离、本地wheelhouse构建sdist→wheel、支撑sdist→wheel及direct wheel均成功 | 05–07 |
| 产物审计 | 产品无tests/frozen/支撑/开发运行依赖；真实帮助资源、metadata/console入口、MIT原版权/NOTICE均保留；sdist重建wheel与direct wheel逐成员且完整SHA256一致 | 14，artifacts.json |
| 真正仓库外新venv | `C:\Users\PC\AppData\Local\Temp\RCm03 1105 中文 空格` 中两个新venv，分别只装产品wheel、产品+支撑wheel，均no-index/no-deps | 15–16、19–20 |
| 导入与依赖来源 | 两环境实际origin均在各自site-packages，sys.path/pth无Firstcode源码，无pytest/Ruff/mypy/build/Hatchling；真实importlib帮助资源可读 | 22–23 |
| 外部真实CLI/统一offline | console版本优先、长短帮助，installed offline4case全过；不是只审metadata/包头 | 24，boundaries.json |
| 六个未实现suite | oracle/runtime/protocol/live/terminal/install全部非零、逐项not-run和原因；unknown suite、空选择、缺解释器均非零 | 24 |
| 真资源故障 | 仅外部安装副本帮助资源临时改名；version仍0/help70/offline1，help+resource failed，其余两项passed；finally原路径原字节恢复后offline4重过 | 24 |
| KeyboardInterrupt | 已安装driver seam受控投递Python中断，真实自有子进程被kill并等待，suite exit1、后例not-run；未声称真实终端Ctrl+C验收 | 25，cancellation.json |
| 真实deadline | 真实sleep子进程等待15秒超时，case failed且已kill/join；不是注入TimeoutExpired假装实测 | 26，deadline.json |

Node和依赖仅复用了主代理明确授权的两个02公开工具子树，先复制到本票自有路径。没有读取/执行i03或其它私有cache，也没有复制来源缓存的home/.dao/runs/dist。Node字节hash和来源lock、复制依赖树指纹见 public-inputs.json；Windows长路径复制只作用于授权node_modules。来源Node24历史ENV未重跑、未改写，12项不扩大成来源全量215文件或产品Agent通过。

## 需修复的清理缺陷

`tests/support/ruocun_acceptance/driver.py` 的 `execute` 在已启动进程的 `communicate` 抛 `OSError` 时，直接写 failed/exit=null，然后无条件写 `cleanup.command_joined=true`，没有kill/wait/finally。

独立 `cancellation.py` 在已安装support wheel上投递一次受控等待异常，运行的是实际 `python -I -X utf8 -c 'import time; time.sleep(30)'` 自有子进程；不是用stub假装子进程。`execute` 返回时实测 `poll() is None`，却声明 command_joined。验证命令25因此真实exit1。复核脚本finally单独kill/wait了两个自有子进程，`reviewer_cleanup.owned_children_exited=true`。这里证明指定故障切点的代码缺陷，不声称本机自然发生OS管道错误。

普通KeyboardInterrupt的真实子进程清理本轮已观察成功，但候选报告将已取得的真实returncode写null；若修复取消证据，应保留真实终止码和独立取消状态。进一步的清理失败/再次中断仍不得伪装已清理。原候选README如实写未注入KeyboardInterrupt；本轮新增证据不能回填覆盖原raw。

## 原始证据与清理边界

commands.json是逐条实际argv/cwd/exit/env策略/扫描/清理回执；raw.zip保留完整工程stdout/stderr、仓库外case/资源故障、来源三轮wire/状态/清理及复核失败。raw-manifest.json逐成员绑定SHA256，并实际从zip内重读核验。artifacts.zip封存本轮真实产品/支撑成品，artifact-manifest.json绑定；source-inputs.json记录本轮维护源码字节。当前scan.json对维护源码/配置、所有新证据、wheel及ZIP展开成员、候选原03ZIP静默扫描，无命中；只报告有无。新版本化路径均不超过150字符。

封存阶段首次 `git diff --cached --check` 将本机新JSON的原始CRLF（已设-text保持字节）判成尾空白；原失败保留于复核过程记录。随后只为本证据目录JSON增加精确 `cr-at-eol` 规则并保留其它空白检查，没有重写JSON/ZIP/raw或产品源码，重新检查后通过。

工程命令均join；来源stall/deadline子进程退出、server关闭；被故障注入暴露的自有活进程已由复核器补做kill/wait。外部帮助资源已原字节恢复。自有venv/wheelhouse/来源cache/外部fixture及原始state保留；不自动清理任何私有磁盘cache、未合并worktree或系统设置。没有真实模型/付费调用，没有代填用户体验、公共Status/module-map/matrix/spec。
