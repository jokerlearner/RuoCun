# B-r1 固定构包与仓外安装

状态：固定包、成员绑定和纯安装技术出口完成；后续manual helper发现新空工作区导出缺父容器的真实缺陷，R1不是最终通过候选。原包/原回执保留，已按主协调批准单独准备R2；R1默认全量仍由主协调安全收尾。
日期：2026-11-13。未提交Git，未修改仓库`.venv`或全局Python，未触碰真实用户会话。

## 固定输入

- 已按主协调正式冻结指令保存 `D:\rcb-dd7453\r1`，包含完整受控`src/ruocun`和包配置/README/许可/锁。
- 来源类型为`frozen-working-tree`，不是`git archive HEAD`。输入指纹：`e4a12606737e3234bb7804d48b7377a1caa09d8312054e0476f5a717ccf8fd61`。
- [逐文件输入与字节数](t07-r1-inputs.json)、[冻结/构包原始回执](t07-build-raw/t07-freeze-r1/command.json)。冻结时验证前后工作区字节稳定，复制后再次核对。
- 基于冻结副本一次构造sdist，再从sdist构造wheel；另做直接wheel核对。`hatch_build.py`保持`py311-none-win_amd64`及非purelib标签。

## 产物与绑定

- wheel：`dist/compaction-b-r1/ruocun-0.1.0.dev0-py311-none-win_amd64.whl`。
- sdist：`dist/compaction-b-r1/ruocun-0.1.0.dev0.tar.gz`。
- [交付副本SHA](t07-r1-deliverables.json)、[完整绑定报告](t07-r1-artifacts.json)、[绑定命令](t07-bind-r1/command.json)。
- 314个产品成员在冻结源码、sdist、重建wheel及实际纯安装目录逐字节一致；直接wheel与sdist重建wheel的SHA相同。
- 实际核对3份许可文件、依赖metadata、版本和Windows包标签；受控SQLite归档与实际3.54.1运行库门禁通过。
- 包中不包含tests、`.scratch`或Git材料。绑定脚本复用现有integration断言，但不会把脏工作区的HEAD伪称为产品源码身份。

## 仓外环境

| 环境 | 实际解释器 | 内容 |
|---|---|---|
| pure | `D:\rcb-dd7453\pure\Scripts\python.exe` | 仅哈希锁runtime依赖及固定B-r1 wheel，无pytest。 |
| QA | `D:\rcb-dd7453\qa\Scripts\python.exe` | 官方哈希开发/runtime闭包、B-r1 wheel、非editable测试支撑wheel。 |

开发wheel全部从官方PyPI按固定锁及`--require-hashes`下载，59枚有效离线闭包留于`D:\rcb-dd7453\dev-wheelhouse`；mypy采用锁允许的官方pure wheel，避免既有WDAC编译扩展问题。
运行时纯环境消费现有`.cache/b06-runtime-wheels`的44枚闭包。未更新任何pin或锁。[离线wheel指纹](t07-wheelhouse.json)
QA与pure均`pip check`通过；pure真实`--version`、`--help`通过。每个工程进程使用白名单，HOME/AppData/ProgramData/TEMP均指向合成路径；不继承账户、Hooks、MCP或真实凭据。

## 普通产品入口独审

- 独审在QA安装执行已有T06两案：[2 passed](reviewer-t06-installed/command.json)。
- 独审在**不含pytest的pure解释器**执行同两案：[2 passed](reviewer-t06-pure/command.json)。外层pytest只负责启动fixture，产品严格用pure Python `-I -m ruocun`，无src loader。
- 两案覆盖普通CLI、本地HTTP/SSE、多轮和两次压缩、关闭后第二进程恢复、原文回查/导出，并验证失败压缩保原文停止。
- [pure来源与27个受审产品文件指纹](reviewer-pure-fingerprints.json)证明安装路径及冻结B-r1字节一致，非借用仓库源码。

## 尚待集中收口

manual helper在没有预建`.ruocun`的新空工作区复现`AtomicFileError`：两种导出入口只创建`exports`私有子目录，缺少父容器时失败。修复不得通过夹具预建父目录掩盖。R2只增加两入口“仅缺失时创建父容器”四行，见[t07-r2-pending.md](t07-r2-pending.md)。

主协调负责最终默认全量与集中静态、跨票验收表及发布说明。若产品字节需修，另建B-r2而不覆盖B-r1或回填本候选全绿。
真实模型摘要质量、供应商缓存命中和Windows Terminal体验不属于本页纯安装通过结论。
