# A02/07 真实存储路径候选

2026-11-10；实现分支 `impl/07-store`，已合入集成 `33e49cf`（06稳定client），未改client或公共cli；本记录不替代主协调的票据状态、矩阵及独立复核。源码与原始测试仅采用唯一冻结快照 `dao-f17e189-7ac654a0dc06`，8个相关成员的hash/测试名/行号见本目录 `source-store-index.stdout.bin`。完整归档另经 `source-archive-verify` 校验。

## 实际实现与边界

`StoragePort`类型仍唯一位于 `session/contract.py`。`DurableStore`只由专属线程创建/使用/关闭；新增推荐工厂 `StorageWorker.open(session_dir,session_id,cwd,runtime,identities=None)` 负责在线程中创建真实端口并claim。调用者先await `load_recovery_view()` 获得owner；intent/result/run/recovery/checkpoint写入、读取、持久收据查询、close均经同一串行线程，默认sqlite线程检查保持，不暴露连接/游标。

真实SQLite采用已固定官方3.54.1 DLL，绝不回退旧库；实际清单（版本/source ID/compile options/DLL与驱动路径和hash/VFS）由独立演示输出保存。WAL/FULL/busy3000/foreign_keys读回；消息/checkpoint/revision/事件delivered与操作收据同一事务，run/event与结果/run/event分别原子。COMMIT回执未知不伪装rollback；worker阻挡后续写，允许按持久operation ID核实。await取消不取消已接受事务，close收齐队列后在线程中关连接。

Schema版本为本产品1，沿D09保留来源v2逻辑；只初始化版本0且真正无表的库。schema创建/版本/identity在同一事务，失败不留半初始化。既有库在claim前校验表列、quick_check、JSON、可信checkpoint/identity/revision及现有记录；DAO v2、未来、非空0、坏库、缺checkpoint均拒绝，原数据库不被静默重建。恢复多条读取在同一SQLite读事务快照中。

每次写事务内检查owner/epoch，活owner拒绝、死owner接管递增epoch，跨host和查询失败不当死亡；旧writer和旧close不能覆盖/释放新owner。Windows真实进程查询新增持进程句柄的零等待退出判定，防止已退出内核对象仍因创建时间可读而误判活owner。PID重用以创建时间fence；真实系统重启/强制PID复用未验。

SQLite目录保持已独立修复的平台上下文至连接关闭；数据库与-wal/-shm/-journal在打开前及创建后验证私密ACL、owner、普通文件/单链接，读路径同样核验sidecar。平台新反例与修复见 `../sprint-platform-r2/README.md`，最终接收以独立复核为准，不扩大同账户恶意行为保证。

## 来源测试对应与本票范围

| 冻结来源预期 | 本票可运行目标证据 |
| --- | --- |
| `durable_store.test.ts:26` 活owner/旧writer fencing | `test_real_dead_owner_can_be_recovered_without_losing_checkpoint`；`test_stale_writer_cannot_write_or_clear_new_owner`；原 `test_live_owner_cannot_be_taken_over_by_another_process` |
| `:27` transcript与event delivery一起rollback；`:28` receipt重开去重 | `test_checkpoint_delivery_and_run_event_failures_rollback_atomically`；`test_reopened_events_deduplicate_and_acknowledge_only_consumed_event` |
| 已知工具结果复用且unknown阻挡新副作用 | `test_tool_identity_conflict_never_reuses_another_operations_result`；`test_reopened_started_intent_is_unknown_and_blocks_changed_call_id`；重开started在claim事务转unknown |
| 坏库/未来版本失败关闭 | `test_bad_database_is_rejected_without_empty_fallback` 的9种合成库；schema初始化注入失败可正常重试 |
| TaskWait只确认自身结果；失败不能发布终态 | 本票覆盖持久事件子路径的选择性ack和run/event rollback；完整scheduler等待/paused/唤醒仍归11/17，不冒充已实现 |
| `process_identity.test.ts` 稳定身份、PID创建时间、child退出、权限失败 | `tests/test_session_identity.py` 真实当前/12个活子进程/退出保留句柄，加已登记查询故障seam；DB层另验证查询失败/跨host不接管 |
| `sqlite.ts:13–22` readonly/fileMustExist，显式事务原错 | `test_session_sqlite.py`；真实SQLite读回、事务注入与只读目录/字节前后检查；不把系统协调文件说成零物理写 |
| `durable_file.ts` 同目录临时/fsync/rename/目录sync | Windows端口20项与独立原生窗口复核；不把源码POSIX目录fsync照抄为Windows已支持 |
| `log.ts` SQLite权威、旁路日志/JSON导出不是真相 | `test_reopened_events_deduplicate_and_acknowledge_only_consumed_event` 写入冲突state.json/events.jsonl后仍从DB恢复 |

MM-591由平台 `windows/durable_file.py` + `file_contract.py` 承担；MM-593/601分别由 `durable_store.py`、`sqlite_port.py`、`runtime.py`、`storage_worker.py`承担。MM-595/600在本票仅覆盖保存/恢复数据路径，完整列表/resume/导出/会话模型归26，成本模型归28，升级归81（这些票本身也引用对应MM）；不把整份来源复合测试全部计入07通过。

## 红→绿记录

各命令的完整argv、退出码和原始字节均归档；标签即 `tools/run.py --label <标签> --state .cache/sprint07 -- <argv>`。

