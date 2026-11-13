# RuoCun 0.1.0.dev0 本地交付

## 原生配置与品牌更新 b09-r7

Windows x64 CPython 3.11，源提交 `0a0c523e12b9a47bcd4d1685546461cc70f32f9c`。账户、设置和扩展从若存原生入口加载，产品环境开关使用 `RUOCUN_`。正式界面、帮助、模型提示和包说明使用若存品牌。[配置决定](../adr/0018-native-configuration.md)

本机硅基流动账户已迁到若存 Windows 凭据服务。读回核对保留原 Key、服务地址和模型，未发出模型请求。桌面的「若存 Code」快捷方式指向正式入口，已实跑打开新版 Windows Terminal。旧入口副本 `Open-RuoCun.b09-r6.cmd` 可回退。

原生配置独立定向复核 112 项、最终安装包终端与配置定向验证 40 项通过，覆盖有重叠。固定源、sdist、wheel 和安装目录的 309 个产品文件字节一致。构建使用固定源码归档，包内许可证及归属声明与归档原文一致。

默认全量首轮 1,682 项通过、6 项失败、4 项未选。将临时目录设在仓外，绑定最终安装包和更新后的测试断言后，6 项均定向复验通过。

| `dist/b09-r7-final/` 文件 | SHA-256 |
| --- | --- |
| `ruocun-0.1.0.dev0-py311-none-win_amd64.whl` | `fa782eade89f5e3a1c507808dd0820d5751189cc65d9b4f1d1b5da88276b87fb` |
| `ruocun-0.1.0.dev0.tar.gz` | `9daea07b6e00df4b161d5fca938959affb7e1ae312567563f811a6a31efb01c2` |

## 正式终端更新 b09-r6

Windows x64 CPython 3.11，源提交 `e30a104f3c0d6cb4327f173b76bba691b7645267`。实时区按收到的思考、正文和工具请求显示状态。中文终端向模型补充简体中文思考指令，实时正文使用服务端返回的文本。语言切换从下一轮更新指令，无额外模型请求。

专属 Windows Terminal 重绘先绘欢迎卡和原始 Sixel 帧，再重放历史。旧安装在历史超出可视区时稳定漏画原始图形帧。原图和欢迎卡共用同一窗口尺寸，测试覆盖放大、缩小、长历史及草稿保留。

源码定向验证 62 项、缩放独立复核 16 项、安装包终端定向验证 17 项通过，覆盖有重叠。已核对 309 个产品文件在源提交、sdist、wheel 和安装目录中的字节一致。正式入口使用 `venv-b09-r6`。用户在真实 Windows Terminal 运行 `/help`、最大化并还原后滚回欢迎卡，确认原图清楚。入口副本 `Open-RuoCun.b09-r5.cmd` 可用于回退。

| `dist/b09-r6/` 文件 | SHA-256 |
| --- | --- |
| `ruocun-0.1.0.dev0-py311-none-win_amd64.whl` | `834b4c6c641feec26139b770ede52872cd0247a4e4ba9e9bfda6398926185c00` |
| `ruocun-0.1.0.dev0.tar.gz` | `ed8be177cab841f9a1f39ffdac36874cb4f6052fff9374c36c89554b198f6d59` |

## 正式启动界面更新 b09-r5

Windows x64 CPython 3.11，源提交 `4dd8430475cd00e24006f9f689b332acc3fdfb04`。底栏以绿色显示权限模式和 Shift+Tab，随后显示模型短名、费用、上下文和 Git 分支。空闲时按键在智能批准和全权放行之间切换并显示提示。当前会话有任务运行或等待时，按键只提示。两档调用既有权限裁决，按键选择在当前进程生效。欢迎卡保留若存形象，交互界面仅在保存失败或结果未确认时提醒。

源码定向验证 42 项、独立权限与调度复核 39 项、安装包终端定向验证 21 项通过，覆盖有重叠。已核对 309 个产品文件在源提交、sdist、wheel 和安装目录中的字节一致。正式入口使用并行安装 `venv-b09-r5`，已启动新的 Windows Terminal 窗口。原安装 `venv` 和入口副本 `Open-RuoCun.b09-r4.cmd` 可用于回退。

| `dist/b09-r5/` 文件 | SHA-256 |
| --- | --- |
| `ruocun-0.1.0.dev0-py311-none-win_amd64.whl` | `808641b25aed1bceb495b67b55bae811a3176256604fb72c6f9d53c64fc93438` |
| `ruocun-0.1.0.dev0.tar.gz` | `f3aed759093930ec2414181ce0514465176b5f154bb84f6383adb04b6c91d932` |

## 最终 Windows 候选 b09-r4

