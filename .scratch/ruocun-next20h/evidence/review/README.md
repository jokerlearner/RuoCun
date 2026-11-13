# N0 独立模块审查

后续 N1 模块结论分列：[共享队列／Scheduler](n1-shared-review.md)、[边界／输入 owner／运行依赖](n1-input-review.md)、[权限 A](n1-permissions-a-review.md)、[权限 B／34控制](n1-permissions-b-controls-review.md)。已发现的 P2 均已回修复验，实际源码绑定见 n1-source-binding-02.json 与 n1-b-controls-binding.json；这些模块通过不代表普通入口、N1 新产物或 09／11／34 整票通过。A 报告中 B 尚待的文字保留为当时切片边界，后续 B 模块结论读其专属报告。

后续权限装配与排队正文快照见 [runtime/projection 独审](n1-runtime-projection-review.md)，固定 79c→832 与 508；setMode(normal) 来源差异已修复复验，剩余模块阻断 0，未推定普通入口或整票完成。

N0 集成固定 r2 的最终独审见 [n0-integration-review.md](n0-integration-review.md)：产品 `908cd14`／固定根 `70c7464`，已发现真实客户端空截断回调缺口经独立红→绿关闭；90 包成员与 sdist／wheel／仓库外实际安装一致，约定既有入口全部通过，剩余审查阻断 0。下文保留先前模块审查及当时待集成状态，不能将其历史“尚待”误读为 r2 现状。

当前结论：已审类型 `92ddc62`、图片存储 `ba4fa2e/9a365cb` 经 `8d29155` 回修，以及 Read `1ac88d2` 的模块接缝通过，可供 root 集成。审查源码合并点 `41e07987c241c8c50265fae8b9539a550cf48b19`，九个所涉产品文件、锁摘要及候选指针见 `n0-source-binding.json`。尚未构建本批 wheel，普通 loop/CLI 多模态闭环、原 08 完整出口及最终安装均待 root 集成验证；不据本模块结果解锁 09/34，不改变人工 pending。

## 存储接缝

ImageData 的 base64/mediaType 与冻结类型一致，ToolContext 新字段默认 None，旧调用兼容。ToolResult 在唯一 contract 声明为 str 或完整 tool packet，旧 str 不转型；新 packet 写入和读取校验 role、call ID、文字及图片字段，拒绝 journal 的投递标记。worker 入队结果和复用返回均深拷贝，未增加 StoragePort、物理 schema 或版本。

flushReadImages 只从当前 history 构造纯候选，tool.imageDelivered 与合并后的 user 图片消息同一 checkpoint 提交，确认后才交换；恢复补缺 pair 后仍独立 flush，已配对但未投递的图不会丢失。再次重开不重复注入，压缩移除旧调用后不扫描老 journal 重注。replace_context 的 reset_prompt 默认保持原压缩行为，图片投影显式 False 保留 API 用量统计。Chat 的既有 imageData 分支和 Responses 映射会剥离 tool 内部字段；user 消息没有新内部标记。loop 仍须在每次派发前/消费后清空 ctx 图片槽，并单独验收最终 wire。

原三项必要确认及九项 worker 回归独立执行：首轮 **11 passed / 1 setup error**，唯一错误来自本审查者把 Windows basetemp 写进普通 Python 字符串，反斜杠被解释为控制字符；该用例未执行，不是产品失败。改为正斜杠路径后，只复跑原真实 Conversation 用例 **1 passed in 3.34s**，原失败字节保留。

静态发现一个实际保真缺口：通用文本脱敏会修改恰好匹配合成 secret 的图片 base64/data URL。原负责人以 `8d29155` 仅对结构受限的完整 tool imageData 和合法 inline image URL 保真，普通文本、同名普通 base64 字段及远程 URL 仍脱敏。复用原真实重开 fixture、令 secret 为同一图的 base64，独立复跑受影响用例 **1 passed in 2.93s**。没有增加案例或故障矩阵；journal 图字节、checkpoint URL、再次恢复及普通文本脱敏均在该原用例中确认。存储剩余阻断 0。

原字符串兼容是新实现读取旧结果；未声称旧二进制可完整恢复新增图片 journal 的所有切点。自身会话/图片材料仍使用既有私有存储，不触碰 DAO 会话。

## Read

只读核对冻结 read_file.ts、paths.ts：按扩展名进入图片分支、按原 magic 前缀确定真实媒体类型、图片独立 5MB/vision 护栏、图片分支早于文本 readMeta、读前 mtime/size 和中文/英文提示、UTF-16 单行截断符合来源。未额外引入图片解码库或扩大格式方言，动态文件访问回调留给后续 35 接线。

独立复跑既有 paths/文本 Read/MVP 适配和原三项图片必要确认，**28 passed in 0.31s**。复用已审独立来源核对脚本，四个 ZIP/只读展开成员及中英运行时 description/schema 均一致；未用当前产品生成预期，未改八个 core 或共享执行器。Read 剩余模块阻断 0。

## 类型检查与环境

本私有 venv 的首次 mypy 与实现者相同，导入编译扩展被应用控制阻止，记 ENV，未回填通过、未更改主机策略。其后 root 提供并固定官方同版本纯 Python mypy 2.4.1（接受决定/锁提交 `5ec3a809`），独立核对 SHA256=`1784648d6ec8c2b5465e3f26241b845a0b3cb4e56c993c64abe16989e7698999` 后，仅在本私有 venv 用 no-deps/no-index/force-reinstall 替换发行包；其它锁定依赖版本保持。

实际 wheel 无 pyd/dll/so，实际导入 mypy 为 Python 源文件，版本仍 2.4.1，见 `raw/n0-review-mypy-env-01`。原存储五文件及 Read/paths 两文件定向检查 **Success: no issues found in 7 source files**，见 `raw/n0-review-seven-source-mypy-02`。原 ENV 和首次路径无效输出均保留，不探索替代系统入口，不共享可写 venv。

全部过程沿外层清空环境启动器、tools/run.py、固定 CPython 3.11、合成 HOME/config/TEMP，源码定向显式指定本树 src；不冒充 wheel 或仓库外安装验收。命令均 joined，所有回执 scan_hit=false。真实模型/付费 API 调用 0；Windows Terminal、真实模型图像质量及用户体验未验。
