# N0：Read图片与来源元信息

基于root已审共享类型`92ddc62d3462281bedebe308b4341d7bb6bdbfdb`。独占产品改动只有tools/read_file.py、tools/paths.py的detectImageFormat；不修改agent/loop、agent/runtime、ToolContext/ImageData、Session/Conversation及公共状态。原08未结题，09/34未实施。

## 实现与来源

- 冻结`src/tools/paths.ts:63–84`：扩展名决定是否走图片分支，真实mediaType按PNG四字节、JPEG两字节、GIF三字节、RIFF四字节前缀判断。沿源实现，RIFF不另验证WEBP容器、图片不另引入解码库，未扩大格式方言。
- 冻结`src/tools/read_file.ts:52–88`：保留文本5MB护栏；图片即使显式offset/limit也独立拒绝大于5MB；格式不可识别或显式非视觉sessionModel拒绝。成功设置`ctx.currentImageData={base64,mediaType}`并返回文字说明；依来源，图片分支早于文本readFiles/readMeta建立。根loop负责读取/清空图片槽、图片user消息及持久化，本切片不冒充端到端多模态通过。
- 冻结`read_file.ts:89–129`：既有文本行号/分页/默认2000行/小文件提示、二进制拒绝、读前mtime+size保留；中英文消息恢复源文本，语言选择适配既有ctx.lang。源中“不支持视觉模型”一条本来固定中文，继续保留。行截断按来源JS UTF-16 code unit计算，不以Python码点改变2000上限。
- 读取权限继续复用已审approvedPath，不更改路径/软链/审批契约。Read中英description与schema通过`check_source.py`直接从已校验ZIP的JS运行时字符串独立核对，结果见source-runtime-metadata.json/source-receipt.json；不是从当前产品反推。源码及测试4成员与只读展开字节一致，MIT归属沿项目现有LICENSE/NOTICE。

## 验证与边界

先跑既有paths/read/适配25项作为基线，通过；冻结paths.test.ts没有图片格式断言、Read也没有图片闭环单测，因此新增3项明确标为N0必要适配确认，而非伪称已有DAO测试：4种magic前缀一条轻量确认；英文文本/真实Read槽及UTF16单行；格式/5MB/vision三条明确来源拒绝分支。不扩组合/竞态矩阵，不调用模型。

原MVP的“图片明确不支持”是ADR-0011必要适配，不是来源要求；本轮范围已恢复图片，仅把同一个四字节PNG输入改成实际Read成功/图片槽断言。原失败raw保留。原14条文本Read及6条路径来源测试未改，其余MVP适配断言未改。最终定向28 passed；增加UTF16确认后3项适配再次通过。Ruff通过。元信息独立核对曾捕获英文漏`far`，已修且原失败保留。

**mypy为ENV未通过**：本私有venv的mypy导入前报`DLL load failed ... 应用程序控制策略已阻止此文件`，没有产生产品类型诊断。未修改主机策略、未更换位置绕过；stdout/stderr与命令原文保留在n0-read-mypy，交root/独审使用其已批准环境补验，不能写成类型检查通过。

所有工程命令经外层白名单启动器＋tools/run.py，固定311 -I/-X utf8、原私有18锁venv、合成HOME/config/temp。按N0授权使用显式本树src导入作定向源码验证，没有editable安装、没有每片重建wheel；最终安装产物由root统一固定。raw及命令索引见commands/command-index.json。真实模型API0，真实Terminal/人工体验未验。
