# D06 技术原型独立集成复核

结论：具备继续 D10 等技术路线与后续产品实施的条件。此结论仅接收可运行技术原型和自动证据；不等于 HITL 全通过，也不继承为产品 WT 通过。按 ADR-0004，剩余人工项交最终 77/78/85；本审查未关闭 D06，未修改 map、模块对应表、验收矩阵、CONTEXT 或父规格。

## 合并与环境

- 独立 worktree：`.worktrees/m06`；分支：`merge/d06-prototype`。初始状态 clean。
- 起点/integration：`35125492cb1b89545494b2a9ca6ba2da554cabd8`。先 `git merge --ff-only integration/ruocun-migration`，结果 Already up to date。
- 候选分支 `impl/d06-terminal` tip 核实为 `ad48d6c86d5e9b1dad0961c035c9f66641ac4b63`；再 `git merge --quiet --no-ff impl/d06-terminal`。
- 无冲突合并点：`9e643bff6bafaaee232c04e4788acfc2bbf63e4d`；父提交依次为上述 integration 与候选。
- 使用 m06 自有 `.venv`，Windows Python 3.11.9。`pip install --require-hashes -r requirements.lock` 与 `pip check` 成功，原始输出在 [r1](r1/)。锁 SHA-256：`79df88ff07692194aeb33f5a737166ed48ce954673f5d333a7968b6fba03ae7e`；11 个锁定包版本逐一核实。
- 只读核查本 worktree 中的冻结 ZIP；未读写活动 DAO，未操作 i06 程序、日志、终端、venv，也未请求用户重新操作。

## 独立复测与审计

完整结论见 [r3/report.json](r3/report.json)、[raw stdout](r3/pytest-stdout.txt)、[清理凭据](r3/cleanup.json) 和 [文件哈希清单](r3/manifest.json)。运行：

```powershell
.venv/Scripts/python.exe .scratch/ruocun/integration-evidence/d06/verify.py r3
```

r3 已存在，不应覆盖；复跑需使用新的 `r4` 等短目录。入口仅为本次集成审计，不改变原型或既有测试断言。

- 既有 14 项检查：**14 passed in 1.09s**。使用 m06 代码、m06 Python、唯一新 basetemp `r3/t`，禁用无关 pytest 插件自动加载。
- 覆盖粘贴归一化、280 JS UTF-16 单位与 6 行阈值、报告形状 paste、一次 FIFO 消费、Esc 顺序/草稿、双 Ctrl+C、同一 ptk 输入链、迟到/分片 DA/cell/CPR/focus、图形支持/不支持/超时、dispose、图片 fixture fallback，以及真实 worker 成功/失败/退出清理。
- focus 的 `ProtocolOutput.write_raw` 精确启用/关闭次数和顺序由原测试核实；正常 `/exit` 与可控 `/crash` 的实际 harness 日志均记 enabled→disabled→shutdown-complete，见 [focus-review.json](r3/focus-review.json)。这是协议自动证据，不是用户真实切焦点体验通过。
- 5 组 harness 日志均以 shutdown-complete 结束，资源列表为空。补充真实 worker raw 记录在 [worker-events.jsonl](r3/worker-events.jsonl)。同 owner 的 worker 事件 PID 经 OS 父子关系绑定到本次 venv launcher；两个精确进程 handle 均记录 creation time/可执行路径。detach 后旧 foreground cancel 被拒，两个进程仍运行；显式取消后 launcher 43052 与实际 worker 24140 的相同 handle 均从 WAIT_TIMEOUT=258 变为 WAIT_OBJECT_0=0，pump 完成，等待后无迟到事件。只覆盖本次单级 worker，不推出通用进程树/持久 runner 已实现。
- [candidate-files.json](r3/candidate-files.json) 核对候选目录每个 Git 跟踪文件的字节与候选 blob 相同，包括历史 raw 材料。源码/PS1/lock/fixture 不变。原目录 latest-automated 指针未改。
- [original-report-review.json](r3/original-report-review.json) 复核 3 轮历史报告的 stdout、lock 和全部 12 个代码 hash。首轮报告是在首次提交前运行，声明 HEAD `f2c96cbf` 尚无原型；其 12/12 hash 可绑定后来提交 `7036050`。第二轮声明 HEAD `acc85b7` 仅 11/12 与运行代码相同，NoProfile 修正未提交；其 12/12 可绑定 `d295a15`。最新报告 `20261105T070609Z-e9ad63` 的 12/12 同时匹配其声明 HEAD `d295a15` 和本次合入代码。前两轮不被扩大解释为运行时 HEAD 已包含未提交源码。
- [tdd-raw-index.json](r3/tdd-raw-index.json) 保存 8 轮已有 red/green 材料哈希与原始结尾摘要；阅读确认 trim 次序 red 与 focus 缺失开关 red 为真实行为失败；第 07 轮等待观察时序修正按原审计单列。没有把缺模块 red 或修正观察时序夸成产品完整性证明。
- [source-contract-review.json](r3/source-contract-review.json) 校验冻结归档的全部 checksums，并保存 7 个关键源码的 manifest hash/行号片段：`app/App.tsx:483-489,1335-1362` 的先 trim 后展开、粘贴归一化与阈值；`app/run.tsx:15-59` 内联及退出清理；`terminal_reports.ts:24-206` 唯一 reader、paste、迟到/分片/查询；`tab_attention.ts:30-66` focus 启停；mascot 状态抑制与锚点、imagePaste 5 MiB 界限和 width 实现。原型边界不等于全量机械复现。
- [fixture-review.json](r3/fixture-review.json) 对 manifest 全部 11 例核对文件字节/hash，并独立重算文本归一化与来源提交摘要。

