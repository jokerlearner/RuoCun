# 两处行为保持的代码简化与代码量统计

日期：2026-11-13。分支：integration/ruocun-migration。基于本轮开始时的工作树，未提交Git。

## 实现结果

用户批准上轮建议第1、2项；本轮仅修改两个产品文件：

1. src/ruocun/tools/edit_file.py：Edit匹配失败后直接抛出相同的ToolRejected消息，移除同输入的重复诊断与空detail拼接。保留独立diagnoseMismatch接口及其已有测试。减少2物理行。
2. src/ruocun/tui/app/app.py：runAccountPicker移除冗余adding赋值和不可达判断。列表选择、删除模式取消、切换/删除返回、新增步骤、await和异常传播顺序保持。减少4物理行。

本轮使用code-simplification。独立代理复核通过，说明见 [独立复核](evidence/independent-review.md)。精确改动见 [本轮差异](changes.patch)。

对本轮开始时的474个Python源码和测试文件进行SHA-256比较，仅上述两个文件改变，无新增或删除，所有测试文件保持。工作树在本轮前已有大量未提交改动，本轮对比的是改前快照，不是Git HEAD；详见 [范围校验](scope-verification.json)。未处理第3项demo入口或其它候选。

## 自动验证

从明确环境白名单启动，HOME、配置和TEMP指向合成目录。三个命令均退出0，回执sensitive_match=false。

| 检查 | 实际结果 | 原始回执 |
|---|---|---|
| 六个相关现有测试文件 | 61 passed in 34.95s | [pytest](evidence/simplification-related/command.json) |
| 两个修改源码Ruff检查 | All checks passed! | [Ruff](evidence/simplification-ruff/command.json) |
| 两个修改源码mypy | Success: no issues found in 2 source files | [mypy](evidence/simplification-mypy/command.json) |

现有测试：tests/test_mvp_edit_file.py、tests/test_n2_edit_support.py、tests/test_n2_edit_recovery.py、tests/test_b02_modals.py、tests/test_b02_account_runtime.py、tests/test_b02_tui_app.py。未修改断言或增加测试。

各回执目录保留stdout.bin与stderr.bin，使用 [源码测试入口](evidence/pytest_source.py) 将当前src置于导入路径。命令回执中的原始入口在临时目录，该相同入口已复制到本记录中方便核验。

本轮为局部内部简化，仅报告上述定向检查与静态复核；没有把它们等同于全量测试、构包或真实Windows Terminal体验验收。

## 改后的分模块代码量

统计时间：2026-11-13 11:26（Asia/Shanghai）。范围为当前工作树src/ruocun下的全部Python文件，包含未跟踪文件；按一级目录分组，嵌套子目录归属一级模块，根Python文件单列。排除缓存，tests、仓库tools、evals和文档不计入产品源码小计。

代码行不含空行、纯注释行和真正的模块/类/函数docstring；同行仍有代码时计代码行。多行数据、提示词和翻译等字符串常量计入代码，因此这不是纯业务逻辑行数。物理总行包含代码、纯注释/docstring与空行。

| 模块 | Python文件 | 代码行 | 纯注释/docstring行 | 空行 | 物理总行 |
|---|---:|---:|---:|---:|---:|
| 根目录入口与公共文件 | 9 | 760 | 78 | 142 | 980 |
| agent | 36 | 8,966 | 172 | 990 | 10,128 |
| approval | 4 | 67 | 5 | 20 | 92 |
| client | 7 | 1,503 | 206 | 229 | 1,938 |
| commands | 4 | 210 | 9 | 58 | 277 |
| config | 14 | 827 | 62 | 214 | 1,103 |
| data | 2 | 36 | 1 | 5 | 42 |
| hooks | 3 | 301 | 5 | 53 | 359 |
| i18n | 5 | 618 | 5 | 28 | 651 |
| lsp | 6 | 496 | 7 | 65 | 568 |
| mcp | 2 | 556 | 11 | 78 | 645 |
| memory | 14 | 1,431 | 30 | 295 | 1,756 |
| obs | 5 | 441 | 18 | 111 | 570 |
| permissions | 22 | 4,632 | 44 | 575 | 5,251 |
| platform | 12 | 2,343 | 163 | 370 | 2,876 |
| prompt | 2 | 150 | 4 | 39 | 193 |
| repomap | 7 | 350 | 8 | 70 | 428 |
| session | 18 | 3,949 | 287 | 649 | 4,885 |
| skills | 12 | 1,005 | 25 | 190 | 1,220 |
| tools | 57 | 4,487 | 108 | 725 | 5,320 |
| tui | 38 | 2,386 | 60 | 418 | 2,864 |
| **合计** | **279** | **35,514** | **1,308** | **5,324** | **42,146** |

由本轮两文件改前快照反推，改前产品源码为42,152物理行，本轮减少6行；不能把统计代理异步采集的文件名baseline当成改前时间点。最终数值来自改完后重新读取的快照。

另列产品包内文本资源29个、1,209物理行；SQLite DLL ZIP二进制1个、1,450,919字节，均未混入Python代码行。产品外Python：tests为195文件/27,849物理行；仓库tools为3文件/219物理行；evals为27文件/2,441物理行。这些不是全仓其它语言或配置的总量。

原始逐文件统计与SHA-256见 [统计快照](code-metrics.json)。计数期间未检测到产品文件变化或新增，AST解析零错误；源码清单摘要为10aead5950f55ad4863935da52c5a812939d82714b50eb5fa329f8cd1c81e810。

可在仓库根目录使用PowerShell复算到自选输出文件：

    python -X utf8 '.scratch/code-simplification-20261113/count_code.py' '.' --out '<统计结果绝对路径>'

计数脚本 [count_code.py](count_code.py) 只读源码，不导入或执行产品模块。
