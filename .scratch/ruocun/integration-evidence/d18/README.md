# D18 独立合并复核：取消异常路径暂不通过

复核分支 `merge/d18-io`，工作树 `.worktrees/m18`。2026-11-05 从 clean 的 `c8f710c6027623a6918144f39211300568dcc161` 起步，先执行 `git merge --ff-only --quiet integration/ruocun-migration`，再 quiet no-ff 合入候选 `14fcde35586374480c8ac917a2cfb4dce638e8e3`，产生合并提交 **`75265981726fb7ea2f29b646f9960fa7a2120b8c`**。主代理集成提交在复核期间冻结。未触碰 `.worktrees/i18`、产品代码、原 19 轮证据、原测试期望或统一状态／map／spec／matrix。

**复核结论：原测试通过，D18 技术收口暂不通过。** 存在 pending OVERLAPPED I/O 异常退出时提前释放资源的代码缺口，交独立修正代理处理；本报告不改变 D18 任务状态，也不把实验测试通过解释为产品或最终验收通过。

## 阻断发现与最小修复验收

位置为候选的 `.scratch/ruocun-discovery/experiments/durable-io/probe.py`：

- **134–139 行**：已经收到 `ERROR_IO_PENDING` 后，若 `CancelIoEx` 返回非 `ERROR_NOT_FOUND` 的失败，或取消后 1500ms 的 `WaitForSingleObject` 仍未 signaled，就直接抛异常。
- **143–144 行**：初次等待返回异常也直接抛出，此时没有确认原 pending 操作终结。
- **151–153 行**：所有上述路径均进入无条件 `CloseHandle(event)` 的 finally；函数退出后，局部 `OVERLAPPED` 和 buffer 也不再保持强引用。因此“报本轮失败”与“安全释放原生 I/O 材料”之间缺一层所有权收口。
- **140 行**：正常取消完成路径调用了 `GetOverlappedResult`，但没有记录实际完成状态；本轮观测不能区分正常完成、取消完成和其它完成错误。

这是**静态代码审查发现**，不是声称本机真实驱动发生过 1500ms 取消不完成。本轮真实管道进行了 3 次 pending 取消，均在健康路径完成；原 6 项测试也未覆盖异常取消返回／取消完成等待超时。没有人为 mock Win32 错误或改期望使测试变绿。

