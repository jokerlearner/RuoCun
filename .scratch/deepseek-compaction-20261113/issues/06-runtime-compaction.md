# 06 — T04 接入主子执行与统一提交

Type: task
Mode: AFK
Status: resolved
Assignee: Codex root + compact_audit
Parent: [02 — B 方案](02-compaction-and-archive.md)
Blocked by: [04 — T02](04-pressure-and-selection.md), [05 — T03](05-transcript-storage.md)
用户体验验收：not-required

## 实施范围

执行[task.md 的 T04](../task.md#t04--主子执行与统一压缩提交接线)。主、同步/后台/恢复子代理经各自 journal adapter 使用同一策略；接入手动、自动、超限和目标模型检查。
保持失败停止、取消权威、工具配对、后台等待、图片与未知副作用保护，提交前核验模型投影未变化。

## 验收条件

- [x] AC01–AC06/10–AC13/16 受影响路径通过。
- [x] 05 已经独审集成，不消费未确认存储候选。
- [x] 主/子范围不串、压缩失败不唤醒等待，不重放已执行工具。
- [x] 压缩接线和提交/取消边界独立复核通过。

## 证据

主预算/控制器/loop51项通过（ctrl2），主账户/会话等15项通过（mr3）；子同步/后台/fork/TaskSend/跨进程恢复30项定向及静态通过，见[子接线交付](../evidence/t04-child-summary.md)。独审新增子入口7项通过（reviewer-child-final），主新路由/导出6项、原子发布16项、ArchiveRead权限7项与两进程CLI2项分别通过。原始失败和来源差异见[执行记录](../execution.md)。产品已冻结待09集中全量/构包，真实模型质量未验。
