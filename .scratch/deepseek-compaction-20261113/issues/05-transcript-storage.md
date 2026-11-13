# 05 — T03 实现原文归档与原子存储

Type: task
Mode: AFK
Status: resolved
Assignee: Codex /root/memory_audit
Parent: [02 — B 方案](02-compaction-and-archive.md)
Blocked by: [03 — T01](03-contract-baseline.md)
用户体验验收：not-required

## 实施范围

执行[task.md 的 T03](../task.md#t03--完整原文分段归档与存储确认)。复用 SQLite、专属存储线程和现有 owner/revision/操作回执，完成增量原文、来源映射、版本和显式离线升级。
这是高风险持久化接缝，必须独立复跑及集成后才供 06/07 消费；附件不得被当作同 DB 事务的替代品。

## 验收条件

- [x] AC05/06/08/09/12/16 通过受影响的存储与恢复入口；普通CLI完整组合由06/07/08继续验证。
- [x] 归档、引用、新投影及操作回执同成同败，重复/冲突可区分。
- [x] 同文不同身份保留，元数据更新不误增用户消息。
- [x] 新旧语义版本隔离、备份升级和失败保留有证据。
- [x] 独立复核通过，无已知阻断，已释放06/07消费本存储接口。

## 证据

实施与红绿路径详见[交接记录](../evidence/t03-delivery.md)，工作区候选绑定[文件指纹](../evidence/t03-file-fingerprints.json)；未创建本票Git提交，也未覆盖原有未提交改动。

- [最终定向24 passed](../evidence/t03-20-final/command.json)：9项公开StorageWorker/真实SQLite归档测试及既有worker、恢复、图片和cleanup；测试不读取真实用户数据。
- [Ruff通过](../evidence/t03-21-final-ruff/command.json)；[Mypy 7文件通过](../evidence/t03-22-final-mypy/command.json)。
- [冻结旧writer拒写新语义](../evidence/t03-12-frozen-reader/command.json)：实际加载保存的旧contract/DurableStore，拒绝新storage_version=3，DB主文件SHA保持。
- 独审亲跑：[主存储7项及旧reader](../evidence/reviewer-t03-final/command.json)、[Ruff](../evidence/reviewer-t03-ruff/command.json)、[升级/取消](../evidence/reviewer-t03-upgrade-cancel/command.json)、[增量材料/继承闭包](../evidence/reviewer-t03-lifecycle/command.json)。后者3 passed，独审已明确无阻断并释放。
- 独审指出完整导出不得复用ArchiveRead的20附件上限，已仅对export解除上限，[2项定向复验通过](../evidence/t03-23-export-refs/command.json)。ArchiveRead仍限制输出。
- 确认回滚、丢失提交确认、受理后取消、升级失败的原始证据和首轮失败均保留于交接记录；不将命令目录名称当通过依据。

## Comments

2026-11-13：T03完成。新会话语义版本3、SQL user_version1；旧会话只走显式离线备份升级。普通保存与归档唯一SQLite事务，子run保存有独立持久操作回执，明确拒绝未知操作自动重放。附件复制先确认后发布DB引用，不声称文件与数据库跨域原子回滚。

主/子循环、公开命令与工具、完整导出及固定wheel仍由06/07/08/09结题；本票完成不表示真实模型质量、Windows Terminal体验或整个B方案已验收。