触发条件为原生操作返回 `ERROR_IO_PENDING` 后，出现取消请求失败、取消完成迟于 1500ms，或等待 API 异常。Windows API 契约没有保证所有驱动都可立即完成取消；发出取消请求后，原 `OVERLAPPED` 仍可能被内核使用。[Microsoft CancelIoEx](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex)、[取消 pending I/O 的注意事项](https://learn.microsoft.com/en-us/windows/win32/fileio/canceling-pending-i-o-operations)均要求在真正完成之前保留相关结构。

最小修复应把 pending 操作的强引用与事件／管道所有权交给明确的收口路径：正常完成后读回并记录完成状态才释放；无法在取消预算内确认完成时，不能按普通异常展开局部资源。对于本独立 probe，可在持有原生状态的隔离 worker 内停止后续工作，由外层在有界时间内按实际 PID／创建时间／held handle 确认 worker 退出，使 OS 回收进程资源；也可使用等价、可审计的保留所有权方案。修正需要保留本轮证据，新增有界异常路径验证材料，分别证明取消失败、取消完成超时、wait 异常和普通成功／断开路径不会提前 free，并重新通过原 6 项测试及原始清单校验。若异常分支靠受控注入验证，应明确标为注入证据，不写成真实驱动超时实测。

## 独立执行与材料

读取了根规则、CONTEXT、相关 ADR（包括 ADR-0004）、D18 票、实验 README／latest／run.py／verify.py／test_probe.py／probe.py、冻结来源说明及对应规格边界。本票为 standalone probe；人工体验按 ADR-0004 集中到最终整体验收，本轮无需用户操作。

在 m18 独立安装依赖到本工作树的 `.t`，pip 缓存为 `$env:TEMP/ruocun-d18-m18-pip`；未借用 i18 环境。使用原入口和未占用轮次名：

```powershell
$env:PIP_CACHE_DIR = Join-Path $env:TEMP 'ruocun-d18-m18-pip'
python -m pip install --target .scratch/ruocun-discovery/experiments/durable-io/.t -r .scratch/ruocun-discovery/experiments/durable-io/requirements.txt --disable-pip-version-check
python .scratch/ruocun-discovery/experiments/durable-io/run.py m18-independent-r01
```

结果为 **6 passed in 5.21s**。精确命令、环境、解释器 SHA、依赖、stdout/stderr、exit、4 份当次 Python 字节快照及全部 probe 产物保存在 [m18-independent-r01.zip](m18-independent-r01.zip)，共 **134 个文件**。归档 SHA-256：

`d306080b1a76567988920c282de66c69b8488d49d5ee160ba59c17e018f25704`

归档成员由 [round-member-sha256.json](round-member-sha256.json) 绑定，整套复核材料由 [evidence-sha256.json](evidence-sha256.json) 绑定。新轮生成后以原生 `Move-Item -LiteralPath` 从 probe/raw 移到本工作树被忽略的 `.t/m18-independent-r01`，保留字节，再归档；未覆盖旧轮次或重写原 raw 清单。归档仍保留运行时原绝对路径，物理位置调整不重写其 JSON。

原 `verify.py --git` 在合并后、独立运行前通过一次；新轮移出原 raw 后再通过一次，后者原始输出为 [candidate-verify.stdout.json](candidate-verify.stdout.json)，命令和退出码见 [candidate-verify.exit.json](candidate-verify.exit.json)。原 **874 raw 文件、19 轮 snapshot、Git archive blob 字节**全部吻合，包括失败轮次。只读重验独立归档与原校验结果：

```powershell
python .scratch/ruocun/integration-evidence/d18/audit.py
python .scratch/ruocun-discovery/experiments/durable-io/verify.py --git
```

[summary.json](summary.json) 给出独立结果；[post-process-state.json](post-process-state.json) 记录追加的 OS 读检查。`audit.py --capture` 是一次性采集入口，会拒绝覆盖本轮归档；通常复核只运行无参数入口。

## 独立结果与限制

| 检查 | 本轮结果 | 解释边界 |
| --- | --- | --- |
| 四条发布路径 | 都读到完整 version=2 合成回执；发布后 ACL 实际读回 | 目录 `READ|WRITE` flush 成功，只读返回 5，POSIX os.open 路径 errno=13；均不是断电证据 |
| 临时共享占用／ACL 暂拒 | 都真实返回 5；7／8 次尝试后分别在 0.235／0.281 秒发布 | 错误 5 本身不能区分共享与 ACL 原因；场景已知才开启暂拒重试 |
| 永久占用／永久 ACL | 前者 10 次后 0.359 秒耗尽；后者 1 次立即报永久拒绝；旧 version=1 均保留 | 350ms 是重试预算，调度造成轻微超出；不等于把阻塞 native 调用变成硬实时截止；candidate 不是终态 |
| 崩溃冷读 | replace 前强杀读旧 1；replace 后强杀读新 2 | kill 绑定原 held handle 与创建时间；只覆盖进程崩溃 |
| 独立并发读 | 每路径 40 次发布；分别 202／253／152／233 次完整读取，均见 41 个版本；malformed 全空 | `ReplaceFileW` 带 backup 路径有 7 次打开错误 2 和 3 次错误 32；其它三条本轮无打开错误。没有把可用性错误改写为内容损坏或隐去 |
| 真实进程退出 | 11 个受管 worker 的 ready/process/cleanup PID 与创建时间逐一匹配；held handle 全部 signaled 且关闭 | 另以 OpenProcess(QUERY_LIMITED_INFORMATION|SYNCHRONIZE) 重查，11 PID 均不存在（87）；未按裸 PID 终止进程 |
| 健康管道资源路径 | 服务端事件 51 开／51 关，客户端 48／48；管道关闭后返回 2；服务端 ready=144、关闭后143 | 首次安全／随机 API 缓存增长保留在原记录；这些数量不证明未触发的异常取消路径安全 |
| ACL 身份尝试 | 当前身份三类对象均可实际打开；匿名模拟 token 均拒绝 5 | 独立账户仍为 not-run；同用户其它进程同属信任边界；HMAC 不替代 ACL |
| 管道协议 | 错 key/run、stale epoch 拒绝，epoch 可前进；静默连接服务端约0.359秒超时，半帧断开109 | 合法最大4096／超长4097是 probe 的字节帧界限；不能替换冻结来源65536字符缓冲或产品最终契约 |

本轮未进行断电、系统崩溃、重启、注销、独立账户、远端机器、真实模型、完整 Agent 或 Windows Terminal 用户体验验收。原 6 项 probe 测试和自动资源观测各自保留，不代表上述项目通过。取消异常缺口修复并经再次独立复核后，才可重新考虑 D18 技术收口。
