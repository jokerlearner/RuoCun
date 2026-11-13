# 41 fork 与隔离，17 恢复边界独立核验

固定候选 `d4046bd`。独审树的 `src`、`tests` 与候选一致。依据冻结 `tools/agent.ts:174–256`、`agent/runAgent.ts:179–191`、`agent/fork_agent.ts`、`agent/resume_agent.ts`，以及 ADR-0009/0010/0013/0015/0017。

`b02-review-fork-boundaries` 中，已有 Git 派发异常转发和后台 fork 的普通 CLI 用例通过。后台 fork 完成真实 Read，回环请求沿原父模型、原系统提示和精确 API 工具目录；已提交工具结果后实际强杀进程。重开显式继续遇缺少特殊现场，返回 2，模型请求数不增加。第三项无 HEAD 仓库的 CLI 用例初次因白名单未包含 Git 而停在夹具初始化。显式加入已知 Git 目录后，仅复跑该用例，`b02-review-fork-worktree-unavailable` 为 1 passed in 3.61s。已确认的隔离创建失败返回错误、子请求为零。

`b02-review-fork-worktree-unknown` 复用普通运行时，实际在合成仓库创建工作树后注入 Git 回执不明。运行时退出 74，只有一条父模型请求，工作树和分支留存，原 HEAD 保持。SQLite 留下父 Agent `started`、子 run 数为 0，原 TodoWrite 仍为已确认结果。脚本退出 0，实际 Git 现场保留在合成目录。未将已创建对象误报为未发生，也没有派发子代理或清理待核实的工作树。

fork 核心精确工具与嵌套拒绝沿用实现者实际 2 项定向。源码核对父请求发送前固定 API 工具与派发表，子表独立。即使 API 保留 Agent 定义，实际 handler 仍通过子深度拒绝递归。后台 fork 以 `fork` kind 持久记录，子工具在父回执后校验同父意图、当前 owner epoch 和 run scope；缺少特殊材料时在授权事务前拒绝继续。`remote` 保留同机 Git 工作树语义，已知独立提交和未提交改动的清理边界沿用实现者真实 Git 2 项回执。17 已验证的查询、决定和普通 checkpoint 显式继续沿用相应回执。

本次均使用白名单和合成 HOME，敏感扫描无命中。41 当前执行与失败边界、17 所需的特殊现场拒绝边界通过独立核验。
