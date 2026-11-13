# 若存发布资源来源核对

后续用户决定恢复重写前的主系统提示及其动态片段，再采用 A1–A5 事实适配，B 项沿用旧规则。当前决定和实际修改见[恢复与适配记录](system-prompt-restore.md)。下文保留资源重写批次的处理与验证记录。

## 本次改动

| 范围 | 处理 |
| --- | --- |
| 模型提示 | 重写双语系统提示，以及压缩、权限判定、代理交接、反思、记忆、技能适配、长任务提醒和网页提取提示。移除旧提示词提取脚本。保留既有命令、工具、协议标签与恢复检查。 |
| 内置资源 | 重写 8 个技能、4 个子代理和 6 个斜杠命令的提示。移除已重写技能目录里的旧许可副本，随包分发的第三方声明见 [THIRD-PARTY-LICENSES.txt](../../THIRD-PARTY-LICENSES.txt)。 |
| 工具与界面 | 重写模型可见的工具说明、运行提示和较长的双语界面文案。保留参数、快捷键、语言键和占位符。文字欢迎页采用新短句、太极画法和深浅主题配色。 |
| 若存形象 | 从原始角色 PNG 的独立预览产物装配。六帧 Sixel、256×244 尺寸、5 秒时序和静态回退像素哈希均与此前一致。设计、预览生成器和原始帧哈希记录在包内。 |

[主提示资源](../../src/ruocun/prompt/resources/) · [技能资源](../../src/ruocun/skills/resources/) · [角色帧来源](../../src/ruocun/tui/resources/mascot-frames.json)

## 仍随包发布的迁移实现

| 若存实现 | 冻结快照中的对应证据 |
| --- | --- |
| [Shell 预处理](../../src/ruocun/permissions/bash_preprocess.py) | `src/permissions/bash_preprocess.ts` 的安全环境变量集合、匹配模式和剥离执行包装的处理顺序。 |
| [Shell 安全判断](../../src/ruocun/permissions/bash_safety.py) | `src/permissions/bash_safety.ts` 的命令分类集合、危险判断分支和对应正则。 |
| [反思触发计数](../../src/ruocun/agent/reflect_cadence.py) | `src/agent/reflect_cadence.ts` 的计数状态、窗口范围和重置条件。 |

源码树逐文件摘要未发现与冻结快照完全相同的产品文件。按字符串去除标点、空白并归一大小写后的相似片段，再核对源代码和素材来源。短命令、数据格式和独立素材的匹配需要结合来源判断。上述实现的原版权与许可随包收录在 [THIRD-PARTY-LICENSES.txt](../../THIRD-PARTY-LICENSES.txt)。用于对照的冻结归档及其独立许可仍可按原记录复核。[冻结基线](../migration/baseline.md)

## 验证边界

资源重写批次的 Windows wheel 与 sdist 均逐字节核对了 308 个产品文件及当时的两份根许可声明。两种包都排除了原始对照归档、测试目录和技能目录的旧许可副本。

本轮合成回归通过 261 项，Ruff 与 mypy 通过。Windows wheel 在仓外隔离目录安装后成功运行 `--help`。内置子代理定义变化后，旧任务检查点仍受原定义一致性校验约束。已保存的主会话可以读取。真实模型输出及 Windows Terminal 本轮的视觉效果未重新人工验收。
