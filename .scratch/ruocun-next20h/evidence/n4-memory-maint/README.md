# 32 记忆蒸馏与整理

领取基线 `39520c3686167274e738854b805b9b4551d921ef`，冻结 DAO `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`。本切片迁移 `memory/distill.ts` 的请求、候选解析，以及 `memory/consolidate.ts` 的计划解析、请求和作用域门槛。

蒸馏非 fork 排除系统消息，取渲染轨迹末 24000 个 UTF-16 单元，禁用思考。fork 保留主请求前缀及工具，末尾追加抽取指令。解析保留五类记忆、重要度门和目录噪声/秘密过滤。冻结普通入口走统一反思器，独立 `distill()` 来自调试与测试路径。真实保存轨迹验证由主线以合成响应接入。

合并模型只生成计划。三个作用域分别至少 12、15、20 条，间隔 3 天。请求用来源提示词、一个 user 消息、温度 0，坏结果或请求失败为空计划。

| 回执 | 结果 |
| --- | --- |
| [来源 red](raw/n4-32-pure-red/command.json) | 两模块缺失，收集失败 |
| [纯模块 green](raw/n4-32-pure-green/command.json) | 蒸馏 9 项及合并纯断言 12 项通过，0.16 秒 |
| [Ruff](raw/n4-32-pure-ruff/command.json)、[末次 mypy](raw/n4-32-pure-mypy-final/command.json) | 通过，mypy 2 源 |

首次 mypy 的两个数字字段收窄错误保留原回执。命令经白名单、私有 CPython 3.11 与合成模型回调运行，敏感扫描均为 false。

## 原生作用域发布与审计

存储端口采用独审放行的 `73fe495a04b6bf37ac2ab529f40d106c5824c0e3`，从集成 `8ef40a352ba448a1eaf62505547998854558038d` 消费。`maybeConsolidate` 读取 native active 记录和本作用域 marker，模型返回后核对 marker 和原条目的内容身份。合并旧记录时，只接受该原生作用域已知、未锁且 `source/sourceHash/origin` 一致的记录。实际 canonical 沿原键/标题定位，保留原始来源元数据。模型给出的 source 标签只存在于计划中。canonical 确认发布后才以原条目身份软取代旧记录，正文保留，`supersededBy` 指向实际 canonical 文件名。全部旧目标缺失且 canonical 为新条目时沿冻结纯新增，旧记录不参与变更。

已知冲突按实际确认计数。取消停止剩余修改，结果未知结束当前作用域且不重试或继续写 marker。模型空计划保留原数据并沿来源记录本次门槛时间。蒸馏与合并计划对拟保存的凭据字段作检查。`createMemoryAuditSink(sessionDir, env)` 写实际蒸馏和合并事件，使用总开关及独立 MEMORY 开关，合并理由经过脱敏。

冻结合并 17 项中后 5 项用已审 Windows 原生存储验证计划写回与 marker。原写回用例还确认不同源与锁定条目字节保留。审计迁移本票涉及的 6 项，反思事件归后续票。

| 回执 | 结果 |
| --- | --- |
| [存储与审计 red](raw/n4-32-store-audit-red/command.json) | 待实现接口导致收集失败 |
| [蒸馏来源字段 red](raw/n4-32-distill-source-secret-red/command.json) | 原蒸馏用例检测到额外候选 |
| [完整模块 green](raw/n4-32-store-audit-green/command.json) | 32 passed in 0.83s |
| [Ruff](raw/n4-32-store-audit-ruff/command.json)、[mypy](raw/n4-32-store-audit-mypy/command.json) | 通过，mypy 3 源 |

源与候选工作区字节见 [source-members.json](source-members.json)。所有回执仅用合成目录、响应和凭据，敏感扫描为 false。主线验收普通启动的 GC、非阻塞合并和真实已保存工具轨迹接线。

## 纯新增与未知发布回修

恢复冻结的缺失旧目标纯新增断言，候选持久字段仍经校验，模型的来源标签不落盘。既有 canonical 及混合已知和未知目标仍走保守判断。`maybeConsolidate` 只软停 `ToolRejected`，让未确认发布等异常到达入口，供其报告该作用域。本次通过同一门控用例注入真实存储会产生的未知发布错误类型，确认同域不再软取代旧条目，也不写 marker 或完成审计。该用例验证调用边界，实际替换后的旧正文保留由存储端口验证。

[两项 red](raw/n4-32-canonical-unknown-red/command.json) 后 [两项 green](raw/n4-32-canonical-unknown-green/command.json)，0.41 秒。[Ruff](raw/n4-32-canonical-unknown-ruff/command.json) 及 [mypy](raw/n4-32-canonical-unknown-mypy/command.json) 通过。初版字节记录保留，回修字节由本次提交固定。

## 同名 canonical 的恢复副本

从集成 `02189637cd45b7338b5544b1ad563f08a4739959` 消费已独审的存储恢复端口 `0ee5d7388935ba64d34d97a2cd282f5e6dc60a05`。合并仅在更新已存在的 canonical 时要求保留旧字节。原门控用例在独立合成作用域注入真实原子替换后的目录同步失败。异常回执确认替换已发生，恢复副本字节与原 canonical 完全一致，拟软取代条目保持原字节，marker 和完成审计均未写入。

[缺少恢复副本的 red](raw/n4-32-original-copy-red/command.json) 为 0.80 秒，[原用例 green](raw/n4-32-original-copy-green/command.json) 为 0.70 秒。[Ruff](raw/n4-32-original-copy-ruff/command.json) 与 [mypy](raw/n4-32-original-copy-mypy/command.json) 均通过，回执敏感扫描为 false。
