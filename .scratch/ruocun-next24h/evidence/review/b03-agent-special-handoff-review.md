# 批次 03 第 67 票 fork 与 remote 交接独立复核

固定候选 `5f6dc52`。在 Windows 真实 SQLite、真实合成 Git 仓库和仓外临时目录复用原 `tests/test_n67_agent_handoff.py`，选择 fork、remote。2 项通过，1 项普通分支按范围略过，耗时 9.75 秒。白名单使用合成 HOME、配置及请求替身，扫描无敏感值命中。[独立回执](raw/b03-review-agent-special/command.json)

- Fork 的前台和后台三次请求使用同一精确工具目录。后台运行一个精确目录中存在、普通后台白名单外的工具，仅执行一次。原前台工具摘要与后台持久材料一致。SQLite 还检查同一父调用、原执行类型、交接双向收据和工具摘要。旧父取消信号未取消新后台。
- Remote 的两次实际写入在同一原工作树完成，父目录未出现误写，带改动的工作树保留。交接前以原 Worktree 句柄核目录与 Git 管理目录身份、仓库登记和分支，SQLite 保存并核对原路径、分支及材料。完成后以同一原句柄进入既有收尾，干净且仍持原身份才清理，改动及独有提交保留。失败、取消保留目录，Git 变更结果未确认时记录 unknown。自动用例验证脏树保留，清理授权和失败分支按源码复核。

冻结 `src/tools/agent.ts` 的 `!isolate` 分支覆盖普通、fork 和 remote。当前候选补齐前次报告中的 fork 与 remote；显式 worktree 隔离保持前台。Fork 跨重启的既有精确工具材料限制不因本轮交接改变。终端真实按键及视觉体验仍由批末窗口另计。未修改产品，未构包。[此前普通 Agent 独审](b03-agent-handoff-review.md)
