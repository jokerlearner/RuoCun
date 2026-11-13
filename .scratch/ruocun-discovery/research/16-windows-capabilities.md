# Windows 系统能力与隔离后端的可行边界

研究日期：2026-11-05

任务：[查清 Windows 系统能力与隔离后端的可行边界](../issues/16-windows-capability-research.md)

前置：[终端、Windows 平台、验证资产与交付候选研究](04-terminal-platform-delivery.md)

后续输入：[用最小 Python 探针验证 Windows 平台能力](../issues/17-windows-capability-experiment.md)

## 1. 本轮结论与证据口径

- **Windows 有可由 Python 对接的原生隔离机制，尚不能选定等价后端。** Job Object 适合命令树的限额、取消和生命周期；restricted token + ACL 是限制写入的候选；AppContainer 是文件、网络等资源隔离的候选。三者职责不同，通常需要组合，不能拿 Job 创建成功作为 OS 文件/网络隔离证据。[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)、[Restricted Tokens](https://learn.microsoft.com/en-us/windows/win32/secauthz/restricted-tokens)、[AppContainer isolation](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation)
- **优先缩小到两条原生探针：AppContainer + Job；write-restricted token + ACL + Job。** 前者先验证读写权限和两种网络模式，后者先验证写限制及主机工具链可用性；后者的断网需另接有依据的网络机制。Windows Sandbox、Windows containers 和 Sandboxie 保留为有前提的候选，不作为本机后端已经补齐的证明。它们的限制见第 3 节，排序是研究建议。
- **Task Scheduler 可承接系统级触发，cron 兼容层仍需 Python 负责。** 简单日/周/月规则可直映，复杂五字段规则可研究“系统每分钟唤起 Python dispatcher”。必须显式处理重叠、漏触发、时区/DST、登录身份和可执行文件升级路径；不能沿用系统默认值后称与 cron 等价。[Trigger Types](https://learn.microsoft.com/en-us/windows/win32/taskschd/trigger-types)、[Task Scheduler 2.0 Interfaces](https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-2-0-interfaces)
- 凭据优先试 Windows Credential Manager；唤醒锁有线程状态与句柄式 power request 两条原生路径；图片剪贴板可试 Pillow 或 Win32 数据格式；通知已有 Windows 来源分支，需补 Python 生命周期与错误观测。各候选均未安装、未运行。
- **未发现必须改变既定目标的新范围冲突。** edition、管理员辅助程序、虚拟化、通知身份注册等属于待选后端的条件，尚无事实证明所有可行候选均不能满足 Windows 全功能目标。本报告不代替后续路线决定，不把“禁用沙箱”“换成 WSL/Linux 容器”“功能跳过”计作补齐。

本轮遵守 [ADR-0001：Python 迁移边界与 Windows 优先验收](../../../docs/adr/0001-python-migration-boundaries.md) 与 [ADR-0002：独立仓库与纳入 Git 的本地工程记录](../../../docs/adr/0002-versioned-project-workflow.md)。核心 Python、允许底层语言绑定、Windows 优先完整验收、Linux/macOS 后续实机均为既定目标。

唯一 DAO 源码为 [冻结参考快照 dao-f17e189-7ac654a0dc06](../reference/README.md)：基准提交 f17e189dc68a0a0a0b9937784e1b7ce29aed80eb，树 SHA-256 7ac654a0dc06a9724982c35119501d65a3863e000458dcc0e2765fa66b53180c。只读解包根为 D:/java supplement/Firstcode/RuoCun/.worktrees/reference-dao-f17e189-7ac654a0dc06/source；下文“快照 路径:行号”均在该根中，不指活动 dao-code。

**证据区分：**“快照事实”仅说明代码；“官方声明”说明文档/API 契约；“候选/建议”是研究推论；“待实测”不计为通过。本轮未读取当前主机 edition/build、未调用系统能力探针、未修改 ACL/任务/凭据/剪贴板/通知注册/电源或虚拟化配置，也未运行 DAO 或产品测试。官方网页在本轮浏览核验；候选库的 main/master/stable 页面是当日材料，后续实验必须固定实际版本，不能以网页版本替代已安装版本。

## 2. 必须对照的来源契约

| 能力 | 冻结源码事实 | Windows 迁移的对照重点 |
| --- | --- | --- |
| 沙箱开启与失败 | DAO_SANDBOX=1 才开启；未开启或明确 disable 才返回 null；Windows 开启时返回不支持。快照 src/tools/sandbox.ts:4-13、:39-65。 | 是否启用、后端是否可用、是否获准绕过三种状态分开；后端启动失败必须可观察。 |
| 文件限制 | macOS 允许默认读/执行/网络，拒绝 file-write，再允许 cwd、指定临时路径与设备；Linux 只读绑定 /，可写绑定 cwd、独立 /tmp、proc/dev。快照 src/tools/sandbox.ts:23-34、:51-63。 | 基线是“工作区可写、其余文件写受限、临时资源例外”，不是“仅能看见工作区”；不同来源平台自身也非完全相同。Windows 必须列出实际可读、可写和私有临时根，验证主机工具链可用性。 |
| 网络限制 | 默认不切网络；DAO_SANDBOX_NO_NET=1 时 macOS deny network*、Linux --unshare-net。快照 src/tools/sandbox.ts:10-13、:32-33、:60-61。 | 默认网络可用和显式禁网都要验证。仅设置 HTTP_PROXY、禁某个域名或去掉环境变量不证明 OS 层断网。 |
| 审批与绕过 | dangerouslyDisableSandbox=true 会要求 ask；前台把该值传入 sandboxSpawn。快照 src/tools/exec_shell.ts:335-350、:397。 | OS 拒绝不能静默重试成普通进程；明确绕过需走原审批语义。审批和 OS 强制限制独立存在。 |
| 持久后台 | managed start 调用 sandboxSpawn，错误 throw，成功 SpawnSpec 写 manifest；runner 使用该 spec 启动子进程。快照 src/tools/managed_shell.ts:170-182、src/tools/shell_runner.ts:114-121。 | 持久 runner 必须保存实际隔离模式/策略标识，重连不新起任务，也不因主界面退出解除限制。 |
| 旧后台分支的差异 | startManaged 在未绑定 durable store 时回落 start；旧 start 只在 sb 且无 error 时用包装，error 分支会普通 shell 启动。快照 src/tools/process_manager.ts:113-118、:178-181。前台则明确错误返回，快照 src/tools/exec_shell.ts:185-186。 | **静态 fail-open 分支**，不是本轮 Windows 运行失败，也尚未穷举全部入口可达性。探针必须分别覆盖前台、durable 后台、无 store 后台及后台绕过参数，登记兼容差异，不能复制这个分支后称隔离通过。 |
| 系统定时 | add 只用粗略正则检查五字段形状，再写 crontab；list/remove 用 marker 和 1 起始序号；固定 cwd、prompt、可执行路径与日志。快照 src/schedule.ts:5-52。 | 来源未定义完整 cron parser，实际接受语法由安装的 crontab 决定。不能据此承诺任意 cron 方言。 |
| 定时运行前提 | 一次性 headless 调用，提示机器需开机且未休眠，无终端回答审批。快照 src/tools/schedule_tool.ts:5-24、:35-37。 | 系统定时不等于会话内 loop；不得启动 TUI 等输入，也不能擅自提升权限或放开审批。 |
| 凭据、唤醒锁、图片、通知 | KeychainPort 有 get/set/delete，set 失败可返回 file 存储；Windows 未实现钥匙串/唤醒锁/图片 clipboard；通知已有 NotifyIcon PowerShell 分支。快照 src/config/credential.ts:5-8、:33-45；src/config/keychain.ts:16-57；src/tui/wakelock.ts:5-17；src/tui/imagePaste.ts:5-27；src/tui/notifier.ts:51-58。 | 平台端口补齐并保留 best-effort/失败状态；不把有通知分支说成完全缺失，也不把文件 fallback 描述成系统凭据保存成功。 |

## 3. OS 隔离候选：真实边界与前提

### 3.1 Job Object 是进程治理层

官方 Job 支持把进程作为集合管理、限额和 TerminateJobObject。通常由 CreateProcess 创建的后代会自动加入，breakaway 标志可改变行为；文档特别列出 Win32_Process.Create 创建的后代不自动关联。Windows 8/Server 2012 起支持 nested jobs。现代 Windows 的安全限制要逐进程设置，旧 JobObjectSecurityLimitInformation 不再受支持。因此 **Job 本身没有来源要求的目录读写白名单/网络禁用策略**；网络限速同样不等于断网。[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)、[SetInformationJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-setinformationjobobject)

Python 可通过 ctypes 调 Kernel32，或用 pywin32 的 Win32 包装；这是绑定可行性，尚未验证任何具体版本的函数覆盖。[Python ctypes](https://docs.python.org/3/library/ctypes.html)、[pywin32 官方仓库](https://github.com/mhammond/pywin32)

**建议的启动/退出契约：**先创建并配置 Job，再 suspended 创建受限子进程、关联成功后恢复，避免普通启动后关联的空窗；关联失败要终止尚未运行的子进程并报错。普通前台可研究 KILL_ON_JOB_CLOSE；该标志的实际含义是“最后一个 Job handle 关闭时终止”，并非“任意 owner 退出时终止”。持久后台应由 runner 持有 Job，主 TUI 的退出不能成为最后 handle 的意外关闭。上述顺序为设计建议，需验 PID+creation time、handle 继承和 nested Job 环境。[AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject)、[JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information)

### 3.2 restricted token + ACL：保留主机读取的候选，不能单独宣称断网

CreateRestrictedToken 可删权限、把 SID 设为 deny-only、添加 restricting SID。常规 restricted SID 使资源访问必须同时通过原 SID 与 restricting SID 两次检查；WRITE_RESTRICTED 则只在写访问检查时使用 restricting SID。因此它值得研究为“原用户可读内容仍可读、仅允许指定根写”的候选，**不能无证据排除它**。[Restricted Tokens](https://learn.microsoft.com/en-us/windows/win32/secauthz/restricted-tokens)、[CreateRestrictedToken 的 WRITE_RESTRICTED](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-createrestrictedtoken)

候选组合是受限 token、单独 SID、实验 workspace/tmp 的窄 ACE、必要的低完整性/桌面及句柄约束、Job。它不是只设置 cwd：文件 ACL、owner/WRITE_DAC、删除/重命名、reparse point、继承的可写 handle 和子进程 token 都需要实际尝试证明。MIC 默认 no-write-up 可阻止低完整性写中完整性对象，但不是“仅 cwd 可写”的目录策略，不能独用低完整性标签作结论。[Mandatory Integrity Control](https://learn.microsoft.com/en-us/windows/win32/secauthz/mandatory-integrity-control)

权限上，官方说明普通程序可以使用调用者 primary token 的受限版本创建进程，相关 SE_ASSIGNPRIMARYTOKEN 例外存在；CreateProcessAsUser 还有 token 权限、配额、桌面等条件。**不能笼统宣称这条路线必须管理员，也不能保证当前环境普通用户一定成功**。先在普通用户自己的实验目录内探测，失败记录 Win32 error，而非顺手提权或扩大系统 ACL。[Restricted Tokens](https://learn.microsoft.com/en-us/windows/win32/secauthz/restricted-tokens)、[CreateProcessAsUserW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessasuserw)

token 本身不提供来源那样的网络开关。若用 WFP/WFAS 补网络层，必须设计与本次执行及后代身份绑定的策略，不能只封 python.exe 后宣称所有子工具断网。WFP 有按应用/用户等条件过滤的能力，BFE 有自己的访问控制；默认并非所有普通用户都能添加过滤器。需要明确辅助服务/提权安装、过滤规则生存期、代理/回环/IPv6、故障和清理。本轮不新增规则、不更改防火墙。[About WFP](https://learn.microsoft.com/en-us/windows/win32/fwp/about-windows-filtering-platform)、[WFP Access control](https://learn.microsoft.com/en-us/windows/win32/fwp/access-control)、[ALE](https://learn.microsoft.com/en-us/windows/win32/fwp/application-layer-enforcement--ale-)

### 3.3 AppContainer：首要原生文件/网络隔离候选，兼容性待证

AppContainer 的文件/注册表、凭据、网络、进程与窗口隔离是官方能力。访问通常是 user/group 权限与 package/capability SID 权限的交集；可为具体目录授读、写、执行，非简单继承当前用户所有权限。无 network capability 时不能访问网络；network capability 可细分 Internet、Intranet、server。普通 AppContainer 与更严格 LPAC 有区别，首轮不用 LPAC 作为默认复杂度。[AppContainer isolation](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-isolation)、[Launch an AppContainer](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer)

直接 Win32 启动路径已公开：创建/派生 profile SID，组 SECURITY_CAPABILITIES，经 STARTUPINFOEX / PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES / CreateProcess 创建；此属性及 CreateAppContainerProfile 的最低客户端是 Windows 8。文档没有把这些 API 限定为 Windows Pro，也不要求此直接路径先变成 UWP 产品；这不等于本轮已经在 Home 或任何 build 验证。Python 可用 ctypes 封装，或采用经过验证的底层绑定；字长、结构布局、SID/attribute list 的存活与释放须验。[UpdateProcThreadAttribute](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute)、[CreateAppContainerProfile](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-createappcontainerprofile)

**与来源的潜在差异是待证兼容性，尚非否定结论：**

1. 来源在主机命名空间中广泛可读，AppContainer 默认可见资源更窄；Python interpreter/DLL/venv、Git、PowerShell、npm/pip 及它们的配置/缓存可能需要明确读执行权限或私有可写根。先验最小 Python，再验实际工具链；不能为省事对整盘授写。
2. profile 自有存储及 tmp 也会成为可写资源，要逐一列入策略，不能声称工作区以外绝无可写位置。profile 是 per-user/per-app；创建可能返回 E_ACCESSDENIED 或 already-exists，须使用本次实验的唯一名称、记录 SID，并只清自己的 profile。[CreateAppContainerProfile](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-createappcontainerprofile)
3. “默认联网”不能只加 internetClient 就假定等价主机网络。微软 UWP 网络隔离说明对 localhost 通信有 loopback exemption 要求；将这个限制用于直接 Win32 AppContainer 的具体效果仍需实测。不能全局加 loopback 豁免后宣称禁网；分别测 127.0.0.1、::1、宿主非回环地址、DNS、HTTPS、子进程及所需代理。[UWP/Firewall loopback 文档](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/troubleshooting-uwp-firewall)
4. runner 控制通道和输出通道需要窄授权，不能把任意“替我执行/打开文件”的 broker 暴露给受限进程。网络关闭时不能依赖被关闭的 TCP 通道维持取消。应用审批仍在 host，不能将 AppContainer 故障自动解释为获准绕过。
5. 结束时先取消/等待 Job、关闭输出和存储 handle，再删除 profile、恢复本次改过的 ACL；删除 profile 官方要求尽量先关闭存储 handle，失败时状态不确定，应重试核实。不能只看到删除调用成功文本就省略残留检查。[DeleteAppContainerProfile](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-deleteappcontainerprofile)

### 3.4 有基础设施前提的其它候选

| 候选 | 有依据的能力与前提 | 与本项目契约的距离、当前处理 |
| --- | --- | --- |
| Windows Sandbox | 独立内核/硬件虚拟化；Home 不支持，支持 Pro/Enterprise/Education 等指定 edition；Windows 10 1903+ / Windows 11、虚拟化、内存/磁盘、启用可选功能等条件。关闭传统 Sandbox 会丢弃 guest；host 已装软件不会自然出现在 guest。[产品说明](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/)、[安装前提](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-install) | .wsb 支持网络开关、host 目录只读/可写映射；默认网络和剪贴板重定向开启，不可沿用默认配置后当断网通过。更像独立执行环境，需供应 guest 工具链、路径/输出/取消和后台生存期；不能以 Home 上不可用否定所有原生路线。[配置](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file) |
| 新版 Windows Sandbox CLI | Windows 11 24H2 起文档列 start/list/exec/stop/share/connect；exec 返回退出码，但该 CLI 文档明确当前不提供进程 I/O；ExistingLogin 需要活跃 guest 用户会话。[Windows Sandbox CLI](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-cli) | 不能写成“Windows Sandbox 完全不能自动化”，也不能直接当与 host shell 流式 stdout 等价。微软较新的 winapp 路线通过 guest agent 提供重定向流等能力，增加 CLI/agent/guest 配置依赖；先登记候选，不在首轮原生探针安装。官方仍说明一次只能一份 Sandbox，不适合假定每个并发任务独占一份。[winapp Sandbox execution](https://learn.microsoft.com/en-us/windows/apps/dev-tools/winapp-cli/sandbox-execution) |
| Windows containers | process isolation 隔离文件系统/注册表/网络等 namespace但共享 host 内核；Hyper-V isolation 每容器独立内核。Windows Server 2016+、客户端指定 Pro/Enterprise edition，Hyper-V 模式需对应角色；镜像/host 版本兼容另有要求。[Isolation modes](https://learn.microsoft.com/en-us/virtualization/windowscontainers/manage-containers/hyperv-container)、[系统要求](https://learn.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/system-requirements) | 需容器 runtime/service、Windows 镜像、挂载/网络/工具链分发，路径和进程身份不再等同 host；可由 Python 调 runtime API/CLI，但不因调用者 Python 就免去这些依赖。本轮不拉镜像、不启用功能。WSL/Linux 容器仅可说明其 guest 能力。 |
| Sandboxie Plus/Classic | 维护者提供文件/注册表隔离、进程管理、WFP 网络规则；有 driver/service，项目列 Windows 7+ 64 位及不同版别/许可。[维护者 README](https://raw.githubusercontent.com/sandboxie-plus/Sandboxie/master/README.md)、[文件规则](https://github.com/sandboxie-plus/sandboxie-docs/blob/main/docs/Content/ResourceAccessSettings.md) | Python 可以编排外部后端，核心仍可 Python；需要固定版本、安装权限/签名/授权、文件重定向语义和清理验证。默认把写重定向到 box，不等同“外部写立即拒绝”。维护者明确用户态 Winsock hooks 可被绕过，WFP 模式另有规则/loopback/失败语义；不能以 GUI 的 Test Rules 代替实际网络 I/O。[WFP Support](https://github.com/sandboxie-plus/sandboxie-docs/blob/main/docs/PlusContent/WFPSupport.md) |

以上候选都没有本轮运行结果。当前最省实验范围的顺序是原生 AppContainer、原生 write-restricted 路线，再根据已证实差距研究基础设施后端；不提前承诺所有候选都能满足，也不据尚未实现宣称任一 API 不可行。

## 4. 系统定时：Task Scheduler 与五字段 cron

### 4.1 Python 对接和映射候选

Task Scheduler 2.0 有 ITaskService/ITaskFolder/ITaskDefinition/trigger/action/settings 等接口，Python 可用 pywin32 COM 接 Scheduler 服务；固定 XML + 注册 API 也是候选。首轮建议 COM/XML，避免先把 prompt、cwd、重定向拼成多层 PowerShell/cmd 文本。[Task Scheduler 2.0 Interfaces](https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-2-0-interfaces)、[pywin32](https://github.com/mhammond/pywin32)

| 输入类别 | 候选映射 | 必须证明或明确的边界 |
| --- | --- | --- |
| 0 9 * * * | daily trigger 09:00 | 本地墙上时间、时区变更、DST 缺失/重复时间、登录/锁屏条件。 |
| 30 8 * * 1-5 | weekly trigger 工作日 08:30 | 星期编号转换；不能把 cron 周日 0/7、Scheduler bitmask 混为一谈。 |
| 0 9 1 * * | monthly trigger 每月 1 日 | 29/30/31 日和月集合；不得把不存在日期改为当月最后一天而无记录。 |
| */15 9-17 * * 1-5、列表/步进/月组合 | 展开多个触发器，或系统 PT1M 触发 dispatcher，由 Python 匹配 cron | 原生日/周/月 trigger 不是任意 cron parser。展开数量、重复触发去重、首次边界、错过分钟和 dispatcher 事务必须验证。 |
| DOM 与 DOW 同时受限，例如 0 9 1 * 1 | 同一 cron matcher 管理，或月/周 trigger 合并并去重 | Cronie 的经典行为是两者任一命中；不是 AND；两者同一天命中也只应启动一次。来源未固定宿主 cron 实现，因此此处是待定义的兼容方言而非已证明的来源跨平台唯一语义。 |
| L、W、#、?、秒字段、宏、随机扩展或无效数值 | 按实际选定方言验证后支持或明确拒绝 | 来源 regex 不等于支持这些语法。不能截成五字段或静默近似后写“已添加”。 |

映射依据：[Task Scheduler Trigger Types](https://learn.microsoft.com/en-us/windows/win32/taskschd/trigger-types)。cron 数值列表、范围、步进、DOM/DOW OR 与特定 DST 行为的第一手例子来自 [Cronie crontab.5 源码](https://raw.githubusercontent.com/cronie-crond/cronie/master/man/crontab.5)，**不把该实现等同冻结来源在每台机器实际安装的 crontab**；来源只交给系统 crontab（快照 src/schedule.ts:13-36）。Open Group 当前及旧版页面本轮返回 403，未将未读取的标准文本当作本轮证据。

dispatcher 是系统触发的短生命周期 Python 程序，非依赖 TUI 常驻的内存 scheduler。Task repetition 支持最短一分钟间隔，Duration 省略可无限重复；是否每个 cron 各一任务、还是一个分发任务、是否引入已审查 cron 库，待探针后决定。不能用“每隔 15 分钟”算术替代“每小时指定分钟”的墙上时间集合。[repetitionType](https://learn.microsoft.com/en-us/windows/win32/taskschd/taskschedulerschema-repetitiontype-complextype)、[Task Scheduler schema](https://learn.microsoft.com/en-us/windows/desktop/taskschd/task-scheduler-schema)

### 4.2 必须显式设置的运行语义

| 维度 | 官方事实 | 对照与探针要求 |
| --- | --- | --- |
| 时区/DST | StartBoundary 无 offset/Z 时使用主机当前时区/DST；显式 offset 或 Z 时按该 offset，与主机时区/DST无关。[StartBoundary](https://learn.microsoft.com/en-us/windows/win32/api/taskschd/nf-taskschd-itrigger-get_startboundary) | 保留原始 cron 和选定时区语义；“每天当地 09:00”不要只在注册时换成永久固定 UTC。DST gap/fold/更改时区的具体触发次数仍需试验，文档这一条不足以推导所有边界。 |
| 漏触发 | StartWhenAvailable 默认为 false；设 true 的补触发会排队，有默认延迟，不保证补齐每个错过的分钟。[StartWhenAvailable](https://learn.microsoft.com/en-us/windows/win32/taskschd/tasksettings-startwhenavailable) | 来源明确提示醒着才触发（快照 src/tools/schedule_tool.ts:13）。首轮先验 no-catch-up，另验 opt-in 补触发；不要擅自默认唤醒或追跑全部旧任务。dispatcher 必须定义 late tick 容忍窗及幂等键。 |
| 同任务并发 | MultipleInstancesPolicy 默认 IgnoreNew；还可 Parallel、Queue、StopExisting。[MultipleInstancesPolicy](https://learn.microsoft.com/en-us/windows/win32/taskschd/taskschedulerschema-multipleinstancespolicy-settingstype-element) | 来源不加互斥。若目标采用并发，应显式 Parallel 或由短 dispatcher 启动独立 run；选 Queue/IgnoreNew 会改变行为，不能隐去。单次触发去重与禁止合法相邻轮并发不是同一件事。 |
| 时限/电池 | 默认 ExecutionTimeLimit 72 h，可用 PT0S 无限；schema 中 DisallowStartIfOnBatteries、StopIfGoingOnBatteries 默认 true。[ExecutionTimeLimit](https://learn.microsoft.com/en-us/windows/win32/taskschd/tasksettings-executiontimelimit)、[schema](https://learn.microsoft.com/en-us/windows/desktop/taskschd/task-scheduler-schema) | 必须读回最终 XML，不让未声明默认值替代来源行为。用缩短时限实验证明机制，不能跑几分钟就声称验证了 72 h。长任务的产品时限是否需要变化另按既定契约登记。 |
| 唤醒 | WakeToRun 可要求系统为任务唤醒。[WakeToRun](https://learn.microsoft.com/en-us/windows/win32/taskschd/tasksettings-waketorun) | 系统定时的唤醒功能与任务执行期间 wakelock 分开；实际唤醒受硬件/策略影响，未实测不保证。 |
| 登录/身份 | 普通用户可按条件注册自己的低权限任务；InteractiveToken 仅已登录会话；Password/S4U 要求 batch logon 权利。官方 S4U 文档写“不存密码、无网络和加密文件访问”。[Security Contexts](https://learn.microsoft.com/en-us/windows/win32/taskschd/security-contexts-for-running-tasks)、[logonType](https://learn.microsoft.com/en-us/windows/win32/taskschd/taskschedulerschema-logontype-simpletype) | **文档限制不是已实测“模型 HTTPS 一定不通”。** 分别验匿名 TCP/HTTPS、需要用户凭据的 UNC/代理、凭据库、用户 profile，以及已登录/锁屏/注销；记录实际 token/logon type。不能为了任务注册成功改用 SYSTEM 或暗存用户登录密码。 |
| 命令与升级 | ExecAction 分 Path、Arguments、WorkingDirectory；环境变量值可能被 task engine 缓存。[ExecAction](https://learn.microsoft.com/en-us/windows/win32/taskschd/execaction) | 用绝对稳定 launcher 路径和任务 ID/受 ACL 保护 manifest，避免把敏感 key/prompt 原样堆进任务参数；manifest 仅作为建议，不擅改外部格式。升级若替换路径，需更新任务并读回/实际触发；PATH 更新不代表已修复旧 action。 |
| 失败和查询 | task 注册、权限及运行是不同操作，用户创建的任务通常可自行读/改/删/运行。[Security Contexts](https://learn.microsoft.com/en-us/windows/win32/taskschd/security-contexts-for-running-tasks) | list 的服务不可达/拒绝不能像来源 readCrontab catch 那样当空；保存 HRESULT/LastTaskResult、实际 worker receipt、exit status 和日志。API“注册成功”不等于工具执行成功。 |

输出重定向由 headless wrapper 显式打开日志，不能假定 ExecAction 会解释 >>。用“程序路径、参数字符串、工作目录”分别构造并测试中文、空格、单双引号、百分号、美元及换行 prompt；日志目录先创建、权限失败清楚返回。来源固定日志路径与工具入口参数见快照 src/schedule.ts:8-10、src/tools/schedule_tool.ts:35-37。编号 list/remove 应基于本产品任务命名空间的稳定列表，不能删除非本产品任务。

## 5. 凭据：Windows Credential Manager 与失败兜底

**首选探针候选：**ctypes 或 pywin32 对接 CredWriteW / CredReadW / CredDeleteW，类型 CRED_TYPE_GENERIC；TargetName 纳入独立 service 与 account/profile，避免仅换 UserName 导致同 TargetName 覆盖。官方 CREDENTIAL 结构以类型和 target 识别凭据，TargetName 不区分大小写，generic blob 最大 5×512 字节。CRED_PERSIST_LOCAL_MACHINE 是同用户同机器跨登录会话可见，不是“全机所有用户共享”。[CREDENTIALW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw)

这带来一项具体映射测试：来源 addProfile 直接按 JavaScript 对象键检查/保存名称（快照 src/config/profiles_store.ts:45-50），不能假定 Profile 与 profile 必须合并。Windows TargetName 需可逆编码或稳定无碰撞标识保持 account 语义，至少验证仅大小写不同及 Unicode 名称，不擅自改变 profile 命名规则。

端口仍对应 get(account)、set(account,key)、delete(account)（快照 src/config/credential.ts:5-8）。成功才保存 keyRef；set 失败的原契约会落 inline key（快照 src/config/credential.ts:33-45）。新适配至少内部区分 not-found、拒绝、无 credential set、依赖不可用、编码/长度错误；get 的空值不能对用户误报“已从系统凭据库读回”。这些 API 关联当前 token 的 logon session，network logon session 没有关联 credential set；CredRead 分配的内存须 CredFree。[CredWriteW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credwritew)、[CredReadW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credreadw)、[CredDeleteW](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-creddeletew)

Python keyring 的 WinVaultKeyring 是备选：维护者源码优先 pywin32-ctypes，再回落 pywin32；有 service/username 冲突处理，默认 persistence 为 enterprise。不能只调用 keyring 自动发现后就假定选到目标后端/本机持久化。探针需要固定 backend、persistence、版本和 profile 映射。[keyring Windows backend 源码](https://raw.githubusercontent.com/jaraco/keyring/main/keyring/backends/Windows.py)

来源对外部钥匙串调用设 8 s 上限，并允许显式关闭（快照 src/config/keychain.ts:10-19）。Windows native binding 没有因此自动获得同样的有界启动契约。建议不要在 UI 输入线程同步等待可能阻塞的端口；如使用隔离 helper 限时，超时写入应标为结果未知并查询核对，不能既宣称未保存又直接产生第二份存储而不记录。真实服务错误与 helper 超时的证据分开。

**失败文件兜底必须如实呈现。** 来源的 0600 chmod 不证明 Windows DACL（快照 src/config/profiles_store.ts:33-38）。后续若保留 inline fallback，要核查当前用户和继承 ACE、父目录/临时文件与备份的 ACL；系统凭据库没有按应用代码身份隔离同用户所有程序的本项目承诺，不能把 profile 命名分隔夸大为同用户进程间安全边界。DPAPI 是另一个加密落盘候选，默认通常与同用户登录凭据和机器关联；它不是 Credential Manager，也不能直接替换配置格式后声称零变化。[CryptProtectData](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata)

所有实验只用合成秘密，日志只记状态/长度/一次性 hash，不写值，不通过 argv 传值。注册后 headless 登录方式能否读回同一 credential 是系统定时探针的一部分，不能从交互会话的成功外推。

## 6. 唤醒锁：线程状态或句柄式 power request

| 候选 | 官方机制与前提 | Python 生命周期建议及限制 |
| --- | --- | --- |
| SetThreadExecutionState | API 文档最低 Windows XP；ES_CONTINUOUS + ES_SYSTEM_REQUIRED 持续请求系统运行；不带 CONTINUOUS 只重置 idle timer；返回前一次线程状态，0 表示失败。它不能阻止用户主动 Sleep，away mode 不用于普通长任务。[SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) | 简单首选探针。由固定长寿线程 acquire/release，任务引用计数 0→1 请求、1→0 清理；不能在任意线程池 worker 释放别的线程状态。不默认请求 DISPLAY_REQUIRED。嵌套、取消、异常和重复 release 均验。 |
| PowerCreateRequest + PowerSetRequest / PowerClearRequest | Windows 7+ 有句柄式对象及 reason；Set 增加相应类型计数，Clear 减少，最后 CloseHandle。[PowerCreateRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powercreaterequest)、[PowerSetRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powersetrequest)、[PowerClearRequest](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powerclearrequest) | 若多 task/runner 管理比线程状态更自然，可比较此候选。每次成功 Set 配对一次 Clear，失败不减计数；finally 关闭 handle。不是无限防睡保证。 |

微软明确说明 Modern Standby + 电池供电时 system/execution request 在睡眠超时后还有终止条件，用户主动休眠也会终止相应请求；必须记录 S3/Modern Standby、AC/DC、电源策略，不能由一次 API 返回非零保证电脑永不睡。[PowerSetRequest 限制](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-powersetrequest)

来源是回合 acquire/finally release，只在 completed 且超时阈值后通知（快照 src/index.ts:1524-1534）。不要为此永久持锁；持久后台若应阻止 idle sleep，应由其实际生命周期所有者持有，不能主 UI 结束回合即释放所有后台锁。产品目标如何覆盖后台按后续既定调度契约收口，不在静态研究擅自扩为常驻不休眠。

## 7. 文本与图片剪贴板

文本复制可直接 Win32 CF_UNICODETEXT，避免把中文交给未知 code page 的 clip 子进程。写入须正确 owner/window、OpenClipboard/EmptyClipboard/SetClipboardData/CloseClipboard，成功交接后由系统拥有内存；OpenClipboard(NULL) 后 EmptyClipboard 会使 owner 为 NULL，导致 SetClipboardData 失败，不能照抄这种常见简化写法。[OpenClipboard](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-openclipboard)、[SetClipboardData](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setclipboarddata)

图片的最小高层候选是 Pillow ImageGrab.grabclipboard()，官方支持 Windows，返回值可能是 Image、文件名列表或 None，文件列表并不保证都是图片。必须分支处理，不能把文件列表或多文件读取自动当 clipboard image；来源的单图片路径粘贴与 clipboard 图片是两条入口。[Pillow ImageGrab](https://pillow.readthedocs.io/en/stable/reference/ImageGrab.html)、快照 src/tui/app/App.tsx:1303-1338。

需要精确格式/alpha 时可用 ctypes/pywin32 读注册 PNG 格式、CF_DIBV5、CF_DIB、CF_BITMAP，再交解码器转 PNG；CF_DIB 是 BITMAPINFO+bits，DIBV5 是 V5 header+色彩信息+bits，不能当现成带 BMP 文件头的数据。PNG 不是此标准格式表中的固定常量，读取注册格式必须显式检查。每次成功 Open 都 finally Close；立即复制系统返回的内容，不释放 GetClipboardData 返回的 handle，不在 Close 后使用它。[标准 clipboard formats](https://learn.microsoft.com/en-us/windows/win32/dataxchg/standard-clipboard-formats)、[GetClipboardData](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getclipboarddata)

原图片入口限制输出 PNG 原始字节 ≤5 MiB（快照 src/tui/imagePaste.ts:20-23）；Windows 不能只查 base64 字符数。解码前还需验证尺寸、stride、长度、压缩格式及像素上限，避免压缩小但解码巨大的数据；这是防御性适配建议。RGBA/半透明、24/32 位 DIB、上下颠倒/stride、多显示器截图格式都以像素和尺寸断言，不能用“返回了 Image”作为正确。

**触发和恢复是独立问题：**来源仅 macOS 空 paste 才查询图片（快照 src/tui/app/App.tsx:1303-1313）。Win32 clipboard API 可用并不证明 Windows Terminal 粘图片会产生同样事件。后续探针必须观察真实 WT 的用户粘贴路径；若需新增明确快捷键/命令，先把具体体验与兼容影响交平台/终端决定，不能悄悄在任意空输入时轮询 clipboard。已有文本事件读取图片失败要保留文本。

测试写入前要保存可恢复的完整状态。任意 clipboard 可含私有格式、延迟渲染和进程所有 handle，单读文本不叫完整备份。首轮**写入测试在一次性 Windows 用户会话/VM 中做，预置并记录可完整恢复的合成 formats**；主会话只做不会 EmptyClipboard 的读取。如必须在已有 clipboard 做写入，先证明所有当前格式均能 materialize/复制/恢复；有无法恢复的格式则不覆盖。恢复前检查 sequence，若用户期间已复制新内容，不用旧快照覆盖新内容。[延迟渲染与所有权](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setclipboarddata)、[GetClipboardSequenceNumber](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getclipboardsequencenumber)

## 8. 通知：已有 balloon 契约与 toast 候选

来源 Windows 用 PowerShell Forms NotifyIcon，ShowBalloonTip 后等待 5 s 再 Dispose，所有错误忽略；这说明已有 best-effort 通知，并不保证 toast 历史、点击或时长（快照 src/tui/notifier.ts:51-58）。微软当前 Forms 文档将 timeout 参数标为 deprecated，展示时间由系统辅助功能设置决定，因此“等 5 s”不是渲染成功或完整展示证明。[NotifyIcon.ShowBalloonTip](https://learn.microsoft.com/en-us/dotnet/api/system.windows.forms.notifyicon.showballoontip?view=windowsdesktop-9.0)

| 路线 | 可用机制 | 必须验证的生命周期 |
| --- | --- | --- |
| 原生 balloon，尽量对应来源 | ctypes/pywin32 建隐藏窗口和消息循环，用 Shell_NotifyIconW NIM_ADD/MODIFY/DELETE；回调窗口承接通知，NOTIFYICONDATA 固定字符容量和 flags。[Shell_NotifyIconW](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/nf-shellapi-shell_notifyiconw)、[NOTIFYICONDATAW](https://learn.microsoft.com/en-us/windows/win32/api/shellapi/ns-shellapi-notifyicondataw) | 串行通知队列或合并策略、延迟展示、用户点击/关闭、Explorer 重启、正常/异常退出删除 icon、线程停止。保留有界等待，不能只 sleep 固定秒数；API accepted 与用户看到分开记录。静态文档不足以保证无桌面/勿扰时弹出。 |
| WinRT desktop toast | Windows.UI.Notifications + Python WinRT projection 是绑定候选；经典 desktop API 要有效 AppUserModelID/Start menu shortcut，激活回调另有要求。[桌面 toast 官方步骤](https://learn.microsoft.com/en-us/windows/win32/shell/quickstart-sending-desktop-toast)、[PyWinRT](https://pywinrt.readthedocs.io/en/latest/) | Python projection 不代替身份注册。安装/升级/卸载管理自己的 AUMID/shortcut/COM activator；记录 Failed/Dismissed/Activated、超时/历史、进程退出后激活、旧路径和正确会话路由。[进程退出后的激活契约](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/win32_tile_badge_notif/respond-to-toast-activations) |
| Windows App SDK app notifications | 有 app 通知和 activation 管理；官方当前声明 elevated app 不支持发送/接收；Python 绑定/辅助库、SDK runtime 供应要另行证明。[App notifications overview](https://learn.microsoft.com/en-us/windows/apps/develop/notifications/app-notifications/) | 可作后续候选，不假定已有可直接安装的 Python 等价端口；不为普通通知引入未核验的 SDK/broker，也不让管理员工具执行把主 UI 一并提升。 |

标题/内容必须作为原生数据/XML text node，不能把 JSON.stringify 的结果当 PowerShell 字面量；来源确有插入 -Command 的代码（快照 src/tui/notifier.ts:55-56），PowerShell 双引号会展开变量与子表达式，因此该做法存在静态转义风险。[PowerShell 引号规则](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules) probe 用中文、单双引号、美元、括号、换行与 XML 特殊字符合成载荷，确认字面显示且不执行内容。通知失败不阻塞已完成回合，也不能伪造 displayed=true；内部记录 submitted/failed/visible-observed/clicked 等分离状态。自动恢复正确 WT tab 不是来源 Windows 已证明能力，不能把点击启动另一份 TUI 当作回到原会话。

## 9. 收紧后的最小平台探针输入、预期与恢复

以下是 [用最小 Python 探针验证 Windows 平台能力](../issues/17-windows-capability-experiment.md) 的**实验设计输入**，不是已执行步骤。产物只写该票的 discovery/experiments/windows/，不修改冻结来源，不先移植产品平台层。

### 9.1 共用环境与证据

1. 先记录 Windows edition/build/arch、普通或 elevated token、真实登录类型、Python/依赖精确版本、启动路径、所在卷文件系统、嵌套 Job、电源类型与 sleep model；有 Sandbox/容器候选才记录可选功能/虚拟化/runtime/镜像标识。不能从本报告推定当前主机满足条件。
2. 每次实验分配 run UUID；实验根包含 workspace、tmp、outside 三个并列合成目录，outside **也在可删除实验总根内**，其初始 ACL 允许普通父进程读写，避免用系统文件天生拒绝写假装沙箱拒绝成功。需额外授予读执行权限的 Python/runtime 使用根内独立副本，不能为跑通探针修改主机 Python 安装目录 ACL。所有 SHA/ACL/对象名先写 manifest；绝不改盘根/用户主目录 ACL。
3. worker 是固定本地 Python 合成程序，不接模型/API key，输出操作名、PID+creation time、token/container/Job 标识、开始/结束单调时钟、请求/实际值、Win32/HRESULT 和成功/拒绝。host 验证实际文件变化与服务器收到的连接/字节，不能只信 worker 自述。
4. 每项结果标 passed/failed/unsupported-prerequisite/not-run，并分 API 绑定测试、真实 OS 行为、真实 WT 体验和用户验收。没有 edition/权限条件不计失败也不计支持；没有读写/网络实际尝试不计隔离通过。
5. 全局 finally 只清本次 UUID 对象；强杀场景用独立 cleanup manifest 恢复。退出时核对 PID+creation time、Job 活动成员、ACL、任务、凭据、profile、窗口/icon/注册与文件残留。无法完整清理记失败并保留精确恢复步骤。

### 9.2 先做的原生最小集

| 编号 | 输入/操作 | 预期与验收证据 | 清理/恢复 |
| --- | --- | --- | --- |
| WC-01 Job 对照 | 无文件隔离的 worker→child→grandchild，均持续写合成心跳；另试受控 breakaway；先独立 Job，后在已有 Job 的父环境。 | 无安全策略的 Job 中仍能写 outside/连本地 server，证明它仅是治理对照；取消后所有受管 PID 终止、心跳不再更新；关联失败无先运行窗口。 | 终止本 Job、等待后代、关全部 handle，验证无继承 handle 使 KILL_ON_JOB_CLOSE 延后；不可按裸 PID 扫杀。 |
| WC-02 AppContainer 文件 | profile 唯一名称；Python/runtime 只读执行，workspace/tmp 授必要写；outside 不授写。读/新建/覆盖/append/rename/delete/建子目录/重设 ACL；受控 junction 指向 outside。 | 记录成功读取 runtime、workspace/tmp 操作成功、outside 原用户可读文件是否可读以及所有写实际拒绝；拒绝若来自 runtime 启动失败不能算文件隔离通过。child/grandchild 相同行为；任何 profile 自有可写根完整登记。 | 取消 Job、关存储 handle，恢复仅本次改过的 DACL/label，删除 profile 并复查存储，最后删实验文件。 |
| WC-03 write-restricted 文件 | 与 WC-02 同 worker 和同初始 ACL；使用 WRITE_RESTRICTED+独立 SID/窄 ACE，去权限；先默认网络，不伪装已断网。 | 外部读与工具链较窄方案差异可比；外部写/删除/ACL 操作拒绝，内部允许；专测 owner/继承 ACE/handle/reparse/后代不能扩大权限。token 创建成功不计隔离成功。 | 终止 Job、关 token/process/thread handle；按 manifest 恢复 ACL；若请求额外权限返回失败，不现场扩大主机 ACL。 |
| WC-04 网络两模式 | host 绑定 127.0.0.1 和 ::1 的独立 TCP/UDP server；如有测试网卡再测 host 非回环地址；对 child/grandchild 尝试连接/listen、数值地址和名字解析。AppContainer 无 capability 与所需 network capabilities 分别启动。 | 允许模式实际 server 收到随机 nonce；禁网模式没有收到，worker 得拒绝/有界失败；区分“回环本就受限”“server 没开”“能力阻断”。若显式 no-net 的要求包含 guest 自身 loopback 也必须单列，不能用 host loopback 拒绝代替。 | 关闭 server/sockets，取消 Job；只删除本 profile 的本次豁免/规则。首轮不加全局 loopback exemption，不安装 WFP service；restricted-token 无网络层部分标未覆盖。 |
| WC-05 后台与失败 | runner 拥有 Job；主 UI 正常退出/崩溃，runner 继续写；重连再取消；另外故意提供无效 sandbox 配置。 | keep-background 下不因 UI handle 关闭杀 worker；显式取消收口。前台/durable/无 store 三入口在隔离启动失败时均清楚失败，审计记录本次没有普通 shell；明确绕过只有审批通过才单独执行。依据第 2 节静态 fail-open 差异登记。 | 停止自己 runner/Job，核对 run receipt 不重复启动；取消 marker/端点/输出文件按 UUID 清除。 |
| WC-06 Task CRUD/触发 | 自己的任务目录和 UUID，普通用户/InteractiveToken，固定合成 worker；实际近未来一次触发与 PT1M 重复，中文空格 cwd、引号/百分号/美元/换行 prompt 经 manifest。 | 创建→查询→修改→查询→实际 receipt→删除→查无；核对 executable/argv/cwd/文本 hash、run 身份、无多余 console 窗口；服务拒绝不报空列表。 | 先停本次 running instances，再删本任务/本次创建的空 folder；保留清理查询结果。 |
| WC-07 cron/重叠/升级 | 纯 Python matcher 用 0 9 * * *、*/15 9-17 * * 1-5、0 9 1 * 1、闰日/31日、无效字段；OS 触发 worker 跑超过 1min，观察相邻触发；复制到新 launcher 路径模拟升级。 | 合成时间集合符合明确方言，DOM/DOW 同时命中只一次；实测 Parallel/IgnoreNew/Queue 差异，读回 time limit/battery 默认并按候选显式值对照；升级后旧任务触发新绝对路径且不双跑。 | 删除两份合成 launcher/manifest、还原本次任务或直接删 UUID 任务；未运行 72h 则只声明读回配置与缩短时限机制验证。 |
| WC-08 credential | 两 profile、仅大小写不同的 profile、中文 account；合成短/边界长度 secret；新进程读回/覆盖/删/删不存在；受支持的无 credential set/拒绝环境另试。 | 不串 profile；值一致仅记 hash；返回长度/encoding 正确；不存在、访问失败和超时未知状态分开。故障注入验证 file fallback **只属 adapter 证据**，不能冒充真实服务拒绝。 | 删除所有本次 TargetName；查不到才完成；清本次合成 fallback/备份并检查 DACL；不触碰真实 key。 |
| WC-09 wakelock | 固定线程两层 acquire，分别 release；取消/异常/重复 release；若对比 PowerRequest 则逐次 Set/Clear；普通用户下可用的 powercfg /requests 作只读辅助。 | 0→1/1→0 转换、持有线程、API return、引用计数和请求移除有证据；API 失败不标已持锁。系统实际是否会睡需独立受控电源实验，不能由短时运行代替。 | finally 清同线程状态或平衡 Clear+Close；worker 异常退出后复查无本次 request，不修改系统电源计划。 |
| WC-10 clipboard | 在可恢复合成剪贴板会话写中英/emoji、PNG/RGBA、DIB24/32/alpha、文件列表、无图/空、接近/超过5MiB、畸形大尺寸；另一个 helper 短暂占用 clipboard。 | 文本不乱码；图片尺寸/像素/alpha 与 fixture 相符；返回 list 不误读；有界失败后输入文本保留；无写读取前后 sequence/格式不变。真实 WT 的粘图片事件另验，不伪造空 paste 结果。 | 每次 Close、释放自己尚未交给系统的内存/窗口；完整恢复预置 formats 并核对；用户若产生新 sequence 不覆盖。 |
| WC-11 notification | 普通用户桌面原生 balloon；中文、引号/美元/XML 特殊字符；连续完成通知、进程提前结束/正常退出；有必要再注册独立测试 AUMID 做 toast。 | 实际画面/回调与 submitted 分开；无多余 PowerShell/console 窗口；关闭或阻断通知时回合照常完成且记录结果；点击不会误起新业务任务。 | NIM_DELETE/停消息线程/释放 icon；若测试 toast，删本 AUMID 通知历史和本次 shortcut/COM 注册，只处理 manifest 记录的键。 |

WC-01～WC-11 是首轮最小场景组，可共享一个 worker/fixture。依赖与权限前提不满足的候选明确 not-run，不能临时改用其它隔离层替其填 passed。

### 9.3 需要隔离环境的补充项

- **定时登录/网络：**在一次性 Windows 测试用户或 VM，分别 InteractiveToken/S4U/Password（若该候选确有必要且实验身份具备前提）测试已登录、锁屏、注销。只用合成值；分别测本地匿名 TCP、受控 HTTPS、需用户凭据的代理/UNC、CredRead 与 profile 文件；不得将官方 S4U 限制扩写为本轮实证 HTTPS 一定失败。不得为实验保存真实 Windows 密码、改企业策略或关闭服务。
- **时区/DST/漏触发：**先给 matcher 注入 clock/zone 数据做 gap/fold/跨年/时区变更序列；OS 实际跨 DST 与休眠/关机漏触发放到可回滚 VM 快照，记录并恢复原时间、时区、电源状态和任务 XML。不能改日常主机时钟获得“快速证明”；纯函数通过不算真实 Scheduler DST 通过。
- **网络与隔离覆盖：**回环只是最小可重复基线，不证明完整 Internet/LAN/UNC/代理/IPv6、设备与所有内核攻击面。需要外网时用受控测试 endpoint/nonce，不访问真实模型或凭据。WFP、Sandbox、containers、Sandboxie 仅在其候选被继续选择后另立安装/恢复步骤，在 VM 快照验证，不在本静态研究或原生首轮暗装。
- **电源/通知/剪贴板体验：**AC/DC、Modern Standby、用户主动 Sleep、勿扰/关闭通知、Explorer 重启和真实 WT 图片事件各自保存实机观察。更改系统设置只在一次性环境，完成恢复快照；通知 API 成功不等于用户看到，系统 request 存在不等于永不休眠，clipboard API 有图不等于终端产生事件。

## 10. 本轮交付状态与后续收口

本轮完成静态源码/API/候选前提研究，提供了可执行到“输入—实际尝试—观察—清理”的探针设计；没有产品实现、自动运行通过或用户体验验收结果。API 文档所列的最低系统版本不等于 RuoCun 的发布支持下限；最终支持范围须与选定 Python、wheel/standalone 依赖及实际 Windows 环境一起验收。没有新范围冲突，也没有需要重新询问 Windows 全功能、核心 Python 或其它平台顺序的问题。

后续由 [用最小 Python 探针验证 Windows 平台能力](../issues/17-windows-capability-experiment.md) 产生实际证据，再据此形成平台方案。应优先解答：AppContainer 能否以窄授权运行必需主机工具链及两种网络模式；write-restricted 路线能否完整限制外部写且以可接受前提补网络；系统定时采用何种 cron 方言/映射/登录语义；辅助端口在最终 wheel/standalone 产物中能否完成其生命周期。这些是后续技术收口，当前不替路线决定票预先定案。
