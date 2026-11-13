# 批次04普通入口接线

48 的红回执为未识别 /hooks。普通入口接线后，同一合成用例验证未信任项目的配置隔离、--no-hooks 禁用及实际 Hook 改写 Write 后仅写入最终文件，1 项通过。[红回执](raw/b04-hooks-ordinary-red/command.json) · [绿回执](raw/b04-hooks-ordinary-green/command.json)

43 的红回执为已完成任务的 TaskSend 未启动后续请求。普通入口接线后，复用 40 的回环与恢复用例共 6 项通过。已结束代理按原任务身份接续，原 Read 回执在新请求中恰有一次，追加指令在最后一条用户消息。[红回执](raw/b04-tasksend-ordinary-red/command.json) · [绿回执](raw/b04-tasksend-ordinary-green/command.json)

两个入口均使用合成工作区、回环 HTTP 与环境白名单，未调用真实模型。[静态检查](raw/b04-first-seams-mypy/command.json)

44 真实普通管道输入 `/batch` 缺参、`/btw`、`/coordinator`、`/goal <目标>`、`/task` 与带参 `/batch`。未接线时无缺参提示。接线后备注命令零模型请求，目标与长任务指令进入首轮，关闭后移除专用指令，批量真正执行两个 Agent 并收回两份结果。[红回执](raw/b04-goal-ordinary-red/command.json) · [绿回执](raw/b04-goal-ordinary-green/command.json)

49 使用冻结实现前的 Git `c288587` 导出的源码复现提交 Hook 缺失。接线后，真实回环请求显示启动前缀唯一、恢复前缀替换、用户提交注入在对应消息之后，拒绝提交零请求，正常两次退出各执行一次 SessionEnd。与直接调度回归合计 11 项通过。[红回执](raw/b04-session-hooks-source-red/command.json) · [绿回执](raw/b04-session-hooks-source-green/command.json)

49 首次临时命令从旧开发环境安装导入了旧产品，结果不计入候选。以上两份 49 回执都显式导入各自被测源码，工作目录、环境和模型均是合成数据。
