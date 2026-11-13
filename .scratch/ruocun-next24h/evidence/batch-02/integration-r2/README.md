# 批次02集中构建 b02-r2

固定源码 `bbe9cd75b1e3f764629bcf9315ec620e84b08431`，Windows x64 Python 3.11 wheel SHA256 `33b2aadfe1a1cad522c82351cd73bcad30805f2b097dc313c614e1bc121fcbb2`。一次构建输出 sdist 和 wheel，另从同一工作树直接构建 wheel 核对，两个 wheel 哈希一致。Git 源码、sdist、wheel、隔离安装的239个产品文件逐字节相同。六项运行依赖按锁离线安装，`pip check` 和四项安装冒烟检查通过。[文件绑定](artifacts.json) · [安装回执](offline-summary.json)

唯一全量回归以 `1f64ecc14432d2d5ec46b721d557521954435f8f` 为基线，`1571 passed, 3 deselected`。Ruff 全树、mypy 216 个文件通过。之后仅普通代理恢复改动三个源码文件，使用来源定向、真实 CLI 同一次性授权回归及独立复验覆盖最终差异。首次包核验使用主工作树的 `NOTICE.md` 换行，因构建工作树采用另一种合法换行而拒绝。改为绑定实际构建工作树后原产物核验通过，未重建。[全量回执](raw/b02-r2-full/stdout.bin) · [恢复差异复审](../../review/b02-sync-recovery-review.md)

构建和验收使用隔离目录、白名单及合成模型。64图片、65输入、66面板已取得真实Windows Terminal技术反馈。用户确认形象出现但清晰度不足，68仍在处理，63的焦点与标题注意状态实机待验。77/78整体人工体验仍待验。
