# 18 真实 WT 技术前置只读独审

本次仅查原始记录与 launcher 控制流，复用此前输入 owner、ParserGate、粘贴资源边界、调度接线的定向独审，不再启动产品或添加测试矩阵。

主协调转达用户在新 Terminal 窗口完成五项操作并回复“全部正常”：流式、编辑排队及 emoji 删除、Esc 清队/暂停、多行折叠与缩放、双 Ctrl+C 退出。这是用户实际操作反馈，并非代理的 UI 目测；逐项原始对话由主协调保存。

只读核验 `n18/wt/runs/20261111T044203Z-514e10`：

- `start.json` 绑定 `ac0fc733688bf699be3e18134342600af99161a6`、干净源码、逐成员摘要与真实 WT_SESSION。其 `src` 与本轮冻结 `5048b4d` 的 Git diff 为空。
- 产品实际 argv 为根 venv `python -I -X utf8 -m ruocun`，`evidence_kind=installed-technical`；合成 HOME/配置/workspace，环境白名单与清空执行点均有记录。回环服务器只监听 127.0.0.1，模型调用为 0。
- `requests.jsonl` 实际四条合成请求，包含“开始流式”“下一条中”与七行完整原文，不把请求日志当成视觉光标或未提交草稿的独立证据；这些视觉项依用户实操反馈。
- `launcher.json` 实际 `exit_code=0`、`forced_stop=false`；`before` 与 `after_child` 均输入 503/输出 7，`mode_equal_before_repair=true`，补救后也相同。已读 `launch.py`：该结果来自持有的产品子进程实际退出和随后 ConsoleMode 采集；补救仅在模式不等时执行，本次没有借补救冒充自动恢复。

结论：此前缺失的早期文本路径真实 WT 技术前置已具备，可由主协调将 18 记 resolved 并解锁 65。此结论覆盖本票现有文本路径，不扩展为图片、后台任务、完整主题或全部 WT 母案例族通过；77 整体用户体验仍 pending。

旧 `20261111T043941Z-3a66d1` 的设置路径弹窗与停止请求按失败/环境中断保留。本独审读取时该目录只有 start.json，没有 launcher 正常退出回执；不将其并入本次通过。
