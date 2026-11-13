# N1 权限候选 A 独审

固定初候选 `6a8d7856a9eaf30c93ba8999bf43078c0adc56a6`（起点 19106d7），JSON 回修 `16f4a6541bf220df4a68b3b5ec3a8f9bacc93f2c`，私有 glob 回修 `c591c307581ee3a4dd85ec0426b1508bc3021fc6`。只合这些固定 ref 到独立树，不读取或消费作者在途 B parser／walker。初候选 18 产品文件的 SHA256 与 candidate-a.json 独立相等，记录于 `raw/n1-review-runtime-wheels-01`；该初始绑定不假称覆盖后续回修，后续由固定回修 diff 与最终源码指纹绑定。

## 范围与来源

独立读取冻结 rules／settings／engine／gate／trust／plan 等对应源码、候选与原来源测试。检查规则私有方言／deny>ask>allow、非对称 wrapper／环境剥离、敏感与危险判断、checkPermissions 收紧、审批 once／session／always、层级合并、原生品牌路径与坏文件保留、plan 工具描述与 allowedPrompts 不被转成授权。

没有发现来源外的默认放行：非 Bash async 沿原同步裁决；A 未注入 parseBash 时明确报未装配，未把简化／legacy 当完整生产 parser。classifier 只接受可选 callback 和合成 fake，root 本批不注入，不启动 24 或真实模型 API。API 列表隐藏与 plan 执行硬门是不同接缝，后者及最终参数的审批／handler 同一性仍由 root 普通入口候选验收。

trust 默认只选择原生 .ruocun/trusted.json；项目显式兼容源是否经过信任由 root 注入 projectConfigPresent 与统一 source loader 装配。settings／approval 的低层写 helper 接受显式文件路径，本身不自动发现旧 DAO；root 必须传原生写目标，不能把加载来源跟踪的兼容路径用作写回路径。此处是待查的组合合同，不把低层 helper 通过写成实际 CLI native-only 已通过。

按批准范围选择相关既有子集，复跑 rules 路径匹配、engine、gate 决策／批审批、settings、trust、approval、plan、坏文件保留及 AST 注入端口，独立 **113 passed in 0.46s**。没有重复作者 392 项全套，未构建／重建环境。回执 `raw/n1-review-permissions-a-source-01` 明列实际选择，不能把 113 写成全部来源 it 或完整 A 所有断言复跑。

## 发现与关闭

1. **P2：Python JSON 非标准常量会使源判损坏的权限文件生效。** 默认 json.loads 接纳 NaN／±Infinity，源 JSON.parse 拒绝整文。例如包含有效 defaultMode=bypassPermissions 与 bad:NaN 的文件，初候选仍启用模式；写 helper 也可能改写按 ADR13 应保留的坏文件。作者在 settings／trust／approval 及 identity／engine 直接 API 加 parse_constant 拒绝。读侧保留空配置／不可信／空审批集，写侧抛错保留字节；没有新增 schema 或宽松兜底。作者复用原 missing_and_bad／preserve fixture red→green，独立仅复这两项 **2 passed in 0.13s**，同一五个修改源文件 mypy **全部通过**，见 `raw/n1-review-permissions-json-01`／`raw/n1-review-permissions-json-mypy-01`。
2. **P2：私有 glob 的 '?' 被 Python 扩为 Unicode 码点。** 冻结 globToRegExp 的 RegExp 未带 u，按 UTF-16 单元匹配；初候选 Python [^/] 会令 Read(secret?.txt) 错误匹配 secret😀.txt，拓宽 allow。作者仅对私有 glob 的 pattern／匹配文本转 UTF-16 单元，不改工具 glob 方言或非 glob 的精确／前缀判断。作者在原路径参数 fixture 加该已知断言 red→green，本审只复该原受影响参数项 **1 passed in 0.06s**，rules 同一 mypy **1 源通过**，见 `raw/n1-review-permissions-utf16-01`／`raw/n1-review-permissions-utf16-mypy-01`。没有新增测试函数或边界矩阵。

两个 P2 均关闭，A 模块规格／工程规范剩余阻断 0，可供 root 消费 A 协议。完整 AST／walker B、共享 Node48 后续扩展、普通入口层级装配、最终参数、plan 运行硬门、可信持久交互和 09 整票仍未通过，不由本结论推定已完成。

全部 T-N 输入／路径为合成 fixture，危险命令只作为规则文本，分类器为本地 fake；没有执行真实 Shell 副作用、真实 HOME／凭据或模型 API。命令沿外层白名单启动器／tools.run，私有已验 venv，joined、scan_hit=false，未变更断言以自证当前输出。
