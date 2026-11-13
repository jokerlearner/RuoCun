# N1 普通入口组合候选

临时唯一归属按root派发：agent/runtime.py、必要help资源、原test_mvp_product.py及一个受控TTY接线fixture。本候选已合审过领域基线c72099f52073c9692b74d99c726b925e26477c23，不改loop、Conversation、权限、Skills控制、scheduler/broker、shared types或公共记录。09/11/34/19仍由root统一状态验收；本候选不是这些票的最终固定产物出口。

## 实际消费与流程

- PermissionRuntime消费完整B的真实默认AST通道，没有另造分类器/解析器；run_turn同Task执行authorize→intent→dispatch，effective getMode与apiToolsForMode每次请求/调用实时使用。Plan API及写/exec/MCP执行硬门沿已审loop。Conversation新intent使用permissions-v1/gate-approved，不把自动规则放行记作text-confirmed。
- 原生ToolSearch、deferred EnterPlanMode/ExitPlanMode、ListDir已注册，ctx只绑定既有setMode/askChoice/externals/searchTools。askChoice仅真正interactive下注入，沿冻结index.ts:865/1118保留无人值守的既有降级；不把pipe预塞y当真人批准。
- 所有轮次消费既有SessionScheduler与Conversation队列端口。每run独有Event赋给ctx.signal；业务loop的generation/request token/Event过滤由已审run_turn负责，可信usage/完整tool pair仍保存。queue_user在ack事务中同时保存用户原命令及当时Skill正文；consume只用持久投影，不重新读磁盘。保存确认后才反馈输入已保存；拒收恢复broker草稿并停受影响轮，不重放原输入。
- `_run(args, *, broker_factory=None)` 是唯一必要测试注入，无CLI测试旗标。实际stdin TTY且无argvPrompt才启单InputBroker；受控factory同口径视为interactive。TTY审批/选择共用同一输入owner，返回原str或选择取消None；notice/delta经过同broker串行输出。关闭先触发scheduler.close失效Event、关闭broker唤醒审批/输入，再等可信run与输出Task收齐，最后关Conversation。只结束审批等待Future，不Task.cancel模型/工具轮次，不启动额外reader。
- pipe保持原顺序input→submit→finished，headless保持首批Todo规则与既有退出码。费用/粗估报告/上次API85%阈值/摘要失败保留/历史token恢复/图片重开/SIGINT路径沿原入口复用。查询命令不追加user、不暂停；历史/模式/技能操作先pause→settled。
- `/skills`消费既有SkillControls：TTY选择，pipe列表及明确单项/批量开关，保存后重启生效，不做运行中刷新。TTY专用/simplify优先SIMPLIFY_BODY，即使同名磁盘覆盖或core禁用。其它通用手动Skill按原命令入账、本体投影；自定义命令文件仍未支持。
- `/files`纯查询按readMeta插入序中属于readFiles的键优先，set中无meta项后部稳定列出；不造读取事实。CLI先extractCliPermissions，再argparse --yolo；trust操作不查模型账户/不连API，信任回执只写原生目录。权限与Skills来源诊断仍区分显式兼容与原生来源，兼容设置不被命令修改。

Windows ProgramData在复制父环境后、applyDotenv前固定canonical：父PROGRAMDATA优先，缺失C:/ProgramData。已核applyDotenv只补未设键，因此项目.env无法重定向最高managed层；不改权限策略内容或共享文件。实际产品父环境仍可指定原路径；工程fixture显式传合成父ProgramData。

## 来源与验证

来源为唯一冻结index.ts的普通命令/权限/信任/CLI装配及对应既有模块测试，消费的产品依赖哈希列在source-members.json。直接复用原CLI用例，不重跑已审392/162/38矩阵。

原test_mvp_product.py由预塞y改为显式bypassPermissions+deny；子进程始终绑定父进程实际加载的目标ruocun包根，开发时同src、最终安装时同site-packages，不借旧installed包假验新入口。仍验证原工具批/拒绝、静态Skills、项目指令、双进程保存重开、图片、费用/上下文/effort及摘要路径；同批增加ListDir实际调用定位main.py。非TTY顺序输入仍单列，不宣称Terminal体验。

新增只有一个必要受控ptk Input实际runtime/真实Conversation fixture：忙时FIFO与查询不pause、ack中Skill快照、审批独占保草稿、拒收不ack且恢复原文、/files、/skills Esc（空回车区别复用e40已过broker用例）、专用simplify优先级、plan工具可见性及执行硬门、政策tag、待审批关闭时完整pair与实际usage。fake仅位于模型请求边界；无真实网络模型/费用。没有新增压力/排列/故障框架。

最终定向结果：

- n1-runtime-managed-parent-final：两个既有入口fixture **2 passed in 14.45s**；合成父ProgramData与项目.env改址输入，确认父托管来源优先。
- n1-runtime-listdir-entry-final：原CLI同一用例追加ListDir后 **1 passed in 11.30s**；TTY未受影响，不重复运行。
- n1-runtime-delivery-mypy：最终runtime **1源文件成功**；n1-runtime-delivery-ruff相关3文件成功，随后最后CLI用例的纯新增ListDir调用由n1-runtime-entry-test-ruff再次确认。

