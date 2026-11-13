# M04 — 首版独立复核、安装与交付

Type: task
Status: awaiting-user
Assignee: /root/mvp_review
Blocked by: [M01](01-files.md), [M02](02-shell.md), [M03](03-runtime.md)
用户体验验收：pending

独审：M01/M02已通过；M03已回修推理现场、父层初始化、JSON常量与来源失败屏障。code-review双轴剩余产品阻断0；r2纯产品仓库外安装、实际七工具/恢复/普通两轮、runtime SIGINT、SQLite固定组合通过。主协调最终全量**601 passed / 3 deselected**，五项工程入口及64包成员绑定通过，自动技术出口完成；人工体验仍pending。最终记录见[独审证据](../evidence/m04/README.md)。本机console launcher受策略拦截为ENV，模块入口通过，未将launcher记为通过。

按[首版规格](../spec.md)逐候选审查，复跑对应来源测试及必要取消/保存重开/纯wheel安装；固定产物与源码/hash一致后可复用，最终交付重建。核对七工具实际运行、拒绝不执行、错误不伪造成功、进程回收、真实SQLite组合及包资源。源测试、合成服务、真实模型、真实Windows Terminal体验分开记录，未验不accepted。

交付简明中文用法、配置/数据位置/恢复限制、版本产物；全量迁移历史票不由首版通过自动结题。独立审查者不能是所审产品实现者，失败交回原负责人，保留原始证据。
