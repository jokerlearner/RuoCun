# 批次 06 第 55 票独立复核

源码候选 `88c9ba67`（含 `07f1baa7` / A `8234c7a2`），已合固定产品 `0a0c1cea`。独立核 Python 入口/LSP源码在两保存点无差异；client.py SHA256 与真实服务回执一致：`9c88cb8ed2c3726116bb07bba02ba59092b01b9418641adaa59d4b6282de97e8`。只提交独审证据；白名单合成 HOME、项目、服务及模型，不改根纯安装环境。

## 来源协议与实际生命周期

原 `tests/test_b06_lsp.py` 独立实际 **2 passed in 0.44s**。覆盖配置整 server 后覆盖/坏文件跳过、扩展名路由与客户端复用；复用 D15 独立 fixture 的 UTF8 分帧/反序合包、UTF16 外部行列、中文空格 URI、didOpen v1→didChange v2、请求超时 cancel，以及 shutdown→exit 和实际进程退出。[来源回执](raw/b06-review-lsp-source/command.json)

源码独审 Windows 启动先 CREATE_SUSPENDED，再将实际 owned Popen HANDLE 挂入 KILL_ON_JOB_CLOSE Job，之后按该尚未恢复 PID 唯一初始线程 Resume；绑定失败仅终止本次拥有的进程/Job。关闭先给有界 shutdown/exit，最后核 Job 成员句柄、终止遗留树、等待 accounting 归零及句柄 signaled，正常父退出也清遗留子孙。POSIX 组设计未当成实机已验。

读循环在读 body 前检查 Content-Length，上限 16MiB；header 累计与 StreamReader limit 为 16KiB，非法/EOF使当前 pending 失败。取消/超时发送 cancel，旧 ID 移出 pending，迟到结果不配对新请求；关闭幂等任务等待实际收口，不以发出 kill 为退出证明。

独立[单条组合探针](b06-lsp-boundaries.py) 沿现有独立 Content-Length fixture 形状：旧请求超时后发迟到旧响应，同时新请求待处理，新请求仍只得到准确 fresh result；随后对端只发送 **16MiB+1 的长度声明、不发 body**，客户端立即以长度超限拒绝，没有等 body。对端故意不响应关闭/EOF且有真实心跳子进程，dispose 返回后两者保留的 OS HANDLE 都 signaled，心跳不再写入。[最终组合回执](raw/b06-review-lsp-boundaries-final/command.json)

此组合只实际执行消息体长度上限、迟到 ID 和挂住树清理；header 上限/EOF分支另为源码核对，没有虚报更多故障矩阵通过。

前几次组合探针卡在合成 Python 心跳子进程的就绪阶段，尚未进入 late/frame 断言。改用 base Python 仍红；仅将非协议子进程 stdio 从继承 LSP 管道改为 DEVNULL 后才稳定就绪并绿，产品未修改。该对照未进一步区分是哪一条继承 stdio 导致等待，不能推成产品 Job 缺陷。首轮在 finally 中打印了过早的“通过”文字，但回执明确 exit=1，不作为边界通过；最终探针已把成功输出移到所有断言之后。诊断 status/DEBUG 已删除。[最初无效夹具](raw/b06-review-lsp-boundaries/command.json) · [延长就绪仍失败](raw/b06-review-lsp-boundaries-r2/command.json) · [诊断](raw/b06-review-lsp-child-diagnostic/command.json) · [仅换解释器仍失败](raw/b06-review-lsp-base-child/command.json) · [隔离子stdio后绿](raw/b06-review-lsp-child-stdio/command.json)

## 普通 CLI 与真实服务器

[普通 pipe CLI 探针](b06-lsp-cli.py) 从用户 lsp.json 进入真实配置/manager/工具：ToolSearch 激活 LSP，真实 stdio 定义结果含中文空格路径及 UTF16 `:1:5`，下一模型请求准确消费。随后创建分支并 `/resume`：新会话的实际 SessionStart command Hook 独立读取旧服务 shutdown/exit 标记并检查进程退出，结果为 true；独审拥有的旧服务 HANDLE 同时 signaled。旧资源先完成，才进入新会话 Hook，没有替换旧运行闭包。

再移除配置，从普通 CLI 做 ToolSearch LSP，下一请求仍无 LSP schema、没有新服务输出；总计 **5 个模型请求**（配置路径3、无配置路径2）。[普通入口回执](raw/b06-review-lsp-cli/command.json)

真实第三方 TS 验证按 ADR-0015 复用 B 的固定候选证据，不重跑九组。已只读核[官方包与实际回执](../n55-real-server/README.md)、[结果/六个进程句柄](../n55-real-server/actual/results.json)、透明 wire 及 exercise：TSLS5.0.1/TypeScript5.9.3，冻结 sample 九操作与一次编辑同步均成立；client hash 运行前后相同并与本树一致，六个原活进程保留 HANDLE 在 dispose 后全部 Wait0，TSLS自然 exit0、遗留 tsserver 由 Job 终止 exit1，如实区分。不是仅安装版本或只查 PID 消失，也不扩张成所有语言服务器都已验。

本次独立运行回执敏感值扫描无命中。55 已审范围无阻断，可消费固定产品 `0a0c1cea` 的唯一里程碑出口；没有全量、构包、付费模型或体验代验。
