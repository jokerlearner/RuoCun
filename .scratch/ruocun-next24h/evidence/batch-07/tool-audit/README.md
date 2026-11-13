# 57 工具审计纯模块

来源为只读冻结 dao-f17e189-7ac654a0dc06/source.zip 的 src/tools/tool_audit.ts、tool_audit.test.ts 及 src/session/audit_switch.ts，MIT。本切片仅 tool_audit.py 及专属测试；普通运行时工具调用、观测后端与 /audit 组合由主协调及57主实现者接线，不能凭此四项宣称整票完成。

三个来源断言组迁移：call记录字段及120长度；细粒度审计禁用；按错误率/调用数排序和时长汇总/报告。必要适配合并进紧凑用例：先传入redact处理当前会话凭据，再用既有permissions.secrets过滤完整参数，最后截取120个UTF-16单元，避免切断秘密后遗留前缀；原生RUOCUN变量优先DAO后备；明确沿来源specific=1可覆盖总AUDIT=0；不可写目录不影响工具结果；跨会话读取缺失/坏行旁路、仅LF切行保留字符串内Unicode分隔符。读入非call事件由summary忽略。报告仍为来源中文格式与UTF-16名称填充。

公开API：createToolAuditSink(sessionDir,env=None,*,redact=None)->ToolAuditSink；sink.call(name,cap,ok,durationMs,args,*,metadata=None)。可选metadata仅接受sessionId/taskId/runId/toolCallId四个关联字段，也经过脱敏，不记录其它任意载荷。其它公开函数为readAllToolTraces、summarizeToolTrace、formatToolReport及ToolTraceEvent/ToolStat类型。审计回调或I/O异常旁路，不执行重试、不影响实际工具执行或其存储回执。

白名单tools/run.py启动，根.venv加载本工作树代码、合成HOME和输入，无模型/网络/系统设置操作。raw/b07-tool-audit-red为实现前4项ModuleNotFoundError；同断言green为4passed，Ruff/Mypy通过。四条执行元数据scan_hit=false，人工检查均为合成值。未运行全量、未构包，未修改ToolContext/tool_batch/runtime或本票状态。普通接线及独审另计。
