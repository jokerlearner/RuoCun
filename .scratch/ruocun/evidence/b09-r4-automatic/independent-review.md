# 最终 R4 自动技术出口独立复核

复核候选 `5c7b73cd`，包源 `fcde3a921ba42aa1b52844757b343291fc073d21`，技术出口产品 `2d57674be8ea4715de26ba04939d74e1a8bc2cdf`。两个产品提交之间只有一处 pytest 夹具的绘制时序变化。独立在实际非 editable R4 QA 安装中运行该提交的两个 owned/shared 节点，**2 passed in 1.37s**。原安装组保留 60 通过、1 失败。后续源码组 54 通过及共享重绘 30 次成功均核过实际回执。 [独立定向](../../../ruocun-next24h/evidence/batch-final/r4-review/final-review-r4-resize/stdout.bin) · [R4 安装包](../../../ruocun-next24h/evidence/batch-final/package-r4/README.md)

核对权威矩阵 9 个 WT 和 10 个 WIN 自动行、R3 逐项记录和独立复核、15 个真实回执及实际 wheel。原 R3 引用曾取主工作树 CRLF 字节，干净检出拒绝了该 SHA-256。修正后引用 Git LF 字节，19 个新案例文件与对应矩阵行、原引用及状态逐项一致。隐藏原生控制台输入/输出模式从 503/3 到 1008/5，正常退出恢复 503/3，无补救；仓外重试实测同一 run 启动一次、三份工具结果提交及取消清理。 [校验回执](../../../ruocun-next24h/evidence/batch-final/r4-review/final-review-r4-19-canonical/stdout.bin) · [修前拒绝](../../../ruocun-next24h/evidence/batch-final/r4-review/final-review-r4-19/stderr.bin)

R4 两个自动技术出口独立复核通过。实际 Windows Terminal 用户操作、系统登录和重启按对应人工记录判定。 [77 技术复核](77-wtaccept-review.json) · [78 技术复核](78-wincaps-review.json)
