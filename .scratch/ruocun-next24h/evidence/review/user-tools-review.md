# 21 问答与用户消息独审

受审候选为上下文端口 `719dac7`、工具 `022318a`、普通入口与 schema 接线 `dfab138`，以及来源描述修复 `9d074bd`。独审树 `1c74d27`，本票工具与普通入口接缝剩余审查阻断 0。

对照冻结 `src/tools/ask_user.ts:58–121` 与 `send_message.ts:25–47`，简写与结构化问答、顺序多问题、空回答、讨论后跳过剩余问题、附件 UTF16 截断及主动提示语义均沿来源。问答取消将当前轮暂停并保存中断配对，普通空答案继续按未回答记录。共享 schema 落实来源 array 的 minItems/maxItems，回调在工具配对保存后显示 SendUserMessage 的正文与附件。

独立复用原问答来源测试、普通 TTY 与 registry 测试，**25 passed in 5.36s**。6 个受影响源码 mypy 与定向 Ruff 通过。另以 [user-tools-runtime.py](user-tools-runtime.py) 复用既有普通 TTY 注入方式实际验证多选 `1,2` 返回 A/B，讨论选择跳过后题，Send 主动消息与附件正文实际进入同一输出 owner，以及 Esc 返回用户中断、配对已保存、调度 paused 且无第五个模型请求。单一接线场景通过，没有新增测试框架。

独审发现 AskUserQuestion 中文 description 误拼入 schema 描述与工具名的实际来源差异。冻结描述逐字对照首先失败，`9d074bd` 删除 6 个额外字符串后，同一 [来源绑定](verify-user-tools-source.py) 证明 AskUserQuestion 与 SendUserMessage 的中英 description 全部与归档逐字一致。原失败和绿色回执保留，字符串修复未重复运行无关功能。

全部回执均来自明确白名单与合成 HOME/config/TEMP，显式加载独审源码，exit 0、scan_hit=false，唯来源绑定红回执按实际 exit 1 保存。此次只提交审查与合成接线证据。完整终端模态视觉、Windows IME/缩放和用户体验仍待对应后续票与人工验收。
