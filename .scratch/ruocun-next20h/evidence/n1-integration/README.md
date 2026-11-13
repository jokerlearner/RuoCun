# N1／09、11、19、34统一集成

Status: complete / automatic-exit-passed（09、11、19、34；人工体验单列）。

固定产品及首轮测试源：`a7d803ce64f214ba7d757c134bbf0d80526d2dbb`。`dist/n1-r1`由sdist重建wheel，`.cache/n1-r1-direct`从同源直构；两wheel字节一致，SHA256=`1efa7574ab375baa04978646d72e522439bea44e82e420a0e3c4a11b5a5b6799`。root私有开发环境已安装该包，默认mypy检查108源、Ruff及offline入口均通过。

## 本批路径

- 09：分层权限、完整纯PythonShell解析、安全walker、原生/显式兼容装配、plan双层限制、同一最终参数裁决及实际写入。auto模型分类器后置；未声称24完成。
- 11：持久FIFO输入、手动Skill正文同ack冻结、安全边界消费、pause与新Event、迟到展示隔离；单输入owner协调聊天/审批/选择与退出。pipe逐轮顺序；后台15–17未实施。
- 19：ListDir、Glob、Grep双语/schema与/files实际入口。Python re沿首版已批准差异；已读事实仅当前进程，不声称跨重启恢复read map。
- 34：阶段A静态发现/8core原文/手动与模型调用，加完整目录、单项/批量控制和TTY选择；TTY专用simplify优先。开关重启生效，35/36动态发现与安装待前置结题后推进。

各模块来源、red→green及独审见[独审入口](../review/README.md)与[最终普通入口审查](../review/n1-ordinary-runtime-review.md)。本批复用原DAO测试语义，仅保留必要Python接缝确认，未新增压力/竞态矩阵。Read线程所有权及取消后不新建区外审批已按原fixture回修，旧失败回执保留。

## 出口

原始命令由白名单外层启动器及tools/run.py执行，合成HOME/config/temp；真实模型及付费API调用0。`bind.py`核对固定git archive、sdist/direct wheel、实际安装各成员、许可及两个运行依赖，结果写artifacts.json/runtime.json；绑定结果与功能通过分开记录。

固定包已与121个实际安装产品成员逐字节绑定，SQLite 3.54.1，运行依赖恰好prompt_toolkit 3.0.52及wcwidth 0.9.4。首跑绑定遇本机Git autocrlf将未固定eol的hook/NOTICE转换，原失败保留；回修只对三项包装输入识别合法checkout换行，仍按实际字节核sdist及wheel，产品成员严格不归一化。实际仅LICENSE为CRLF checkout。同一r1包重验通过，未重新构建。

[仓库外纯安装独审](../review/n1-final-install-review.md)通过，实际安装121成员、依赖版本、pip check、原CLI/受控TTY和SQLite门禁均验证。两个验证环境失败回执保留，未修改固定包或门禁。

首轮全量 `raw/n1-final-pytest-r1`：1153 passed、1 failed、3 deselected，435.57秒。唯一原受控TTY fixture在等待初始banner时超时；独立源码及同包仓库外入口已过。先用可判别的小组合查全量收集的进程差异；不因模块/安装独立通过而忽略全量失败。09/11/19/34仍claimed，真实模型、Terminal/resize及用户体验继续单列。

首轮之后，原两文件收集稳定复现系统SQLite 3.45.1提前加载，等待掩盖真实RuntimeGateError。9f5026d仅隔离原TTY fixture进程，保留26条断言、等待和真实门禁；独立原两文件4项通过（0525ad4）。固定产品/构建输入相对于a7d803c无变化，复验不重打包。

最终全量：复验源码 `896ecaf2124f49ff74c6f0cefb2a501727431387`、同一r1已安装，`raw/n1-final-pytest-r1-fixture2` **1154 passed、3 deselected in 384.67s**，exit 0，敏感扫描false。固定产物、类型/格式/离线、仓库外独审均通过，四票resolved；真实模型、Windows Terminal/resize及人工体验仍pending。原失败回执作为历史保留。
