# 唯一参考快照

当前参考：dao-f17e189-7ac654a0dc06
基准提交：f17e189dc68a0a0a0b9937784e1b7ce29aed80eb
源码树 SHA-256：7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c

## 固定范围

[metadata.json](dao-f17e189-7ac654a0dc06/metadata.json) 记录来源版本、路径、提交、状态及捕获范围。
[source.zip](dao-f17e189-7ac654a0dc06/source.zip) 保存当前 797 个已跟踪文件和 8 个未跟踪源码文件的原始字节。
[manifest.json](dao-f17e189-7ac654a0dc06/manifest.json) 保存每个路径、Git mode/index blob、来源、状态、长度和 SHA-256。
[tracked-working-tree.patch](dao-f17e189-7ac654a0dc06/tracked-working-tree.patch) 保存相对 HEAD 的二进制差异；[staged-index.patch](dao-f17e189-7ac654a0dc06/staged-index.patch) 保存暂存区差异。
status.porcelain.z 与 index.entries.z 保留 NUL 分隔的 Git 原始记录。
[checksums.json](dao-f17e189-7ac654a0dc06/checksums.json) 校验上述归档和元数据。

这是一份源码工作区快照，不含 Git 完整历史、忽略的 node_modules、凭据或运行数据。
依赖仍需按锁文件安装；这不构成可离线运行的完整环境镜像。
快照中本地源码和未跟踪源码均属于本次冻结参照，迁移中若要调整其行为须登记差异与理由。

## 校验与恢复

在 RuoCun 根目录运行：

~~~powershell
python .scratch/ruocun-discovery/reference_tool.py verify .scratch/ruocun-discovery/reference/dao-f17e189-7ac654a0dc06
python .scratch/ruocun-discovery/reference_tool.py extract .scratch/ruocun-discovery/reference/dao-f17e189-7ac654a0dc06 --destination .worktrees/reference-dao-f17e189-7ac654a0dc06/source
~~~

目标解包目录必须尚不存在；校验会检查归档路径、完整成员集合和每个文件哈希。
reference/ 下的 .gitattributes 将快照材料设置为 -text，防止 Git 换行转换改变校验值。

后续研究仅从已校验的解包副本或 ZIP 成员读取；需要运行来源测试时再建立独立可写实验副本。
归档不含 .git：需要 Git 发现、检查点或 worktree 行为的实验应创建受控 Git fixture 或独立实验仓库，明确代码根与被操作工作区，避免意外继承上层 RuoCun 的仓库边界。配置与会话根也使用实验输入，不借用真实用户状态。
报告使用“快照源码路径:行号”定位归档中的文件，不把活动 DAO 路径当作长期证据。
可删除解包缓存后重新从归档恢复；归档、清单和研究记录均入 Git。
