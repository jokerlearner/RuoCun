# N1 共享接缝独审

## N0 公共状态收口

只读核对固定 `de82088217b72d5196d866c8bc81dc0b00471f48`。08 resolved 对应实际 r2 全量 687 passed／3 deselected、默认 mypy 78、Ruff／offline／build、固定 70c7464／r2 与 90 成员安装及独审；检查现有 raw／command 及新增关键链接，未重跑产品。原 r1 的 685 passed／1 failed、exit=1 及首轮产物绑定保留，真实 SSE 通知红→绿也保留。02–85 的有效 82 票中实际 resolved 7 票；01 测试入口确认不计入该分母。09／11／34 仅领取，未推定母案例族或人工体验完成。

指出 N0 集成首段“后继未解锁”和计划“本次未改任务状态”的两处旧时态，root 在 19106d7 已明确其为历史初始状态，未删除旧证据。

## 兼容类型

固定 `9dc976086acffff5cecfaf5c2c423d2c0b0e80bd` 相对 de82088 仅追加 Tool／ToolContext 的 optional／default 字段及 ChoicePrompt Protocol。字段均位于原 dataclass 既有字段之后，旧位置／关键字构造不变，默认 None／False，无新运行分支。setMode、askChoice（含 multi=False）、searchTools 与冻结类型一致；checkPermissions 保留 deny／ask／None 的收紧结果，shouldDefer 默认 False。纯类型追加未增测试或重建环境，后续消费候选单独核实实际行为。

## Registry／原生 ToolSearch

固定起点 9dc9760，候选 `19106d791ed2fd2ed82f776effea29a15cd3c021`，差异非空，本树干净后合入。独立读取冻结 registry.ts／registry.test.ts、tool_search.ts，对照实现及原断言。

- predicate、英文回退、注册顺序、未激活的 80 个 UTF-16 code unit 短描述／空 schema、hideUnactivatedDeferred 过滤及激活后的完整参数符合来源。
- 搜索按工具名／描述子串匹配，已激活不重复命中。真实 API 隐藏不增加合法参数 dispatch 的激活硬门；仅真实 schema 校验失败时引导先 ToolSearch，已激活后走普通错误。
- MCP 仅登记来源前五个注册名的可见性状态，无外部连接／发现／搜索产品路径；本批组合根仅供原生工具，不推定 53 整票通过。
- ToolSearch query 按来源 z.string().min(1) 拒绝空值，通用 minLength／maxLength 按 JS UTF-16 计数。原 Skill.name 也声明 minLength=1，冻结 skill.ts:24 同为 min(1)，新校验会同时兑现它；已提醒 root 修正“只有新 query 消费”的记录，不视为产品回归，未扩矩阵。

既有 `tests/test_registry_deferred.py` 与 `tests/test_mvp_registry.py` 原断言独立 **24 passed in 0.28s**，见 `raw/n1-review-registry-source-01`。没有重复构建／全量或改变断言。

Node v24.15.0 仅求值冻结 ToolSearch 两段已审字符串字面量表达式，与产品资源逐字比较，全部相同；没有执行冻结模块或写参考树。指纹见 `raw/n1-review-toolsearch-strings-01`：

| 来源／资源 | SHA256 |
| --- | --- |
| 冻结 tool_search.ts | 0932d7a6883228c0c28b7c943c1cd6d0d0644d2e40fabcf02084f3cc87a909e5 |
| 中文 description | 73587936861aa1ed55e75b7e2cc9dded32570867945db63bbbf8edce3967479c |
| 英文 description | 9a53a27be5e08342b7a9c80c528b564f7f861406deff426562f9a9aa7343b67c |

规格／工程规范剩余阻断 0，可供 root 与两条实现线消费。此处只有已固定共享前置接缝结论；Conversation 队列、权限规则主体及 scheduler 尚待候选，不写成 N1 整票或普通 CLI 已通过。

外层白名单启动器／tools/run.py、私有 Python 3.11 venv、合成 HOME／config／TEMP；两组命令 joined、scan_hit=false，模型 API 0。源码定向显式指定本树 src，不冒充最终固定 wheel／安装或人工体验。

## Conversation 已确认输入队列

固定初候选 `1c1e666b03c78d53fada79d5406d18956a43eb6a`，敏感载荷回修 `e28cfb5f120eff939a5daed7fe05e3532927a727`。只改变既有 Conversation 的 queue／consume／discard／state 端口及序列化锁，不扩唯一 StoragePort、Checkpoint schema／版本或数据库。

同一 async 锁覆盖每个公有 checkpoint 方法的 ledger／revision 读取、worker 提交等待、确认及内存 ack／投影交换。queue 返回身份在确认后，重复文本仍独立 input_id／seq；consume 只按已确认队首、重复消费返回 False；用户投影与 consumed 同 checkpoint，拒绝只 discarded，暂停的 discarded 与 paused 同 checkpoint。checkpoint 提交异常沿旧接缝 blocked，未确认不换账本／revision；接纳前校验拒绝不伪称数据库未决。open 尚未发布对象的私有提交不与公有调用并发；running 恢复 paused、旧 foreground-only／新进程 closed 恢复 idle，并恢复 plan／normal。原未决工具仍禁止盲重放，完整图片配对／投递不另开恢复路径。

