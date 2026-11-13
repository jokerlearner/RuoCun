# B-r3 固定包与最终增量验证

状态：R3构包、独立安装、314成员绑定、工程静态和source-free T06＋Todo独审通过；整个B方案验收由主协调统一结题，真实终端体验单列待用户反馈。
日期：2026-11-13。纯安装与QA均为仓外独立环境；无真实模型质量或Windows Terminal人工通过结论。

## 来源与差异

- [R3输入清单](t07-r3-inputs.json)来自正式冻结工作区，指纹`5f530430e385fef8b05837f06165d5c8cdd3c308cc70c87bdd52bfcab0744486`；冻结副本为`D:\rcb-dd7453\r3`。
- 对R2全部受控输入逐项比对，唯一产品差异为`src/ruocun/agent/context_runtime.py`。保留R2已确认的四行导出父容器修复，没有新增模块/依赖或改锁。
- R3增加共用`_pinnedTodos`：重开后从当前投影恢复最后有效任务pin；明确成功的`TodoWrite([])`继续表示清空，不复活旧任务。压缩和模型切换两入口共同消费。
- 该US09缺陷由真实两进程CLI独审红绿确认，原[red](reviewer-todo-red/command.json)、[green](reviewer-todo-green/command.json)保留。
- R1默认全量[f2](f2/command.json)实际1734 passed、1 failed、4 deselected，唯一失败为新增原生命令后的旧catalog总数；原52条来源保留并定向修正。未重跑无关全量，不冒称R3另一次全量通过。
- R2导出/catalog/package/私有文件受影响安装定向由[r2-target](r2-target/raw/r2-catalog-export/command.json)保留；R3只按上述单文件差异复用未受影响证据。

## 构包与安装身份

[314成员绑定](t07-r3-artifacts.json)、[绑定命令](t07-bind-r3/command.json)、[交付副本摘要](t07-r3-deliverables.json)、[最终SHA复验](t07-r3-final-sha.json)。根源码、冻结副本、sdist、重建wheel和实际pure-r3安装逐成员相同；直接wheel与sdist重建wheel的SHA相同。
根受控输入在发布副本前再次核对，无漂移。三份许可证、metadata依赖、Windows包标签及实际SQLite3.54.1受控运行库均通过。

| 本地交付文件 | SHA-256 |
|---|---|
| `dist/compaction-b-r3/ruocun-0.1.0.dev0-py311-none-win_amd64.whl` | `3b34d7366716c4ec14fd01ef2b629cf26ef84aa11273ac513012b3fb2808baa4` |
| `dist/compaction-b-r3/ruocun-0.1.0.dev0.tar.gz` | `1b5c2e84506fe7f66e38ad7761b95afa616fbeb00635fa4f11168fa555d300c6` |

- pure-r3：`D:\rcb-dd7453\pure-r3\Scripts\python.exe`，仅runtime哈希依赖及R3 wheel，无pytest；[pipcheck](t07-pure-r3-check/command.json)通过。
- qa-r3：`D:\rcb-dd7453\qa-r3\Scripts\python.exe`，同锁开发依赖和实际非editable测试支撑；[pipcheck](t07-qa-r3-check/command.json)通过。
- R1/R2包、安装环境及失败回执原样保留；未覆盖仓库`.venv`或全局安装。

## 本候选实际执行项

- [安装包controller 13 passed](t07-r3-controller/command.json)，包括重开pin保留与显式空任务不复活的参数化用例。此入口用QA-r3 `-I -m pytest`，没有src注入。
- [全仓Ruff](t07-r3-ruff/command.json)、[Mypy](t07-r3-mypy/command.json)通过。
- [manual helper全新工作区预制](t07-r3-manual-prepare/command.json)通过，没有预建`.ruocun`；该模式不启动真实终端，不记录视觉/缩放通过。
- [仓外source-free独审r3x](r3x/command.json)：原两进程T06两案＋Todo恢复/显式清空组合，实际3 passed，产品严格pure-r3 Python `-I -m ruocun`，basetemp=`D:\rcb-dd7453\review-r3`。不复跑无关全量。
- [最终独立指纹](reviewer-r3-final-fingerprints.json)：根323个受控包输入全部匹配R3，27个受审产品文件与pure-r3安装一致，输入指纹与本页相同。
- 较早长basetemp组合中，Todo的clear场景曾在DB初始化前遇到路径长度环境失败，未发送模型；原失败保留为reviewer-r3-installed，短标签r3i三项通过，最终只采用上述仓外r3x回执，不冒充删除失败或Todo逻辑回归。

## 体验与结论边界

真实模型摘要质量、供应商缓存命中与最终Windows Terminal交互/缩放继续按实际结果单列。以上为固定候选的自动技术证据，不能替代用户体验验收。
