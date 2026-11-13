# WIN-01 本机 PowerShell 7 批准与执行

源码验证固定在 `065366b8` 的产品内容。用 PowerShell `Resolve-Path -LiteralPath` 解析本机 Codex WindowsApps 目录中的 `pwsh.exe`，通过 `tools/run.py` 的环境白名单启动探针。实际启动版本为 `7.6.9`，该可执行文件 SHA-256 为 `2a6769a3330dc1084d0154bfde7d164ab750ca7f700f313f9d417c1be78b2233`。探针使用合成配置、环境和工作目录，通过真实权限入口注入两次合成回答。首次拒绝后无法取到获准计划，命令标记文件也未创建。第二次批准后，同一个计划的外层 `cmd.exe` 和完整解码的 PowerShell 脚本与审核内容一致，明确保留非标准安装路径的一次人工审批。

真实进程把中文、空格、emoji、单双引号、换行和 `% ! ^ $` 原样交给 PowerShell 启动的 Python 子进程。合成环境原样继承，合成密钥按执行环境规则过滤。Bash 返回 Unicode stderr 与退出码23。工作目录清理确认成功。源代码实际导入路径和具体输入输出见回执。Ruff 通过，两条白名单运行 `sensitive_match=false`。[源码回执](raw/b08-pwsh-candidate/stdout.bin) · [启动参数](raw/b08-pwsh-candidate/command.json)

最终 wheel 验证沿用 [pwsh_probe.py](pwsh_probe.py)，使用固定安装目录中的 Python，省略 `--source`。探针会校验 `ruocun` 从该解释器所在环境的 `Lib/site-packages` 导入。复用 `tools/run.py`，传入 `-I -B -X utf8`、探针绝对路径及 `--pwsh` 的已解析绝对路径。最终产品提交和 wheel 的字节绑定由批末集成记录提供。本记录仅覆盖 WIN-01 的显式 PowerShell 7 子案例，真实 Windows Terminal 和人工出口仍分别验收。
