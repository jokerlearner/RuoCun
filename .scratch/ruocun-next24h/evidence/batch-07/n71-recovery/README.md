# 71 恢复会话时的 eval 隔离

冻结来源 `src/index.ts:293–328` 的 eval/通道边界与原54 HTTP合成夹具。复用实际普通 CLI、真实 SQLite 检查点和回环 HTTP MCP 服务。白名单 `tools/run.py` 使用合成 HOME、项目指令和凭据。所有模型响应来自本地固定脚本。

首次普通运行确认项目指令进入首 system，MCP 工具已注册，明确 RPC 拒绝形成已提交工具结果。以原会话 ID 加 `--eval` 恢复后，首 system 重新装配，用户、助手、配对工具历史按原内容保留，模型请求只增加一次。MCP 工具目录为空且服务端协议记录无新增。随后沿54的原路径产生一次已经发生但结果未确认的外部写入。普通重开和 eval 重开都保留状态74。eval 重开后，MCP 记录与模型请求数保持原值，SQLite 里的工具记录保持逐条相等，外部写入计数仍为1。

同一个 HTTP 定向用例在 `f0d40b2d` 执行时失败，eval 重开使 MCP 记录由6条增加到11条。`30d78b0d` 通过全部断言。原 SSE 参数保持原测试行为，本回执只运行 HTTP 定向项。两条运行和 Ruff 的 `scan_hit=false`，回环服务与进程均收尾。合成测试回执见 `raw`。

旧队列另用一个实际 SQLite 检查点验证。Conversation 在 idle 状态确认 `/synthetic-old-skill` 与其磁盘正文投影，关闭后以空 stdin 管道启动普通 `run_cli --eval --continue`。`30d78b0d` 把旧展开正文送入一次模型请求，定向失败。`02ac776d` 返回0并显示跳过提示，模型请求数为0。再次打开 SQLite，原输入 ID、原文、已保存投影和历史用户／助手消息完整保留，队列状态为 `discarded`。测试只替换模型响应，保留真实会话、恢复和调度路径。两次运行与 Ruff 的 `scan_hit=false`，回执见 `raw/b07-eval-queued-*`。