2026-11-12，77、78、85 已通过，有效范围 79/79。固定源提交 `fcde3a921ba42aa1b52844757b343291fc073d21`，构建和验收环境为 Windows x64 CPython 3.11。最终实际安装的 309 个成员已与固定产物逐字节核对。[产物及定向验证](../../.scratch/ruocun-next24h/evidence/batch-final/package-r4/README.md) · [最终验收](../../.scratch/ruocun-next24h/batch-final.md#最终验收与交付)

| `dist/b09-r4/` 文件 | SHA-256 |
| --- | --- |
| `ruocun-0.1.0.dev0-py311-none-win_amd64.whl` | `cd9724366ddd1dcb449c53321daff4048ffa967244fa96b83e54411ad131e139` |
| `ruocun-0.1.0.dev0.tar.gz` | `a1ffcc6a5681c9b086cac725b2f7ec713b8127a5f1a8023c0cbd7a5cc5bb104e` |

最终 Windows Terminal 交互、Windows 重启后恢复原会话及系统凭据、正常退出与合成凭据清理均已核实。Ubuntu WSL 保留既有源码及 POSIX Shell 实跑回执。macOS 实机、完整 POSIX 安装运行、其它 Windows 账户的安全负例和托管 CI 待验证。成套真实模型评估与量化性能门禁按确认范围移出。[范围核对](../../.scratch/ruocun/issues/85-delivery.md)

## 批次09技术候选 b09-r3

批次09技术候选的固定源提交为 `8e7760cea9ad7fa7b500fccd32984f5c9813f930`。下列构包、安装和恢复材料保留为 R3 技术历史。评估成绩覆盖本地合成场景。[批次与证据](../../.scratch/ruocun-next24h/batch-09.md)

| 文件 | SHA-256 |
| --- | --- |
| `ruocun-0.1.0.dev0-py311-none-win_amd64.whl` | `764d9f908c583de07f32f48f0618b74c0c82f273ec02ae672496efb00aedb81d` |
| `ruocun-0.1.0.dev0.tar.gz` | `d94cabc7c5cf9dfd1054c94f54c5e183400c7333c69e714c53ac3ae85502711c` |
| `requirements-runtime-win311.lock` | `9d963ff54a69be39ef85ae24ca583d27a4e12ffc2b5bd58d31ad6b077ffe54b1` |
| `requirements-dev-win311.lock` | `f4e2b6c96033a245bfd54de952c0d0220c68496759559475fea4bd61e43d584e` |
| `requirements-observation-win311.lock` | `063126e0f4e537a802223e632d69dd5b13bcd2abcf8b0dc9f75bc2dd364ba9fa` |

本地包在 `dist/b09-r3/`。用 `Get-FileHash -Algorithm SHA256 <文件>` 核对实际文件。表中的观测锁摘要按 Git 内的 LF 字节计算。若 Git 在 Windows 检出为 CRLF，该文件的本地摘要为 `3d6591d2a4c04a60940986f4cafa5fdfe6c2e892fabaa26dde7a02a794c22d58`。309 个随包成员已比对 Git 归档、sdist、wheel 和安装目录。[产物与成员清单](../../.scratch/ruocun-next24h/evidence/batch-09/package-r3/artifacts.json)

## 可重建路径

1. 取上述固定提交，在 Windows x64 使用已核验 CPython 3.11.9。候选构建的工作树中 `LICENSE` 为 CRLF，其余产品成员换行和 Git 对照以清单为准。
2. 在合成 HOME 和受控工程环境按开发锁安装构建工具。准备包含锁定依赖的离线 wheelhouse，使用 `pip install --no-index --find-links <wheelhouse> --require-hashes -r requirements-dev-win311.lock`。
3. 通过 [白名单执行器](../../tools/run.py) 执行 `python -I -X utf8 -m build --no-isolation --outdir <新的输出目录>`。默认先生成 sdist，再从 sdist 生成 wheel。向另一目录用 `python -I -X utf8 -m build --no-isolation --wheel --outdir <另一个输出目录>` 构建直接 wheel。技术候选两次 wheel 的 SHA-256 一致。新建仅有产品和运行依赖的 venv，检查仓外 `--version`、`--help`、依赖一致及恢复入口。
4. [本地 CI](../../.github/ci/README.md) 提供同样的分阶段检查和产物回执。完整包绑定使用[成员核验脚本](../../.scratch/ruocun-next24h/evidence/integration/bind.py)，输入、退出和摘要在[候选记录](../../.scratch/ruocun-next24h/evidence/batch-09/package-r3/README.md)。

| 平台 | 本批证据 |
| --- | --- |
| Windows x64 CPython 3.11 | 实际构包和纯安装、仓外会话和后台恢复、手工更新及数据保护，Windows 默认测试和定向回归各保留实际回执。最终 Windows Terminal 用户操作单列。 |
| Ubuntu WSL | 实跑源码导入、3.11 语法和实际 POSIX Shell，适配与禁网路由另有来源回执。当前标准包为 Windows x64。 |
| macOS | 已配置源码适配检查，实际 runner 和产品实机待验证。 |

CI 本地入口和工作流定义已交付，当前仓库未配置远程。已核对默认测试、精确复跑、平台和实际仓外安装回执。[82 平台记录](../../.scratch/ruocun-next24h/evidence/batch-09/n82-ci/README.md)

## 第三方组件与终端资源

- [若存许可证](../../LICENSE)、[发布须知](../../NOTICE.md)和[第三方许可证](../../THIRD-PARTY-LICENSES.txt)随当前构建产物分发。
- Windows 运行闭包含 44 个已锁定 wheel。各 wheel 的版本、来源元数据、锁定 SHA-256、许可声明和实际许可文件摘要均可核对。可选观测的 16 个 wheel 另有登记。[运行依赖许可清单](runtime-licenses-win311.json) · [可选观测许可](../../.scratch/ruocun-next24h/evidence/batch-07/n57/dependency-closure.json)
- 随包 SQLite 3.54.1 是已核验官方固定 ZIP。安装运行时实际解包，核对 DLL、版本、source ID 和 Win32 VFS。SQLite 为 public domain。[包内来源](../../src/ruocun/resources/runtime/README.txt) · [实际绑定](../../.scratch/ruocun-next24h/evidence/batch-09/package-r3/runtime.json)
- 批次 09 的欢迎角色曾从冻结快照里的本地素材覆盖层装配。后续已核对独立角色 PNG、预览生成器和帧来源，当前包内数据直接取自独立预览产物。[本次来源核对](resource-provenance.md) · [原始材料记录](../../.scratch/ruocun-discovery/research/04-terminal-platform-delivery.md)

[安装与恢复](../install-and-recovery.md) · [更新日志](../../CHANGELOG.md)
