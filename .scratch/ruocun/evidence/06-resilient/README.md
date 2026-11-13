# 任务 06 未完成检查点（Codex 接续）

本记录是开发检查点，**不是任务完成或可合并结题声明**。任务 06 仍为 claimed；
DNS 阶段取消尚不满足要求，默认 HTTPS、代理及中断资源边界尚需独立复核。

## 接续及现状

- 分支 `impl/06-resilient`，worktree `.worktrees/wb-i06`，接续前 HEAD `588c1f9`。
- 接续前已存在 `client.py` 的未提交修改及 `resilient.py`、两个测试文件；未丢弃或覆盖原成果。
- 预期依据冻结快照 `dao-f17e189-7ac654a0dc06` 中 `src/client/client.ts`、`client.test.ts`，以及规格 WIRE-07/08 和 ADR-0005；冻结源码仅从归档读取。
- 产品客户端增加可选增量回调，保留 `streamChat` 原签名；默认 HTTP 按到达顺序处理字节，HTTPError 保留状态与响应头，原生 RUOCUN 环境变量优先。重试、部分内容保留、限定次数及非流式兜底在新 `streamChatResilient` 中组织。
- 默认 HTTP 使用计时线程及本次连接持有的 socket 尝试中断读写；测试涉及的 Windows 3.11 中，单独 `shutdown` 未唤醒被 `socket.makefile()` 持有的阻塞读取，当前尝试底层关闭。该实现依赖 CPython 3.11 私有 socket 细节，必须审查 SSL、句柄竞争、状态与资源生命周期；**不得直接按已验证的最终跨平台方案使用**。自定义 transport 必须自行处理可中断性。

## 验证环境与范围

- Windows、CPython 3.11.9；`.venv` 内已安装工作树版本，测试使用 `-I -X utf8`。
- `tools/run.py` 为每次子进程提供显式环境白名单及合成 HOME、配置和临时目录；不读取真实账户或调用真实模型。测试均为合成传输或本机 127.0.0.1 临时 HTTP 服务，服务和工作线程由测试 finally 关闭并 join。
- 每条命令具有独立 label，原始输出保留在该 worktree `.cache/boot/raw/<label>/`，runner 的敏感值扫描结果均为 `scan_hit=false`。生成的 `.ruocun-acceptance/`、缓存、虚拟环境保留，未纳入提交。
- 检查点全量 `codex06-checkpoint-pytest`：**282 passed、3 deselected、1 strict xfailed**，exit 0；其中 xfail 是已复现的 DNS 取消缺口，绝不等同全部通过。
- `codex06-checkpoint-ruff`、`codex06-checkpoint-mypy`（31 个文件）、`codex06-checkpoint-build`、`codex06-checkpoint-offline` 分别 exit 0；offline 仅四个任务 03 入口案例，不能代表完整 Agent 验收。
- 检查点实现提交 `d31ff33` 后，合入当时集成 tip `0e0bde1`，合并提交 `d9f2295`；`codex06-postmerge-checkpoint` 定向回归 17 passed / 1 xfailed，exit 0，scan_hit=false。合并引入的材料为项目记录及 D22 实验记录，不代表任务 06 通过。
- 真实模型调用 0；真实 Windows Terminal、人工体验、HTTPS/代理真实端到端、全量冻结来源 oracle 未运行。

## 逐项实验与红绿

| 子路径 | red label / 结果 | green label / 结果 |
| --- | --- | --- |
| 本机 HTTP 503 前产出重试 | `codex06-red-http`，exit 1，真实 HTTPError 未进入重试 | `codex06-green-http`，exit 0 |
| 环境变量优先级 | `codex06-red-env`，exit 1 | `codex06-green-env`，exit 0 |
| 已取消时不开始传输 | `codex06-red-precancel`，exit 1 | `codex06-green-precancel`，exit 0 |
| 响应结束前处理首帧 | `codex06-red-stream`，exit 1 | `codex06-green-stream`，exit 0 |
| 增量回调先于流结束 | `codex06-red-delta`，exit 1 | `codex06-green-delta`，exit 0 |
| 有产出后连接停滞中断 | `codex06-red-idle-stall`，exit 1；`codex06-green-idle-stall` 首次修复仍失败 | `codex06-debug-watch4` 验证底层关闭可以唤醒；`codex06-checkpoint-pytest` 对应测试通过 |
| 非流式兜底响应头停滞中断 | `codex06-red-fallback-stall`，exit 1 | `codex06-green-fallback-stall`，exit 0 |
| 本地化原生连接重置 | `codex06-red-native-net`，exit 1 | `codex06-green-native-net`，exit 0 |

