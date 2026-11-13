# 批次07首轮安装包的 Windows Shell 复验

首轮候选产品 SHA 为 `c8e7723de82b8bb1ae7bfea56111091da9957946`。原 wheel 的 SHA-256 为 `3e199e1b5864adc86da9600a07fbca9714661481a0247c7ccb4b2a4b6c4efc3d`，安装目录为 `.cache/b07-r1-installed`。首轮全量中，`tests/test_n15_managed_shell.py::test_real_detach_reconnect_logs_and_once` 在 runner bootstrap 阶段失败，启动器退出码为 `3221225786`（`0xC000013A`），当次 `runner.log` 长度为0。[首轮产物绑定](../integration-r1/artifacts.json) · [首轮全量回执](../integration-r1/raw/b07-final-full/stdout.bin)

| 白名单执行 | 结果 | 回执 |
|---|---|---|
| 原安装包单独执行失败用例 | 1 passed，7.00 秒。回执打印了原安装包导入路径 | [单项](raw/b07-shell-installed-single/stdout.bin) |
| 原安装包按收集顺序执行相邻前序和失败用例 | N13 的8项、N14 的4项及原 N15 共13项通过，12.78 秒 | [前序及原用例](raw/b07-shell-installed-predecessors/stdout.bin) |
| 只读查询首轮失败现场的 SQLite | 唯一运行记录的 status 与 phase 均为 `failed-before-grant`。运行目录仅有 capability、manifest 与空日志，未生成 runner state、grant、start claim 或测试副作用 `starts` | [原现场](raw/b07-shell-original-db/stdout.bin) |

复跑沿用原 wheel 的安装解释器，启动时只在 pytest 进程追加测试依赖路径。两次 pytest 使用各自的仓外合成临时目录。SQLite 探针以 `mode=ro` 打开原数据库，输出仅含状态、文件名和测试副作用是否存在。三条命令均已收尾，`sensitive_match=false`，原回执位于 `raw/`。

`0xC000013A` 对应 Windows 的 `STATUS_CONTROL_C_EXIT`。原记录确认命令在授权前停止，控制事件的触发来源和退出根因仍未知。紧邻的测试序列未复现退出。对照批次06，两个安装包的 Python 3.11.9 启动器、`managed_shell.py`、`shell_runner.py`、runner 身份摘要成员与 `__main__.py` 字节一致。`cli.py` 在批次07有变化，两个内部角色的分支逻辑相同。首轮失败仍按原结论保留。[Microsoft NTSTATUS](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55) · [批次06全量](../../batch-06/integration/raw/b06-final-full/stdout.bin)
