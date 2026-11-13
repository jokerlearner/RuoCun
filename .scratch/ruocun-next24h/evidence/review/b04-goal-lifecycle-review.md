# 批次 04 第 44、49 票独立复核

最终候选 `dc3f76d1`，独立树 `src` 与 `tests` 和主线候选一致。白名单合成 HOME、配置、会话和回环服务。受控 Windows SQLite，未调用外部模型、未构包。最终定向执行退出码为 0，敏感值扫描无命中。

## 44 内置命令和长任务

在最终候选复跑原普通 CLI，用 `/btw` 持久保存备注且无单独模型请求，`/coordinator` 与带目标的 `/goal` 打开长任务，`/task` 关闭并移除旧指令，`/status` 显示真实开关，`/batch` 实际发出两个子代理请求并汇总两项结果。[最终回执](raw/b04-review-goal-agent-hooks-final/command.json)

在 `cf1b75f4` 复用同一普通入口测试重开边界。显式 plan 优先于 yolo，yolo 优先于长任务带来的 auto。两个状态查询都没有增加模型请求。重开时没有启用 goal，则旧自主指令从真实请求移除，之前的 `/btw` 备注仍可读取。后续候选对该路径只增加状态输出和 Hook 互斥，没有改变权限优先级或指令清理。[复现](b04-goal-resume.py) · [回执](raw/b04-review-goal-resume/command.json)

## 49 会话和子代理 Hooks

最初 `2ff8cff` 普通会话原测试通过，覆盖启动上下文、正常重开替换、提示拦截及 SessionEnd。最终 `dc3f76d1` 在同一普通 CLI 夹具分别注入真实 SQLite 丢回执。两项均只有首次已确认模型请求，失败的事件命令实际执行一次。之后重开 exit 74，命令和模型均不重复，失败进程及重开不触发 SessionEnd。[普通来源复跑](raw/b04-review-session-hooks/command.json) · [故障复现](b04-session-hook-loss.py) · [最终回执](raw/b04-review-session-hook-loss-final/command.json)

- UserPromptSubmit 失败后，SQLite 中原输入仍为 queued，模型上下文无该输入。先前历史保持，新 SessionStart 已确认的标记仍在。
- SessionStart 失败后，上一会话的已确认标记仍在，后续输入未接纳，原先已消费的输入保持。
- 子代理原生命周期用例在最终候选通过。Start 在首个子模型前执行一次，输出只注入该子上下文，父 PreToolUse 不继承。后台取消后 Stop 用独立信号，在原子 run scope 持久确认且不唤醒新子模型。用户定义 Hook、项目受信及 `--no-hooks` 通过普通入口源码核对。确认前取消的独立窄回归沿实现证据复用。[最终回执](raw/b04-review-goal-agent-hooks-final/command.json)

初版故障夹具把注入的 loader 放错 argv 位置，并以无空白的字符串比对 cmd 重定向文本。修正索引和空白比较后，两条故障均在实际 SQLite 和普通 CLI 复验通过。44、49 的独审范围无阻断，未修改产品。
