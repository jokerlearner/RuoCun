# Session／费用基础：独立复核与停止保存点

2026-11-10。实现者 `/root/e01_context`，候选 `c8b30e3e06f1a4d1f8214e3e80100c8295bbe04b`；审查者 `/root` 未编写本切片产品或测试。独立分支 `codex/session-cost-review`，worktree `.worktrees/session-cost-review`，从含最新停止边界的 `e8a3922dee3d0f6ddee87de621217b262d2ac377` 创建，合并点 `371e73a92b1f2ffe6327e6b24441eeae73c66661`。已核对该合并点与候选的 src、tests、pyproject.toml、开发锁完全一致。

范围只含内存 Session 与 cost，属于28的局部基础模块。28整票、完整恢复、命令和loop预算接线均未完成；不以本次通过解锁29或改写母案例族通过状态。08及其它票均已停止。

## 来源与代码审查

根目录AGENTS、CONTEXT、ADR-0005/0009、28票、规格、模块对应及WIRE-06/REC-07等记录作为要求。直接读取冻结ZIP中的四成员并与实现者阅读副本核对SHA-256：

| 成员 | SHA-256 |
| --- | --- |
| src/session/session.ts | 14c9aad3d94ef38c7f06b2c5854808e6d7d90eba82a34c44a4a0a2b85c59104b |
| src/session/session.test.ts | da9e746d0bdd3d59200e94ef5bb43a487a9dfbbb166d8ccd6eb464c6b4689722 |
| src/session/cost.ts | 38e9ca91cb239e57bf8d82891bf87db0251e3fc4c36e8ccca18b48d2dcecdcbe |
| src/session/cost.test.ts | 939d2e2b178237389149a0d4a7672075a96a7ed2bc16d1b7b713632676c85d99 |

规范审查：保持来源职责和camelCase公开接口，复用既有ChatMessage、Usage及D09环境别名；未改变共享存储、平台、client或loop，也未加依赖。代码、来源测试和证据一起提交。预算只有查询能力，持久桥仍未提供，范围说明准确。

规格审查：逐项读取四来源文件、两产品文件和19项既有断言迁移；20条价格数据与来源一致，已知模型优先、归一/回退顺序、cache miss推导、按模型累计、clear与缓存骤降行为均沿来源。未发现本切片阻断项。价格是冻结数据，不声称当前厂商报价；没有新增测试或扩展故障矩阵。

## 独立运行

Windows x64 / CPython 3.11.9，独立venv，从已核验只读wheelhouse按18包哈希锁离线安装开发闭包。通过既有tools/run.py与外层清空环境启动器执行，合成HOME/AppData/TEMP，禁用PYTHONPATH和用户/pytest插件配置。产品由本worktree先构建sdist，再由sdist构建wheel并非editable安装，测试运行已安装产品。

| raw标签 | 结果 |
| --- | --- |
| review-venv / review-deps | 环境创建及哈希锁安装，exit 0 |
| review-build | sdist→wheel构建成功，exit 0 |
| review-install | 本次wheel安装成功，exit 0 |
| review-source-tests | 原有两文件，19 passed in 0.13s，无skip/xfail |
| review-ruff | 两产品文件及两测试文件，exit 0 |
| review-mypy | 两产品文件，无问题，exit 0 |

完整argv、实际输出与退出码见raw各目录。7份工程回执均scan_hit=false；提交前再次扫描原始输出，未发现常见凭据模式。未重复全产品回归、来源Node执行、性能、模型、跨重启恢复或终端体验，不将上述未验范围记为通过。实现者既有red、全项目静态检查与构建证据见[实现记录](../../evidence/28-context/session-cost/README.md)。

## 停止与资源

所有本次命令均等待退出；精确worktree路径筛选的Python/Node/ruocun等自有工程进程检查见resources.json。实现者与08负责人已分别确认退出。未启动真实模型、网络服务或可视终端；没有付费调用。venv、产物、合成状态、各worktree和历史失败材料保留。主协调接收本小模块并保存公共记录后停止；继续执行等待用户明确恢复。
