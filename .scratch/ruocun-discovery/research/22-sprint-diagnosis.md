# D22 冲刺诊断：PSEC 组合 MandatoryPolicy 3→1

日期：2026-11-10。调查分支 `codex/sprint-d22`；独立 worktree `.worktrees/sprint-d22`；起点 `092b1cccc8ea85c05d27acfbd45d4fc23acfbf51`，开始时 Git clean。本文是新研究记录，不修改 D22 票、地图、状态、规格或验收矩阵。研究分支本地保留，由主协调收录报告，不整分支合并。

**判别结论：当前 A 仍失败，不能继续组合 Python、B/C 或解锁 60/61。** 已用原字节归档建立稳定的纯数据红回放，排除了“所有 CreateProcessAsUserW 都消耗该位”和探针显式写 policy 两个解释；问题定位在增加 PSEC 启动属性后、实际 worker 执行前的系统 token 派生边界。公开一手资料没有给出 Windows 内部清除 `0x2` 的确切实现原因，也没有保证该组合下 `1` 与请求的 `3` 等效。不能写成“按设计所以安全”，也不能写成已证实可逃逸或所有 Windows 后端不可能。

## 1. 契约、来源和本轮边界

已读根 AGENTS/CONTEXT、domain/issue-tracker、ADR-0005/0006、冲刺计划/实施进度、D10/17/20/22/D12、R-14/R-16、WIN-09、60/61，以及 D22 报告、全部 `.py/.ps1` 与既有独立静态复核。T0 沿主协调登记的 `2026-11-10 19:01:22 +08:00`，不把启动授权解释为取消具体探针停止条件。

- 冻结参考仍是 `dao-f17e189-7ac654a0dc06`。本轮直接读取 ZIP 中 `src/tools/sandbox.ts`：来源要求工作区/tmp 可写，其余写受限，显式 no-net；Windows 原版返回不支持。Windows 补齐、owner/DACL、后代及工具链等完整目标沿现规格，不从来源缺口缩减。
- D20 已实测同用户 owner 的 outside RO 对象可被修改 DACL；本轮没有重跑或否认该失败。D22 必须先满足 A，再判 B 该已知缺口。
- D22 固定一次组合已于历史 a1 触发停止；没有新建 PSEC、受限 token、私有 desktop/Job、真实目标进程或网络探针，没有安装/启用组件、改 ACL/服务/firewall、尝试新 flag 或变更宿主。
- 本轮仅启动短时标准库 Python 数据读取进程。其环境先清空，再写入固定白名单，HOME/配置/tmp 指向本目录新建 `synthetic-home`；不读真实模型、凭据或父环境秘密。
- 旧 `audit.py` 末尾会覆盖 `e/post.json`，没有运行。旧目录、原 a1 ZIP、旧 `post.json` 均只读；新资产位于独立的 [token-policy-replay](../experiments/token-policy-replay/)。

## 2. 先建立红信号，再进行原因判断

实际采用 `C:/Users/PC/.codex/skills/diagnosing-bugs/SKILL.md`：先 trace replay，再最小化，再列出四个可证伪假设交主协调，随后做静态/官方资料判别。本轮不具备获准的新真实系统复现实验，不能把纯数据回放冒充 OS 重跑；它准确锁定已捕获的症状，并保留后续修复应满足的字段判据。

在本 worktree 根执行：

```powershell
& .scratch/ruocun-discovery/experiments/token-policy-replay/safe.ps1 -Mode archive -OutputTag archive-r1
```

实际返回 `exit 1`，核心输出：

```json
{"requested_mandatory_policy":3,"actual_mandatory_policy":1,"removed_bits":2,"requested_policy_preserved":false}
```

第二次同一命令改独有 tag `archive-r2`，相同结果，单次约 0.5 秒；没有重跑真实组合。删去 SID、组、IL、Job、路径、退出等非症状字段后，仅保留 [minimal.json](../experiments/token-policy-replay/minimal.json) 的两个整数，以 `-Mode minimal -OutputTag minimal-r1` 回放仍 `exit 1`。两个值是这个最小比较的输入；归档 hash/成员路径用于来源校验，不参与“3 与 1 是否相等”的判据。

以 `-Mode detector -OutputTag detector-r1` 检查纯合成 `3→3` 可绿、`3→1` 可红，返回 `exit 0`。这不是安全验收绿色，也没有把历史失败改成期望失败测试。

