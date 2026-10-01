# HAL停止证据初核：解析未知不等于原日志无信息

> 历史初核报告，版本2026-09-28-r1。文中“当前”与继续调查步骤仅指当时状态，不是活动指令；#9 的调查已作为历史工作完成，不在本报告重开。现行路线见[滚动路线](ROLLING_ROADMAP.md)，当前协议见[#15](https://github.com/shuo19mo/prediciton-token/issues/15)。

对现有17归档的派生事实复算，B的603个失败候选中，601条 `stop_reason=null`，2条 `explicit_timeout`；1,197条记录均没有整次token cap。分层为SAB 476未知/2超时、CORE 48未知、SWE 77未知。来源hash及分母见[聚合复算](../../reports/research_audit/current_evidence.json)。

`stop_reason` 当前解析器仅识别最终字符串TIMEOUT/ERROR前缀；它不是完整停止机制分类器。因此601不能写成“601条原始日志均无停止证据”。SAB的478失败中460条 `has_eval_log=true`，需核读诊断内容及与真实终止的关联；benchmark判分日志也不能直接冒充agent终止原因。

| 证据层 | 已查事实 | 对统一删失编码的意义 | 未解决项 |
|---|---|---|---|
| SAB Self-Debug历史规则 | 最多10轮；程序退出/输出文件存在、代码无变化可提前停止 | 正常结束不等于完成benchmark；`max_tokens`只限制单调用 | 各失败实际触发分支；过程中是否曾满足最终标准 |
| SAB Generalist历史规则 | 200步；配置budget=1.0；费用回调误将输入计数用作输出计数 | 名义美元预算不是可信整次token上限，也不证明实际触发 | 回调/工具结束/异常各分支逐运行证据 |
| CORE历史规则 | 40步、辅助视觉模型；48条失败候选都有max_steps字段 | 步数限制不是token cap；配置存在不等于每题触发 | 保存的steps或最后动作是否可关联，是否有提前结束 |
| SWE记录 | 77失败候选；43有per-instance美元限制、1有budget字段、33没有上述字段 | 空patch、评估错误、失败与停止原因不可混为一谈 | 对应历史scaffold和依赖版本的停止路径、异常日志 |
| 调用结束 | 模型finish_reason至多说明该调用结束 | 不能推出整条任务成功、失败或预算停止 | 需要完整任务层的终止证据 |

冻结源码出处（只读，不执行）：

- [SAB Self-Debug](https://github.com/princeton-pli/hal-harness/blob/23fc5665d6804fa72240f479e38f73fb53600002/agents/sab_example_agent/science_agent.py#L166)：sha256 `46d1f4c06d98518d3d90eb369939a79d7db7917a78e93ff786f804a39e8b56a6`，166–253行停止和调试分支；另一Opus归档对应edfe626b版本文件hash相同。其余提交仍需逐一绑定。
- [Generalist](https://github.com/princeton-pli/hal-harness/blob/bc575cd58bdb0a203c08952169df7e5d3330b8d8/agents/hal_generalist_agent/main.py#L90)：sha256 `71d1287b61e31f8a1c06d3ce8d37d31332553e3c6b505eed77e7b72b2aaa26dc`；90–99行费用回调、507–509行SAB agent设置。该证据不自动套用到所有SWE Generalist历史提交。
- [CORE](https://github.com/princeton-pli/hal-harness/blob/c7354ebd3ce3d284e3c89150e1218836c42eccac/agents/core_agent/main.py#L721)：sha256 `994e2e84f792b17ee62081001559c41f06299150dd95db0e9c9819ebce4c433c`；721–732行配置与运行调用；Sonnet4的7e56e668版本文件hash相同。

## 识别判断

目前支持的是“日志提供最终benchmark结果和观察用量”，没有直接证明完整前缀首次成功时点。对自然失败：同一继续过程未知、T>U未验证、条件独立删失未验证。超时标记也不能免除这三项要求；最终可成功仅为工作假设。

可以考虑成功终点的条件预测、机制有证据的子集、未知机制下的显式敏感性三条路线，但其评价对象不同。人工删失完整成功记录仅用于受控验证，不能补出自然失败的成功成本真值。本轮没有据此批准训练或选择survival模型。

## 继续调查的可执行步骤

按已冻结来源与历史commit建立本地机制索引；优先核对SAB评估日志与停止分支，随后读CORE/SWE保存的终止记录。每项分别记录规则存在、实际触发、是否可继续、是否观察中间成功及缺失。仅能从固定历史记录确定时才赋值，保留unknown；公开摘要不含逐题测试真值。

验收需覆盖当前候选中每个benchmark/scaffold的证据可得性，给出支持/不支持/未知及对研究目标的影响。以上初核未满足全部验收，因此该issue应保持开放。
