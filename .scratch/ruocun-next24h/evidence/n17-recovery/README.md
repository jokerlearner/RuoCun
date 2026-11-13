# 17 恢复查询与人工决定候选

当前为在途候选，17保持claimed。普通命令入口由root组合，恢复高风险接缝等待独审；普通代理继续所需38/39/41实际dispatcher尚未提供，不把当前拒绝路径记成全功能通过。

冻结来源见manifest，原ZIP只读。repairToolPairs逐assistant保持原消息，按tool_calls次序配回已有工具消息或真实journal结果；结果未知与确认未执行用不同提示，绝不重放。查询仅公开任务身份、种类、状态、人工依据及未决工具，不倾倒runner capability/执行环境/代理恢复原材料。查询不暂停，操作命令由root先pause→settled。

resolve、decide、continue许可复用唯一StorageWorker/StoragePort；journal/run/事件、决定ID和`[用户恢复决定]`消息在同一SQLite事务。重复同ID内容一致返回原回执，冲突拒绝。失败注入在journal修改后、checkpoint写入前，真实SQLite回滚后journal仍unknown、历史与决定均未增加；修复后同ID可正常提交。未知写入真实文件保持原字节，重开/重复决定不执行写入。

decide仅对该任务最新且唯一unknown运行接受completed/failed/canceled，保留旧状态、用户证据和resolved_by_user，不制造runner关闭收据。关联Bash未知结果仅按精确RunRef补人工标签，已有真实结果不覆盖。与manager每run发布锁互斥，旧观察器不会把人工核实结果重写成真实关闭。当前manager的poll/kill会明确返回resolved-by-user，不冒称exit/cancel；再次恢复跳过控制此run。用户决定承担未知处理，不意味着开发者已证明原执行的客观结果。

丢失代理/fork/monitor执行器变interrupted，保持真实kind，不启动工作；已有后台快照时同事务生成一次interrupted事件。manual不启动执行。缺失/变更附件登记只读MissingResultAttachment未决；用户明确接受缺失后记决定及原hash关联，文件仍缺失，不伪造文件已修复。manager.restore(report_errors=True)将已知终态的坏收据/日志材料报告为RecoveryMaterial未决，原终态不变；显式处理后记录接受标记，后续不重复核验/重启该已处理材料。默认restore仍保留15旧异常行为。

continue先检查已保存模型、agentType、定义版本、worktree、messages、权限与预算；fork还需父上下文、精确工具、裁剪与路径隔离材料，禁止降级。真实dispatcher未绑定时明确拒绝，不保存虚假启动成功。注入执行器端口已用真实SQLite和实际文件副作用验证：先持久一次性许可+新RunRef后才调用，成功重复ID不再调用；执行器抛错后新run保留unknown，同ID重试不调用、不伪成功。产品未来dispatcher还须验证当前已加载定义/原模型/工具材料并实际装配38/39/41，当前不能宣称普通子代理端到端已恢复。

新增4项定向测试来自冻结配对/决定/恢复语义：纯配对1、真实SQLite恢复1（含事务rollback、幂等、附件、注入继续）、复用15原生夹具的runner日志缺失1及runner真实丢失后人工decide1。17固定目标4通过；最后仅收窄query公开字段后定向2通过，原生代码不变。中间共享回归25通过（旧编辑恢复五切点、15存储、16实际投递、worker），此回执明确是最终窄修前的中间候选，不冒充最终全量。7源mypy、Ruff通过。n17-regression第一次因测试路径写错而exit4，真实原始失败与更正后的回执均保留。

全部测试经tools/run.py白名单、合成HOME/配置/会话；无真实/付费模型、无全量/build、无人工体验验收。raw扫描false并审查，仅合成输入和已知仓库路径。原生runner测试有界退出，runner-loss沿原Job端口证明子孙止写，未对未认证未知发控制。

## root组合端口

