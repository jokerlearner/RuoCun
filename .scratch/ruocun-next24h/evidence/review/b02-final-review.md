# 批次02固定包独审收口

固定产品 `5be452c14d45bbcf7437924ca8449a79d481d84a`，唯一 wheel `dist/b02-r1/ruocun-0.1.0.dev0-py311-none-win_amd64.whl` SHA256 `834e9fb2932aaebae5d01363a1f1b8ca158b9f1be0b3b8616ba1a3bbb616ea39`。本记录仅汇总独审实际结果；主协调的唯一里程碑全量与sdist/direct绑定另据其真实回执记录。

## 17恢复

按固定产品已收 `10abeb3`/`0d45a9e`、`d064e59`、`99cad2c` 与普通CLI回执 `a8306fe` 核源码。独立 `b02-review-n17-risk` **3 passed in15.12s**，只跑真实SQLite恢复决定/history原子、rollback/同ID幂等/不重放与附件/continue注入边界；真实runner丢失后的人工决定不造receipt；已COMMIT但回执不明确原样保留、重开对账一次。未重25项。

人工决定保留resolved_by_user、用户证据与旧unknown状态来源，不制造runner客观终态收据。manager发布与决定互斥，人工处置后不再poll/kill旧执行。已知终态坏材料仍保留终态并登记RecoveryMaterial，源码分支与B既有真实回执复用；query不输出capability/环境/代理恢复原材料，普通blocked入口仅开放明确恢复处理。

普通CLI未知Write→query/resolve/query的三进程、零模型、原文件不变回执复用B实际普通入口记录，未再跑该组合。当前普通agent继续的真实38/39/41 dispatcher未装配，产品明确拒绝；注入端口的一次许可测试不等同完整继续。**17保持claimed，不能写整票resolved。**

## 68与组合入口只读审查

按ADR0015只读 `3a35ef3`/`5be452c`，复用A的来源、同owner产品seam及静态资源逐帧机器绑定回执，未另跑普通组。欢迎/图形/标题/业务输出同一队列和run_in_terminal，Reports唯一reader，串行查询有界且关闭唤醒待查询，帧写前核epoch与generation、单帧背压，未知几何/非TTY/浅色/窄屏降级，shared不清scrollback。主题/缩放/关闭收回动画与在途写，静态资源6帧/10步及来源SHA明确。

组合根只传实际model/cwd/version/branch等状态，observer后台状态只更新展示，不篡改任务结果。当前源码审查无阻断。**实际WT图形显示、缩放残留/IME、77整体体验继续pending**；没有为暂停前新增用户操作或新功能。

## 仓外纯安装：本次实际运行

全新 `C:/Users/PC/AppData/Local/Temp/ruocun-b02-r1-pure`，运行依赖从`.cache/b02-runtime-wheels`按runtime锁 `--require-hashes`离线安装，随后安装上述唯一wheel。未安装pytest或开发支撑，未注入源码路径。各label的command/stdout/stderr在同名raw目录，全部exit0/scan false：

- `b02-review-pure-venv-r1`、`deps-r1`、`install-r1`：新环境、六项运行依赖与同包安装。
- `b02-review-pure-binding-r1`：[绑定脚本](b02-pure-binding.py)从固定Git archive逐成员核**213个产品文件**，source/wheel/实际安装集合及字节全等；三份原测试fixture与runtime锁也核冻结blob及实际SHA。
- `b02-review-pure-original-r1`：原七工具/审批/正常保存重开、原受控TTY断言、help/version实际通过。执行的[验收脚本副本](b02-outside_confirmation.py)含可选锁闭包核验；实际distributions仅pip、setuptools、ruocun及prompt_toolkit/wcwidth/rich/markdown-it-py/mdurl/Pygments。线程清理后非主线程为空。
- `b02-review-pure-owner-r1`：原owner脚本`--installed`，manager默认真实同包`-m ruocun` helper/runner。保留HANDLE按真实DB owner PID/creation强杀，runner继续，新owner同run接管，RunRef/runner/start.claim/一次执行计数与原ack不变；最后真实cancel receipt、Job孙进程止写、runner退出通过。本次launcher确为shim，没有错杀转发器假验owner退出。
- `b02-review-pure-pipcheck-r1`：No broken requirements found。

实际受控SQLite3.54.1，DLL SHA256 `4b59d3cded9dc1608544160f3b4b10ac974c6ac0d6ffc23064e5f4c8dbd05aea`，门禁met。开发与验收均合成HOME/配置/会话、白名单和回环服务，无真实或付费模型请求，无真实用户凭据读取。所有已启动验收进程已正常收口，原状态保留可追溯。

当前构建所需独审出口通过。69未启动；后续功能与未验实机项保留。按用户最新要求完成本次构建记录后暂停。