`codex06-pytest-b` 暴露一次 idle 竞态导致部分内容丢失，277 passed / 1 failed / 3 deselected；修正后 `codex06-pytest-c` 278 passed / 3 deselected。不得抹去首轮失败。

## 未完成及下一步

1. `tests/test_resilient_http.py::test_cancel_during_dns_resolution_returns_without_waiting_for_dns` 通过合成阻塞解析复现取消不能及时返回；`codex06-dns-e` 是 **1 xfailed**，不是通过。测试释放解析器并 join 自己启动的线程。默认 240 秒 idle 在同一解析阶段也缺少中断保证。
2. 评估独立、可终止且必须 wait 的 DNS helper 时，不能全局替换 `socket.getaddrinfo`：需扩展每个 HTTP/HTTPS 连接的受控解析及连接生命周期，代理时解析实际代理、HTTPS 保留原主机名和隧道语义、地址按原顺序尝试；同时明确隔离环境、子进程停止和 Windows standalone 打包。该方案尚未实现或验证。
3. 对 socket 私有关闭补齐 Windows + TLS + 代理 + 资源竞争独立验证，并确认不复用已关闭的句柄；对 DNS/连接/响应体/fallback/取消路径分别验证未遗留 worker、无迟到回调。
4. 补齐独立来源对照、可运行产品路径及既有五项入口的最终回归；合并最新集成分支后另行交独立 merger。公共任务状态、模块对应表和验收矩阵由主代理维护；本检查点不能关闭任务或母案例族。

## DNS helper 接续进展（仍待独立复核）

- 合成 helper 与本机代理/TLS/重定向原型、原始回执见 [prototype/README.md](prototype/README.md)，原型提交 `572a8a7`。其通过不等同产品通过。
- 已在候选实现中为命名主机引入请求私有解析 helper：显式白名单环境、stdin JSON、进程对象级 terminate/communicate/wait；不修改全局 `getaddrinfo`。数字 IP 用 `AI_NUMERICHOST`。冻结程序不假装已支持该 helper，任务 80 仍须适配。
- 原来的 strict xfail 已替换为产品路径真实受控 helper 测试：`codex06-red-supervised-dns` exit 1，`codex06-green-supervised-dns` exit 0；`codex06-dns-real-timeout` 的三个定向测试 exit 0，涵盖取消时 helper 已退出、流与 fallback 阻塞均超时退出、localhost 正常解析及进程结束；模拟的敏感父环境值不进入 helper。
- `codex06-product-proxy-tls-redirect` 首轮重定向测试失败，本机 localhost 首个 IPv6 地址连接耗尽 3 秒；改用只返回本机 IPv4 的合成解析器隔离之后，`codex06-product-proxy-tls-redirect2` 两个产品路径用例 exit 0，覆盖 302 POST→GET、两次解析、显式本机代理 CONNECT、TLS SNI、错误主机名及不信任证书拒绝。TLS 测试依赖 CPython 安装携带的公开 localhost 测试证书；若不存在会显式 skip，不视为验证。
- 本轮曾发生合成测试经宿主系统代理返回 502 的事件；详细原因、范围、补救和原始回执见 [proxy-test-incident.md](proxy-test-incident.md)。之后测试显式禁用系统代理或指定本机代理；未使用真实模型或真实凭据。
- Windows socket 私有关闭、CPython 私有连接工厂、其他解释器和系统、真实企业代理、冻结独立程序仍有验证和适配边界。任务 06 在独立复核与其余验收项完成前继续 claimed。

## 合并集成 tip 后的实现者自验

