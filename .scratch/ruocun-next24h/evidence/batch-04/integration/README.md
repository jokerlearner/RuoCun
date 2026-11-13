# 批次04集中构建 b04-r1

固定产品源码 `dc3f76d175923fd74b099d7c9ed0b2cf9a8128d1`。Windows x64 CPython 3.11 wheel SHA256 `a0938b766c7fea6d6907c88d7ff7e216bd62c6375ec79ed048d013831da8e5a3`。同一次里程碑构建产出 sdist 与 wheel，直接构建 wheel 的哈希一致。Git、sdist、wheel 与隔离安装的 253 个产品成员逐字节一致，实际 SQLite 为 3.54.1。[产物绑定](artifacts.json)

锁定运行依赖离线安装，`pip check`、四项离线冒烟、全仓 Ruff 及 230 个源码文件的 Mypy 检查通过。[离线回执](offline-summary.json) · [Ruff](raw/b04-final-ruff-fixed/command.json) · [Mypy](raw/b04-final-mypy-fixed/command.json)

从隔离 wheel 安装导入产品，在仓库外的合成临时目录执行一次默认全量回归。实际 `1602 passed, 3 deselected`，耗时 690.04 秒。借用的测试依赖路径已移除，安装产物仍可用。[固定包导入路径](raw/b04-final-source/stdout.bin) · [全量回执](raw/b04-final-full/stdout.bin)

定向测试和独审使用合成工作区及回环 HTTP。真实模型请求为零。本批未跑冻结 DAO 的同机性能对照。77/78 的整体体验单列。[批次记录](../../../batch-04.md)
