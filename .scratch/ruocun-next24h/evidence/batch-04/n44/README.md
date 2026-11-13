# 44 内置命令与长任务提示

`runBuiltinCommand` 保留 `simplify`、`remember`、`review`、`init`、`batch`、`skillify` 六条。空 `remember` 或 `batch` 返回用法，未知名称返回 `None`，其它命中返回单轮 prompt。中文 `simplify` 共用冻结技能原正文；`init` 和 `skillify` 使用产品原生 `RUOCUN.md`、`.ruocun/skills`，并行派发使用产品 `Agent` 工具名。`review` 的 GitHub PR 分支只接收 ASCII 数字，沿用冻结 JS 的匹配边界。冻结 `commands/builtin.ts` 只有中文模板，英文按对应用途与约束翻译。

`LONG_TASK_DIRECTIVE` 与 `LONG_TASK_DIRECTIVE_EN` 从冻结 `system_prompt.ts` 恢复完整尾部指令。前台转后台使用已实现的显式 Ctrl+B，落盘提示指向实际返回的输出路径，指令未修改模型硬轮次配置。实际长任务开关、权限、普通命令入口、回环 `/batch` 与独审由主协调另外登记。

`b04-44-builtins-red` 复现原模块缺失，`b04-44-directive-red` 复现原简写没有编排与等待提示。`b04-44-builtins-final` 通过内置指令及既有系统提示共 29 项。`verify-prompts.py` 只读冻结归档，`b04-44-builtins-source` 将 8 个中文命令分支及 2 份中英长任务指令按上述产品差异逐字绑定，英文内置语义经同一测试覆盖。白名单定向 Ruff 和 Mypy 通过。未发真实模型请求、未构包。
