# 阶段A普通入口集成记录

Status: automatic-exit-passed / human-pending

固定阶段起点`cb074ee`，范围ADR-0012；后续20小时计划ADR-0013已保存。本记录保留局部验证、r1问题和最终r2出口，阶段A通过不等于原票整票完成。

## 来源与差异

沿冻结`index.ts`的项目指令、静态Skills装配、目录渐进披露、通用手动Skill正文、用量/窗口/effort/压缩命令；`agent/loop.ts`的轮数上限、预算提醒/显式hard、工具轮间主动压缩及上下文错误最多两次压缩重试。主动触发沿实际`session.lastPromptTokens ?? 0`达到窗口85%，chars/3只作分类估算，不替代API实际用量。

普通入口注册已审Skill，使用原生RUOCUN指令及D09显式兼容来源，AGENTS不自动进入产品；启动只注入目录。手动`/slug`按来源使用原正文作为模型投影，原始命令仍在同事务确认的输入账本内；恢复后刷新当前能力前缀，保留原历史/工具结果。

压缩成功先等待唯一Conversation/StorageWorker确认再交换上下文。失败、空摘要或取消保留原上下文并停止受影响本轮；空摘要不把来源占位“(摘要为空)”视为成功，属于已批准失败保留规则的具体实现差异。已确认输入账本不因压缩被删除，未知工具结果保持阻塞、不自动重放。回合末压缩失败不返回一次性运行成功。

R1累计token可含历史；费用/预算只按本次进程。native skills-disabled读取及paths启动扫描沿来源，本批仍不写禁用状态、不实现35运行时激活/36安装或完整TUI选择器；原34整票不因此关闭。共享walker忽略`.ruocun`是产品路径品牌适配，避免搜索/条件匹配自身原生状态目录。

## 验证记录

沿现有公开CLI合成确认扩展一条端到端路径：原七工具/拒绝/保存重开/两轮文本，补项目指令隔离、Skill按需正文与手动调用、用量/窗口/effort/status、显式压缩后继续；无真实模型或付费API。新增两条源loop既有断言：工具轮之间主动压缩、两轮硬上限。既有真实Conversation确认复用并加入手动命令账本/正文投影；未重造StorageWorker测试矩阵。

| 回执 | 结果 |
| --- | --- |
| a-loop-hooks-red | 2 failed：已安装旧产品不接受compact/max_turns参数，有效来源red |
| a-product-wiring-red | 1 failed：旧普通入口返回unknown tool: Skill；证明模块文件存在不能替代CLI接线 |
| a-root-ruff-1 | 仅runtime导入顺序失败，修正后a-root-ruff-2通过 |
| a-root-wiring-green-1 | 17 passed in14.54s：已有loop/普通CLI/真实Conversation/boot来源与必要适配；实际覆盖Skill正文与手动投影、命令及压缩后继续 |
| a-root-static-ruff | 全仓Ruff通过 |
| a-root-static-mypy → a-root-static-mypy-2 | 仅审计usage的TypedDict标注失败；显式Usage cast修正，77源文件通过；无行为改写 |
| a-final-pytest-r1 | 固定03893b3/wheel 3f3c…：669 passed, 3 deselected in384.13s；首轮双轴仍发现3项Spec/1项记录P2，不能据此宣称出口完成 |
| a-unicode-cli-red → a-unicode-cli-red-2 | 首次fixture为220普通字符+emoji，未截出孤立项而通过；修正到219普通字符+emoji后同一既有产品函数在首请求前UnicodeEncodeError/exit71，证明SQLite保存边界同样受影响 |

Unicode诊断复用独审已捕获单例及原CLI函数；已有明确异常行，未扩大假设/随机矩阵。实际需收口的JSON边界是流式/非流式HTTP编码、检查点摘要编码及SQLite JSON文本；统一只转义孤立代理项，普通Unicode及既有摘要字节不变，不使用surrogatepass发送非法UTF-8。来源catalog的UTF-16截断语义保留。

r1独立Standards为1项P2记录同步，Spec为3项P2（Unicode、来源实际状态、未确认保存footer）。已回修：既有覆盖fixture与普通CLI增加实际覆盖诊断断言；sourceStates复用加载对象，无二次读/扫；project_doc报告真实注入/重复/空/读取失败，profiles消费实际选择结果；blocked先显示最后确认保存点，不再显示当前保存成功。JSON/Skills关键接缝已由独审5c5ad18静态通过，Ruff/mypy77文件通过。六张原票及两权威表已补局部证据，不修改原票Status。固定r2安装/全量及独审复验待执行。

## 最终r2自动技术出口

产品源码`bccbb57062a5518aad8ee4882eae4a1eef3429e6`。最终wheel为`dist/advanced-a-r2/ruocun-0.1.0.dev0-py311-none-win_amd64.whl`，SHA256=`d55dfac288d0638a5cd406daf65cf9dc01cab2eb9b93b8c99142c6361cb64de6`；sdist SHA256=`996372ede852b5bed4fba0b97e306bbf45b26f6877ae448773e673597967b865`。源码/依赖未再变化。r1及其问题、错误fixture、提前于sdist构建完成发起的失败安装回执均保留；最终安装只用已确认完成的不可变产物。

| 检查 | 实际结果 |
| --- | --- |
| a-r2-targeted | 原普通产品/真实账本/项目指令/启动装配共14 passed in14.40s，含219字符+emoji原复现及实际覆盖状态 |
| a-final-pytest-r2 | **669 passed, 3 deselected in372.46s**；3项oracle显式排除，非产品通过；新建仓库外basetemp |
| a-final-ruff-r2 / mypy-r2 | 全仓Ruff通过；mypy77源文件通过 |
| a-final-offline-r2 | 既有offline四个安装入口子案例通过，不冒充全规格验收 |
| a-final-build-r2 / direct-r2 / artifacts-r2 | sdist重建wheel=direct wheel；87成员源码=wheel=非editable安装；SQLite实际3.54.1、固定归档/DLL门禁通过 |
| 独立最终复验 | [独立报告](../review/README.md)，`b0ccb70`；仓库外环境仅pip/setuptools/ruocun，87成员绑定、原product+ledger函数与Unicode原复现确认；Standards原1项和Spec原3项均关闭，剩余0 |

原始stdout/stderr/退出与环境回执见本目录raw，均为合成输入，scan_hit=false；[artifacts.json](artifacts.json)/[runtime.json](runtime.json)绑定最终r2，[artifacts-r1.json](artifacts-r1.json)保留首轮。外层清空环境、私有CPython3.11.9/18包锁及合成HOME/config/session，没有真实模型/付费API。仓库外运行使用`python -m ruocun`；MVP记录的console launcher应用控制ENV不在本批改主机策略。

本批ADR-0012所列自动技术出口完成；真实模型、Windows Terminal视觉/缩放、用户体验和其它平台实机继续未验。原08/19/28/29/34/70仅登记相应子路径，不因本批将整票resolved；34选择/控制、08图片等缺口先由后续N0收口，再按真实前置解锁。原82票完整完成数仍6。