| 红信号 → 修复后 | 实际缺陷/预期 |
| --- | --- |
| `store-open-race-red` → `store-open-race-green` | 目录验证返回到sqlite3.connect之间被换junction；现在连接全周期保持平台边界 |
| `intent-conflict-red` → `intent-conflict-green` | 相同ToolRef却改最终args/digest复用旧结果；现在按语义操作身份核对 |
| `db-hardlink-red` → `db-hardlink-green` | 既有DB有外部硬链接别名仍写入；现在原地拒绝且别名字节不变 |
| `schema-red` → `schema-green` | 缺表、空checkpoint、坏JSON在claim后裸错/留资源；现在claim前拒绝并关闭 |
| `initialization-red` → `initialization-green` | schema失败留版本0非空半库；现在初始化事务rollback后可重试 |
| `unknown-reopen-red` → `unknown-reopen-green` | 重开started未标unknown；现在claim原子转unknown且新调用ID仍不能重放 |
| `worker-public-factory-red` → `worker-public-factory-green` | 新推荐真实线程工厂；全部StoragePort方法在真实连接上执行 |
| `recovery-snapshot-red` → `recovery-snapshot-green` | SQLite驱动边界注入并发提交使恢复视图混合前后记录；现在一个读事务一致快照 |
| `complete-demo-red` → `complete-demo-green` | 独立模块演示入口从缺失到真实两进程保存/恢复 |

另有原错保留和回执未知的真实SQLite故障注入；`real-transactions-worker` 2项通过。它模拟COMMIT完成后的回执丢失，不声称硬件掉电/磁盘满实测。`readonly-sidecar-acl` 首次因本次辅助函数挪动错误NameError失败，已纠正并保留 `readonly-sidecar-acl-fixed`；不能把该失败解释为平台失效或抹去。阶段全量、旧安装副本误验等原始记录如实保留，最终固定候选结果见后续汇总。

## readonly实际物理边界

遵守冻结DAO `sqlite.ts` readonly+fileMustExist：禁止业务写/建不存在的DB，不claim owner，不改checkpoint/revision。本机3.54.1实测 `readonly-sidecar-report`：活writer时主DB与WAL帧字节不变，但-shm字节变化；正常close只剩DB后，mode=ro读取会创建-wal和-shm。这是SQLite WAL锁/索引协调文件，[官方WAL只读说明](https://www.sqlite.org/wal.html#read_only_databases) 允许其已存在或被创建，不是业务状态提交。未改成immutable，避免活writer恢复读语义变化。新增文件逐个通过独立PowerShell Get-Acl读回：仅当前SID一个继承FA主体；产品端口同时验证owner/DACL和链接条件。

## 独立演示与当前工程入口

```powershell
.venv\Scripts\python.exe tools/run.py --label own-chat-restart --state .cache/own07 -- .venv\Scripts\python.exe -I -X utf8 -m ruocun.session.demo --workspace .cache/own07/new-demo --archive tests/fixtures/sqlite-dll-win-x64-3540100.zip
```

父目录需存在，workspace必须不存在；重复运行拒绝且保留DB字节。配置仅合成key，本次loopback真实HTTP/SSE返回中文与emoji；save子进程经真实worker提交消息、已接受输入、usage及持久操作收据并正常关闭；recover新进程claim epoch2、读回revision1和收据，随后关闭。输出实际SQLite运行库全清单；未调用真实模型、未访问外部API或真实用户配置。

`session-final-demo` 已独立执行通过。`session-final-ruff`、`session-final-mypy`、`session-final-offline`、`session-final-build` 已通过。

### 固定候选与最后关联修复

固定 `5201d55` 产品代码（合纯文档后 `973e63d` 等价），9个源码与非editable已安装文件逐一SHA匹配，`session-fixed-pytest` 在整个运行中未重装/改动安装：**387 passed、3 deselected，189.51秒**。此前 `session-tests` 385 passed 为阶段回归，运行期间有候选重装，不用它作为固定验收证据。

独立review随后真实证明5类错配持久化：result传入不同run，result/event或run/event传不同RunRef或session。D09要求冲突关联拒绝；DAO的事件自身携带run快照，在原结构中不能独立传入这些错配。本次Python拆参数后丢失约束，因此在结果和run/event事务内加13行最小关联检查，冲突保留tool.started且run/event零新增。原独立5红保留，当前本地 `association-red` 5 failed；修复后 `association-green` 原5反例加既有正确result/run/event路径共6 passed（15.18秒）。`association-ruff`、`association-mypy`、`association-build`全部通过，offline与演示涉及的入口未改、使用前述固定结果。

用户明确测试以DAO已提供语义为准后，停止新增扩展竞态/故障/边界假设；最后仅修复上述已确认真实错写并复跑已有反例/正确路径。不因纯文档合并或该最小修复再重复扩展全套。后续独立审查按来源测试与必要安装演示收口；实际结题仍由主协调判断，不在本分支改公共状态。

`installed-candidate.json`保存最后安装与源码匹配hash，旧匹配记录另留 `installed-before-association.json`；构建产物hash与资源回执见 `delivery-receipt.json`。新命令均已join，私有保护句柄/线程经对应路径关闭；没有付费API进程或本次保留的运行helper，历史未知对象和合成缓存继续保留。不把这些资源回执当作PKG-07性能对照验收。

未验：真实模型、最终WT/人工体验、独立账户、断电/硬件I/O故障、实际PID重用/系统重启、其它OS/卷、wheel/standalone完整发布组合；这些保持各自票门禁。历史异常对象、探针、`.ruocun-acceptance/`保留未纳入提交，未读取未知文件内容。新进程均等待退出，线程close与目录guard有真实清理验证；公开依赖缓存复用，原始合成工作区保留以便审查，不混入产品成果。
