# 70 固定52命令逐项盘点

盘点日期：2026-11-12。冻结基线：dao-f17e189-7ac654a0dc06/source.zip；固定目录为 `.scratch/ruocun/module-map.md` CMD-* 的52行。产品快照为主线 `7cf5921b`，另外只读观察了主协调尚未提交的 `/audit` 接线；下表明确区分这部分在途改动。此次仅写本清单，不改产品、不运行测试、不改票状态。

表中 `runtime` 指 `src/ruocun/agent/runtime.py` 的 `command` 实际分支；ContextManager 指 `agent/context_runtime.py` 的 command；permissions 指 `permissions/runtime.py`。`T` 为已有普通入口/TTY测试，`M` 为已有模块测试，`—` 为未定位该命令的直接行为断言。这里只登记可复用测试位置，**不代表本轮已复跑、不代表每个子参数/失败边界均验收**。欢迎文字、帮助、schema和静态分支均不能代替实际行为证据。

来源定位：基础9项为 `src/commands/commands.ts`；其余TTY分支为 `src/index.ts`（下表 I+行号）；内置prompt为 `src/commands/builtin.ts`；theme/loop为 `src/tui/app/App.tsx`。同一命令的基础dispatch和TTY分支可以并存，保留来源大小写。

| 序号 | 冻结名称／别名、来源 | 当前实际路由／状态 | 已有测试位置与待补事实 |
|---|---|---|---|
| 1 | `/model`，基础30＋I2475 | runtime账户/模型面板及switch_model | T `test_b02_account_runtime.py`：真实请求模型切换；别名/来源参数范围由70复核 |
| 2 | `/plan`，基础44 | runtime→permissions.command，工具Gate和目录裁剪 | T `test_n1_runtime_tty.py`；M `test_n1_permissions_runtime.py::test_mode_commands_follow_source_toggle` |
| 3 | `/clear`，基础51＋I1923 | runtime→Conversation.clear＋todos清理＋history重绘 | T `test_b05_sessions.py::test_source_session_commands_switch_branch_and_continue_through_normal_entry` |
| 4 | `/compact`，基础55 | runtime暂停/等待保护→ContextManager.command | T `test_mvp_product.py`交互用例；M `test_advanced_context_runtime.py`保留上下文失败路径 |
| 5 | `/cost`，基础59 | runtime→ContextManager；费用/token查询 | T `test_mvp_product.py`；M `test_advanced_context_runtime.py::test_source_context_cost_status_queries_show_current_process_scope_and_do_not_append_messages` |
| 6 | `/lang`，基础61 | runtime设置语言、写用户配置并刷新broker | — `/lang`直接执行断言待70；`test_b02_onboarding_entry.py`仅证明引导语言保存，不代替此命令 |
| 7 | `/help`，基础71 | **缺实际slash路由**；`--help`资源读取是另一入口 | — 70补实际help消费，欢迎页包含字符串不算行为 |
| 8 | `/exit`，基础76 | runtime普通/blocked输入循环精确匹配后break，finally收尾 | T `test_n1_runtime_tty.py`、`test_b07_platform_entry.py`及多条普通入口测试；带参数形状另核 |
| 9 | `/quit`，基础77；I1921含keep-background | 无参同exit；**`/quit --keep-background`缺实际路由** | — 无参别名/显式保留后台直接断言待70，不能把已有manager.detach当slash已接 |
| 10 | `/skills`，I1930 | runtime SkillControls列表/面板、单项和批量开关 | T `test_n1_runtime_tty.py`、`test_mvp_product.py`；各批量子命令证据仍按所属技能模块复用 |
| 11 | `/context`，I1968 | runtime→ContextManager上下文组成/预算 | T `test_mvp_product.py`；M `test_advanced_context_runtime.py`查询不加user |
| 12 | `/context-window`，I2251 | runtime验证参数→ContextManager；K/M窗口设置/锁定 | T `test_n1_runtime_tty.py`无效输入、`test_mvp_product.py`设置；M `test_advanced_context_runtime.py` |
| 13 | `/tasks`，I2042 | runtime task_manager.running()报告 | — 普通slash直接断言待70；`test_n40_agent_tasks.py`仅任务模块证据。来源不假称列出全部Shell |
| 14 | `/mcp`，I2047 | runtime→mcp_manager.command，按读/写暂停策略 | M `test_n53_mcp_caps.py`；普通回环已交前批证据，70应绑定具体回执，不把M当TTY全部验证 |
| 15 | `/diff`，I2078 | runtime→tools.git.gitDiff真实工作区 | T `test_b02_checkpoint_entry.py::test_rewind_code_and_restore_preserve_real_git_history` |
| 16 | `/doctor`，I2086 | **缺实际路由及汇总实现** | — 70组合既有账户/依赖/平台能力；不增加未授权外网探测或把Windows未支持写成可用 |
| 17 | `/memory`，I2098 | runtime→memoryCommand；有效删除先暂停 | T `test_n1_runtime_tty.py`；M `test_n4_memory_audit.py::test_tty_memory_query_and_valid_delete_share_native_store` |
| 18 | `/permissions`，I2118/I2410 | runtime→permissions.command，查询与有效编辑区分 | T `test_mvp_product.py`、`test_n1_runtime_tty.py`；M `test_n1_permissions_runtime.py`。冻结早查询分支遮蔽后编辑分支是已登记来源差异，不能暗改既定门禁 |
| 19 | `/session`，I2123 | runtime当前ID/标题/cwd/保存版本/状态报告 | T `test_b05_sessions.py`真实普通入口保存/切换 |
| 20 | `/audit`，I2135 | `7cf5921b`尚无路由；**root在途**runtime→commands.audit.auditCommand | 在途 `test_b07_audit_command.py`纯六类报告测试；57工具审计M `test_b07_tool_audit.py`。普通入口接线/脱敏/不暂停仍由57收口，不提前算70已过 |
| 21 | `/resume`，I2159 | runtime历史列表/指定ID，保护活owner/其它cwd/未决后台后切会话 | T `test_b05_sessions.py::test_source_session_commands_switch_branch_and_continue_through_normal_entry`；blocked输入有专用恢复入口 |
| 22 | `/branch`，I2187 | runtime→Conversation.branch副本，不重复启动历史后台操作 | T `test_b05_sessions.py`普通分支后载入；历史副作用边界沿26/17既有证据 |
| 23 | `/rename`，I2193 | runtime→Conversation.rename | T `test_b05_sessions.py`保存标题/原会话重开 |
| 24 | `/rewind`，I2200 | runtime.rewind：用户节点截断；显式code关联本进程已确认快照 | T `test_b02_checkpoint_entry.py`真实Git/对话回退，不能与仅文件restore混作同一行为 |
| 25 | `/export`，I2228 | runtime会话Markdown导出并显示路径 | T `test_b05_sessions.py`；M同文件Unicode导出断言 |
| 26 | **`/Config`**，I2239 | runtime大写分支展示当前账户/模型/权限配置 | — slash直接断言待70；`test_b06_config.py`仅Config工具读写/坏文件保留。来源帮助小写`/config`与实际分支不一致，不能伪造小写别名 |
| 27 | `/effort`，I2242 | runtime→ContextManager保存并影响后续请求 | T `test_mvp_product.py`、`test_n1_runtime_tty.py`无效输入；M `test_advanced_context_runtime.py` |
| 28 | `/status`，I2269 | runtime→ContextManager＋scheduler状态＋长任务状态 | T `test_mvp_product.py`、`test_b04_goal_entry.py`；查询不发新模型轮 |
| 29 | `/plugin`，I2274 | **scope excluded**，票20/插件能力按当前范围移出 | 不要求本批实现或假返回。保留原来源记录，不从52目录删除其来历 |
| 30 | `/hooks`，I2282 | runtime显示实际已载入Hook运行时清单 | T `test_b04_hooks_entry.py::test_ordinary_cli_loads_only_trusted_hooks_and_executes_rewritten_input`含未信任/禁用查询 |
| 31 | `/agents`，I2287 | **缺slash路由**；内置/自定义定义加载器已存在 | — 70复用当前实际agentCatalog/已载入定义，不能只打印硬编码目录冒充有效定义 |
| 32 | `/files`，I2292 | runtime显示本进程ctx.readFiles/readMeta | T `test_n1_runtime_tty.py`已读文件/TTY查询；重开不声称恢复此临时记录 |
| 33 | `/copy`，I2297 | runtime取末条非空assistant→既有剪贴板端口 | T `test_n1_runtime_tty.py`；Windows Unicode/不可用失败证据沿已有平台端口 |
| 34 | `/btw`，I2305 | runtime保存system备注，不立即请求模型 | T `test_b04_goal_entry.py`下一真实合成请求才带备注 |
| 35 | `/account`，I2312 | runtime账户面板/list/add/rm/switch，复用既有凭据事务 | T `test_b02_account_runtime.py::test_real_account_model_requests_and_unknown_save_preserves_scene` |
| 36 | `/accounts`，I2312，account别名 | command入口先归一`accounts→account`，共享同一动作 | — 别名直接行为断言待70；不能用account测试单独声称别名通过 |
| 37 | `/bypass`，I2344 | runtime→permissions.command显式模式切换 | M `test_n1_permissions_runtime.py::test_mode_commands_follow_source_toggle`；TTY接线共用permissions动作 |
| 38 | `/yolo`，I2344，bypass别名 | 同permissions命令路由，不改变deny/危险边界 | M同上，两别名均实际调用 |
| 39 | `/mode`，I2356 | runtime按查询/变更区分→permissions.command | T `test_b04_goal_entry.py`、`test_n1_runtime_tty.py`；M权限模式测试 |
| 40 | `/goal`，I2378 | runtime长任务切换/目标提交，queue_user保存展开prompt | T `test_b04_goal_entry.py`普通下一请求/持久指令检查 |
| 41 | `/task`，I2378，goal别名 | 同长任务分支；无目标时切换状态 | T `test_b04_goal_entry.py`无参关闭；带目标子形状由70核现有证据 |
| 42 | `/coordinator`，I2400 | runtime合并的长任务模式入口 | T `test_b04_goal_entry.py`开启状态；不重建已缩减的独立协调引擎 |
| 43 | `/restore`，I2458 | runtime工作区检查点恢复，先保存回退前状态并journal确认 | T `test_b02_checkpoint_entry.py`；未知副作用保现场，不以恢复对话代替恢复文件 |
| 44 | `/recovery`，I1922 | runtime→RecoveryController.command；blocked路径专门可用 | T `test_b02_agent_background_entry.py`及已提交17普通CLI回执；M `test_n17_recovery.py`。fork材料不完整拒绝是明确保留边界 |
| 45 | `/simplify`，builtin | runtime.runBuiltinCommand→projected_input→实际模型轮 | T `test_n1_runtime_tty.py`；M `test_b04_builtin_commands.py`中英来源展开 |
| 46 | `/remember`，builtin | 同一builtin/projected_input；空参给用法，非直接记忆CRUD | M `test_b04_builtin_commands.py`中英；普通prompt消费路径共用，逐命令不额外声称已验 |
| 47 | `/review`，builtin | 同一builtin/projected_input | M `test_b04_builtin_commands.py`，注意与自定义代理initialPrompt同名并非同一路证据 |
| 48 | `/init`，builtin | 同一builtin/projected_input生成项目指令任务 | M `test_b04_builtin_commands.py`；不把该prompt已生成当模型实际完成文件写入 |
| 49 | `/batch`，builtin | 同一builtin展开批量提示，模型发真实Agent工具 | T `test_b04_goal_entry.py`真实父→两子→父合成请求/结果配对；M builtin来源 |
| 50 | `/skillify`，builtin | 同一builtin展开技能编写提示 | M `test_b04_builtin_commands.py`中英文；不声称命令自身直接安装技能 |
| 51 | `/theme`，App | runtime本会话主题切换＋broker样式刷新，不写成全局持久化 | — slash直接切换待70；`test_b02_tui.py`仅颜色/渲染等模块来源证据 |
| 52 | `/loop`，App | runtime→scheduler.start_loop/stop_loop；timer排队，退出清理 | T `test_b03_loop_entry.py::test_loop_ordinary_entry_stops_future_requests`真实输入owner＋合成模型 |

