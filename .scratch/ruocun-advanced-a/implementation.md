# 阶段A实施进度

启动基线0b9537a（用户已选Skills＋上下文管理）；原首版r2及人工pending状态保持。用户Q2已选择“摘要失败保留原上下文并停止本轮”，按ADR-0012继续接线；后续约20小时顺序及失败处理规则已确认并[落库](../ruocun-next20h/plan.md)，阶段A自动出口后连续推进，当前阶段A实施授权保持。

## 已保存并独审的模块

| 范围 | 产品/候选 | 真实结果 |
| --- | --- | --- |
| 输入账本/上下文替换 | fa5815a；独审70220b6 | 不改StorageWorker/Checkpoint；已确认输入ID/seq独立于压缩messages、提交确认后替换；新增必要存储确认＋既有MVP产品独立2 passed in12.07s |
| compact成功路径、窗口解析、缓存审计 | f73d237；独审04b0a08 | 24 passed（17来源+7最小适配）、Ruff/mypy；固定wheel69成员绑定。摘要异常透传，原DAO硬截断一条未移植通过 |
| 静态Skills与8core | 06b427d；独审a34cee8/c478ff4 | 20 passed（19来源+1core黄金），TS真实运行时8个正文/元信息=golden=安装资源；fixed wheel80候选成员绑定 |
| 项目指令 | b499046→e9d5e23→3c3e488；独审c478ff4 | 6来源+1 D09显式兼容，独立7 passed；含..路径最小确认通过；canonical workspace与path.resolve规范化问题已修 |

各独立回执见[evidence/review](evidence/review/README.md)；实现日志分别在foundation/project-doc/skills/context目录。工程运行均白名单、合成HOME/config/temp、311.9/18包锁，真实模型API0调用。project_doc的“无git”来源用例必须用新建仓库外pytest --basetemp；默认合成TEMP在仓库内不满足该来源fixture前提，原环境无效失败保留。

## 未完成／接续

1. 阶段A自动技术出口已完成。最终产品`bccbb57`，r2 wheel SHA256=`d55dfac288d0638a5cd406daf65cf9dc01cab2eb9b93b8c99142c6361cb64de6`，在`dist/advanced-a-r2/`。669项通过、3项oracle排除，Ruff/mypy77/offline/build、87成员/SQLite实际运行库/仓库外纯安装均通过；[集成记录](evidence/integration/README.md)。真实模型/Terminal/人工仍pending。
2. 独立最终回执`b0ccb70`：两轴原4项全关闭，剩余0；旧报告和失败保留。`sourceStates`复用本次加载对象显示实际覆盖，JSON四个边界保留来源UTF16语义并转义孤立项；保存未确认只显示最后确认点。原生产品指令与工程AGENTS隔离，R1费用口径不变。
3. 下一步按[后续20小时计划](../ruocun-next20h/plan.md)进入N0，先补08/34实际缺口再解锁后继。人工体验保持后置，不再逐功能询问启动；T0以该计划实际开始记录为准。

原08/28/29/34/70均未因本批模块局部结果虚标整票resolved；原82票完成数仍6，人工体验继续后置。原工作树、venv、不可变候选、原始失败与参考技能保留。
