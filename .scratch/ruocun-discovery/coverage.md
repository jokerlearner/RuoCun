# 调查重点与决策覆盖

本表只关联用户重点与具体决策任务，不代替任务中的研究结论和验收证据。

| 用户重点 | 来源调查 | 必要最小验证 | 路线收口 |
| --- | --- | --- | --- |
| 完整功能、职责和调用关系 | [查清完整功能、模块职责与运行时调用链](issues/02-function-runtime-research.md) | 涉及状态边界的行为纳入运行时实验 | [确定模块对应原则与迁移顺序](issues/13-module-sequence-decision.md) |
| 原模块到 Python 的对应原则 | [查清完整功能、模块职责与运行时调用链](issues/02-function-runtime-research.md) | 由依赖替换风险决定是否新增小实验 | [确定模块对应原则与迁移顺序](issues/13-module-sequence-decision.md) |
| 终端及 Windows 输入、粘贴、中断、缩放 | [查清终端与 Windows 缺口、测试资产及交付候选](issues/04-terminal-platform-delivery-research.md) | [用真实 Python 终端实验确定输入与渲染路线](issues/06-python-terminal-prototype.md) | [确定终端框架与 Windows 平台适配方案](issues/10-terminal-windows-decision.md) |
| 流式、调度、后台、取消和恢复 | [查清完整功能、模块职责与运行时调用链](issues/02-function-runtime-research.md) | [用最小 Python 实验验证取消与崩溃恢复契约](issues/05-runtime-recovery-experiment.md) | [确定 Python 并发、任务与恢复技术路线](issues/08-python-runtime-decision.md) |
| SQLite、配置和扩展协议 | [查清 SQLite、配置与扩展兼容契约](issues/03-data-extension-research.md) | [取消与崩溃恢复实验](issues/05-runtime-recovery-experiment.md)、[扩展协议与兼容解析实验](issues/15-extension-protocol-experiment.md) | [确定持久化与外部扩展的兼容边界](issues/09-storage-extension-decision.md) |
| 原测试、回放及评估工具复用 | [查清终端与 Windows 缺口、测试资产及交付候选](issues/04-terminal-platform-delivery-research.md) | 测试入口分别标记本地、系统、模型/网络及人工依赖 | [确定测试、回放与评估的复用门禁](issues/11-test-replay-decision.md) |
| Windows 缺口及对应实现 | 三份源码研究及 [Windows 系统能力与隔离后端研究](issues/16-windows-capability-research.md) | 真实进程与恢复实验、真实终端原型、[Windows 平台能力探针](issues/17-windows-capability-experiment.md) | [确定终端框架与 Windows 平台适配方案](issues/10-terminal-windows-decision.md) |
| 安装、打包及发布 | [查清终端与 Windows 缺口、测试资产及交付候选](issues/04-terminal-platform-delivery-research.md) | [验证 Python 安装与打包的最小闭环](issues/07-python-distribution-experiment.md) | [确定安装、打包与发布配套](issues/12-install-release-decision.md) |

所有路线汇入 [确定模块对应原则与迁移顺序](issues/13-module-sequence-decision.md)，最后由 [核验地图已足以生成完整迁移规格](issues/14-spec-readiness-check.md) 逐项检查 CONTEXT.md 九项目标。

取消与恢复实验已完成。[Windows 持久文件与 IPC 权限验证](issues/18-windows-durable-io-experiment.md)及[含 WAL 修复的 SQLite 环境验证](issues/19-patched-sqlite-runtime-experiment.md)均已独立复核，相关条件已纳入运行时、存储和标准包路线。

D14 已核对八个调查重点及九项目标的追踪关系。具体决策状态以子票及 frontier.py 为准。[D14 核验](research/14-spec-readiness.md)
