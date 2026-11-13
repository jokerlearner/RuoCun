# 09 装配独审修正：退出规划清运行时覆盖

冻结 `index.ts:1134-1137` 的 ctx.setMode 在 mode 为 normal 时同步清 permModeOverride。
本次仅在 PermissionRuntime.setMode 增加同样的清理：`/mode default`→setMode(plan)→
setMode(normal) 后恢复配置默认 auto。`/plan` 命令自身沿来源 toggle，未改该分支。

原 `test_mode_commands_follow_source_toggle` fixture 补明确断言，
`n1-runtime-mode-review-red` 1 项确定失败；green 1 passed；同文件 Ruff、mypy 1 源通过。
未扩矩阵、未重复 3/162/392 项或构建。产品 hash 和原始命令/输出见 `runtime-mode-review/`。
