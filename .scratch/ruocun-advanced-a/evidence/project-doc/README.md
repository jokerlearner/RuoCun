# 项目指令模块候选

来源冻结src/project_doc.ts及project_doc.test.ts六条既有语义；品牌路径按D09为RUOCUN.md/local。增加一份D09必要显式兼容/覆盖/内容去重接线确认，共7 passed in0.06s。frontmatter无新解析器，AGENTS/CLAUDE不回退，用户→Git根..cwd、本级local顺序保持。`.git`文件/目录均为边界；显式兼容来源标签带ID和原路径，链内文件归所在层，链外显式文件绑定声明workspace层。

逐段red→green在raw，缺模块、原生读取、local叠加、祖先链、显式兼容先失败后通过。一次chain-green中的无Git用例属于环境无效：默认合成TEMP在RuoCun仓库内，实际上存在祖先.git；未改断言，而以唯一、新建的仓库外--basetemp复跑，6来源+1兼容通过。最终全量/独审也须把pytest基目录放到仓库外（固定任务名新目录，已存在则保留而拒绝覆盖）。

定向mypy1源文件通过，Ruff导入顺序已整理，产品和测试未通过格式整理扩展行为。尚待模块独审与root普通CLI接线；不是70路由整票完成。无模型API/真实HOME，来源活动DAO未改。
