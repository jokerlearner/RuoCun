# 61 网络沙箱独立复核

固定集成候选 `f15d6a4f`，实现来源 `efa772c6`。第 61 票通过独立复核。

`raw/b08-review-sandbox-network-windows/` 实际 3 passed in 0.23s。两条来源对照覆盖默认网络、Linux `--unshare-net`、macOS Seatbelt `(deny network*)`、严格等于 1 的兼容变量、缺工具、前台绕过和单独 no-net。第三条实际 Windows Bash 验证普通执行可用，明确启用沙箱时在备份和启动前拒绝。

`raw/b08-review-sandbox-network-wsl/` 在已有 Ubuntu 24.04 WSL 和私有解包的官方 bwrap 上独立运行，退出 0。文件沙箱默认可以访问合成 127.0.0.1 HTTP 服务。显式禁网使连接被拒绝。只设 no-net 而未启用文件沙箱时仍可访问。服务器实际只收到 `/default` 和 `/unsandboxed`，三个模式各自成功写入工作区标记。探针清理合成工作区、监听器与线程。

源 `sandbox.ts:6–12,32–34,41–65` 与候选接线一致，网络标志使用批准计划的固定环境。当前证据覆盖 WSL 的 Linux 实际网络隔离、macOS 配置分支和 Windows 不支持边界。macOS 实际隔离仍待实机。两份回执为白名单合成环境，秘密扫描未命中。
