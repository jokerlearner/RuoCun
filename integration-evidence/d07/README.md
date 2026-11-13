# D07 fresh merger 独立复核

日期：2026-11-05。分支 `merge/d07-distribution`；隔离 worktree `D:\java supplement\Firstcode\RuoCun\.worktrees\m07`。结论：**候选的 wheel/sdist 与 Windows onedir 合成分发闭环可收录；onefile 继续为 ENV／运行未证实，产品和最终终端验收未完成。** 本轮未发现需要改候选行为或测试期望的实质问题。

## Git 与输入

- 从 clean `integration/ruocun-migration=6fbbda843979de465d94e525669870577e2a9c82` quiet FF 正式 ref，再 quiet no-ff merge 候选 `fc2fd117576e8872cc1a9f5fd327464bf6f2710e`。
- 候选 merge：`d698f5dd8cb1ddeed1dcf14d8328ebf7062837c3`。本报告之后的封存／同步提交见分支 tip 与后续同步记录。
- 已读根 AGENTS／CONTEXT、领域／issue 工作流、ADR-0001／0004、迁移基线、规格 R-15/T-N1/T-N5、PKG-01～06、对应发布项、D07 票与分发源码／锁／报告，必要 D06／D19 报告。本复核未自行修改公共 Status、地图、规格、矩阵；i07 未触碰。
- [platform.json](platform.json) 绑定本轮执行前的源码、锁、许可、文档等输入 SHA256；复核后这些原输入逐字节未变。忽略目录内的新 SQLite DLL 来自固定官方 URL，经 archive SHA3 与 DLL SHA256 验证，见 [download.json](download.json)。未调用会覆写原 candidate／许可／旧证据的准备和封存脚本。
- [historical.json](historical.json) 独立核验旧 `n/i3/s3/r5c/g5` 的 stdout/stderr hash 和 122 个输入快照；冻结源归档六成员与 manifest／source-contract 全部一致。旧 r5 仅作为明确脱敏审阅副本理解；未读取 `.cache/private/r5.dpapi.bin` 或任何私有原始材料。

## 本轮实际执行

所有测试、构建和安装子进程均从 [review.py](review.py) 的显式环境白名单启动。HOME／USERPROFILE／APPDATA／LOCALAPPDATA／TEMP／pip cache 均指向合成区域，未继承模型或账户变量。Windows build 26200、CPython 3.11.9 x64，token 未提权。bootstrap 的 `platform.machine()` 为空，另用真实 `GetNativeSystemInfo` 取得 AMD64=9，见 [native-platform.json](native-platform.json)。主机原本有 Python；PATH 屏蔽只作为查找隔离，不表示 clean VM。

独立构建 venv 与测试 fixture 位于真正仓库外中文空格路径：

`C:\Users\PC\AppData\Local\Temp\RuoCun-m07-D07-中文 空格-20261105`

| 复核项 | 实际结果与证据 |
| --- | --- |
| 锁／标准构建 | 新 venv 按 hash lock 安装并下载 wheelhouse；从 sdist 构建 wheel、再直接构建 wheel，逐字节一致。wheel `py3-none-win_amd64`、`Root-Is-Purelib:false`，内置 DLL 与固定候选相同；sdist 含 DLL。见 [artifacts.json](artifacts.json)、raw `00`～`05`。 |
| pytest 计数 | **5 passed / 1 skipped，4.57s**。四个 CLI 测试函数（版本/参数、SQLite/资源、三种生命周期、UTF-8）与一个 wheel 测试函数通过。唯一 skipped 是要求显式选择的 onefile；没有执行被拒产物。此计数不包含下面两个独立脚本。见 raw `06-pytest/stdout.bin`。 |
| 仓库外 fresh venv | 真正仓库外 cwd／中文空格新 venv、无 PYTHONPATH；临时隐藏本 worktree 的 pkg 后运行；18 条实际命令全部符合预期。空 wheelhouse 缺依赖安装 exit1 可解释，完整离线安装成功，无 pytest/build/Hatchling/PyInstaller；版本 exit0、非法参数 exit2、启动冲突 exit70、中文 emoji pipe、PATH 冲突均通过。见 raw `07-install-probe/receipts/summary.json` 与 `commands.json`。源码随后原路径原字节恢复。 |
| 升级／卸载 | 错误 hash 升级 exit1 后仍为0.0.1且配置/DB hash不变；0.0.2升级成功且外置合成数据原字节保留；卸载命令／模块移除而配置／DB仍原字节保留。见同一安装 summary 的五组 before/after。 |
| onedir 独立重建 | 由新构建 wheel 安装后冻结，中文空格产物路径；根 incidental sqlite DLL 在本票 artifact 中明确 pin 为固定候选，见 [pin.json](pin.json)。5 个 CLI 场景及 SQLite／D06 底层导入通过，仓库外 cwd，PATH 中 python/node/bun 均不可见。见 raw `08`～`10`。 |
| onedir 内部角色 | worker／restart／协作取消共三场景；同 exe 用明确内部角色再入，未传 `-m`。owner 先退出，child 才 release/cancel；每场景恰有 owner+child 两条 start，无递归入口。每个父子都实际核对 SQLite source ID／DLL／驱动、WAL/FULL=2、提交/回滚/重开/完整性和资源。取消场景确认 canceled；不把它等同强杀或 Ctrl+C。完整 argv 见 [frozen-argv.json](frozen-argv.json)，对应原 runtime 收据在 raw `10.../receipts/p0..p2`。 |
| runtime 身份／退出 | 源码测试6个、onedir6个，共12个去重 runtime PID+创建时间，均由 observer 独立保留 Win32 handle、核对实际 runtime 身份并等待同句柄 exit0；不是把 venv/PyInstaller launcher PID当作 worker。各 cleanup.json、observed.json 保留结果。 |

