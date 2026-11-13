# 09 候选 B：真实 Bash parser / security walker

叶子 parser 由线二独占迁移，来源提交 `c562759` 与仅变量/类型回修 `19f7394`，
本树 cherry-pick 为 `dafb162`、`3320fe9`。其 81 源函数、6 个同来源命令 raw Node 断言和
2 个 UTF-8/资源帽接缝的依据另见 `../n1-bash-parser/`。

本候选完成 `ast.ts` 的 24 个函数（见 manifest 逐函数映射），`parser.ts` 薄封装和
`bash_ast.ts` 桥接。未知节点、控制字符、变量/命令替换、scope 隔离、条件/循环、重定向、
quoted heredoc、算术叶子及 wrapper/内建命令的后置语义检查均沿来源处理。
Python 适配保留 JS UTF-16 长度门与 trim 字符集、Node UTF-8 字节偏移；fd 用浮点对应源 Number。

生产 `evaluateWithAst` / `decideAsync` 默认懒加载真实 `parseBashForSecurity`，Gate 默认也走
该路径。注入 parser 仅作为显式测试接缝。空/超过 10000 个 UTF-16 单元依来源回退；解析器
50ms/50000 节点帽或异常依来源转 `PARSE_ABORTED` → too-complex，不固定 fallback。

验证为本树源码导入，无真实模型/付费 API，无 Node oracle 调用或新增产品依赖：

- `n1-b-ast-red` / `n1-b-runtime-red`：桥接缺失和 async 生产默认尚未接入的原始红灯。
- `n1-b-ast-first-green`：26 passed / 66 deselected。冻结 bash_ast.test.ts 的 24 个有 kind
  断言输入 + 两个仅空条件分支输入合为 25 pytest 项，另有 engine.test.ts 原 5 条 async 断言合 1 项。
  没把来源两个无硬断言输入升级为新验收条件。
- `n1-b-source-integrated`：162 passed，覆盖上述与受影响 rules/engine/gate/seam、叶子 8 项。
- `n1-b-ruff-green`：Ruff 通过。`n1-b-mypy-integrated` 保留叶子原 4 个类型错误；
  类型回修后 `n1-b-mypy-green`：15 源文件通过。回修仅变量列表更名/显式 Optional，未重复运行 162 项。

本次没有重跑不受影响的 A 全 392 项，也没有创造冻结注释中提到但归档不存在的 3449 golden。
所有 B 产品字节、冻结源 hash、命令和原始输出绑定在 `candidate-b/manifest.json` 与 raw/。
普通入口装配、最终参数裁决/模式硬门、固定 wheel、整票出口与人工体验仍由集成阶段验收；
本模块通过不表示 09 resolved。
