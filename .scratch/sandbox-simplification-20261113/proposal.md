# 若存沙箱简化讨论归档

状态：已收口；用户选择保持现有沙箱，Docker 与 Windows 沙箱改造暂缓。
日期：2026-11-13。
最终决定：[ADR-0019](../../docs/adr/0019-learning-oriented-sandbox-goal.md)。

**最终决定：保持现有实现，不为进一步简化而重构沙箱，暂不开展 Docker 或 Windows 隔离改造。** 现有沙箱与 DAO 采用一致的轻量包装思路，能力边界继续按 ADR-0008。下面的开源分析与 A／B／C 路线保留为历史研究，本轮均未采纳，不形成后续实施或体验验收任务。

## 已确定的目标与研究范围

用户明确：个人维护，以学习有代表性的主流 harness 设计为主要目的，希望控制复杂度，并具有有限而真实的沙箱能力。

研究曾将“精简”理解为缩小保留能力的范围，同时保持执行结果、失败与取消含义真实。用户最终选择保留现有能力，本轮不做功能收缩；已有正确失败处理继续保留。

“主流”在本次研究中只指有代表性的公开项目采用并能从源码核查的设计，不表示市场采用率，也不保证任何项目的短实现自动满足若存已有契约。

术语按当前产品区分：

| 术语 | 当前含义 |
|---|---|
| 审批 | 决定某次工具操作是否获准执行 |
| Shell 沙箱 | 只约束经该入口启动的命令及子进程，独立文件工具与扩展另计 |
| 外层隔离运行 | 让若存进程及其本地工具在一个受限环境中运行；共享文件和外接服务仍有各自权限 |
| 工作树隔离 | 用独立 Git 工作目录组织改动，不是 OS 沙箱 |

## 先核查若存当前究竟复杂在哪里

当前 [platform/sandbox.py](../../src/ruocun/platform/sandbox.py) 为 87 行，主要是开关、Seatbelt／bubblewrap 参数和不可用时报错。它已经是很小的包装模块，尚未实现 Windows OS 沙箱。删除这部分并加入 Docker 管理，不会自然降低整体复杂度。

邻近的 shell_plan、process_tree、managed_shell 和 shell_runner 分别承担执行方言、冻结工作目录与环境、输出与停止、后台控制和恢复。它们不能全部归入“沙箱代码”，也不能在未改变功能范围的情况下直接删掉。

这里必须修正前一份调研报告中的若存适用前提：**现有正式若存不能直接装入 Linux Docker 后就保证正常运行；连普通会话也存在明确的 Windows 平台门禁。**

