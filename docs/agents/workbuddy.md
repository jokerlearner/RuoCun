# 使用 WorkBuddy 接续 RuoCun

此页说明WorkBuddy的接入方式；当前开发工具、完成数、集成提交、未完成候选、停止边界及下一张票以[实施进度](../../.scratch/ruocun/implementation.md)为准。最初03后交接WorkBuddy的安排保留为历史，不能当作当前启动授权。

排程、计时和启动边界读取[当前 24 小时计划](../../.scratch/ruocun-next24h/plan.md)及实施进度。派发时按[当前范围](../adr/0014-terminal-and-scope.md)过滤旧 frontier，批次和验证按[ADR-0010](../adr/0010-selected-scope-and-lean-workflow.md)。

## 在截图界面如何选择

1. 中央“办公 / 开发”选择 **开发**。
2. 输入框下“选择工作空间”选择 **`D:\java supplement\Firstcode\RuoCun`**。这是主工作区，包含独立 Git 仓库、规格、记录和冻结参考。不要选择父目录、活动 DAO 或历史实验 worktree。
3. 如显示分支选择器，保留 **`integration/ruocun-migration`**。主协调会话的 **Worktree 开关保持关闭**，以便统一维护集成与任务状态。
4. 权限先保持截图中的 **默认权限**。它与项目中的执行授权是两回事，工具自身弹窗仍由用户处理。“完全访问”是客户端所有任务的全局开关，不是仅此项目的设置。
5. 模型可先保留截图里的 **Hy4**。截图没有展开其它模型；本交接没有测试或承诺某个 WorkBuddy 模型的开发能力。无需为接手额外填写 RuoCun 的模型 API Key。
6. 如果出现该项目的工作区信任确认，核对路径为 RuoCun 后选择正常打开；受限模式可能不加载项目技能。无需信任 DAO 父目录或全盘。
7. 将[主协调 prompt](workbuddy-prompts.md#主协调会话)粘贴到输入框发送。以后继续使用同一主协调任务，进度保存在 Git。

工作空间负责指定读写目录，不能替代 Git 分支与状态核验。接手时必须记录实际 HEAD；若文件已有变化，先检查来源，保留未保存工作。

## 技能如何准备

本项目已携带 [ruocun-workflow](../../.codebuddy/skills/ruocun-workflow/SKILL.md)，内含 implement-spec、tdd、code-review 等必要原始参考和许可，无需从市场搜索同名技能，也无需复制 Codex 的整个配置目录。

官方开发配置说明支持项目 `.codebuddy/skills/<name>/SKILL.md`。这里只新增项目技能与文档，规则入口仍是 `AGENTS.md`，没有安装 Hook、MCP、全局命令或权限豁免，也没有复制凭据。

这套文件已检查结构和链接，尚未在用户的 WorkBuddy 5.9.4 实际加载验证。如果“已安装”里没有显示该项目技能，仍可让代理直接读取上述 `SKILL.md` 及其引用文件，按同样工作流执行。交接临时目录也提供单技能 ZIP；如需界面导入，可到“专家·技能·连接器 → 技能 → 添加技能 → 上传技能”选择该包。导入成功和本项目技能是否自动加载，都以客户端的真实反馈为准。

不必先安装办公、PPT、网页发布类技能或连接器。项目源码、Git、Python 与测试工具链才是本次必要环境。

## 第一次接手必须确认的能力

主代理应先核对当前授权与停止边界，再汇报以下真实结果；规则或能力缺失仅阻塞依赖它的票，其它前置已满足的独立工作按当前授权继续：

- 能否读取 Git 纳管的规格和记录、运行 Git/Python/测试，以及创建独立分支和 worktree。
- 能否新建独立上下文的实现子代理、指定其工作目录、后台运行并回收结果；让一次只读子代理返回其路径、分支、HEAD，核实后再派正式票。
- 能否使用独立 merger 复验候选并完成本地集成。仅创建 worktree 不等于已经创建独立子代理。
- 实际并发槽位是否支持主协调+2实现+1独立审查共4槽，审查者未参与所审候选。按ADR-0010复用同领域负责人、worktree及私有环境，逐批记录基线和隔离状态；关键接缝交回，不用reset处理已有候选。

官方 Worktree Task 可用于手动创建独立任务：开启 Worktree 时，**Base Branch 选择 `integration/ruocun-migration`，不要沿用默认 main**。它会从已提交的 tip 创建分支，不携带未提交文件。具体分支名可使用工具实际生成的名称，并登记到任务票。

若当前版本没有可由主代理调用的子代理能力，先明确这一限制。可采用同一客户端的独立 Worktree Task 执行实现和复核，主协调任务负责发出[实现/复核 prompt](workbuddy-prompts.md#独立实现任务模板)、回收 SHA 并更新状态。用户需要手动新建这些任务时，由主协调代理一次给出具体票、Base Branch 和 prompt。不要用同一会话内几个角色标题冒充独立代理，也不要静默改为所有票在主目录实施。

## 环境与接续位置

正式工程入口、依赖锁和隔离安装方法读取项目的[开发说明](../development.md)与[03 票](../../.scratch/ruocun/issues/03-boot.md)。各 worktree 使用自己的虚拟环境。历史实验中的解释器/Node cache仅在证据明确授权的只读边界使用，不当成正式产品依赖。

正式实现、决策实验使用各自目录和状态。D22失败资产按ADR-0008保留为历史，额外Windows沙箱已取消。03通过不代表最终标准包或终端验收完成；独立程序、成套live成绩及旧量化性能门禁按ADR-0010移出，不再从旧模板恢复。

用户已要求人工体验集中最终整体验收；源故障、迁移缺陷、环境无效、未验证分别记录。产品自己的凭据、费用和真实模型验收，不能用 WorkBuddy 登录态或内置模型可用来代替授权。

## 官方依据与适用范围

核对日期：2026-11-05。用户截图版本为 WorkBuddy 5.9.4；以下是当日官方在线说明，菜单和能力仍需客户端实际确认。

- [创建任务](https://www.codebuddy.cn/docs/workbuddy/Create-Task)：选择工作空间与补充文件上下文。
- [Git 集成和并行开发](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Worktree-Task)：任务分支、Worktree Task、Base Branch 与提交边界。
- [技能](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)：技能页和本地包上传。
- [开发配置兼容](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Setting#代码开发的用户级配置兼容说明)与[配置目录](https://www.codebuddy.cn/docs/cli/codebuddy-dir)：开发模式配置及项目级技能结构。后者是官方设置页引用的 CodeBuddy 文档；不据此推定本客户端所有 CLI 功能都可用。
- [默认权限与安全沙箱](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Permission-Modes)：权限入口、全局完全访问与工作区信任。
