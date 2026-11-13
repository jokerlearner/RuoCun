# 批次 04 第 48 票 Hook 命令与 Windows Job 独立复核

冻结候选 `391044b`（集成同补丁 `1c8b3cd`），独立工作树从 `042e6da` cherry-pick。白名单使用合成 HOME、会话及仓外临时目录。两次进程退出码 0，敏感值扫描均无命中。

- `tests/test_n48_hooks.py` 与直接受影响的 `tests/test_n14_output.py` 共 6 项通过。真实 Hook 收到无额外换行的 UTF-8 JSON，args 为原 JSON 字符串，兼容事件/工具变量可见、合成密钥环境变量被过滤。选择、命令顺序、deny 优先级和 exit 2 保持。原 Shell 默认仍为 DEVNULL stdin、两流合计 10 MiB，原有增量输出、原始字节、双流 EOF、CLIXML、cmd 方言测试通过。[回执](raw/b04-review-hooks-native/command.json)
- 复用既有 Windows Job 的子孙夹具，将真实 Hook 的绝对时间设为 2 秒。2 MiB stdin 无进程读取，孙进程持续写文件并刷 stdout。实际 2.031 秒返回，审计为 timeout，原子进程与孙进程的已持有句柄均在返回时 signaled，文件继续观察后保持不变。部分输出没有被当作命令决策或上下文。临时目录正常清理。[复现](b04-native-hook-timeout.py) · [回执](raw/b04-review-hooks-timeout/command.json)

命令引擎与受管 stdin 接缝无阻断。工具意图、权限与普通入口接线待后续候选审查。本次仅新增独立证据。
