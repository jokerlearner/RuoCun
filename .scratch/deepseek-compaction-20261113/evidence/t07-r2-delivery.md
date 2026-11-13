# B-r2 正式构包身份与仓外安装

状态：根源码已应用批准导出修复，R2输入与包绑定已正式确认并保留本地副本；随后独审确认Todo重开再压缩丢失的US09缺陷，R2为中间候选，最终交付等待B-r3，不据此宣称全部完成。
日期：2026-11-13。无Git提交、真实模型调用或真实用户会话升级。

## 源码与产物身份

- R1全量已安全结束：[f2](f2/command.json)，实际1734 passed、1 failed、4 deselected。唯一失败为原固定catalog总数断言，新增原生归档命令后主协调更新测试并保留原52条来源断言；原失败未删除。
- R2从R1冻结副本派生，**仅**`src/ruocun/session/log.py`两导出入口各加两行：父`.ruocun`不存在时创建，再沿原逻辑创建私有exports。既有父容器不改ACL。
- 主协调应用后，[全部根包输入核对](t07-finalize-r2/command.json)差异0；[正式输入清单](t07-r2-inputs.json)已设`root_applied=true`，来源为真实冻结工作区。原[pending清单](t07-r2-inputs-pending.json)保留。
- 输入指纹：`5b5ce2441081e779020f4d3022e57230c9c7ae11c9eb83715e05df289d3dc39e`。
- [正式绑定](t07-bind-r2-final/command.json)、[314成员及依赖/许可/运行库报告](t07-r2-artifacts.json)。根输入、R2冻结副本、sdist、重建wheel、direct wheel和实际pure安装字节相等。

| 交付文件 | SHA-256 |
|---|---|
| `dist/compaction-b-r2/ruocun-0.1.0.dev0-py311-none-win_amd64.whl` | `602bf15e672a2031b0c49ca717bbbe89d192b2d68be7d9f4f83d207547c163bb` |
| `dist/compaction-b-r2/ruocun-0.1.0.dev0.tar.gz` | `a6e8d79f7561d8dc1afd9669307803584abe8f0e4d2a4eeb318b643c2ee6a4cf` |

[交付副本摘要](t07-r2-deliverables.json)。R1包、纯环境及原始回执完整保留，未覆盖。

## 定向安装验证

- pure-r2：`D:\rcb-dd7453\pure-r2\Scripts\python.exe`，仅官方哈希runtime闭包与R2 wheel，无pytest；pipcheck通过。
- qa-r2：`D:\rcb-dd7453\qa-r2\Scripts\python.exe`，相同依赖锁加开发闭包和非editable测试支撑；pipcheck通过。未修改R1 QA或仓库`.venv`。
- [全新工作区manual预制检查](t07-r2-manual-prepare/command.json)：没有预建`.ruocun`，通过实际CLI压缩/会话/当前投影导出链。明确不是视觉/缩放通过。
- [source-free pure-r2两案独审](reviewer-t06-pure-r2/command.json)：2 passed，实际产品严格用pure Python `-I -m ruocun`，不注入src路径。
- 本次最小修复不需要再次执行全部无关集成。R1已通过部分依据只有一个产品文件的差异范围复用；主协调的R2安装[导出、catalog、package及私有目录定向](r2-target/raw/r2-catalog-export/command.json)已通过。

## 未扩大结论

独审已用真实CLI确认：TodoWrite被归档后重开`ctx.todos`为空，再压缩会丢旧任务pin。主协调将修复有效pin恢复并保持显式`TodoWrite([])`清空不复活，形成B-r3。R2原包与以上正确回执保留；最终默认全量/定向归因、其它票和用户真实终端体验由主协调统一汇总。
