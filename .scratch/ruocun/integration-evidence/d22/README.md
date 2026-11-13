# D22 候选历史材料独立静态复核

复核日期：2026-11-10。复核工作树 `.worktrees/codex-m22`，分支 `codex/review-d22`，起点 `e44363226a20d162ef602faa30c1ec5a06a79a23`。候选为 `319923eb4fbd64a0db43aabf143eeae8041f4cb3`，原工作树 `.worktrees/i22` 在复核时 Git clean；候选通过 cherry-pick `9a17fe3` 收录为历史调查材料。未改写候选原始归档、`manifest.json` 或 `e/post.json`。

## 范围和方法

- 只读检查任务票、报告、探针代码、原始结果、清理审计记录及 Git 状态。使用 PowerShell/.NET 读取既有文件和 ZIP，不运行沙箱实验、`pytest`、`run.py` 或 `audit.py`，不访问真实模型或凭据；未查询当前进程、Job 或桌面。以下清理结论来自当时留存证据，不是本次现场复查。
- 对照候选 `manifest.json` 逐项独立重算 34 个文件的长度和 SHA-256：34/34 一致。六组记录的 `raw.txt` 和 `bytes.zip` 均与各自 `run.json` 所载 SHA-256 一致；进一步读取 ZIP 内 39 个执行时源码文件并以 `source_sha256` 独立重算，39/39 一致。原 `e/post.json` 曾记录六组 CRC 检查通过；本轮未独立重算 ZIP CRC。
- 逐项读取冻结参考 `source.zip` 中 805 个成员并与冻结 manifest 的长度及 SHA-256 比较：805/805 一致。执行记录所列五个 D20 只读依赖的当前文件 SHA-256 均与当时登记值一致。这些文件哈希校验不等于完整来源行为已通过。
- `ntoken.py`、`probe.py`、`safe.ps1`、`test_token_psec.py`、`worker.py` 的当前字节与 a1 归档的执行时源码相符；`run.py`、`scan.ps1` 不同。候选报告说明二者在 a1 后分别加 `-B` 和补成功退出码；实际运行版本保留于 a1 归档，本轮未重新执行以推断变化效果。
- 已保存的扫描结果仅记录当时常见 token 模式和当时敏感环境值均未命中；这不是对所有秘密的穷尽证明，也不是本轮重新扫描真实用户环境。

## 核验结果与边界

- a1 原始结果记录 A 为 `failed`、B/C 为 `not-run`，共五次目标启动；组合 cmd 退出码为 0，实际受限及 AppContainer 状态均为真，原请求与实际各有两条 restricting SID。请求 `MandatoryPolicy=3`，挂起目标实际值为 1；严格比较还发现组和完整性等级变化，故按停止条件没有执行组合 Python。留存 `post.json` 将组差异限定为完整性标签替换，并记录用户、owner、restricting SID、privilege 等字段相等，`NEW_PROCESS_MIN` 位 `0x2` 未保留。
- 记录表明普通 Python 与受限 Python 分别退出 0 和 `0xC0000142`。受限 Python 未取得 worker 回执；组合 cmd 仅有 host 对挂起进程 token 的检查，不能推成组合 Python 或后代 worker 的实测。
- 五个 a1 目标的记录均显示 process 已 signaled、关闭 Job 前活动数为 0、关闭后按名称查无。历史 `post.json` 另记录八个原进程均不再运行、八个 Job 和私有 desktop 查无、workspace/tmp DACL 已恢复且与未修改同级目录一致。PSEC 服务端 teardown 没有独立查询，合成目录与被拒清理的 ignored 缓存仍保留；不能将 Git clean 当作全部磁盘或服务资源已清理。
- r2/g1/g2/g3/r3/a1 记录的退出码依次为 2/1/1/0/1/1；与候选报告中 collection 错误、两轮失败、一次通过、缺实现失败及 A 安全断言失败的记录一致。r1 重定向为空，外层没有可靠退出码，不计作 pytest 结果。

## 复核指引的证据覆盖风险

候选 README 将 `audit.py` 描述为只读复核，但该脚本尾部会直接写入 `e/post.json`，覆盖历史审计文件；它还依赖当时的本地 `run` 目录。**不要在原候选工作树或本历史证据目录执行该脚本。** 如未来确需复查，应先在隔离副本中让输出写入新的独立路径，保留原始 `e/post.json`，并遵守环境白名单与敏感数据审查；本次没有执行。

本记录支持把候选作为一次按停止规则结束的失败调查收录，**不证明 Windows 沙箱安全目标已达到，也不解锁产品 60/61/78 或完整发布门槛**。是否以及如何继续实验仍须遵守 D22 的既定限制和任务依赖；本复核不变更任务票或验收矩阵。
