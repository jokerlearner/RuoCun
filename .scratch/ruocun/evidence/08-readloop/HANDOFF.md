# 08 未完成保存点（B01）

保存时间：2026-11-10 19:51 +08:00。主协调转达用户“再完成一个小模块后保存进度并停止”，指定28的Session/费用基础作为最后模块；08立即停止新增实施，09未开始。

## 分支与范围

- 分支：`codex/b01-tools`；工作树：`D:\java supplement\Firstcode\RuoCun\.worktrees\b01-tools`。
- 起点：`12a4fa1ae201456dc97ee24f1ee8f1c31f309f86`（含08领取记录，07已resolved）。
- 产品代码、测试和公共状态均未修改。本保存点仅含本文，不是08可审候选或完成证据。
- 08仍未实现，未执行产品测试、五入口、安装后工具回合、真实模型或终端体验。

## 已核对来源

已读项目AGENTS、CONTEXT、domain/issue-tracker、ADR-0005/6/8/9、08票、当前实施记录、冲刺计划、规格相关运行/存储条款、对应表的本票条目及验收矩阵相关案例。已读项目ruocun-workflow与implement-spec/TDD规则；来源测试语义迁移优先，不新增额外测试门槛。

唯一来源为`dao-f17e189-7ac654a0dc06`冻结ZIP，归档SHA256实读匹配：`1f8308959d8b9ac0783b6ce6ddbffe7a71cc60bc59332f309f0d62083efac078`。已解包至忽略目录`.cache/frozen/`，未运行来源或修改活动DAO；尚未执行reference_tool的完整成员清单校验。

已阅读或定向阅读下列冻结成员：

- `src/tools/types.ts`、`schema.ts`/`schema.test.ts`、`todo_store.ts`、`todo_write.ts`/`todo_write.test.ts`。
- `src/tools/read_file.ts`/`read_file.test.ts`、`registry.ts`/`registry.test.ts`、`tools_for_mode.ts`/`tools_for_mode.test.ts`、`output.ts`/`output.test.ts`、`paths.ts`、`src/permissions/sanitize.ts`。
- `src/tools/execute.ts`、`execute.test.ts`的案例索引、`execute_durable.test.ts`。
- `src/agent/loop.ts`的入口、历史清洗、空响应/预算截断修复、工具执行与图片回灌段；`loop.test.ts`相关案例与索引、`loop_durable.test.ts`案例索引。

后续应继续按08所需案例完整读取，以上不宣称全量来源测试已迁移或运行。

## 已确认接口和行为

- 08独占`agent/loop.py`和本票`tools/`模块；不改client、07平台、`session/contract.py`或公共cli/矩阵。仅注册已经实现的Read/TodoWrite，后票工具不能占位冒充执行。
- 冻结Read：文本1-based行号、offset/limit、默认2000行、单行2000个JS UTF16单位、5MB护栏、NUL拒绝；图片扩展名+magic检测、视觉模型检查，图片先置于`currentImageData`再在tool消息后以user图片消息回灌。成功文本读取才登记`readFiles/readMeta(mtimeMs,size)`；路径含符号链接逃逸和可疑Unicode审批边界。
- 冻结TodoWrite：整表替换、最多一个in_progress、空表清空、activeForm优先、全完成且至少3项时验证提醒；无独立task ID。
- 冻结headless首批只检查批中是否出现TodoWrite：出现即`done=true`且同批其它工具可执行；不能自行改成TodoWrite成功后才解锁。
- 坏JSON不能执行handler；截断修复只用于诊断。历史中坏arguments替换为`{}`，执行仍用原始参数；普通空assistant最多两次重试（三次空失败），不保存空assistant。预算截断分支另有收敛提示/low effort/256000/强制工具及不支持时回退，需按来源保留。
- 使用07的`StorageWorker.enqueue_intent`、`enqueue_result_and_event`、`enqueue_checkpoint`和恢复视图；intent先于副作用，结果持久后再配对/复用。未创建另一套StoragePort或会话框架。

## 与28的共享Session约定

E01已发早期稳定接口，尚未在本分支消费其提交：

- `Session(systemPrompt: str, model: str, *, env: Mapping[str,str]|None=None)`。
- 字段：`messages`、`model`、`mode`、`usage`（camelCase四键promptTokens/completionTokens/cacheHitTokens/cacheMissTokens）、`lastPromptTokens`、`lastSentLength`、`budgetCNY`。
- 方法：`addUser(content)`、`addUsage(u,model=None,*,requestId=None,attemptId=None,provider=None,endpoint=None)`、`notePrefix(fp)`、`onCacheBust(fn)`、`cacheHitRatio/costCNY/overBudget/usageSummary/clear/setModel/toggleMode`。
- 持久桥：`toCheckpoint(base: Checkpoint)->Checkpoint`、`fromCheckpoint(checkpoint,*,env=None)->Session`。
- 08不得另造Session；恢复后先核对E01实际提交与以上约定。

## 环境与实际命令结果

外层启动器`.cache/run.ps1`创建ProcessStartInfo并清空环境，再显式传入Windows系统项、Python311路径和合成HOME/USERPROFILE/APPDATA/LOCALAPPDATA/TEMP；工程子进程再经既有`tools/run.py`白名单启动。没有读取真实凭据或继承父环境。

- Python：`C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe`；本地`.venv/`已创建。
- 公共wheel缓存仅只读复用：`D:\java supplement\Firstcode\RuoCun\.worktrees\wb-i06\.cache\wheels`。
- 第一次将哈希锁文件与`-e`混用失败：pip拒绝对editable要求单一hash；无产品安装成功声明。
- 单独按`requirements-dev-win311.lock`离线安装开发闭包成功；收据`.cache/state/raw/deps/command.json`记录exit=0、sensitive_values_present=false、sensitive_match=false。
- 随后`pip install --no-deps --no-build-isolation -e . -e tests/support`失败：缺少editable构建所需`editables`模块；收据与扫描后合成日志位于`.cache/state/raw/editable/`。未因停止要求继续补装/调试，尚不能从该venv运行已安装产品。
- 未新增产品依赖、未修改锁文件。环境安装失败属于准备步骤，不是产品测试失败或08来源行为结论。

## 资源与下一步

上述ProcessStartInfo均WaitForExit完成。保存时按精确工作树路径筛选Win32_Process，未发现自有python/pythonw/node/pytest/ruff/mypy进程。没有启动模型服务器、数据库worker、runner或付费请求。worktree、venv、冻结解包、合成状态与原始合成日志保留，不清除历史。

后续仅在用户重新明确授权后继续08：先核对新集成tip/E01接口、补齐安装路径，再以来源已有测试逐条red→green完成Read/Todo/registry/execute/loop和真实本地兼容client+SQLite工具回合；完成后独立复核集成，才可领取09。
