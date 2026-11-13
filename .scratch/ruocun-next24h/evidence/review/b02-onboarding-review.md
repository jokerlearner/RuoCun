# 69 首次引导独立核验

固定源码 `d8a924b`，对齐后 `src` 和 `tests` 与候选相同。按 ENT-02、冻结 `src/tui/onboarding/Onboarding.tsx`、`src/index.ts:450–475` 和 D09/ADR0013 核验。源码顺序为校验密钥、保存账户、选择信任、保存语言、保存明确同意的信任。缺账户且真正交互才启动向导，已有可解析账户重启时复用。信任适用于 D09 的项目 settings/local/hooks。明确拒绝会覆盖当次启动的信任判定，持久记录维持原值。

| 独立回执 | 实际结果 |
| --- | --- |
| `b02-review-onboarding-entry` | 原普通入口用例 1 passed in 5.76s。受控真实 InputBroker 同一 owner 完成保存、退出和重新启动。账户、中文、项目许可状态均复用。回环 `/models` 校验仅一次。 |
| `b02-review-onboarding-boundaries` | 复用普通入口和真实 InputBroker 的合成边界脚本 exit 0。四个与确认和信任直接相关的断言见下。 |

坏原生 config 在创建向导和任何验证前拒绝，原字节不变，钥匙串端口调用为零。假钥匙串模拟写入已可见但回执超时，退出码 1，写调用一次，密钥现场保留，未保存后续账户文件、语言或信任。坏语言文件在账户已确认后触发退出码 1，已确认的账户与 keyRef 保留，原坏语言字节不变，信任尚未写。现有信任记录和 `RUOCUN_TRUST=1` 同时存在时，显式拒绝仍阻止当次加载项目的 plan 默认值，账户和语言保持可用，原信任记录不改。

以上经过 `tools/run.py` 白名单和合成 HOME，均 `scan_hit=false`。真实模型调用为零，涉及系统凭据的路径用内存替身。普通环境用例只调用回环校验端点。实际 Windows Terminal 的显示与输入体验单列。

`d8a924b` 审查发现旧 `trust.addTrusted` 直接覆盖写入会暴露已有有效记录。`bb0b5a5` 已改为先解析既有记录，已信任时直接返回。新增记录时在同目录创建独占临时文件，写入后 flush 和 fsync，关闭文件再执行 `os.replace`，最后清理临时文件。沿用当前 Windows 目录和 ACL 的可用边界。

在独审树应用 `bb0b5a5` 后，只复跑 `test_trust_publish_failure_preserves_previous_receipt`。回执 `b02-review-trust-publish` 为 1 passed in 0.14s，退出码 0，敏感值扫描未命中。用例注入替换失败，确认原信任文件逐字节保留、临时文件已清理。其余场景沿用上述 `d8a924b` 回执。
