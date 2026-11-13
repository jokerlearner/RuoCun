# 18 终端编辑产品候选

起点为 `1271687`，分支 `codex/n24-terminal`。此记录覆盖文本输入、模态优先、粘贴和取消键的产品子路径。共享 runtime 调度接线由主协调集成后另验，真实 Windows Terminal 与用户体验保持待验。

来源为唯一冻结快照 `f17e189 / 7ac654a0dc06` 的 `src/tui/app/App.tsx` 483–491、1102–1125、1295–1357，以及 `App.test.tsx` 的双Ctrl+C、ESC队列/回填/Down清空和裸CR粘贴断言。D06 `test_terminal.py` 的280/281 UTF16与同一输入链断言复用为产品测试。组合字、旗帜及ZWJ移动删除是D10所需的最小Unicode平台确认，使用已有 `wcwidth==0.9.4` 的grapheme API。

实现沿用 `agent/input_broker.py` 的唯一输入owner和输出锁。新增 `tui/input_text.py` 负责来源文本粘贴折叠及单次展开。超过280 UTF16单位或去尾换行后超过6行时折叠，显式Enter才提交。普通草稿、审批草稿分别保留。Esc交调度回调处理，只有真正暂停且草稿为空才回填最后提交。Ctrl+C在2秒内再按才退出。公共接口新增 `on_escape: async () -> bool` 与 `set_status(state, queued)`，旧构造与调用保持兼容。

## 验证

所有命令由现有 `tools/run.py` 的显式环境白名单启动，HOME/配置/会话/TEMP在 `.cache/n18` 合成目录。使用根venv依赖，`-I -c` 显式把当前worktree的 `src` 放在导入路径首位。pytest也从当前worktree的测试文件启动。命令全文及原始stdout/stderr在 `raw/*/command.json` 和对应文件，均经调用器环境敏感值扫描，无命中。

- `n18-red` 新增三项来源/平台断言在旧产品失败，实际3 failed。
- `n18-final-tests` 当前4项输入验证、既有3项broker和1项普通runtime受控TTY，共8 passed。
- `n18-final-ruff` 修改产品和测试静态检查通过。
- `n18-final-mypy` 修改产品3文件严格类型检查通过。

## 仍需接续

真实Windows Terminal正常入口、IME候选确认、连续缩放、可见滚动历史和mode/cursor恢复仍待技术取证。当前受控TTY/DummyOutput结果不替代这些结果。图片粘贴和拖图读取继续按64/相关多模态入口收口。未闭bracketed paste的大输入资源边界沿D10保留待验，当前不宣称无限输入安全。65的转录与完整渲染区仍为后继。18保留claimed，最终用户体验归77。

## 同一reader协议补齐

D10 3.2的协议隔离现沿D06 `protocol.py` 与 `terminal_app.py:446–448` 迁入 `tui/terminal_reports.py`。只包装实际ptk VT parser，DA/cell/focus回包在按键解析前处理，paste内部相似序列保留原文。CPR在ptk renderer等待定位时交还原parser，以保留产品自身定位。独立tick只处理同reader已积累的数据，不创建额外stdin reader。正常退出恢复原parser slot，后端缺少锁版本slot时启动明确拒绝。

初次产品接入的 `n18-gate-tests` 实际9通过/2失败，原因是定时到达的Esc已经进入原parser缓冲但未触发app key processor。按D06已验证的tick→flush_keys→process_keys接线修复。`n18-gate-green` 对来源协议3项、编辑4项、既有broker3项和普通runtime1项，共11通过。`n18-gate-mypy` 产品4文件通过。`n18-gate-ruff` 首次仅import顺序失败，修后 `n18-gate-final-ruff` 通过。失败原始回执保留，均使用相同隔离入口且无敏感值命中。主协调的真实Windows Terminal取证及独审继续，18保持claimed。

## 单次文本paste的资源边界

按D10 3.3登记本轮实现值，单次paste正文上限为 **8 MiB UTF-8字节**，包含中文和emoji的实际编码字节。由同一Reports在parser之前暂存，完整END到达后一次交给ptk。编码计数按最多4096码点小片段进行，跨限输入不先编码或缓存整段无限载荷。超限清空本次暂存，界面显示“此次粘贴超过 8 MiB，已整段拒收，原草稿保留。”，随后一直吞到本次END，防止其换行/Esc/命令文字变成独立按键或提交。正常结束后继续接纳新输入。未闭paste只保留有限正文及至多结束标记长度的尾片段，退出清理其暂存。

这是本轮具体Python/终端适配值，超过8MiB的单次粘贴需要用户缩小内容或引用文件。普通键入、已确认输入及既有草稿不因拒收该次paste被改写。仍不把此受控证据当作真实Terminal或IME体验。

`n18-paste-cap-red` 实际2失败/2通过，捕获旧行为在paste未闭时先透传正文。`n18-paste-cap-green` 最终共13通过，新增必要平台确认包括原1MiB样本接纳、实际8MiB多字节边界、同一次feed跨限的整次拒收、分片END恢复，以及产品输入owner可见拒收原因、原草稿保留和paste内部控制键不执行。最后一个产品路径使用缩小后的相同公开上限以缩短定向运行。`n18-paste-cap-ruff` 和 `n18-paste-cap-mypy` 通过。全部沿白名单合成环境，敏感值扫描无命中。
