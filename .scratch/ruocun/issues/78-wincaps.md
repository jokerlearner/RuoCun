# 78 — 本轮Windows能力及不支持边界最终验证

Type: task
Mode: HITL
Status: resolved
Scope: reduced
Assignee: none
Parent: [完整迁移规格](../spec.md)
Blocked by: [58 — Windows系统凭据存取及fallback可用于请求](58-credentials.md), [59 — 系统定时来源路由与Windows不支持边界](59-schedule.md), [61 — 网络隔离开关保持来源语义与平台限制](61-sandboxnet.md), [62 — 电源能力路由与Windows无防休眠保证](62-power.md), [63 — 终端通知及标题注意状态（无桌面通知）](63-notify.md), [64 — Windows粘贴图片进入视觉模型请求](64-clipboard.md), [17 — 恢复查询及显式决定解开未知工具/执行](17-recovery.md)
Automatic exit: passed
Automatic evidence: .scratch/ruocun/evidence/b09-r4-automatic/78-wincaps-automatic.json
用户体验验收：accepted

## What to build

普通用户验证保留的凭据、进程树、ACL/flush、沙箱边界、图片/文本clipboard及恢复。W3下Windows系统定时明确不支持，W5下无防自动休眠保证，W6下只保留终端提示/标题；这三类验收真实能力路由和不支持说明，不开发或伪造原生后端。其它保留能力的登录/重启边界仍按支持策略实际留证。

范围依据：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)。保留WIN-06/07/10母族及59/62/63硬前置，使自动出口核验本轮明确边界；自动出口与用户体验分别记录。

## Context pointers

自动技术出口与人工出口按[ADR-0006](../../../docs/adr/0006-batched-sprint-workflow.md)分别汇总。可自动组合的真实 Windows 检查须满足矩阵和独立复核，79 消费该出口。用户操作、登录或重启的子项按最终实机回执验收。

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[NEW-01](../module-map.md#新增适配层候选位置)、[NEW-02](../module-map.md#新增适配层候选位置)、[NEW-03](../module-map.md#新增适配层候选位置)、[NEW-04](../module-map.md#新增适配层候选位置)、[NEW-05](../module-map.md#新增适配层候选位置)、[NEW-06](../module-map.md#新增适配层候选位置)、[NEW-07](../module-map.md#新增适配层候选位置)、[NEW-08](../module-map.md#新增适配层候选位置)、[NEW-09](../module-map.md#新增适配层候选位置)。

## 共享接口与并行

接口领域：HITL/平台。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WIN-01](../acceptance-matrix.md#win-01) — Shell/环境探测：本票路径覆盖的子案例满足“方言显式、编码/argv不损坏，doctor与env不执行POSIX误语法，审批与执行一致”。
- [x] [WIN-02](../acceptance-matrix.md#win-02) — 受管进程树：本票路径覆盖的子案例满足“身份核验、有限force收口、真实close才canceled；keep-background独立生命周期，无多余可见窗口”。
- [x] [WIN-03](../acceptance-matrix.md#win-03) — IPC与ACL：本票路径覆盖的子案例满足“已认证且最小访问范围可实证；HMAC不替代ACL，进程身份/句柄继承可查”。
- [x] [WIN-04](../acceptance-matrix.md#win-04) — 持久文件/SQLite：本票路径覆盖的子案例满足“失败保持原文件，持久确认含义真实、网络不支持明确拒绝；不把目录fsync失败吞掉”。
- [x] [WIN-05](../acceptance-matrix.md#win-05) — 系统凭据：本票路径覆盖的子案例满足“Credential Manager或等效后端，case collision可区分，失败不误报系统保存，秘密不入日志”。
- [x] [WIN-06](../acceptance-matrix.md#win-06) — 系统定时边界：Windows入口明确拒绝本轮不支持，无系统注册/执行；会话内loop不冒充定时，帮助及能力报告一致。
- [x] [WIN-07](../acceptance-matrix.md#win-07) — 电源边界：Windows无防自动休眠保证，不假称持锁；用户自行管理电源策略的说明可见，正常进程/资源生命周期仍准确。
- [x] [WIN-08](../acceptance-matrix.md#win-08) — 图片/文本clipboard：本票路径覆盖的子案例满足“Windows原生读取，图片类型/上限一致；失败不吞原文本、不执行路径为命令”。
- [x] [WIN-09](../acceptance-matrix.md#win-09) — OS文件/网络隔离：本票路径覆盖的子案例满足“按ADR-0008沿用DAO平台能力；Windows启用时明确不支持，普通Shell不冒充隔离；支持平台与实机状态单列”。
- [x] [WIN-10](../acceptance-matrix.md#win-10) — 提示渠道与数据：只显示安全终端提示/标题，准确说明无桌面通知，不启动桌面通知后端或返回虚假发送成功；提示失败不改变任务状态。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

2026-11-12，用户确认 b09-r4 实机恢复正常。Windows 的启动和登录身份均变化，固定包重开同一 SQLite 会话，读回同一系统合成凭据并提交前后两条验收标记。退出码 0，控制台模式恢复，删除凭据后读回 not-found。自动门禁继续覆盖本轮的定时、电源、沙箱、持久化、权限和进程边界。其它 Windows 账户的安全负例和非 Windows 完整产品实机按既有范围留待验证。[最终实机回执](../../ruocun-next24h/evidence/batch-final/acceptance-r4.json)

最终批次 b09-r4 已按实机发现的画面改动定向复跑，并逐项绑定未受影响的原证据。[最终自动回执](../evidence/b09-r4-automatic/README.md)

批次09最终包 b09-r3 对账户配置改动定向复验并复用未受影响的案例，人工体验仍待最终验收。[最终自动回执](../evidence/b09-r3-automatic/README.md)

批次09固定包的自动出口按实际帮助差异和原证据逐项重新绑定。人工体验仍待最终验收。[换绑记录](../evidence/b09-automatic/README.md)

批次08固定产品 `8ee4a9b992ee7a77759b3295708dda32bebbe68f` 的[自动技术出口](../evidence/b08-automatic/README.md)通过独立复核，真实终端体验及本票需人工确认的系统条件仍待最终验收。

## Comments

- 2026-11-10：按W3/W5/W6收缩Windows原生能力，不移出母案例族，也不由范围变化解锁自动出口。58凭据与64图片剪贴板等未选项继续保留。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
