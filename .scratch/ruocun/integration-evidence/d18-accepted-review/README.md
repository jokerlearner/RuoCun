# D18 二次修正最终独立复核：技术实验接收

**结论：本轮接受 D18 standalone 实验的二次修正。** 原生提交之前已有持久应用所有权，未确认提交／完成时材料不会随异常展开释放；真实 worker 入口最外层保护也覆盖诊断异常。没有发现新的实质阻断。本结论只供根代理登记 D18 技术收口，不改变统一状态，不代表产品运行时、独立账户、断电或最终 Windows Terminal 体验验收通过。

独立分支 `merge/d18-final`，worktree `.worktrees/m18q`。从 clean 的 `4048910744a7aab60a9bc75d721df9262a403292` 出发，先 quiet FF 统一集成，再 quiet no-ff 合入候选 `1860c70ad6109dbd09ac80ac7a2a118d77818012`，产生受测合并 **`d719be86b5d768270620dedc7d8db9ed870ff35e`**。读取了 AGENTS／CONTEXT、domain／tracker、ADR-0001／0002／0004、D18票、R-10／R-11与REC-12／WIN-04边界、冻结来源说明，以及 d18-first-review、d18、d18p、d18-final-review、d18q 完整报告和最终实现／测试。

## 两处阻断的复核

- `probe.pipe_io` 的 owner 在 ConnectNamedPipe／ReadFile／WriteFile 可提交之前登记，强持有原管道handle、event、OVERLAPPED、buffer及count。只有已返回的同步结果明确未pending／已完成，或997后的真实完成状态确认，才解除所有权并关闭event。尚未收到997时不会把Internal初值当作完成证明。无法确认的任意异常（包含BaseException）保留owner并抛出不可被普通OSError／TimeoutError吞掉的PendingIoUnconfirmed；poison后拒绝继续I/O，禁止断开或关闭其管道。
- `pending.py` 的真实CLI整个入口有最外层finally原生停止；诊断dump异常不能绕过。`entry.py` wrapper虽有安全保护，但测试同时要求`target_entry_returned_with_pending=False`与`python_atexit_reached=False`，因此wrapper不能把缺少目标保护的实现掩盖成通过。本轮真实入口诊断注入时，应用owner=1、Internal=259、event有效，随后由目标入口先原生自终止96；没有到达wrapper逃逸标记或Python atexit。

独立预期来自微软契约：[CancelIoEx](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex)只请求取消，完成前不能释放／复用OVERLAPPED；[GetOverlappedResult](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-getoverlappedresult)区分实际完成与996；[HasOverlappedIoCompleted](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-hasoverlappediocompleted)只用于已经997开始的异步操作。[TerminateProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess)之后仍须由外部held handle确认实际退出；发出终止请求不等于资源已回收。本轮重新核验这些官方页面，没有由候选输出反算预期。

## 独立运行与真实退出

以自有短venv／cache和本worktree独立`.t`依赖启动原`run.py m18q-independent-r01`，没有借用其它worktree环境。所有新venv、pip、pytest、probe、worker、审计及采集Python子进程明确使用OS变量白名单；HOME、配置、缓存、临时目录均指向合成工作区。精确入口和环境**变量名称**在`bootstrap.ps1`、`review.py`及对应`*.exit.json`，未保存整个父环境。采集日志先静默扫描，再只展示结果；真实父环境的敏感值比较及ZIP解压成员扫描见`sensitive-scan-*.json`，未匹配也未输出凭据值。

**原6＋新增取消／完成10＋新回归2，共18 passed in 9.79s。** 只运行这一完整新轮，没有重放原19轮或无关原生实验。归档[m18q-independent-r01.zip](m18q-independent-r01.zip)共245文件；执行前7份脚本原字节／SHA、exact命令、Python／Windows／依赖版本、stdout／stderr／exit和所有产物均保留。原raw轮次移动前已检查解析后的源／目标均在本worktree的预期raw／`.t`之内；新轮原字节保留在`.t/m18q-independent-r01`，不改JSON中的运行时原路径，不改原raw清单。

归档SHA-256：`9bef71032644c1ded923b4fffb092ece4f568f90a84772dd24919a79e8059c11`。成员清单见[round-manifest.json](round-manifest.json)，结构结果见[summary.json](summary.json)。

