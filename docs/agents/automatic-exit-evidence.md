# 自动技术出口证据格式

本格式实现 ADR-0006 的已批准门禁。产品状态仍由 `.scratch/ruocun/acceptance-matrix.md` 维护；JSON 清单只是可核对的索引。实际 77/78 的出口与用户体验仍按其票据和真实证据记录。

当前覆盖范围以[ADR-0010](../adr/0010-selected-scope-and-lean-workflow.md)为准。WIN-06/07/10等母族仍需真实验证“不支持/无保证/终端反馈”的修订行为，不靠删族绕过覆盖。scope excluded与passed不同；依赖工具的scope过滤尚待[适配](../../.scratch/sprint-tooling/issues/02-scoped-frontier.md)，现有自动出口证据校验能力未被取消。

只有任务图明确声明的 `79 wheel → 78 wincaps`、`84 winintegrate → 77 wtaccept` 的 `dependency_exits.<key>=automatic` 可以消费此格式。未声明时保留整票 `resolved` 门禁；其它出口声明保持阻塞。85始终要求77、78两票均 `resolved` 且 `用户体验验收: accepted`，支持中英文冒号，不接受自动出口替代。`claimed` 票不进入可派发 frontier。

## 文件和字段

在出口票写入唯一的 `Automatic exit: passed`、`Automatic evidence: .scratch/ruocun/evidence/<name>/automatic.json`。字段缺失、重复、未知状态及证据不一致均阻塞；JSON重复键和未知schema版本也阻塞。路径使用仓库相对的正斜杠 ASCII 路径，文件位于 `.scratch/ruocun/`；禁止绝对路径、空段、`.`、`..` 和解析后越出仓库的链接。所有文件只读作数据，工具只调用固定的 Git 查询，不执行清单、证据、审查文件或其中的命令。

以下是格式占位示例，尖括号值必须以真实完整值替换后才可使用。它不构成任何产品通过证据。

```json
{
  "schema_version": 1,
  "ticket": ".scratch/ruocun/issues/78-wincaps.md",
  "product_commit": "<40位小写完整SHA>",
  "review_commit": "<40位小写完整SHA>",
  "integration_commit": "<40位小写完整SHA>",
  "implementer": "<实施负责人标识>",
  "matrix": {
    "path": ".scratch/ruocun/acceptance-matrix.md",
    "sha256": "<矩阵原始文件字节的64位小写SHA256>"
  },
  "cases": [
    {
      "id": "WIN-01.process",
      "evidence": {
        "path": ".scratch/ruocun/evidence/<name>/process.json",
        "sha256": "<该证据原始字节的64位小写SHA256>"
      }
    }
  ],
  "review": {
    "path": ".scratch/ruocun/evidence/<name>/review.json",
    "sha256": "<独立复核原始文件字节的64位小写SHA256>"
  }
}
```

`ticket` 必须为出口票本身。77使用WT案例族，78使用WIN案例族，实际清单必须覆盖任务图给该票登记的全部案例族；每个自动子案例使用稳定的 `母ID.子ID`，不得重复或为空。每份产品证据继续满足矩阵既有的环境、来源、产品路径、输入/预期/实际、退出和资源清理规则。工具校验文件和记录一致性，具体产品断言、真实Windows执行和覆盖完整性由独立复核负责。

## 矩阵中的逐项记录

在权威矩阵内保留原母行并增加以下固定列名的表，逐行列出该票**全部**可自动验证的产品子案例。人工项仍待验；不能省略失败或未运行的自动项。表中的 `passed` 表示该实际子案例已经验证，不是整族或用户体验通过。

| Automatic ticket | Case/subcase | Result | Product commit | Evidence | SHA-256 | Review |
| --- | --- | --- | --- | --- | --- | --- |
| .scratch/ruocun/issues/78-wincaps.md | WIN-01.process | passed | <产品完整SHA> | .scratch/ruocun/evidence/<name>/process.json | <证据SHA256> | .scratch/ruocun/evidence/<name>/review.json |

工具要求该票所有自动表行与清单案例集合完全一致，所有任务案例族有实际子案例且母ID仍存在；Result必须全为`passed`，产品SHA、文件路径、文件hash和复核指针逐项一致。同票重复行、缺行、多行或任一不一致均阻塞。原母行可继续汇总部分通过和人工待验；精确的自动子案例结果取自上述逐项记录。

## 独立复核文件

```json
{
  "schema_version": 1,
  "ticket": ".scratch/ruocun/issues/78-wincaps.md",
  "product_commit": "<产品完整SHA>",
  "implementer": "<实施负责人标识>",
  "reviewer": "<未参与该候选实施的复核负责人标识>",
  "status": "passed",
  "cases": ["WIN-01.process"]
}
```

复核的票、产品SHA、实施负责人及全部案例必须与清单一致。两个角色需为非空的可追溯标识，不得填none/unknown/pending，也不能仅变更大小写后冒充独立身份。工具不替代协调者对实际独立复核上下文的核实。

## 提交和过期规则

1. 提交待验证产品P；执行并保存真实的全部自动子案例证据。
2. 独立复核P及全部子案例，将复核文件、逐项矩阵和证据提交为R。R必须在P之后，不能用P本身充当复核提交。
3. 由协调者集成R得到I；快进时R和I可以相同。工具验证完整SHA及 `P → R → I → HEAD` 祖先链。
4. 在I之后发布清单和票的出口字段并提交。清单中的矩阵/复核/各证据必须与I和HEAD内的文件字节一致；复核还必须存在于R。票、清单、任务图也必须与HEAD一致。保留LF等原始字节，避免Git换行转换破坏hash。

`src/`、`tests/`、`tools/`、`pyproject.toml`、`requirements-dev.in`、`requirements-dev-win311.lock` 任一受版本控制的输入相对P变化，或出现未忽略的未跟踪产品输入，都会使该出口过期。矩阵任意行变化也会保守失效，须更新对应真实复核、集成和清单；不得删除其它记录来恢复通过。Git缺失、命令失败/超时、无效SHA、未集成分支、文件缺失或hash漂移均阻塞。

## 查询兼容

原文本、`--json`、`--mermaid`入口和既有输出字段保留。`read_graph(root=...)`与CLI的`--root`允许独立合成仓库验证。任务记录新增 `dependency_blockers`，其键与 `unresolved_dependencies` 中的路径相同，值为固定原因码，不输出原始证据内容或异常值。85所需的77/78图记录缺失时也阻塞，记为`missing:<key>`。
