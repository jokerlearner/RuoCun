# 66 选择与审批面板候选

66按65→66批内许可实施，保持claimed。组合根账户/模型/权限动作归主协调；实际审批/输入所有权与账户写入接缝须独审集成后69才消费。无产品build/full、真实模型或真实用户凭据/剪贴板操作。

## 端口与原职责

InputBroker仍唯一读stdin；app/modals.py只持选择/审批展示状态；onboarding/select.py保留原Select方向键循环与initialIndex，为App通用选择器提供clamp变体。approval_prompt(requests,cancelled=...)返回既有ApprovalDecision字典，y/a/n即时选择、dangerous/noPersist不接受a，批内逐项且并发batch串行，Esc否决本批及排队审批并请求pause。非交互仍由组合根保留原stdin_prompt降级。

ask_choice(question,options,multi=False,cancelled=...)保留源同义保留项去重、枚举展示、单选即时、Enter/空格多选、独立完成行、空集警告、自填和讨论意向。讨论只返回工具结果，不abort；Esc取消由组合根暂停对应回合。长列表滚动选项，系统完成/自填/讨论入口保持可见。select(title,items,initial_index=0,wrap=False,refresh=None)供账户/provider/模型使用，refresh只读列表回调在同一面板仍有效时替换，关闭取消迟到更新。

ask_text(prompt,secret=False,cancelled=...)统一文本输入，凭据字段secret=True只掩码显示、不反显到转录。pick_skills复用既有SkillControls的单个/批量setter，默认只列第三方、t显隐内置、a/A/b/B/i/I按源生效并留在选择器。on_cycle_mode异步回调供Shift+Tab显示权限提示；实际auto↔bypassPermissions切换和保存由唯一runtime实现，不在UI复制权限判断。

app.app导出runAccountPicker(ui,AccountActions)、runModelPicker(ui,listModels,switchModel,listGatewayModels=None)。AccountActions字段沿已交接签名：同步listAccounts，异步switchAccount/removeAccount/addAccount及可选fetchGatewayModels。面板不直接写cfg或调用系统凭据。新增/切换/删除、provider顺序deepseek/qianfan/volcengine/zhipu/custom、网关列表及手动model兜底沿冻结App；custom按源透传deepseek provider+显式baseUrl/model。Name为空允许默认，但Esc为None明确取消，不误当空白继续写入；后端保存/凭据结果不明异常不捕获后重试或报成功。

config/auth_wizard.py按MM453迁移源注入ask/validate/write循环及现有58 persistKey，验证无效可重输、空key放弃。新cfg由组合根实际保存；KeychainPort未知写异常原样上抛，不重复persistKey。该纯引导模块不代表账户/模型runtime已装配。

## 实际来源与红绿

source.json绑定冻结源及测试SHA。wizard-choice-red、account-ui-red、cycle-red为真实缺模块/方法/按键路由红。source-candidate为11项DAO来源语义用例通过，涵盖源KeyWizard3场景、Select初值与环绕、单/多选/自填、审批排队/危险限制/Esc与主草稿、账户切换/新增及掩码、自定义网关列表/手输、模型选择回调、英文Shift+Tab提示。9源Ruff/mypy通过；已有3输入owner回归在前一UI切片通过后按ADR0015复用，不重复整套来源/产品全量。

沿现有普通TTY确认包会发送y+Enter的实际接缝另发现：即时审批完成后，同一输入批剩余Enter可能下溢提交此前主草稿。modal-owner-boundary-red精确复现，修复为当前输入批仍归已完成模态，下一事件循环再交还主输入；不是计时debounce，不修改草稿。原case含a+Enter、并发下一审批、dangerous屏蔽a、Esc清队及未自动提交，定向green且9源静态检查通过，随后受影响11来源组复绿。没有虚构先测历史。

本候选所有回执tools/run白名单、合成HOME/config/temp与合成key，敏感扫描false；原文事件进一步在JSON解码后的展示字段清VT（沿65独审修复）。普通入口、真实后续请求换账号/换模型、许可持久规则与用户实际窗口均另记，不用面板fake-actions证明真实后端完成。
