# 依赖工具自动出口适配：实现候选证据

日期：2026-11-10；负责人：`/root/workflow_tooling`；分支：`codex/sprint-tooling`。
起点为领取记录 `f06e866019b35b17fb16af0a7e0826d793945588`，全量验证基线为 `435f71f8f997b54d80b67b050d4bfd6f41281dd6`；交付前另合入只更新D22环境前提文档的集成tip `fa9bb86e846af39f8c9dfd0c66c56dae45027e35`，无产品代码变化。

本票为开发工程工具适配，不计入84张产品实现票。候选已实现、自动验证通过，等待未参与实现者独立复核；用户体验为not-required。77/78的实际自动出口仍为pending、证据none；没有创建其产品通过结果。

## 改动及依据

- 依据ADR-0006和本票批准条件，沿`read_graph(root=...)`、CLI的JSON/文本/Mermaid既有边界实施；测试使用磁盘上的合成Git仓库、票、矩阵和证据，调用公开reader/CLI，没有替换内部验证函数。
- 仅79→78、84→77明确声明的automatic边可消费出口；核对完整产品/复核/集成SHA祖先链、已提交原始字节与SHA256、矩阵稳定子案例全集及独立角色。普通/D依赖仍检查resolved；85额外强制77/78完整resolved与用户accepted；claimed不重派发。
- 缺失、错误、重复、过期、未集成、路径越界、Git不可用均阻塞；原因码追加在兼容的任务记录中。证据文件只读，不执行其中的数据或命令。
- 格式及发布顺序见[说明](../../../../docs/agents/automatic-exit-evidence.md)。实现只改依赖工具、测试、格式说明和本票专属证据，未编辑产品src、公共图/状态/矩阵或原始references。

## 红绿与回归

`commands.json`列出全部命令、退出码和原始日志hash，`raw/<label>/`保留经白名单包装器扫描的stdout/stderr和命令回执。

| 行为 | 红信号 | 对应绿信号 |
| --- | --- | --- |
| 在独立root读取并消费79的已集成78出口 | tooling-red01：缺少reader root入口 | tooling-green01 |
| 改写证据后不能放行 | tooling-red02 | tooling-green02 |
| 完整集成SHA须实际存在 | tooling-red03 | tooling-green03 |
| 矩阵failed不能被清单passed覆盖 | tooling-red04 | tooling-green04 |
| 实施者不能自作独立复核 | tooling-red05 | tooling-green05 |
| 85不接受resolved但人工pending | tooling-red06 | tooling-green06 |
| 独立review_commit必须有实际来源 | tooling-red07 | tooling-green07 |
| CLI三种模式支持独立root | tooling-red08 | tooling-green08 |
| 85缺少77/78图边仍不得绕过硬门禁 | tooling-red09 | tooling-green09 |
| 未跟踪产品输入令旧出口过期 | tooling-red10 | tooling-green10 |
| 重复JSON字段不得隐藏无效值 | tooling-red12 | tooling-green12 |

`tooling-red11`是新增无效case类型反例的先验运行，已被现有矩阵集合检查拒绝（退出0），未宣称为新增红绿。第一次扩展反例回归为32 passed、2个夹具空提交错误；后续只将合成提交允许为空，最终回归全部通过。补充复核身份用例时将其review_commit同步到真实复核提交，最终针对该夹具再验1 passed，避免被较早的提交检查遮住角色检查。

最终工具测试56项，包含两条允许边正例、全部状态、未知/未声明/错误边、缺文件/hash/提交/矩阵/复核、短SHA、未集成分支、复核文件不在所列提交、产品漂移、重复/深层JSON、普通和D依赖、claimed、85两种冒号及自动覆盖反例。

## 五项既有入口

| 入口 | 命令标签 | 结果与范围 |
| --- | --- | --- |
| pytest | tooling-final-pytest | 375 passed、3 deselected；319既有产品/工程测试加56工具测试；产品oracle/live/terminal/install按已有标记排除 |
| 统一验收 | tooling-offline | 4 passed：ENT-01.version/help/resource/unimplemented；驱动自身注明task03 implemented subset |
| Ruff | tooling-ruff-final | 配置范围通过；另tooling-ruff-script-pass显式核查原配置排除的issue_graph.py通过 |
| mypy | tooling-mypy | 配置的32个source文件通过；不把该结果扩称为scratch脚本或全部测试的类型检查 |
| build | tooling-build | wheel与sdist构建通过；工具脚本不进入产品打包范围 |

依赖由只读公开wheelhouse离线、`--require-hashes`安装。首次尝试editable安装因离线未安装editables而失败，保留`tooling-product-support`日志；改用普通wheel安装产品和验收support后成功，不增加依赖、不改产品代码。Ruff显式scratch检查的两次import布局失败及最终修正日志均保留。

## 真实图、环境和资源

`tooling-repo-frontier`实际查询84张票：5 resolved、2 claimed、77 blocked，frontier为空。77/78仍blocked、Automatic exit pending、Automatic evidence none、用户体验pending。两票及公共表未被本候选改写。

所有venv、依赖、测试、构建和验收均由现有`tools/run.py`启动，环境白名单、合成HOME/APPDATA/LOCALAPPDATA/TEMP，不继承父环境业务配置，不访问真实凭据。Git子进程另用固定白名单、合成HOME、禁用全局/系统配置及交互提示。`tooling-environment`记录实际Windows/Python和固定工具版本；`artifact-hashes.json`绑定脚本、测试、格式说明、lock、包装器及构建产物。

本次实现准备与执行约19:15–19:29（Asia/Shanghai）；首个正例19:16形成，送审时间在票Comments记录。未发生外部决策阻塞；准备失败和反例红信号保留，没有通过删失败材料修绿。所有本次启动命令已结束并回收；验收子进程commands_joined/streams_closed均true。合成工作区、venv、构建产物及公开依赖缓存保留供复验。没有付费模型、真实Windows Terminal操作或用户体验结果。
