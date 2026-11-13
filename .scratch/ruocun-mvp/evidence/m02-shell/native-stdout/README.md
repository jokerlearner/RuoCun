# 普通CLI原生Python stdout缺失：合成启动环境定位

2026-11-10，组合基线`3184953`，M02产品三叶字节未改。原候选`8b76ee1`及先前证据全部保留。

主协调的真实七工具合成SSE回合完成Write/Edit，但Bash `& '<当前venv>/Scripts/python.exe' 'main.py'`（`print('new')`）返回只有PowerShell首次模块进度CLIXML与exit0，缺失new。先复用该完整组合测试，在本树`m02-native-combined-red`同样失败，之后缩小到嵌套subprocess.run、相同精简环境和同一Bash handler。没有调用真实账户/付费模型，没有运行额外压力或历史探针。

按diagnosing-bugs先建立red信号，再逐项最小化。独立handler直接执行的最小原生命令通过（最初label名native-red但实际green，不虚标失败）；嵌套精简env的最小复现失败。这个复现无需SQLite、StorageWorker或私密目录初始化，已排除它们是必要条件。

候选假设为标准流嵌套、初始化改变进程状态、精简环境差异。随后只改变一个变量：给CLI的合成子环境补`PATHEXT=.COM;.EXE;.BAT;.CMD`。相同cwd、命令、stdin和stdout/stderr重定向下，结果从缺失new变成`new`和exit0。原始CLIXML在成功时仍然存在，是首次模块准备进度，不是stdout缺失的充分条件。

| 检查 | 实际信号 |
| --- | --- |
| raw/m02-native-red | 直接handler最小Python命令1 passed；证明不能只在该较浅接缝回填回归通过 |
| raw/m02-native-combined-red | 真实七工具普通CLI与原症状相同，1 failed |
| raw/m02-native-nested | 缩小后的精简env嵌套handler，exit1；返回exit0但无new，独立预期断言失败 |
| raw/m02-native-pathext | 唯一补PATHEXT，exit0；返回new及exit0；其余不变 |

窄复现脚本为上层`native_diagnosis.py`：不带参数重现缺失；带`--pathext`只恢复该一个固定合成变量。所有进程均joined，未启动服务或后台runner，所有command.json的敏感匹配false。该脚本是已捕获fixture问题的诊断资产，不新增产品测试矩阵。

结论限定于实际观察：测试为CLI构造env时丢失了Windows执行所需的PATHEXT；tools/run直接测试父环境原本已提供它，产品Shell沿来源过滤敏感变量而保留普通环境。建议只修主协调拥有的`tests/test_mvp_product.py`环境白名单，恢复父合成PATHEXT并重跑原七工具+双进程重开。没有修改Bash编码、Job句柄、取消语义或07存储端口；最终完整组合复验由主协调记录。
