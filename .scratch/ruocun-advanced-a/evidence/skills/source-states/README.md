# D09 Skills来源实际状态

基于主协调指定稳定提交`03893b3e5b7762557a23d3a0e869d5a1c209026b`。仅修改skills/skills.py、skills/runtime.py、原runtime测试中的四目录fixture及本证据；不修改agent/runtime、project_doc、Skill结构或共享存储。

`loadSkills(*dirs, loaded_by_directory=None)`保持正常返回值；提供可选容器时，在现有gather之后追加本次各目录原对象列表，不复制对象，不新增读取。`loadRuntimeSkills(..., sourceStates=None)`保持正常返回值，传字典时按兼容source id写入`生效N项；被覆盖N项；禁用N项；paths未匹配N项`。未提供字典的既有调用保持原行为。

诊断复用最终disk对象identity集合，非胜者先记被覆盖；胜者按native disabled名称、已有可见结果名称分别记禁用、生效或paths未匹配。没有再实现覆盖算法、二次文件加载或二次paths扫描。同一路径再次声明由最后一次加载的原对象承担来源，前一个声明记覆盖；不向Skill添加来源字段。`--no-skills`仍提前返回、不读取技能，来源状态明确为`已禁用（--no-skills，未加载）`，不伪造未读取的数量。缺失/不可读路径仍由root入口诊断。

仅复用原四目录fixture，加入同一兼容项目目录再次声明的id、一个disabled项及一个未匹配paths项。预期：用户兼容被覆盖2项；前次项目兼容被覆盖4项；最后项目兼容为生效1/覆盖1/禁用1/paths未匹配1。没有增加测试项或扩矩阵；原25项仍全部通过。Ruff通过；mypy首次发现循环变量可选类型与前文变量名推断冲突，改名后2个产品文件通过，失败回执保留。

按本轮最小修复指令，不重新构建整个模块产物或修改既有不可变wheel。验证使用白名单启动器、tools/run.py、私有311 -I/-X utf8及显式本树src导入运行原25项，回执明确为源码定向复验；最终集成wheel由root统一重建与验收。没有真实模型调用，8core原文/header均未修改。原始red→green、静态检查和实际命令在commands/及command-index.json。
