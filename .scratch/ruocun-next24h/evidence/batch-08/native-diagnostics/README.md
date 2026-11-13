# Windows 原生补证

固定包 `8ee4a9b9` 的 [WT-09 与 WIN-08 回执](../../../../ruocun/evidence/b08-automatic/README.md)由 [控制台探针](../console_probe.py)和[剪贴板探针](../clipboard_probe.py)产生。控制台使用单独隐藏的 Windows 进程和实际输入缓冲，按合成 `/exit` 前后直接调用 GetConsoleMode。[Windows 控制台输入文档](https://learn.microsoft.com/en-us/windows/console/writeconsoleinput)

现有登录会话创建匿名窗口站返回 183。改用合成参数创建独立的网络凭据会话，随后成功新建匿名窗口站，无网络访问。首次直接切换进程窗口站时，生产启动方式的子进程继承检查失败，探针在读取剪贴板前停止。最终启动工作进程时明确绑定新窗口站及其私有桌面，确认后才用生产辅助进程读取合成输入。[窗口站连接规则](https://learn.microsoft.com/en-us/windows/win32/winstation/process-connection-to-a-window-station) · [创建窗口站](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowstationw) · [临时进程登录选项](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createprocesswithlogonw)

诊断退出与成功补证分别保留。现有交互窗口站的剪贴板内容未被读取或改写。
