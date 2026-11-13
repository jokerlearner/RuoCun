# RuoCun 架构整理记录（2026-11-13）

当前状态：两项内部整理完成；定向测试、独立复核、构包和仓外安装通过。完整回归首轮1685通过、3失败，原3项随后定向复验全部通过；不是一次全量全绿。

## 范围和结果

用户在阅读临时架构报告后授权：代理认为值得修改的项目可以调用合适技能完成。
本轮选择报告 01、02，保持现有行为；报告 03（输出裁剪）和 04（子 MCP 生命周期）暂缓。
需求、验收与唯一文件归属见 [spec.md](spec.md)。

1. **普通子代理检查点**：在既有 agent/resume_agent.py 集中候选转录、恢复材料剩余轮次和 inbox 清空的联动构造。同步和后台 owner 仍各自保留锁、停止许可、脱敏、身份比较字段、turnLimit、失败处理，以及提交确认后再更新内存的顺序。没有改存储 schema 或 MCP 生命周期。
2. **原生 JSON 文件**：新增 config/native_json.py，通用对象读取保护不再寄居账户实现；设置和 MCP 复用私密目录作用域与发布流程。账户原导出名字保留，账户格式、POSIX 保存差异、设置锁及 dotted path、MCP 目标限定和校验时点保持。

验证中另修复一个既有夹具的不一致：test_mvp_product.py 的模拟维护服务仍匹配旧提示词，当前 memory/consolidate.py 已在本轮开始前改用新文本。只同步请求识别子串，未改产品提示或任何断言；82个assert的AST逐一相同，见 [断言保留核对](evidence/fixture-preservation.json)。这不是新增测试用例。

收益是共同规则只维护一份。检查点小切片净增14行（含说明），没有以减少总行数为质量门槛，也没有继续引入策略参数袋或通用框架。

## 独立复核

- Standards：独立审查最终差异，0项发现；共同候选确有规则组装，原生 JSON 作用域确有资源生命周期，均非纯转发。
- Spec：独立逐分支核对F1/F2，0项行为偏差；消息别名、前后台身份字段差异、读写平台判断、发布错误与未知结果传播保持。
- 独立高风险复跑：4个既有文件，15 passed，21.99s，exit=0，scan_hit=false。
- 两名实现者不审自己的候选；复核未修改源码。

## 实际验证

所有测试、构建及安装命令经现有 tools/run.py 的明确环境白名单启动。
HOME/USERPROFILE、配置、TEMP、会话与安装目录均指向本轮合成位置；没有真实模型请求或个人凭据操作。
原始命令回执与stdout/stderr见 [evidence/](evidence/)。

| 检查 | 实际结果 | 回执 |
| --- | --- | --- |
| 改前子代理快照 | 19 passed，31.22s | [agent-baseline](evidence/agent-baseline/command.json) |
| 改前配置快照 | 29 passed，21.03s | [config-baseline](evidence/config-baseline/command.json) |
| 改后子代理 | 19 passed，28.94s | [agent-after](evidence/agent-after/command.json) |
| 改后配置 | 29 passed，20.51s | [config-after](evidence/config-after/command.json) |
| 独立高风险 | 15 passed，21.99s | [independent-critical](evidence/independent-critical/command.json) |
| Ruff | 最终通过；首次仅tasks.py导入换行失败，原记录保留 | [最终](evidence/cleanup-ruff-final/command.json)、[首次](evidence/cleanup-ruff/command.json) |
| mypy | 7个改动源码检查通过 | [cleanup-mypy](evidence/cleanup-mypy/command.json) |
| 标准包 | sdist→wheel构建通过 | [cleanup-build](evidence/cleanup-build/command.json) |
| 仓外干净安装 | 离线锁定运行依赖、pip check、版本/帮助及311成员字节绑定通过 | [安装门禁](evidence/cleanup-installed-gate/command.json)、[字节核对](evidence/installed-origin/stdout.bin) |
| 源码默认完整回归首轮 | 1685 passed、3 failed、4 deselected，518.46s | [首轮命令](evidence/cleanup-source-full/command.json)、[JUnit](evidence/full-first-junit.xml) |
| 原3失败在新包QA定向复验 | 3 passed，19.06s | [最终复验](evidence/installed-failures-final/command.json) |
| 夹具Ruff | 通过 | [cleanup-ruff-fixture](evidence/cleanup-ruff-fixture/command.json) |

轮次与耗时来自两次不同测试运行，不作为性能收益证据。
所有已归档回执的秘密扫描为false。首次Ruff失败及完整回归原失败均保留，没有回填通过。

## 完整回归失败的处理

- 包元数据：源码测试所用开发venv仍安装旧产品METADATA，仅列3个运行依赖。当前新wheel已绑定完整依赖；在新包QA环境中原断言通过，未修改元数据断言或开发venv。
- 维护事件超时：保持源码布局的改前快照也在 maintenance_started.wait(8) 失败。独审核对到夹具的旧提示词识别不匹配本轮之前已有的提示改动。同步识别文字后，原来的消息、拒绝、重开、并行维护与等待时限断言在新包中通过。
- Shell detach身份失败：完整回归首轮失败；改前保持src布局定向复跑与新包QA两次定向复跑均通过。没有改Shell或IPC代码。首次控制错误的具体根因未证实，不把“复验通过”描述为已定位并修复该根因。
- 首次在长合成路径的新包复验中，MVP还出现runner启动超时；原回执保留。最终使用全新较短合成根运行原3项全部通过。未延长超时、删除断言或改写产品返回值。
- 新包QA从本轮已核实的纯安装复制到单独目录，仅补入现有开发环境的pytest框架库和测试support；原纯安装保持。QA产品来源断言指向自身site-packages。脚本与所有原始回执在 evidence/verification-scripts 和相应label目录中。

## 产物与改动保护

- 起点分支：integration/ruocun-migration，HEAD 00a1c78dc2e1e4e837fc39ed43dbfcd1c3979c04，消费当前既有未提交改动。
- 在本轮修改前保存14,259个已跟踪现存文件的SHA-256；本轮写入白名单为六个已有源码文件、一个夹具文件、新的原生JSON内部模块和本目录记录。没有覆盖其它既有产品改动。
- 最终核对发现本轮之外的并发文档变化：CONTEXT.md、ADR-0019、沙箱研究目录与diagram目录。已读取新ADR确认不改变当前产品契约，原样保留，详见范围回执的external字段；未误归入本轮实现。
- 本轮wheel SHA-256：0e8cdbbdbf312214315c90d5e1700b8e3e94b244aa9354241ba9ecc9ce7bcfbd。已比对七个改动成员与源码字节相同，见 [范围与绑定](evidence/scope-check.json)。
- 仓外产物与合成QA状态保存在 C:\Users\PC\AppData\Local\Temp\ruocun-architecture-edit-20261113，未替换用户日常安装。
- 当前未提交Git；不将用户其它未提交变化混入本轮。
- 本轮没有改变终端交互，未新增真实Windows Terminal体验验收；原79/79迁移记录不被本轮重写。
