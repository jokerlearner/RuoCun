# 38 同步内置子代理候选

从固定849f5ba开始，39/40/41/17按实际依赖留待后续。38由既有父`run_turn`派发`Agent`，每个子任务建立独立`Session`、模型、read/write跟踪、工具池和权限模式。它复用相同的模型客户端与工具执行器，父模型获得最终工具结果，不获得子转录。支持前台单任务、最多20条批量请求、默认最多10路模型并行及输入顺序汇总，单条已知失败保留其它结果。独立`RUOCUN_SUBAGENT_MAX_TURNS`（兼容DAO前缀）缺省500，父会话轮数不传入。父取消对当前子模型及工具生效。内置定义按冻结来源提供四个类型；verify的强制后台、显式后台、fork和隔离在同步入口明确拒绝，实际功能由后继实现。explore保留冻结的Write/Edit排除和Bash审批边界。mode=plan和父plan均把写/执行从真实工具池移除，子代理无法退出继承的只读边界。

子工具使用run UUID作为journal scope。SQLite当前owner内的精确父`Agent` intent和同run记录通过后，子工具才可排除该正在执行的父意图；其它已知/未知状态仍遵循原guard。并行子任务的模型请求仍可并行，工具批持有同会话锁，避免兄弟started journal与结果确认相互污染。真实写后结果未知时不结算父Agent，保留原文件、原子/父intent与子RunRecord的unknown；重开归类未决而不执行。子代理不消费父TaskWait登记，假造未注册的等待调用按普通无效工具处理。Agent角色、模型、范围、子转录和usage保存在已有RunRecord，暂未接入40的可继续材料及后台生命周期。

自动权限模式的工具分类读取子转录，保留真实父规则、请求回退、独立模式和审计。父auto时同步结果额外走DAO的handoff分类，复用已有模型选择/传输与usage审计回调。仅使用子用户任务和工具调用构建摘要；凭据脱敏、助手自由文本排除。block增加警告，异常/无可判定XML提示手工检查；都保留原结果。普通组合端口为`ctx.runAgent = createAgentRunner(session, ctx, registry, permissions, conversation, options, env=env, project_instructions=project_text, handoff=createAgentHandoff(classifier_context, call_classifier, output))`。root在默认Registry注册`agentTool`，把`agentCatalog`加入主提示并用普通CLI验证。

原始缺模块red保留。首轮实现受冻结TS的CRLF提取缺陷影响产生空角色资源，保留中间红，统一换行后冻结四定义进入真实请求。最终6项定向通过（38三个真实SQLite回合，加旧16 TaskWait、17 resolve及15 Shell存储关联），12源mypy与Ruff通过。作用点包括原父工具/子工具同ID、作用域伪造拒绝、真实写入与explore禁止写、模型与转录隔离、handoff warning、并发顺序/失败/取消/预算、未知真实写不重放。所有测试使用当前worktree/src、白名单与合成HOME，实际SQLite，模型仅注入边界，均未调用真实或付费模型。普通产品组合及独审待root，当前不标38完成。

## 子工具结果回执失联回修

独审在b1e6d9b真实执行Write后模拟SQLite回执丢失，父层虽报告outcome_unknown，Conversation仍未blocked，子run仍running。修复让已产生持久副作用的结果保存异常走原UnknownToolOutcome，普通只读结果保存失败仍原样传播。子run checkpoint保存异常也立即停止会话。worker已因未确认COMMIT停止写入时保留可信原记录。下次打开，同子scope和父Agent关联中仍有未确认副作用，才将旧子run归类unknown。若SQLite已确实保存子工具结果，恢复保留结果原文，将已丢执行器的run归类interrupted，父Agent仍未决。无论哪种情况，都只尝试保存一次结果，实际文件只写一次。原独审脚本、两个回执分支及原子恢复回归通过，未重新构包或跑全量。
