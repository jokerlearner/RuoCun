# Task03 修复轮独立复核

**候选 `90efe4f7a271c8c39f9fc6d35479bdeed6813028` 在本票既定启动/工程子路径的增量独立复核通过。** 初轮 `25c56bc04428f9c5147a513471c292b95473840e` 的失败、源码期望和raw保持原字节；本报告仅更新修复候选的结论，不改写第一次失败。完整Agent、聊天/TUI/SQLite、正式发行及最终终端体验仍不在本次通过范围，也未启动04。

复核仍位于独立 `.worktrees/m03` / `merge/03-boot`。由clean `25c56bc` no-ff 合入精确修复候选，merge为 `e11a20d9cc004c8d2fc02170dd112fa21f3ae6b9`；正式集成ref仍为 `46c8243650333e61325346d367068cad0c93ebfa`。未修改公共Status、module-map、验收矩阵或spec，未私改产品实现。

## 改动与独立边界验证

已逐行读取新 `driver.py`、新增 `test_acceptance_process.py` 和实现者r2 README/inputs/result/原失败说明。修复用同一Popen拥有的进程/句柄确认退出并关闭管道，实际exit和逻辑130分开，无法确认退出则 `cleanup-failed` 并停止后例；退出确认阶段的中断不能覆盖成success。错误诊断保留操作/异常类型/数字代码，不复制任意异常文本。

除候选新增4项测试外，另用本目录 `faults.py` 在**仓库外新空、只装最终两个wheel的环境**独立执行四个边界。其受控Python异常发生在真实Popen/communicate/wait/poll边界，所有子进程是真实自有Python进程；不是空stub，也没有声称真实内核损坏、系统拒绝终止或真实终端Ctrl+C。

| 独立边界 | 实际结果 |
| --- | --- |
| communicate OSError | execute返回时实际child已退出，真实exit=1，case failed/逻辑1，joined及streams_closed=true；原“活进程却记已结束”复现转绿 |
| communicate KeyboardInterrupt | suite逻辑130；实际child退出码单独保留，case cancelled，其余3项not-run，joined/流关闭均true |
| wait/poll均无法观测退出 | case/suite均cleanup-failed、逻辑1、exit=null、joined=false；保留同一拥有对象身份及wait/poll错误，后3项not-run；外层复核器独立回收实际child |
| 退出确认阶段KeyboardInterrupt | 真CLI已完成且child实际exit0，仍cancelled/逻辑130；后例not-run，真实exit确认和流关闭为true，不能把中断吞成成功 |

逐项原始报告和独立最终清理回执见 `faults.json` 与 raw.zip。4个自有child均由复核器finally再次确认退出和管道关闭，不按裸PID重新获取/杀进程。

## 增量工程与独立安装

13条工程命令均通过既有 `tools/run.py` 从明确allowlist、合成HOME/AppData/TEMP、NUL pip配置启动，无PYTHONPATH/账户变量，不重试D21被拒helper；本轮没有策略拒绝。

- 默认pytest：**29 passed / 3 deselected，2.86s**，pytest8.4.2/CPython3.11.9 Windows x64，新增4个真实child故障回归均运行。
- `ruff check .`、strict `mypy` **11 source files**、`pip check` 均exit0。
- 标准PEP517隔离产品sdist→wheel、支撑sdist→wheel均exit0，仅从原已验证本地wheelhouse安装后端闭包。
- 真正仓库外中文空格新venv：`C:\Users\PC\AppData\Local\Temp\RCm03 1105 中文 空格\support-r2`，只用no-index/no-deps安装本轮产品和支撑wheel。实际origin均为该venv/site-packages，sys.path/pth无Firstcode源码，无pytest/Ruff/mypy/build/Hatchling。真实 `python -m ruocun_acceptance offline` **4 cases passed**，逐case真实exit和流关闭正确，suite逻辑0。
- 产品wheel仍为 `feeb2e2d77d3aaeede79681536f90a8955faef8fbc68d054928626ab84e99a8c`；新支撑wheel为 `58cf0ef5decc4f9df4ee57a562e0ec2e84ea57ff91382e172bf748b69ed11e21`，与实现者r2最终wheel一致。独立支撑wheel仅driver.py及RECORD变化，oracle/资源/许可/metadata其余成员字节均一致，无新运行依赖。

audit.json核对上一轮31个未改维护输入、18个开发wheel字节、原独立raw/artifact归档hash均不变；产品CLI、版本/帮助资源、开发锁、构建配置、来源oracle及其测试输入均未改变。产品sdist与本复核器上一轮独立产物字节相同，支撑sdist仅driver成员变化，见sdist-delta.json。实际本轮产物hash记录于audit.json与artifact-manifest.json，不拿他人的sdist hash替代本轮值。

因此沿用上一轮本复核器实际来源oracle **12 passed / 39.66s**、版本优先/长短帮助、纯产品环境、六suite非零not-run、unknown/空选择/缺解释器、真实缺资源/恢复后的offline4、15秒deadline证据，没有为无关文档或无变化输入重跑长链。Node24历史ENV仍原样分列。

## 封存与限制

commands.json记录本轮13条实际argv/cwd/exit/allowlist与清理回执；raw.zip封存工程stdout/stderr、新默认测试真实fault receipts、仓库外四边界及offline案例，raw-manifest.json逐成员hash后实际从ZIP内读回验证。artifacts.zip及artifact-manifest.json保存本轮四个真实成品；result.json汇总本轮范围。所有新版本化路径不超过150字符。

scan.json对维护源码/配置、开发wheel、本轮产物/证据及ZIP/tar展开成员、原候选与两轮独立raw静默扫描当前敏感环境值，只报告有无，无命中；不记录变量名/值。扫描控制器不启动测试/构建子进程。所有记录工程命令已join，测试及复核持有的自有子进程均退出/流关闭；无法观测案例的候选报告仍诚实保留cleanup-failed，实际资源由外层持有对象清理。自有venv/wheelhouse/外部fixture/state保留，不清理私有缓存或未合并worktree。

本结论只覆盖ENT-01/TEST-07在任务03定义的两个完成母子路径，由主代理收录公共完成/接续记录。没有付费模型调用、人工终端代验、业务runner或正式发布通过声明。
