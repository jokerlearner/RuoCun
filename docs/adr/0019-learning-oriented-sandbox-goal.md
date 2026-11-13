# ADR-0019：以个人学习与低复杂度为目标，沙箱保持现状

Status: Accepted
日期：2026-11-13

用户明确若存是个人维护的编码代理，主要用于学习主流 harness 的正确设计，并希望控制维护复杂度。经源码对照，当前沙箱已采用与 DAO 一致的轻量 Shell 包装思路，由现成工具和操作系统实施限制；用户最终确认保持现状，暂不做 Docker 或 Windows 沙箱改造。

继续沿用 [ADR-0008](0008-source-first-sandbox-parity.md) 的现有行为：可选、默认关闭，保留 Seatbelt／bubblewrap 包装与现有失败处理，Windows 仍明确无 OS 沙箱后端。本轮不增加容器或 Windows 隔离部署，不做为此引入的 Linux 运行时移植，也不缩减既有会话、后台或恢复能力。

[简化方案](../../.scratch/sandbox-simplification-20261113/proposal.md)及其中的 A／B／C 路线作为历史研究归档，本轮均未采纳；[讨论票](../../.scratch/sandbox-simplification-20261113/issues/01-sandbox-design.md)按决策收口关闭。后续仅在用户提出新的明确需求时重新评估，历史候选不自动形成实施待办。本次文档收口不代表新增隔离能力或平台实测通过。
