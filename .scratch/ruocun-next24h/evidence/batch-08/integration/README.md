# 批次08集中交付 b08-r1

固定产品 `8ee4a9b992ee7a77759b3295708dda32bebbe68f`。Windows x64 CPython 3.11 wheel 为 `dist/b08-r1/ruocun-0.1.0.dev0-py311-none-win_amd64.whl`，SHA-256 `01330dead041e70177f609e338b433619b630919be055e8a47c5d52a5fdd8298`。sdist 重建的 wheel 与直接构建的 wheel 字节相同，Git 归档、源码、sdist、wheel 与仓外安装的 309 个产品成员一致。[成员及锁文件绑定](artifacts.json)

默认全量 `1699 passed, 4 deselected in 621.80s`。Ruff、Mypy、锁定依赖隔离安装、`pip check`、仓外普通启动和四项离线验收通过。`tools/run.py` 为每个进程设置白名单和合成用户状态。pytest 直接导入安装产物。[全量回执](raw/b08-final-full/stdout.bin) · [离线验收](offline-summary.json)

72 的评估工程尾项由独立定向回执覆盖。封包后的修复只涉及 `evals/` 工程脚本和证据，已核对包成员和自动出口的受控输入相对固定候选无差异。[评估独立复核](../review/n72-eval-runner.md)

77/78 的自动子案例以该固定包和实际回执为准。终端 IME、连续缩放和画面体验，登录/重启和其它账号条件继续按最终验收单列。Ubuntu WSL 的文件与网络隔离实测和 macOS Seatbelt 参数验证见对应票。真实模型调用为零。[自动子案例](../../../../ruocun/evidence/b08-automatic/README.md) · [批次记录](../../../batch-08.md)
