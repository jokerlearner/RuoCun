# 64 图片输入只读独审

审查候选 `fe0a425` 与普通入口 `191eb0a`；按ADR0015只读源码、冻结来源与既有回执，没有读写系统clipboard，没有复跑普通MVP/TTY或构包。

当前已交源码接缝无阻断。复用 `n64/raw/b02-64-final` 的7 passed in 2.94s、4源Ruff/mypy，以及root `b02-root-image-entry` 的原MVP/TTY 2 passed in 29.64s；实际回执exit0/scan false。原生剪贴板busy/延迟渲染与最终用户复制合成图的真实字节链仍待验，不能把合成port当作系统成功。

已核要点：

- 唯一InputBroker保留Content队列；图片只显示占位，Enter才展开成原data URI。runtime按AcceptedInput.original显示用户文字/附件标记，不打印base64，不把Skill投影正文当用户原文。原Skill展开保留非text附件。
- 保存失败将原Content交restore_submission重建图片占位，并保留在编辑草稿与光标。图片读取失败保留原paste文本；不支持视觉沿来源保留文字或显式图片忽略提示。
- `@path`经原classifyPath核工作区/realpath；显式粘贴绝对图片路径按来源允许用户选择的文件。路径不拼shell；data URI由检测后的真实MIME与base64构造。JSON参数不转命令，不因扩展名伪造MIME。
- 原生helper只读PNG/DIBV5/DIB/文件列表，不EmptyClipboard/SetClipboardData、不释放系统handle，Open/Close与GlobalLock/Unlock配对。base解释器直接运行同包stdlib文件、无shell/venv shim，5秒subprocess监督；raw图像不落日志/临时文件。
- 原始/编码输出5MiB、D17的20m像素预算先于DIB像素分配；PNG长度/CRC与header核验、DIB stride/header/mask及RGBA转换清晰。JPEG/GIF/WebP仅头部/大小预算并发送原编码，没有声称完整码流解码验证。该限制与已交证据一致。

Windows真实附图待集中技术窗口，整体77体验不在此代填。16P2另作高风险独审，本记录不解锁其后继。
