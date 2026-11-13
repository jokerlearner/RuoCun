# M03 纯Python前台闭环证据

产品候选：`1ad72d6f06f499b50bfaacfd22daf3140f40f44f`。固定起点：`01e4606`；范围按ADR-0011。最终r2自动技术出口通过；人工体验仍pending。旧候选通过与r2最终结果分别列出。

普通`ruocun`入口已接配置→既有Chat/Responses客户端→七工具→参数校验/文字审批→已提交intent→handler→已提交结果/检查点→继续请求。全为Python核心；SQLite是已确认的底层依赖，非TypeScript运行包装。写前读取、基线检查和exec失败屏障保留；未知写结果停止、不自动重放。CLI不再用demo代替真实Agent。

## 来源与差异

冻结快照`dao-f17e189-7ac654a0dc06/source.zip`，SHA256=`1f8308959d8b9ac0783b6ce6ddbffe7a71cc60bc59332f309f0d62083efac078`。实际来源是`agent/loop.ts`、`loop.test.ts`的普通回答/空回答/模型选择/工具配对/坏JSON/上下文错误，`tools/execute.ts`及`execute.test.ts:169–186`的失败屏障和拒绝分支；复用既有client的reasoningContent/responseItems与StoragePort v1，未重造客户端或数据库。

首版有9条循环/执行来源回归，以及1个必要产品接线确认（七工具实际改写/执行、拒绝、第二进程重开）。不将它们算作完整DAO循环/调度/恢复测试通过；后台、自动压缩、动态扩展、完整TUI与完整恢复UI后置。

- 完整assistant字段保留，坏JSON清洗历史；NaN/Infinity与JS JSON.parse一致拒绝，实际参数仍交注册表校验。
- 审批逐项明确；来源复杂权限与Hook后置。已知副作用前拒绝可修正重试，写入已开始后未知异常保留未决。
- 普通StorageWorker确认提交后才显示保存；恢复历史总token，费用仅本次进程。保存父层使用既有私密目录端口创建，既有ACL只核验，07叶子不改。
- 上下文达到供应商上限时停止并提示新会话，不静默删历史；不实现自动压缩。
- exec失败屏障适配来源已登记的S-05格式缺口：真实Bash结果`[exit N,运行…]`和来源测试`[exit N]`都识别；后续write/exec跳过，read/plan仍可继续。

## 已运行结果与原始失败

所有命令经清空外层环境的启动器与`tools/run.py`，固定CPython3.11.9 x64、18包hash锁、私有venv及合成HOME/配置。无真实模型或付费API调用。raw逐命令保存原始stdout/stderr与环境/退出回执，`raw/** -text`不改字节。

| 检查 | 真实结果与raw目录 |
| --- | --- |
| 初始red | `mvp-loop-red`缺产品安装，是环境无效；安装后`mvp-loop-red-valid`缺agent模块才是有效red |
| 首轮循环 | `mvp-loop-green-1` 7 passed |
| 推理现场回修 | `mvp-reasoning-red` 1 failed/7 passed → `mvp-reasoning-green` 8 passed |
| 普通入口初始化 | `mvp-product-1`请求前AtomicFileError；根因缺sessions父层，3184953修组合入口，未放宽SQLite/私密目录门禁 |
| 原生命令环境诊断 | `mvp-product-2/3`已真实改文件但stdout缺失；唯一原因是本测试子环境漏PATHEXT，详[单变量证据](../m02-shell/native-stdout/README.md)，产品Shell字节未改 |
| 七工具与正常重开 | 修合成环境后`mvp-product-4` **9 passed in9.26s**（当时8循环+1产品）；确实执行Python得到new、拒绝文件不存在、第二进程携历史继续 |
| 来源失败屏障 | `mvp-barrier-red`稳定复现后续命令误执行；1ad72d6回修，`mvp-barrier-green` **9 passed in0.16s** |
| 旧候选完整回归 | `mvp-final-pytest` **600 passed,3 deselected in363.64s**；对应0c3c726/旧wheel，不替代r2回归 |
| r2检查 | `mvp-r2-pytest` **601 passed,3 deselected in379.66s**；`mvp-r2-ruff`、`mvp-r2-mypy`、`mvp-r2-offline` exit0；mypy 66源文件 |
| 标准包构建 | `mvp-r2-build` sdist→wheel与`mvp-r2-direct`直接wheel成功；`mvp-r2-artifacts`确认两wheel完全相同、源码/安装/wheel **64个包成员字节相等**，实际SQLite **3.54.1** |

[artifacts.json](artifacts.json)绑定r2 wheel/sdist/hash/64叶子与开发锁；[runtime.json](runtime.json)记录实际加载DLL路径、三摘要、版本/source ID、编译选项与CPython驱动。r2位于根`dist/mvp-r2/`；wheel SHA256=`802e22a52be3b24917460d81353dca50a8ae736e70da5ab2449a3b20abaa8ad7`。

`mvp-r2-text-rounds`复用既有product函数，补普通同进程两轮输入+/exit，**1 passed in11.15s**；独立纯产品环境同一函数也通过。`mvp-r2-chinese-install`中文空格路径安装通过；本机生成的console launcher受应用控制WinError4551阻止为ENV，`mvp-r2-console-policy`确认同一安装的`python -m ruocun`版本/帮助均exit0，未改主机策略。最初launcher启动失败发生于runner创建进程前，初次回执未形成；相同环境的策略复现及模块入口结果已保留。

独立审查与仓库外安装由[M04](../m04/README.md)负责并已通过。真实Windows Terminal按键、视觉/缩放、用户体验、真实模型能力和Linux/macOS实机未验；程序内SIGINT与真实进程对象退出的证据不能冒充这些体验已通过。原82张完整迁移票没有因本首版子集自动完成。
