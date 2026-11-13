# 64 图片附图候选

64保持claimed，普通runtime接线与最终用户剪贴板操作由主协调收口。本候选只用冻结来源及D10/D17已定设计，无真实模型、无系统clipboard读取/写入、无产品build/full。

## 来源与入口

source.json绑定imagePaste.ts、App.tsx/测试、Read与paths的冻结SHA，以及D10§6.3和D17 clip.py。原App的@图片路径明确classifyPath后拒绝工作区外；绝对图片路径paste则直接读用户粘贴的文件，两条不同路径保持。不存在/非图片/读取失败的paste原文留在草稿，不当作命令。@路径失败保留原文字部分，模型不支持视觉时沿源提示并发送文字或“[图片已忽略]”。

PasteStore同时支持文本与图片占位，Enter才展开为原ContentPart[]，图片data URL不显示在转录。InputBroker仍唯一读者；configure_images可注入合成只读port，正式Windows默认Alt+V显式附图，只插占位不提交，不依赖WT是否发送空Ctrl+V paste事件。问题/审批框普通文本paste仍为文本；不向已有问题框偷塞异步图片。保存失败restore_submission接受同一Content并重建图占位，同时保留正在编辑的草稿。

## Windows窄端口及边界

platform/windows/clipboard.py读取优先注册PNG→DIBV5→DIB→CF_HDROP。系统handle只GlobalLock/Unlock和及时复制，不GlobalFree、不EmptyClipboard、不SetClipboardData，Open/Close配对。原生读取由base Python直接运行同包自包含stdlib文件，固定系统环境白名单，5秒subprocess监督；超时精确终止并等待该直接子进程，无shell或venv转发shim，不写clipboard图像日志/临时文件。文件列表最多64项的资源边界明确拒收超量，不改剪贴板。

来源5MiB原始字节和编码PNG上限保留，D17已有20,000,000像素预算先于DIB像素分配。DIB24/32及BI_RGB/32位BI_BITFIELDS核header、尺寸、stride、长度和channel masks，bottom-up/top-down及V5 alpha转换为PNG；非法/超限返回无图、保留草稿。图片文件保留原编码，经magic与尺寸头部校验，PNG另核chunk长度/CRC/IEND；不因为PNG压缩体小忽略解码尺寸。原Read工具不修改，路径发送实际MIME而非扩展名猜测。

明确边界：没有引入完整JPEG/GIF/WebP像素解码库，文件发送原始编码；其头部/MIME/尺寸预算检查不是完整压缩码流验证。DIB原生转换已覆盖上述24/32位子集，其它压缩/位深明确无图返回。macOS保留有限osascript PNG来源流程，Linux暂无剪贴板后端；非Windows实机未验。本模块不包含未来/copy的CF_UNICODETEXT全局写入能力。

## 实际回执

image-red、owner-red分别是缺图片模块和缺owner明确动作的真实红。final为7项通过：4个来源/D10必要合成用例（真实临时图片路径、占位/不支持模型、D17 RGBA与DIB24/畸形资源边界、真实ptk Alt+V/拖路径失败及不自动提交）和3个既有输入owner回归；4源Ruff/mypy通过。冻结App附图测试使用12byte假PNG仅测magic，本迁移按D10畸形护栏改为有效1px合成PNG，附图语义断言不减。

系统Clipboard API路径和用户实际Alt+V/模型请求字节链等待集中技术窗口；本轮没有读、输出、保存或改写用户当前剪贴板，也没有把合成port当作真实系统成功。native busy/迟延渲染/跨进程占用等操作系统实证不由这些合成用例补填。所有raw经tools/run白名单、合成HOME/config/temp，敏感扫描false。
