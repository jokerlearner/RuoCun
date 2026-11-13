# 冻结 DAO oracle

这是任务 02 的开发期支持，不是 RuoCun 产品入口。任务 03 可从统一 `ruocun_acceptance oracle` 驱动调用 `driver.run_oracle(root, output, cache=..., node=...)`，无需重新实现 CLI 或 fake server。

任务03现将本目录作为独立 `ruocun-dev-support` 的 `oracle` 包安装，测试从已安装的 `oracle.driver` 导入，取消 `sys.path` / 动态源码导入。可在仓库外执行 `python -m oracle.driver --source-root <含冻结参考的只读根> ...`；默认参考根是显式 cwd，不再从安装包的 `__file__` 猜仓库。`ruocun_acceptance oracle` 目前诚实返回 not-run/非零，未将来源驱动结果登记为产品套件通过。

`output` 必须尚不存在。驱动只从指定冻结归档校验/恢复源码；每次校验全部 805 个源码文件并重新 tsc 构建，再调用原 package.json 声明的 `dist/index.js`。默认缓存位于本 worktree 的 `.worktrees/oracle`。`--install-deps` 显式执行锁文件 `npm ci`，允许下载依赖；普通运行不安装依赖。

已验证环境：Windows 11 build 26200、Python 3.11.9、pytest 9.2.0、Node 22.23.4。Node 24.15.0 的三请求回合有退出阶段 native assertion，不能把失败隐藏或据此断言 Python 回归。详细 raw 和归因见[本票证据](../../../.scratch/ruocun/evidence/02-oracle/README.md)。Python 产品最低版本不由本票决定。

已有 Node 22.23.4 可直接通过 `--node` 指定；使用专属缓存，避免混用 Node ABI。以下命令在当前 worktree 根执行，示例路径对应本票已准备好的隔离工具链：

```powershell
.venv/Scripts/python.exe tests/support/oracle/driver.py --node .worktrees/oracle/node22/node_modules/node/bin/node.exe --cache .worktrees/oracle-node22 --install-deps --output .worktrees/oracle/fresh-plan-read
.venv/Scripts/python.exe tests/support/oracle/driver.py --node .worktrees/oracle/node22/node_modules/node/bin/node.exe --cache .worktrees/oracle-node22 --scenario read-first --output .worktrees/oracle/fresh-read-first
.venv/Scripts/python.exe tests/support/oracle/driver.py --node .worktrees/oracle/node22/node_modules/node/bin/node.exe --cache .worktrees/oracle-node22 --scenario stall --timeout 10 --output .worktrees/oracle/fresh-deadline
```

`stall` 的预期是取消，CLI 退出 1，不是源行为通过。`plan-read` 要求两次真实模型 HTTP 请求，`read-first` 要求首次 Read 被 headless 计划门拒绝，补 TodoWrite + Read 后完成，总计三次请求。模型回答均是 fake SSE 输入；验证对象是实际请求、schema、Read 结果和进程退出，不是模型质量。

pytest 沿用已确认的 T-N1，不建立产品开发包：

```powershell
$env:RUOCUN_ORACLE_NODE=(Resolve-Path .worktrees/oracle/node22/node_modules/node/bin/node.exe).Path
$env:RUOCUN_ORACLE_CACHE=(Resolve-Path .worktrees/oracle-node22).Path
.venv/Scripts/python.exe -m pytest tests/test_source_oracle.py -o addopts=--strict-markers -q --basetemp .worktrees/oracle/pytest-rerun
```

两个环境变量仅选择 oracle 工具链；不包含真实账户。新工程默认以 oracle marker 分层这3个需材料的CLI测试，9个纯归因断言留在默认集合；以上显式命令恢复完整12项。未设置变量时使用 PATH 的 Node 和默认缓存，环境故障仍会使显式测试失败，不会自动跳过。`--basetemp` 请使用本 worktree 内未承载其它工作的目录，pytest 会清理该指定临时目录。

安装 Node/npm 的准备阶段也必须使用合成 HOME、空 user/global npmrc 和专属 npm cache；可复用 `driver.isolated_env()` 后通过 subprocess 执行显式 npm 命令。Node 本身不纳入 Git。若 `better-sqlite3` 的官方预构建下载超时，本票的[故障归因](../../../.scratch/ruocun/evidence/02-oracle/fault-attribution.json)保存了官方 URL 和 SHA-256；只可校验后放入专属 npm `_prebuilds` 缓存再重跑 `npm ci`，不修改锁文件或源码。

子进程环境采用 allowlist：合成 HOME/USERPROFILE/AppData、cwd、Git 配置、npm 配置、空 keychain、禁用更新/反思/Skills/MCP/Hooks/Web。profile 内唯一凭据是公开的 `oracle-not-a-real-key`。`network_guard.mjs` 只在 fetch 系统边界放行指定本地 origin 和内联 WASM data URL；来源自己的公网 HEAD 探测会被拦截并记录。这是测试 transport guard，未声称 OS 级网络/文件沙箱。

退出和取消证据分开记录。deadline 使用本次启动进程的 PID 执行 Windows `taskkill /T /F`，服务线程随之关闭；该证据仅覆盖 oracle 自身的 CLI/探测子进程，不替代产品任意后台任务的取消验收。输出保留，便于检查；缓存和数据库均在忽略目录，不会修改活动 DAO、真实用户配置或其它 worktree。

`classification` 取决于 source/port 两侧状态。source 通过、port 未运行时仍为 `UNVERIFIED`。确认 `SOURCE-DEFECT` 或 `INTENTIONAL-DELTA` 需要调用方提供独立证据决定，不能从相似错误文本自动推断；本票的分类表测试仅测试该规则，不代表已执行 Python 产品。