**关键调用约束**：此锁不保护 loop 在外部直接修改 Session。consume／replace_context 必须只由同一 scheduler 的完整 assistant／tool 安全边界调用，或 pause 后等待真正 settled；当前飞行请求不得由第二任务异步交换投影。否则仅检查“当前工具已配对”不能防止 worker 等待期间的晚 append 被旧候选覆盖。root 已接受，并写入 e28 接缝记录／consume 方法说明；普通入口最终复审仍须核对，不能由本模块通过推定接线已安全。

**发现并关闭：排队载荷脱敏改变待执行指令。** 初候选 queue 把 payload 经 _safe 脱敏，consume 默认又把该 payload 用作模型指令；若包含当前 secret，会从原文变成占位文本。root 按 D09／ADR13 在任何 _input／commit／ack 前比较 _safe(content) 与原文，不可完整保存则明确拒绝接纳，调用方保留草稿；不确认“已保存”或执行替代文。不使用 `[REDACTED]` 字面量启发式，不引入敏感 RAM 映射／密钥库／新 schema；未发布候选无真实用户数据迁移承诺，正式路径恢复读取可信、未改字节的已确认 payload。

原 `test_advanced_conversation.py` 同一真实账本 fixture 与三项原图片存储确认独立 **4 passed in 4.98s**。回修仅复跑该原账本 fixture，含新增的拒绝前后 checkpoint 完全相等断言，独立 **1 passed in 2.64s**。root 的明确缺 queue_user red、首个错误文件路径 exit4／零收集 ENV、敏感载荷 red→green 均保留；本审未扩故障矩阵、未重跑全量。回执为 `raw/n1-review-queue-source-01` 和 `raw/n1-review-queue-redaction-01`。

队列端口剩余阻断 0，可供模块消费。真实 Hook 尚未接产品，测试的 rejected=True 仅证明该端口不追加历史；普通入口的草稿保留、命令暂停／settled、boundary 位置另审。

## SessionScheduler A

固定来源候选 `95a304204f786768865a6b07b3c9160370660b0c`，close 回修 `f8e7be16f6703729d73a704fc0bc40b5171e5e40`，类型回修 `a19cc3f3882a8978b5605e282bcf39fe677d55f4`。产品只新增 agent/session_scheduler.py，使用注入队列端口，没有自行创建存储或消费未审 Conversation。独立读取冻结 session_scheduler.ts 及当前来源／必要适配断言。

FIFO 按 seq 在 boundary 消费，单泵 _active／_scheduled 防并发模型轮；每个 run 独立 Event，generation 使旧 delta 可被组合根识别。pause／reset／close 在等待 _control／discard 确认前先失效 generation、设置当前 Event；不会 Task.cancel 可信运行。close 等旧 run 自然 settled 后清订阅，closed 后不再 pump；保存失败没有接纳回执。恢复保留 queued，原 running 回 paused；原 closed 的新 scheduler 可回 idle。_wait_until 通过 Future 通知等待，不轮询。

**发现并关闭：close 被迟到 queue 失败改回 paused。** 初候选 submit 持 _control 等待 queue；close 先设置 closed／失效 generation 并等待同锁；queue 随后抛错时，submit 异常分支无条件 paused／再次失效 generation，close 后续确认因 generation 已变不再设置 closed，最终可能重新 submit／pump。作者只在已 closed 时禁止该覆盖，保留 lastError／原异常／无 ack；复用原 queue-save-failure fixture 的受控 Event 交错 red→green，未新增测试项或矩阵。本审静态发现后独立复该原受影响用例 **1 passed in 0.13s**。

初候选原七项独立 **7 passed in 0.11s**。本私有既有纯 Python mypy 实际执行初次报 comparison-overlap（跨 await 的可变状态被静态窄化），这是产品类型错误，不是原 compiled mypy ENV。作者沿冻结来源用 status().state 读取 await 后实时状态，不 ignore／降规则。独立同一 mypy 复跑 **Success: no issues found in 1 source file**。真实失败和绿色回执均保留于 `raw/n1-review-scheduler-{source,mypy}-01`、`raw/n1-review-scheduler-{close,mypy}-02`；未重复已过七项或重建环境。

Scheduler A 剩余模块规格／工程阻断 0，可供 root 消费。本结论只覆盖前台切片；11 尚需普通入口、迟到 callback／requestid 隔离及组合端口复审，后台 Runtime／等待句柄／事件投递／keepAlive／后台解绑产品未迁移，不能填 15–17 或整票 11 已完成。全部新回执继续沿同一白名单／合成环境，joined、scan_hit=false、真实模型 API 0。
