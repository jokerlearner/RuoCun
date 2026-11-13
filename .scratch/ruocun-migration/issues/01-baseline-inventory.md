# 01 — 核实迁移基线并完成覆盖盘点

Type: research
Status: blocked
Blocked by: .scratch/ruocun-discovery/issues/14-spec-readiness-check.md
用户体验验收：not-required

## 工作内容

- 对基准提交逐项盘点模块、工具、命令和扩展入口。
- 单独审查已登记的本地覆盖层。
- 提交本地改动的继承建议，供用户决定。
- 核对模块对应表和验收矩阵的遗漏。
- 根据依赖关系生成独立实施任务票。
- 形成 Python 工具链及语言绑定依赖的选型建议。

## 完成条件

- 功能、模块和关键行为均能追溯到来源。
- 本地覆盖层均有处理决定，未决项明确列出。
- 每个迁移域均关联验收项。
- 后续实施任务具有输入、前置条件和完成标准。

## 验证证据

待执行。

## 相关记录

- [迁移规格](../spec.md)
- [迁移基线](../../../docs/migration/baseline.md)
- [模块对应表](../../../docs/migration/module-map.md)
- [验收矩阵](../../../docs/migration/acceptance-matrix.md)

## Comments

- 2026-11-05：工程初始化时建立本票。尚未开始执行，工作流配置完成不代表本票已解决。
- 2026-11-05：用户启动 [RuoCun 迁移决策地图](../../ruocun-discovery/map.md)。来源盘点、兼容调查和技术路线统一在新地图开展，本票暂不并行领取；地图完成后再核对本票剩余交付，不因建图自动标记解决。
