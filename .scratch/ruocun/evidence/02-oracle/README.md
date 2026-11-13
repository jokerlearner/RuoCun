# 任务 02 — 冻结参考 oracle 证据

基点 `3933493`；交付前已合入集成分支 `3cd697b`。本票只建立参考对照和开发测试支持，产品入口、迁移实现及真实终端/模型验收均未开始。

## 实际结果

| 子案例 | source 实际结果 | port | 证据 |
| --- | --- | --- | --- |
| TEST-02.ORACLE-PLAN-READ | Node 22.23.4；2 请求；plan schema 排除 Write/Edit/Bash；TodoWrite 与 Read 回灌正确；exit 0 | not-run | [完整 raw](runs/node22-plan-read/) |
| TEST-02.ORACLE-READ-FIRST | 首次 Read 整批拒绝且未泄漏内容；补 TodoWrite + Read 后回灌正确；3 请求；exit 0 | not-run | [完整 raw](runs/node22-read-first/) |
| TEST-02.ORACLE-STALL | 本地 server 已收到第一请求后停止响应；deadline 停止 CLI 和子进程；server 关闭；source=canceled | not-run | [取消 raw](runs/node22-deadline/)、[进程树停止](runs/node22-deadline/tree-stop.json) |
| TEST-05.ORACLE-ENV-NODE24 | 同冻结 tree/lock/构建 CLI，工具链路正确但退出 3221226505，`UV_HANDLE_CLOSING` native assertion | not-run | [Node24 raw](runs/node24-read-first/)、[独立差分归因](fault-attribution.json) |

`Read` 独立字面预期是 `2\t口腔研究`；材料为 `alpha\n口腔研究\nomega\n`，offset=2、limit=1。计划结果是 `▶ 读取材料`。`ORACLE_COMPLETE` 是 fake assistant 脚本输入，仅用来判断脚本回合走到结束，不当作模型任务质量证据。

各 raw 目录包含原始 request body、原始 SSE bytes、完整已发送工具 schema、解码请求/响应、stdout/stderr、实际 argv/cwd/allowlist env、版本及关键源码/原生依赖/驱动 SHA-256。`sha256.json` 校验源运行的所有顶层 raw；`schemas.json` 是从实际第一请求抽取的派生材料。runtime 合成配置/数据库保留在命令指向的忽略缓存，正式证据不复制数据库。

唯一来源是 `dao-f17e189-7ac654a0dc06`，tree SHA-256 `7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c`，共 805 个成员。未读取活动 DAO 的凭据或配置，未修改活动 DAO。

## 预期出处与范围

本票亲读冻结源码及对应既有断言：

- `src/index.ts:318–414, 867–910, 1072, 1710–1753`：配置、headless、提示与一次性入口；`package.json:8–35` 的真实发布 CLI/构建入口。
- `src/tools/read_file.ts:46–57, 109–135` 与 `src/tools/read_file.test.ts:20–32`：1-based 行号及 offset/limit。
- `src/tools/todo_write.ts:50–75` 与 `src/tools/todo_write.test.ts:10–56`：plan capability、清单文本。
- `src/tools/registry.ts` 与 `registry.test.ts`：真实模型 schema 序列化和注册外部行为。
- `src/client/client.test.ts:48–72, 103–119`：流式工具参数分片、请求 tools/parallel_tool_calls。
- `src/agent/loop.ts:647–678` 与 `loop.test.ts:1208–1230, 1358–1380`：plan 模式发送及执行边界。
- `src/tools/execute.ts:129–142` 与 `execute.test.ts:318–371`：headless 首批 TodoWrite 门及补计划后继续。
- `src/env_snapshot.ts:40–56, 92–136`、`src/session/process_identity.ts`：公网探测拦截、WindowsPowerShell PATH 需求及清理范围。

[run_source_tests.py](run_source_tests.py) 在合成 HOME/temp 中运行上述直接相关的 6 个来源测试文件，实际 **190/190 通过**；[原始输出](source-tests.stdout.txt)和[命令/退出码](source-tests.json)完整保存。不是全量 215 文件来源测试通过。

TDD seam 沿用规格 T-02/T-N1：原 CLI、fake HTTP/SSE、真实工具/文件/进程、纯归因输入输出。未新增产品注入 API。

| 切片 | red | green |
| --- | --- | --- |
| 计划/Read 完整回合 | [缺少驱动模块](red-01.txt)；[第一次实跑发现 PATH 缺口](green-01-attempt.txt) | [首次成功](green-01.txt)；最终回归覆盖 schema 与结果 |
| headless 拒绝后重试 | [驱动未提供该场景](red-02.txt)；[随后确实暴露 Node24 退出错误](green-02-built.txt) | Node22 对照退出 0，最终回归通过 |
| deadline 清理 | [未提供 stall 场景](red-03.txt) | [进程树取消通过](green-03.txt)，最终回归又验证已收到请求 |
| 故障归因 | [缺少归因函数](red-04.txt) | [9 个独立规格字面预期](green-04.txt) |

合入 `3cd697b` 后，[最终 pytest](final-pytest.txt)为 **12 passed**，命令及版本见[复跑说明](../../../../tests/support/oracle/README.md)。Ruff 仅检查本票 Python 文件，结果另存 `quality.txt`；没有提前建立 pyproject 或产品开发包。

## 故障、未验证与清理

[fault-attribution.json](fault-attribution.json)保留 source/port 双侧状态。Node24 与 Node22 的差分足以定位到运行时/平台组合，归为 ENV；不声称已找出 libuv 内部根因。原 raw 不倒改：source 成功/port 未运行仍为 UNVERIFIED，失败 raw 也先保留 UNVERIFIED，再由该独立记录说明归因。

没有已证实的 SOURCE-DEFECT、PORT-REGRESSION 或已确认 INTENTIONAL-DELTA。分类表中的对应状态只是测试输入。付费模型调用 0：模型 transport 只允许本地 fake origin，公网 fetch 被记录并阻断；未做 live、Windows Terminal 缩放或用户体验验收。

[cleanup.json](cleanup.json)区分三件事：正常 CLI 已退出，deadline 的 CLI/子进程已停止且 server 关闭；本 worktree 的 `.venv`、源码/npm/Node22 缓存和合成 runtime 为复跑保留且被忽略；初次 pytest 的默认 Temp 目录 `C:\Users\PC\AppData\Local\Temp\pytest-of-PC\pytest-1612` 因自动审查拒绝删除而保留。自动审查原文为 `rejected: blocked by policy`，无更具体原因；未换工具绕过。目录保留不表示进程残留。没有删除本 worktree 或其它 worktree。

`collect_evidence.py` 原样复制并核验 raw。本目录及测试支持中的 `.gitattributes` 设置 `-text`，避免 autocrlf 改变 raw/绑定脚本。`manifest.sha256.json` 绑定本票代码、说明与正式证据。
