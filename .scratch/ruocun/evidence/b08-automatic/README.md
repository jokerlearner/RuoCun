# 批次08的自动技术证据

固定候选 `8ee4a9b992ee7a77759b3295708dda32bebbe68f`，安装 wheel SHA-256 `01330dead041e70177f609e338b433619b630919be055e8a47c5d52a5fdd8298`。权威矩阵收录 WT-01 至 WT-09、WIN-01 至 WIN-10 的自动子案例。[安装和全量](../../../ruocun-next24h/evidence/batch-08/integration/README.md) · [验收矩阵](../../acceptance-matrix.md#批次08自动技术出口)

每个子案例的 JSON 指向同候选 pytest 命令、JUnit 原始回执、具体断言及已知验证边界。WIN-01 另含本机 PowerShell 7 实际审批、Unicode argv 和退出码回执。WIN-05 另含本机 Credential Manager 的实际读写删除证据，两个仅本轮生成的合成键均核对为已删除。矩阵行引用对应复核文件。

WT 自动运行覆盖 Unicode 编辑、队列、粘贴和模态、重绘、终端控制、交接、Sixel 路由及回退。WT-09 另在私有隐藏 Win32 控制台实际运行安装包，输入模式由 503 变为 1008，正常退出后恢复至 503，无补救操作。[控制台原生回执](console-output.json)

WIN-08 在新建隔离窗口站用安装包的生产辅助进程读取真实 Win32 合成剪贴板。先核对主线程与异步工作线程启动的辅助进程都进入该站，再验证空、PNG、DIB、超限和纯文字边界。释放私有剪贴板、桌面和窗口站。此前的真实 Windows Terminal 交互按原包保存。当前候选的终端视觉、IME、连续操作与系统条件留给人工验收。[原生剪贴板回执](clipboard-output.json) · [历史 PNG 与终端操作](../../../ruocun-next24h/evidence/n18/wt/runs/20261111T075358Z-ea4e4c/README.md) · [历史交接与 Unicode 剪贴板](../../../ruocun-next24h/evidence/n18/wt/runs/20261111T101837Z-52f7cc/README.md)
