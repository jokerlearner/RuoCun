# N24-r2 仓外纯安装独审

结论：本轮约定的严格包绑定、运行依赖与默认同包后台角色出口均通过。按 ADR-0015 只运行下列直接受影响项，没有重跑全量、MVP 或 TTY 矩阵，没有启动65。r1失败保持原记录。

固定产品提交 `31208a95bef737c9e6bfbfb861695c84f2f90276`，同 wheel `dist/n24-r2/ruocun-0.1.0.dev0-py311-none-win_amd64.whl` SHA256 `c12ead3d1174a2b6099431a1984a30cd50edaae13b7d1dfb013650d9a9b6baa9`。新建 `C:/Users/PC/AppData/Local/Temp/ruocun-n24-r2-pure`，保留 r1环境，不覆盖。依赖仍按锁离线安装，无开发包/pytest/source路径注入。

## 本次实际运行

| raw label | 实际结果 |
| --- | --- |
| n24-review-pure-venv-r2 / deps-r2 / install-r2 | 全部 exit 0；新环境、锁定依赖、同 wheel 安装 |
| n24-review-pure-binding-r2 | exit 0；冻结 Git archive、168 个 wheel 成员、实际安装逐成员严格同字节，同成员集合 |
| n24-review-pure-pipcheck-r2 | exit 0；No broken requirements found |
| n24-review-pure-owner-r2 | exit 0；默认同包 `-m ruocun` helper/runner 真实启动，DB owner 强杀、同 run 接管、真实取消收据/Job 孙进程止写及 runner 退出均通过 |

所有回执敏感扫描 false，经明确白名单、合成 HOME/配置/TEMP 启动，无真实/付费模型请求。owner闭环从数据库真实 ProcessIdentity PID/creation 和 retained HANDLE 取证，launcher本次仍是shim。原 ack 未覆盖，runner身份、start.claim和一次启动计数不变，接管 owner/control epoch递增；没有用取消请求代替停止收据。结束后 retained owner/runner均确认退出。

## 功能证据复用及差异证明

旧产品 `5048b4d26066aa062e12fc6d03655ba33e2cc95f`，旧 r1 wheel SHA256 `827ac349c96b2f364b6e3db8a8830b376fd8c7b2ba7690d249fc0b81e695d1a7`。本次 `pure-binding.py` 对该旧 wheel 的所有产品成员再次逐字节比较：仅 `ruocun/session/conversation.py` 的350个CRLF统一为LF，其余167个成员完全相同，没有包内行为改动。

因此沿用 [r1纯安装报告](pure-r1-review.md) 的 `n24-review-pure-original-r1b`：原七工具、审批、普通保存重开、原TTY、help/version、实际受控SQLite及线程清理。其两份fixture本次仍与新冻结提交相同（允许标准统一CRLF checkout），实际SHA256分别为：

- `tests/test_mvp_product.py`：`3a34fd218de1bbe4a750fa177b22d16441a399baa6181221e571327106f3b3dc`。
- `tests/test_n1_runtime_tty.py`：`dc0138c0ba5d728d4e95185cc14effc901df3901a9b2d21359537b6c1f4d8d82`。

来源managed shell fixture的loader修正为源码显式loader、安装真正模块入口；本次owner脚本使用的新fixture内容与 `31208a9` 相同，并在installed模式去掉fixture全部role override，以manager默认启动命令运行，不伪装源模式。该fixture实际SHA256 `2dda7c07cb28d377dd79317c5578b74bd50a6d25a47d7313b436b82a7c4af9fa`。其四个旧全量失败的定向复验由主协调另留回执，不在此冒称独审重跑。

r1严格字节出口失败未改成通过；本次r2严格出口通过作为新的替代结果。真实WT文本技术项见[独立只读记录](terminal-wt-review.md)，77整体体验保持pending。
