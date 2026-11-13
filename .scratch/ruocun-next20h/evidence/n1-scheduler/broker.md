# 最小TTY输入 broker 候选

已合 root 审过的依赖/队列 tip `5ba5951d9112b406b028c60d9436175e91144d4b`。只新增 `agent/input_broker.py` 和本票专属3项测试；不改公共入口、权限模块、依赖锁或持久化。普通入口由 root 消费后再验，本候选不结11，不把实际重定向 stdin pipe 或 Windows Terminal/resize 写成通过。

## API与生命周期

`InputBroker(*, on_pause: async()->None, input: Input|None=None, output: Output|None=None)`。root仅在TTY启动；真实重定向输入仍保留原顺序文字模式。

- `await start()` 启动唯一 ptk Application 的输入链，`await next_submission() -> str|None` 交出明确 Enter 提交的文本，输入结束返回 None。提交内容沿 D06 先 strip；BracketedPaste 由 ptk 处理，换行不会自行提交。
- `await ask_approval(prompt:str) -> str` 使用同一 Application 的独立回答 Buffer，原样返回答案，由权限层解释 once/session/always 等选择。Esc/CtrlC/EOF/close返回空串；输入层不做 bool 业务裁决。审批期间不追加用户提交；模态先拒绝，原草稿和光标继续保留。
- `restore_submission(text:str)` 在持久化接纳失败时，把原文本放回草稿；已有编辑内容以换行保留，光标保持其在原草稿中的相对位置。只有 root 收到未确认错误时调用，不把敏感原文写入新的外存储或日志。
- `await write(text,end='\n')` 通过同一 app 上下文的 run_in_terminal 串行输出，不抢另一份 stdin reader，不覆盖草稿。root负责既有脱敏与安全展示。
- 主草稿下 Esc/CtrlC 调用注入的 on_pause，保留草稿；审批下先返回空串。空草稿 CtrlD结束输入。`await close()` 等 Application 完成及暂停回调结束，唤醒输入/审批等待者；默认创建的 Input 由其最终 close，注入 Input 由调用方拥有。不取消任何模型任务，也没有 input线程/新reader。

这是批准的文字输入适配，不复制 D06 全屏、Rich、图形、任务面板、后台、协议探针或双CtrlC退出。动态Skills等专用命令仍由root路由。

## 来源与证据

复用 D06 `experiments/terminal/terminal_app.py` 的唯一 Application、独立模态草稿及 run_in_terminal 输出owner职责，测试沿 `test_actual_prompt_input_chain_paste_is_not_submit_and_stream_keeps_draft` 与 modal-first/Esc保草稿语义；产品依赖固定官方纯Python `prompt_toolkit==3.0.52`、`wcwidth==0.9.4`，锁及官方wheel哈希由root审定。实际导入版本和 pip check 在本私有venv通过，没有重建18包环境或wheel。

3项受控 Input 自动用例 red→green、Ruff两文件通过：

1. 真实 ptk 按键链：粘贴不自动提交，模型文字输出保留正在编辑的草稿与光标。
2. 必要审批接缝：同一输入owner回答不进入用户队列，回答原字符串保真；拒收原文恢复时保留两段；CtrlC优先拒绝审批并恢复草稿。
3. 必要关闭接缝：Esc调用暂停且保草稿；close结束尚待审批/提交，并确认默认创建的受控 Input.closed=True、app.is_running=False，重复关闭可返回。注入Input的用例另确认不会被broker擅自close。

create_pipe_input 是 ptk 的程序化测试 Input，**不是对实际重定向 stdin pipe 忙时输入的支持证明**。默认Win32Input的实际Windows Terminal/raw-mode及resize恢复仍人工pending。mypy未在已知编译扩展ENV失败的私有入口重试，交root/独审既有纯Python工具链核验，不回填通过。最终源码/安装及全量由root统一出口。

原始缺模块/缺方法/未触发暂停失败及green见raw/n1-input-*，pin安装/import/pipcheck亦保留；broker-command-index.json逐项标注exit和敏感扫描，broker-source-members.json绑定产品/测试/D06来源与runtime锁。全部工程命令沿白名单启动器和合成HOME/config/temp，scan=false；真实模型/付费API调用0。

## 34选择器必要端口

root要求选择界面区分 Enter 空回答与 Esc关闭：新增 `await ask_selection(prompt)->str|None`，Enter保留原str（包括空串），Esc/CtrlC/EOF/close为None。仍共用原 Application、Buffer与Future；ask_approval仅包装None→空串，09接口不变。复用原审批/取消fixture添加空Enter与Esc区分，实际缺方法red→green，受影响原用例1 passed、Ruff通过；没有重跑原3项全套或新增排列矩阵。源码指纹更新，旧7f98候选hash保留在该历史提交；两次运行及Ruff原始回执见raw/n1-input-selection-*。
