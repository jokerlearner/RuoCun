# D19 修正的独立合并复核

候选：`0419c42c3593a6b56f78e9cad063c2a0c6e56600`。起点 integration `7b76694694fb3b9bc99e6a82560f825dbc3d4523`；先 `merge --ff-only integration/ruocun-migration`，再 `merge --quiet --no-ff impl/d19-sqlite-identity2`，合并点 `3a00c588fbd685ac4086cafd7d00e16ed64bd7c5`。本目录仅记录独立审查，不更新票据、map、矩阵或 CONTEXT。

指定长名工作树 `D:\java supplement\Firstcode\RuoCun\.worktrees\merger-d19-identity-validation` 实际成功 checkout/merge。候选本票 746 个 tracked 文件可读取；最长仓库相对路径 146 字符（在此工作树中完整绝对路径 224 字符）。三个普通文本 `.gitignore`、`README.md`、`requirements-dev.txt` 通过 `git hash-object --path` 的正常换行过滤对应 blob，其余 743 个文件严格比较原字节。[原归档复核](r2/archive-review.json)保留完整结果。

`h.zip` 1033 个成员逐个核对集合、大小、SHA-256、b1b15b5 Git tree/blob 原字节；内部原审计的 1029 个文件再次逐 SHA 核对，失败日志保留。`r.zip` 174 个成员逐大小/SHA 与 manifest 核验，独立读取身份 red `39784 != 29064`、1 failed/1 passed 和其中原合同 12/12。没有以旧 60404b8 或旧 12/12 作为本轮接受依据。

独立审查源码确认：覆盖仅位于本票 adapter；原 frozen probe/run_probe 字节不改。`DirectProcess` 保留 CreateProcess 返回的 handle，spawn 与 kill 均从同句柄读取 PID/创建时间；kill 中核对 spawn/ready/actual runtime 身份，TerminateProcess 后等待并核对退出码与存活状态，写 kill 回执后才返回。冻结 `crash_case` 在 kill 返回和 wait 之后才重开数据库/启动三次冷恢复。监督 Job 在 CreateProcess suspended 后绑定，再 ResumeThread；cleanup 等待 owned handles 和 Job active=0。

先逐原始回执独立复核候选 n 轮，后在本工作树新建本票专属 `.venv`（CPython 3.11.9、include-system-site-packages=false），安装固定 requirements，用 prepare.py 重取官方固定 ZIP 并再次独立核验 ZIP SHA3/SHA256 与 DLL SHA256。新 basetemp 为本票忽略目录 `.venv/q`，执行前断言不存在。完整[命令](r2/command.json)、[环境](r2/environment-review.json)、[pytest 日志](r2/pytest.txt)保留。

新 pytest：**2 passed in 10.94s**。actual SQLite **3.54.1**，source ID `2026-10-16 14:45:20 555e07ef33f69a0957d24d8e555b702464a131d6f1607f4c3c1e4551e8e6ca76`，DLL SHA-256 `4b59d3cded9dc1608544160f3b4b10ac974c6ac0d6ffc23064e5f4c8dbd05aea`。

独立 [fresh-round-review.json](r2/fresh-round-review.json) 直接读取八组 ready/runtime/kill/result：同 retained handle、spawn/ready/runtime PID+创建时间完全相同，wait=0（WAIT_OBJECT_0）、exit=1、worker_alive_after_wait=false；八个身份后验均已退出。21 份冷恢复回执分别与实际 runtime 身份对应，零恢复效果执行、零 pending events；35 份 runtime 身份唯一且均已退出，DLL/驱动实际文件摘要、compile options、VFS 与 harness 原字节全部核验。12/12 合同、34 owned、Job active=0；单独实际运行库测试产生的另一个身份也已退出。

新运行 181 个原始文件在 [fresh.zip](r2/fresh.zip)，[逐成员清单](r2/fresh-manifest.json)记录大小与 SHA，已对 ZIP 回读复验；忽略目录原文件同样保留。原候选 n 轮、h/r 归档及全部旧 evidence 不改。原 runtime 两份脚本（本工作树及主工作区）与全局 Python exe/python311.dll/sqlite3.dll/_sqlite3.pyd 的[前](r2/before.json)[后](r2/after.json)指纹一致；全新默认 Python 仍为 SQLite 3.45.1。

首次自写 verifier 只允许 README/requirements 正常换行差异，遗漏普通文本 .gitignore，因而在 pytest 前产生审计工具断言。原 [verify.py](verify.py)、[before.json](before.json)、[原错误回执](first-audit-trace.txt)和[解释](first-audit-failure.txt)保留；经主代理明确许可，仅扩展这三个普通文本的 Git clean 核验，另存 [verify2.py](verify2.py)并在 r2 保存后续全部结果。未修改候选脚本、产品或测试期望，所有 -text 资产继续严格字节比较。

本结论仅为合成 SQLite/进程恢复契约实验，非产品存储、wheel/standalone、真实模型、Windows Terminal、断电、真实 PID 复用或其它平台验收。未复现罕见 WAL-reset 竞争；官方版本/构建来源是修复依据，普通压力通过不作为修复证明。没有 push、清理 worktree 或改全局 Git/Windows 设置。
