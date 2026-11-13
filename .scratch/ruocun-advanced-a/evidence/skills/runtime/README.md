# 阶段A：启动 Skills 装配

起点主协调稳定提交 `facc7dd77dab05b3023d481c38c857f74d4d00f2`，已快进合入其后单行walker品牌适配 `e74e96a7cc3d14cc034ae71afb6bffc48861f408`。本切片只新增`skills/runtime.py`、独有测试/证据；主协调独占的agent/runtime、loop、共享类型、Session/Conversation和公共状态表未修改。8core正文及资源保持原样。

公开API为`await loadRuntimeSkills(cwd: Path, userRoot: Path, compatibility: Compatibility, *, disabled: bool = False) -> list[Skill]`。显式目录按兼容用户→原生用户→兼容当前项目→原生项目顺序传给现有loadSkills；D09项目source须workspace匹配。没有默认旧DAO/HOME发现。显式兼容缺失/不可读的产品诊断仍由主协调入口处理，本模块沿既有loader忽略不可读文件的行为，不在此另造配置入口。

原生`userRoot/skills-disabled.json`只读过滤磁盘/core；读取或JSON解析异常沿来源视为空，JSON null为空、字符串/数组按可迭代项取有效名称，非可迭代形状报ValueError。磁盘全部名称先抑制同名core，即使该磁盘项稍后因paths不匹配而隐藏，也不复活core。缺失的core补`dir=''`及`slug=name`，保留invocation开关。

条件技能仅启动扫描一次：复用walkFiles/globToRegExp，匹配前4000个文件，任一pattern命中即可；全部条件已命中则提前停止。命中项克隆去paths、只入列表一次；未命中项本批不返回、不建动态池。共享walker的`.ruocun`忽略由root提交，本模块没有重复局部过滤。不实现35的文件访问动态发现、持久禁用写入、usage排序或36安装。

`SKILLS_HEADER`为冻结index.ts中文skillsHeader原运行时串，仅用于目录提示，不含正文。`capture_receipt.py`从已校验ZIP的模板字面量独立核对已安装导出串，未增加header fixture或模型重写；来源hash/运行时header hash在`source-receipt.json`。来源为index.ts:770–861的装配/扫描/header、discover.test.ts:27–54的无条件/预激活只出现一次及既有skills.test.ts的覆盖语义；D09目录身份是已批准的必要适配。

5个最小测试覆盖D09四层顺序和core覆盖、no-skills、native禁用只读、来源预激活筛选/去重/不复活core，以及4000边界。前4条各有原始red→green，第5条用4001项轻量文件迭代器直接确认边界，没有真实创建4001文件或扩故障矩阵。原20条Skills回归保持，合计25 passed。定向Ruff首次仅测试import格式失败，手动修正后通过；mypy单产品文件通过，原始失败均保留。

所有工程命令经既有外层启动器＋tools/run.py、固定311 -I/-X utf8、18包锁私有venv、合成HOME/config/temp。测试始终消费非editable `py311-none-win_amd64` wheel；`commands/`和`command-index.json`保存实际命令、失败、通过和scan-hit=0回执。没有真实模型API调用。固定候选源代码/产物/安装字节绑定另见`candidate-receipt.json`；普通CLI集成、最终阶段A出口及人工Terminal/体验仍由root后续验收，不据本5项关闭原34/35/36。