| 复核项 | 本轮证据 |
| --- | --- |
| 9个未确认场景 | 取消失败／1168预算等待／wait失败或异常／虚假wait后真实GOR996／GOR适配错误／真实pending读写取消失败／原生提交返回边界异常：原材料由应用owner持有，event有效、Internal=259、无提前close、poison复用拒绝，全部自终止96且未靠监督者补杀 |
| 真实OS完成 | 未注入CancelIoEx→995／STATUS_CANCELLED；真实pending ReadFile对端关闭→109／STATUS_PIPE_BROKEN，确认完成后释放，均正常退出0 |
| 诊断入口回归 | 受控observation写异常；目标最外finally先终止96，atexit与target escape均False |
| 受管进程 | 23份process／ready／cleanup的真实PID与创建时间一致；held handle全部signaled并关闭；强杀回执绑定原handle；另独立OpenProcess重查23个原进程均不存在（87），见[post-process-state.json](post-process-state.json) |
| 退出后管道 | 原始回执均确认缺失；另用独立CreateFileW重开14个实际管道名，全部真实返回2，见[post-pipe-state.json](post-pipe-state.json) |
| 原6项 | 四条发布路径均读到完整version=2；replace前强杀冷读旧1，replace后读新2；4路并发读malformed均空，服务端event 51开／51关；匿名token三对象真实拒绝5，独立账户仍not-run |

`ReplaceFileW`带backup的并发读本轮有10次打开错误2、7次错误32；其它三路无打开错误。原始可用性错误完整保留，未改写为内容损坏或隐藏。细节见[facts.json](facts.json)。

取消5／1168、wait适配失败／抛错及GOR适配错误均为Win32边界注入，native_called=false的返回不能算OS取消结果。提交回归的997来自真实ConnectNamedPipe，随后BaseException为受控注入，不声称真实Ctrl+C精确命中。诊断OSError也为注入，不声称真实磁盘写失败。RED安全锚的职责和早期失败在旧归档中保留，本轮绿色必须来自应用owner及目标入口保护。

## 历史审计与最新同步

原`verify.py --git`：874 raw、19轮快照及Git blob字节全部通过。旧m18归档134文件／11worker、d18p三归档108份worker回执、d18q两归档96份回执均由各自原审计通过；旧失败证据与清单原字节未改。

保留了旧fresh审计在当前实现上的**预期拒绝**：`audit-old-review-on-current.*`退出1，停于旧`audit.py:51`的源码SHA断言；它绑定73候选，不能用于宣称新实现失败或直接改旧assertion。随后在忽略目录`.t/m18q-historical-review`中建立精确旧源码只读视图：review文件取当前Git原字节，LAB脚本取原m18f ZIP的执行前h快照。原audit在该视图退出0，原16项、两个阻断与25份worker记录仍自洽。命令、哈希、拒绝与成功日志分别保存，见[historical-view.json](historical-view.json)。没有回滚当前实现，也未把旧候选重新接收。

完成本轮后 quiet no-ff 合入根正式tip **`cc90a65fa38604a0d5ac3ff92889e2321df5a00f`**，产生同步合并 **`c98578104572a0486523f7262380e5e9c0eefdc3`**。该变化仅D07实验／证据及统一文档；D18实现和既有证据路径零diff，7份受测脚本SHA仍逐项一致，因此依根指示只做相关差异与只读审计，不重跑无关native实验。见[sync-check.json](sync-check.json)。本复核后续提交仅添加本目录，未私改产品、候选、原期望、统一Status／map／spec／matrix；未删除其它worktree或私有cache。

最终只读入口：本目录`audit.py`校验本轮与既有审计结果，`seal.py check`额外校验14个管道回执、同步差异与全目录SHA。`seal.py stage`逐项对比Git暂存blob原字节后提交；`.gitattributes`保留证据原字节，缓存不纳入清单。

首轮封存／暂存字节检查均已通过，但隔离HOME下未配置Git作者，提交返回非零，HEAD仍为同步合并c985781。初版采集器只保存了自己的断言日志，未保存该次git commit的stderr，因此没有把推断当作原始提交报错。随后同一白名单环境的只读`git var GIT_AUTHOR_IDENT`明确返回Author identity unknown，原始输出保存在`identity-probe.*`。`collection-r01/`保留当时seal脚本、初版清单、敏感扫描及已通过的暂存回执，`seal-failure-stage-*/`保留失败断言。恢复仅给这次提交显式指定合成作者`Codex <codex@local>`，不读取真实用户Git配置，不改变全局配置；重新扫描、封存并再次逐项检查暂存blob。没有重跑业务探针或覆盖旧失败材料。

二次暂存检查又明确拒绝了采集清单问题：初版排除所有同名`evidence-sha256.json`，误把保存于`collection-r01/`的历史清单也排除；Git实际暂存了该文件，因此集合断言失败。`collection-r02/`保留修正前脚本／清单，第二次失败日志保留。最终只排除当前顶层清单，历史清单均作为普通字节纳入哈希，再次逐项比较；没有改动任何候选／历史测试断言。

本轮没有真实驱动取消卡死／超时、真实精确Ctrl+C竞态、真实诊断磁盘故障、断电、系统崩溃、重启、独立账户、远端机器、模型、产品或Windows Terminal最终体验证据。坏驱动若使终止等待仍不signaled，只能报告未确认，不可伪报OS回收；本轮所有退出均已实际确认。
