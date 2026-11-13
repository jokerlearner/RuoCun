# 本轮固定包与统一出口

Status: complete / automatic-exit-passed。固定产品及测试源 `594c083bd1fceb375414a8fb05f7d37da42c8512`，本轮N0–N5自动技术出口通过。真实模型、Windows Terminal/resize及人工体验单列pending。

沿已经实际验证的N1绑定脚本，只将回执范围切为`n5-final-*`。统一对照固定Git源码、工作树、sdist重建wheel、direct wheel及实际安装逐成员；实际运行依赖保持两个固定版本，SQLite门禁及许可/打包输入保留。旧N1脚本、回执、产物不覆盖。

固定源后只构建一套候选，先用同包跑默认pytest、Ruff、mypy、offline与实际安装绑定；独审复用已验仓库外环境和关键原入口，避免重复每个模块的全部回归。使用明确白名单及合成配置，真实模型/Terminal/resize和人工体验单列。未通过保留回执并修复受影响路径。

固定 `dist/n5-r1/ruocun-0.1.0.dev0-py311-none-win_amd64.whl` 由sdist重建，direct wheel字节一致，SHA256=`600a9a8b9a90611c771cd26ab041380288d3e9319d3be8227f201251326eaca5`；sdist SHA256=`c9230ec7fd0553b1582a15aa2eb2ebe46851775505573cbcd31ee3a69de45fc1`。已在私有开发环境离线安装。固定源、工作树、两份wheel及实际安装147个产品成员严格匹配；两项锁定运行依赖未变，实际SQLite 3.54.1。见[成员及锁](artifacts.json)和[运行库](runtime.json)。Ruff、默认mypy（132个源码文件）、offline、构建均通过。

[仓库外纯安装独审](../review/n5-final-install-review.md)通过：实际只有产品、锁定运行依赖和环境自带安装器，pip check通过；直接复用原CLI和受控TTY断言、标准模块入口、真实SQLite门禁及退出无线程。首次独立绑定仅遇测试文件的Git与检出换行差异，复验只接受标准换行转换并绑定运行的实际测试文件哈希；147个产品成员仍严格逐字节，无重建或变更包。

同一固定安装的[默认全量回执](raw/n5-final-pytest-r1/command.json)：**1359 passed、3 deselected in 446.79s**，退出码0，敏感扫描false，验收进程已收口。3项为默认筛选未选中的来源oracle入口，未计作本次通过。全部使用合成配置和回环响应；真实/付费模型调用0。未进行真实终端、跨平台实机或新增性能阈值测量。本轮只构建这一套正式候选。
