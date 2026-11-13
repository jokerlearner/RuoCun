# N1 权限 B 与 34 控制模块独审

## B：真实 parser／walker

固定候选 `85b793db8195353d36e128f52434ad855d123f7c`，起点为已审 A `c591c307`。包含叶子 c562759→19f7394 在实现树的同字节 cherry-pick，以及 ast／parser／bash_ast 桥、rules／engine／Gate 的真实默认装配。只合固定 ref，不跟随作者在途 runtime 或其它 WIP。

独立读取固定来源 wrapper／bridge、叶子词法／语句／参数与引用／重定向／budget／UTF8 实现、安全 walker 的 scope／参数／替换／heredoc／算术／后置 argv 检查，以及逐函数映射与原断言。产品只有纯 Python，不调用 Node、WASM、系统 Shell、shlex 或新增解析库。

- 原空命令／超过 **10000 UTF-16 单元**的 wrapper 不可用与实际解析 abort 分开。长度门按 surrogatepass UTF16 计数，JS trim 使用明确字符集；没有用 Python len／默认 strip 偷换该门。
- 叶子游标按代码点，Node.startIndex／endIndex 及文字切片按 UTF8 字节表，引用换行 gap 保留。save／restore 同时保存字符／字节位置；正常错误尾部进入 ERROR 节点或解析失败，不靠丢弃尾部声明简单命令。
- **50ms／50000 节点**沿来源每 128 节点检查时钟；异常／超时／节点帽／Python 递归异常返回 None，wrapper 转 PARSE_ABORTED，bridge 转 too-complex。没有把资源中止变成 fallback 后放行，也没有提高进程递归上限。
- 未知节点和形状走 too-complex；命令替换、pipeline／分支／subshell 的 scope 拷贝、变量占位、quoted heredoc、算术叶子及危险内建／wrapper／jq／重定向检查沿来源。simple 结果仍先 checkSemantics 再给规则子命令；未见迁移额外拓宽 allow。
- evaluateWithAst 默认懒加载真实 parseBashForSecurity，decideAsync／Gate Bash 默认消费它；不再只靠 A 的注入 fake。显式测试注入仍保留。fallback 只沿来源不可用分支保留，未把整个解析器固定成 fallback。

仅复约定上层 **26**（25 个原 bash_ast pytest 项＋1 个原 async engine 项）与叶子 **8**，独立 **34 passed in 1.03s**；同一既有 pure Python mypy 检查权限目录 **15 源文件通过**。回执 `raw/n1-review-bash-b-source-01`／`raw/n1-review-bash-b-mypy-01`。未重复作者 162 项，更未创造归档不存在的 3449 golden 或宣称完整 Shell 语法等价性。作者的原四个真实类型错误及变量／Optional 回修保留为历史，不写成 ENV。

逐产品／冻结成员 hash 与 source-map 计数另见 `n1-b-controls-binding.json`。剩余 B 模块规格／工程阻断 0，可供 root 消费；实际执行仍为现有 PowerShell5.1，普通入口最终参数、权限硬门与 09 整票须后续集成验收，不能从此 parser 通过直接结题。

## 34：Skills 目录与禁用控制

固定 `dbeee6422723352172654af5fec6b58748b85d6a`，独立核对冻结 index.ts:779–831、toggle.test.ts 三项、App.test.tsx:837–887 两项及既有五项 startup 适配。

保留全部 core 行（含被同名 disk 覆盖标记）及 disk 目录，目录标签由原对象所属 source 提供。禁用按来源技能名称而非另造标识；core 被覆盖时始终显示被覆盖，开关不撤销覆盖顺序。显式兼容 source 只显示来源，不写参考／兼容文件；唯一写目标 userRoot/skills-disabled.json 为原生目标。

文字选择器默认第三方，数字／空 Enter 翻转可见行，t 切换 core 显示，a/A、b/B、i/I 批量开关及 None 取消；仅适配已批准文字功能，不替代完整 TUI 箭头／视觉。修改通过既有 Windows 私有原子发布；提交返回前不交换内存禁用集，发布未确认则 blocked，后续修改停止。现有坏 JSON／非字符串条目不能被开关覆盖，非 JSON 常量拒绝；startup 容错沿来源。已加载的上下文／工具池不动态刷新，明确重启生效。

原五项控制与原五项启动适配独立 **10 passed in 0.28s**，control／runtime 同一 mypy **2 源通过**；回执 `raw/n0-review-skills-controls-01`／`raw/n0-review-skills-controls-mypy-01`。剩余模块阻断 0，可供 root 接普通入口；没有据模块结果将 34 resolved 或解锁 35／36。

全部工程验证使用私有既有 venv、外层白名单启动器／tools.run、合成 HOME／config／TEMP，命令 joined、scan_hit=false。危险文本不作为 Shell 执行，没有真实模型／付费 API；未构建、未做最终 N1 wheel／安装、未扩故障矩阵。真实模型质量、Windows Terminal／resize 与人工体验仍 pending。
