# 批次02欢迎图修复构建 b02-r3

固定源码 `fe046b96d6dd978aecd923fb63fb310302d26080`。Windows x64 Python 3.11 wheel SHA256 `38d3e0bc0edfc970ce199bfa0e88ebc767637151f2cb84b65b96796eb2b15289`。直接与sdist重建的wheel相同。Git、sdist、wheel和隔离安装的239个产品文件逐字节一致。运行依赖按锁离线安装，`pip check` 和四项安装检查通过。[文件绑定](artifacts.json) · [安装回执](offline-summary.json)

本版承接[b02-r2](../integration-r2/README.md)的批次全量1571项及恢复差异定向复验。此次产品差异集中在欢迎形象与输入owner。修改前定向复现首次原始帧尚未写出，修改后欢迎组9项通过，合并终端、渲染与引导受影响范围共26项通过。定向Ruff与mypy通过。[终端定向](raw/b02-r3-tui/stdout.bin)

实际Windows Terminal先收到终端能力与光标回包，再绘制原256×244 Sixel帧。用户确认图清楚，深浅主题输入此前已确认清楚。原Windows Terminal标题和焦点注意状态属63待验项，68据此前置暂保留整票在途，77/78整体体验单列。[实机回执](../../n18/wt/runs/20261111T092536Z-1592d0/README.md)
