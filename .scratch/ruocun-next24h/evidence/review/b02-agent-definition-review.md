# 39 自定义代理定义独立核验

初始候选 `a476233`，普通入口接线 `f01e5e0`。核对 39 的 EXT-05/CFG-03、冻结 `agent_defs.ts`、`agent_tools.ts`、`runAgent.ts`、`agent_memory.ts`、`turn_budget.ts` 及 `index.ts`，沿 D09、ADR-0009/0013/0015。只在白名单、合成 HOME 和受控 Windows SQLite 中执行，模型由夹具注入。

初始独立回执 `b02-review-agent-defs` 为 3 passed in 2.87s，包含冻结 parser 和实际子派发。普通 CLI 内置、自定义子派发与定义的 5 项结果沿主协调回执。来源核对确认项目定义覆盖用户与同名内置角色，`--no-skills` 停用磁盘定义；项目 agents 沿冻结发现边界。工具列表先裁剪，memory 有来源定义级 Read/Write/Edit 找回，plan 仍实质移除写入。完整模型 ID 与调用覆盖保留，`inherit` 由父会话解析，独立轮数与 effort 进入实际模型回合。当前解析 Hook/MCP 字符串引用，声明后在执行前明确拒绝，由后续对应端口完成。

原三项用例通过后，复用同一真实子派发夹具确认两个缺口。`b02-review-def-external-red` 观察到子 `bypassPermissions` 下区内写、无授权区外读和区外写均实际成功。冻结 `runAgent.ts:405–416` 继承父上下文，`index.ts:1398–1417` 的区外授权读父模式；RuoCun 现有 Write 额外执行区外授权，应保留。`b02-review-def-memory-red` 观察到相对写入实际工作树，角色长期记忆路径却也在临时工作树内。冻结 `agent_memory.ts:23–27` 绑定进程项目目录，进入工作树只切换工具执行目录。

`646b5f8` 修复后在已合 `f01e5e0` 的独审树复跑原两条。`b02-review-def-external-green` 确认区内实际写成功、区外无授权读写都未发生。子工具分类使用独立模式，区外路径继承父回调，每次工具派发新建父授权作用域。`b02-review-def-memory-green` 确认相对写仍落在活动工作目录，长期记忆路径指向原项目。两次退出码均为 0，敏感扫描无命中。父单次区外许可需逐次询问，沿用实现者该路径回执。

39 独立审查通过，已验证的定义、权限及执行接缝可供后继任务使用。
