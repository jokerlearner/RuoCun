# 07 — T05 实现归档回查、导出与生命周期

Type: task
Mode: AFK
Status: resolved
Assignee: Codex root + memory_audit
Parent: [02 — B 方案](02-compaction-and-archive.md)
Blocked by: [05 — T03](05-transcript-storage.md), [06 — T04](06-runtime-compaction.md)
用户体验验收：not-required（终端体验集中于 09）

## 实施范围

执行[task.md 的 T05](../task.md#t05--只读回查导出分支与会话生命周期)。提供范围受限、分页的命令/工具；完整与当前投影导出分开；落实 clear/rewind/branch 和附件清理规则。
与 06 共享的运行时、子代理和 Conversation 文件按锁串行，不通过复制父回调扩大权限。

## 验收条件

- [x] AC07–AC10/12–AC14/16 可从普通入口和产物观察。
- [x] 普通子代理无法查父归档，fork/exactTools 不自动扩权。
- [x] 重复原文、清空/回退边界、分支独立闭包和附件引用正确。
- [x] 帮助/schema/命令目录与实际能力一致。

## 证据

T05技术出口已完成；06已resolved。以下存储/材料证据与主协调公开命令/权限/导出证据共同承担本票，最终包与人工体验由09单列。

- [05已resolved](05-transcript-storage.md)：scope绑定列表/读回/导出/继承接口可消费，完整契约和边界见[T03交接](../evidence/t03-delivery.md)。
- [可信spill依赖红](../evidence/t03-13-dependency-red/command.json)→[绿](../evidence/t03-13-dependency-green/command.json)：压缩后归档依赖保留；branch复制必要材料至新私有目录，父会话封存删除后子仍可按实际路径/hash读取完整内容。
- [选定继承prefix与明确任务suffix](../evidence/t03-14-import-prefix-green/command.json)：只导入当前可见来源闭包，不按正文匹配猜源，不复制未引用的clear前历史。
- [生命周期独审3 passed](../evidence/reviewer-t03-lifecycle/command.json)：材料闭包、范围选择和cleanup已放行。默认直接prune仍保留原有附件门禁，cleanup仅在完整检查其它会话依赖后允许独立封存。
- 原始message及digest不因分支搬移改变；实际物理材料通过DB别名提供。ArchiveRead有界引用和完整JSON附件清单分别处理，[导出上限修正复验](../evidence/t03-23-export-refs/command.json)。

公开CLI/ArchiveRead及权限通过`perm1g`和独立`reviewer-archive-deny`；完整/当前JSON、clear/branch/重开/读取通过B05（R2安装包的`r2-target`25项涵盖该组）；流式revision一致性及原子发布分别有`reviewer-route-export`6项、`reviewer-atomic-publisher`16项。独立QA/pure两进程闭环通过`reviewer-t06-installed`、`reviewer-t06-pure`，R2纯包重跑通过`reviewer-t06-pure-r2`。新空工作区导出父目录缺陷在R2修复；Todo重开保留缺陷在R3修复、独立真实CLI红绿通过。帮助、schema和命令目录已同步。
