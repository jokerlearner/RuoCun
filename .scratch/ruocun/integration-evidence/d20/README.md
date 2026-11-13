# D20 PSEC 独立合并复核

日期：2026-11-05；分支 `merge/d20-psec`；独立 worktree `.worktrees/m20`。证据唯一规范位置为 `.scratch/ruocun/integration-evidence/d20/`。只复核 D20 技术调查，不修改公共 Status、地图、规格、模块对应表或验收矩阵。

**可收录为“调查已回答，但完整 backend 仍不满足”的技术实验。** 原候选及本轮均不能称为完整沙箱、产品通过或最终后端选型。普通用户 Python 可以窄绑定 PSEC 1.1，实际运行宿主 Python/Git/Windows PowerShell 并控制所测文件和网络边界；但 outside RO 仍允许 WRITE_DAC 和真实 DACL 元数据变更，是安全目标失败，不能归作环境失败。

## 合并与来源

开始时 `m20` clean，HEAD 与正式 `integration/ruocun-migration` 均为 `400112fc6341b84f17f22ae57b14660402042690`；确认正式 ref 与工作树无差异后，quiet no-ff 合并候选 `fc74e893ac8c8f699f6d84364ce040ae83d967d8`，得到 `9e5d326078fa85c217832bb2a78be65b3f42d3ce`，无冲突。相对起点仅引入 PSEC 目录的 75 个原资产，未回退公共记录。

复核证据先提交 `1182c439301bce363b8c4aa94c6e043e84ac1e72` 后，按协调 quiet no-ff 同步正式集成 `3f8aabc4db36125b7012d47eb5aaa78a8534d7c2`，得到 `0ec5def6946a9db760b7290003f8c50b8c5ceabb`。该增量只收录 D08/D09 研究、ADR-0005 与状态/规格澄清；已阅读相关决定，并独立核对实验/PSEC来源线索/D20票/本复核路径的上游差异为零，原75资产及新ZIP hash仍一致，未重跑无关实验。

已读 AGENTS/CONTEXT、ADR-0001/0002/0004、D20 票、`research/psec-lead/`、实验 README、Python 绑定/worker/测试/网络/ACL、原历史 raw 和归档，以及 D17 不等价边界。PSEC 与 D17 AppContainer 路线结果分开，未重跑 D17。

固定 Microsoft MXC `f4aa3fd59306d140ccf7448e914306fc6cdb74d0`，MIT 许可保留。schema、参考 Rust 源码及原始下载 hash 均逐一复核；另独立读取只读缓存 `secenv.rs`，SHA-256 为 `2bc998c58eb50c6f4a2913197ac3d5b7245a78c34e1e9ebe52a21908b4eacb09`，原字节收在本轮 ZIP 的 `source/secenv.rs`。核对了 PSEC 标识、v1.1 inline uint16、字段/vtable 槽位、Create/Query/Version/Close ABI 和 `35 | 0x20000` 启动属性。运行核心为 Python stdlib ctypes；未运行官方 SDK、Rust/Node 代理、遥测或额外服务。

[before.json](r1/before.json) 校验原 manifest 的 74 项及 manifest 自身，共 75 资产，所有历史 run 的 raw/zip/代码成员 hash 和固定来源一致；[after.json](r1/after.json) 确认本轮后 75 项全部未变。原红绿轮、首个完整 `final` 的 6 failed/2 passed/1 xfailed/3 errors、后续 repair/final2 及入口失败完整保留，没有重写旧断言或旧 raw。

## 本轮执行

只执行一次原始最小组：**11 passed、1 xfailed in 27.93s，pytest exit=0**。该 pytest 子进程墙钟约28.27秒。原始 stdout/stderr 分别以二进制保存于 [pytest.stdout](r1/pytest.stdout)、[pytest.stderr](r1/pytest.stderr)，exact 命令、包/OS/ABI/二进制 SHA 和白名单环境键在 [run.json](r1/run.json)。测试文件和所有原候选源码字节均未改；没有关闭、绕过或降低 WRITE_DAC 原期望。

新建本 worktree 专属 `.v`，安装原固定 `requirements.lock`；短 pip cache `.c`、运行目录 `.r/r1` 均自有且保留。setup 的命令/stdout/stderr/exit 在 [setup](setup/)。所有 venv/pip/review/pytest/host/worker/后代/helper 进程从明确环境白名单启动，HOME/USERPROFILE/配置/临时目录均指向合成目录，Git 禁用系统/用户配置，PowerShell 不加载 profile。controller 非 elevated，Windows Professional 25H2 26200.9711，Python 3.11.9 x64。新进程只触达自有测试文件/ACL/Job/loopback；外网仅微软无认证首页、TCP443 与验证证书/hostname 的 TLS GET。未改系统策略、组件、账户、全局 ACL/防火墙或 loopback exemption。

