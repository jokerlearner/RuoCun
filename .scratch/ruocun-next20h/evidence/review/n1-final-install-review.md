# N1 r1 固定产物与仓库外独审

产品/测试源固定 `a7d803ce64f214ba7d757c134bbf0d80526d2dbb`；普通入口和 Read 模块审查见 `n1-ordinary-runtime-review.md`。本次只读复用 root 统一构建的 r1，不构建、不重跑全量、权限 392/162 或其它模块矩阵。

`dist/n1-r1/ruocun-0.1.0.dev0-py311-none-win_amd64.whl` 和 direct wheel SHA256 同为 `1efa7574ab375baa04978646d72e522439bea44e82e420a0e3c4a11b5a5b6799`，先核相等再消费。sdist SHA256=`37c440c796815dac6115a748e2a6ee0261ae6fac71db5dfcfb57e819d8b1cb4b`。

沿已核 CPython 3.11.9 私有仓库外纯安装 venv，按现有 runtime lock 的官方哈希、no-index/no-deps 安装 `prompt_toolkit==3.0.52`、`wcwidth==0.9.4`，并从上述同一 wheel 离线替换旧 N0 产品。`pip check` 通过；实际环境只含 pip、setuptools、ruocun 及两项运行依赖，无 pytest、mypy、Ruff。见 `raw/n1-review-outside-install-01`。

独立从固定 git archive 对照实际 worktree、sdist、wheel 和仓库外 site-packages：**121 个产品成员集合及字节完全一致**，无旧安装残留；direct 与 sdist 重建 wheel 同完整哈希。wheel 标签 py311-none-win_amd64，Root-Is-Purelib=false，除产品和自身 dist-info 无其他成员；sdist 无测试、scratch 或 worktree。wheel METADATA 与已安装发行版恰好两项 Requires-Dist，版本与实际已装依赖相同。逐成员指纹见 `n1-final-install/artifacts.json`，独立命令见 `raw/n1-review-outside-binding-02`。构建 hook/许可证等包装文件继续使用 root 工程绑定证据，不重复该全脚本。

在新建的仓库外合成状态目录，沿已有纯安装方法用 `n1_outside_confirmation.py` 只调用**原普通 CLI 和唯一原受控 TTY 两个函数**。不复制或改写断言，不装 pytest；TTY 仅通过 stdlib ExitStack/patch 提供原 fixture 使用的 setattr/setenv，还原后不留 patch。父进程实际 ruocun 来自该 venv 的 site-packages，CLI 子进程绑定相同产品；TTY 不冒充真实 Windows Terminal/resize。两原函数、标准模块入口 `--version`/`--help` 均通过。实际已加载的私有 SQLite 3.54.1 受控 DLL 使用相同路径身份复核，gate=met，最终非主线程 0。原函数所在文件哈希执行前后不变，与固定源绑定一致。见 `raw/n1-review-outside-confirmation-02`。

首两条原失败如实保留：`raw/n1-review-outside-binding-01` 复现旧归档脚本在 Git autocrlf 下的包装 hook EOL 差异，独立最终产品绑定显式固定 archive LF，全部产品字节仍严格比较；`raw/n1-review-outside-confirmation-01` 在两个入口函数都已执行后，helper 末尾请求了与 TTY 实际加载不同路径的同版 DLL，受门禁正确拒绝。后者只改验收 helper 复核实际路径，用同两原函数重跑得到完整 exit0；没有改包、门禁、源断言或主机策略。这两次是 ENV/验证接线，不回填成通过或冒充产品失败。

全部进程沿白名单启动器/tools.run、合成 HOME/config/TEMP，原始回执保留，敏感扫描 false，真实/付费模型 API 调用 **0**。r1 仓库外固定安装独审阻断 **0**；项目全量及任务票自动出口由 root 的独立证据决定，真实模型、Windows Terminal/resize 与人工体验仍 pending。

## 全量测试收集隔离复验

初次全量记录 1153 项通过、1 项失败、3 项 deselected。收集 `test_session_sqlite.py` 时顶层导入绑定系统 SQLite 3.45.1，原 TTY 用例在同一进程启动时被真实运行库门禁拒绝。等待首条输出的超时掩盖了该异常。作者保留原超时和显式取得 `RuntimeGateError` 的两份失败回执。

测试提交 `9f5026d0c50e90caf103c2cd7833cf507957b795` 保留原 pytest ID，把原 TTY 过程放入同一解释器的 `-I` 子进程。包根取父测试实际导入的 `ruocun.__file__`，子进程在测试临时目录运行，使用显式环境白名单及合成 HOME、ProgramData、TEMP，stdin 关闭。实际 `runtime._run` 仍调用真实门禁。子进程退出码被断言，已结束任务的原异常从等待循环直接传出。独立 AST 比较确认原过程 26 条断言和 5 处异步及释放等待调用逐项一致，8 秒等待与 0.01 秒轮询均保留。

独立仅复原 TTY 和 SQLite 两文件，**4 passed in 4.16s**，exit 0，敏感扫描 false，真实/付费模型 API 0。回执见 `raw/n1-review-tty-sqlite-01`。固定 `a7d803c` 到主线测试合并点 `896ecaf` 的产品及构建输入字节相同，上节仓库外纯安装证据继续绑定同一 r1。复现上节时向纯安装 helper 传入 `a7d803c` 的两个原测试文件。`9f5026d` 的新 pytest 包装器由本节组合验证覆盖。全量复验由 root 记录。
