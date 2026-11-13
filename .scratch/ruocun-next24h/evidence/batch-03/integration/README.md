# 批次03集中构建 b03-r1

固定产品源码 `5f6dc52bbb410c32772d70b1d42a1a80207610d0`。Windows x64 CPython 3.11 wheel SHA256 `14d98f94cc32c00358b47a764f0620a3cb5c0e4656efb1f85d98f3b1af9d70e6`。同一轮产出源码包及 wheel，再直接构建 wheel 校验，两者哈希一致。Git、源码包、wheel 和隔离安装的 245 个产品成员逐字节一致，实际运行 SQLite 3.54.1。[产物绑定](artifacts.json)

六项运行依赖按锁离线安装。`pip check`、四项安装冒烟、全仓 Ruff 和 222 个源码文件的 Mypy 检查通过。[离线回执](offline-summary.json)

全量测试使用独立的测试环境。同版本旧安装曾通过测试依赖路径被误识别，第一次运行停在收集。关掉借用路径后完成固定包安装，再恢复测试依赖路径并确认实际导入来自本次隔离环境。构建产物和纯安装未受影响。

固定 wheel 的全量运行记录为 `1587 passed, 1 failed, 3 deselected`。失败项在已有系统 SQLite 的 pytest 进程内直接启动 `/loop` 测试入口，触发产品的受控 DLL 门禁。把该测试移到新进程后，父进程预先导入系统 SQLite 的定向复验通过。保留原全量及单项复验回执，复用其它 1587 项结果与固定 wheel。[全量回执](raw/b03-release-full-fixed/stdout.bin) · [定向复验](raw/b03-release-loop-fixture/stdout.bin)

真实终端记录见[批次03](../../../batch-03.md)。用户完整体验归 77/78。产品验证使用合成输入和回环 HTTP，真实模型请求为零。
