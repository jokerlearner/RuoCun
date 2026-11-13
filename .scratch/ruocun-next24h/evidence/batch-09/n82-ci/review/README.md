# 82 平台持续集成独立复核

复核候选 `c9e760f424b372df30e1f2657b21d3f1edaada8e`。Windows 标准包、静态检查、纯安装和 QA 使用固定解释器及锁。独立读取 R1 首轮和回修 JUnit，首轮 1699 个实际节点中正好 20 个失败，修正后的 20 个通过节点与原失败集合完全一致。后续仓外 QA 实际以非 editable 方式安装开发支持 wheel，独立 `python -I` 子进程从相同 QA 的 site-packages 导入产品和测试支持。 [全量及环境修正回执](../README.md)

另开独立合成状态复跑最终本机入口。同版本 R1 预装环境搭配 R3 wheel，在 `ruocun/agent/runtime.py` 字节失配处拒绝，退出 1。R3 纯安装与 R3 wheel 的 309 个产品成员及两份元数据匹配，随后版本和帮助检查成功，退出 0。两条命令秘密扫描均无命中。两个工作流中的回执上传均以 `success()` 为条件。 [错包拒绝](b09-review-n82-mismatch/installed-origin/stderr.bin) · [同包校验](b09-review-n82-match/installed-origin/stdout.bin) · [工作流检查](../raw/b09-ci-artifact-guard/stdout.bin)

Ubuntu 24.04 WSL 实际核对 278 个产品文件的 Python 3.11 语法和编译、来源 CLI 与原生 Shell。macOS 及托管 CI 尚未运行，POSIX 完整安装和运行按支持矩阵单列。第 82 票的本地技术路径和工作流配置独立复核通过。 [Linux 回执](../raw/b09-ci-wsl-posix-design/stdout.bin)
