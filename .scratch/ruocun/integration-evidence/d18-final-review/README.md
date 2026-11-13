# D18 fresh 独立复核：两个异常出口仍不接收

冻结集成 `70b835a9c820f4171199d0790af6f99a1d1c8875`，候选 `73e63d387654316ee2a415d7e47547725caf40d9`。从 clean 的 `.worktrees/m18f`、分支 `merge/d18-pending-verified` 出发，先 quiet FF 当前集成，再 quiet no-ff 合入候选，合并提交 **`069def00672567e1ad7e0c6fdbd6ba3adbb13911`**。原候选、首次失败复核、原19轮、修正归档和各自 SHA 均保留；未修改候选代码／测试期望／原清单、产品、统一 Status／map／matrix，未触碰 i18／i18f 活动材料。

**结论：指定16项全绿，但 D18 修正仍不接收。** 当前已登记 pending 之后的取消失败／等待异常路径能保留材料并原生终止；提交返回到应用登记所有权之间，以及新增 worker 的诊断异常出口，仍存在下面两个缺口。

## 阻断1：原生提交完成与应用登记 pending 之间有提前关闭窗口

候选 `probe.py:137` 初始 `pending=False`；`141`／`145` 调用真实 ConnectNamedPipe／ReadFile／WriteFile，直到 `152` 才登记 `pending=True`。若原生调用已经返回 ERROR_IO_PENDING，而 Python 在该调用返回／状态登记边界抛出 BaseException，`195` 的 finally 仍走普通关闭 event，未向 PENDING_IO 转交原 OVERLAPPED／buffer／count。此时最外层 `804` 的 stop_pending_process 也因列表为空不能保护资源。框架没有排除此类异常，中断目标与该窗口直接相关。

独立最小 seam 在**真实 ConnectNamedPipe 返回 FALSE／997 后**立即抛出 `SubmissionBoundaryInterruption(BaseException)`，不改候选。正式证据见 `submission-interruption-r02/result.json`：真实 Internal=259、event 有效、**非法 event close 尝试1次、应用 owner=0**。现有测试 Boundary 仅抑制该次真实 close 并保留 OVERLAPPED 安全锚；复核脚本在自己的 finally 直接原生 TerminateProcess(96)，避免实际 UAF。因此该安全锚没有掩盖失败：非法尝试和缺失应用所有权均原样记录。

这是**提交返回边界受控异常注入**，不是声称真实用户 Ctrl+C 恰好命中了该时序，也不是伪造 OS 997。共享提交代码中的 ReadFile／WriteFile 有同类静态窗口，本轮只对 ConnectNamedPipe 做这一最小确认。

最小修复建议：在进入可提交原生 I/O 的边界之前建立持久应用所有权，确保任何无法判定提交／完成状态的异常都保留原材料并 fail-stop；只有确定同步未提交或真实完成之后才解除所有权和关闭事件。不能仅在 `pending=True` 之后增加 catch，也不能依赖测试安全锚替代应用持有。尚未收到997时不能无条件把 Internal 初值当作完成证明。

## 阻断2：新增 pending worker 的诊断异常可以进入 Python shutdown

`pending.py:143–152` 在捕获未完成 I/O 后写 observation，再于 `153–154` 执行 stop_pending_process；`204–206` 的 worker 入口缺少最外层 finally 保护。若 observation 写入等诊断步骤抛异常，原生终止不会执行，Python 会进入 shutdown，随后可能析构仍活跃的 ctypes 材料。

独立运行候选原 `pending.py` 入口，只对 observation 写入边界注入 OSError。正式证据 `shutdown-diagnostic-r02/result.json` 记录：**Python atexit 已到达，真实 I/O 仍 Internal=259、event 有效、应用 owner=1**。复核专用 atexit 回调先记录这个不安全出口，再调用原生 stop_pending_process(96)，在全局材料拆除之前终止进程。没有真正释放活跃材料，未声称真实磁盘曾写失败。

最小修复建议：worker 的整个调用入口以不可绕过的最外层 finally 执行原生 fail-stop；保留材料到该边界，诊断本身失败也不能走普通 Python shutdown。该保护须覆盖诊断、复用检查及证据输出异常。

## 独立执行与结果

读取根 AGENTS／CONTEXT、domain／tracker、相关 ADR、D18票／首次复核指针、规格 R-10／R-11 和 Windows 边界、d18／d18p README、实现及新增测试。所有新测试、安装、审计和 worker 子进程均由 `safe_env.child_env` 固定 OS allowlist 启动，pip 使用 `--isolated`。独立短 venv／cache 的精确位置见 `setup.json`，没有借用其它 worktree 的环境；未把整个环境作为 pytest 参数或失败 repr。

