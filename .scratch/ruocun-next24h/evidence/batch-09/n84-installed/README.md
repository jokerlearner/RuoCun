# 84 · 最终 Windows 安装包集成

固定候选 b09-r3，产品提交 `8e7760cea9ad7fa7b500fccd32984f5c9813f930`，wheel SHA-256 `764d9f908c583de07f32f48f0618b74c0c82f273ec02ae672496efb00aedb81d`。依赖 76、81、82 已通过，77 的自动技术出口已在任务图实际验证。使用 Windows x64 CPython 3.11.9 仓外 QA 安装，产品及测试支撑均为非 editable 安装。命令经白名单和合成用户目录启动，运行前逐字节核对导入路径与 309 个产品成员。[固定产物](../package-r3/README.md) · [实际非 editable 安装](../n82-ci/README.md) · [命令](raw/b09-n84-installed/command.json)

| 范围 | 安装证据 |
| --- | --- |
| 注册、工具 schema、拒绝坏参数和按需激活 | 复用来源工具注册、ToolSearch、权限与计划态用例。通过实际安装目录加载并执行，离线断言覆盖工具可见性、确认边界和拦截。 |
| 固定命令与八项 core Skills | 复用冻结来源命令词法、51 个公开固定命令目录及明确排除的插件入口、内置八项黄金文本及 SHA、Skill 加载和覆盖用例。 |
| 启动及平台路由 | 实际普通入口 eval 开关与受控通道，Windows 显式沙箱拒绝及正常 Shell；另用 R3 受影响 110 项覆盖账户、向导、启动、终端、定时/电源和 Deck。 |
| 运行与恢复 | 复用 [76 R3 的10项](../eval/n76/README.md)与既有 59 项源码离线回执，覆盖后台等待、取消、Hooks、MCP 防重放、LSP 和 Deck。[79 仓外](../n79-probe/README.md)在纯安装下实际接管同一 Shell run。[81 升级](../n81-upgrade/README.md)实际恢复原会话并保护异常数据。 |
| 终端与原生能力 | 77、78 的 19 项自动技术证据按同一 R3 产品重新绑定，当前原生凭据和控制台模式有独立复验。真实交互、登录和重启留在两票人工出口。 |

本批安装集成实际 **61 项通过**。依赖、绑定、执行和敏感值扫描均通过。[stdout](raw/b09-n84-installed/stdout.bin) · [77/78 自动技术出口](../../../../ruocun/evidence/b09-r3-automatic/README.md)

## 结果归因

- **PORT-REGRESSION**。R1 的未知配置版本可以改写。修后 R3 的四类账户异常和两类会话库异常均保留原字节。离线评估的重定向和无效反思值也已单独修复并保存回执。[81](../n81-upgrade/README.md) · [73](../eval/n73/README.md) · [74](../eval/n74/README.md)
- **ENV**。R1 默认全量首跑 1679 通过、20 因测试依赖对子进程不可见失败、4 未选。隔离 QA 下原 20 项精确复跑均通过。R3 在同一来源测试基线上按产品两处文件的差异复用，新增当前包定向用例。Windows 应用控制对新生成 launcher 的 4551 错误按实际记录，R3 的模块入口仓外验证成功。[82 回执](../n82-ci/README.md) · [79 环境差异](../n79-probe/README.md)
- **SOURCE-DEFECT / INTENTIONAL-DELTA**。来源缺陷按原工单保存。系统定时、防休眠、桌面通知、特殊 fork 无完整现场、历史费用及插件等按已批准范围和来源行为各自裁决。[保留范围](../../../../../docs/adr/0010-selected-scope-and-lean-workflow.md)
- **UNVERIFIED**。真实模型、最终 Windows Terminal 人工操作、macOS 实跑和原始外部帧材料按原记录保留。安装使用标准 Python 包，自动通过范围以本页和逐票为准。
