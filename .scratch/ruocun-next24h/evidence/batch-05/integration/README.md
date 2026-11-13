# 批次05集中构建 b05-r1

固定产品源码 `c85b80d5677236523d61998bdf58ecf4d4a9c96e`。Windows x64 CPython 3.11 wheel SHA256 `d8de9d7d0ffa17b58799fec993ebfc8dc7f6bfa7cdf0dea4f6afb80387fa8663`。同一次里程碑构建产出 sdist 与 wheel，直接构建 wheel 的哈希一致。Git、sdist、wheel 与隔离安装的 **262个产品成员逐字节一致**，实际SQLite为3.54.1。[产物绑定](artifacts.json) · [绑定回执](raw/b05-final-bind/command.json)

运行依赖按37项官方hash闭包离线安装，固定SDK1.30.0、Pydantic2.14.2/core2.50.2，`pip check`通过。[依赖来源](../dependencies-fixed/wheels.json) · [实际安装/导入](../ordinary/README.md) · [原始未采用依赖](../dependencies/README.md)

全仓Ruff、231个源码文件Mypy及四项离线冒烟通过。[Ruff](raw/b05-final-ruff/command.json) · [Mypy](raw/b05-final-mypy/command.json) · [离线回执](offline-summary.json)

从隔离wheel安装导入产品，在仓库外合成临时目录执行本批唯一一次默认全量回归，实际 **`1621 passed, 3 deselected in 737.20s`**。默认3项oracle未选，不计为通过。[全量回执](raw/b05-final-full/stdout.bin) · [固定包导入路径](raw/b05-final-source/stdout.bin)。测试临时借用路径已移除；纯安装中产品路径仍正确、pytest不可导入，标准命令版本正常。[纯安装收尾](raw/b05-final-installed-clean/command.json)

26、46、51–54逐票定向和高风险独审均已通过，见[批次记录](../../../batch-05.md)。SDK日志脱敏与未知结果保留有真实副作用/SQLite证据；不把连接重连当作工具重做授权。集成时发现的维护stamp启动回归，其原红、区分性诊断和修复后两项原用例结果见[共享证据](../ordinary/README.md)。没有覆盖或删除原失败。

全部模型服务均为本地合成服务，没有付费/真实模型调用。本批没有新增真实Windows Terminal体验或冻结DAO同机性能成绩；77/78完整人工出口仍pending。
