# B 方案独立复核（最终 B-r3）

日期：2026-11-13。结论：下列已复核接缝没有未解决的阻断项，可供最终集成消费。此结论不代替整套回归、固定安装包验收或用户体验验收。

最终候选为 B-r3：仓外 pure-r3 普通 CLI 的两项 T06 加一项 Todo 重开回归，在全新仓外 `D:\rcb-dd7453\review-r3` 下执行，`r3x` 为 **3 passed / 17.33s**。产品命令均为 pure-r3 Python 的 `-I -m ruocun`，没有 src loader。Todo 场景得到 `{keep:true, explicit_clear:false}`，保留任务且显式清空不复活。

最终绑定见 [reviewer-r3-final-fingerprints.json](reviewer-r3-final-fingerprints.json)：当前 root 的全部 323 个构包输入与 B-r3 冻结清单一致；本代理审查的 27 个产品文件与 pure-r3 实际安装字节一致。B-r3 输入总指纹为 `5f530430e385fef8b05837f06165d5c8cdd3c308cc70c87bdd52bfcab0744486`。后文 B-r1 指纹与较早回执保留为阶段证据，不冒称同一候选。

本代理未修改被审产品或实施测试，未提交、回退 Git。只维护白名单启动器与独立普通 CLI 验收脚本。源头研究、规格/计划和 T01 接口审查在此前完成，遵循 ADR-0009 复用已有用例与故障 seam，没有新增故障矩阵。

## B-r1 阶段审查范围与指纹

指纹：[reviewer-final-fingerprints.json](reviewer-final-fingerprints.json)。其中 27 个产品文件的当前字节均与构包冻结清单 [t07-r1-inputs.json](t07-r1-inputs.json) 相符；另登记 7 个直接使用的测试文件和 2 个本代理维护的证据辅助文件。

- 构包输入总指纹：`e4a12606737e3234bb7804d48b7377a1caa09d8312054e0476f5a717ccf8fd61`。
- 本次复核清单指纹：`230f1ca9431abbc61fd20842228a3b0918e3bf57b544f6cfdf4999aadf915f0e`。
- 边界：较早命令先于最终冻结清单执行；当时 T03 原片有独立的 inputs/outputs 指纹。最终清单固定本次复核候选，不能倒称所有历史测试都在完全相同全仓字节上运行。

只读核查包括：纯候选压缩与实际请求体预算、主/子 typed rewrite 提交、取消/未知确认后停止、不缩小则不重发、切模型资格检查先于账户配置发布、存储原文/派生来源/元数据版本和同事务回执、v1 显式离线升级、选定 prefix 来源闭包与材料别名、cleanup 依赖保护、scope 读取权限、原文 TaskOutput/重开恢复以及流式原子导出。

## 独立亲跑证据

所有命令通过明确环境白名单启动；HOME/配置/会话/临时目录均为合成值，未读取真实账户。以每目录 command.json 的 exit 和 stdout 为准。

| 证据目录 | 实际结果 | 可消费范围 |
| --- | --- | --- |
| reviewer-t02-policy | 22 passed | 策略公开行为、近期尾部/配对、prune 与摘要进展 |
| reviewer-t03-final | 8 passed | 当时 7 个归档节点与冻结旧 writer 实际拒写 |
| reviewer-t03-lifecycle | 3 passed | 压缩后 spill、独立 branch 材料、cleanup 及选定 prefix |
| reviewer-t03-final-increment | 9 passed / 9.82s | 最终归档公开节点，含完整 export 不受 20 个展示引用上限截断 |
| reviewer-route-export | 6 passed / 13.00s | 相同 model 换 provider 的窗口、后台 scope 变化时停止发布、B05 既有行为 |
| reviewer-atomic-publisher | 16 passed / 7.85s | bytes/Iterable 共用私有文件、替换及持久确认通路 |
| reviewer-archive-deny | 7 passed / 0.67s | 固定 scope 的有界 ArchiveRead、普通子代理隔离、显式 deny |
| reviewer-child-final | 7 passed / 19.48s | 普通 CLI 的同步/后台 prune、summary、fork、TaskSend、跨进程 TaskOutput |
| reviewer-t06-final | 2 passed / 8.37s | 源码入口的两次压缩→重启回查；冻结 v1 建库→公开离线升级→重启导出 |
| reviewer-t06-installed | 2 passed / 9.11s | 仓外 QA 安装包入口重跑上述两案，无 src loader |
| reviewer-t06-pure | 2 passed / 9.16s | 仓外仅运行时依赖安装包重跑上述两案，pure 无 pytest，无 src loader |

T06 使用普通 CLI 子进程、本地 SSE 同行和真实文件/SQLite，没有替换产品内部组件。它验证执行契约，不评估真实模型摘要质量。原始失败证据保留，夹具修复及无效红证据的界限见 execution.md、t03-delivery.md、t04-child-summary.md。

