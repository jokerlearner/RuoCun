# D18 提交边界与 worker 最外层终止保护修正

继续同一 `impl/d18-pending-io`／`.worktrees/i18f`。从 clean 的旧候选`73e63d3`开始，先 quiet FF 合入 fresh merger 完整证据提交`8c0bc48`，读取[二次未接收报告](../d18-final-review/README.md)，再进行两条回归的 red→green。旧候选、原19轮874 raw、m18、d18p及fresh review整套字节未改。本报告只提交修正候选，不自行改变统一状态或宣布技术收口。

## 修复范围与独立预期

1. `probe.pipe_io` 在原生 ConnectNamedPipe／ReadFile／WriteFile 调用之前，把OVERLAPPED、buffer、count、event及管道句柄登记为持久应用所有者。只有原生调用返回且明确同步完成／未形成pending，或已开始pending的完成得到确认，才解除所有权并关闭event。返回到应用判断之间发生异常时，不再依据默认`pending=False`释放；未获997前也不读取Internal初值推断完成。
2. `pending.py` 整个实际CLI入口最外层`finally`调用原生`stop_pending_process()`；诊断、复用检查或输出再抛异常也不能进入Python shutdown。新`entry.py`仅为测试真实CLI入口的诊断写入异常，自己的最外层同样保护，并在目标入口逃出时记`target_entry_returned_with_pending`；测试同时要求该标志与`python_atexit_reached`均False，不能由测试wrapper掩盖目标缺口。

独立期望仍来自[CancelIoEx](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex)、[取消pending I/O](https://learn.microsoft.com/en-us/windows/win32/fileio/canceling-pending-i-o-operations)、[GetOverlappedResult](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-getoverlappedresult)、[HasOverlappedIoCompleted](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-hasoverlappediocompleted)与[TerminateProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess)：实际完成前材料必须存活；提交取消不等于完成；未提交状态不能用作pending完成证明；原生自终止须由外部held handle确认退出。两处回归的失败预期由fresh reviewer独立发现给出，没有从本轮结果反算期望。

## red→green与注入边界

| 轮次 | 结果与意义 |
| --- | --- |
| g01→g02 | 真实ConnectNamedPipe返回FALSE／997后立即注入BaseException。RED：真实Internal=259时early-close尝试1，应用owner=0；GREEN：原材料被应用持有，无early-close、禁止复用、自终止96后held handle确认退出 |
| g03→g04 | 真实pending且应用owner=1后，在observation写边界注入OSError。RED：进入Python atexit=True；安全回调在全局拆除前原生终止96。GREEN：目标CLI最外层先终止，atexit=False且target_entry_returned_with_pending=False |
| g05 | 原16＋新2全量18 passed，9.84s |
| g06 | 按根新AGENTS环境规则把HOME／USERPROFILE／APPDATA／LOCALAPPDATA／XDG配置与缓存／TEMP改为本实验`.t/env`合成目录；相同18项passed，10.20s |

两条新回归均明确是边界异常注入。997来自真实原生提交，不冒充真实Ctrl+C命中；诊断OSError是受控注入，不冒充真实磁盘故障。RED安全锚保留OVERLAPPED且抑制非法CloseHandle，atexit锚在ctypes拆除前终止；非法关闭或shutdown标志仍让测试失败。GREEN必须由应用所有权及目标最外层保护成立，不能靠锚变绿。没有扩展MemoryError等无限异常矩阵。

真实OS证据仍单列：原六项真实文件／进程／管道、未注入取消995、未注入断管109、真实pending读写，以及所有held handle退出观测。坏驱动卡死／真实取消超时、真实精确用户中断、真实诊断磁盘失败仍未验。

## 材料与审计

`tdd.zip`保留g01–g06共585个原字节文件；`tdd.json`绑定archive及成员SHA，`tdd-summary.json`列50份PID／创建时间／held handle signaled／关闭清理回执；`tdd-os.json`再次OpenProcess确认原worker已退出。每轮在执行前保存脚本快照及SHA，exact命令、Python环境、stdout/stderr/exit保留。g01、g03失败未改；新轮从原raw移至本worktree忽略目录`.t/guard-rounds`后独立归档，不改JSON原路径或原raw清单。

所有子进程均为固定OS变量allowlist；g06起HOME／配置／临时目录进一步固定为合成工作区。归档前在原始成员上扫描父采集进程可见的敏感环境值与常见token形状，均0命中，不保存或输出任何秘密值。新证据全部`-text -diff`，跨worktree按原字节校验。只读入口：`python .scratch/ruocun/integration-evidence/d18q/audit.py`。

产品、模型、断电、重启、独立账户及Windows Terminal体验验收仍无新增证据，原16项和新增2项绿色不代替fresh merger复核。

## 最新集成同步与最终检查

实现及首批证据提交`432479e`后 quiet 合入根集成`6fbbda8`，产生`2f5a4ae`，无冲突；已读取其新增AGENTS环境隔离规则。g07在该合并状态全量18 passed in9.59s。pip元数据采集曾在仓库根产生3个缓存文件，已原字节移至本实验忽略目录`.t/stray-pip-cache`；随后显式固定PIP_CACHE_DIR／命令行cache路径、禁用pip配置／自更新检查与用户site，g08再次全量 **18 passed in9.57s**，仓库根未再生成pip目录。没有读取真实用户配置或改动旧证据。

`final.zip`另保留g07／g08的490文件，不覆盖首批归档；`final.json`绑定成员字节，`final-summary.json`／`final-os.json`记录46份身份、退出和OS重查。本轮合计96份受管worker清理回执全部通过。当前7份实验脚本与g08执行前快照SHA一致；g08环境记录git_head=2f5a4ae及最终safe_env／run的实际字节哈希，后续只提交这些受测字节、报告和审计材料。

原入口检查`verify.py --git`为874 raw／19快照／Git blob通过；原m18审计、旧d18p审计及本次d18q审计exit=0，命令与原始stdout/stderr/exit分别在`verify.*`、`first.*`、`previous.*`、`current.*`。fresh review的原`audit.py`还要求当前LAB源码必须等于73候选；在已修正源码上按其原入口运行返回1，失败停于第51行源码哈希，原始拒绝保存在`review.*`，不把这个结果伪报为通过。

随后在忽略目录`.t/review-replay`建立只读历史视图：复制原review的tracked原字节，LAB脚本仅取其原m18f ZIP内h快照，不回滚或更改当前实现；原audit在该历史视图exit=0，见`review-replay.*`。它证明原16项／旧两个阻断及25worker记录仍自洽，不代表旧候选被接收。报告初稿曾把所有审计笼统写为0，已据实际拒绝纠正；失败日志和中间提交保留。对原raw／raw清单／d18／d18p／d18-final-review另做git diff，均无字节变化。

交付同步根集成`4048910`（D17独立实验归档及状态文档），quiet merge为`7c99f1b`，无冲突。与g08绑定的7份durable-io脚本SHA逐项仍一致；依主代理要求不重复运行无关实验，D18最后全量结果仍为g08的18 passed。原始证据及本次96份清理回执再次按清单校验通过。
