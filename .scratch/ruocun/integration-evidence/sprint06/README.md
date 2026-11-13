# A01 / 06 独立复核

审查者：`/root/sprint_review06`，未参与产品实现；本目录只保存独立测试、来源预期和复核证据，不修改公共任务状态或验收矩阵。

## 固定范围与环境

- 独立工作区：`D:\java supplement\Firstcode\RuoCun\.worktrees\sprint-review06`，分支 `codex/sprint-review06`。
- 起点：`092b1cccc8ea85c05d27acfbd45d4fc23acfbf51`；初始候选 `4b8a63d`，合入起点后的独立 HEAD `853ae4bb03f32fd3142a79f53cf7e1f3fcadab73`。
- 已读 AGENTS、CONTEXT、domain、issue-tracker、ADR-0003/0005/0006、spec R-07、06票、MM-439、WIRE-07/08、implementation、sprint-48h、项目 workflow 和 code-review 技能。工具没有 Skill 专用接口，直接读取技能文件；ADR-0006 的四槽约束下，独立审查槽自行分列规范与规格结论，未再占用额外代理槽。
- 来源只使用冻结 `dao-f17e189-7ac654a0dc06/source.zip`。`prepare_source.py` 从归档读取并逐 SHA256 校验 client/client.ts、responses.ts、sse.ts 和 config/profiles.ts 后，写入本工作区私有 `.cache/sprint06-source`。`source_contract_oracle.cjs` 用只读公开缓存 TypeScript 5.9.3 的 `transpileModule` 转换语法，运行原逻辑；不改来源模块。
- Windows / CPython 3.11.9 x64；pytest 8.4.2、Ruff 0.17.3、mypy 2.4.1、Hatchling 1.33.0、build 1.6.1；来源 Node 22.23.4。开发闭包依照 `requirements-dev-win311.lock` 的18包哈希从 `wb-i06/.cache/wheels` 只读安装。
- 每条执行均从 `tools/run.py` 的显式环境白名单启动，`--state .cache/sprint06`；HOME/AppData/TEMP/config/session均为合成目录，Python采用 `-I -X utf8`，未读取真实配置、调用真实模型或接触活动DAO。
- 旧 `.worktrees/codex-m06-r2` 的测试与回执只读作为线索；本目录所有标注亲跑的结果均在上述新工作区产生。

## 初始候选发现（历史失败；后续已修复复验）

| 问题 | 独立预期与实测 | 产品定位 |
| --- | --- | --- |
| fallback 超时构造越过非法值 | 冻结 client.ts:150 先 `AbortSignal.timeout(idleMs)`，无效值不得发送 fallback；Node22亲跑仅接受0..4294967295整数。初始候选7项无效值均错误发送fallback，4项有效/环境NaN控制通过。 | resilient.py `_nodeTimerMs` 与 fallback 分支；必须分开 stream timer 折算和 fallback 参数校验 |
| Retry-After数字解析 | 来源 `Number("0x0")`/`Number("0b0")`=0，429后应重试成功；原逻辑亲跑calls=2，port两项直接ApiError429。 | resilient.py `retryAfterMs` 的float解析 |
| 无可显示delta的工具碎片 | 仅id或arguments不设置来源yieldedAny，网络失败后应重试。原逻辑亲跑calls=2；port针对ConnectionResetError和StreamDisconnected共4项均calls=1空partial。带name的控制来源calls=1保留partial。 | resilient.py `_stateHadOutput` 与 client.py `runStreamAttempt` 的StreamDisconnected处理 |
| fallback错误继承旧429状态 | 流式429+RA0后，fallback200非法JSON，来源最终status缺失；port错误继承流式429，可能误导loop限流分类。 | resilient.py fallback catch中的e2_status继承 |

首轮规范审查未发现可单独成立的非工具规范硬违反；上述均为规格兼容性阻断。没有把代码气味猜测升格为失败。

## 亲跑记录

每项完整命令、cwd、退出码和扫描结果见 `raw/<label>/command.json`，输出见同目录 `stdout.bin` / `stderr.bin`。以下label均在前面加 `sprint06-`。

| label | 结果与范围 |
| --- | --- |
| venv / tools2 / install / support | 全部exit0；独立venv、18包锁定闭包、产品与支撑包非editable安装 |
| tools | exit1：首次误指不存在的根缓存路径，随后改用已核验公开缓存；环境准备失败，非产品失败 |
| initial-pytest | 301 passed / 3 deselected，46.21s；没有skip/xfail |
| initial-ruff / initial-mypy / initial-build / initial-offline | 全部exit0；mypy32文件；offline仅任务03的4个已实现入口，不能代表完整Agent |
| node-timeout / node-version / environment | exit0；保留Node22 uint32边界与实际工具版本 |
| negative-fallback | 首次5 failed，均多发非流式请求 |
| fallback-timeout-expanded | 7 failed / 4 passed；新增2^32、显式NaN及正边界控制 |
| prepare-source / source-contract / source-contract2 | exit0；校验归档并运行原来源逻辑，与port并列归因 |
| retry-boundaries | 4 failed；2种Retry-After、2种工具碎片 |
| fragment-signal | 4 failed / 3 deselected；补齐两种断流异常的同源分支 |
| fallback-status | 1 failed / 4 deselected；fallback错误status继承问题 |
| public-network | 3 passed；公开streamChat的DNS取消、fallback部分响应体后的取消/idle，helper退出、服务器和请求线程join、无迟到delta |
| wheel-venv | exit0；已准备真正仓库外纯产品venv，待修复候选构建后安装和执行独立wheel探针 |

