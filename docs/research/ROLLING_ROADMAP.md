# 滚动研究路线

设计版本：2026-10-01。项目总体目标是预测成功完成任务所需的 token 数量；本轮首个实证采用可直接观测的成功运行终点。GitHub [Issues](https://github.com/shuo19mo/prediciton-token/issues) 与 [Milestones](https://github.com/shuo19mo/prediciton-token/milestones) 是唯一进度入口；本文是版本化设计，不维护第二套实时状态。保留现有七个 milestone，只在当前证据确定确有必要时创建下一项 issue，不预建未来实验或模型网格。

当前协议为 [#15](https://github.com/shuo19mo/prediciton-token/issues/15)，数据/代码版本固定在 [`480e548f340f12d854064bbf8208d90b008893ef`](https://github.com/shuo19mo/prediciton-token/commit/480e548f340f12d854064bbf8208d90b008893ef)。[#14 Astra 验收](https://github.com/shuo19mo/prediciton-token/issues/14#issuecomment-5901809512)仅通过 M2 数据准入，不表示师兄确认、训练、预测效果或贡献成立。

## M0 · 项目现状与证据资格审计

- **科学问题：** 已有证据足以支持怎样的研究方向？
- **进入条件：** 完成已有事实和证据复核。
- **交付物：** 停止机制、继续过程、首次成功可见性核查，以及由证据导出的研究问题。
- **证据通过标准：** 事实与假设分开；机制判断均可追到原字段或固定历史版本；支持、不支持或未知均可验收。
- **重构条件：** 停止机制不支持统一删失时，停止该编码并重定研究目标。

历史验收：[#8](https://github.com/shuo19mo/prediciton-token/issues/8)、[#9](https://github.com/shuo19mo/prediciton-token/issues/9)、[#11](https://github.com/shuo19mo/prediciton-token/issues/11)。M0 通过可靠交接门槛不表示潜在成功成本可识别、survival 有效或贡献成立。

## M1 · 相关工作与投稿风险记录

- **科学问题：** 最近工作与未来具体论文主张有哪些重合及投稿风险？
- **进入条件：** 对应主张出现时，复用已验收的 #12/#13 证据作定向对照；不循环开展候选否证。
- **交付物：** 对具体主张记录相关工作、已知重合、证据缺口和投稿风险。
- **证据通过标准：** 归因准确、已知重合和限制写实；不以材料数量或未找到同题证明贡献。
- **重构条件：** 真实结果无法支持拟议主张，或已知工作覆盖主要差异时，收窄或重构主张。

历史结论 `NO_SUPPORTED_CANDIDATE` 保留为创新与投稿风险；一般运行前 token 预测已有直接近邻，成功条件筛选本身未证明独立贡献。按后续路线，它不是 M2/M3 的数据或首轮实证阻断条件。见 [#12](https://github.com/shuo19mo/prediciton-token/issues/12)、[#13](https://github.com/shuo19mo/prediciton-token/issues/13)。

## M2 · 观测成功终点数据与首轮实验准入

- **科学问题：** 既有记录能否支持一项定义清楚、可诚实评价的成功终点实验？
- **进入条件：** 复核固定来源、成功标签、actor token 口径、运行前输入、任务/家族分组及隔离；不要求先指定 survival 或其他建模方法。
- **交付物：** 可追溯的数据准入报告、明确的成功终点定义、受控训练/评价材料及限制。
- **证据通过标准：** 成功终点、失败消耗和潜在成功成本分开；计数与来源可复核；同题/家族不跨分区；评价真值与训练输入隔离；输入时点及缺失处理有据。
- **重构条件：** 计量、关联、分组或隔离不可靠时修复或收窄评价目标；支持不足时报告限制，不补采或伪造样本。

历史验收：[#14](https://github.com/shuo19mo/prediciton-token/issues/14)在 [`480e548`](https://github.com/shuo19mo/prediciton-token/commit/480e548f340f12d854064bbf8208d90b008893ef) 通过观测成功终点数据准入；详见[验收评论](https://github.com/shuo19mo/prediciton-token/issues/14#issuecomment-5901809512)。训练侧有 102 条成功标签（43 个任务、19 个家族），评价输入 186 条，私有合格成功标签 32 条（13 个任务、6 个家族）。`review_ready / training_approved=false` 仍是包的事实状态；M2 PASS 不等于师兄确认、训练或贡献。

## M3 · 强基线与最小实证

- **科学问题：** 运行前任务文本能否在未见任务上，超出配置典型成本与长度/配置元信息基线，改善观测成功终点 token 预测？
- **进入条件：** #14 已由 Astra 独立验收；师兄训练前真实确认目标、包指纹、可见范围、冻结协议和运行环境。M1 风险记录不阻断。
- **交付物：** 按 #15 运行三个固定基线；在全部 102 条训练样本上拟合并为 186 条评价输入生成完整冻结预测；Luna 对私有 32 条合格成功标签/13 个任务/6 个家族独立评价，Astra 独立验收。
- **证据通过标准：** 配置中位数、元信息 Ridge、TF-IDF 加元信息 Ridge 参数固定；全缺失 `max_steps` 删除，其余数值缺失只按训练统计处理；三个预测文件 ID 完整、唯一、有限且非负，并在读取测试标签前冻结；任务等权指标及家族聚类不确定性可复算。正、负或不确定结果都可完成执行；文本模型不必获胜。
- **重构条件：** 发现协议、指纹、输入隔离或标签问题时，在评分前修复；结果无增益或不确定性较大时如实记录，由下一阶段依据真实结果决定是否收窄、停止或提出唯一必要后续问题，不追逐参数或换划分。

当前执行项：[师兄确认并运行首轮三基线，返回冻结预测供独立评价 #15](https://github.com/shuo19mo/prediciton-token/issues/15)。分工为 Astra 规划与验收、师兄模型实现/训练/调参、Luna 接口检查与独立评价、主代理管理 GitHub。预测结果本身不自动证明贡献。

## M4 · 结果复核与后续实验决策

- **科学问题：** M3 首轮真实结果留下哪些会影响研究判断的具体问题，是否需要后续实验？
- **进入条件：** #15 的师兄确认、三基线训练、冻结预测、Luna 独立评价和 Astra 验收已完成；本阶段不重复首轮工作。
- **交付物：** 引用现有固定版本结果与验收，依据实际未决问题记录继续、收窄、修复或停止决定；确有必要时提出一个具体后续实验及其核验要求。
- **证据通过标准：** 决策可追到真实结果，明确已有证据与未知；若现有证据已回答问题，可直接引用，不要求再训练、再评分或重复首轮验收。
- **重构条件：** 发现目标错配、泄漏或协议偏差时返回对应环节；负结果和支持不足如实保留，不据外层分数追逐参数。

未来阶段纲要；M3 结果返回前不预建执行 issue 或扩展方案。

## M5 · 完整证据与稳健性检验

- **科学问题：** 经最小实证留下的发现是否稳定，且重要到足以支持具体贡献？
- **进入条件：** 存在真实、可审计且值得继续的结果，能够支持一项明确主张。
- **交付物：** 由该结果和主张决定的必要稳健性/反证检查，以及贡献审查。
- **证据通过标准：** 主要主张经得住关键替代解释；支持范围、负面发现和不可估计项均清楚记录。
- **重构条件：** 结论主要依赖小样本、未证机制假设、试后选择或单一划分时，收窄主张或返回对应研究阶段。

未来阶段纲要；具体检查随证据决定，不预建模型或实验网格。

## M6 · 证据成熟后的论文与内部投稿审查

- **科学问题：** 成熟证据能否支撑面向 NeurIPS/ICML/ICLR 正式主会的论文？
- **进入条件：** 前序贡献审查通过，核心主张与证据稳定，限制和可复现性明确。
- **交付物：** 真实证据支持的完整稿件、逐项主张出处、复现材料与内部审查记录。
- **证据通过标准：** 主张逐项可追溯，关键内部审查已处理；稿件完成、内部通过、实际投稿和录用分别记录。
- **重构条件：** 核心主张缺证、被新工作覆盖或审查未通过时返回研究阶段，不以改写掩盖缺口。

论文写作暂停，直到 M5 的真实证据与贡献审查支持恢复。

## Milestone 导航

- [M0 · 项目现状与证据资格审计](https://github.com/shuo19mo/prediciton-token/milestone/1)
- [M1 · 相关工作与投稿风险记录](https://github.com/shuo19mo/prediciton-token/milestone/2)
- [M2 · 观测成功终点数据与首轮实验准入](https://github.com/shuo19mo/prediciton-token/milestone/3)
- [M3 · 强基线与最小实证](https://github.com/shuo19mo/prediciton-token/milestone/4)
- [M4 · 结果复核与后续实验决策](https://github.com/shuo19mo/prediciton-token/milestone/5)
- [M5 · 完整证据与稳健性检验](https://github.com/shuo19mo/prediciton-token/milestone/6)
- [M6 · 证据成熟后的论文与内部投稿审查](https://github.com/shuo19mo/prediciton-token/milestone/7)

历史验收索引：[M0 #8](https://github.com/shuo19mo/prediciton-token/issues/8)、[#9](https://github.com/shuo19mo/prediciton-token/issues/9)、[#11](https://github.com/shuo19mo/prediciton-token/issues/11)、M1 [#12](https://github.com/shuo19mo/prediciton-token/issues/12) 与 [#13](https://github.com/shuo19mo/prediciton-token/issues/13)、M2 [#14](https://github.com/shuo19mo/prediciton-token/issues/14)。这些链接仅作历史证据索引，不是本地状态表。