## 后续派发界面

1. 70真缺产品动作：help、doctor、agents；quit的keep-background子形状。audit是57在途动作，等待固定提交/独审，不能重造同名模块。
2. 70入口形状：未知合法命令已有错误码2；当前凡以`/`开头均送command，冻结commands.ts的名称谓词拒绝含`/`或`.`的路径形式，应确认`/tmp/a.py`等不被误报命令。确认大小写、六builtin/技能解析优先级及query不暂停，修改动作保持pause→settled。
3. 首参操作员不混入52条slash：`trust`已早路由；**`Schedule`**已按59普通入口明确Windows拒绝；**`Skill add`**仍待70复用36安装端口。首字母大小写来自冻结index.ts，不从help猜别名。
4. 本表不是flags表。此前已报普通缺verbose/debug/api-key/provider/obs/progress-advice/no-progress-advice/eval；42已接reflect两开关。57负责obs实际消费者，71负责eval及独立关闭通道；不因接受参数就宣称隔离。帮助随最终真实能力同步。
5. 可分离的纯模块只有目录/解析/调度谓词等；runtime仍是动作唯一owner，57/70不要各自新建第二套账户、权限或持久化层。56 Deck、60/61沙箱不由本批普通命令清单代验；77/78人工出口不自动启动。

核查方法仅为只读冻结zip、当前源码分支、测试文本和既有范围记录；没有新增实现、测试运行或通过结论。所有后续证据仍需绑定最终产品SHA，不能直接把本表中T/M标签转换为票完成状态。