仓外安装包复验使用 `D:\rcb-dd7453\qa\Scripts\python.exe -I -m ruocun`，每案的 installed-product.json 记录实际 `site-packages/ruocun` 导入路径、版本与 sys.path，没有 checkout/src。旧 v1 建库仅显式加载冻结旧 contract/store，运行时依赖从 QA 安装包导入。独立按字节核对 27 个被审产品文件，与本次冻结输入全部相同，见 [reviewer-installed-fingerprints.json](reviewer-installed-fingerprints.json)。

同两案另使用 `D:\rcb-dd7453\pure\Scripts\python.exe -I -m ruocun` 通过。pure 只有运行时锁定依赖及冻结 wheel，pytest 仅由仓库外层证据驱动器执行，不装入 pure。其每案 installed-product.json 同样证明真实安装导入；27 个产品文件再次逐字节匹配，见 [reviewer-pure-fingerprints.json](reviewer-pure-fingerprints.json)。

## 已复核修复

- 子 run 的操作身份必须区分新的 A→B→A 状态变化，不能只用请求正文 hash 去重；重试使用稳定操作 ID/digest 回执。
- 旧会话升级在维护提交前验证 revision 与活 runner；真实冻结旧 writer 在新 storage_version=3 下拒写，SQL user_version 保持 1 不会绕过业务身份门禁。
- 相同 model 换 provider/baseUrl 后刷新实际窗口，同时保留用户手工窗口。
- 完整导出逐页绑定各 scope revision，全部字段结束后复核，变化发生时在 atomic replace 前失败。
- ArchiveRead 纳入现有权限身份映射，显式 deny 生效；其 callback 在子上下文创建时清空，由对应 journal 按本 run scope 重新绑定。
- TaskOutput 与后台 progress 按原文偏移读取，不按压缩后的消息下标切分；跨进程 bind 使用同一来源。
- 完整 export 的附件引用清单解除展示上限；ArchiveRead 仍保持原有有界引用。

## 尚未验收

- 整套最终回归、Ruff/Mypy/构包安装以主协调的固定候选证据为准，此处不把定向结果累加成整包通过。
- 未使用真实模型；真实摘要质量、供应商缓存/计费效果未验。
- 未做真实 Windows Terminal 操作与缩放；无头普通 CLI 通过不等于终端体验验收。
- 保留既定边界：旧压缩已经遗失的原文不能补回；SQLite 与附件文件不宣称跨域原子回滚；账户配置和会话提交不宣称跨文件分布式事务。

## 后续定向增量

以上冻结指纹属于 B-r1，不改写为后续候选的整包证据。

- B-r2 仅补两个 export 入口缺失 `.ruocun` 父私有容器初始化，沿原 ACL 验证与 atomic publisher 通路。仓外 pure-r2 的既有 T06 两案在 `reviewer-t06-pure-r2` 通过（2 passed / 8.56s）。另独立运行同一 manual helper 的 `--prepare-only`，使用全新 workspace 且不预建 `.ruocun`，`reviewer-manual-r2` exit=0；它没有启动界面，manual/visual/resize 状态仍 pending。
- `reviewer-r2-root-binding.json` 逐项核对 323 个构包输入时，root 仅 `context_runtime.py` 与 R2 不同，因为已开始下面的 Todo 修复；不宣称当时 root 整体等于 R2。
- 后续发现压缩后只剩任务 pin、TodoWrite 已归档时，重开得到空 ctx.todos，第二次压缩会静默移除旧清单。单个独立普通 CLI 证据节点对 keep/显式 clear 两场景分别运行两进程、两次有效摘要，`reviewer-todo-red` 得到 `{keep:false, explicit_clear:false}`，确证数据保留缺口。
- 主协调只改 ContextManager 解析当前可见 pin 及其后成功 TodoWrite 配对：无新结构化状态时保留 pin 原文，成功空列表是有效清空，失败结果忽略；compact 与目标模型资格检查共用。没有解析显示文字伪造结构化 todos，没有扩 UI/存储职责。同一证据在 `reviewer-todo-green` 通过（1 passed / 8.95s），得到 `{keep:true, explicit_clear:false}`。随后已在 B-r3 pure 安装包通过，不能倒算 R2 已安装包含该修复。
- B-r3 首次组合回执 `reviewer-r3-installed` 为 2 passed / 1 failed：Todo 的 clear 场景在首个 CLI 启动即 CorruptDatabaseError，尚未到 Todo 断言。该夹具的 session.db 路径为 252 字符、rollback journal 名到 260 字符；相同产品/原断言换短标签 `r3i` 后 3 passed / 18.32s，再按主协调要求移到全新仓外短 basetemp，最终 `r3x` 3 passed / 17.33s。原失败保留，不抹除、不计作 Todo 逻辑红证据，也不宣称修复了产品 SQL 长路径支持。
