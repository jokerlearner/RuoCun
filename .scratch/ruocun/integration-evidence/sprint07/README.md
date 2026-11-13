# A02 / 07 独立复核：本票来源路径通过

审查者 `/root/sprint_review07`；独立分支 `codex/sprint-review07`、worktree `D:\java supplement\Firstcode\RuoCun\.worktrees\sprint-review07`。起点 `33e49cfe09e3b7b06761b3b2d6c4c808958b0d41`，按主协调指令仅合入平台候选 `02fcb71cd1fc5d61fde1e7c46ba1a17857d85801`，合并点 `4247413`。随分支带入的早期 session 代码没有因此通过，也未运行未提交的实现者探针。

已读 AGENTS、CONTEXT、domain、issue-tracker、ADR-0005/0006、当前启动/停止记录、冲刺计划、07票、REC-01/02/03/09/12/15、相关模块行和 D09 唯一 StoragePort 契约。项目 workflow 与 code-review 技能直接读取；四槽约束下本审查槽分列规范与规格结论，不递归占用代理。原 relative_handle_probe 与异常对象保持原状，未运行、未读取内容、未清理。

独立预期来自 REC-12、D09 私密目录与文件持久发布要求、冻结来源 `durable_file.ts` / `sqlite.ts`，以及微软 [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)、[FSCTL_SET_REPARSE_POINT](https://learn.microsoft.com/en-us/windows-hardware/drivers/ifs/fsctl-set-reparse-point)、[FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers) 原始契约。CreateFileW 的共享模式不限制属性访问；非空目录不能设 reparse；FlushFileBuffers 需要写权限。运行结果另行验证，未从当前实现倒推这些预期。

`prepare_source.py` 仅从冻结 ZIP 读取并 SHA256 核对10个相关源码/测试成员，在本工作区私有缓存导出供阅读；不访问活动 DAO，也未执行来源代码。归档和各成员 hash 见 `raw/source-prepare/stdout.bin`。

## 独立环境与运行

CPython 3.11.9 Windows x64，新建私有 `.venv`，以 `requirements-dev-win311.lock` 的18包哈希从 `wb-i06/.cache/wheels` 只读安装。当前产品以非editable方式安装，确保测试实际运行候选副本。

每条命令经本目录 `launch.py` 启动，显式环境白名单、合成 HOME/AppData/TEMP/配置，无 PYTHONPATH；该启动器不读取父进程环境。参数/输出均为经审查的合成值或公开工具数据，保留原始字节并扫描敏感串模式。真实第二进程只操作每次 pytest 新建沙箱内的 `private/alternate`；没有原生相对创建或重命名 API。

```powershell
& 'C:/Users/PC/AppData/Local/Programs/Python/Python311/python.exe' -I -X utf8 .scratch/ruocun/integration-evidence/sprint07/launch.py --label <new-label> -- .venv/Scripts/python.exe -I -X utf8 -m pytest .scratch/ruocun/integration-evidence/sprint07/test_platform_independent.py -q -p no:cacheprovider
```

已亲跑结果见 `raw/<label>/command.json` 与 `stdout.bin/stderr.bin`：

| label | 独立结果 |
| --- | --- |
| platform-regression | 候选自带平台17项全部通过，23.68秒；不抵消以下独立失败 |
| platform-independent | 2 failed / 5 passed：readonly空目录在第二进程 `FILE_WRITE_ATTRIBUTES` 与 `GENERIC_WRITE` 下均被成功设置 junction；写分支 guard 存在时三access均不能改向，真实目录 rename 被拒 |
| platform-transition | 1 failed / 3 passed：`exclusive_write=True` 阶段仅 `FILE_WRITE_ATTRIBUTES(0x100)` 足以成功设置 junction；GENERIC_WRITE 在此阶段被拒。readonly非空目录两access均不能改向 |
| platform-guard-window | 1 failed / 11 deselected：默认写分支可把 guard 创建到替代目录，导致返回的已保护目录实际仍为空且可改向 |

## Standards

未发现另一个可独立成立的已确认规范硬违反。完整五入口、发布和全07复核尚未进行，不能写成规范全通过。资源/隔离与证据规则按本轮实际路径执行。

## Spec

两项未解决阻断，候选不得验收：

1. `durable_file.py` 的 `PrivateDirectory.__enter__` readonly分支没有维持非空性。真实第二进程分别以 `0x100` 与 `0x40000000` 打开空目录，`FSCTL_SET_REPARSE_POINT` 均返回成功。只读模式不写目录是既定约束；必须明确拒绝无法保护的空目录或绑定已有不可移除子项，不能把共享 WRITE 标志当作元数据保护。
2. 默认写分支的绝对 guard 创建不与已持有目录身份绑定。独立测试只在该唯一 `CreateFileW` 调用处控制调度，其余原生调用全部真实：第二进程在 exclusive 句柄已打开后给空 private 设置 junction；真实 CreateFileW 将零字节 guard 创建到 alternate；第二进程从同一原始目录句柄撤销 tag；随后产品末次普通目录核验成功，`__enter__` 返回。实测 private_entries=[]、alternate_guard_count=1；第二进程再次给 private 设置 junction 成功。该结果直接推翻“exclusive共享模式保护空目录到guard窗口”的候选假设。

失败已经即时报主协调与实现者，未由审查者修改产品。guard错位测试未发布真实凭据或业务文件；仅生成零字节保护对象，所有创建、设置与撤销均位于本次新沙箱内。它是确定调度的真实 Win32/子进程反例，不是全mock测试、随机压力或真实跨账户攻击证明。

## 资源与限制

本轮命令均已返回，子进程均通过自身 Popen/communicate 等待退出，设置的 tag 从同一原始持有句柄撤销；上下文关闭后 DELETE_ON_CLOSE guard 消失。`platform-resource-check.json` 检查本轮精确合成路径没有残留 reparse/guard；没有清理历史材料。保留合成目录、venv、依赖缓存及原失败输出。

本轮未执行整张07的SQLite、owner/fencing/事务/恢复、五入口或仓库外wheel验收，等待完整修复候选；未运行真实模型、独立用户账户、断电、其它文件系统/平台、最终standalone或用户体验。readonly非空控制通过不能推广为SQLite连接全生命周期通过，17项回归绿也不能替代失败修复。

## 平台修复轮（d2bae，限定子集通过）

主协调明确指定平台修复候选 `d2baedefcf52357c719ffcf0af91b61541101549` 后合入，独立合并点 `3476fca7ccd7435a6ea70d709118998b95447bf1`。此候选还带进程身份修复，但本轮仍仅执行平台范围，session未据此通过。

独立核对新原生代码与微软 [OBJECT_ATTRIBUTES](https://learn.microsoft.com/en-us/windows/win32/api/ntdef/ns-ntdef-_object_attributes) 及 [Nt/ZwCreateFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/nf-wdm-zwcreatefile)：本次仅完全限定的绝对NT名、RootDirectory=NULL、OBJ_DONT_REPARSE，固定结构自然对齐及Windows x64 ABI检查、同步完成、严格创建/打开信息码；未引入相对创建或重命名。无效打开只明确拒绝，不作降级跟随。

`test_platform_r2.py` 新资产保留原两类反例的独立预期，只适配新接口/实际系统调用边界，不删除原红信号或用mock替代原生调用。写guard与readonly锚两窗口均由真实第二进程在原生调用前设置junction，并从同一原始句柄撤销；测试还核对实际RootDirectory、对象名和同步标志。readonly原始空目录反例改以必须明确拒绝为验收，符合主协调确认的fail-closed方向。

| label | 独立结果 |
| --- | --- |
| platform-r2-install | exit0，非editable重新安装当前产品副本 |
| platform-r2-independent | **9 passed，2.62秒**：两种真实native窗口均拒绝且alternate零新增；readonly空目录/无效锚拒绝；真实第二进程无法删除持有的anchor/guard；稳定期两权限的metadata改向均拒绝 |
| platform-r2-regression | **20 passed**：候选自带原平台及新增窗口全集通过，见原始输出 |

原两类规格阻断在该明确平台子集中已闭环，当前无未解决平台阻断；首轮原始失败保持不变。只确认当前固定本地卷与本机Windows x64的上述平台发布/锚路径，不新增恶意同账户任意操作、跨账户、断电或沙箱保证。

资源回执 `platform-r2-resource-check.json` 限本轮合成路径；所有新子进程已通过Popen/communicate退出，原生tag同持有句柄撤销、guard关闭后消失。本分支未改公共状态、矩阵或产品。完整07、五入口、SQLite全周期、wheel仍等待正式候选。

另已预写但尚未执行的 `store_probe.py` / `test_store_independent.py` 用于后续完整07真实磁盘/子进程复核：期望取自冻结来源与D09/REC，不提前把资产或实现者局部绿算通过。readonly主DB无业务写与WAL/SHM物理维护分别记录，沿用来源只读连接语义，不额外承诺零锁元数据变化。

## 完整候选首轮（5201d；5项关联阻断）

主协调明确指定 `5201d5529f94702fce4164c047a472019de46ebb` 为完整候选，合并点 `9c82b9ad281eed5df2351290d8a6a192db6f5a1f`，并非实现者workingtree。重新非editable安装产品后，已运行的独立检查如下。

| label | 独立结果 |
| --- | --- |
| store-install | exit0，安装完整候选 |
| store-independent-initial | **12 passed / 5 deselected，51.85秒**；真实磁盘和独立子进程，全部命令已收尾 |
| store-association-red | **5 failed / 12 deselected，13.30秒**；真实DB实际写入错误关联，已退回修复 |

12项通过包含保存/重启与旁路投毒、活owner拒绝及持Popen句柄强杀后的epoch2接管、未来/DAO/非空0/缺checkpoint/版本错配拒绝且主DB未覆盖、真实run/event回滚、epoch fencing、ToolRef最终参数冲突、SQLite page limit产生的真实SQLITE_FULL下不ack/不消费事件，以及真实DB线程等待取消、COMMIT后丢回执时阻挡后续写/允许持久收据查询和关闭资源。SQLITE_FULL由该测试数据库的page limit制造，没有填满主机卷；回执丢失只在实际COMMIT返回后注入，不声称硬件故障或断电。只读亲验主DB字节不变，但关闭writer后新增 `session.db-wal` 与 `session.db-shm`；按DAO readonly业务语义记录，不将物理零写作为额外验收。

5项关联阻断的来源是D09既有 `commit_result_and_event`「无意图/冲突关联拒绝」及RunRef/OutboxEvent关联。先查冻结DAO `durable_store.ts:156–165`：`event(event)`直接 `saveRun(event.snapshot)`，run与event共享同一来源；新端口将参数拆开后必须保留该关系。实际失败分别为结果关联异RunRef、结果事件的异RunRef/异session，以及run事件的异RunRef/异session；错误记录真实持久化，包含工具 `result_committed` 与错run/event，不仅是缺少某个异常类型。期望是整体拒绝、原工具仍started且run/event零新增。

本轮用户随后要求以DAO已有测试语义收口、避免大量额外测试。主协调明确：已确认的这5项bug做最小修复并原5项确认绿；已启动12项安全收尾，之后不再扩展故障/竞态假设或从纯静态疑点追加门槛。现有资产和原失败证据保留；后续仅受影响语义与必要安装演示，纯文档候选只比对产品字节。尚无最终07通过结论。

## 最终候选与收口

最终实现候选 `6a4228ddc209d95fde4f09070e123c3034b080cc`，关联最小修复为 `f9c9b5a2bc670c6711bc8ade2fc33fddd8859ddf` 的13行事务内校验。独立合并点 `cb9ee36a617eeb5b03e3cd9db3c9ab600f14ab31`；已读并采用新增AGENTS规则及ADR-0009。没有再扩建测试，原5项反例原样确认绿。

| 最终label | 审查者亲跑结果 |
| --- | --- |
| store-final-install | exit0，重新非editable安装最终候选 |
| store-association-green | **5 passed / 12 deselected，13.44秒**；全部冲突整体拒绝，工具保留started，run/event零新增 |
| store-final-ruff | exit0，All checks passed |
| store-final-mypy | exit0，43个源文件无问题 |
| store-final-build | exit0，隔离后端从锁定公开缓存构建sdist及wheel，未访问索引 |
| store-final-offline | exit0，沿用既有4个工程入口；不代表完整Agent suite |
| store-wheel-install / store-wheel-isolation / store-wheel-pip-check | 全exit0；真正仓库外新venv只安装最终产品wheel，包仅pip/ruocun/setuptools，无pytest、support、editable或源码路径借用，依赖检查通过 |
| store-wheel-demo | **exit0**；产品 `python -m ruocun.session.demo` 的真实loopback Chat→worker保存→退出→新进程恢复通过 |

wheel工作区为 `C:\Users\PC\AppData\Local\Temp\RuoCun 独立wheel sprint07-20261110`，从该目录运行已安装模块，官方固定ZIP也复制到此新合成目录，未借仓库资源。实际回答“你好，世界 😀”，revision保持1、owner epoch1→2、持久收据revision1；HTTP请求golden验证、server_closed、processes_exited均true。输出保留完整SQLite实际清单：3.54.1、D09固定source ID和DLL SHA256、compile options、驱动位置/hash及win32 VFS，门禁met。wheel与sdist SHA256见 `artifact-hashes.json`。

实现者已归档固定5201d等价安装的全量 **387 passed / 3 deselected（189.51秒）**；这是实现者基线，不改写为本审查者亲跑。按ADR-0009，末次13行修复后只重跑原5个独立失败；实现者另保留原5项及既有正确worker路径6项绿。没有重复387项全套或新增排列门槛，先前12项/平台9+20项证据按产品差异范围沿用。

随后合入主协调最新 `10c346f`，最终集成记录合并点 `408442ef4d1bf82a4ef3aad126424f31207ec4fe`：它包含已独立接收的工程issue_graph及其既有测试、ADR/发布路线/状态文档，07产品 `src/`、`tools/`、metadata及开发锁相对上述完整复验点逐字节无差异；已执行 `git diff --exit-code cb9ee36..HEAD -- src tools pyproject.toml requirements-dev-win311.lock` 为0。工程工具增量沿它自己的独立证据，不在本票扩展重复测试。

## 最终 Standards

**0项未解决的已确认规范硬违反。** 核对唯一StoragePort声明、模块职责、参考只读、合成环境与私密状态隔离、代码/证据共同提交、真实自动与人工结果分列。工具检查如表。未以代码气味猜测追加门槛；没有修改公共票据状态、module-map或验收矩阵。

## 最终 Spec

**0项未解决的本票来源路径阻断，允许主协调接收07。** 已核对冻结来源的测试/角色映射：`durable_store.test.ts:26/27/28/32` 的owner、事务/投递、重开及坏库语义，`process_identity.test.ts` 的存活/退出/创建时间与查询失败规则，`sqlite.ts:13–22` 的readonly/fileMustExist与显式事务，以及`log.ts:94–140`的SQLite权威。对应目标测试及复合来源测试中留后票的scheduler/paused/完整会话列表范围见实现者 `evidence/07-store/sprint-session/README.md`；该对应关系不冒充全量来源CLI实际执行通过。

已捕获的readonly空目录、guard错位和五项结果/run/event关联错误均按已有复现闭环；原红信号未删除或改写。Windows私密发布、线程串行、真实保存/恢复、owner及事务、本票开发与wheel实际运行库范围已具证据。本票通过不表示REC整族、全部DAO功能、Windows原生沙箱、性能阈值或最终产品全部完成。

## 最终资源与未验范围

所有本审查者启动的命令已返回，Popen子进程均按拥有对象等待退出；最终wheel两个子进程与本机HTTP服务正常退出。`final-resource-check.json` 对本次精确合成保护目标核验无guard或reparse残留，未跟随pytest便利链接；测试fixture junction、缓存、合成工作区、外部venv及历史异常材料保留。该回执不作全机进程/文件扫描或历史事故无影响承诺。

未执行真实模型、完整来源CLI oracle、真实Windows Terminal/人工体验、独立账户访问、实际PID复用/系统重启、断电或硬件故障、其它OS/卷、最终standalone、性能测量；按既有范围/后续票分别待验。SQLite readonly允许其WAL/SHM索引与锁协调文件物理维护，主DB/业务状态不写及不claim的来源语义保持。没有将这些未验项填为accepted，也未依据新发现的纯静态疑点继续扩测。
