# T04 子运行时接线保存点

状态：实现与定向自动验证完成，已冻结并交独立复核；不代表用户终端体验验收。

## 范围与实际接口

- 产品只改 `src/ruocun/agent/run_agent.py`、`tasks.py`、`resume_agent.py`。保留既有父上下文复制时 `archiveRead=None`，再由各子 journal 按自己的持久 `run_id` 绑定读取。
- `runPreparedAgent` 复用主路径 `ContextManager.before_request`，实际输出限制与请求体预算相同；溢出回调为 `recover_overflow`。
- 同步及后台 journal 的 `compact_context(..., rewrite=...)` 通过 `Conversation.stage_background` 发送到 run scope；只有保存确认后交换内存消息。同步保存及压缩保存保留独立 operation ID，结果未知后沿现有 blocked/停止路径处理，不重发模型或工具。
- `PreparedAgentRun.archive_source_scope/archive_source_indices` 只由可信分派或恢复入口填写。fork 使用父投影实际保留的位置；`prepareAgentArchive` 获取所选当前来源闭包并核对完整相同前缀，新分派说明作为显式尾部追加。
- 普通子代理不继承父 archive callback；普通子代理、同步/后台 fork、TaskSend、显式 recovery 和前台转后台分别使用自己的目标 run scope。转后台原实现会新建 run ID，本次复制可信来源闭包，并保留输出来源边界。
- `agentOutputOffset` 以导入闭包内真实逻辑消息数计算输出边界；`agentOutputMessages` 通过 `archive_export` 分页读原文。因此压缩后最终结果、TaskOutput、重开会话后的活动及后台 progress 不再切分压缩投影的旧下标。

## TDD 与证据

全部模型请求均为 loopback HTTP 合成 fixture。外层 runner 与内层 CLI 使用明确环境白名单、合成 HOME/config/workspace；源码优先 `-I -B -X utf8`，未运行真实模型或读取真实配置。

| 垂直片 | 红证据 | 绿证据 |
| --- | --- | --- |
| 子代理实际输出默认随窗口调整 | `t04-child-01-cap-red` | `t04-child-01-cap-green` |
| 子代理工具结果压缩与 scope 归档读取 | `t04-c2-red`、`t04-c3-red` | 对应 `-green` |
| 后台 TaskOutput 在摘要后保留早期原文 | `t04-c4-red-r2` | `t04-c4-green` |
| 同步 fork 继承当前可见摘要的来源闭包 | `t04-c5-red` | `t04-c5-green` |
| TaskSend 新 run 导入原 scope 的压缩来源 | `t04-c6-red` | `t04-c6-green` |
| 后台 fork 读取继承闭包 | 在 `t4d-r` 中该参数用例通过 | `t4e-g` |
| 显式重开已完成会话后 TaskOutput 仍含早期原文 | `t4e-r` | `t4e-g` |

无效或环境失败的中间证据仍保留：`t04-c4-red` 未实际触发摘要，不能算产品红；`t4d-r` 的 reopen 首次使用 latest 会选未完成会话而新建会话，改为首进程公开打印的显式 session ID 后才得到 `t4e-r` 的真实原文缺失红。早期长标签的 SQLite 路径超过 Windows 路径界限，后续采用短标签与 `e` 合成环境目录。

既有 `test_n38_agent_sync.py` 的两个结果回执丢失用例在 `t04-reg-a` 首次失败。原因是故障注入函数旧签名拒绝 T03 新增 kwargs，尚未进入注入点；经 root 明确授权，只给 `lose_result_receipt` 加 `**kwargs` 并透明传入原保存入口，故障触发位置和全部结果未知断言不变。随后两种回执分支均通过。

## 最终验证

```powershell
& '.venv/Scripts/python.exe' -I -B -X utf8 '.scratch/deepseek-compaction-20261113/evidence/run_checks.py' 't4e-g' pytest tests/test_deepseek_child_compaction.py tests/test_n38_agent_sync.py tests/test_n40_agent_tasks.py tests/test_n67_agent_handoff.py tests/test_b02_agent_entry.py
# 24 passed in 52.98s

& '.venv/Scripts/python.exe' -I -B -X utf8 '.scratch/deepseek-compaction-20261113/evidence/run_checks.py' 't4rec' pytest tests/test_b02_agent_background_entry.py
# 6 passed in 28.40s
```

- `t4s-rf`：上述三产品文件、新增测试和 n38 既有测试 Ruff 通过。
- `t4s-my`：三产品文件 mypy 通过。
- 新增 `tests/test_deepseek_child_compaction.py` 共 7 个普通 CLI 实例；观察的是最终模型 HTTP 请求和实际工具结果，不测试私有 journal 的实现步骤。
- 现有回归覆盖作用域隔离、并行失败、取消/轮次预算、未知副作用/回执丢失、前台转后台、跨进程普通与同步代理恢复、fork 恢复拒绝、TaskSend。
- 运行记录、环境说明及完整合成 stdout/stderr 均在对应目录 `command.json/stdout.txt/stderr.txt`，label 不可复用覆盖。

后续由独立复核代理审查接缝并亲跑新增入口；由 root 统一构包与全局验收，不重复扩大测试矩阵。
