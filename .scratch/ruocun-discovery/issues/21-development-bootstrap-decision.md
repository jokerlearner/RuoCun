# 确定最小开发工程的已验证工具链

Labels: wayfinder:research
Mode: AFK
Status: resolved
Assignee: /root/decision_21_bootstrap
Branch: research/d21-bootstrap
Worktree: .worktrees/r21
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [验证 Python 安装与打包的最小闭环](07-python-distribution-experiment.md), [确定测试、回放与评估的复用门禁](11-test-replay-decision.md), [验证含 WAL 修复的 SQLite 运行环境](19-patched-sqlite-runtime-experiment.md)

## Question

哪些已验证的解释器、构建和开发入口选择，已足以让实现03安装开发包并在仓库外调用版本/帮助，而不把完整平台沙箱和最终发布路线当作这个小切片的前置？

## 依据与边界

84张正式实现任务及全部功能范围保持不变。D07标准包/onedir和D11五入口已具独立证据；03只交付开发包、版本/帮助和offline最小验收，不宣称完整产品或最终安装验收。

旧03间接依赖D12→D10，导致基础工程也等待尚未满足的OS沙箱。工程依赖细化为03→本票，D12仍保留原D09/D10前置；沙箱60/61、Windows78、发布79–84和最终85的全部功能/证据要求保持。最终85仍受D14→D13→D12等完整地图门禁约束，不以本票关闭发布路线。

## 完成条件

- 确定首轮可实际使用的开发Python/Windows架构、构建后端与锁策略，引用D07/D19真实验证范围；首轮开发pin不冒充最终支持版本范围。
- 为已确认pytest、统一验收驱动、Ruff、mypy、build列出可执行配置原则/依赖候选及许可来源。工具精确版本需官方元数据或真实隔离安装验证，不凭回忆猜最新版。
- 明确src/ruocun与开发验收支撑包的可安装边界、资源/版本单源、仓库外验证方法；开发支撑依赖不进入用户标准包。
- 明确03的offline最小可运行路径与未落地suite的诚实状态；未来功能由既有任务加入，不能以空实现/固定成功占位。
- 既有源码/实验归档和原始证据不因lint/type配置而重写；质量检查覆盖实际迁移核心及明确维护的测试支撑。
- 输出供03直接读取的简短路线及必要机器可读pin；完整TUI、SQLite成品/恢复、沙箱、真实模型、最终安装/发布仍由原任务验证。

## Assets

- [标准包独立复核](../../../integration-evidence/d07/README.md)。
- [测试复用门禁](../research/11-test-replay-gates.md)。
- [固定SQLite运行库](../experiments/sqlite-runtime/README.md)。
- [最小工程路线](../research/21-development-bootstrap.md)、[精确pin及官方元数据](../research/21-development-bootstrap.pins.json)、[未执行安装探针请求](../research/21-development-bootstrap.attempt.json)。研究分支`research/d21-bootstrap`提交`eb8ea6a0b95597cc47704edaaa0aaf4867630cd5`保留未合并。

## Comments

- 2026-11-05：依据实测后的真实信息依赖拆分工程入口与全量发布前置；这是调度细化，不减少已确认范围，不把PSEC已知WRITE_DAC失败当作通过。本票解决后才调度03。

- 2026-11-05：三项前置均resolved，领取基础开发工具链研究；沿用既有标准包/来源测试证据，只补必要官方工具元数据，不重复大型系统实验。

## Answer

03采用首轮已验证CPython3.11.9/x64、Hatchling1.33.0、build1.6.1、pytest8.4.2；Ruff0.17.3/mypy2.4.1有固定官方元数据/Windows wheel证明，尚未在本票安装执行。新增完整锁、实际五入口、支撑distribution和仓库外产品验证由03落实；metadata pin不是完整可安装锁。

补充复合PowerShell安装探针启动前被自动审查blocked by policy拒绝，无细因、无实际进程/venv/redgreen，目标不存在，未等效重试。03须读拒绝记录，只执行本票已授权工程目的的可审查窄步骤；若仍被拒应停止该步并说明，不能隐藏失败或绕过策略。

五项入口、src布局、版本单源、独立开发支撑、offline真实case/未实现suite非零、维护范围与安装TDD已明确，无新增目标取舍。只解决开发工具链，不关闭12/10或最终85。
