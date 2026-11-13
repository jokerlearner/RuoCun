# 阶段A：项目指令、基础Skills与上下文管理

Status: implemented / automatic-exit-passed / human-pending
用户选择A，启动基线cb074ee，2026-11-10；本批决定[ADR-0012](../../docs/adr/0012-skills-context-phase.md)。

实际进度与最终固定候选见[implementation.md](implementation.md)。普通入口、669项回归、五入口及独立技术出口已通过，人工仍pending；不由本批推定原08/29/34等整票完成。Q2已选摘要失败保留原上下文停止。

## 交付边界

1. 原生用户/项目RUOCUN.md、RUOCUN.local.md及显式只读兼容源按D09顺序/标签/内容去重注入，Git文件或目录均为边界；工程AGENTS不自动进入产品提示。
2. 静态Skills发现/frontmatter子集、slug/namespace/覆盖、model/user invocable、8个core资源文本及Skill工具可用；启动只放目录，按需正文，文字命令可调用/列出，不声明完整TUI选择器。动态激活/安装/自动第三方改写/插件后置。
3. 复用Session/cost，提供本次费用/预算/轮数、模型窗口/手动覆盖、cost/context/status/effort必要文字入口；R1历史费用提示保持。默认预算提醒，显式hard才停止。
4. 估算、85%主动触发、上下文错误有界反应式压缩、手动/compact、保留旧摘要和活Todo、图片占位沿DAO。Q2差异：摘要失败保留原上下文停止本轮；压缩取消/未提交均保留可信保存点。
5. 压缩只更换模型可见上下文，不删除已确认输入账本，不重放工具；继续使用唯一StorageWorker，任何必要持久字段先由主协调与独审确认，不重造存储。
6. 来源测试＋必要普通CLI合成确认、全量/构建/仓库外固定产物及独审；真实模型/付费API不调用，真实Terminal/人工仍pending。

## 任务与文件归属

| 票 | 负责人 | 独占范围 | 顺序 |
| --- | --- | --- | --- |
| A01 项目指令与共享接线 | /root | project_doc.py、agent/loop.py/runtime.py、cli/help、tools/types.py、skills/types.py、session/session.py/conversation.py及共享记录 | 先固定类型；共用文件唯一写入者 |
| A02 静态Skills | /root/advanced_skills | skills/skills.py、skills/bundled.py、skills/resources/、tools/skill.py、独有来源测试/证据 | 消费已提交共享Skill；模块独审后root接线 |
| A03 上下文模块 | /root/advanced_context | agent/compact.py、agent/context_runtime.py及摘要资源、session/context_window.py、session/cache_audit.py，来源测试/证据 | 按已确认共享契约编码；Q2已选保留上下文停止，模块独审后root消费 |
| A04 独立审查与交付 | /root/advanced_review | 独立证据，不写被审产品 | 先审共享/持久化接缝，再模块与最终固定产物 |

原任务映射：08/19/28的首版覆盖按案例复用，未覆盖不虚关闭；34、29仅本批所列子范围，70仅产品指令子路径，其余原任务/真实硬依赖保留。旧未过滤frontier不用于此批派发；本表只调度所列文件和实际接缝，不消费“整票完成”推定。

工程命令沿外层清空环境启动器＋tools/run.py、私有venv、合成HOME/config/session，沿原生接口作来源断言，不扩压力/故障矩阵。工作树从包含本批记录提交创建，普通同领域可连续推进；存储/权限/取消/恢复的变更先交独审。原DAO与原参考技能只读；来源归档仍dao-f17e189-7ac654a0dc06。
