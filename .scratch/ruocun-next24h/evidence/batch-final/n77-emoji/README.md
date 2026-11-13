# 77 Windows 终端 emoji 显示回修

真实 Windows Terminal 验收报告提交原文为「验收🙂」，回环请求摘要一致，但灰底转录和放大后历史显示「验收??」。使用同一个独立 ConPTY 探针对照实际 R3 安装包与候选源。探针只操作自己创建的伪控制台、临时目录和合成回环服务，通过 Windows Terminal Win32 输入模式发送 UTF-16 单位，将 emoji 的两个代理单位分两次发送。普通 CLI 收到 Enter 后发起模型请求，57 列放大到 127 列触发历史重画，随后正常退出。[ConPTY API](https://learn.microsoft.com/en-us/windows/console/creating-a-pseudoconsole-session)

R3 下草稿、灰底提交和放大后转录都可在真实 ConPTY 的 UTF-8 输出中捕获「验收??」，产品退出 0，模型原文仍为「验收🙂」。Python 直接把正常 Unicode 字符交给同一个输出后端时 emoji 可以显示。实际缺陷在输入侧的既有 VT parser：Windows 原生输入从 prompt_toolkit 按 UTF-16 单位转入 parser，两个独立代理单位直接进入编辑和显示。prompt_toolkit 的 UTF-8 输出用 replace 写成两个问号，模型请求 JSON 则转义代理并由回环解码成正确字符。[R3 原始失败](raw/b09-emoji-conpty-r3-red/stdout.bin) · [最小输入回归失败](raw/b09-emoji-parser-red/stdout.bin)

既有 ParserGate 在进入编辑、粘贴和协议解析前合并代理对，跨输入批次最多保留一个高代理。App 文本清理也处理历史内已有的代理对，原始持久消息仍可读取且没有重写。补丁后同一 ConPTY 输入使草稿、提交、放大回放都保留 emoji，模型原文一致，产品和探针都退出 0。源定向 20 项、Ruff 和三个模块的 mypy 通过。[候选通过](raw/b09-emoji-conpty-fixed-green/stdout.bin) · [旧历史失败](raw/b09-emoji-legacy-red/stdout.bin) · [定向回归](raw/b09-emoji-targeted/stdout.bin)

复跑将 `emoji_conpty.py` 复制到仓外，用 `tools/run.py --cwd <仓外目录>` 启动已安装解释器，传入 `-I -B -X utf8 <探针> cli`。追加候选 `src` 绝对路径可使用已安装依赖执行候选源。所有回执秘密扫描无命中。此次结果为独立 ConPTY 自动复验，真实 Windows Terminal 复验仍由最终批次完成。
