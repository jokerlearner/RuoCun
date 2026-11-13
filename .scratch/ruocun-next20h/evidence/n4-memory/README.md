# 30 分域记忆

`source.json` 固定来源归档、冻结文件、候选源和原始日志摘要。Python 3.11 私有 venv，白名单环境下显式导入源码。真实模型调用 0。

## 存储候选

- 冻结 `memory/{types,frontmatter,hash,validate}.test.ts` 对应 `test_n4_memory_format.py` 的 13 项。Windows CRLF 输入沿 D09 支持，文件源哈希保留原换行。
- 冻结 `memory/store.test.ts` 的路由、slug、origin 过滤、精确去重、locked、删除与状态过滤，对应 `test_n4_memory_store.py` 的 20 项，含 D09 只读 provenance 与坏原件的必要适配。旧版 locked 同名用例只断言 action，现保留原字节并选择空闲文件名。
- 独立的 Markdown 原子发布复用私有数据子目录与现有 Windows 发布端口。未知替换或同步结果向上抛出，已确认失败前置拒绝保留原数据。兼容数据不迁移、不修改。
- 格式/存储红灯为模块缺失，最终 33 项通过。Ruff 和默认严格 mypy 6 个源文件通过。原始红灯和首次静态失败均保留。
- 独审复现内嵌换行破坏 frontmatter。沿原坏原件用例加入同名改写，`n4-memory-meta-red01` 复现未拒绝，`n4-memory-meta-green01` 验证发布前拒绝、旧字节保留和正文多行可读，Ruff/mypy 通过。

## 工具与审核

- `test_n4_memory_tools.py` 沿冻结 `tools/memory_{read,write}.test.ts` 的 5 项查询、8 项写入与删除，以及冻结 `permissions/secrets.test.ts` 的 3 项。MemoryWrite 沿来源保持 plan/auto/常驻，通过既有 `persistentEffect=True` 进入独占派发和耐久账本。写入已确认后才返回记住、更新或删除结果。
- `test_n4_memory_audit.py` 沿冻结 `memory/audit.test.ts` 的 7 项及 `index.ts` 的 `/memory` 分支。合法目标删除才标记为修改，空参数和越界名称返回用法。旧命令首个原生同名的作用域顺序保留，锁定和兼容原件保留。
- 工具中英文描述及字段描述提取自冻结文件的 JS 运行时文本。MemoryRead 两种语言的用户目录路径按 D09 改为 RuoCun 原生品牌。写入凭据扫描在本地执行，拒绝只报告类型。
- 工具/审核红灯为模块缺失，合计 24 项通过。Ruff 和 mypy 11 个源文件通过，保留首次 mypy 失败和修正记录。
- 原命令用例复用一个已知只读别名拒绝，验证多目标报告仍保留先前已确认删除。未知结果仍抛给普通入口。`n4-memory-command-known-red01` 复现拒绝被错误向上抛出，`n4-memory-command-known-green01` 通过同一用例。
- 独审确认冻结的正文扫描未覆盖同样持久化的标题和来源字段。复用原凭据用例，`n4-memory-secret-fields-red01` 复现凭据标题进入来源读取。回修使用相同规则逐字段扫描，在派生文件名和计算来源哈希前拒绝，只回显去重的类别。`n4-memory-secret-fields-green01` 通过原凭据和正常来源哈希 4 项，Ruff/mypy 通过。

长期记忆 Markdown 与会话账本分别持久化。工具级未知写入由既有账本停止，不自动重放。用户主动执行的 slash 删除不生成模型工具对。阶段 31 的自动注入及 32 的整理、蒸馏和自动清理另行迁移。本候选的普通 CLI 接线及打包由集成验证。
