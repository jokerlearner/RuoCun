# 批次 05 第 53 票及 26 暂停恢复补充独审

独审产品已同步 `6d8f3d8c`，包含普通运行时 `a28a23be` 与暂停关闭 `2601a73e`。仅执行风险接缝，白名单合成 HOME、回环服务、假账户，无真实凭据或付费模型。

## 53 能力与普通命令

`tests/test_n53_mcp_caps.py` 独立实际 **2 passed in 2.28s**。独立 stdlib 对端提供 tools/resources/prompts，验证前 5 工具可见、搜索激活后续工具，原始中文/空格 URI、资源二进制说明、prompt 角色与非文本消息，未绑定 elicitation 时 decline、绑定后 accept/content。同一工具先发三类 list_changed 再回工具结果，正文仍准确，后台目录刷新移除旧项加入新项；关闭排空发现请求。原生 add 配置持久化及失败不发布语义一并通过。[能力回执](raw/b05-review-caps-source/command.json)

源码核查 `_ReadTap` 回包槽由 connection 请求锁保护；SDK 消息回调只排队，独立 observer 取得请求锁后刷新目录，关闭后不再发布。配置写入在内存发布之前，坏 JSON/保存异常不被当作新增成功。add 禁用名的来源特殊边界、旧 holder 仍用旧配置直到 reconnect，保持既有明确说明，不改成新行为。

[普通命令探针](b05-mcp-commands.py) 使用已支持私密用户目录（`--private-userroot`）实际运行 `/mcp` 列表、off、禁用时 reconnect、进程重开、on、再次 reconnect。初始连接 1 次，禁用及重开/reconnect 后仍 1 次，启用与重连后共 3 次 initialize；原生 mcp_state.json 先保存禁用名，再准确清空。原 mcp.json 字节不变，真实 HTTP 模型端收到 **0 次请求**。[普通入口绿回执](raw/b05-review-mcp-commands-private/command.json)

原 probe 先用普通 mkdir 建用户根，读取配置成功但 toggle 拒写。按 diagnosing-bugs 保留原红，并在证据侧只包装 persist 区分“写入失败、关闭失败、状态未发布”：实际异常为 `AtomicFileError 私有 DACL 存在额外或缺失的访问主体`，发生在写端口；不是连接关闭问题。仅将根创建方式改为 ensure_private_dir 后原场景通过。产品没有改 ACL 或接管旧目录，这符合既有配置写回前提。该不受支持预置的红不算产品回归，也不把手工目录自动修复声称为支持。诊断包装已从最终 probe 删除。[原红](raw/b05-review-mcp-commands/command.json) · [区分性诊断](raw/b05-review-mcp-write-trace-r2/command.json)

53 已审范围无阻断，可供 54 消费。未把普通命令通过冒充所有交互 elicitation 或完整标准能力已验。

## 26 暂停关闭与 latest

[单条探针](b05-paused-continue.py) 在真实 loopback HTTP 流发送首个片段后，向运行 CLI 的 Python 解释器递交 SIGINT，走真实已注册处理器取消在途请求，实际退出 **130**。这是解释器信号交付，不是 Windows Terminal 实机按键证据。

随后独立子进程用受控 SQLite 读取真实 checkpoint：状态 **paused**、done 为 false、原 owner 不再存活。新进程 `--continue latest /session` 选中原 ID，原 HTTP 模型总请求数仍为 **1**。因此 `2601a73e` 保存暂停后再关闭的路径实际成立；补齐 [26 前报告](b05-sessions-review.md) 最后一段明确未运行的子项。[最终回执](raw/b05-review-paused-latest-r2/command.json)

初轮功能断言已经通过，但检查器在自身解释器加载 SQLite DLL 后，临时目录删除因 DLL 仍映射失败。记录保留为失败；将检查移到短命子进程，退出后再清理，同一功能断言和正常清理均通过。未为此改产品或吞掉清理异常。[检查器清理失败](raw/b05-review-paused-latest/command.json)

本轮所有回执敏感值扫描无命中，没有全量、构包或用户体验代验。26 该补充边界无阻断。
