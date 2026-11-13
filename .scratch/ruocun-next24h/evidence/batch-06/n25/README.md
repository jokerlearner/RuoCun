# 25 Config候选

冻结来源src/tools/config.ts:1–109和src/index.ts:2239–2240。来源无单独config.test.ts，本票沿handler/普通入口既有seam迁移参数、配置结果和重开断言，未创建新的通用故障矩阵。

Config为plan/auto/deferred，读project??user，false/0/空串有效、null回落；不读取enterprise/local。文案修正原描述优先级与实际实现矛盾，保留源码来源。只写原生用户settings.json，兼容来源只读，泛点路径保留无关字段；坏JSON/非对象路径按ADR-0013拒改，不用源catch{}丢弃旧信息。整段RMW用现有path lock，Windows沿PrivateDirectory/atomic_publish，不能把返回文案当持久确认。

权限、checkpoint只在其真实启动调用点读；源Config不热重载权限模式，theme保存值也不决定启动颜色。/Config大写只显示当前实际状态，不调用pause或模型。不擅自实现“下一轮立即热生效”。

现有JSON Schema窄校验补anyOf，供原Config的string/bool/number union；拒绝object/null参数。单条来源测试覆盖写回/覆盖/已知校验/通用点路径/损坏原字节保留。b06-config-red为缺模块真实红；green为导入名错误、green-r2为夹具缺HOME父目录，不记来源行为绿；green-r3原用例通过。check最初引用不存在的test_schema.py，仅收集错误；check-r2复用注册/参数相关组，实际13 passed。Mypy235源码与Ruff通过。所有回执白名单、合成HOME/配置，scan_hit=false，无真实或付费模型。

普通CLI持久会话接线和独立复核尚待实际回执，不据此结题。批末全量/构包集中执行。

后续固定集成已完成，[独立复核](../../review/b06-config-review.md)通过；历史候选记录及原红保留，整票及里程碑结果读取[批次记录](../../../batch-06.md)。
