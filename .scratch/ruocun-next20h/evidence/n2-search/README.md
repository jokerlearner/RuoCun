# 19 浏览与搜索工具候选

基线已合 `96ec0bff8207f4d3b8700dc696163d68f5717062`。本切片仅新增 ListDir、files查询helper及19独有测试，修改既有Glob/Grep的源说明和输出计数；不写 paths/read/types/registry/runtime，不启动10/12。工具候选先独审，实际注册、普通模型入口及/files组合由root负责；当前不将19标resolved。

## 实际复用与API

- 既有 Glob 搜索流程与4条 file_search.test.ts 语义已完整迁移，无需另造搜索器。继续复用 globToRegExp/walkFiles 和原有忽略目录、Windows递归junction边界及正序扫描结果；仅补完整源中英文说明、外部拒绝文案。实际源导出名 fileSearchTool 与原 globFilesTool 兼容别名保留。
- 既有 Grep17条源断言已在MVP迁移，本次原样复用，不增加JS正则运行时。保留已批准Python标准re及明确的无效模式诊断；当前模式/上下文/分页/跨行/文件类型/only_matching行为不重写。补源UTF16显示长度、列号、片段上下文和输出截断计数，以及源已有双语输出/API说明。
- `listDirTool` 使用现有 approvedPath，默认根目录，仅列一层、目录后缀/、JS UTF16字典序、空目录与500项截断；缺失/非目录异常继续由既有执行器配对。沿源外部路径审批，不新增权限层。Python3.11 Windows junction的目录标记与Node Dirent保持一致，不递归扫描它。
- `filesReport(workspaceRoot:str, readFiles:Iterable[str])->str` 为纯文字查询，保留调用方顺序；相对路径、空态、50项及总数逐字沿冻结index.ts:2292–2296。root以readMeta插入序中属于readFiles的键优先，确有set中无meta项后部稳定列出，保留事实；本helper不创建读取记录/DB，不承诺跨进程完整read-map恢复。Windows跨盘相对化沿Node返回原绝对路径。

无需新ToolContext字段或路径回调。来源Read的文件访问回调及未来动态发现仍root/对应后继拥有，本票不提前实现35。

## 来源与验证

只读冻结 `dao-f17e189-7ac654a0dc06` 的 list_dir.ts/test、file_search.ts/test、grep_files.ts/test、index.ts及output.ts。来源字节见source-members.json。MVP已过来源与junction回修直接引用其M01/M04证据，不以全量重写代替复用。

三工具中文/英文完整字符串及17个实际Zod参数字段由 `extract_descriptors.py` 独立从冻结TS字面量/声明提取，提取时不import产品。fixture为tests/fixtures/n2-search-source-descriptors.json，包含来源SHA256；API对比只允许Grep已批准的Python语法说明差异。不是新产品资源文件或通用转换框架；没有声称此提取器可处理任意TS/Zod。

白名单外层启动器→tools/run.py，私有Python3.11、显式src入口及合成HOME/config/temp；所有scan=false，无模型/网络付费调用。原始缺模块、UTF16列号及说明/schema差异red均保留，随后green；首次完整说明比对仍发现multiline参数文案漏对齐，修正后通过。首次Ruff仅新测试import顺序失败，修后通过；没有为纯import排序再跑功能矩阵。

- ListDir6项直接沿原list_dir.test.ts。
- 新增必要适配3项：Grep中文/emoji源UTF16列号/上下文/行长；三工具源说明/API比对；files查询中文路径/空态/50项纯投影。
- 复用既有test_mvp_glob.py 12项（含原Glob4项及glob/walk支撑）与test_mvp_grep_files.py 17项。组合共 **38 passed in 0.34s**；相关4产品＋2测试Ruff通过。
- 本私有旧compiled mypy ENV不重探，类型交root/独审既有pure链执行，尚不写已过；最终wheel、实际安装、普通入口与全量由root统一出口。

普通入口工具定位闭环、/files忙时查询不暂停与固定产物由root后续组合验证，不因本模块38项推定整票/整个来源母族通过。真实模型及Windows Terminal/resize人工体验另列未验，本候选无相应通过声明。API字符串完整比对不改变既有MVP Python正则差异。

## 独审收口：snippet零上下文配额

独审确认MVP原有cap==0时丢before的文字差异；冻结TS before.slice(-0)实际保留before。按root沿源收口，仅移除条件分支，保留UTF16 slice本身；复用原only_matching必要fixture增加同一500单元匹配，先见实际缺before失败再green，受影响原用例1通过、两文件Ruff通过，不新增排列或重跑38矩阵。独审前一候选38项/mypy4源及原始Node双语说明/17字段比对已过，实际回执由独审保存；本目录新red/green保留在n2-grep-snippet-zero-*，source-members更新最终字节。入口WIP未夹入本修复提交。
