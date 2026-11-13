# 79 仓外标准包恢复和资源验证

新候选产品 `0252fe7f` 的 `b09-r1` wheel 已按固定哈希复制到仓外目录，并在同一仓外新 venv 离线安装。实际 wheel SHA-256 为 `142afa7757e6d29ae9b9ed908e4521a5ca6e9f483729b4c915fb4d8142c61cb9`。沿用批次08的 sdist 重建、直接构建及包成员比对流程，项目本轮的产物字节绑定由主协调另行收录。仓外环境按已有 Windows CPython 3.11 哈希锁装运行依赖，`pip check` 通过。探针自身也复制到仓外，使用 `python -I -B -X utf8` 启动，检查当前目录与安装环境均不在 Git 树中。真实导入来自该环境 `Lib/site-packages`，没有 `PYTHONPATH` 或 pytest。仓库源码不参与启动、模型回合或恢复。[旧包绑定](../../batch-08/integration/artifacts.json) · [最终探针回执](raw/b09-new-wheel-probe-final/stdout.bin)

安装的 `ruocun.exe` 用合成模型创建原会话，真实启动受管后台 Shell，随后执行 `/quit --keep-background`。控制进程已退出时，签名状态显示 runner 与 IPC helper 仍活着，且 `start.claim` 已写入。Windows CIM 按带启动身份的两个 PID 读取实际命令行，确认两个已安装的 `python -I -X utf8 -m ruocun` 内部角色。Windows venv launcher 的底层进程映像和 CIM 命令行使用基础 Python，默认角色由已验证的安装包 `sys.executable` 发起。签名 manifest 记录的 runner 版本和代码指纹与已安装包一致，未配置替代 helper，真实 IPC 与恢复动作成功。

第二个安装进程用 `python -m ruocun --continue <原会话ID>` 接管同一个 run。实际 BashOutput 返回原进程 Unicode 日志，KillShell 发出终止请求，真实签名终态为 `canceled`。runner 身份不变，控制 epoch 增加，业务启动标记仅一次。只读 SQLite 检查证实 Bash、BashOutput、KillShell 三条结果均已提交，内置 SQLite DLL 也已实际解包并通过普通运行门禁。五次模型请求全部发往合成回环端点。runner、helper、业务进程和回环线程均已收尾，临时项目已清理。

安装元数据的版本、console entrypoint、MIT 声明和许可文件均可读取。代表帮助、SQLite 归档和来源说明、双语提示和语言模块、内置代理和 Skill、Bash parser、工具 schema、嵌入帧及许可的17个安装成员逐字节匹配 wheel。嵌入帧数据仍带冻结源文件、SHA 与源头说明。原始外部 PNG 与 manifest 不在冻结快照，其可再生成性和独立授权仍按 E-02 保持未核实。[矩阵 E-02](../../../../ruocun/acceptance-matrix.md) · [帧数据](../../../../../src/ruocun/tui/resources/mascot-frames.json)

`raw` 保留三次探针调试失败和最终结果。初次错写语言文件位置，第二次漏设已安装 console script 的合成 UTF-8 输出环境，第三次只读 SQLite 连接未显式关闭导致 Windows 临时清理失败。三项均修在探针，最终产品与安装包字节保持一致。Ruff 及 `git diff --check` 通过，所有白名单回执 `sensitive_match=false`。

复跑时，将 `installed_recovery.py` 与固定 wheel 复制到仓外，用新仓外 venv 的 Python 通过 `tools/run.py --cwd <仓外目录>` 启动，传入 `-I -B -X utf8 <探针> --wheel <仓外wheel> --sha256 <固定摘要>`。环境保持纯运行依赖，真实会话使用探针自己的合成 HOME 和回环服务。旧 `b08-r1` 另在仓外完成锁定安装，保留作第81票的旧环境基线。

## 最终候选复验

产品 `8e7760ce` 的 `b09-r3` wheel SHA-256 为 `764d9f908c583de07f32f48f0618b74c0c82f273ec02ae672496efb00aedb81d`。用第82票 `--stage package` 新建仓外纯环境、按运行哈希锁安装 R3，仓外模块入口 `python -m ruocun` 重新创建、分离并恢复同一真实 Shell run。五次回环模型请求、一次业务启动、三条已保存工具结果、签名取消终态以及 runner、IPC helper 和业务进程关闭全部确认。新环境仅装运行依赖与 wheel，随包 SQLite 归档走真实门禁，未手工复制 DLL。实际安装成员重新按 R3 wheel 比对。复跑在上面的参数后追加 `--module-entry`。[R3 原始回执](raw/b09-r3-installed-recovery/command.json) · [结果](raw/b09-r3-installed-recovery/stdout.bin)

R1 初次控制入口仍保留 `ruocun.exe` 真实成功证据。R2 重装后的 launcher 遭本机 Windows 应用控制拒绝（WinError 4551），R3 使用同版本包的模块入口，且仍检查安装元数据的 console entrypoint。本机策略保持原样。[R2 原始回执](raw/b09-r2-installed-recovery/stderr.bin)
