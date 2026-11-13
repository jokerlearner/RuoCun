# 82 平台门禁与实跑回执

冻结 `.github/workflows/ci.yml:3–24` 的推送／PR lint、类型检查、测试与构建意图由本仓 `.github/workflows/ci.yml` 保留。冻结 `release.yml:3–35` 的候选产物生成意图由手动 `package-candidate.yml` 保留，范围按 D2 为 Windows 标准 wheel/sdist 与哈希。两个工作流均用仓内 `.github/ci` 入口，仓外安装回执和 JUnit 可直接复用。当前仓库未配置远程，两个工作流已本地解析并验证 POSIX 命令语法，托管运行待验。[本地入口](../../../../../.github/ci/README.md) · [工作流解析](raw/b09-ci-workflows-parse/stdout.bin)

Windows 本机以 CPython 3.11.9 运行 Ruff、mypy 和新 CI 安装冒烟。安装阶段复用最终 `b09-r3`，产品 `8e7760ce`，wheel SHA-256 `764d9f908c583de07f32f48f0618b74c0c82f273ec02ae672496efb00aedb81d`。运行实际新建仓外 venv，离线锁定安装，`pip check`、纯包导入位置、版本和帮助均通过。[静态检查](raw/ci-static) · [最终包冒烟](raw/ci-package-r3)

默认全量按一次运行安排在 R1 产品 `0252fe7f`、wheel SHA-256 `142afa7757e6d29ae9b9ed908e4521a5ca6e9f483729b4c915fb4d8142c61cb9`。首轮为 **1679 passed，20 failed，4 deselected**，657.74 秒。原全量 stdout 与 JUnit 保留。9条失败的验收辅助进程未安装 `ruocun_acceptance`，其余11条普通入口和 ACL 夹具的独立 `python -I` 进程未安装 pytest。首轮只向 pytest 父进程追加开发依赖路径，无法让子进程看见这些模块。[首轮](raw/b09-ci-installed-full/stdout.bin) · [首轮 JUnit](raw/windows-r1-first-junit.xml)

用另一个仓外 QA venv 离线安装同一 R1 wheel，把测试辅助路径加入该 QA 环境后，根据原 JUnit 精确选取20个失败 node id。**20 passed**，51.98 秒。R1 全量和原失败用例的结果分别保留，R3 的受影响路径由主协调另做定向。产品纯安装环境未加入 QA 路径。新 CI 在纯产品冒烟之外给 QA 环境实际安装开发锁、同一 wheel 与 `tests/support`，让真实子进程也能运行这些用例。[精确复跑](raw/b09-ci-installed-red20/stdout.bin) · [复跑 JUnit](raw/windows-r1-red20-junit.xml)

Ubuntu 24.04 WSL 的现有 CPython 3.12.3 实跑 Linux 设计入口，278 个产品 Python 文件按 3.11 语法解析并编译，来源 CLI 版本和帮助成功，实际 `/bin/sh` 保留 Unicode 与环境变量，Linux 沙箱禁网参数正确。该入口还检查包标签仍是 Windows x64。macOS 工作流配置了同一设计检查，现环境无 macOS runner，实跑待验。POSIX 产品包安装与完整运行保持未验。[WSL 回执](raw/b09-ci-wsl-posix-design/stdout.bin)

所列本地进程用白名单和合成状态，两份 JUnit 单独扫过环境敏感值，均未命中。完整回执及 XML 可供84复用，产品安装与人工体验边界依对应票判断。

在另一全新仓外 QA venv 中，逐项实跑最终 CI 的开发哈希锁、R3 wheel 和 `pip install --no-index --no-deps --no-build-isolation tests/support`。pip 构建并安装了普通 `ruocun_dev_support-0.1.0-py3-none-any.whl`。产品、pytest、oracle 与 `ruocun_acceptance` 均从该 QA 的 `site-packages` 导入，独立 `python -I` 子进程也全部导入成功。检查未使用 editable 或 QA 注入路径。这一步仅验证实际安装链及导入，批次全量仍复用上述回执。[实际构建](raw/b09-ci-qa-clean-support/stdout.bin) · [父子导入](raw/b09-ci-qa-clean-child-import/stdout.bin)

独立复核后复跑实际安装身份。旧入口把同为 `0.1.0.dev0` 的 R1 纯环境与 R3 wheel 组合，旧包的导入、版本与帮助均通过。探针提供了不存在的 Git 路径，用来在旧门禁通过时停在 QA 之前。修复后同一组合在安装身份处因 `ruocun/agent/runtime.py` 字节不同退出 1，版本、帮助和 QA 步骤未执行。实际 R3 纯环境搭配 R3 wheel 通过 309 个产品文件及 `METADATA`、`WHEEL`，随后版本和帮助通过。两个工作流均解析确认原始回执上传只在 `success()` 时执行。Ruff 通过，未复跑全量或重打包。[原错配](raw/ci-mixed-before/installed-origin/command.json) · [现拒绝](raw/ci-mixed-after/installed-origin/stderr.bin) · [R3 字节校验](raw/ci-r3-bind-pass/installed-origin/stdout.bin) · [上传条件](raw/b09-ci-artifact-guard/stdout.bin)