候选自审复用同一TTY fixture捕获参数错误路径会无故暂停并丢弃已确认队列：/effort invalid及/context-window broken原先只因有参数即pause。先见实际Event被设置的red，再用既有parseContextWindow及effort合法枚举在操作前分类，错误反馈不暂停、不追加user。受影响同一TTY用例n1-runtime-readonly-errors-green **1 passed**，mypy1源通过；未扩用例或重复原CLI有效参数路径。后续仅import排版的Ruff结果另录。

原始失败如实保留：首CLI red为权限flags尚未接入；首TTY失败为fixture把Intent字段当ToolRecord直接字段，修为item.intent后通过，不能写成产品缺陷；mypy首次真实类型错为ChoicePrompt参数名不匹配，已按options契约修正，没有ignore。首次Ruff仅import排序。n1-runtime-cli-green/tty-02/tty-final虽功能断言通过，但当时managed路径隔离未证明，标partial/ENV，不作最终出口；后续合成managed版本被最终父环境＋项目.env确认取代，不覆盖旧raw。

本私有环境先前compiled mypy被Windows应用控制阻断的首ENV原raw继续保留于[旧回执](../n0-image-store/raw/n0-image-types/command.json)，不回填为通过。root本阶段明确批准复用已独审官方同版pure wheel，SHA256=1784648d6ec8c2b5465e3f26241b845a0b3cb4e56c993c64abe16989e7698999；先核hash复制私有cache，再按既有mypy-pure.lock仅换2.4.1 flavor。import显示.py，pip check成功，18版本依赖未重建；未挪DLL/改系统策略/共享venv。当前实际类型green是这条已审工具修复后的新证据。

所有命令经白名单启动器→tools/run.py，私有Python3.11及合成HOME/config/temp；回执scan=false，日志只有审查过的合成值。command-index.json保留分类与原stdout/stderr，source-pytest.py为入口原字节。没有重建wheel/安装新产品，最终build/install/全量/仓库外验证由root统一一次；真实Windows Terminal/resize及真实模型另列未验。

## 独审回修：只读查询保留飞行run状态

独审捕获context命令分支把active无条件赋为mutating，/status或非法effort之后会把飞行run标为空闲，外部SIGINT因而误走KeyboardInterrupt退出。复用同一个TTY fixture捕获实际注册的SIGINT handler并受控调用，先见真实错误分支red，再仅让mutating命令维护active；只读路径不改run状态。随后真实Event取消、旧delta隔离、新Event继续、FIFO及原审批/关闭路径一并完成，七次合成请求的可信prompt用量77一次累计，末尾配对仍唯一。受影响原用例1通过、mypy1源/Ruff两文件通过；没有新增case或排列，也未重复原CLI已过路径。该调用为受控handler验证，不冒充实际Windows Terminal键盘体验。

后续消费权限唯一作者已审11f0ac6（本树cherry-pick 384a38a），缺kind/rule的/permissions add仅反馈用法，不再被分为修改操作。原TTY同一段追加该输入，沿原队列/Event断言确认无暂停；受影响1项、mypy1源及Ruff通过，没有在runtime重写权限规则方言。/files查询先取readFiles/key tuple快照避免迭代共享容器，根因Read worker发布元信息的修复由root单点拥有，尚不在此处假称已消费。

## N1 r1 全量中的 TTY 启动失败

固定包第一次全量的唯一失败发生在原TTY用例等待首条启动输出。把该用例与`test_session_sqlite.py`放入同一pytest收集，再只选择TTY用例执行，即可复现同一`TimeoutError`。让等待循环读取已完成入口任务的结果后，同一复现直接显示`RuntimeGateError`。被收集的SQLite测试模块顶层已导入`sqlite3`，实际为3.45.1。入口因此无法证明本次请求的受控DLL已在首次导入前绑定，按门禁拒绝启动。

原TTY测试ID和场景断言保留。场景现由新鲜`-I -X utf8`子进程执行，以父测试已载入的`ruocun`包根作为导入路径。子进程使用显式环境白名单及合成HOME、ProgramData和临时目录，入口等待仍为8秒，任务提前结束时直接报告原异常。产品字节未改变。源码两文件组合执行原TTY及3个SQLite测试通过，固定包全量由主线复跑。

| 回执 | 结果 |
| --- | --- |
| [同进程收集复现](raw/n1-tty-sqlite-collect-red/command.json) | 1 failed, 3 deselected in 8.66s，首条启动输出超时 |
| [读取实际任务错误](raw/n1-tty-sqlite-gate-red/command.json) | 1 failed, 3 deselected in 0.61s，受控SQLite门禁拒绝 |
| [新鲜子进程，两文件组合](raw/n1-tty-sqlite-isolated-green/command.json) | 4 passed in 3.82s |
| [定向 Ruff](raw/n1-tty-sqlite-isolated-ruff/command.json) | All checks passed |

四次命令的敏感值扫描均为`false`。
