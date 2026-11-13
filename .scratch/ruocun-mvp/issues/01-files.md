# M01 — 六项文件/计划工具与注册派发

Type: task
Status: resolved
Assignee: /root/mvp_files
Branch: codex/mvp-files
Worktree: .worktrees/mvp-files
Blocked by: none（复用已完成02–07与首版共享声明）
用户体验验收：not-required

结果：候选88fc474已独立复核并集成。96项定向通过（91来源+5必要适配）；Windows junction遍历缺口以同一复现red→green，受影响29项独审通过。[实现证据](../evidence/m01/README.md)，最终整体验证另由M04登记。本票只关闭首版六工具子集，原完整迁移票不因此结题。

按[首版规格](../spec.md)迁移冻结DAO的Read/Write/Edit/Glob/Grep/TodoWrite及registry/schema/path子集；先来源断言red再green。保持对应路径、read metadata/写前读取与外部修改拒绝、整表todo语义；首版文本文件，未支持图片明确说明。完整源测试中后置功能单列不适用，不删除来源或假称完整测试通过。

接口与文件归属见规格；tools/types.py由root单点维护。只提交本票源码、来源测试和独有简短证据；不改client、存储、cli、公共表。提供可消费候选及真实未验项，由独立审查后集成。
