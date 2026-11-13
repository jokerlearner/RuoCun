# r1 独立审计入口提前退出

本次尚未启动 pytest 或真实 worker；只完成候选文件字节清单。

审计入口初版错误地要求每轮报告的 `head_before_run` 已包含全部被运行源码。第一次读取历史报告 `20261105T070254Z-df27ed` 时，`git show f2c96cbf:.scratch/ruocun-discovery/experiments/terminal/Copy-Case.ps1` 返回 128（该 HEAD 尚无原型），入口以 `subprocess.CalledProcessError` 退出。历史材料和产品均未修改，r1 不计为测试失败或通过。

随后只修正审计入口：如实分列运行时 HEAD 与报告哈希可绑定的后续提交。首轮 12/12 绑定首次实现提交 `7036050`；第二轮运行时 HEAD `acc85b7` 仅匹配 11/12（Open-Hitl 的 NoProfile 改动尚未提交），12/12 绑定 `d295a15`。最新报告 `20261105T070609Z-e9ad63` 的 12/12 同时绑定其声明 HEAD `d295a15` 和本次合入代码。不能将前两轮扩张为提交前源码在运行时 HEAD 已提交。

锁定安装及 pip check 原始材料保留于本目录；新的完整复验使用 r2，不覆盖 r1。