审计入口的两次中断均保留：[r1 原因](r1/reviewer-abort.md) 是把运行时 HEAD 当源码快照的过强假设；[r2 原因](r2/reviewer-abort.md) 是未考虑 Windows venv redirector 的双 PID。r2 的既有 pytest 同样 14 passed；finally 已调用 shutdown，后续只读确认 PID 43780 已不存在，见 [post-cleanup.json](r2/post-cleanup.json)。只修审计入口，不改产品、原断言或旧 evidence；r3 才作为完整复核与精确清理结论。

## 技术约束与后续产品范围

输入由 ptk 单 reader 负责，ParserGate 仅插入其既有 VT parser；raw/cooked ownership 仍归框架。当前锁版本私有 parser slot 是显式候选风险，native console fallback 未验，需 D10 与产品适配封装。输出经同一 OutputOwner/run_in_terminal 队列，Rich 只在 StringIO 格式化；无第二个 Live writer。图形仅正向能力确认后的合成 12×12 Sixel，epoch/focus/modal/草稿/后台条件限制绘制。

完整六帧 mascot/首页动画及 CPR 锚点、owned viewport 重建、持久 runner/孙进程树/keep-background/重启接管、Windows 系统图片剪贴板、产品管道模式、真实标题/通知/唤醒锁和完整选择器并非本原型已实现能力，由对应产品票承担。最终 TUI 库、最低 Python 和发行形态尚未由本复核决定。

## 人工证据和最终待验清单

按 ADR-0004，已取得用户反馈仅为第一组“中文 IME/emoji 编辑、流式两条排队与第三条草稿、连续缩放及历史选择”回复“正常”。只保留这些子项；不据此标记任何整个产品 WT 行通过。i06 的活动 run `20261105T070656Z-49da20` 未在本审查中干预或自动退出。

WT 编号已与权威验收矩阵逐行核对，使用 WT-03 流式、WT-04 中断、WT-05 缩放、WT-06 面板、WT-07 焦点、WT-08 图形、WT-09 恢复，未采用早期研究中的另一编号排序。最终待验仍包括：

| WT | 尚需产品/最终人工证据的部分 |
| --- | --- |
| WT-01 | 组合期候选确认/撤销与 Esc 的完整场景、grapheme 编辑、字体/DPI/多屏等；不扩大第一组反馈 |
| WT-02 | 真实 WT 单/多行/大段/连续粘贴、分帧与转义形状、输入中间及问题框、拖拽/附件、系统图片剪贴板、耗时与峰值内存 |
| WT-03 | 完整产品及真实模型的流式队列/模态/输入延迟；原型第一组主观反馈仅限指定场景 |
| WT-04 | 真正键盘操作下模态→清队列→暂停、Ctrl+C/Ctrl+D、worker 前后台与显式取消；产品持久后台/进程树 |
| WT-05 | 完整产品长时输出/超高消息、reflow 残影、滚动复制、共享/自有窗口、字体和缩放变化；保留已取得第一组反馈 |
| WT-06 | 真实快捷键截获、面板/问题/审批焦点层级，以及产品选择器、主题/语言 |
| WT-07 | 实际焦点切换、标题/通知/唤醒锁生命周期；发送 1004 启停和合成 focus 不能替代此项 |
| WT-08 | 本机真实支持/不支持/无响应路径、resize/modal/背压画面、完整 mascot/欢迎锚点及屏幕阅读器等产品路径 |
| WT-09 | 产品非 TTY/重定向/EOF；真实正常/异常退出前后的 mode/cursor/颜色/paste/focus/title；强杀、窗口关闭、注销/断电/重启及恢复操作 |

本次没有真实模型请求或费用，也没有代理代填用户体验。主代理可按 ADR-0004 统一更新技术票和后续依赖；最终 77/78/85 仍须相应证据与用户实际验收。
