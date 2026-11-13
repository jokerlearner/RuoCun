# 81 安装升级与数据保留

使用仓外中文及空格路径的新建 CPython 3.11 x64 虚拟环境，从 `b08-r1` 安装升级到 `b09-r3`。两份 wheel 的包元数据版本同为 `0.1.0.dev0`，按产物字节与更新后的内置帮助确认实际替换。本票证明同一开发版本两个固定候选间的手动升级流程。旧包 SHA-256 为 `01330dead041e70177f609e338b433619b630919be055e8a47c5d52a5fdd8298`，最终产品 `8e7760ce` 的 R3 wheel SHA-256 为 `764d9f908c583de07f32f48f0618b74c0c82f273ec02ae672496efb00aedb81d`。

1. 从旧包普通入口创建真实已持久会话。进程结束后检查 SQLite 持久回执与 WAL sidecar 已收口。复制整个合成 `.ruocun` 到仓外完整备份并比对四个文件的字节。
2. 按已锁运行依赖和固定 wheel 执行 `pip --force-reinstall`，通过 `pip check`，升级前数据和备份哈希原样保留。旧、新应用均使用随包 SQLite 运行库，探针没有复制 DLL。显式恢复原会话 ID，第二条新消息成功提交，两次模型请求只使用合成回环。
3. 在数据的独立合成副本验证数据库未来版本及坏页，分别得到 `VersionRejectError` 和 `CorruptDatabaseError`。原字节、请求次数及会话树不变，切回正常副本仍可读取。
4. 使用实际 `/Config` 与 `/account default` 检查四份原生配置副本。未知版本且含旧形状凭据、损坏 JSON、版本2的 `profiles` 数组、版本2的 `activeProfile` 非字符串均拒绝，配置字节、会话树及模型请求次数不变。
5. 执行 `pip uninstall` 确认包卸载、合成用户数据与备份仍在、合成 DAO 文件保持原样，最后清理工作区。

[R3 原始回执](raw/b09-manual-upgrade-r3/command.json) · [R3 断言结果](raw/b09-manual-upgrade-r3/stdout.bin)

R1 上已验证停止、备份、更新、同会话继续、数据库拒绝及卸载。另一个 R1 探针发现含旧形状凭据的未来版本配置可被 `/Config` 读取、由 `/account default` 实际改写为版本2，R3 回执覆盖这一回归。中间 R2 探针已经得到坏 JSON 的真实拒绝，探针一处过窄的本地化诊断词匹配失败，R3 同时检查通用文件名和保护原件提示。[R1 端到端](raw/b09-manual-upgrade-r1-module/stdout.bin) · [R1 配置缺陷](raw/b09-future-config-installed-repro/stdout.bin) · [R2 中间结果](raw/b09-manual-upgrade-r2/stderr.bin)

本机 Windows 应用控制阻止中文路径中生成的 console launcher（WinError 4551）。实测使用该环境由 PATH 解析的 `python.exe -I -X utf8 -m ruocun`，同时核实安装的 `ruocun.exe` 路径与元数据。原策略保持原样。直接 console 入口的 R1 成功另见第79票。所有运行回执经环境白名单与秘密扫描。[原始 launcher 拒绝](raw/b09-manual-upgrade-first/stderr.bin) · [第79票](../n79-probe/README.md)

复跑时将 `manual_upgrade.py` 复制到仓外，从仓外的 Python 经 `tools/run.py --cwd <仓外目录>` 启动，传入 `--old-wheel`、`--new-wheel`、`--wheelhouse` 和 `--runtime-lock` 的绝对路径。R3 加 `--require-config-protection --require-v2-shape-protection`。探针自行创建另一仓外环境和合成 HOME。
