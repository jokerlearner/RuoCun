# 08 — T06 完成普通入口跨进程验收

Type: task
Mode: AFK
Status: resolved
Assignee: Codex harness_provenance
Parent: [02 — B 方案](02-compaction-and-archive.md)
Blocked by: [06 — T04](06-runtime-compaction.md), [07 — T05](07-archive-access-lifecycle.md)
用户体验验收：not-required

## 实施范围

执行[task.md 的 T06](../task.md#t06--普通产品入口跨进程验收)，以[checklist.md](../checklist.md)为出口。优先扩展已有真实 CLI/本地 SSE/多进程与恢复测试，不建立第二套入口。
仅合成 HOME/配置/会话和白名单环境；敏感日志先审查再留证，不调用付费模型。

## 验收条件

- [x] AC01–AC14/16 有定向技术结果及真实请求/持久产物证据。
- [x] 第二进程重开可回查原文，完整导出顺序和次数正确。
- [x] 来源差异、未覆盖项和原始失败分别记录。
- [x] 独立复核无阻断，不把技术结果回填为体验 accepted。

## 证据

独立复核真实CLI→本地SSE→持久会话→新进程：两次压缩重整、近期原文、模型ArchiveRead、完整/当前JSON导出，以及真实冻结v1 writer→离线升级→备份哈希→新进程查询均通过（reviewer-t06-final，2 passed）。脚本[evidence/test_t06_cli.py](../evidence/test_t06_cli.py)只使用公开入口与合成资料；固定安装包同两案由09重新绑定。原始夹具错误回执保留，不计产品故障或真实模型成绩。
