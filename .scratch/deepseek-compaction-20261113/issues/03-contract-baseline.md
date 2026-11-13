# 03 — T01 固定归档契约与实施基线

Type: task
Mode: AFK
Status: resolved
Assignee: Codex /root
Parent: [02 — B 方案](02-compaction-and-archive.md)
Blocked by: none
用户体验验收：not-required

## 实施范围

执行[task.md 的 T01](../task.md#t01--固定契约版本和实施基线)，按[plan.md](../plan.md)绑定原文身份、投影来源、事务/幂等、版本升级、预算和权限契约。
修改共享契约由本票唯一负责人控制；保留当前工作区已有改动。技术细化不得冒充旧 ADR 已经确认。

## 验收条件

- [ ] 脏工作区差异、来源 SHA、文件锁与未来分支基线记录齐全。
- [ ] AC01/05/06/09/13/16 的接口与兼容行为无歧义。
- [ ] 测试主路径使用现有 CLI 与 StorageWorker 接缝，没有第二套验收框架。
- [ ] 独立契约审阅通过；03 完成后才释放 04/05。

## 证据

2026-11-13 用户启动实施；[ADR-0020](../../../docs/adr/0020-compaction-transcript-archive.md)记录技术基线及既定测试边界。23个原文件已复制并绑定SHA256，HEAD为381f73d；不提交或覆盖原有其它改动。
共享接口冻结：ArchiveRewrite(expected_messages,mapping,derived)；ArchiveDerivation(id,kind,target_index,source_indices)；策略返回candidate(messages,origins,replacements)，root负责适配。StoragePort/Worker的归档参数可选，归档内容纳入幂等digest；类型由T03唯一写入者维护。
独立角色已核查owner/版本门禁与现有测试环境，既有两项基线2 passed（不算B实现结果）。T02与T03分文件并行；T03独审后才释放接线。
