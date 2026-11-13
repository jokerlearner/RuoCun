# 批次06集中构建 b06-r1

固定产品源码 `0a0c1cea71d9cc5ea3beb3db70f734242d70c8c0`。Windows x64 CPython3.11 wheel SHA256 `c2aac559110ec650f05df0abadfb5acccaa6b468ec0edb8e06297a06e215b6b1`。sdist重建wheel与直接wheel一致，Git/源码工作树/sdist/wheel/隔离安装中的 **285个产品成员逐字节一致**，实际SQLite3.54.1。[产物绑定](artifacts.json) · [绑定回执](raw/b06-final-bind/command.json)

44项运行依赖按官方hash锁在空环境离线安装、7grammar实际解析与pip check通过；主产品声明11项直接依赖。Node/TypeScript仅私有验证依赖，未加入产品运行闭包。[完整依赖来源](../dependencies/runtime-wheels.json) · [安装收据](../ordinary/README.md)

全仓Ruff、Mypy254个源码文件、四项离线冒烟与纯安装通过。[Ruff](raw/b06-final-ruff/command.json) · [Mypy](raw/b06-final-mypy/command.json) · [离线回执](offline-summary.json)

本批唯一默认全量实际 **`1641 passed, 3 deselected in 727.16s`**。产品从隔离wheel安装导入、仓外合成临时目录执行；默认3项oracle未选，不计通过。[全量回执](raw/b06-final-full/stdout.bin) · [实际导入路径](raw/b06-final-source/stdout.bin)。临时QA路径已移除，纯安装中pytest不可导入、产品路径与版本启动正常。[安装收尾](raw/b06-final-installed-clean/command.json)

五票的来源语义、普通入口及高风险独审均通过，详见[批次记录](../../../batch-06.md)。LSP真实TS九操作及编辑同步、迟到ID/限长/Job整树止写和普通会话资源交接分别有证据；API及协议不以只安装依赖或文案存在充当通过。

模型服务和网页验证均为本地合成，真实/付费模型调用为零。未新增真实Windows Terminal体验、其它平台实机或量化性能成绩；77/78完整人工出口仍pending。所有原失败与诊断保留，不覆盖历史。
