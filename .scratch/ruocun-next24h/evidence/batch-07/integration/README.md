# 批次07集中交付 b07-r2

产品固定提交 `d00d4a1b4333b52656e635dbdac0a46890fa6f16`。Windows x64 CPython 3.11 wheel 位于 `dist/b07-r2/ruocun-0.1.0.dev0-py311-none-win_amd64.whl`，SHA256 `9a82cbeb424277d4fce047016887e2fa150bbe584a42a12c1639136aa2879f43`。sdist 重建和直接 wheel 的字节一致。Git 归档、源码、sdist、wheel 与仓外安装的 306 个产品成员严格绑定，实际使用 SQLite 3.54.1。[构建与安装绑定](artifacts.json)

默认安装沿用 44 项锁定运行依赖。可选观测的 16 项锁定依赖另在隔离环境安装，并用同一 wheel 向本地 OTLP HTTP 接收器实际导出。默认包验证了 `opentelemetry` 与测试依赖的缺省状态。两套环境的 `pip check` 通过。[安装和导出回执](installed-observation.json)

默认全量 `1684 passed, 3 deselected in 668.43s`。安装产物直接导入，合成工作目录和环境由 `tools/run.py` 隔离。全仓 Ruff、mypy 和四项离线验收通过。临时测试路径移除后复验普通包启动。[全量回执](raw/b07-final-full/stdout.bin) · [离线验收](offline-summary.json)

首候选全量暴露 `--continue=latest` 的旧原生语法回归，已修复并独立复跑原三条恢复用例。另一次 Windows runner 在授权前退出，同首包单项及相邻前序复验通过，退出原因尚未确定。两类用例都通过了修复候选的全量回归。首轮所有失败及产物继续留档。[首候选](../integration-r1/README.md) · [续会话独审](../../review/b07-resume-equals-regression-review.md) · [Shell 复验](../n15-recheck/README.md)

42、57、59、62、70、71 的技术出口与高风险独审均通过，有效进度 **64/79**。Windows 系统定时、自动防休眠按 W3/W5 显示能力边界。POSIX 使用合成端口及受控进程取证。观测验证覆盖本地接收及失败旁路，远端入库待实际部署验证。77/78 人工体验仍待验。[批次记录](../../../batch-07.md)