证据分别为 [archive-r1](../experiments/token-policy-replay/evidence/archive-r1.stdout.json)、[archive-r2](../experiments/token-policy-replay/evidence/archive-r2.stdout.json)、[minimal-r1](../experiments/token-policy-replay/evidence/minimal-r1.stdout.json)、[detector-r1](../experiments/token-policy-replay/evidence/detector-r1.stdout.json)，各自并列保存 stderr/exit/白名单键名。

## 3. 原字节与对照事实

新 [inspect_capture.py](../experiments/token-policy-replay/inspect_capture.py) 只读取文件/ZIP，绝不导入归档中的 launcher；`safe.ps1 -Mode inspection -OutputTag inspection-r1` 返回 `exit 0`，[结构化结果](../experiments/token-policy-replay/evidence/inspection-r1.stdout.json) 证明：

- 旧 manifest 所载 34/34 资产长度和 SHA-256 一致；a1 ZIP CRC 完整；7/7 执行时源码与 a1 `source_sha256` 一致，原 raw hash 一致。
- a1 ZIP SHA-256：`687dc92b7f19a933bd7ca65d81521ce9e436a0f22f078485ecb199457def0c55`。
- 原 `e/post.json` SHA-256：`1eb80222ba883a26e246f29ba9cb8f382a819d278f4c24429569fb4ba388cc9f`。
- ordinary Python 的 host 挂起 token 与 worker 自查 token 全字段相等，验证了这一正对照 seam；组合 cmd 没有 worker 自查，不能外推成组合 Python 已验证。
- 归档 `probe.py` 的 AST 中所有 `set_token(...)` 调用的信息类只有 `6`（DefaultDacl），没有写 `27`（MandatoryPolicy）。`ntoken.py` 读取类 `27` 并以 DWORD 解码。

| 历史 a1 目标 | 观测 policy | IL | AppContainer | 退出 |
| --- | --- | --- | --- | --- |
| ordinary cmd | 3 | medium 8192 | false | 0 |
| ordinary Python | 3 | medium 8192 | false | 0，worker 回执 |
| restricted cmd | 3 | medium 8192 | false | 0 |
| restricted Python | 3 | medium 8192 | false | `0xC0000142`，无 worker |
| restricted + PSEC cmd | 1 | low 4096 | true | 0，仅 host token 观测 |

组合 token 的 User/Owner/restricting SIDs/privileges 保留；组差异由已有 post 审计精确为完整性标签替换。low IL 是当前进程限制收紧，不能与 `0x2` 清除一起笼统写成所有限制丢失。挂起 token 的观测发生在 `CreateProcessAsUserW` 成功之后、`ResumeThread` 和 worker 之前，受信 worker 或 Python 初始化不是这次 cmd policy 变化的原因。

## 4. 四个假设与判别

以下排序在官方查询前已发给主协调，没有先选一个原因再寻找证明。

| 排名/假设 | 可证伪预测 | 现有判别与剩余不确定性 |
| --- | --- | --- |
| 1. PSEC 派生 AppContainer token 的系统路径重建 policy | 若确属有意设计，官方应给出该派生/继承规则或源码中固定设置；若原输入 token 实际已为 1，则该解释不成立 | 原请求为 3、standalone 为 3、组合 suspended 为 1，支持将边界定位到 PSEC 系统路径。但已查官方公共 SDK/文档未给出内部清位语句；“按设计重置”仍是未证明假设，不能把相关性升格确切内部根因 |
| 2. 观测 ABI/信息类或句柄错读 | 若成立，官方结构/枚举应与探针不符，或普通 worker 与 host 查询不一致 | 官方类序号/结构匹配，普通 Python 两侧全字段相等；保留的是创建所得精确 process handle，再 OpenProcessToken。未发现支持此假设的证据；组合尚无第二实现的独立原始字节查询，故不作数学上的完全排除 |
| 3. launcher 自行写 policy 或覆盖 token | 若成立，执行时归档应存在写 policy 的调用或在观测前替换已创建进程 token | 归档 AST 只有 DefaultDacl 写入；实际 token 在 resume 前由 retained process handle 查询。未发现此路径；不能拿当前脚本代替归档代码，本轮已逐源码 hash 绑定 |
| 4. 所有 CreateProcessAsUserW 都会消费 NEW_PROCESS_MIN | standalone restricted cmd 也应从 3 变 1 | 被同一 a1 的 standalone restricted cmd=3 直接证伪；不能以“只对新进程有效所以自动消失”解释现结果 |

