# 迁移决策任务依赖图

本图由子票依赖生成，当前状态以 frontier.py 实时查询为准。箭头从前置问题指向后续问题；研究或实验解决不等于产品验收通过。

~~~mermaid
flowchart TD
  n0["冻结可复现参考快照 · resolved"]
  n1["查清完整功能、模块职责与运行时调用链 · resolved"]
  n2["查清 SQLite、配置与扩展兼容契约 · resolved"]
  n3["查清终端与 Windows 缺口、测试资产及交付候选 · resolved"]
  n4["用最小 Python 实验验证取消与崩溃恢复契约 · resolved"]
  n5["用真实 Python 终端实验确定输入与渲染路线 · resolved"]
  n6["验证 Python 安装与打包的最小闭环 · resolved"]
  n7["确定 Python 并发、任务与恢复技术路线 · resolved"]
  n8["确定持久化与外部扩展的兼容边界 · resolved"]
  n9["确定终端框架与 Windows 平台适配方案 · resolved"]
  n10["确定测试、回放与评估的复用门禁 · resolved"]
  n11["确定安装、打包与发布配套 · resolved"]
  n12["确定模块对应原则与迁移顺序 · resolved"]
  n13["核验地图已足以生成完整迁移规格 · resolved"]
  n14["用最小 Python 适配器验证扩展协议与兼容解析 · resolved"]
  n15["查清 Windows 系统能力与隔离后端的可行边界 · resolved"]
  n16["用最小 Python 探针验证 Windows 平台能力 · resolved"]
  n17["用最小 Python 探针验证 Windows 持久文件与 IPC 权限 · resolved"]
  n18["验证含 WAL 修复的 SQLite 运行环境 · resolved"]
  n19["用最小 Python 实验验证原生 ProcessContainer 隔离 · resolved"]
  n20["确定最小开发工程的已验证工具链 · resolved"]
  n21["验证受限primary token与PSEC能否补齐元数据隔离 · resolved"]
  n0 --> n1
  n0 --> n2
  n0 --> n3
  n1 --> n4
  n2 --> n4
  n3 --> n5
  n3 --> n6
  n1 --> n7
  n2 --> n7
  n4 --> n7
  n17 --> n7
  n18 --> n7
  n2 --> n8
  n4 --> n8
  n14 --> n8
  n17 --> n8
  n18 --> n8
  n3 --> n9
  n4 --> n9
  n5 --> n9
  n16 --> n9
  n19 --> n9
  n1 --> n10
  n2 --> n10
  n3 --> n10
  n14 --> n10
  n3 --> n11
  n6 --> n11
  n9 --> n11
  n8 --> n11
  n7 --> n12
  n8 --> n12
  n9 --> n12
  n10 --> n12
  n11 --> n12
  n12 --> n13
  n2 --> n14
  n3 --> n15
  n15 --> n16
  n4 --> n17
  n15 --> n17
  n4 --> n18
  n16 --> n19
  n6 --> n20
  n10 --> n20
  n18 --> n20
  n9 --> n21
  n19 --> n21
  n16 --> n21
~~~