运行入口为本目录 `review.py`：创建自有短 venv，按原 requirements 安装至本 worktree 的 `.t`，然后执行原 `run.py m18f-independent-r01`。精确命令、时间、环境变量名称、stdout／stderr／exit 分别保存于同名材料。只新增这一完整轮次，**16 passed in 9.11s**；归档 `m18f-independent-r01.zip` 的226成员及6份脚本快照由 `round-manifest.json` 绑定。新轮移出原 raw 至本 worktree 忽略目录 `.t/m18f-independent-r01` 后归档，没有覆盖原轮次或修改原清单。

| 指定检查 | 独立结果 |
| --- | --- |
| 原6项＋新增10项 | 16 passed，9.11秒 |
| 原 `verify.py --git` | 874 raw、19轮快照、Git blob原字节均通过 |
| 首次 m18 `d18/audit.py` | 134文件、11worker及原失败结论保留通过 |
| 修正 `d18p/audit.py` | tdd／final／latest三归档、108份worker退出回执通过 |
| 当前8个未确认场景 | 应用 owner保留、event有效、无early close、复用拒绝；自终止96后held handle确认退出 |
| 当前真实OS完成 | 未注入 CancelIoEx→995／STATUS_CANCELLED；真实对端关闭→109／STATUS_PIPE_BROKEN |
| 新两个缺口的安全确认 | 均独立记录unsafe出口，随后原生终止96，真实管道打开返回2 |

原新增测试中的取消5／1168、wait失败／抛异常、虚假wait与GOR适配错误仍按注入记录，native_called=false 的返回不算OS取消结果；真实GOR996与真实995／109分别保留。没有把原全绿测试扩展解释成未覆盖异常路径安全。

两类最小确认的 r01 原始日志／回执保留；早期辅助脚本未在执行前保存自身快照，故各追加 r02，在启动 worker **之前**保存完整复核辅助脚本及候选3脚本原字节／SHA，不重写 r01。正式阻断确认以 r02 为准；不是新增业务场景或重跑原19轮。两个r01和两个r02均通过held handle确认退出，合计本轮21＋4＝**25个受管worker**身份／创建时间／signaled／关闭回执通过，另以 OpenProcess(QUERY_LIMITED_INFORMATION|SYNCHRONIZE)重查原进程退出，见 `post-process-state.json`。管道缺失依据真实打开返回2，未按裸PID扫杀，也未把发出Terminate请求当作已退出。

只读复核入口：

```powershell
python .scratch/ruocun/integration-evidence/d18-final-review/audit.py
```

`audit.py --capture` 只用于本轮一次性追加总结／OS重查；普通入口校验归档成员、脚本快照、退出回执、原审计结果、敏感内容和整套 `evidence-sha256.json`。提交前另由仍能看到当前真实敏感环境的父采集进程扫描全部新增文件及ZIP解压成员，只报告有／无，不保存或打印凭据值；结果见 `sensitive-scan.json`。

首次封存清单误含 Git 忽略的 `__pycache__`，staged 原字节检查已明确失败；PowerShell 当时没有因原生 Python 非零退出停止，留下中间提交 `a355641`，不作为交付。原拒绝清单／扫描记录保留于 `collection-r01/`，调整原因见 `collection-adjustment.json`。后续仅修正本复核材料的清单，排除缓存，再核对所有 staged 原字节并通过检查后提交；候选实现、原测试期望及任何历史证据未改，未重跑业务测试。

## 依据与边界

[Microsoft CancelIoEx](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex)要求实际完成之前不能释放或复用 OVERLAPPED，取消请求本身不代表完成。[GetOverlappedResult](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-getoverlappedresult)和[HasOverlappedIoCompleted](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-hasoverlappediocompleted)支持已开始pending操作的状态判断；未提交状态不能被误读成已完成。[TerminateProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess)的原生自终止不返回，外部终止须等待进程；pending I/O 完成／取消之前进程不会真正退出。上述官方页在本轮重新核验，未引用外部二手材料。

没有真实驱动卡死／取消超时、精确用户中断竞态、真实诊断磁盘失败、断电、系统崩溃、重启、独立账户、远端机器、模型、产品或 Windows Terminal 体验验收。本报告只将已确认的两处代码异常出口退回继续修正；原来源失败审查始终保留，不能用绿色probe代替最终门禁。
