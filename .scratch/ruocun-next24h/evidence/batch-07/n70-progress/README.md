# 70 本地进度提醒切片

基线主线631fbc44包含70正式领取记录，57前置已独审。来源只读冻结dao-f17e189-7ac654a0dc06/source.zip的src/agent/loop.ts:196–213、232–248、728–762；对应loop.test.ts:845–1101。source-binding.json保存文件SHA256、行号和三条未改写的原始提示模板。产品progress_advice.py直接保留这三条原文，不在运行时读证据文件。测试中的完整预期从独立冻结提取记录构建。

实际默认ADVISE_GAPS为4/3/2，来源部分注释和测试叙述仍写5/4/3，不能用旧注释覆盖可执行代码。正有限Number值可由ADVISE_GAPS覆盖，RUOCUN优先DAO；保留非整数值，不悄悄取整。判据是出现Write/Edit/NotebookEdit/Bash，或实际存在后台运行项且本批非空、全部为BashOutput/TaskOutput/TaskGet/TaskList。TodoWrite不算推进，混合Read的轮询批和空批也不能用后台标志重置计数。

API：createProgressAdvice(environ=None)->ProgressAdviceState；state.step(calls,*,runningBackground=False,interactive=True,enabled=False)->str|None；返回值是应追加至已保存历史的system正文，state.notice是同次可见notice，下一步自动清空。公开gaps/noProgress/nextAdviceAt/stuckAdviceCount/totalStuckEvents，仅本次runTurn局部累计。每次runTurn开始新建状态；进展会清零本次卡住次数但不会清零累计触发次数，累计第三次即使中间有零星修改也升级。默认enabled=False；无交互fallback不建议AskUserQuestion。全部为本地纯逻辑，不请求模型或产生额外token。

四个紧凑来源组red→green：默认关闭及4/7/9/11轮递减节奏、原文/notice；四类实际工程动作及真正后台轮询；零星修改重置后累计第三次升级；环境值/无交互原文。raw保存实现前4项ModuleNotFoundError、同断言4passed、Ruff/Mypy通过，tools/run白名单合成HOME，全部scan_hit=false。未运行全量、未构包、未调用网络或模型。

本候选不修改共享loop/runtime/CLI，不代验append-only保存、notice接线或headless默认开关。主协调在实际工具批结果已配对保存后调用step，把返回system追加至同一历史/存储链并输出notice；自然结束的空assistant分支不额外制造一步。轮数临近上限提示属于另一原有分支，本切片不改写。70整票仍待普通入口组合和独审，不自行resolved。

主线 `d22c2395` 接线后新增一条真实 `run_turn` 验证，复用现有合成模型与 Read 工具。第4次工具结果先与调用配对并通过 journal 保存，追加提醒时保留既有上下文。提醒保存后显示一次，紧接着进入第5次请求，并继续保留在第6次请求的历史前缀。无交互提示不建议询问用户，模型请求总数为6。此测试以记录型 journal 验证保存顺序及提交参数，SQLite 和 CLI 参数默认行为仍以其各自入口证据为准。`raw/b07-progress-loop-final` 同时运行此接线测试和4条模块用例，5项通过，Ruff通过，两条 `scan_hit=false`。
