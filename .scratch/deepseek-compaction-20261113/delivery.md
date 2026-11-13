# B方案交付：DeepSeek风格压缩与完整原文归档

日期：2026-11-13。候选：**B-r3**。实现、自动出口及独立复核完成；Windows Terminal视觉/缩放与用户整体体验为`pending`，真实模型质量未验。

## 交付内容

- 主/子执行共享最终请求预算、近期原文保留、完整工具组切点、头尾裁剪、旧摘要重整、缩小门禁及有界超限恢复。
- 原文、消息版本、派生来源、活动投影和幂等回执沿现有SQLite同事务确认；失败/取消/未知确认保留现场，不重放历史操作。
- 用户`/archive list/read`、范围绑定的只读`ArchiveRead`，完整/当前投影导出；主子隔离、fork精确继承、分支材料闭包、clear/rewind边界和会话共同清理。
- 显式备份离线升级到storage_version3，旧writer拒写，旧摘要缺口明确标识。
- 修复新空项目导出父目录缺失，以及压缩后重启再次压缩丢失任务pin；明确空TodoWrite仍清空，不复活旧pin。

使用与升级：[发布说明](../../docs/release/deepseek-compaction.md)。架构决定：[ADR-0020](../../docs/adr/0020-compaction-transcript-archive.md)。来源为固定MIT DeepSeek Harness `e8f7b93a344964de3dca1ace9e72b6e4d6de87cb`，许可随包附带。

## 固定产物

- [B-r3 wheel](../../dist/compaction-b-r3/ruocun-0.1.0.dev0-py311-none-win_amd64.whl)，SHA256 `3b34d7366716c4ec14fd01ef2b629cf26ef84aa11273ac513012b3fb2808baa4`。
- [B-r3 sdist](../../dist/compaction-b-r3/ruocun-0.1.0.dev0.tar.gz)，SHA256 `1b5c2e84506fe7f66e38ad7761b95afa616fbeb00635fa4f11168fa555d300c6`。
- [完整输入清单](evidence/t07-r3-inputs.json)，总指纹`5f530430e385fef8b05837f06165d5c8cdd3c308cc70c87bdd52bfcab0744486`。
- 初次构包验证使用仓外pure/QA的`D:\rcb-dd7453`环境，未替换仓库`.venv`。后续用户明确授权更新日常入口，现已切到`C:\Users\PC\Apps\RuoCun\venv-compaction-b-r3`，配置及6个旧会话已保留并验证；见[当前部署](deploy-current.md)。
- 当前工作区有大量原有未提交改动，按文件副本和指纹保留；本轮未创建Git提交。

## 自动结果与复用边界

| 检查 | 实际结果/证据 |
| --- | --- |
| 唯一完整源码回归 | B-r1的[f2](evidence/f2/command.json)：1734 passed、1 failed、4 deselected，470.42秒；不是全绿，不删除原失败 |
| 原失败处置 | 旧目录限制52项，B新增archive后53项。保留原52来源项及排除plugin的断言，新增native archive断言。R2安装包[B05/目录/包/原子文件25项](evidence/r2-target/raw/r2-catalog-export/command.json)通过 |
| 新空项目导出 | R1的manual-prepare/2真实失败；R2/R3原空项目公开CLI预制通过，未预建`.ruocun`，不把诊断对照当通过 |
| Todo重开回归 | [独立red](evidence/reviewer-todo-red/command.json)→[green](evidence/reviewer-todo-green/command.json)，keep=true、显式clear=false；正式controller两例及真实CLI共[14项通过](evidence/todo-final/command.json) |
| 最终工程静态 | [全仓Ruff](evidence/r3-f-ruff/command.json)通过；[Mypy291源码](evidence/r3-f-type/command.json)通过 |
| 工程统一入口 | [pure离线4案例](evidence/off1/command.json)通过；最终pure的pip check/版本/帮助、受控SQLite及构包绑定见T07回执 |
| 独立接缝复核 | [独审报告](evidence/reviewer-final.md)：预算/存储/升级/取消/范围权限/子代理/材料/导出均有亲跑定向证据 |
| 最终同包公开入口 | [r3x](evidence/r3x/command.json)：纯运行包、无源码注入，T06两案及Todo双场景共3节点通过；[最终指纹](evidence/reviewer-r3-final-fingerprints.json)核对root全部323输入及安装27被审文件一致 |
| 固定包 | B-r3的snapshot/sdist/direct wheel/重建wheel/实际安装314产品成员逐字节一致；[构包记录](evidence/t07-r3-delivery.md) |

按ADR-0015复用：R2相对R1只加log.py导出父目录初始化四行；R3相对R2只改context_runtime.py的Todo pin恢复。各次差异都有完整输入指纹；不把R1全量改写为R3重新执行全量。B-r3实际运行其受影响controller、空项目导出、两次压缩/重启/回查/升级及Todo跨进程案例。

首轮f1临时目录在checkout内，违反无Git夹具前提，已中止且不计任何通过数。个别CLI验收遇到长合成路径的SQLite启动失败，保留原记录，改用仓外短目录重复同一节点；不改产品/断言来掩盖失败。

## 最后的人工作业

在真实Windows Terminal中运行下列命令。脚本只准备独立合成HOME、工作区、localhost模型与同一测试会话；不使用真实账户、不操控GUI，也不自动判定人工通过。

```powershell
& 'D:\rcb-dd7453\pure-r3\Scripts\python.exe' -I -X utf8 'D:\java supplement\Firstcode\RuoCun\.scratch\deepseek-compaction-20261113\evidence\manual_terminal.py' --python 'D:\rcb-dd7453\pure-r3\Scripts\python.exe' --wheel 'D:\java supplement\Firstcode\RuoCun\dist\compaction-b-r3\ruocun-0.1.0.dev0-py311-none-win_amd64.whl'
```

按脚本显示的`/archive`、分页读取、导出和`/compact`命令观察显示，缩窄/放大窗口后确认可读并正常退出。人工体验与真实摘要质量不由`--prepare-only`、isatty或无头测试代替；09及主票在自动通过后保持`awaiting-user`。

## 规模与保留限制

[逐文件统计](evidence/change-size.json)只计算启动前保存的23文件副本和本批新增文件，未将用户其它Git差异归入本批。新增5个产品模块810行，新增5个测试文件1093行；另有已有产品的接线修改。原估算没有充分计入子执行持久化、范围权限、附件闭包及升级/确认接缝，实际改动较大。

不能补回旧版已删除的原文；字数估价不是精确tokenizer。SQLite与外部附件、账户配置与会话不宣称跨文件原子事务。R3只保住模型可见任务pin，不反解析格式化文字伪造完整结构化Todo/TUI状态。未调用真实供应商模型，未宣称摘要质量、缓存收益或其它平台实机通过。
