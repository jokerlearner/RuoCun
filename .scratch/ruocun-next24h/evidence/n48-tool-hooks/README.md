# 48 工具 Hooks

冻结 DAO `dao-f17e189-7ac654a0dc06`。对照 `src/hooks/hooks.ts:29–143`、`src/hooks/hooks.test.ts:8–90`、`src/hooks/integration.test.ts:8–23`、`src/tools/execute.ts:40–99,140–211`、`src/index.ts:1212–1226,2282–2285` 和 D09。

- 按文件、事件、组和命令声明的顺序加载。只有 command 执行，async 声明仍按来源顺序等候。以 UTF-8 无附加换行 JSON 提供 stdin，保留 DAO/RuoCun 环境别名与声明的工作根。复用 Windows Job/POSIX 进程组，按来源 4 MiB 每流，默认 30 秒。确认回收后，超时和超限按非零退出处理。回收未确认时保留独立 Hook 意图。
- PreToolUse 的独立持久回执按原调用身份、事件和有效配置匹配。同一调用复用已确认输出，摘要不符、缺失或未知时不重跑。用整对象改写的最终参数进行 schema、权限、审批、journal、派发、PostToolUse 和审计。deny 不能被 Hook allow 覆盖，敏感、危险或未解析的 Shell 不能靠 Hook allow 降权。Hook ask 使用真实人工审批。
- 工具效果已确认时先保存真实工具结果，再登记独立 PostToolUse 意图。Post 返回信息不回滚工具。受保护目录中的审计只记录脱敏的参数片段和事件状态。带密钥的配置命令正文不写日志。
- 来源命令协议与实际改参用例先红；修复后 3 项通过。真实 Windows 命令读 UTF-8 stdin，核对 exit2、改参只执行一次、允许声明无法越过硬 deny、ask 绕过分类器、Post 同参且退出2无回滚、保护 ACL 和审计脱敏。相邻权限、工具批和 Windows Job 用例通过，Ruff、mypy 通过。
- 配置选择支持常用来源匹配规则和命名组。Python 端对不能解析的 matcher 报错，未宣称覆盖全部 JS RegExp 扩展。项目 Hook 只由普通入口按已确认项目可信状态装配，独立生命周期归49。全程合成环境，无付费模型或构包。
