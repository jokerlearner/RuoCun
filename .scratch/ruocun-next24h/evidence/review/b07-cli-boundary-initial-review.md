# 70 CLI 与命令边界首轮独审

`3779c8fc` 的 CLI、目录和原受控终端组合实际通过 5 项，用时 11.10 秒。`raw/b07-review-cli-routes/` 保留原命令与输出。所有复验使用白名单环境和合成数据，秘密扫描未命中。

普通入口实测查询无模型请求，本地 Skill 操作员安装写入预期目录。临时 key 通过请求凭据字段使用，未创建账户配置，所检会话 JSONL 无该值。文件路径保留为提示词，符合词法的未知命令返回 2。原受控终端单例在模型请求仍运行时检查 `/status` 等查询及无效变更，当前取消信号保持未设置，原队列、草稿、审批和模式断言均通过。源码审查确认账户切换、MCP 变更、权限变更和会话操作等有各自的 `pause_settled` 路径。

`d22c2395` 在 `_parse_cli` 引入原生 `--` 终止符兼容，冻结 Node oracle 继续保留 DAO 的不同结果。两条普通入口探针确认外层仍存在阻断。

- `raw/b07-review-native-terminator-red/` 的实际 `run_cli` 先抽取权限。终止符后字面 `--permission-mode bypassPermissions --allow Write` 被解读为权限配置，得到 bypassPermissions 和 Write allow，且从原提示删除。
- `raw/b07-review-cli-meta-secret-red/` 的实际 `cli.main` 把终止符后的 `--version` 解读为版本查询。相同回执也确认两个显式 `--api-key` 时，第二个合成 key 值进入 prompt。该风险位于参数过滤，未调用模型或执行工具。

两项外层解析阻断已交主协调处理，重复凭据的首个值仍可按来源选择，所有显式凭据值应排除于提示。第 70 票等待修后同探针和进度提醒接线证据。
