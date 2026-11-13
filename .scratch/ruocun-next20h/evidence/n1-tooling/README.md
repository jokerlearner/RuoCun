# N1文字输入依赖

已批准D06/D10的prompt_toolkit3.0.52与wcwidth0.9.4供最小单owner TTY输入使用；不增加Rich、面板或完整TUI，不改PowerShell5.1。两个官方py3-none-any wheel的版本、URL、SHA256及依赖闭包见[input-wheels.json](input-wheels.json)。没有系统安装或策略修改，也不调用模型API。

新运行锁固定这两个纯Pythonwheel；开发锁以-r包含它，原18个开发包版本及mypy两种已验flavor hash保持，总闭包20包。原03及N0的18包/无产品依赖记录保留为历史。仅这两个已验包增补到各自私有现有venv，pip check与实际消费回执单列；不重复重建已验证的18包环境。后续完整重解析使用tools/lock.py的显式输出参数，避免覆盖03原始来源记录。

真实TTY broker使用已选输入链，保留聊天草稿并独占审批；非TTY继续现有顺序文字模式，不声称pipe忙时队列已通过。自动Input端口确认不替代真实WindowsTerminal/缩放/IME人工体验。依赖就绪不等于broker或11完成。

root实际回执：n1-input-wheels官方纯Pythonwheel下载/摘要、n1-input-lock-verify通过既有锁工具显式输出再次核验二包、n1-install-input-deps按hash/no-index装入既有私有venv、n1-input-pipcheck与n1-input-import均退出0。实际导入版本3.0.52/0.9.4。两包可写安装环境独占，其他角色只读复用wheel、分别安装。
