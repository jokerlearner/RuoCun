# D18 pending OVERLAPPED 所有权修正

分支 `impl/d18-pending-io`，worktree `.worktrees/i18f`，从 `3541a53` clean 起步，按要求 quiet 合入首次候选及独立复核 `3c8b969`，本地合并提交 `6713d4e`。本附录是修正候选，不改统一状态，不代表产品或最终用户验收。原 [首次独立复核](../d18/README.md)、m18 134 文件归档、原19轮874 raw及失败证据保留原字节。

## 真正修复的范围

仅 standalone durable-io 实验：`pipe_io` 收到真实 ERROR_IO_PENDING 后，任何未确认完成的异常都保留管道句柄、event、OVERLAPPED、buffer及count强引用；以不可被普通TimeoutError／OSError处理器吞掉的 `PendingIoUnconfirmed` 停止后续I/O。禁止复用、断开或关闭该 pending 管道。完成状态由 GetOverlappedResult 结果及等价于 SDK HasOverlappedIoCompleted 的 STATUS_PENDING 检查确认，保存实际成功／995／其它完成错误后才释放事件。

外层 finally 仍可清理其它受管worker；全局强引用跨这些栈展开存活。probe 最外层 finally 使用原生 TerminateProcess 自终止96，绕过会释放 ctypes 的Python shutdown；held handle 监督者确认进程真实退出后才能记OS回收。不是收到 kill API 成功就记退出。底层坏驱动可能连终止也不完成，监督等待有界，未 signaled 时不能报回收；本轮注入场景均已确认退出。

所有新子进程使用固定 Windows 必需变量 allowlist；不继承模型／服务密钥。没有新增产品隐藏端口，注入只在单独 `pending.py` 测试harness内包装Win32边界。没有改原六项测试期望。

## 独立预期依据

- [CancelIoEx](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex) 与 [取消pending I/O](https://learn.microsoft.com/en-us/windows/win32/fileio/canceling-pending-i-o-operations)：取消请求不证明完成，不能提前释放／复用OVERLAPPED；1168也不提供目标完成的证明。
- [GetOverlappedResult](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-getoverlappedresult) 与 [HasOverlappedIoCompleted](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-hasoverlappediocompleted)：仅在提交返回997后检查pending状态；FALSE／996表示仍未完成，完成可能有错误。
- [WinError 500–999](https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--500-999-)、[WinError 0–499](https://learn.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-)及[MS-ERREF NTSTATUS](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55)：独立固定预期995／STATUS_CANCELLED=0xC0000120、109／STATUS_PIPE_BROKEN=0xC000014B，没有从本轮JSON反算期望。
- [TerminateProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess)：会请求取消pending I/O，进程须在相关I/O完成或取消后才能真正退出；held handle signaled才是本轮OS回收边界。

## TDD与证据分层

`tdd.zip` 包含f01–f08的750个原字节文件；`tdd.json`绑定archive与成员SHA256，`tdd-summary.json`列各轮exit及66个进程，`tdd-os.json`独立OpenProcess重查全部原worker已不存在／退出。只读入口：`python .scratch/ruocun/integration-evidence/d18p/audit.py`。

| 轮次 | 结果与含义 |
| --- | --- |
| f01→f02 | CancelIoEx适配失败5，真实ConnectNamedPipe仍pending；RED观察到旧实现非法close event尝试，GREEN保留所有权 |
| f03→f04 | 真实CancelIoEx完成995；RED缺完成记录，GREEN读回固定完成状态后关闭event |
| f05→f06 | 新增边界覆盖；f05的3个失败来自测试安全锚误把同步ERROR_PIPE_CONNECTED=535路径的Internal值当pending。修正harness只在原生返回997后判断，不改实现／期望；失败原样保留 |
| f07 | 原6+新增10全量16 passed，9.11s |
| f08 | 加入poison后禁止再次提交的观察、坏驱动监督超时不伪报回收；全量16 passed，9.24s |

**边界注入证据**：取消5、取消1168后实际等满1500ms仍pending、首次wait返回失败／抛异常、虚假wait完成后真实GOR996、GOR适配错误6、真实pending读／1MiB写上的取消5。取消API在这些场景未按其名称向内核发出请求；注入项明确记录native_called=false，不冒充OS成功或真实驱动取消超时。未确认时观察原OVERLAPPED与原buffer被应用所有者持有、event仍可查询、无提前close尝试、poison复用被拒绝，随后原生自终止96；外层匹配实际PID／start，确认held handle signaled并关闭、管道不存在。

**真实OS证据**：未注入的原六项完整运行、真实CancelIoEx→995／STATUS_CANCELLED、真实pending ReadFile对端关闭→109／STATUS_PIPE_BROKEN。新增测试安全锚阻止RED实际触发UAF，但非法close尝试依然失败；GREEN的应用所有权另核对原生材料身份，不以harness安全锚替代实现。

每轮保留exact命令、Python／环境、脚本快照与哈希、stdout/stderr/exit。新轮从原raw移动至本工作树忽略目录`.t/pending-rounds`后独立归档，JSON中的原绝对路径不重写，未更新原raw清单。归档前已扫描当前敏感环境值和常见密钥形状，均0命中，不保存任何凭据值。

没有断电、系统崩溃、重启、独立账户、恶意同用户、真实驱动卡死、模型或Windows Terminal体验证据；D18技术收口仍待独立合并复核。

## 合入最新集成后的最终复验

实现提交`035ac8b`后 quiet 合入最新统一集成`84258fc`，产生`0468972`，无冲突、clean。f09以该合并提交及同一实现快照再次全跑：**16 passed in 9.49s**；`final.zip`保留226文件，`final.json`绑定archive及成员SHA256，`final-summary.json`记录21个受管worker的PID／创建时间／held handle清理回执，`final-os.json`再次OpenProcess重查原worker已退出。`final.zip`内8个未确认场景均event有效、原生状态259、应用持有原材料、复用拒绝，随后自终止96且没有需要监督者补杀；2个真实完成场景正常退出0。

最终只读检查均exit=0，原始stdout/stderr/命令/exit分别保存在`verify.*`（原入口`verify.py --git`，874 raw、19快照、Git blob字节通过）、`legacy.*`（原m18归档134文件／11worker保留通过）、`archives.*`（本次两份归档及87份worker清理回执通过）。原raw目录已恢复仅含原19轮；新失败轮与早期harness误报没有删除，而是原字节保存在独立ZIP。当前代码与final内harness哈希一致，最终提交仅追加此报告和复验材料，不再改变受测实现。

集成随后新增原生隔离研究线索，交付前再次 quiet 合入`70b835a`，产生`4eff4db`，无冲突。f10以该合并提交及同一实现快照全量 **16 passed in 9.24s**；另存`latest.zip`（226文件）、`latest.json`、`latest-summary.json`、`latest-os.json`，不覆盖f09。新增21份worker清理回执全部通过，三份归档总108份清理回执；`latest-verify.*`、`latest-legacy.*`、`latest-archives.*`再次原入口复验均exit=0。此后的交付提交仅添加这些证据及说明。
