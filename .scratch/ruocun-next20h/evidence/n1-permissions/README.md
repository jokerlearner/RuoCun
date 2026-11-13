# N1 / 09 候选 A：规则、设置与审批门

本候选基于 `19106d791ed2fd2ed82f776effea29a15cd3c021`，只修改线一独占文件。
冻结来源归档与 MIT 许可证 SHA、每个产品文件及对应 TS/source test 的 hash、
规划工具四段原运行时描述 hash 见 `candidate-a.json`。未读取活动 DAO 或真实用户配置。

实现：规则私有 glob/命令前缀、环境与 wrapper 非对称剥离、工具身份及 rememberRule；
settings 数组并集/后层模式覆盖/CLI flags/来源追踪；模式与风险裁决；审批批处理及
once/session/always；原生目录信任；deferred 规划工具和模式工具表。
`allowedPrompts` 沿来源只是权限预声明，handler 没有把它转成权限授权。

验证为显式本工作树 `src` 导入，未声称这是 wheel/install 验证：

- `n1-a-verify-final`：392 passed。迁移原 rules、identity、bash_preprocess、settings、
  bash_safety、dangerous_patterns、engine、gate、approval、trust、plan_mode 适用断言，
  原测试的作者目录改为合成 `/fixture/fishing`。tools_for_mode 仅迁移普通内置与 deferred 子例；
  MCP 连接/搜索/完整 51–54 后置。少量来源断言合并在同一 pytest 用例中，392 不等于 DAO 的 it 数。
- `n1-a-static-final`：Ruff 通过。`n1-a-types-final`：mypy 18 源文件通过。
- `n1-a-record`：归档/许可证 SHA、四段 plan 描述逐字比对、18 产品 LF 字节检查通过。
- 分片 red→green 原始失败/修正结果保留在 `raw/`；其中 settings 首次 green 和 gate 首次
  green 是测试适配问题（缺 asyncio marker、objectSchema required 参数），也原样保留。
  纯 Python mypy 切换只发生于本私有 venv；官方同版 wheel 的固定 hash 见 `mypy-tool.lock`。

必要 Python 接缝：`permissions/bash/types.py` 单点定义 UTF-8 byte offset Node 与
simple/too-complex/fallback union。`evaluateWithAst(..., *, parseBash)` 与
`decideAsync(..., *, parseBash)` 接受异步 parser。`PermissionGate` 保持来源位置参数，
另接受 keyword `parseBash`；候选 A 未装配 parser 的 Bash async 路径明确报错，不能静默当 legacy。
仅用本地注入 fake 验证 async 规则分支；不声称完整 AST 已通过。

`config/trust` 的 `isTrusted/addTrusted/shouldTrustProject` 可显式传 `userRoot`；
`shouldTrustProject` 另接 `environ` 与 `projectConfigPresent`，供 root 统一处理显式兼容
项目 settings/local 的信任门，不自动读取旧 DAO。trust receipt 永远原生。
本模块只执行 gate，目录层级装配与兼容文件诊断仍属 root。

ADR-0013 有限差异：原来源写入 helpers 对坏 JSON 可能用空对象覆盖；本候选读取仍容错，
但修改现有坏 JSON/错误根结构时抛错、保留现场。`test_n1_permissions_preserve.py` 是该要求的
最小适配确认，未计作来源原断言。审批表存在非字符串项时也保留文件并报错。

未验/未完成：B 的完整 parser/walker、来源 bash_ast/ast 测试、普通 CLI 接线后的最终参数
同一裁决和 plan 执行硬门、整套固定产物、独审与人工终端体验。可选 classify callback 只迁移
来源协议与 fake 测试，没有创建分类器、真实模型调用或启动 24。09 仍 claimed，不能 resolved。
