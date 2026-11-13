# 36 安装与适配模块独审

固定候选 `13a38072a724aeb447f76d59892c9bba6fb17f85`。只读核对冻结 `skills/install.ts`、`tools/skill_install.ts`、`skills/adapt.ts`、`skills/convert.ts` 与原票 36 的 `EXT-03`、`TOOL-SkillInstall`。

工具 `source` 必填非空，`scope` 缺省 user，保留 exec/required/deferred。Git 拉取使用受管前台进程的绝对可执行路径和字面参数，本地和 Git 均沿 `SKILL.md` 识别完整目录。写向两个原生层，源正文和二进制保持原字节。同名合并先在可见根外同卷准备，旧目录独立备份；已知失败恢复旧目录，目录交换未知保留暂存并传播未知异常。仅确认发布的结果登记 refresh scope。普通入口在结果配对后消费该 scope 的验证另见入口证据。

适配沿来源外来词判定及 `inherit-model-v2` 键，保留未转换源，模型不可用返回通用提示与原文。当前工具表无 agent 时保留原任务意图，既定默认继承当前主模型。缓存写失败保留本次已得到的正文。

独立复跑完整复制／同名／二进制、受控 Git、原目录回滚、cache 和 fallback 五项，`5 passed in 0.35s`，`raw/review-36-subset01`。没有 Git 网络或真实模型调用。

## 已关闭的路径缺陷

固定候选的实际 Windows 合成路径探针确认三项差异。大写 `.GIT/config` 被复制。原生缓存的目录重解析点会读取外部缓存并跳过适配。本地源根的重解析点在校验前被 `resolve()` 消去，实际能导入。探针只含合成标记，退出 1，回执 `raw/review-36-paths-red01`。

回修 `022aa3adf4261a7d2cab90d5dfdfd0c2d551cd6f` 按平台路径名规则排除 Git 行政文件和目录，拒绝显式本地源及祖先的路径别名，并用既有 `PrivateDirectory` 只读文件锚约束缓存读取。相同 Windows 探针确认三项均已关闭，正常合成适配回调一次，`raw/review-36-paths-green01`。三个原受影响用例通过，`3 passed in 0.35s`，`raw/review-36-affected01`。普通缓存命中、源字节、二进制和原生层确认继续校验。

四次运行使用私有 Python 3.11 与合成 HOME/config/TEMP，均无秘密匹配。剩余模块阻断 0。

## 普通入口

固定 `bf7f10e8593f27452b2c1467b1137d89f019fe4f` 独立复用原受控 TTY 用例，`1 passed in 3.95s`。同一工具批完成两次实际审批，安装提示显示原 `source` 及用户 `scope`，完整资源与源文件字节保持。下一模型请求保留原前缀及调用原序，新增安装目录位于已保存工具配对后。plan 请求没有 SkillInstall。模型经 Skill 读取新装正文，合成辅助响应沿原生缓存实际落盘，正文调用配对、用量和追踪保留。回执 `raw/review-36-entry-tty01`。

静态核对每轮只收已确认发布范围。工具批配对及图片投影确认后，当前代次才读取该原生层，保留 known、disabled 与 paths 过滤。发起提交前复核 Event 和代次，确认后扩活列表。关闭磁盘 Skills 时不刷新；适配请求使用本轮 Event，用户中止后不会发起新的适配。剩余入口阻断 0。验证使用合成目录、受控终端输入与注入响应，未访问真实 Git 远端、模型或 Windows Terminal。