完整候选快照、当前实际脚本、固定 ABI 来源、全部新运行合成文件和所有成功/失败回执见 [bytes.zip](r1/bytes.zip)，SHA-256：`6647184698b96d71f6c62bdc9b233c31a4b160a1ee2f1b0ff273afbc7e6b4492`。[逐成员清单](r1/archive-manifest.json) 与 ZIP 回读逐一核验；[observations.json](r1/observations.json) 只从已保存字节提取观测，没有再次运行任何原生/联网/ACL实验。

## 实际结论与边界

| 边界 | 本轮真实结果及限定 |
| --- | --- |
| 文件与三代 | 真实三代 PSEC SID hash 一致、非 elevated。workspace/tmp 的 read/create/overwrite/append/rename/delete 成功；outside 显式 RO 可读，五种数据变更拒绝，host 同脚本正对照成功。只证明明确授权目录，不能推定任意宿主路径读取。 |
| **WRITE_DAC 已知失败** | 三代 outside `WRITE_DAC` 打开及同 DACL 写回均成功；第0代实际给自有 `write_dac0.txt` 加随机 SID 的 FR ACE。worker 等待时 host 独立读回 ACE 确实存在，host 恢复原 DACL、读回完全一致，finally 再恢复；独立后审计3个样本均无随机 ACE。严格 xfail 正在记录目标失败，不能计为安全通过。未试图扩大真实账户权限或进一步数据写逃逸。 |
| junction/handle | 自有 workspace→outside junction 的 host 写成功、PSEC 三代拒绝；精确 junction 已移除，outside 保留。inheritable outside 写 handle 的 host 正对照成功，PSEC worker 得 `0xC0000008`；launcher 明确 `bInheritHandles=False`，只证明不继承策略，未证明 PSEC 撤销已授予 handle。 |
| 宿主工具 | 真正执行主机 Python、Git `--version`/自有 repo status、Windows PowerShell `-NoProfile -NonInteractive` 合成标记；不外推任意工具链、冻结解释器或发行安装环境。 |
| 外部网络 | net/no-net 均有各自 host 三代 TCP443/TLS 正对照。net 三代成功，no-net 三代 TCP/TLS 10013；TLS 未降级。DNS 由 controller 解析，容器内 DNS/代理/认证网络未验。 |
| loopback | 宿主 v4/v6 TCP/UDP 的 host 三代两组都成功；net 三代成功，no-net TCP10013/UDP有界超时。宿主 nonce 24/12，net 自身及真实父子连接共20条/no-net0条。自身、后代、宿主分别有实际回执，未用 host 自身失败冒充拒绝。 |
| Job/取消 | retained 三代真实 PID+创建时间+持有 handle 证实 signaled、身份一致、心跳停止，Job ActiveProcesses=0，再 close 环境。只证明 force 收口，非温和取消、产品管道/持久 runner 通过。 |
| owner crash | 合成 owner `os._exit(29)` 不执行 finally；supervisor retained 三代 handle 均 signaled/身份匹配/心跳停，精确 Job 查询2。**未调用 PSEC close，服务端状态无独立 query 契约，server teardown 仍未独立证实**，不从 Job 消失外推。 |
| fail closed | 缺失合成 EXE 实际 CreateProcessW 错误2、started=false、finally 关闭 Job/环境；无较弱回落。无效 network 和严格 `require_write_dac_deny=True` 在 fixture/workload 创建前明确报错，目标目录不存在。未知请求、缺失导出或不支持版本的拒绝另由源码核对；本机导出存在，不冒称实际测过缺失 DLL 的平台。 |

[post-audit.json](r1/post-audit.json) 是本轮退出后的独立只读审计：27 个记录 PID/创建时间身份全已退出（若 PID 重用，以创建时间区分）、8 个精确 Job 名不存在、3 个 DACL 样本随机 ACE 不在、原 DACL 恢复且读回一致、自有 junction 不在而目标保留。未按裸 PID 杀进程；没有删除其它 worktree、旧 venv、磁盘缓存或原始 fixture。此审计只覆盖记录样本及对象，不等于所有 PSEC 系统资源已清理。

原始及新增文件和 ZIP 解压成员在提交前经 [scan.ps1](scan.ps1) 静默匹配当前敏感环境值和常见 token 形状，只输出有无；[scan.json](scan.json) 两项均 false。它是本轮具体扫描结果，不是所有隐私模式的完备证明。

封存入口曾把扫描脚本成功路径未设置的 `$LASTEXITCODE` 当作失败，工具输出与修复依据见 [collection-failure-excerpt.md](collection-failure-excerpt.md)；该次无原字节文件，明确仅存输出摘录。修正只增加扫描成功时 `exit 0`，未重跑业务实验。

后续 D10/D12/产品60/61/78 仍需解决 WRITE_DAC 完整权限元数据契约，并验证最低 OS/edition/导出缺失、任意路径与工具链、owner/write-owner、已授权 handle、其它 reparse/竞争、细粒度网络/DNS/代理/跨环境、产品 I/O/温和取消/后台重连以及 owner crash 服务端所有权。人工终端体验按 ADR-0004 留在最终整体验收。
