# 03复核后修复：真实进程退出与清理记账

本轮延续03；原候选 `4a833cd703ae9c22669eb759ab2781139964afef` 未通过独立进程故障复核。已完整合入 `25c56bc04428f9c5147a513471c292b95473840e` 的独立失败证据（同样包含正式集成 `46c8243650333e61325346d367068cad0c93ebfa`）；旧证据、断言与raw没有改写。正式集成的增量是平台路线/依赖与实施记录，没有相关产品或测试输入变化，不为这些文档重跑来源12项。

## 问题与修复

独立复核的 `communicate` OSError 在真实 Popen 已启动之后触发，候选返回时真实自有 sleep child 仍运行，却写 `command_joined=true`。KeyboardInterrupt 子进程虽已停止，报告却把真实退出码写成null。原失败材料位于 `../../../integration-evidence/03-boot/`（从本目录回到 `.scratch/ruocun/` 后）；其提交/原始字节保留，不能将后来的修复结果回填成第一次通过。

现在 execute 的 `finally` 统一收口同一 Popen 拥有的进程和stdout/stderr：异常后查询、必要时请求终止、同一拥有对象等待最多5秒，等待异常后尝试同一对象poll确认，再逐一关闭管道。不会按裸PID重新查找/杀进程，不把 kill 请求当作退出证明；没有引入业务 runner、进程树管理或隐藏产品入口。

case `exit` 保存实际观察到的子进程码，`logical_exit` 表示验收逻辑结果，取消为130。记录 PID、可执行文件、启动观察单调时间及 Popen 拥有关系；诊断保留操作、异常类型、errno/winerror，避免复制任意异常文本。`command_joined`、`streams_closed` 根据实际结果；无法确认退出/关闭就明确 `cleanup-failed`、非零，并停止后续case。suite汇总使用真实case清理结果，不再常量写true。取消在communicate或退出确认阶段发生都不能被当作成功；实际exit可为0/1/平台终止码，与逻辑130独立。

## TDD和实际回归

测试在已确认的 subprocess 系统边界投递受控Python API异常，执行的都是本轮自有真实 Python 子进程。**没有声称复现真实内核/管道损坏、操作系统拒绝终止或终端Ctrl+C。** 测试finally保留真实Popen对象，独立kill/wait/关闭本测试创建的材料，红测也不泄漏；受控wait/poll不可观测案例明确由测试在外层清理。

| 真实边界与独立预期 | red | green |
| --- | --- | --- |
| communicate OSError后 execute 返回前真实子进程必须停止/等待，管道关闭 | `r2-00-red-pipe`：child仍运行、joined却true | `r2-02-green-pipe`，最终默认回归 |
| 取消实际child exit保留，逻辑130，后续case not-run | `r2-04-red-cancel-fields`：实际退出码被写null | `r2-06-green-cancel`，最终默认回归 |
| 真实child的wait/poll观察均被受控异常阻断时，明确cleanup-failed/nonzero/false，保留身份诊断 | `r2-07-red-unconfirmed`：原清理异常直接逃逸 | `r2-09-green-cleanup`，最终默认回归 |
| 真实CLI已完成、退出确认阶段投递KeyboardInterrupt，不能成功 | `r2-16-red-cleanup-interrupt`：原结果success/0 | 最终默认回归：child实际exit0、逻辑130、其余case不运行 |

第一次取消测试夹具在每次communicate都投递中断，导致pytest中断exit2，原 `r2-03-red-cancel` 留存；随后将投递限定为一次，得到明确的实际exit丢失红测。`r2-10-ruff` 的新测试import排序错误也保留并修正。没有修改原25项断言。

最终安装新支撑wheel后：**默认pytest29 passed / 3 deselected**，其中新增4个进程故障回归；Ruff check . exit0，mypy strict **11 files** exit0；根标准隔离build、支撑标准隔离build、pip check均exit0。Windows/CPython3.11.9 x64及五工具版本/18包hash闭包沿用原固定输入，无依赖或版本pin变化。

新建仓库外中文空格 `C:\Users\PC\AppData\Local\Temp\RC03-1105 中文 空格\support-r2` venv，只从本轮wheel安装产品与支撑，无源码/PYTHONPATH、无开发工具依赖；实际 `python -m ruocun_acceptance offline` 调用已安装产品，**4 case passed**，每个进程exit确认和流关闭都为true。相关命令为 `r2-18/19/22/23/24`。

产品CLI源码未变；原 source oracle **12 passed** 继续作为旧轮实际结果，未无关重跑。新支撑wheel内 oracle/driver.py、network_guard.mjs、来源测试和开发锁都对照原输入hash确认未变。Source Node24历史ENV、真实模型及最终终端体验仍保持原边界。

## 产物与封存

本轮产品 wheel SHA256仍为 `feeb2e2d77d3aaeede79681536f90a8955faef8fbc68d054928626ab84e99a8c`。新支撑wheel为 `58cf0ef5decc4f9df4ee57a562e0ec2e84ea57ff91382e172bf748b69ed11e21`，支撑sdist为 `59eb22114b0e7733ea971c4f5369b36c511c5e5434b8f1eb25bdda54d9e2a00a`。

产品sdist本轮hash `f6e8d744edd34cf1a38892bf2690369673cf8eb42a190098945b0383ee5a64e4` 与首次产物不同；逐成员对照仅 `.gitignore` 和 README 的CRLF→LF，规范换行后字节相同，见 [sdist-delta.json](sdist-delta.json)。这是原候选提交前字节检查的换行规范化现于重建包体现，没有新增产品行为或改旧sdist/raw。产品wheel metadata读取文本后不受影响，逐字节相同。

[commands.json](commands.json) 与 [raw.zip](raw.zip) 保存本轮25条实际命令、99个raw成员，其中15份fault receipt记录各次真实子进程退出及测试最后清理；[raw-manifest.json](raw-manifest.json) 绑定逐成员hash并内存解包重验。四个本轮成品另封 [artifacts.zip](artifacts.zip)，hash/member见 [artifacts.json](artifacts.json) 与 [artifact-manifest.json](artifact-manifest.json)。原66命令/270raw及独立merger失败封存保持原字节。

[inputs.json](inputs.json)、[result.json](result.json) 记录修复输入、同步范围与统计；[scan.json](scan.json) 对代码、证据及原始成员静默扫描当前真实敏感环境值，无命中，不记录变量名称/值。所有命令和child仍是环境白名单、合成HOME/config/TEMP。进程测试本轮自有子进程均由测试finally确认退出，外部安装/venv/wheelhouse/raw保留；不清理别的worktree/用户数据，不尝试系统策略调整。

仅收口03开发驱动；不启动04、不扩大业务runner、真实模型或最终终端范围，公共状态由主代理维护。
