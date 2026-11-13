# RuoCun 迁移决策地图

Labels: wayfinder:map
Status: resolved

## Destination

技术路线、兼容边界、测试入口和迁移顺序明确，足以生成可执行的完整迁移规格。
地图完成表示前置决策和必要验证均闭合；本轮建图不等于已到达终点。

## Notes

- 当前交付范围与执行方式已由[ADR-0010](../../docs/adr/0010-selected-scope-and-lean-workflow.md)修订，原完整规格/研究中的R1/R3/W3/W5/W6/D2/D3/V1/V2相关旧承诺以新决定为准。未关闭研究票状态保持，不把范围选择当研究或产品通过。
- 沿用 [CONTEXT.md](../../CONTEXT.md) 已确认的九项目标，仅在发现新的范围冲突时提问。
- 每次先读取 [wayfinder](C:/Users/PC/.codex/skills/wayfinder/SKILL.md)、[grilling](C:/Users/PC/.codex/skills/grilling/SKILL.md) 和 [domain-modeling](C:/Users/PC/.codex/skills/domain-modeling/SKILL.md)；本项目上下文格式按用户约定保留目标和边界。
- 来源冻结与首轮只读研究已完成。续跑按 frontier 认领下一项，执行该票必要的实验；每轮最多解决一项非研究子票，候选路线与用户取舍分开记录。
- 唯一参考为 [冻结快照 dao-f17e189-7ac654a0dc06](reference/README.md)，包含提交与本地覆盖层。后续调查和迁移不跟随活动 DAO 目录漂移。
- 研究使用本地 research/ 分支及独立 worktree；不推送，不开 PR，不合并研究分支。可追溯的研究报告收录到本地图目录，供后续 worktree 读取。
- 研究事实和建议分开记录；只有实际完成的检查才记为通过。终端选型依赖真实 Python 程序在 Windows Terminal 的输入、粘贴、中断和缩放实验。
- HITL 原型由用户提供体验反馈，代理不代填用户验收。已确定目标不重复进行 grilling。
- 实验使用独立工作区、合成配置/凭据和受控输入；涉及 Git 发现的场景建立自己的实验仓库边界，运行来源程序时不继承 RuoCun 主仓库或真实用户状态作为测试输入。
- 决策细节在子票的 Answer 和所链接研究资产中；此图仅索引一句话摘要。
- 子票位于 [issues/](issues/)；使用下列查询得到当前可领取问题，不在此重复维护开放票清单。
- 用户重点与任务的对应见 [调查与决策覆盖](coverage.md)；[任务依赖图](dependencies.md) 由 frontier.py 生成，当前领取状态以实时查询为准。
- 历史建图校验见 [validation.json](validation.json)；当前运行时实验校验见 [实验记录检查](experiments/runtime/validation.json)。两者均不代表产品测试或终端验收。
- [完整行为规格及附件](../ruocun/spec.md)按冻结研究综合。2026-11-12，D14 独立核对决定、覆盖和前置后完成地图收口。产品交付继续按实施进度及最终用户验收记录。

~~~powershell
python .scratch/ruocun-discovery/frontier.py
python .scratch/ruocun-discovery/frontier.py --json
python .scratch/ruocun-discovery/frontier.py --mermaid
~~~

## Decisions so far

- [确定终端框架与 Windows 平台适配方案](issues/10-terminal-windows-decision.md)：公共终端、Shell 和系统端口按已验路线适配。沙箱范围由 [ADR-0008](../../docs/adr/0008-source-first-sandbox-parity.md)确定，Windows 显式启用时拒绝。22 保留历史调查结果。

- [确定安装、打包与发布配套](issues/12-install-release-decision.md)：采用标准 Python wheel/sdist 与支持矩阵，依 [ADR-0010](../../docs/adr/0010-selected-scope-and-lean-workflow.md)手动停进程、备份和更新。
- [确定模块对应原则与迁移顺序](issues/13-module-sequence-decision.md)：按冻结 805 个成员保持模块职责，以实际依赖和可验行为安排迁移。
- [核验地图已足以生成完整迁移规格](issues/14-spec-readiness-check.md)：九项目标和八类调查重点均有归属与证据，已核对范围、依赖与真实验收边界。

- [用最小 Python 实验验证原生 ProcessContainer 隔离](issues/20-windows-psec-experiment.md)：Python原生路线可运行，但WRITE_DAC实测违反RO目标，完整backend不选定，交平台路线处理。
- [确定最小开发工程的已验证工具链](issues/21-development-bootstrap-decision.md)：首轮开发pin/支撑包/五入口边界已明确，解锁03，实际安装与测试仍由实现完成。

