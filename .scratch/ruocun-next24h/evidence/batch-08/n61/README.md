# 61 Bash 沙箱的网络开关

第60票独审集成 `2ddf43ef`，第61票领取记录 `3ba1d359`。依据冻结 DAO `src/tools/sandbox.ts:6–12,32–34,41–65` 和 `src/tools/sandbox.test.ts:27–49`。文件沙箱默认保留网络，`RUOCUN_SANDBOX_NO_NET=1` 启用禁网，原生变量优先 DAO 兼容变量。该值从已批准的执行环境读取。Linux 在原文件沙箱参数后、`/bin/sh -c` 前追加 `--unshare-net`。macOS 在原 Seatbelt 配置末尾追加 `(deny network*)`。单独指定 no-net、沙箱关闭或已授权前台绕过时仍走普通 Shell。

源码定向测试在实现前两项失败，实现后连同60的相关验证共五项通过。测试覆盖默认网络、两个平台的禁网配置、别名及严格值、无文件沙箱时 no-net 无效、缺工具以及 Windows 明确拒绝。Ruff 和 Mypy 通过。[来源红](raw/b08-sandbox-network-red/stdout.bin) · [来源绿](raw/b08-sandbox-network-green/stdout.bin)

Ubuntu 24.04 WSL 实测复用了60私有解包的官方 bubblewrap 0.9.0，仅对同一 `127.0.0.1` 合成 HTTP 服务请求。沙箱默认网络可用，显式禁网使连接返回 `ECONNREFUSED`。单独设 no-net 且沙箱关闭时，仍可请求同一个服务。服务器只收到 `/default` 和 `/unsandboxed` 两个请求，三次调用各自成功写入工作区标记。实现前同一探针在显式禁网模式仍收到 HTTP 响应，实际失败。合成监听器、线程、进程和临时目录都已收尾。[实测红](raw/b08-wsl-network-red/stderr.bin) · [实测绿](raw/b08-wsl-network-green/stdout.bin) · [探针](wsl_network_probe.py)

实际网络结果来自 WSL 的 Linux bwrap。macOS 验证到 Seatbelt 配置，等待实机验证。Windows 启用沙箱仍在启动前拒绝，POSIX 可恢复后台 Shell 边界沿60。回环测试的环境与输入均为合成值，所有回执由白名单 `tools/run.py` 生成，`sensitive_match=false`。未安装系统组件或调用付费模型。[60 文件隔离](../n60/README.md)
