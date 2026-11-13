# 查清完整功能、模块职责与运行时调用链

Labels: wayfinder:research
Mode: AFK
Status: resolved
Assignee: Codex/runtime-research
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [冻结可复现参考快照](01-reference-snapshot.md)

## Question

冻结快照实际具备哪些功能、工具、CLI/斜杠命令和关键运行状态？模块职责、主要调用关系以及流式调用、工具调度、后台任务、取消和恢复路径分别是什么，哪些行为必须进入 Python 迁移规格？

## 依据与边界

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 逐模块盘点全部源目录与顶层入口，列出全部注册工具和命令，说明发现方法。
- 给出启动组装、单轮执行、流式事件、前后台调度、取消、恢复、退出的调用链。
- 区分状态机事实、历史文档叙述和未运行的行为假设。
- 审查相关本地覆盖层，指出可观察行为差异。
- 给出 Python 模块对应原则、运行时候选路线、必要实验和遗漏风险。

## Assets

- [冻结 DAO 的完整功能、模块职责与运行时调用链研究](../research/02-function-runtime.md)
- 本地研究分支：research/ruocun-core；初稿提交：326b66b0e2f00d3e115014bf4d98cca4f6f52d96；校对提交：1ee8428b1cff394c65268c12ceba2d43080c047f。

## Comments

- 2026-11-05：建图时先认领，委派本地独立 research 分支进行只读调查。
- 2026-11-05：主会话独立核对目录数后收录校对版本；静态研究完成，未运行产品或测试。

## Answer

已覆盖 19 个源码子目录及 234 个非 .test. 源码文件（含 fixture/辅助模块），登记各模块职责、主要调用链、完整工具/命令清单和所有本地覆盖层。
静态定义工具 43 个，普通启动默认注册 42 个；固定 slash 名字并集 52 个，不同入口能力存在差异。恢复依赖 SQLite、执行意图/结果、owner/epoch、runner 和代理检查点，不能统一为聊天 JSON 续读。
Monitor、fork、不同隔离与启动入口、定时层次及来源瑕疵均分别列为待规格化行为；详细候选和证据见报告，后续实验及路线票尚未解决。
