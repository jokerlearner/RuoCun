# N24-r1 仓外纯安装独审：字节绑定未通过

本候选不作最终通过。固定产品提交 `5048b4d26066aa062e12fc6d03655ba33e2cc95f`，wheel SHA256 `827ac349c96b2f364b6e3db8a8830b376fd8c7b2ba7690d249fc0b81e695d1a7`。

独立创建仓外 `C:/Users/PC/AppData/Local/Temp/ruocun-n24-r1-pure`，只离线安装锁内两项运行依赖及同 wheel，没有 pytest、开发支撑或源码路径注入。所有进程经白名单与合成 HOME/配置/TEMP 启动，无真实或付费模型请求。

| raw label | 实际回执 |
| --- | --- |
| n24-review-pure-venv-r1 / deps-r1 / install-r1 | exit 0；依赖按 require-hashes 离线安装，同 wheel 安装 |
| n24-review-pure-original-r1 | exit 2；仓外 cwd 下相对脚本路径不存在，属于独审命令笔误，产品未执行 |
| n24-review-pure-original-r1b | 改绝对脚本路径后 exit 0；原七工具/审批/保存重开与原 TTY 断言通过，version/help 通过 |
| n24-review-pure-owner-r1 | exit 0；默认同包 `-m ruocun` helper/runner，真实 owner 强杀后同 run 接管与取消收据/Job 止写通过 |
| n24-review-pure-pipcheck-r1 | exit 0，依赖完整 |
| n24-review-pure-binding-r1 | exit 1；冻结源码与包字节不一致，不能宣布最终通过 |

以上敏感值扫描均为 false。原 TTY 结束后非主线程为空，实际受控 SQLite 3.54.1，DLL SHA256 `4b59d3cded9dc1608544160f3b4b10ac974c6ac0d6ffc23064e5f4c8dbd05aea`。实际安装 distributions 只有 pip、setuptools、ruocun、prompt_toolkit、wcwidth。

## 发现与处置

[pure-binding.py](pure-binding.py) 从固定 Git archive 取得源码，逐成员核同 wheel 和仓外安装。首个失败是 `ruocun/session/conversation.py`：冻结 blob 18232 字节、0 个 CRLF，wheel/根工作文件/安装文件均 18582 字节、350 个 CRLF。确认是整份 LF→CRLF 转换：没有据此声称存在逻辑差异。但项目 `/src/** eol=lf` 契约要求严格相同，因此保持失败，未放宽 binder。

主协调已决定统一实际工作文件字节，另建 r2。r1 wheel、纯环境、成功运行回执及失败绑定回执全部保留，不覆盖、不将 r1 功能通过偷换为完整交付通过。

## 默认安装角色边界

owner 脚本 `--installed` 模式从原测试 AST 提取 `_CODE` 字符串，不导入 pytest；删除 source path 与 source role override，只使用 manager 默认同包 `python -I -X utf8 -m ruocun`。SQLite ZIP 取实际安装资源。真实 DB owner PID/creation 与 retained HANDLE 再次核验，本次 launcher 确是 shim；runner 经 owner 退出仍活着，新 owner 接管保持原 RunRef/runner/start.claim/一次启动计数/真实 ack，最后真实 canceled receipt 与孙进程停写、runner 退出均通过。

用户 Windows Terminal、IME、缩放与体验仍未验收。15 等待 r2 固定包最终出口。