```python
await manager.restore(report_errors=True)
recovery = RecoveryController(conversation, session, background, manager)
await recovery.recover()  # 启动一次；不在每次查询重新归类活代理
# blocked时仍开放/recovery；其它副作用维持原blocked。
# 查询不暂停；isMutatingRecoveryCommand(line)时先pause→settled。
notice = await recovery.command(line)  # None表示非本命令
```

恢复命令可在blocked时提交明确用户决定，不经普通accept_user（普通写仍拒绝）。处理后若conversation.blocked仍True则保留停止。无材料/非法参数/明确已回滚抛ValueError；未分类存储异常或结果不明不自动重试。manager.close沿原finally必经，并逐条显示保留通知。root可不传continue_agent，产品返回真实未装配原因；不能把这条拒绝改成继续成功提示。

## 提交回执未明的窄修

CommitUnconfirmedError与RollbackError继承StoreError。最初Controller将所有StoreError包装为ValueError，虽Conversation已blocked且未重放，但会混淆结果未明和明确拒绝。仅这两类异常改为原样上抛。单条实际SQLite复现已保存red→green：数据库确实提交决定/历史后注入丢回执，本进程保持blocked，不宣称回滚；重开查询真实回执、重复同ID只保留一次决定与用户历史。修复只改recovery.py这条异常分支；单源mypy、2文件Ruff通过，不重跑原生生命周期或25项。

## 普通CLI唯一接缝

合并root d064e59与窄修后，用ordinary-cli.py按一条场景运行：真实Write handler在已提交intent后写目标文件，故意不提交result；独立普通CLI以--continue /recovery查询，真实显示unknown；第二CLI显式resolve；第三CLI再查询。三次exit0，回环计数server零请求，文件字节不变；另一独立存储进程核journal result_committed、恰好一条决定及用户历史、assistant原文保留。没有真实/付费模型调用，未再扩大测试或构包。原始CLI stdout/stderr、计数摘要及当前runtime/recovery指纹见manifest-ordinary-cli.json与raw/n17-ordinary-cli。root仍负责17整票真实依赖与状态，查询/resolve/decide候选不等于普通agent继续完整出口。

## 普通同步代理检查点

冻结 DAO `f17e189` 的 `src/agent/runAgent.ts:400–404,436–446` 在执行前及运行期间保存子代理状态。`src/agent/resume_agent.ts:96–99` 用已保存的子工具回执配对，再追加新用户指令。`src/session/recovery.ts:47–48` 标记丢失执行器并等待显式继续。

RuoCun 同步代理在请求前保存已扣减的业务轮次，在模型和工具结果提交时保留转录。恢复材料绑定实际工作目录和工作区身份、角色版本、模型端点、权限和工具目录。新快照显式记原同步或后台工具裁剪策略。旧格式仅从有完整后台身份记录的 40 快照识别后台策略。特殊 fork 继续沿原缺材料门禁保留现场。

真实 SQLite 验证在原同步代理完成一次 Write 后、第二次模型请求边界终止拥有者进程。原实现重开缺少 `recovery_material`。修复后，新拥有者保留两轮余量和原同步专有工具。显式核实旧父 Agent 之前没有新派发。核实后创建新 run，读取原配对、原 Write 未重放，重复同决定也未再次派发。相邻验证覆盖旧格式后台继续和 fork 内核。所有回执见 `raw/n17-sync-*`。模型边界使用合成响应。

复用同一中断夹具覆盖动态权限和工具目录。原子代理通过 ToolSearch 实际激活延迟工具，调用 EnterPlanMode 后在下一模型请求边界强杀。原实现把已保存的动态状态当作权限或工具漂移而拒绝。修复在独立子上下文恢复已保存的只读 plan，并按原 API 目录精确激活已注册的延迟工具，随后用完整 schema 摘要、权限、路径和其余材料重新校验。恢复请求沿用原工具顺序，已激活只读工具读到原文件，模型尝试的写入被 plan 门禁拒绝。同批验证旧后台快照和 fork 内核。原始回执见 `raw/n17-sync-plan-*`。
