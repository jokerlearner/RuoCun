# Windows 可选 MXC 沙箱

默认关闭，沿用 `RUOCUN_SANDBOX=1`。启用后若依赖缺失、摘要不匹配、MXC 不可用或原生命令行不能保真执行，该次命令明确失败，不自动切换 legacy 或无限制 Shell。Windows 模式不接受 `dangerouslyDisableSandbox` 整次绕过。

## 独立固定依赖

准备[官方 Codex CLI 0.169.0 Windows x64 独立包](https://github.com/openai/codex/releases/tag/rust-v0.169.0)，保留完整目录结构与配套文件。若存不会自动下载、升级或调用桌面应用的私有二进制；wheel 不捆绑它。官方程序自己的许可证随其独立发行包保留。

`codex.exe` 必须匹配 SHA256：

`ce1945eb440b5481ed1233ebaf32b7056ee7e4e452fa62ffe1cbfb26103cdee0`

在本次启动的 PowerShell 中设置：

```powershell
$env:RUOCUN_SANDBOX = '1'
$env:RUOCUN_SANDBOX_CLI = 'D:\tools\codex-0.169.0\bin\codex.exe'
python -m ruocun
```

路径替换为你实际解包的位置；不用修改用户 Codex 配置。未设置 CLI 路径时，查找固定位置 `~/.ruocun/dependencies/codex/0.169.0/bin/codex.exe`，不搜索 PATH。

该程序只承担本地 sandbox 子命令。若存保持原模型、账户和会话流程，无需把任务交给 Codex 模型。宿主必须实际支持 MXC，系统版本够新不能代替运行验证。

## 写范围与批准

内置 Bash 前后台、Monitor、子代理同类命令和 Write/Edit 遵守启动项目写范围；普通 `cd` 不扩大范围。独立控制 profile、CLI、Python 运行时及会话/恢复控制材料受只读保护。

支持命令请求 `additionalWriteDirectories: ["D:\\another-project\\output"]`。这只是请求：若存通过真实审批端显示本次命令和具体目录，只有一次性明确批准才绑定到该执行计划；不继承 yolo、旧 always 或全外部写权限。后台恢复沿原签名计划接回，不按新配置扩权，也不自动重放结果不明的命令。文件工具区外写同样逐次审批。

Windows 保留原 HOME/USERPROFILE、PATH 和普通环境继承/敏感名称过滤；TEMP/TMP/TMPDIR 及 pip/npm/Maven/Gradle 缓存指向 `~/.ruocun/sandbox/work/<项目身份>/` 内的专用目录，控制 profile 位于其兄弟 `control/`。缓存冷启动可能重新下载依赖。其它工具的用户目录写操作可能需要明确目录授权，未承诺所有工具链兼容。

网络默认保留；现有 `RUOCUN_SANDBOX_NO_NET=1` 要求限制该命令网络。它不控制若存自身的模型请求或可信扩展。

## 能力边界

Hook/MCP/LSP 是已配置的可信扩展，排除在首版保证之外；框架自身配置、记忆、会话及管理操作继续使用各自的受控端口。这是内置文件/命令入口的限制，不是整个若存进程或所有管理功能的系统隔离。

当前验证聚焦 Windows x64 默认 cmd 协议，额外 Python 启动桥保留原 `/d /s /c`、引号、标准句柄和退出码。MXC 内 PowerShell 的语言限制可能影响 .NET 操作。后台接回指宿主未重启且原 runner 仍存活时，不保证跨 Windows 重启继续运行。真实终端视觉与缩放体验单列验收。

MXC 的上游[已知限制](https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/mxc-sandbox/README.md)包括硬链接按不同路径分别授权：可写路径与区外路径若指向同一底层文件，写入仍会影响该文件。本方案以普通越界修改防护为目标，不宣称能安全执行任意恶意代码。
