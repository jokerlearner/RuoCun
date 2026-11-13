# 27 工作树候选

工作树和工具定义沿冻结 DAO `agent/worktree`、`tools/enter_worktree` 与 `tools/exit_worktree`。完整中英描述与 schema 保留。项目身份留在原 workspace，路径解析 cwd 交上下文切换。分支命名 `ruocun-wt-<id>`，路径 `<显式目录>/.ruocun/worktrees/<id>`。私有子目录的 `.gitignore` 限定自身，Git 实查 ignored 后才建立工作树，保留原项目根 `.gitignore` 字节。支持显式 Git 仓内子目录，工作树创建路径仍限制在该目录下。

清理前验证目录和 Git 管理目录身份、common dir、checkout 根、当前分支、HEAD、分支引用和 Git 工作树注册。预检未提交文件（包括 ignored）或创建基线之后的提交时要求明确 discard。只有本实例创建的对象有清理入口，Git 操作结果不明时保留现场并抛出，阻止当作已完成。keep 仅退回原 cwd。实际注册、文件权限根及命令接线归主协调。

冻结语义用例先实际缺模块失败，随后真实 Git 验证创建、未提交/提交保护、清理、工具嵌套拒绝和 keep/remove。最初非 Git 夹具放在项目 worktree 的缓存，Git 向上发现了项目仓库，失败创建留下一个新引用。通过单条 reflog、创建时 HEAD `530edaa18d5aded8db093274cfdd8a5ed34c9b72`、工作树未注册且目标目录缺失确认仅为本次试验引用，以 `update-ref -d refs/heads/ruocun-wt-x <旧SHA>` 精确清理，随后 Git 核实引用不存在。该失败回执保留。修正夹具先确认目录真正位于所有祖先 Git 仓库之外，再验证无仓库返回，并在独立合成仓库验证显式嵌套 cwd、脱离分支后拒绝清理。所有工具日志使用白名单与合成 HOME，秘密扫描均为 false。

影子检查点沿冻结配置开关、项目布尔值优先、默认关闭、超时与慢快照停用，存于 `.ruocun/shadow.git`。独立 Git 对象、引用及索引绑定明确 workspace，Git 命令移除继承 `GIT_*` 路径重定向。已存在的来源不明目录保留。源 `reset --hard` 改为先确认回退前快照，再以影子 Git 两树检查更新已管理文件，保留线性快照历史，使回退前状态仍可列出并按完整提交 ID 恢复。拒绝覆盖未纳入快照的忽略文件、链接、重解析点及私有 Git 路径。结果不明时保留影子操作锁，禁止下次自动写入。

Windows 源迁移调试保留空 Git 模板未生成 `info` 和排除字面 pathspec 仍触发忽略路径提示的实际回执。补建自有 `info`，使用 glob 子树排除后，4 项定向测试通过。覆盖显式开关、设置覆盖、快照列表、原 Git HEAD/index 字节保持、忽略文件和二进制保留、目录碰撞拒绝、回退前状态可逆、实际子进程超时后未重复请求。Ruff 和 mypy 通过。普通 CLI 的 `/diff`、`/restore`、`/rewind code` 接线与独审由主协调登记。