| 当前源码事实 | 位置与影响 |
|---|---|
| 普通会话启动先准备受控 Windows SQLite DLL | [agent/runtime.py:579](../../src/ruocun/agent/runtime.py#L579)；[session/runtime.py:115](../../src/ruocun/session/runtime.py#L115) 非 Windows 拒绝 |
| 正式会话的 owner 身份需要 Windows 进程身份查询 | [session/process_identity.py:47](../../src/ruocun/session/process_identity.py#L47) 与 [83](../../src/ruocun/session/process_identity.py#L83) 对非 Windows 拒绝 |
| 可恢复后台执行和 runner 目前限定 Windows | [managed_shell.py:269](../../src/ruocun/tools/managed_shell.py#L269)、[shell_runner.py:394](../../src/ruocun/tools/shell_runner.py#L394) |

因此，“仅禁用后台就能在 Linux 中跑前台正式 CLI”也没有成立。Linux 前台底层进程函数的存在，不等于正式会话链已经跨平台。当前结论来自源码检查，不是容器内实测。

## 最值得学习的三份开源参考

| 参考与固定版本 | 学什么 | 不直接照搬什么 |
|---|---|---|
| Pi coding-agent，`d36266e06669c6991a7c9509d1da04d18d30378d` | [官方 Plain Docker 方案](https://github.com/earendil-works/pi/blob/d36266e06669c6991a7c9509d1da04d18d30378d/packages/coding-agent/docs/containerization.md#L30-L80)：镜像准备工具链，显式共享项目，专用卷保存配置与会话，普通代理入口在容器内运行 | 示例的挂载、身份和凭据参数不能当作通用安全策略；它也不能消除若存自己的 Windows 平台依赖 |
| mini-swe-agent，`04d809ceab9df28f9adaed044884180159172930` | [Environment 接口](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/__init__.py#L61-L70) 与 [主循环调用](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/default.py#L154-L157)：主控只知道执行与结果，不知道本机还是容器 | [Docker 执行](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/docker.py#L101-L136) 与 [清理](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/docker.py#L153-L161) 很短，但不建立若存完整的真实取消、后台和跨重启恢复契约 |
| OpenCode，`7e441d348ea0dc951e470dbd84d6c3a0df34aa9a` | [安全声明](https://github.com/anomalyco/opencode/blob/7e441d348ea0dc951e470dbd84d6c3a0df34aa9a/SECURITY.md#L15-L19)：将应用权限提示与容器／VM 隔离分开，隔离可以由部署提供 | 不据此声称普通容器有任意多租户强隔离保证，也不把没有内置沙箱当作权限系统缺失 |

参考优先级：Pi 的整进程部署职责作为主参考，mini 的小接口作为辅助阅读，OpenCode 用来校准审批与隔离的边界。它们说明这种设计有公开实践，不能证明所有主流代理都使用它。

## 历史候选的职责分析

本节是形成最终决定前的比较，不是当前改造计划。

| 动作 | 具体建议 | 理由 |
|---|---|---|
| 保留 | 现有审批、执行计划、真实退出结果、明确拒绝不支持的平台 | 这些是保留范围内的正确行为，不是沙箱平台的额外花样 |
| 暂保留 | 现有约 87 行的原生 Shell 包装，按实际能力说明 | 目前没有代码复杂度证据支持为简化而重写它 |
| 简化 | 把隔离模式的操作系统、任务类型和生命周期限定为一个清楚的组合 | 减少支持范围比复制多后端框架更有效 |
| 外置 | 项目共享、工具链、配置／会话存储和环境启动 | 核心不需要同时维护 Docker API、远程文件协议和容器调度 |
| 暂不新增 | 内置 Docker 工具后端、容器池、云调度、跨机器恢复、自研 Token／WFP／ACL | 它们增加职责和接缝，尚未服务明确的学习范围 |

外层整进程方案的最小运行约定：只开放指定项目或项目副本；为配置与会话提供专用目录；凭据按本轮需要传入；明确网络是否允许；隔离启动失败就失败；停止环境时核实内部工作已结束。普通可写挂载会修改宿主项目，这不是保护当前工作树的机制。依据：[Pi 共享限制](https://github.com/earendil-works/pi/blob/d36266e06669c6991a7c9509d1da04d18d30378d/packages/coding-agent/docs/containerization.md#L18-L28)。

## 历史候选路线（本轮未采纳）

**A：保留当前 Windows 产品，外层使用独立 Windows 环境。**

在单独 Windows VM 中运行现有若存，概念上可以沿用 Windows DLL、进程身份、Job 和 IPC，避免仅为 Docker 改造正常会话链。复杂度主要转移到环境部署、资源、项目传入和结果带回。它属于外层隔离部署，不是内置 Windows 沙箱实现；需要后续实际验证，不能将架构可行当成已交付。

如果选 Windows Sandbox 这类临时环境，还必须接受关闭环境后内部状态丢失，并为需要保留的结果显式安排输出目录。需要长期会话和后台接回时，持久 Windows VM 比临时环境更贴合现有承诺。来源：[Microsoft Windows Sandbox](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/)。

**B：明确设计 Linux 学习版，再采用 Pi 式外层 Docker。**

如果用户愿意为低复杂度缩减执行能力，可以把 Linux 可兼容项目作为学习版范围，先明确保留哪些会话与执行能力，再准备一个固定镜像和简单启动入口。后台与跨进程恢复是否保留，需要单独决定。

这条路线的职责划分最适合学习容器化 harness，但当前若存仍需要处理 SQLite 运行库、进程身份、私有持久文件等平台依赖；保留后台还要处理 runner／IPC。它是运行时范围与平台的改造，不能包装成“修改 sandbox.py 几行即可”。具体最小改动要在用户选择后继续收敛。

**不优先选择 C：Windows 主控＋内置 Linux Docker 工具执行。**

此时命令、文件路径、配置、取消和恢复会横跨两套环境。只把 Shell 改成 docker exec，又会留下仍在宿主运行的文件工具与扩展。若要求边界完整，就需要更完整的远程工具与生命周期协议，违背本轮控制复杂度的优先目标。SWE-ReX 的 [启动](https://github.com/SWE-agent/SWE-ReX/blob/5c995c365dfb1fd5bc56fda688be5d8538f9931f/src/swerex/deployment/docker.py#L233-L284) 与 [停止](https://github.com/SWE-agent/SWE-ReX/blob/5c995c365dfb1fd5bc56fda688be5d8538f9931f/src/swerex/deployment/docker.py#L285-L309) 展示了这些额外职责。

## 最终决定与讨论收口

已确定：个人维护、harness 学习、控制复杂度、隔离能力如实说明；当前沙箱本体已经精简，保持现状。

此前的平台优先级、部署复杂度、后台取舍与共享方式问题，随用户选择不开展本轮改造而关闭，不再等待回答。

保留当前 Windows 运行、会话、后台与恢复能力；不增加 Docker 后端、外层 Windows 隔离部署或为此进行的 Linux 学习版移植。原候选只供将来用户提出新需求时回查。

决定依据是现有设计职责清楚、直接复用外部沙箱工具，未发现为了降低复杂度而必须重构的理由；这不是对所有平台隔离效果的新增实测结论。

## 文档与实施状态

CONTEXT.md 与 ADR-0019 已记录最终决定，ADR-0008 的现有能力约定继续有效。[讨论票](issues/01-sandbox-design.md)以决策收口标记 resolved，用户体验验收为 not-required。

本轮仅更新工程记录，产品代码与既有验收结果保持原状；未安装、运行或验收候选隔离环境。没有由本文产生的待实施任务。
