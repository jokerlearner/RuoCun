# 日常入口更新：新并行 B-r3 环境

状态：新Apps环境安装及合成验收完成，供主协调切换；本分段没有修改launcher、桌面shortcut、旧venv或真实HOME配置/会话。
日期：2026-11-13。执行前确认目标目录不存在，创建全新环境，没有覆盖已有安装。

## 实际安装

- 解释器：`C:\Users\PC\Apps\RuoCun\venv-compaction-b-r3\Scripts\python.exe`。
- Python可执行文件SHA-256：`21bb438c0d4a6f1f164b9a646f6ee000340185e5871180aec06db8d3f07c0082`。
- 固定wheel：`dist/compaction-b-r3/ruocun-0.1.0.dev0-py311-none-win_amd64.whl`，SHA-256 `3b34d7366716c4ec14fd01ef2b629cf26ef84aa11273ac513012b3fb2808baa4`。
- runtime依赖来自既有本地wheelhouse，按R3冻结运行锁`--require-hashes --no-index`安装；新环境没有pytest或其它开发依赖。
- [安装身份](installation.json)、[创建](apps-create/command.json)、[运行依赖](apps-runtime/command.json)、[固定包](apps-wheel/command.json)。

## 实际验证

- [pip check](apps-pip-check/command.json)、[version](apps-version/command.json)、[help](apps-help/command.json)全部退出0。
- [字节绑定](apps-bind/command.json)、[完整314成员及6个随包metadata/许可报告](apps-artifacts.json)：新安装与R3冻结源码/sdist/wheel逐字节一致，直接wheel相等；实际SQLite3.54.1受控门禁通过。
- 随包METADATA、WHEEL、entry_points和3份许可证与wheel逐字节一致；pip会重写的RECORD与额外安装记录不冒作原wheel字节。
- [真实新解释器source-free验收](apps-t06-todo/command.json)：外层pytest使用独立QA，产品固定上述新Apps解释器`-I -m ruocun`，3 passed/18.93s。覆盖两次压缩/跨进程恢复/原文回查导出、显式离线升级入口，以及Todo保留和显式清空不复活。
- 所有进程都使用明确环境白名单，HOME/AppData/ProgramData/TEMP、配置和会话指向本批合成目录；没有加载真实账户或调用真实模型。

## 交接边界

安装前后当前`Open-RuoCun.cmd` SHA仍为`c6217892e074bec62487f2a77bbdc9fba63ce3fe10744a4cc0297dbb45a554ee`；`open_ruocun.py` SHA仍为`e570975d3daa57ec1c1d3c345b455db1e6a62cfca08e0c1f6735c2ed30390ac8`。未切换桌面入口。
主协调负责真实数据备份、旧会话显式升级、活动进程核对和launcher切换。本页不表示真实会话已升级或用户终端体验已验收。
