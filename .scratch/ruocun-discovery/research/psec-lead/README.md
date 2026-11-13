# ProcessContainer 原生路线线索（未选型）

2026-11-05，主代理在等待独立复核期间进行只读补充调查。研究分支`research/d10-psec-lead`本地保留，不合并；主会话可收录本报告与证据。本材料不解决D10、不代替D17复核，也不表示文件/网络隔离已通过。

一手来源固定到Microsoft MXC提交`f4aa3fd59306d140ccf7448e914306fc6cdb74d0`（`git ls-remote https://github.com/microsoft/mxc.git HEAD`），只下载文档/接口源码供阅读，未安装或运行其SDK。该项目MIT许可；这里只记录接口事实，不移植其业务实现。

- [接口及消费方式](https://github.com/microsoft/mxc/blob/f4aa3fd59306d140ccf7448e914306fc6cdb74d0/README.md)：存在原生executor和非Python SDK，需核实Python窄FFI或原生底层依赖的可用边界，核心仍须Python。
- [OS支持表](https://github.com/microsoft/mxc/blob/f4aa3fd59306d140ccf7448e914306fc6cdb74d0/docs/backends/process-container/os-version-support.md)：文档列24H2/25H2构建26100/26200.9278及后续能力分界；实际导出和请求能力探测优先，不能单凭版本号判断。
- [网络策略](https://github.com/microsoft/mxc/blob/f4aa3fd59306d140ccf7448e914306fc6cdb74d0/docs/backends/process-container/networking.md)：描述每环境的WFP、host loopback及API能力；这是进一步验证候选，不从文档推定本机行为。
- [FFI契约](https://github.com/microsoft/mxc/blob/f4aa3fd59306d140ccf7448e914306fc6cdb74d0/src/mxc-sdk/src/backends/process_container/common/secenv.rs)：系统`processmodel.dll`、Create/Query/Version/Close导出，PSEC FlatBuffer和进程启动属性。只借公开仓库定位API，不把Rust/Node业务作为Python运行依赖。

下载字节hash见[download-sha256.json](download-sha256.json)，只读缓存位于根工作区`.worktrees/reference-mxc-f4aa3fd`。缓存可按上述固定提交重取。

## 本机只读观察

[probe_support.py](probe_support.py)仅以System32查找规则加载系统DLL、查询只读support/version；未创建安全环境/进程、未改变DACL、防火墙、账户、组件或策略。运行命令：`python .worktrees/reference-mxc-f4aa3fd/probe_support.py`，结果原字节收录为[read-only-support.json](read-only-support.json)，脚本SHA绑定在结果内。

本机26200.9711 Professional/25H2：四个导出存在；support返回HRESULT 0、flags=15；version major=1查询成功、available=1、minor=1。只说明可进一步调用的前提，**不证明安全环境能创建、Python/工具链能运行、允许/拒绝或生命周期正确**。

## 最小后续问题

应以独立合成工作区验证PSEC能否在普通用户下实现来源要求：允许根/临时目录可写、外部写和reparse逃逸拒绝、真实主机工具读取、联网与no-net、宿主/自身/后代回环、真实Job取消及环境关闭。不安装组件、修改全机ACL/防火墙或运行audit无隔离模式。失败须fail-closed；不能偷偷回退AppContainer或普通Shell。

若实测可行，D10/D12再决定绑定、最低OS、打包与兼容；若不行，保留错误和前提，再评估真正需要用户取舍的范围或安装条件。
