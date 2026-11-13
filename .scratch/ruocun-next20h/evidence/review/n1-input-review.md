# N1 边界、输入 owner 与依赖独审

## 主循环安全边界与迟到展示事件

固定候选 `9532a16c86772533630b3d246f74b7e8edb6c492`，回修 `b1631ad197a68461ef83de51406ab9dd9a357b5d`。只复已有一个必要 Python 接线 fixture，不重复原 22 项／构建／全量。

on_boundary 与 accepts_delta 可选，旧调用兼容。沿冻结 loop.ts:433，预算／轮数／轮内压缩先于 boundary，边界先于请求组装；完整工具批配对、图片投影与保存完成后才进入下一模型轮。每请求独有 object token，线程只 call_soon_threadsafe 投递，业务 loop 实际消费时检查 token、Event 与可选 scheduler generation。可信 usage／完整结果仍从完成口登记，不把 UI 过滤当作费用或 journal 丢弃。

发现一个 P2 退休窗口：Python finally 在 except 分支全部结束后才执行，旧代码的 context-length 恢复分支会先 await save／compact，期间旧 token 仍可渲染迟到 delta。root 最小回修为 except 入口立即退休 token，finally 保留兜底。复同一原 fixture，增加已确认窗口的 context-length→compact 路径，作者明确 red→green；独立原受影响 fixture **1 passed in 0.18s**。初候选同 fixture 的普通返回／后续请求分支独立 1 passed in 0.20s 保留，未把初绿当作该异常窗口已通过。回执 `raw/n1-review-boundary-delta-01/02`，剩余阻断 0。

## 运行依赖

固定依赖提交 `5ba5951d9112b406b028c60d9436175e91144d4b`，采用 D06／D10 已选 `prompt_toolkit==3.0.52` 和 `wcwidth==0.9.4`，没有升级到未批准版本、加入 Rich 或扩完整 TUI。D10 明确这些固定版本与单输入 owner；依赖就绪不是终端产品或人工通过。

独立读取 root 的官方 PyPI 元数据核验脚本、下载／核验回执与锁，然后只读核对两份固定 wheel 的实际 SHA256、py3-none-any／Root-Is-Purelib=true、无 pyd／dll／so、Requires-Python 与 Requires-Dist。ptk 只依赖 wcwidth，后者无运行依赖，均兼容固定 CPython 3.11。两 hash 与运行锁、pyproject pin 及 root 官方核验记录相同，见 `raw/n1-review-runtime-wheels-01`。未重复下载或重建环境。

在独占的既有私有 venv，仅用 no-deps／no-index／require-hashes 从只读 wheelhouse 增补这两包；实际安装 3.0.52／0.9.4，pip check 成功，随后实际受控 ptk 输入链消费成功。原 18 开发包 pin／已核 mypy 两种发行 hash 未改；开发锁通过 -r 引入两个运行包。tools.lock 新显式输出参数可保留旧 03 证据；root 官方核验时使用了新目标路径。回执 `raw/n1-review-runtime-install-01`、`raw/n1-review-runtime-pipcheck-01`。

指出旧 tools/audit.py／阶段A bind.py 仍检查无 Requires-Dist 且使用历史目录；root 明确两者为历史入口，并将文档注明。新版 N1 binder 必须使用新证据目录并检查恰好上述两运行依赖。当前已安装 N0 r2 产品元数据仍无依赖，**未运行新版 test_package 去冒充新包验证**；最终 N1 wheel／仓库外纯安装仍待统一出口。

## InputBroker

固定初候选 `7f98df9ffb6001896395f74796706311fe2e0a13`。独立读取 D06 terminal_app.py 中单 Application、独立模态 Buffer 和 run_in_terminal 相关职责及现有三项必要断言。

唯一 ptk Application／Input，主草稿与审批回答用两个 Buffer；审批不混入提交队列，原字符串交权限层解释。Esc／CtrlC 模态优先拒绝，主草稿仍保留；粘贴不自动提交。restore_submission 把未接纳原文与已编辑草稿合并，保留相对光标。write 选择同一 app 上下文并串行 run_in_terminal；没有新增 reader／input 线程。close 等 app 与暂停回调结束，完成审批／输入等待，默认创建的 Input 由 broker 关闭、注入 Input 由调用方拥有；不 Task.cancel 模型。

原三项独立 **3 passed in 0.45s**，既有纯 Python mypy 对 broker **1 源文件通过**，见 `raw/n1-review-broker-source-01`／`raw/n1-review-broker-mypy-01`。没有发现模块阻断。

后续选择端口叶子 `e40b0b555241136a12b4cc79548f182b10dd9d3a` 仅 cherry-pick 为本树 `427fe46`，没有带入其父 Node48 类型候选。ask_selection 保留空 Enter=''、取消 None；ask_approval 包装取消为空串，保留 09 原字符串合同。只复原同一受影响审批 fixture **1 passed in 0.45s**，同一 broker mypy **1 源通过**，见 `raw/n1-review-selection-source-01`／`raw/n1-review-selection-mypy-01`。

本批已发现的 P2 关闭，边界／输入叶子／依赖选择剩余模块阻断 0，可供 root 消费。普通入口的 pause→settled、草稿失败回填、原生写回、generation／request token、关闭输出等组合行为仍需最终接线独审。受控 create_pipe_input 不代表实际重定向 stdin 的忙时支持；真实 pipe 保留顺序模式，真实 Windows Terminal／resize／IME／完整 TUI 仍 pending。

所有工程命令沿外层环境白名单启动器／tools.run、合成 HOME／config／TEMP，私有 venv 独占；命令 joined、scan_hit=false，模型 API 0。不新增故障矩阵、不构建新 wheel、不将本模块结论写成 11／34 整票通过。
