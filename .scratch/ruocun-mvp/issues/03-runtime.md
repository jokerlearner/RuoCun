# M03 — 模型工具闭环、文字入口与正常恢复

Type: task
Status: awaiting-user
Assignee: /root
Branch: integration/ruocun-migration
Blocked by: [M01](01-files.md), [M02](02-shell.md)（允许先按共享声明迁移独立循环断言，实际接线消费已复核实现）
用户体验验收：pending（最终真实终端体验单列）

结果：最终代码1ad72d6的r2固定产物通过601项全量回归、Ruff/mypy/offline/build；独立9条循环来源、仓库外七工具/拒绝/正常重开/普通两轮/SIGINT/固定SQLite通过。用户体验仍pending。原始red/失败、必要回修、来源与产物绑定见[M03](../evidence/m03/README.md)及[M04](../evidence/m04/README.md)。本机console launcher WinError4551为ENV，使用已验`python -m ruocun`。

按[首版规格](../spec.md)实现普通产品入口而非demo：配置→streamChatResilient→校验/审批→intent→handler→结果与消息保存→后续模型请求。仅七工具；无忙时排队/自动压缩/后台，失败和上下文上限清楚停止，不将未知副作用当未执行重放。

首版多轮文字输入、单次prompt、流式输出、Ctrl+C、恢复会话及费用范围提示；复用StorageWorker，不另造存储。正确模型请求/工具消息配对与正常保存重开使用对应DAO测试、合成服务及最小双进程确认；真实模型预算未授权则不调用。源码、证据交M04独立复核，本票不自审。
