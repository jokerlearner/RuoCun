# 26 会话管理候选

基线 `69bbc6fe`，冻结来源 `dao-f17e189-7ac654a0dc06`；逐成员源码hash见 source-bindings.json。冻结 log.test.ts 的同cwd/未完成/真实用户轮筛选、保存摘要、压缩保留和clear重置是本票直接来源。index.ts:2160–2199 的 /session、/resume、/branch、/rename 及导出/clear接入普通入口。

普通入口 /session与/resume列表只查询；目标ID、cwd和活owner以及原会话运行/未知run先检查，合法切换才pause→settled→save。_run外循环等旧会话SessionEnd、scheduler/broker/任务/MCP/存储完整收尾后再SessionStart，未替换旧闭包。--continue无ID按findResumable，只选同cwd未完成且无活owner、有用户轮的最近会话；干净关闭记录由closed判done，显式ID仍可重开。--continue后想直接提供斜杠命令时用 `--continue -- /session`，保留已有可选ID解析契约。

/branch只建立快照，不切换。新UUID的owner、输入账本、tool/run/outbox从空开始，保留已配对聊天、累计usage、model/mode、标题/任务摘录。内联图片深复制；既有附件路径及digest显式登记为分支持久引用，原拥有附件的会话不自动清理；本轮不声称自动回收此类父会话。/clear保留会话ID及历史输入账本，queued由明确pause处置为discarded，只将模型消息清到系统前缀并重置task_title。Checkpoint新增可选task_title，旧记录默认兼容，None不加入请求digest，避免改变旧幂等身份。

清理沿冻结每日节奏，默认30天。会话先IMMEDIATE事务核活owner、closed、无queue/未知工具或run/event/附件，再写tombstone拒新claim；私有trash中核目录/文件身份及seal后物理删除。失败保留原位或trash现场。修正源mtime删会话风险：mtime只用于旧无元数据记录排序，安全删除仍核耐久状态。自动清理扫描所有cwd scope的保留run/recovery_material，保护精确worktree/cwd及附件；无法完整读某会话时停spill/subagent/worktree回收。只移除自身已登记、干净、无独有commit且无人引用的旧工作树，不执行影响其它Git条目的全仓worktree prune。

## 已有定向回执

- raw/b05-26-title-red：扩展冻结摘要保持用例，缺rename接口真实红。
- raw/b05-26-entry-red：基线主线源码普通CLI对rename仍未知，独立源预期红。
- raw/b05-26-final-source：3 passed，包含真实受控SQLite的会话排序/摘要/clear/附件分支/物理prune，以及真实普通CLI回环first→rename→branch→clear→export、/resume分支续写、显式ID重开、--continue新会话。只有合成HTTP响应，无真实模型或费用。
- raw/b05-26-protected-worktree-red/green：主线旧cleanup确实删除被保留代理引用的干净工作树；修正后同一真实Git fixture保留，1 passed。只用合成临时repo，未操作参考DAO或用户项目Git。
- 根.venv对7个变更源模块ruff全绿、mypy 0错。所有产品测试通过tools/run.py白名单和合成HOME启动，回执scan_hit均false。

当前是候选，不代填独审或用户体验，不构包、不跑全量。事务封存后无法物理删完会保留tombstone，不能算物理清理完成；长期attachment引用不会悄悄解除。Monitor owner丢失证据沿46单票记录。