- [确定 Python 并发、任务与恢复技术路线](issues/08-python-runtime-decision.md)：单业务loop/专属DB线程/独立runner与IPC helper，按真实提交/停止和分类检查点恢复。
- [确定持久化与外部扩展的兼容边界](issues/09-storage-extension-decision.md)：唯一StoragePort与独立数据身份、显式只读兼容source map、各loader/协议边界已明确，产品仍须实测。

- [用最小 Python 探针验证 Windows 持久文件与 IPC 权限](issues/18-windows-durable-io-experiment.md)：文件/ACL/认证管道事实及pending所有权二次修正获18项独立复核，产品、断电和独立账户仍另验。

- [验证 Python 安装与打包的最小闭环](issues/07-python-distribution-experiment.md)：标准包与Windows onedir独立安装/生命周期通过，onefile策略拒绝保持未证实，交发布路线收口。

- [用最小 Python 探针验证 Windows 平台能力](issues/17-windows-capability-experiment.md)：原生系统候选与非等价边界已有实证，沙箱后续交ProcessContainer最小验证，人工仍最终集中。

- [确定测试、回放与评估的复用门禁](issues/11-test-replay-decision.md)：374项资产已有入口/处置/拥有任务，来源、产品、系统和最终人工门禁分别留证。

- [冻结可复现参考快照](issues/01-reference-snapshot.md)：后续以提交 f17e189 加完整本地覆盖层的冻结源码为统一参照。
- [查清完整功能、模块职责与运行时调用链](issues/02-function-runtime-research.md)：功能、工具/命令、模块与状态链已逐项登记，异构后台任务和不同入口须分别规格化。
- [查清 SQLite、配置与扩展兼容契约](issues/03-data-extension-research.md)：恢复依赖 SQLite 事务与执行身份，各配置和扩展通道分别有其发现、覆盖与协议子集。
- [查清终端与 Windows 缺口、测试资产及交付候选](issues/04-terminal-platform-delivery-research.md)：终端内联体验和真实系统能力须独立验证，测试/脚本/fixture 已按复用方式完整登记。
- [查清 Windows 系统能力与隔离后端的可行边界](issues/16-windows-capability-research.md)：已明确原生后端候选与前提，文件/网络隔离及其它系统能力按真实探针验证后定案。
- [用最小 Python 实验验证取消与崩溃恢复契约](issues/05-runtime-recovery-experiment.md)：局部取消、真实进程接管与事务恢复探针完成；文件/IPC 边界和已修复 SQLite 运行库已形成新前置验证。

- [用最小 Python 适配器验证扩展协议与兼容解析](issues/15-extension-protocol-experiment.md)：代表性11项真实协议/解析探针完成，来源重复副作用已促成ADR-0003；未验范围保留给产品门禁。

- [验证含 WAL 修复的 SQLite 运行环境](issues/19-patched-sqlite-runtime-experiment.md)：官方3.54.1候选通过真实故障/恢复及直接worker身份独立复验，发布产物仍须各自验证。

- [用真实 Python 终端实验确定输入与渲染路线](issues/06-python-terminal-prototype.md)：可运行候选与14项自动/进程技术复核收口；按ADR-0004剩余人工集中最终，不当作HITL全通过。

## Not yet specified

2026-11-10用户要求沙箱模仿DAO，见[ADR-0008](../../docs/adr/0008-source-first-sandbox-parity.md)；22以原A失败、额外目标被替代的结论收口，不是后端通过。12不再依赖额外Windows隔离实验；其他来源优先、已确认差异继续保留。

- 研究和最小实验可能暴露尚无法命名的输入层冲突、恢复竞态或原版未定义行为；出现后先判断现有问题是否覆盖，再建立准确的新问题。
- 已能明确表述的问题均已建票，具体依赖通过 frontier 查询，不在此重复列出。

## Out of scope

- 本轮的产品迁移实现和完整规格正文编写；此地图为其建立决策与证据基础。
- 旧 DAO 会话迁移，按 CONTEXT.md 已确认边界。
- 本轮 Linux/macOS 的实机验收；保留设计和后续验收要求。
- 推送研究分支、创建远程仓库和公开发布；本轮研究与分支保存在本地。

## 实施期验收时点调整

用户已确认[ADR-0004](../../docs/adr/0004-final-batch-human-acceptance.md)：技术验证和编码继续，剩余人工体验统一到最终77/78/85，保留已有反馈及未验项。
