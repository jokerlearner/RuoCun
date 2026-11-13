# 30 记忆工具与审核命令独审

固定 `94f6966ae8e83fa49e4ebaa866352498d1d8f326`。核对冻结 `tools/memory_{read,write}.ts` 和 `index.ts` 的 `/memory` 路径。MemoryRead 保留 query 必填非空、limit 1–20 和三层精确/AND 查询。MemoryWrite 保留五类型、三 scope、重要度和置信区间、所有字段可选及原分域默认，能力为 plan/auto，写入由 `persistentEffect` 进入既有独占和持久意图。来源 path#symbol 去片段后在工作区读哈希。普通命令仅合法删除进入修改路径。已知拒绝保留先前已完成的删除报告，未知异常继续向入口传播。只读兼容原件保留，审核报告保留来源身份。

独立原关键六项通过，`6 passed in 0.40s`。覆盖项目落盘、知识层来源哈希、删除、工具元信息、原凭据正文拒绝及已知命令拒绝。回执 `raw/review-30-tools-subset01`。已审的存储模块不重复运行。

## 敏感元数据缺口已关闭

固定候选仅扫描正文，现有检测规则本可识别的合成值经 `title` 或 `source` 仍实际保存，共两条。探针日志只输出拒绝状态和记录数，`raw/review-30-secret-fields-red01`。

回修 `c21f34f6e8d21e72b7341ad9579b173f24f4c4dc` 在来源读取和写入前扫描三个持久化字段。拒绝回执只报匹配类别。同探针确认两个输入均拒绝，没有目录或文件写入，`raw/review-30-secret-fields-green01`。原拒绝用例复跑通过，`1 passed in 0.16s`，`raw/review-30-secret-fields-affected01`。四次均用合成配置及私有 Python 3.11，敏感扫描未命中。剩余模块阻断 0。

## 普通入口

固定 `f0c3488c2bf6e3b53a77631e3e56ac0df89e0906` 复用原受控 TTY，`1 passed in 4.32s`。忙时 `/memory` 和非法删除不取消在途模型请求。plan 不提供普通写、命令及技能安装，受控普通写被拒。合成模型按有效权限在同批写入用户记忆并读回，实际写意图带 `side_effect=True`；审核显示原生文件，合法命令删除后该文件消失。回执 `raw/review-30-entry-tty01`。

普通入口使用同一原生/显式兼容 MemoryStore，合法删除先暂停并等待前台收尾。命令未知异常停止该操作并要求核对，模型工具未知沿既有 `outcome_unknown` 停止，无自动重试。剩余入口阻断 0。受控输入与注入响应均为合成，未调用真实模型或真实 Windows Terminal。