本轮没有用新 flag、不同 SID、改 IL、补写 policy、换 DLL/设备/桌面 ACL 或重复启动来区分这些假设，因为现有证据足以得出不能继续的门禁判断，而这些变更会超出一次即停边界。未作全盘服务/组件枚举：它不能判别这个 token policy 问题，也不能证明已有服务就有安全可交付后端。

## 5. 官方语义与等价判断

微软把 `0x1 NO_WRITE_UP` 定义为禁止向更高完整性对象写入；`0x2 NEW_PROCESS_MIN` 定义为使用该 token 创建的进程完整性取父进程与执行文件完整性较小者。`0x3` 同时包含二者。因此在**公开 token policy 的声明层面，1 与 3 是不同策略，不能当成同一个值或无意义记账位**。[TOKEN_MANDATORY_POLICY](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-token_mandatory_policy)。

官方 `TokenMandatoryPolicy` 在从 `TokenUser=1` 开始的枚举中为第 27 项，返回结构是一个 DWORD Policy；现有读取没有把它误当成 SID 或其它结构。[TOKEN_INFORMATION_CLASS](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ne-winnt-token_information_class)、[GetTokenInformation](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-gettokeninformation)。

MIC 独立于 DACL，先进行完整性检查。当前 low IL + NO_WRITE_UP 可以说明当前层仍有完整性限制；这不能自动替代 NEW_PROCESS_MIN 的进程创建规则、完整后代限制、低 IL 外部对象、允许根与 owner/DACL 元数据边界。[MIC](https://learn.microsoft.com/en-us/windows/win32/secauthz/mandatory-integrity-control)。本轮未测后代或 B，故既不能宣称实际逃逸，也不能宣称 PSEC 的额外限制在所有有关情形下补出了完全等价效果。

Microsoft MXC 固定 `f4aa3fd59306d140ccf7448e914306fc6cdb74d0` 的公开路径是 PSEC 环境附加到 `CreateProcessW`；其 [secenv.rs](https://github.com/microsoft/mxc/blob/f4aa3fd59306d140ccf7448e914306fc6cdb74d0/src/mxc-sdk/src/backends/process_container/common/secenv.rs) 与 [runner](https://github.com/microsoft/mxc/blob/f4aa3fd59306d140ccf7448e914306fc6cdb74d0/src/mxc-sdk/src/backends/process_container/common/base_container_runner.rs) 没有给出这个自定义 restricted primary token 组合的保留契约。已存 [PSEC 1.1 schema](../experiments/psec/source/ProcessSecurityEnvironment.fbs) 没有 TokenMandatoryPolicy 或自定义 primary token 字段。公共 SDK 封装并非 Windows 内部 token 生成源码，不能凭这里缺字段推导所有底层组合被禁止。本轮官方网页查询日为 2026-11-10；Learn 是当日动态文档，MXC/Sandboxie 证据按链接中的固定提交限定，不作为未来版本行为保证。

**可确定的是 policy 未原样保留、公开声明的规则不同、严格 A 不满足；尚不能确定的是 OS 内部为何特意清位，以及完整 PSEC 约束下是否在所有相关行为上等效。** 即使未来得到等效论证，也必须由主协调/用户明确处理既有 A 的“完整保留”契约，不能自行改判据放行。本轮不建议先放行 B 去赌它能阻止 WRITE_DAC。

## 6. 最多两项后续路线/外部条件

以下都不是已通过后端；本轮未实施、安装或联系外部人员。

### 路线一：保留无安装 PSEC，取得版本绑定的受支持组合或系统修复

必要外部条件是 Microsoft 对当前 OS/PSEC 版本提供可审查的组合支持/修复：明确自定义 restricted primary token 限制保留、MandatoryPolicy/子代及执行文件 IL 规则，以及 owner/DACL 访问的强制边界。当前证据没有这份契约，也没有说明某个现成宿主配置能把 1 恢复成 3。因此这是**等待系统提供方资料或修复的条件路线**，不是本机还可继续排列 flag 的实施方案。

产品交付变化：若仅新 OS 更新/版本支持可满足，需要 D12 固定实际最低构建、processmodel.dll/接口版本、探测拒绝和兼容范围；Python 核心和无安装目标可保持。若支持方要求额外 native broker/服务，须重新提交具体依赖方案，不随查询自动安装。

成本最低下一步：以本报告、a1 ZIP hash、五行对照及红回放准备一个最小问题包，要求支持方说明“是否保留、为何清位、受支持替代 API/版本”。**尚未发送消息或 issue。** 只有得到可检验的新依据，并由主协调明确新的最小验证边界后，才考虑在可回滚环境重启真实 A；A 通过再做原 B，继而 C。没有新资料时，此路线目前不能推进真实验证。

### 路线二：可回滚 Windows 环境评估签名 driver/service + WFP 的主机进程后端

延续 D10 已列的 Sandboxie 原生内核组件候选，不改变“Windows 主机原生进程、宿主工具链和路径、真实 OS 文件/网络限制”的目标。项目一手 [ReadFilePath](https://github.com/sandboxie-plus/sandboxie-docs/blob/87c545edd04baf4a0709251239c5cd658061815c/docs/Content/ReadFilePath.md) 描述只读外部路径；[WFP 文档](https://github.com/sandboxie-plus/sandboxie-docs/blob/87c545edd04baf4a0709251239c5cd658061815c/docs/PlusContent/WFPSupport.md) 描述 driver callout 与独立 loopback 控制。这只是候选依据，不能证明 WRITE_DAC/WRITE_OWNER/reparse、全部协议或故障 fail-closed 已满足。默认 copy-on-write 外写成功也不符合当前“拒绝外写”的目标，不能直接采用默认箱。

产品/宿主条件变化：需要用户接受管理员安装/卸载签名 driver 与 service、全局 WFP 组件、固定二进制版本/签名/hash、升级/崩溃恢复与依赖不可用时明确拒绝。Python 保持业务与编排核心，native 组件只承担 OS 强制层。需要单独裁定实际组件许可；[固定 LICENSE.Plus](https://github.com/sandboxie-plus/Sandboxie/blob/ac6900dc30c940ca57c4590494a816243fa3ce64/LICENSE.Plus) 区分 core GPLv3、QSbieAPI LGPL 与 SandMan 自定义许可，不能把整个 Plus 当 GPL 或声称已解决产品分发许可。

最低验证：先在用户批准的可回滚 Windows VM/专用测试机，用与 D20 同用户 owner、未改 outside ACL 的 fixture，证明允许根实际写成功，outside WRITE_DAC 单独/混合、WRITE_OWNER 及真实无害 ACE 变更全部拒绝且 host 读回不变；任一成功或需放宽规则即停止。该前置通过后才增加 Python/Git/PowerShell 和三代继承、reparse/retained handle、IPv4/IPv6 TCP/UDP 宿主及自身回环、net/no-net、取消/后台/owner crash 与 driver/WFP/service 故障拒绝。通过也只形成后端候选，60/61/78 与安装产物验收仍独立。

不把 WSL/Linux 结果充当 Windows；也不把 Windows Sandbox 的 guest 工具链和共享目录当当前主机 Shell 等价。它的 [官方说明](https://learn.microsoft.com/en-us/windows/security/threat-protection/windows-sandbox/windows-sandbox-overview) 明确宿主已安装软件不会自动出现在 guest，需要另装；故本报告不把它列为当前全目标的直接替代路线。

## 7. 资源、清理和交接

本轮 0 真实模型调用、0 凭据读取、0 PSEC/受限目标/Job/desktop/ACL/服务/驱动/防火墙变更。四次回放命令与两次纯数据 inspection 均已退出；第二次 inspection 仅新增“最小 fixture 与归档一致”的数据检查。仅新增本目录脚本、合成 HOME 目录与 evidence，保留供复核，没有递归删除历史缓存或对象。

历史资源状态只引用原证据：原 8 进程/8 Job/私有 desktop 已记录查无、允许目录 DACL 已记录恢复；PSEC 服务端 teardown 未独立证实，历史 ignored 缓存/合成目录仍保留。本轮没有重新查询现场，所以不更新其资源结论。

当前应继续的独立工作是已解锁产品票；D22 及 D12/60/61/完整安全门禁保持原状态，由主协调统一记录。研究完成不等于 D22 目标已达成，也不自行关闭任务。
