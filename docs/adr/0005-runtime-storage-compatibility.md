# ADR-0005：单业务循环、独立持久执行与兼容数据边界

Status: Accepted
账户与扩展来源装配已由 [ADR-0018](0018-native-configuration.md) 更新。存储、执行与恢复契约继续适用。
恢复增强中R1/R3按[ADR-0010](0010-selected-scope-and-lean-workflow.md)收缩；单业务循环、唯一StoragePort、事务与数据隔离决定保持。
日期：2026-11-05
决定来源：既定迁移目标内的D08/D09技术路线研究，及D05/D15/D18/D19实验与独立复核。研究分支本地保留，不合并。

## 背景

取消Python等待不能停止线程副作用；原生管道材料必须活到真正完成；controller退出与后台执行保留是不同生命周期。来源模块职责应保持，RuoCun自身恢复完整，同时不能让DAO和RuoCun共享活会话或误写旧数据。

## 决定

- 采用单asyncio业务循环、每会话专属SQLite串行线程、独立Shell runner/Job。裸Win32 IPC放在受监督transport helper，原生未知状态不导致UI或执行权威runner自杀。
- 业务取消、真实停止、结果提交与消息确认分开。进程/句柄绑定身份；流generation、数据库owner fencing和runner控制epoch各有职责，不混用。
- 固定SQLite候选采用已验证的官方3.54.1 DLL+标准库组合，不静默退回未达门禁的运行库；每种解释器/产物都须验证实际组合。
- 持久化有session DB与runner本地收据两个原子域，通过身份、幂等导入与确认协调，不宣称跨文件分布式原子提交。
- RuoCun使用独立原生数据/配置/凭据身份；兼容配置和扩展按用户原生compatibility.json的显式只读声明装载。各loader原有顺序与格式单独保持，旧keyRef按准确来源只读解析，写入和删除只影响原生数据。
- 自身会话使用明确产品标识与独立版本；旧DAO会话不导入。未知副作用和材料不足不自动重放或伪装成普通代理继续。

## 唯一契约与实施依据

- [运行时角色与顺序](../../.scratch/ruocun-discovery/research/08-python-runtime-route.md)，研究提交`e4fd721b1bc670325591e72108e1796d1015a07c`。
- [StoragePort、schema、三epoch与兼容source map](../../.scratch/ruocun-discovery/research/09-storage-extension-route.md)，研究提交`5415b2520228b08e4b2e5b4c942537b14fa7f9eb`。具体字段/签名仅在此维护；实际编码声明从单一模块导入，不在并行分支重造。

## 后果与限制

不选择全线程或全进程Agent来替换来源架构。后台类别按实际检查点分别恢复，文件/数据库提交边界有显式未知状态。只读兼容源与原生写回需要保留provenance；配置关闭通道、Hook结果/权限最终参数及协议子集不可由通用合并器改变。

这些是可实施路线，不是产品通过。MCP跨origin redirect、JS RegExp/UTF16、IPC边界、最终SQLite产物和全部恢复路径仍由现有任务实测。Windows沙箱路线及完整发布仍未关闭；人工体验按ADR-0004最终集中。

后续收口：Windows沙箱按ADR-0008沿用DAO已有支持边界，额外后端目标已替代；发布路线由D12收录，产品79–83仍待实施。测试投入按ADR-0009来源基线；上述运行时/数据契约继续有效。
