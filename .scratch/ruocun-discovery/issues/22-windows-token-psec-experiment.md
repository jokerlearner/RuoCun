# 验证受限primary token与PSEC能否补齐元数据隔离

Labels: wayfinder:task
Mode: AFK
Status: resolved
Assignee: /root/decision_22_token_psec
Branch: impl/d22-token-psec
Worktree: .worktrees/i22
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [确定终端框架与 Windows 平台适配方案](10-terminal-windows-decision.md), [用最小 Python 实验验证原生 ProcessContainer 隔离](20-windows-psec-experiment.md), [用最小 Python 探针验证 Windows 平台能力](17-windows-capability-experiment.md)

## Question

普通用户下，公开的受限primary token能否与PSEC启动属性实际组合、保留两层限制并拒绝已确认的outside owner/DACL修改，同时仍允许必要工具和允许目录写入？

## 依据与边界

[D10最小方案](../research/10-terminal-windows-route.md#73-推荐的无安装最小验证任务本轮不执行)、[D20已知失败](../../ruocun/integration-evidence/d20/README.md)。没有官方组合保证，不把LPAC不支持推成所有token组合禁止，也不把单删privilege当owner限制。

只操作自有合成目录、私有token/Job/stdio/desktop；不修改主机设备/运行库/默认桌面ACL，不加全局权限、账户、服务、驱动或防火墙规则，不使用SANDBOX_INERT/禁用代码完整性来使启动成功。子进程白名单及合成HOME，0真实模型/秘密。

## 完成条件与停止规则

1. **A 兼容判别**：普通token与WRITE_RESTRICTED对照，用固定cmd/Python；同一明确受限配置尝试一次组合启动。standalone失败是对照，不因它单独失败省略本题唯一组合观察；组合启动失败、限制丢失或需要更改宿主资源即停。不得flag穷举或扩大ACL直到能跑。
2. 实际worker查询TokenUser/Owner/Groups/RestrictedSids/Privileges/IntegrityLevel/MandatoryPolicy/AppContainer SID及PID/start，证明请求限制确实保留；不凭API返回true断言。
3. **B 已知缺口**仅在A通过后执行：workspace/tmp数据写成功；outside原同用户owner条件不变，WRITE_DAC单独/混合mask、WRITE_OWNER及实际无害随机SID的FR ACE变更分别host正对照/读回/恢复。任一实际元数据修改成功为FAIL，不能用改outside owner/DACL掩去已知条件。
4. **C 最少回归**仅A/B通过后：真实后代token+PSEC继承、Python/Git/PS、junction、net/no-net一组宿主/自身回环、retained handle/Job取消与环境close。只解锁产品候选，不能代替60/61/78实际产品门禁。
5. 原D17/D20证据保持原字节；记录精确绑定/错误/实际token、red/green或明确失败/未运行及资源清理。若A/B失败，交可审查的外部条件/备选建议；不能称所有Windows后端不可能或直接降级。

## Assets

运行资产置于`experiments/token-psec/`；主代理统一状态及矩阵。本票调查完成也不等于目标已达到，必须分别记录。

## Comments

- 2026-11-10当前收口：用户新要求模仿DAO沙箱，已由[ADR-0008](../../../docs/adr/0008-source-first-sandbox-parity.md)替代额外Windows原生隔离目标。本票状态resolved表示失败调查与范围取舍已收口，**A仍FAIL、B/C未运行，不是隔离后端通过**。产品60及发布路线12撤销本票的旧新增目标依赖；原始证据和停止要求保持，禁止恢复组件/VM/组合探针。

## Answer

现有PSEC/restricted token组合未满足原严格A（MandatoryPolicy 3→1），不能用该候选提供完整隔离。独立失败诊断及纯数据重放已收录，精确内部原因和完整等效未证实；见[诊断报告](../research/22-sprint-diagnosis.md)。用户随后明确按DAO实际机制迁移，DAO只有可选macOS/Linux后端、Windows不支持，故ADR-0008撤销新增Windows后端及管理员组件/VM评估。调查完成与产品支持边界分别记录；未产生任何产品沙箱通过结果。

- 用户后续明确选择接受额外组件并先在可回滚Windows环境验证，已记[ADR-0007](../../../docs/adr/0007-windows-sandbox-prerequisite.md)。新前提不修改本票A失败，也不授权日常宿主安装或新flag穷举；先确定候选及测试环境，D12/60/61门禁保持。

- 2026-11-10冲刺诊断：研究候选`5fae2aa723296b46bc984dcb7ac9e20761967cb6`已收录[报告](../research/22-sprint-diagnosis.md)及纯数据重放，未整分支合并。独立审查者核对旧34/34、新25/25资产hash；白名单独立合成HOME的archive/minimal重放均红（3→1、缺位2），detector/inspection通过，未执行真实PSEC/ACL/网络探针。现只能定位观测边界，不能证明内部确切根因或完整行为等效，A仍失败，B/C未运行。两条后续条件见报告；需用户决定是否接受管理员预装签名driver/service/WFP的产品前提，这与原普通用户安装契约有冲突。等待该决策期间不扩大实验或解锁依赖。

- 2026-11-10 Codex 独立静态复核：候选原始材料及复核记录已收录至集成提交 `a7b28f4`，见 [独立复核](../../ruocun/integration-evidence/d22/README.md)。A 失败，B/C 未执行，PSEC 服务端回收未独立证实；产品安全与发布门禁不变，本票仍为 claimed。历史实验报告的 `audit.py` 实际会覆盖 `e/post.json`，禁止在原工作区或集成证据目录直接运行；保护原字节，后续仅可在隔离副本及新输出位置复核。以下 WorkBuddy 交接检查点保留为历史，关于“尚未合入”和“待独立复核”的描述已由本条更新。

- 2026-11-05：D10公共平台路线已定，精确剩余沙箱问题独立保留。原84张任务范围不变，12/60/61及后续最终交付仍等待本票结果，不以拆票规避安全标准。

### WorkBuddy 交接检查点（待独立复核）

- 用户要求完成正式任务03后交接，本实验已安全停止，不再扩大组合。候选提交 `319923eb4fbd64a0db43aabf143eeae8041f4cb3`，分支 `impl/d22-token-psec`，工作树 `.worktrees/i22`，Git clean；主集成尚未合入候选，本票保持 claimed，不能解锁完整沙箱/发布依赖。
- 报告实际位于 `D:\java supplement\Firstcode\RuoCun\.worktrees\i22\.scratch\ruocun-discovery\experiments\token-psec\README.md`。后续先在独立worktree只读复核该候选的原始字节、实际token/停止条件和清理证据；不要直接重复真实组合试跑。
- A组合cmd启动成功，restricting SIDs及删权结果保留；MandatoryPolicy从3变1，`NEW_PROCESS_MIN`位未保留，按既定完整保留条件停止。low IL本身是收紧，不能写成restricting SID丢失或所有组合不可用。组合Python、B/C未运行，WRITE_DAC/owner缺口未被证明修复。
- 实现者已保存8原进程、8精确Job和私有desktop查无、允许目录DACL恢复的审计；PSEC服务端teardown仍未知，待独立复核。ignored字节码缓存精确递归清理被自动审批以`blocked by policy`拒绝，未执行/未换入口，缓存保留；不要把Git clean等同磁盘全清。
- 本轮代理已交回检查点，接手者先核对分支与工作树当前状态，再决定复核/后续明确的最小调查。严格安全目标尚未达到，不默认选择弱后端。
