# N1共享接缝

Status: implementing / no-final-exit

08已在de82088收口，09/11/34分别claimed。root唯一拥有Tool/Registry/loop/runtime/Conversation；两实现线不共写这些文件。

## 原生延迟工具前置

类型9dc9760为兼容追加，旧位置/关键字构造不变，独立静态核对已通过。Registry按冻结registry.ts/test.ts补predicate/英文描述、deferred短描述/空schema、真实API隐藏、按名称/描述搜索激活与已激活不重搜；非法参数提示先ToolSearch，合法隐藏工具仍沿源允许派发。保留MCP最初五名可见性登记以供tools_for_mode消费；没有MCP连接/发现/外部工具产品路径。

ToolSearch中英描述从冻结tool_search.ts字面量提取；本批组合根仅供应原生deferred搜索。新增schema minLength/maxLength按JS UTF-16计数，当前query与既有Skill.name消费minLength，两者冻结源码均为min(1)，空值校验同时补齐来源。原权限/工具族或53整票不因这个前置子路径完成。

实际源码定向：n1-registry-source-red退出1→green23 passed；query空值按原z.string().min(1)确认red退出1→registry及原用例24 passed in0.15s；4文件mypy、Ruff通过。仅源码定向，不是最终wheel/实际CLI接线通过。命令由外层白名单启动器和tools/run.py运行，合成HOME/config/temp，scan_hit=false；原始回执见raw。待独审与普通入口接线，无模型API调用。

## 已确认排队输入

Conversation新增`queued_inputs/queue_user/consume_user/discard_queued/set_foreground_state`，scheduler通过闭包消费。每个重复文本仍有独立input_id/seq，queue确认后才返回身份，consume在同一checkpoint确认消息投影与consumed；Hook拒绝只置discarded。pause的discarded与paused同事务。沿用AcceptedInput和Checkpoint.background_state，无新DB/schema。恢复旧foreground-only为idle、running为paused、closed新进程为idle，并恢复normal/plan。

公有checkpoint方法的同一async锁覆盖读取ledger/revision→提交等待→确认与投影交换；`_commit`仅供锁内或尚未发布的open恢复调用。意图/结果仍复用唯一StorageWorker，不另建日志，也不自动重放未知结果。失败保持原可确认现场，blocked拒绝后续写入。

调用约束：consume/replace_context只在同一scheduler安全边界或pause→settled后执行；锁不宣称阻止任意外部代码直接改Session。普通改变历史的命令须先等旧run真正settled，查询不无故暂停。

独审另发现：旧候选queue保存脱敏payload后默认消费会改掉原指令字节。按ADR13回修，在任何commit/ack前拒绝无法完整保存的含当前凭据输入，调用方保留原草稿；不确认“已保存”、不执行脱敏替代文。复用同一账本fixture证明拒绝前后checkpoint完全相等，n1-queued-redaction-source-red→green（1项）。不靠[REDACTED]字面量猜测，也不新增密钥库/schema或未发布候选迁移承诺。普通同步已消费路径保持。

复用原压缩/重开账本fixture，加入queue与save交错、同文不同身份、重开后按序一次消费、Hook拒绝和暂停持久化的必要Python接缝确认。n1-queued-ledger-source-red明确缺queue_user；首条green命令误写不存在测试文件，exit4/零收集记ENV，未充作通过。修正实际文件路径后的账本＋原图片存储共4 passed in4.95s，单文件mypy及Ruff通过。新增候选仍待独审及普通调度接线，不能由模块结果结题11。

## 主循环边界与展示事件

run_turn追加可选on_boundary/accepts_delta，旧调用兼容。沿冻结loop.ts:433，在轮数/预算/轮内压缩之后、模型请求组装前消费边界；完整tool批配对/图片投影/保存之前不开放。每个请求独有token，线程delta只call_soon_threadsafe投递，业务循环实际消费时复核请求token、Event及scheduler代次；请求收尾失效token。过滤只作用展示，可信usage/回答/工具结果仍由完成口保存。

