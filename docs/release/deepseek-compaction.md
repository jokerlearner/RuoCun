# DeepSeek 风格压缩与原文归档

2026-11-13已按用户后续授权更新当前桌面「若存 Code」入口到B-r3，并备份/升级6个旧会话、保留配置。[当前部署及回退材料](../../.scratch/deepseek-compaction-20261113/deploy-current.md)

本批对应用户确认的B方案：[规格](../../.scratch/deepseek-compaction-20261113/spec.md)、[执行记录](../../.scratch/deepseek-compaction-20261113/execution.md)。具体通过数和包指纹以最终交付回执为准，功能说明不代替测试结果。

## 使用

请求前检查当前输入、工具定义、图片估价和有效输出上限。默认输出上限随小窗口适配；不合法的显式设置在发请求前拒绝。估价仍是启发式，供应商用量另行显示。

有压力时，先在副本中裁剪超过8192字符的普通工具正文，保留前4096、后1024字符。仍需摘要时，重整旧摘要和较早材料，按预算保留近期原文及完整工具组。系统/启动Hook、Todo与恢复控制材料受保护。摘要为空、截断、未缩小、取消或保存未确认时停止，原投影保留。服务器超限恢复只有确认取得进展后才允许有界重试。

```text
/compact
/context
/archive list --offset 0 --limit 20
/archive read <ID> --offset 0 --limit 4096
/archive list --scope <已登记子执行范围>
/export
/export --context
/export --format json
```

默认导出包含可恢复原文及清空/回退边界；`--context`仅输出当前模型投影。JSON保留消息版本、派生记录、引用与图片/附件信息。完整导出分段读取；期间任一已读取范围推进时拒绝发布混合版本，请后台稳定后重试。

模型通过只读`ArchiveRead`按标记中的ID回查原文，分页最多16000字符。范围由当前执行绑定；普通子代理没有父归档回调，fork仅继承实际可见来源闭包。显式权限规则可禁止工具。历史正文不能授予新的执行权限。

清空和回退不抹去已保存原文；分支只复制当前投影所需来源闭包及附件副本。父会话清理后，分支仍能按已登记路径/哈希读取自己的材料。

## 旧会话

新建会话使用`storage_version=3`，SQL的`user_version=1`保持。新程序拒绝直接接管旧语义会话，旧writer拒写新语义。先停止所有使用目标会话的旧进程，再运行：

```text
ruocun --cwd <原工作区> --upgrade-session <ID>
```

先生成一致性SQLite备份和附件清单，报告备份路径及SHA256，再在维护事务中升级。失败保留原数据和备份；不自动降级。数据库备份不等于复制全部外部附件。只能保住当时实际存在的材料；旧摘要遮蔽且已遗失的原文用`legacy_gap`标识，不能补造。

## 来源与限制

固定参考[DeepSeek Harness e8f7b93](https://github.com/deepseek-ai/deepseek-harness/tree/e8f7b93a344964de3dca1ace9e72b6e4d6de87cb)（MIT）。借鉴预算、头尾裁剪、配对切点、近期保留、单份摘要及缩小门禁；未移植TypeScript/Cordis框架。若存以现有SQLite事务维护原文和投影，保留ADR-0012失败停止及既有权限/未知结果边界。许可随包附于THIRD-PARTY-LICENSES.txt。

合成验收不证明真实模型摘要质量、实际多模态token精度或供应商缓存收益。Windows Terminal视觉/缩放及用户体验分别登记，不由无头CLI代替。
