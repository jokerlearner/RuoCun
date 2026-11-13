# 15 普通入口长路径诊断修复

原主线`8415581`的实际普通产品入口在shared长合成HOME下执行Bash，run的父目录已存在，但UUID目录未创建，返回AtomicFileError且runner.log尚不存在。遵循ADR-0009，只补该已确认缺陷的一个窄回归，复用既有private_file/race/runner及普通MVP断言，不改系统长路径注册表，不缩短原入口state，不调用真实模型。

## 实际红与原因

`n15-long-path-red`首先在280字符普通Path.mkdir上得到WinError206，属于复现场景准备失败，不能当作目标AtomicFileError。将普通父目录控制在240字符、追加36字符UUID目录后，`n15-long-path-red2`准确在ensure_private_dir的CreateDirectoryW返回Win32 3，目录未创建。排序假设为DOS目录表示、ACL API读回、NT guard名称拼接；真实结果证明需要统一路径表示，而非权限放宽。宿主普通Python文件I/O也受MAX_PATH限制，故只给CreateDirectoryW加前缀不足以覆盖附件。

`durable_file.local_path`仅接受本地盘符绝对名，短路径保持普通表示，达到248个UTF16码元时使用扩展DOS名。安全检查仍核固定本地卷、每级重解析点、真实owner及精确私有DACL；目录祖先pin/guard分享边界保留。ACL、CreateFile/Directory、Python原子临时写入/替换/清理统一表示；NT guard使用去掉扩展DOS前缀后的正确`\??\`本地名。PrivateDirectory保留可用于实际I/O的路径。

manager构造/run_dir/恢复Path和runner普通内部入口采用同一转换，持久run_dir与runner收到的目录串通所有capability、manifest、grant、日志与收据的Python I/O。grant前错误仅在runner.log实际存在时指向它，否则明确日志尚未创建。未修改B并行的cancel/close/恢复控制逻辑。

## 原入口复验及路径别名接缝

合入主线普通runtime接线后，使用原主仓`.scratch/ruocun-next24h/evidence/shared`作为tools/run白名单state，实际源码指向本worktree；普通MVP用例和TTY用例保持原断言。`n15-long-path-mvp`的首轮7工具/Bash全部成功，但第二进程重开返回71。原因是长run_dir的扩展路径父名，与尚短的普通session/runs文本比较不等。只将既有恢复边界比较两边做相同local_path转换后，`n15-long-path-mvp-green`完整2项通过（21.38秒），包括真实Bash、正常收尾、另一进程重开原会话。原长state未缩短。

## 最终结果

- `n15-long-path-green`：同一240字符父+UUID目录，创建/重复ACL核验、bootstrap真实原子发布、目录Flush、私密文件核验通过。
- `n15-long-path-regression`：既有private_files_windows、private_files_race和真实n15_managed_shell共25项通过（52.04秒）。
- `n15-long-path-final`：窄回归通过，附带确认短路径保持、转换幂等、扩展UNC拒绝（不访问网络）。
- `n15-long-path-final-checks`：3个产品源及该测试Ruff通过，3源mypy通过。

所有raw来自明确白名单tools/run，HOME/config/temp为合成目录，扫描sensitive_match=false；失败栈与原入口输入人工检查仅合成内容。原始红绿均保留。此修复证明本次真实session/run深度的产品执行与恢复，不宣称全产品任意32767字符路径、网络盘或未验证平台支持；18真实终端验收和15其它独审出口独立记账。
