# T03 原文归档与存储交接

状态：产品实现、定向验证及独立复核完成，05票resolved；增量依赖/分支/清理独审3项通过。未提交 Git，未使用真实模型或真实用户会话。
日期：2026-11-13；当前工作区文件指纹见 [t03-file-fingerprints.json](t03-file-fingerprints.json)。已有用户改动按块保留；新增持有文件的旧字节也已保存在 baseline。

## 已实现

- `contract.py` 单一定义 ArchiveDerivation、ArchiveRewrite、ArchiveImport、ArchiveOperation；存储语义版本 3，SQL user_version 仍为 1。
- `archive.py` 在现有 meta 表内保存不可变 raw/metadata版本、summary/prune、clear/rewind/prefix边界和短投影/范围清单；不新增连接或外部权威。
- 普通保存只按位置追加或更新已知协议元数据；改写必须带 expected_messages 和显式映射。重复正文是不同 raw_seq，元数据更新仍属同一个 raw_seq。
- `DurableStore` 与 `StorageWorker` 在 checkpoint/run 事务内落归档和投影；checkpoint digest覆盖改写/导入，子run/result另有持久操作回执。
- 子run受理时生成独立操作ID，handle携digest；同ID同材料可回读，冲突拒绝。不会用正文hash吞掉新的 A→B→A 状态更新。
- 只读 scope/list/read/export/branch 接口经过同一存储线程。summary/prune引用读取展开真实来源，按逻辑身份去重，不按正文去重；图片payload不注入读取文字。
- Unicode分页借助短索引只加载页命中的raw正文；JSON导出另含所有metadata版本、派生记录/来源、首页projection和实际附件refs。
- branch支持指定当前投影位置闭包，并严格以继承材料为相同prefix后追加新任务suffix；原文身份/版本不伪造为新用户发言。
- 可信工具spill格式只在精确workspace私有根解析依赖，登记哈希。branch将闭包文件复制为目标私有材料，原message/digest不改，以逻辑path→实际path别名读回。
- cleanup完整检查各会话后才允许带附件的完成会话封存；其它保留会话依赖其内部文件时继续保护。直接prune默认保留原先附件门禁。
- 显式离线升级拒绝活owner/runner和未知结果；确认SQLite备份及附件身份清单后，维护事务导入当时可见材料并升语义版本。失败保留备份，旧资料缺口明确标记。

## 红绿与定向证据

所有命令均用 `.venv/Scripts/python.exe -I -B -X utf8 evidence/run_checks.py`，白名单与合成HOME/配置/会话/临时目录见每目录command.json。

| 片段 | 原失败 | 对应通过 | 可观察结果 |
|---|---|---|---|
| 自动原文/重复/metadata版本 | t03-01-raw-red | t03-01-raw-green | 保存→关闭→重开、公开分页和scope拒绝 |
| 子run持久回执 | t03-02-run-red | t03-02-run-green | operation ID/digest可跨重开查证、内容冲突拒绝 |
| 派生引用读原文 | t03-03-derived-read-red | t03-03-derived-read-green | summary/prune读取回早期真实消息，非再次返回摘要 |
| 显式旧会话升级 | t03-05-upgrade-red | t03-05-upgrade-green | 不静默升级、备份可查、旧覆盖缺口明确 |
| 原子/取消/升级回滚复验 | 复用既有故障seam | t03-07-atomic-regression、t03-10-upgrade-rollback | 同事务回滚、丢ack回读、不重放、取消等待不撤销受理 |
| 冻结旧writer真实拒写 | baseline实际旧模块 | t03-12-frozen-reader | 旧contract+旧DurableStore拒绝新3，DB主文件SHA未变 |
| 压缩后spill及分支独立材料 | t03-13-dependency-red | t03-13-dependency-green | 父归档保文件、清父后子仍可读私有副本及验证hash |
| 指定继承prefix+新suffix | t03-14-import-prefix-red | t03-14-import-prefix-green | 不复制未选历史，新任务单独追加 |
| scope枚举 | t03-15-scopes-red | t03-15-scopes-green | 主/子登记顺序可查，不加载全文 |
| JSON派生来源 | t03-18-json-red | t03-18-json-green | 派生原字段/来源单列，不拼进raw消息 |

最终定向 [t03-20-final](t03-20-final/command.json)：24 passed，含9项新公开归档测试和既有worker、恢复、图片、cleanup路径。
最终 Ruff [t03-21-final-ruff](t03-21-final-ruff/command.json)：通过。
最终 Mypy [t03-22-final-mypy](t03-22-final-mypy/command.json)：7产品文件通过。此前 t03-19-final-mypy 因并行修改中的 Conversation 两处类型错误非零，原回执保留。
独审原片回执位于 reviewer-t03-final / reviewer-t03-ruff / reviewer-t03-mypy；后增量 reviewer-t03-lifecycle 3项通过，接口已释放。独审指出完整导出附件不能受20引用上限截断，已只对export解除并在t03-23-export-refs重跑2项通过。

## 保留的失败与边界

- t03-06-storage-regression 为45通过、2失败：嵌套fixture从旧安装创建v1，以及当时Conversation尚未传rewrite；原失败保留，主协调接线/夹具修正后定向复验。
- 静态各轮非零回执保留，不能把目录名含green当成通过；实际exit与stdout为准。
- 升级备份包含一致DB及附件路径/hash清单，不宣称已复制所有外部附件。branch独立材料复制先确认、后发布DB引用；不宣称文件与SQLite跨域原子回滚。
- 归档保存的是已接纳消息及已有引用，不重建旧摘要覆盖前的丢失历史、不追溯工具内部尚未保存的原始stdout。
- 真实模型摘要质量、供应商缓存效果、最终wheel及Windows Terminal体验不在本片通过范围。
