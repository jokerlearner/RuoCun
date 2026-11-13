# 30 共享持久写边界独审

固定 `57c551b7d5746754e1680ba385a0b2ec689bcad7`。`Tool.persistentEffect` 默认关闭。批执行用同一判定排空安全组、独占派发并确认 `intent.effect=True`，处理器未知异常沿原有停止路径。DurableStore 继续用现有副作用标记阻止未知状态下的写操作。原 capability 保持权限和 plan API 语义。Bash 失败继续阻止后续 write/exec，期间执行持久 plan 不会清掉已失败状态。

独立复用原安全组和写入屏障用例，`1 passed in 0.24s`。实测合成持久 plan 开始时活跃读为零，意图记录为副作用。回执 `raw/review-30-persistent-effect01`。使用既有私有 Python 3.11、白名单与合成配置，未命中秘密扫描。共享接缝可消费，MemoryWrite 模块和普通入口待后续独审。
