# 60 Bash 文件沙箱

实现基线 `d7727605`。冻结 DAO `src/tools/sandbox.ts` SHA-256 `2f5dbb56b15529eeaafe6fa8bd528c2e32b1e0d739412c913a78b2ebfa6ebb4f`。本切片对照该文件6–30、37–65行和 `sandbox.test.ts:7–25`，以及 `exec_shell.ts:340–350,372–378,397` 和 `managed_shell.ts:176–181`。按 ADR-0008 保留默认关闭、显式启用失败即停止、macOS Seatbelt/Linux bwrap 文件路由和前台单次绕过。平台实际执行使用审批完成时的不可变命令、工作目录及环境。查找后端按冻结顺序使用四个固定目录，忽略 PATH。Seatbelt 引号与反斜杠转义确保工作目录按字面进入配置。

Windows 在前台和后台均拒绝显式启用请求，拒绝先于备份、runner 创建及业务进程启动。原生 RUOCUN 环境变量优先 DAO 兼容变量，严格等于 `1` 才启用。`dangerouslyDisableSandbox=true` 的工具 schema 和自检已经接入。实际强制一次人审由独立共享候选 `45db2f6c` 提供。冻结后台分支不传入该参数，所以本票的后台请求始终按全局开关。普通 Windows 前台及受管后台沿用既有 Job 进程管理。

Linux/macOS 平台有前台沙箱命令路由。Python 的可恢复后台 Shell 依赖 Windows 的受管 runner 和具名管道，本批未提供对应 POSIX 持久后台后端。实际在 POSIX 请求后台时先做沙箱可用性判定，然后在创建备份或进程前拒绝未支持的后台模式。macOS 目前验证至合成 Seatbelt 参数。Linux 实测范围为现有 Ubuntu 24.04 WSL 环境的真实 bwrap 文件隔离，Windows 原生能力由其独立回执证明。

| 回执 | 结果 |
|---|---|
| `b08-sandbox-file-red` | 3项如期失败，平台模块缺失，Windows 启用请求未拒绝。所有输入为一次性合成文件 |
| `b08-sandbox-file-source-final` | 来源和真实 Windows 路径、原 Bash 断言、N14 输出和 N15 同运行恢复定向共33项通过 |
| `b08-sandbox-file-scope` | 收紧应用层备份与输出落盘范围后，受影响来源和 Bash 用例28项通过 |
| `b08-sandbox-file-scope-static`、`b08-sandbox-file-scope-types` | Ruff 和 Mypy 通过 |
| `b08-wsl-inventory`、`b08-wsl-namespace`、`b08-wsl-bwrap-artifact` | 已有 Ubuntu 24.04 WSL，非 root 用户可用。系统未装 bwrap，私有下载并解包发行版 `bubblewrap_0.9.0-1ubuntu0.3_amd64.deb`，SHA-256 `2461f1beee9cb04c8942739fe1a2b37e7b7c2a3d518f0779dc75f9245baa3094` |
| `b08-wsl-file-route` | 先用标准查找路径验证真实缺工具明确拒绝，然后仅在探针进程指定私有 bwrap 目录。真实 Bash 允许写工作区和读取区外，拒绝区外写入，区外原字节不变。区内备份成功，区外备份和符号链接指向区外的输出落盘均未发生 |

文件备份和输出落盘由应用在沙箱之外处理。启用沙箱时，这两处复用工作区路径判定限制已审批 cwd 范围，普通执行保留已有行为。所有回执使用 `tools/run.py` 白名单及合成工作目录，回执 `sensitive_match=false`。WSL 临时项目由探针退出时清理，bubblewrap 解包留在忽略的私有缓存供 61 复用。网络开关与隔离证据归 61。
