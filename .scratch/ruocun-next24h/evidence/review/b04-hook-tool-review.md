# 批次 04 第 48 票 Hook 工具批、权限与恢复独立复核

固定 `8615f1f`，包括普通入口 `1fb4ccf`。独立树的 `src`、`tests` 与主线候选一致。白名单合成 HOME、配置、会话及本地 SQLite，模型使用替身。最终两次执行退出码均为 0，敏感值扫描无命中。

- 原测试 `test_source_hook_rewrite_is_single_and_applies_to_gate_receipt_handler_and_post` 独立通过。Hook 把原目标改为明确 deny 时，即使声明 allow 也不写；允许的同一个最终参数用于 gate、日志、真实 Write 和 Post，重放已确认调用不再执行 Hook 或工具。[回执](raw/b04-review-hooks-gate/command.json)
- 同一风险脚本核危险 Bash 改写。最终参数进入人工拒绝，标 dangerous，自动分类和实际 handler 均未调用。合成脚本只生成危险命令的文本，实际执行端为会直接失败的替身。[复现](b04-hook-tool-boundaries.py)
- 真实 SQLite 两处分开注入丢回执。Pre Hook 副作用仅一次，审批、Write、新请求均未执行，重开保持 unknown。Post Hook 副作用仅一次，原 Write 已有独立 `result_committed`，重开等待确认。只处理 Post 的未知记录后，同一个原 Write 工具结果按原值配对一次；没有重新写文件、运行 Hook 或请求模型。[回执](raw/b04-review-hook-boundaries-final/command.json)

源码复核确认事件名、原调用摘要与现有 tool scope 共同区分 Hook 意图，工具本体使用原 call ID。Pre 完成后才做最终参数校验和审批；Post 在原工具结果确认后才启动。Hook 丢回执从模型循环返回 `outcome_unknown`。普通入口用户、项目与本地 Hook 按已授权信任装配，阶段 49 的会话和代理生命周期另外验收。

首次危险夹具误把批量提示传给文字 ask，触发了审批未完成；改用 `approvalPrompt` 后实际到达人类提示。首轮临时 SQLite DLL 在同进程仍被加载，最终脚本在受控子进程退出后清理临时目录。两处均为独审夹具修正。已审产品范围无阻断，本次未改产品。
