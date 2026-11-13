# 07 会话持久化未完成检查点

本文件保留 `b06e238` 时点的历史未完成状态。2026-11-10 冲刺接续已形成完整代码候选和来源对应，最新实现/红绿/工程入口/明确未验范围读取 [sprint-session/README.md](sprint-session/README.md)；平台反例修复读取 [sprint-platform-r2/README.md](sprint-platform-r2/README.md)。独立复核及主协调验收前，本历史文件和新候选均不构成07结题。

状态：未完成，未通过独立复核；仅为恢复既有开发工作的本地保存点，不能关闭 07 或将 REC 母案例标为通过。接手者应先核对当前集成、独立平台复核和本文件范围。

## 已实现的候选范围

- StoragePort 单一类型声明、SQLite 连接和 WAL/FULL 配置、owner/epoch fencing、检查点与事件/工具状态存储，均待审查。受控 DLL 正常路径先校验固定官方 ZIP/DLL 摘要与实际加载路径、版本/source ID/VFS；导入存储模块不会提前导入旧 SQLite。
- `commit_checkpoint_ack` 增加兼容的可选 `operation_id`，默认以版本化规范请求计算；操作 ID、请求摘要与 revision 在同一事务写入。相同 ID 的不同内容拒绝，相同请求可重读已提交结果；查询未找到不代表已接收的排队请求失败。
- `StorageWorker` 初步实现会话专属单线程、检查点请求接受与取消等待分离；入队时复制可变消息防止身份与实际内容错位；重复等待 close 时仍需等待实际关闭。其它 StoragePort 方法尚未全部经该线程适配。
- Windows 进程身份沿用冻结参考的 CIM LastBootUpTime，以真实创建时间抵御 PID 重用；旧的系统时间减 tick 计算跨进程不稳定。

## 已执行的局部检查

使用 Windows x64、项目 CPython 3.11 独立 venv、`tools/run.py` 环境白名单和合成 HOME/配置/临时目录。真实模型、真实用户会话和 Windows Terminal 验收均未运行。输出按 runner 检查，未发现敏感环境值；原始缓存未纳入提交。

- `identity-red2` → `identity-green`：真实子进程活 owner 身份识别；后者每次使用 12 个子进程，不等于系统重启或全部进程权限情形。
- `readonly-red` → `readonly-green`：只读连接拒绝写入及创建不存在数据库。
- `runtime-red` → `runtime-green3`：存储导入不提前加载旧 DLL，实际受控 DLL 与 VFS 读取；`dll-loaded-path-red` → `dll-loaded-path-green` 和 `store-runtime-red` → `store-runtime-green`：不接受伪报的 DLL 位置。
- `recovery-first` → `recovery-green`：真实两个子进程写入/正常退出/重启恢复；`live-owner`：活 owner 存在时另一个真实进程不能接管。
- `checkpoint-id-red` → `checkpoint-id-green`：同一操作 ID 的相同内容幂等，内容冲突拒绝，退出重启后可查收据。
- `worker-cancel-red` → `worker-cancel-green`：已接受检查点不因等待者取消而取消；`worker-snapshot-red` → `worker-snapshot-green`：接受之后调用方修改原数据不改变已接受请求；`worker-close-red` → `worker-close-green`：重复 close 不能提前声称完成。`worker-unknown` 另检查未分类故障为未知状态。
- `final07-tests`：281 passed、3 deselected；`final07-mypy`、`final07-offline`、`final07-build` 通过，Ruff 首次为导入排序失败，修正后 `final07-ruff-fixed` 通过。其范围是当前候选和仓库既有自动测试，不是全量迁移或 07 独立验收。运行期间仅修正了导入排序与本说明，不改变执行逻辑。

## 文件平台阻塞后的并行子集

当前 Windows 私密文件端口尚未通过路径竞争验证。以下测试只创建自身 SQLite `:memory:` 数据库、使用合成 StoragePort，或查询本次测试进程自身身份；未调用 `DurableStore` 的真实目录入口，不证明 Windows 文件持久化、ACL、受控 DLL 或产品端到端通过。

- `queue-red` → `queue-green`：将 intent/result/run/recovery 写入口与读取入口排入同一专属 DB 线程；新写入句柄的 ID 仅用于进程内跟踪，并非跨重启持久收据。
- `poison-red` → `poison-green`：模拟提交回执未知时，已排队的后续写入原先仍执行；修正后阻止后续写入，保留读取以供核实。`safe-worker-all-seams` 共 9 项通过，另覆盖等待取消、预期未知操作拒绝后仍可记录人工恢复决定、提交前对可变快照复制及已存任务队列关闭行为。
- `safe-sqlite-faults` 3 项通过：只读 SQLite 连接拒绝写入或创建不存在的合成数据库；`:memory:` 内约束失败使 run/event 写入一起回滚；边界注入在 COMMIT 已完成但回执丢失时保留 `CommitUnconfirmedError`。故障注入不是硬件 I/O 或异常断电实测。
- `safe-identity` 1 项通过：对当前测试进程的真实身份，start 或 boot 不匹配返回不存活，另一 host 明确抛错；不代表真实 owner 崩溃接管或旧写者 fencing 的数据库验证。
- `safe-final-tests` 合并执行上述互不触及私密目录产品端口的测试，13 项通过；`safe-final-lint` 与 `safe-final-mypy` 通过。未重跑包含不安全路径端口的全量 pytest、终端/真实模型或产品最终验收。详细原始 runner 输出留在未提交的合成缓存 `.cache/codex07safe/raw/`；不得把缓存等同已归档证据。

## 必须继续的工作

1. 在平台候选独立复核后，对集成后的最终代码重新执行五项工程入口并留可复核证据。
2. 审查新增 StorageWorker 对 StoragePort 方法的串行化、生命周期和错误分类；补真实产品端口与真实多进程的取消、等待、关闭、队列竞争及持久收据验证。
3. 补齐死 owner 接管、旧 writer fencing、跨 host、查询失败、异常版本/损坏库、失败回滚、run/event 原子性等实测；需要真实子进程/故障注入的地方不能仅靠声明。审查数据库初始化与 schema 完整性、文件私密 ACL 和 SQLite sidecar。
4. 独立复核 SQLite 运行库固定来源与产物路径；仅有 Windows x64 开发环境候选，不等于 wheel/standalone 与其它平台的产品验收。
5. 完成任务票所有条件和来源测试对照后再提交独立 merger 复核；原未跟踪 `.ruocun-acceptance/` 由接手者另行审查，不纳入此检查点。
