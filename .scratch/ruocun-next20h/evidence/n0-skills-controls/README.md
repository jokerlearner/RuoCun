# 34文字控制候选

Status: implementing / module-candidate

root单点拥有`skills/control.py`及`skills/runtime.py`的可选目录回调，普通CLI路由仍待接线。保持8core原文和既有按需/手动调用；不把本模块结果结题34，也不解锁35/36。

来源：冻结index.ts:779–831完整目录/disabled/覆盖标记/单项及bundled-installed-all、skills/toggle.test.ts三例、App.test.tsx:837–887两例。目录保留禁用与被覆盖core，显式compat来源额外标来源；开关只写原生userRoot/skills-disabled.json，不改参考/compat文件。已载入上下文和工具池保持来源“重启生效”，本次不偷做35动态刷新。文字选择器默认第三方、数字/空Enter翻转、t显隐core、a/A b/B i/I批量、None取消；完整TUI箭头/视觉按键仍后置，Esc由已审broker选择端口区分。

写入沿既有Windows私有原子发布；提交确认后才交换本地禁用集，未确认停止该控制器。按ADR13，坏JSON/无法保留的非名称条目不被开关覆盖；startup坏JSON容错与源一致，JSON非标准常量不接纳。未新增存储系统、安装或模型调用。

TDD：n0-skills-control-source-red因模块尚无exit2；实现后原三toggle＋两App语义文字适配5项通过。再复原5项启动装配、同一picker fixture加入坏文件保留的必要适配，共10 passed in0.35s；mypy2源、Ruff通过。均为源码定向、白名单环境/合成HOME与私有临时目录；原始回执raw，scan_hit=false。最终产物、普通入口、独审尚待后续，API0。
