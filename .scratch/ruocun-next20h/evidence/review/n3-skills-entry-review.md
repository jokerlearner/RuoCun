# 35 普通入口独审

核对入口 `f4dbdcabab34441a093bf20f5ed7cb9a686f1189`、Write/Edit 通知 `104456a447bc585fac9e462c3834fa800242950b` 和原生用量子目录回修 `09e39f1cc1f770751751eace36e63f2725244c5c`。Write/Edit worker 成功返回后由业务 loop 报告绝对路径。Read/Write/Edit 的普通入口回调只在当前 run 收集路径。完成配对和图片投影后，入口在准备候选前及实际提交前复核 Event 和代次。保持系统前缀与主 API 用量。`replace_context` 确认成功才更新同一活列表，保存期间到达暂停时仍应用该次已确认候选。发现失败和未提交候选各沿自己的边界退出。`--no-skills` 在兼容技能路径诊断、启动 loader、动态通道及用量入口前生效。

用量在实际加载时收集。批边界或结束一次尝试保存，先清本轮待写队列，再按保存结果决定是否采用新值。`failed` 或 `unknown` 停本进程自动写，独立的 loaded 事件仍可记录。该状态处理和 Write/Edit 接缝已静态核对。实际 TTY 验证原生用量写入及仅加载名、轮号和时间的 trace。

初始普通入口把用量直接写入 `~/.ruocun`。该根可由用户手工创建，也会在首次外置配置启动时由 SQLite 提取路径普通创建。Windows 原子发布要求直接父目录的私有 DACL。首个普通 mkdir 复验实际失败，诊断与原始回执保留。单独预置私有根的 fixture 只能验证该环境。`09e39f1` 将用量放到原生 `~/.ruocun/skill-state/skill-usage.json`，由已有原子发布端口安全首次创建直接父目录，现有根的 ACL 保持原样。原 TTY 恢复普通 mkdir 根，验证了产品本身的创建和落盘。

独立原审计用例 **1 passed in 0.13s**，验证 UTF-8 容错与仅按 LF 分行，保留 U+2028 字符。精确回修候选的原 TTY **1 passed in 3.79s**，包含原交互断言、动态目录的工具配对顺序、同一手动正文和模型加载、原生用量及实际 trace。回执 `raw/n3-review-skill-audit-lf-01`、`raw/n3-review-dynamic-tty-01` 均 exit 0、敏感扫描 false，真实及付费模型 API 0。

35 普通入口的受控验证通过。统一固定产物及主线整票记录另见组合验收，真实 Terminal 体验待验。