本轮 wheel SHA256 `53cebe83e58b3ad8ab9fe41f2d1c19e939f5b363a2c6274f2e72ac7145baf790`，sdist SHA256 `e1b5c083fb59a1a511a183ad15e330afc70e99f8bc2a20e44e8abd49b84c4e33`，均与原候选一致。本轮 onedir exe SHA256 `92ca179ea31792babd3fae046bce3a82d211d293f7a5fa6e5004879a90272357`；[逐文件清单](onedir-manifest.json)绑定整个新产物，未声称 freezer 工具链可重现。

## 失败与未验边界

旧 `r5c` 保留共享解包目录清理失败的真实 red，旧 `g5` 保留修正版 onefile 首次 CreateProcess WinError4551 的真实 ENV。两份原 raw hash 均已核对，本轮未重新构建／运行 onefile，也未改名、换位置或改安全策略绕过。默认 pytest 的 skip 不把 onefile 算 green。

本次只复核隔离探针：不是完整 RuoCun 产品打包、产品schema升级/恢复或长期runner升级/receipt兼容；未验证真实parser、凭据读写、外部Hook/MCP/LSP、系统计划任务、无Python/Node新账户/VM、签名安装器或安全策略全矩阵。D06只实际验证 Win32输入/输出类导入、Rich Markdown与wcwidth等依赖；合成grammar只是占位。D19只复用固定运行库与必要 SQLite 基础契约，不重复其强杀恢复全矩阵，不宣称复现罕见WAL-reset问题。Windows Terminal／IME／粘贴／缩放／焦点图形仍按ADR-0004交77/78/85集中人工验收；Linux/macOS/ARM64及其它Python版本未验。

## 证据封存与实际清理

[raw.zip](raw.zip) 保存本轮完整11次顶层命令记录／原始字节、安装18条命令输出／argv与生命周期收据，共165成员；[raw-manifest.json](raw-manifest.json)逐成员列路径、size和SHA256，封存后逐个解压到内存核对。ZIP SHA256 `c43a6902f40d05c51c26a747ac245dff8abd871df7e6866a08a5a408fd4ec30b`，107060字节。原候选证据未重写／删除；新raw目录原地保留但忽略，版本化ZIP可直接内存查看，无需长路径checkout。

已确认本轮全部12个受观察 runtime 退出且句柄关闭；没有遗留活动任务进程，不扫描／终止其它进程。pkg临时隐藏已恢复。独立构建venv、安装fixture、wheelhouse、忽略cache及本轮raw留在本机供复核，未进行额外磁盘清理，也未遇清理自动拒绝。没有读取或删除原i07私有缓存。

[scan.json](scan.json) 静默扫描本轮证据和原版本化证据中的当前真实敏感环境值：只记录是否存在待扫描值和是否命中，结果无匹配；不记录变量名／值或整个环境。最终提交前再核验暂存blob与工作区字节、ZIP成员hash以及敏感值扫描。

## 最后集成同步

独立证据提交 `c00ce418083cabbedea9f0de7efeb4f7f76bff6d` 后，按主会话要求 quiet no-ff merge 正式集成 `4048910744a7aab60a9bc75d721df9262a403292`（D17技术材料及其状态／20领取），同步 merge 为 `631def4a27507541b89e163ab7409440c74f7778`。主会话已经登记 D17 独立hook总exit1限制，本报告不重述为D17整体green。

合并提交相对已验提交的 D07源码／锁／原证据及本轮已提交证据**零路径差异**；仅做相关输入字节、Git来源链与路径上限复核，复用已通过分发链。见 [sync.json](sync.json)。同步后的最终封存tip由交付消息给出；没有为无关D17材料重跑构建／安装／生命周期测试。
