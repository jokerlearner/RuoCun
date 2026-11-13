# N24 r1 独立只读逐成员检查：严格字节出口未通过

固定源码`5048b4d26066aa062e12fc6d03655ba33e2cc95f`，r1 wheel SHA256 `827ac349c96b2f364b6e3db8a8830b376fd8c7b2ba7690d249fc0b81e695d1a7`。本目录只读检查Git归档、主仓工作树src、sdist、从sdist重建wheel、direct wheel、根venv实际installed的168个包成员；不执行产品测试、安装、运行角色、WT或模型，不覆盖主协调integration/bind.py或产物。

## 实际差异

严格六层逐字节比较在`ruocun/session/conversation.py`真实失败，回执`n24-r1-byte-review`保留。完整分类复核确认只有该1个成员不同：

| 层 | 字节数 | SHA256 |
| --- | ---: | --- |
| 固定Git归档 | 18232 | `91af8b1d6b3dde18144c0ace2421b6b4f494f82a63194a4ffd92cc9a7793b787` |
| 主仓工作树src、sdist、wheel、direct wheel、根实际installed各层 | 18582 | `425fd20efb3c94e6b1f4b7b2daf8c481dbc9e8b1688838becf80b3ef07c246fc` |

已实际逐字节断言：`actual == archived.replace(b'\n', b'\r\n')`，且逆转换精确返回归档；准确350个CRLF，没有其它字节差异。固定提交的`.gitattributes`及当前`git check-attr`均规定`/src/ruocun/** text eol=lf`。本检查未修主仓字节或允许binder略过该规定；主协调选择统一已证明的纯换行差异后冻结r2重建。

剩余167个成员六层逐字节相同。全部168个成员在工作树、sdist、重建wheel、direct wheel、实际installed五层的集合与字节一致，两个wheel整包SHA一致。`result.json`列出每个成员归档及实际包摘要、唯一差异每层SHA、完整产物摘要与依赖。`all_six_layers_raw_bytes_equal`明确为false。分类命令exit0只表示完整清单已生成，不能当作r1严格出口通过。

## 资源与打包元数据

新增`tools/resources/exec-shell-poll.json`和`exec-shell-kill.json`在所有包层存在且字节一致。独立读取原冻结source.zip核TS文件SHA、MIT声明及完整原双语description：poll中文485/英文1171字符，kill中文298/英文837字符；各字段4条显式替换能精确重建随包说明，原id参数元数据保留。该检查未导入或运行工具handler。

wheel Windows x64/CPython3.11标签、版本、MIT/NOTICE、sdist成员无tests/.scratch/.worktrees、pyproject/installed/METADATA依赖一致已核；运行依赖仍为prompt_toolkit3.0.52与wcwidth0.9.4。hatch_build.py、LICENSE、NOTICE的既有纯LF→CRLF打包差异单列，不与受明确LF规则约束的src差异混淆。此处不重新执行SQLite运行库加载，功能与纯安装出口由主协调/独审另外记录。

所有读取命令经tools/run.py明确白名单、合成HOME/temp，raw扫描sensitive_match=false。没有改动产品源码、锁、参考快照、已有构建或实际安装目录；r2仍待新固定产物后另行检查。

## r2 一次严格复核

用户确认ADR-0015后，主协调按既有LF规则统一conversation.py物理字节，未改变固定Git归档的产品内容；随后固定源码`31208a95bef737c9e6bfbfb861695c84f2f90276`。本次只最小参数化原check.py的product/release/wheel-hash，使用`--bytes-only --strict`执行一次，不重新核来源描述、不跑MVP/TTY或任何产品测试、不安装、不操作用户窗口。

r2 wheel SHA256为`c12ead3d1174a2b6099431a1984a30cd50edaae13b7d1dfb013650d9a9b6baa9`，direct wheel整包相同。`n24-r2-strict-byte-review`退出0、stderr为空、扫描无敏感匹配：168个成员在固定Git归档、root src、sdist、wheel、direct wheel、root实际installed六层的集合及原始字节全部一致，source行尾例外0。完整摘要见`result-n24-r2.json`。

`r1-r2-difference.json`进一步复用两轮已生成摘要：168个固定Git源码成员哈希完全相同；实际交付成员只有conversation.py由CRLF恢复LF，其余167个成员不变。r1原始严格失败证据和result.json未覆盖，r2严格成功不倒填r1通过。新增资源来源复核沿用r1已有结果，本次`new_resource_provenance_verified=0`明确表示按授权跳过重复核查。