- 合并集成 `0218f2a`（仅增加项目记录）后：`codex06-final-pytest` **289 passed / 3 deselected，未出现 skip/xfail**；本机 CPython 3.11.9 自带 `Lib/test/certdata/keycert.pem`，本机 TLS/CONNECT 证书校验和 SNI 用例确实执行。其他安装缺少该公开测试 fixture 时会显式 skip，且此证书有有效期，不能据此承诺长期或跨平台通过。
- 同轮 `codex06-final-ruff`、`codex06-final-mypy`（32 个产品/支撑文件）、`codex06-final-build`、`codex06-final-offline` 均 exit 0、scan_hit=false；offline 仍仅任务 03 的四个入口。完整来源 oracle、真实模型和最终 Windows Terminal 人工体验未运行。
- `codex06-wheel-venv` / `codex06-wheel-install` / `codex06-wheel-only` 均 exit 0、scan_hit=false：在仓库外独立临时目录创建干净 venv，仅安装新建产品 wheel，以本机合成 HTTP/localhost 测试已安装包及其 DNS helper；验证 helper 进程退出、服务器停止，未访问真实网络。脚本见 [wheel_probe.py](wheel_probe.py)，临时 venv 和测试记录保留。
- `codex06-responses-fallback` 验证注入式 Responses 非流式兜底的输出、工具、reasoning item 与 usage；这不是真实模型或全量 Responses 兼容验收。
- 上述为实现者证据，不替代独立 merger；必须仍保留测试隔离事件、CPython 私有接口、单机合成代理/TLS、其他平台与任务 80 standalone 限制。

## 独立复核回修：公开入口、TLS 与 idle 数值

- 接线：`client.streamChat` 保留旧有参数及 `StreamResult` 的正常/partial 字段，包括 `request_body`；新增可选 `context` 传递增量和取消。它调用韧性编排，韧性编排只调用 `runStreamAttempt`，无递归。不可恢复错误仍抛具体错误，新增允许重试的情况按冻结行为执行。`codex06-red-public-retry` 失败后 `codex06-green-public-retry` 的本机 503 和带 Retry-After 的 429 均通过；`codex06-public-idle-cancel-responses` 覆盖公开入口的本机 idle、取消和 Responses 部分结果。
- 合并帧取消：`codex06-red-coalesced-cancel` 复现同一字节块中第一帧回调取消后仍处理第二帧；改为逐 payload 检查取消，`codex06-green-coalesced-cancel` 通过。已输出第一帧保留、后续帧不投递。
- TLS：真实本机服务先读取 ClientHello 再停住；`codex06-red-tls-handshake` 中取消与 idle 两项均失败。修复将已转移的 SSL socket 登记后再握手；`codex06-public-tls-final` 覆盖公开入口握手取消/idle，以及可信证书、错误主机名、不信任证书、本机代理 CONNECT 和 SNI。未关闭证书校验，测试服务/工作线程 join。
- idle 数值：隔离 Node 22.23.4 的 `codex06-node22-idle-oracle`、Node 24 的 `codex06-node-idle-oracle` 及脚本 `prototype/idle_oracle.js` 已保留；源 `Number(value)||240000` 中空/零/NaN 回默认、负数和 ±Infinity 保留，Node 的 timer 按 1ms 等实际规则调度。`codex06-red-node-numbers` 后 `codex06-green-node-numbers` 9 项通过；错误文案使用原值。不是把危险值默认为 240 秒。
- `codex06-public-old-regression` 首次回归 55 passed / 1 failed：05 局部测试旧断言对 Responses 已产出后缺 completed 要求抛错。冻结 `responses.ts:85` 抛 `Responses stream closed unexpectedly`，完整 `client.ts:141,346-347` 将该错误归为可恢复且已产出时返回部分、不重放。依完整源路径修改该条测试后 `codex06-public-old-regression2` 为 **56 passed**。这仅是该子场景，不能代表全部 Responses 情形通过。
- 以上运行均通过 `tools/run.py` 白名单；合成服务器显式禁用系统代理或使用本机代理，scan_hit=false。真实模型 0、完整来源 oracle 与最终人工体验未验；前述系统代理事件、Windows socket 私有实现及 standalone 限制继续有效。
- 合入用户“完成06后停止”记录所在集成 tip `01e6dab`（merge `a45328e`）后，`codex06-r2-final-pytest` 为 **301 passed / 3 deselected**、无 skip/xfail；`codex06-r2-final-ruff`、`mypy`、`build`、`offline` 全部 exit 0，mypy 32 文件，runner 均 scan_hit=false。仓库外 venv 重新安装此轮 wheel，`codex06-r2-final-wheel-only` 从公开 `streamChat` 路径完成本机合成 HTTP 与 helper 退出验证，exit 0、scan_hit=false。
