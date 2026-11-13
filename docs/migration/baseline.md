# DAO 迁移基线

本文件保留工作流初始化时的历史登记。当前迁移统一采用 [冻结参考快照 dao-f17e189-7ac654a0dc06](../../.scratch/ruocun-discovery/reference/README.md)，包含当前提交与完整本地覆盖层；后续以该快照为准。
下列“待评估”及快照缺失描述均属于初始化时状态，当前快照已保存可恢复源码和差异，不能再将此历史表当作活动基线。

检查日期：2026-11-05

| 项目 | 记录 |
| --- | --- |
| 参考目录 | D:\java supplement\Firstcode\dao-code |
| 来源仓库 | https://github.com/tigicion/dao-code.git |
| 本地版本 | 0.5.15 |
| 基准提交 | f17e189dc68a0a0a0b9937784e1b7ce29aed80eb |
| 已修改的已跟踪文件 | 12 |
| 未跟踪文件 | 8 |
| 来源 LICENSE 的 SHA-256 | 7eac0b4c36ce843dfca5dfe1d56314c8b48535c6aeed41550b8afceaa4c6b71d |

## 对照层次

1. 已提交版本：稳定的来源基线。
2. 本地覆盖层：下表单独记录路径、Git 状态和当前原始文件字节的 SHA-256。
3. 纳入决定：由 [首张任务票](../../.scratch/ruocun-migration/issues/01-baseline-inventory.md) 逐项登记是否继承及理由。

上述记录不表示远程仓库当前最新状态，也不表示源码已经通过测试。
指纹用于识别本次读取的内容，不包含本地改动的完整快照；仅凭指纹不能还原覆盖层。
本地覆盖层未自动视为已提交版本或已经确认的迁移要求。

## 本地覆盖层清单

M 表示已跟踪文件的工作区修改，?? 表示未跟踪文件。
当前纳入决定均为待评估。

| Git 状态 | 来源相对路径 | SHA-256 | 纳入决定 |
| --- | --- | --- | --- |
| M | patches/ink+7.0.5.patch | 770a1b436e8ae86734301f4add7905595b4e6bb41be32222a64294ccb9baa1b4 | 待评估 |
| M | src/config/profiles.ts | 4a18ac20dbe649e6b59a1aa977ea7f7022697c9dddc749c0a9a1030cb7b42288 | 待评估 |
| M | src/session/process_identity.ts | ffd57d1b6aba96086fb7351af4e9a1ccfb48ff3a7dd7fdb54c9278787e1da2d1 | 待评估 |
| M | src/tui/Welcome.test.tsx | 07333e784cedec66cf0444733bc857c6ac319d4a34ab93b488cc4aadc117c11e | 待评估 |
| M | src/tui/Welcome.tsx | 02ace685477d509e9819ed4b424ef81dc02c46414adc0081b968f12b2939b7ab | 待评估 |
| M | src/tui/app/App.test.tsx | 4498060592911e9dfa60e66dcb8f64025017bba04d69518cdbd240044e405d48 | 待评估 |
| M | src/tui/app/App.tsx | 4daf9cf6e9f7d67e21d9300c7df4a9c2f0d351a5fdf18c4267a4f48d7d02dec1 | 待评估 |
| M | src/tui/app/run.tsx | 1a9ed38f88d714d9e2e1b5080143048ec971f4a37b0ad5f94b8130a5d5c114f6 | 待评估 |
| M | src/tui/app/types.ts | fe4a369f29fcea22d6ab59dfb8726c3df3e5bf1667b17c901ef92bacbeba494e | 待评估 |
| M | src/tui/onboarding/Onboarding.test.tsx | 1a69ac79728ba7318cbbcb34ebbf0db02ae4afe17d0a05afa5dbc83ca1d3cb4f | 待评估 |
| M | src/tui/tab_attention.test.ts | 1b76367c03dbc79517b4027aae38d7f40be101eb976cd06753002ca38cead38d | 待评估 |
| M | src/tui/tab_attention.ts | 0311136cc7d58bee87ff6d38fea143f4ac58af2d203494a73dfa4332123cd0c3 | 待评估 |
| ?? | scripts/generate-mascot-data.mjs | f1351fda4e10160ac8c9b5505aee3855d0989b5c1772db5abced5948942ffcbb | 待评估 |
| ?? | src/session/process_identity.test.ts | 1771fd771f1fa881ea84851ded9dfb838d61a412a12bcf728ae7882b9cdbc8b9 | 待评估 |
| ?? | src/tui/brand.ts | 2e1bdee1ade0bd909ce1d91b7228da15d5ddf410df05af37b73b91ca2ac71e53 | 待评估 |
| ?? | src/tui/mascot.test.ts | 211c15749755a2d2ad00e49f15044d2ceb0f350245948342dbdb02d624e3a061 | 待评估 |
| ?? | src/tui/mascot.ts | 61b0df909bfc1f8def136f4e65eca6e4a0f31040330ebab51897fe82faaafeda | 待评估 |
| ?? | src/tui/mascot_frames.ts | 9cae8f042ac80a0c1710e46b4de0d2c5d8098055a5a82728aab0b114180cfb6b | 待评估 |
| ?? | src/tui/terminal_reports.test.ts | fc79de1254816a3d1896a6704ad970e1b046ee2e048a0c6885b8cc5501c24f5d | 待评估 |
| ?? | src/tui/terminal_reports.ts | e4e6c7b81d46535ee1df4e6e0b6a2fdff94e21994f82415d0305df199899d3d2 | 待评估 |

## 已发现的平台检查项

- [src/schedule.ts](https://github.com/tigicion/dao-code/blob/f17e189dc68a0a0a0b9937784e1b7ce29aed80eb/src/schedule.ts) 直接调用 crontab，需要补齐 Windows 实现。
- [.github/workflows/ci.yml](https://github.com/tigicion/dao-code/blob/f17e189dc68a0a0a0b9937784e1b7ce29aed80eb/.github/workflows/ci.yml) 的测试运行环境为 Linux。
- Windows 发布产物的存在，不能替代 Windows 功能验收。
- 本地覆盖层含 Windows 进程身份和终端交互相关改动，需要独立对照和验证。

## 来源使用规则

读取来源以本次登记的提交和覆盖层为依据。
历史设计文档作为线索，现行行为以对应源码和实际验证为准。
需要更新基线时，先登记新提交、覆盖层及影响范围，保留原有来源记录。
参考目录保持只读，产生运行产物的对照在独立临时副本中进行。
