# 首版启动

当前固定产物为[批次02 b02-r1](../.scratch/ruocun-next24h/evidence/batch-02/integration/README.md)，源码5be452c。根目录现有`.venv`已安装此包。新增后台等待/事件、显式恢复决定及终端渲染/面板/图片/欢迎图候选；完整真实终端范围仍待验，69首次无账户引导尚未实现。用户要求本次构建后暂停，恢复点见[批次02](../.scratch/ruocun-next24h/batch-02.md)。下文保留历史首版范围及启动器限制，当前能力以[README](../README.md)和`--help`为准。

后续[阶段A](../.scratch/ruocun-advanced-a/implementation.md)自动技术出口已通过，增加静态Skills/原生项目指令与上下文管理；当前包在`dist/advanced-a-r2/`。下文保留首版MVP边界和本机模块入口，新增命令以当前`python -m ruocun --help`为准，人工体验仍pending。

范围：纯Python七工具编码闭环、逐轮文字审批、前台取消、正常会话保存与重开。高级功能仍按ADR-0011后置；真实模型与Windows Terminal人工体验尚待用户验收。

本机已有安装好的开发环境，可在PowerShell中使用模块入口：

```powershell
& 'D:\java supplement\Firstcode\RuoCun\.venv\Scripts\python.exe' -m ruocun --help
& 'D:\java supplement\Firstcode\RuoCun\.venv\Scripts\python.exe' -m ruocun --cwd '你的工作目录'
```

正式包位于`dist/mvp-r2/`，支持Windows x64 / CPython3.11，实测3.11.9。需要独立环境时，在自己的Python3.11环境用`python -m pip install <wheel绝对路径>`安装，再用`python -m ruocun`启动。

本机临时目录的console launcher曾被应用控制策略以WinError4551阻止，进程未启动；同一安装的`python -m ruocun`版本/帮助和独立纯产品环境的普通Agent已验证。未修改主机安全策略，也不将受阻的`ruocun.exe`记为通过。

启动前在`%USERPROFILE%\.ruocun\config.json`填写自己的账户，或用`--config`指定文件。格式和支持边界见[README](../README.md#用法)，注意包含`"version": 2`。首版读内联key，不接系统钥匙串；本次开发没有调用真实或付费模型。

写入/编辑/Shell前输入`y`批准，其它输入拒绝。`/exit`退出，`/usage`查看用量；运行时Ctrl+C请求取消。Windows的Bash工具使用PowerShell5.1语法。

```powershell
& 'D:\java supplement\Firstcode\RuoCun\.venv\Scripts\python.exe' -m ruocun --cwd '你的工作目录' --continue
```

`--continue`不带ID选择该工作目录最近会话。历史token可恢复，费用只统计本次进程；修改旧文件仍须重新Read。遇到未知副作用会停止并保留记录，不自动重放；先核实实际工作目录。上下文超限后，不带`--continue`启动新会话，首版不自动摘要或压缩。

手工更新前先`/exit`停用会话，备份`~/.ruocun/sessions`，再安装需要的标准包并重新启动。当前更新与恢复流程见[安装指南](install-and-recovery.md)。
