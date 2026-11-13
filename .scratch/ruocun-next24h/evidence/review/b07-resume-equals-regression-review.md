# 原生续会话等号形式回归复核

批末首轮验证发现 `--continue=latest` 被新的参数路由当作提示，导致三条原有后台恢复用例失败。固定候选 `8393c78398cc99c3b60b6193cad3df258e2f2c5b` 保留了这个原生参数。独审复跑原三个参数实例与冻结 CLI oracle 一项，实际 4 passed in 33.50s。回执位于 `raw/b07-review-resume-equals-regression/`。

另通过普通 `cli.main` 捕获组合参数。`--continue=latest /recovery` 正确选择续会话，`-- --continue=latest --model=example` 保留完整字面提示，`--model=example hello` 继续按冻结 DAO oracle 保留为提示且未选择模型。回执位于 `raw/b07-review-resume-equals-literal/`。

两条验证使用白名单、合成 HOME 和本地模型夹具，秘密扫描均未命中。固定候选在本次复核范围内通过。
