# 批次08自动出口独立复核

固定产品为 `8ee4a9b992ee7a77759b3295708dda32bebbe68f`，提交审查前的证据及矩阵为 `e0c5602864c41f7f708d6f64cca2308f5486b128`。核对 19 个不同的自动子案例及 180 条 JUnit 引用，所有引用均对应实际通过的唯一节点。JUnit 有 1699 个节点，零失败、错误和跳过。总报告的另外 4 项为去选。 [权威矩阵](../../acceptance-matrix.md#批次08自动技术出口) · [原始 JUnit](full-junit.xml) · [全量命令](full-command.json)

独立比对 Git 归档、sdist、实际 wheel 与安装目录的全部 309 个产品成员。两个构建出的 wheel 整包 SHA-256 相同，三份锁与固定 Git 字节一致。四份原生执行的命令与输出均与受控执行原始回执字节相同，退出码为 0，秘密扫描无命中。 [构建证据](../../../ruocun-next24h/evidence/batch-08/integration/README.md)

- PowerShell 7.6.9 实际执行保留合成中文、引号、换行和 emoji 参数，拒绝不产生写入，批准写入并返回退出码 23。Windows Credential Manager 按大小写区别两个本轮新建合成目标，读回匹配，精确清除后均返回 1168。 [PowerShell](pwsh-output.json) · [系统凭据](cred-output.json)
- 隐藏的独占 Windows 控制台由实际产品切换输入模式 503 → 1008。写入合成 `/exit` 后正常退出，输入恢复为 503，输出模式保持 3，未执行补救，合成工作区与发现记录已清除。 [控制台](console-output.json)
- 生产剪贴板 helper 在新建的非交互窗口站内实际读取空剪贴板、PNG 和 DIB，拒绝超限输入，并将纯文本留给终端。启动普通及工作线程辅助进程前均核实继承同站。私有剪贴板、窗口站和桌面均收尾，用户交互窗口站的剪贴板内容保持原状。 [剪贴板](clipboard-output.json) · [隔离探针与诊断](../../../ruocun-next24h/evidence/batch-08/native-diagnostics/README.md)

两票自动技术出口独立复核通过。真实 Windows Terminal 的视觉、IME、连续操作与强杀重开，以及另一用户、登录、重启等条件仍在各票人工范围内。 [77 复核](77-wtaccept-review.json) · [78 复核](78-wincaps-review.json)