新增一个必要Python接缝确认，复用原Read两请求：边界看到完整tool pair再加排队消息；旧请求delta和返回后的delta不污染新输出；usage照计。原loop22项＋此项共23 passed in0.18s，mypy1源过。首个组合green误写不存在scheduler文件，exit4/零收集，保留ENV；真正green仅运行实际loop文件。普通入口和最终安装仍待后续，不用模块结果结11。

独审发现context-length异常进入摘要await后finally才退休token的窗口；同一接线fixture加入原context-length→compact路径，实际red明确渲染late-during-compact。回修在except入口立即失效token，finally保留兜底；不增加矩阵或其它用例，原同例复验后收口。

## 排队手动Skill的已确认正文

普通入口提交手动Skill时，原始命令和展开正文在接纳时一并冻结。`queue_user(...,model_content=...)`兼容扩展沿用AcceptedInput.payload，新增`session/inputs.py`只编解码带版本的原文/投影JSON envelope；普通旧str/list内容不改。恢复使用已确认的正文，不重新读取可能已改变/消失的Skill。hasQueued按原文判断，标题也取原文；无新DB/schema。敏感正文同样在ack前拒绝，不能默默改成脱敏替代文。

在安全边界消费时，正文进入消息与consumed同事务提交，账本payload同时恢复为原始命令，避免长期重复保存整段正文；Hook拒绝/暂停的未消费材料保留，不能把受拒绝输入混入历史。正常恢复兼容既有payload；不承诺旧二进制消费本版本新增的待处理投影。

复用原保存/重开fixture增加手动命令正文快照及原文账本检查，n1-input-projection-source-red→green为该fixture＋原scheduler7项共8 passed in2.98s；同fixture账本不长期重复正文 red→green1项，3源mypy/Ruff通过。全部源码定向，未增加另一套场景矩阵，普通入口与最终产物仍待接入。

## 规划硬门与实际策略入口

run_turn追加可选authorize(Tool,最终rawJSON)、permission_mode与api_tools获取器；既有approve调用仍兼容。每工具在同一实际派发Task内裁决后才写intent/dispatch；plan即时硬拦write/exec及MCP前缀，不依赖策略层恰好拒绝。策略/设置确认异常时配齐该批尚未执行的工具结果并停止本轮，不继续执行目标。新增一个必要组合确认：同批EnterPlanMode→Write，即使策略回调返回True也不写入，下一模型请求工具裁剪；原loop23＋此项24通过，mypy1源过。

Conversation保留旧默认metadata，新增可配置policy_version/approval_ref，普通新入口接Gate后将使用permissions-v1/gate-approved，避免规则自动放行仍虚记人工确认。只是执行意图的真实来源标签，不新增存储schema，也不冒充尚未实现的完整perm-trace。

## Read状态的业务loop所有权

忙时/files可在主loop读取已读集合；旧Read worker直接写共享set/dict会与查询遍历冲突。保留原_read_text所有输出/基线登记条件，在只持本次空readFiles/readMeta/图片槽的浅worker ctx运行，await后只在主loop应用该次字段，不复制全局历史map。图像/错误不登记文本基线，offset越界仍保留原读前stat基线。approvedPath的exists/realpath计算同样offload，区外审批callback留在原业务Task/ContextVar，不把授权搬入线程。

复用原绝对Read记录fixture加写入线程断言，n1-read-loop-owner-source-red明确worker写共享状态失败；Read14/原图片/路径/Write/Edit来源共42 passed in0.46s，mypy2源通过。Ruff首次仅导入顺序失败，fix后通过，无额外故障/压力矩阵。此处关闭查询与worker共享状态根因，N2仍须为每并行Read隔离图片槽；不由此宣称工具并发已实现。

独审发现分类I/O await返回后缺少取消复核，旧run可能在暂停后新建区外审批。原授权Read同fixture受控在分类返回前设置Event：red明确仍调用审批，green在分类返回后检查signal，审批未发生；原fixture1项及Ruff通过。无新场景矩阵。
