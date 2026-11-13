# N5 r1 仓库外固定安装独审

固定产品及测试 `594c083bd1fceb375414a8fb05f7d37da42c8512`。`dist/n5-r1` wheel 和 direct wheel SHA256 均为 `600a9a8b9a90611c771cd26ab041380288d3e9319d3be8227f201251326eaca5`。sdist SHA256 为 `c9230ec7fd0553b1582a15aa2eb2ebe46851775505573cbcd31ee3a69de45fc1`。复用既有仓库外纯 CPython 3.11.9 环境，先核产物再离线替换，`pip check` 通过。发行版及 wheel 元数据均仅依赖实际安装的 `prompt_toolkit==3.0.52`、`wcwidth==0.9.4`。环境包含 pip、setuptools、两项运行依赖和 ruocun。见 `raw/review-n5-outside-install01`。

固定 Git 归档、主工作树、sdist、wheel、实际 site-packages 的 147 个产品成员集合和字节一致。wheel 标签 `py311-none-win_amd64`。独立逐成员和测试源摘要见 [artifacts.json](n5-final-install/artifacts.json)，回执 `raw/review-n5-outside-binding02`。首次绑定 `raw/review-n5-outside-binding01` 误把两份测试文件的 Git LF 归档与 Windows CRLF 检出要求相同 SHA。复验先确认实际两份文件匹配固定输入 SHA，再确认只存在标准 Git 换行转换。产品成员始终逐字节比较。首回执保留，期间未更改产物。

在新建仓库外合成状态下，`n5_outside_confirmation.py` 从已安装产品调用原普通 CLI 函数和原 `_exercise_tty` 函数。两个原断言文件执行前后 SHA256 相同，标准模块入口 `--version` 和 `--help` 通过。合成 loopback 覆盖保存重开、图片、记忆快照及维护，受控 TTY 覆盖审批、队列、Skills 和记忆命令。实际已加载私有 SQLite `3.54.1` 通过门禁，非主线程为零。见 `raw/review-n5-outside-confirm01`。

独立固定安装剩余阻断 0。未构建或重跑全量，未安装测试依赖。全部回执使用白名单合成环境，秘密扫描未命中，真实或付费模型调用 0。真实 Windows Terminal、缩放和人工体验仍待验收。