初始301项已覆盖真实本机HTTP503/429、429无Retry-After、background529、增量先于结束、心跳不重置idle、部分内容取消、TLS握手取消/idle、fallback响应头超时、DNS helper取消/超时、localhost解析、代理CONNECT/TLS SNI/证书拒绝与重定向。上述通过不抵消独立新边界失败。

## 最终候选与独立结论

实现者候选 `f12f94995bcdba0f84cfedc824ce0fb0576feeda`（产品修复 `bb22239`），已包含最新集成 `092b1cc`；本审查分支合并点为 `2184ee9de75f63317c4f0b096c276a3a64975936`。只读逐项核对修复差异后，重新非editable安装产品，以下结果均由审查者亲跑。

| 最终label（均加sprint06-前缀） | 独立结果 |
| --- | --- |
| final-install | exit0，重新构建并强制安装当前工作树产品 |
| final-independent | **21 passed，1.46s**：11项fallback超时（7非法+4控制）、7项重试/工具碎片/错误状态、3项真实DNS取消及fallback响应体取消/idle；初始四类阻断均闭环 |
| final-pytest | **319 passed / 3 deselected，44.25s**，无skip/xfail；真实本机HTTP、DNS helper、TLS握手/证书/代理用例实际执行 |
| final-ruff / final-mypy / final-build / final-offline | 全部exit0；mypy32文件；offline4个工程入口，范围保持任务03子集 |
| final-pip-check | exit0，No broken requirements found |
| final-wheel-install / final-wheel-public | 均exit0；真正仓库外 `C:\Users\PC\AppData\Local\Temp\RuoCun 独立wheel sprint06` 的新venv只安装最终产品wheel；不含pytest、无产品运行依赖；从公开streamChat经真实localhost解析和本机HTTP完成503→非流式fallback→wheel-recovered，两个helper均exit0，server线程join、无迟到delta |

构建产物SHA256另存 `artifact-hashes.json`：wheel为 `b6b409c11b35cae4652a92115f4306a7cf24b659697d7eecaf7e5a803c3265e7`，sdist为 `d7885c8934aeefa7d6de4fd28202be7f9182bd6f74cedeab482df6b55ca916a7`。版本、构建和安装回执均指向本轮明确路径，无editable或PYTHONPATH借用。

**Standards：0项未解决硬违反。** 依项目规范核对职责、兼容入口、环境隔离、记录及只读来源边界；工具检查通过。不把代码气味推测作为失败。

**Spec：初始4类兼容性阻断已修复，最终0项未解决阻断。** 对06当前完整可实施范围的WIRE-07/08路径，独立复核通过，**可由主协调快进集成**。本审查者未修改06状态、公共对应表或矩阵；是否结题及这些记录由主协调处理。候选通过不等于整个WIRE族、Agent全量功能或最终用户体验通过。

四类问题的原失败日志和初始结果均保留，未替换为绿色输出。最终只有已修复后的新label记录通过。

最终提交前集成分支前进至 `f06e866019b35b17fb16af0a7e0826d793945588`，已通过合并点 `022d96c75d288bb5280d74bc4da236e2b5bce9ef` 纳入。该增量仅D22研究脚本/证据和工程记录，`src/`、`tests/`、`tools/`、metadata及开发锁相对完整复验点无差异，未修改06产品或测试。合并后 `sprint06-postmerge-independent` 再跑21项独立边界全部通过；既有五入口及wheel证据仍对应相同产品字节。

## 资源与限制

命令进程均已返回，无本审查者遗留的后台命令会话；实际网络测试只访问loopback，显式禁用系统代理或采用测试指定本机代理。自建worker、服务线程已join，受监督helper持有的Popen对象确认退出；最终wheel探针断言没有存活watchdog线程。保留本轮合成工作区、`.ruocun-acceptance/`工程入口产物、私有venv和缓存，不清理历史工作区。所有本轮回执 `sensitive_match=false`，保存/展示前已审查输入、参数和输出均为合成值或公开依赖。

未运行真实模型（0次）、完整来源CLI oracle、真实Windows Terminal/人工体验、其他平台或最终standalone。这些边界不因本票自动测试通过被填为accepted；CPython3.11私有socket/连接工厂和公开TLS测试证书的既有平台限制继续保留，standalone由任务80处理。
