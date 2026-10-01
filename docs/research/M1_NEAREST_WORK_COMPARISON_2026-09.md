# M1 最近工作对照：运行前成功完成 token 预测

> 历史审计报告，日期：2026-09-29。文中的当前判断和建议仅指当时，不是活动指令。#12/#13 风险保留为历史证据，后续路线见[滚动路线](ROLLING_ROADMAP.md)，当前协议见[#15](https://github.com/shuo19mo/prediciton-token/issues/15)。

**审计日期：2026-09-29。** 本报告核对截至该日公开的一手论文原文、附录、可访问作者代码，以及固定的本地历史文献输入。它是 issue #12 的研究比较，不是 HAL 数据再分析、方法定稿或创新性证明。

当前研究目标已确定为：**给定运行前可用的任务和 agent 配置信息，预测成功完成该任务所需的 token 数量。** “成功完成所需”仍有多种可评价定义：一次成功运行的观测 token、同配置成功运行的条件分布/代表值，或一条潜在延续到成功的路径成本。三者不能混称。现有材料尚未确定主 estimand、跨随机运行的聚合规则、失败样本可识别条件或方法贡献；这不改变研究目标已经确定这一事实。

## 固定来源与核查边界

本轮固定读取主目录历史提交 058f351eb6ed4f5819aacba2ab8fbdc371a57a18 的六份只读输入：docs/research/LITERATURE_REVIEW.md、LITERATURE_UPDATE_2026-09-28.md、literature_matrix.csv、CONTRIBUTION_GATE.md、papers/TOKEN_COST_PREDICTION.md、papers/BAGEN.md。这些文件不在公开 main 或本 worktree；本文只摘录需纠正或复核的主张，不复制旧资料。

| 代号 | 一手论文版本（访问日期均为 2026-09-29） | 作者代码/材料固定版本 | 证据状态 |
|---|---|---|---|
| D01 | [arXiv:2604.22750v2](https://arxiv.org/html/2604.22750v2)，页面标注 2026-04-29 | [LongjuBai/agent_token_consumption_analysis @ 335ecf2](https://github.com/LongjuBai/agent_token_consumption_analysis/tree/335ecf2a29607bbfe8b13708f10b7b9091bcba45) | 论文和相关脚本可读；论文引用的数据 CSV 未在固定代码树中核实，源行/有效分母及上游筛选未知。 |
| BAGEN | [arXiv:2606.00198v1](https://arxiv.org/html/2606.00198v1)，页面标注 2026-05-29 | [mll-lab-nu/BAGEN @ 8418bb2](https://github.com/mll-lab-nu/BAGEN/tree/8418bb2c4e4b388687829356ba0435a07a2959d1) | 论文、附录和准备/评估脚本可读；不同环境数据单位不能统一解释为 token。 |
| EarlyEval | [arXiv:2609.02783v1](https://arxiv.org/html/2609.02783v1)，页面标注 2026-09-02 | [inphotoo/earlyeval @ 7fd1a8e](https://github.com/inphotoo/earlyeval/tree/7fd1a8e5b755e1f7ab642bcae77473b53e2bf1d0) | 论文、配置、策略脚本可读；区分论文主协议与仓库辅助/扩展 split。 |
| TokenCast（新近最接近候选） | [arXiv:2609.35760v1](https://arxiv.org/html/2609.35760v1)，v1 首发 2026-09-28（版本历史）；§3、附录 B/C 已核 | [DEFENSE-SEU/TokenCast @ ca5f16e](https://github.com/DEFENSE-SEU/TokenCast/tree/ca5f16ec3851c26370a07a829c25b6e1149f082f) 的 [README](https://github.com/DEFENSE-SEU/TokenCast/blob/ca5f16ec3851c26370a07a829c25b6e1149f082f/README.md#L1-L5) | 固定仓库当时只公开 README，称代码正在整理、尚未公开；实现级特征/过滤链不能从代码确认。 |
| EET（边界） | [arXiv:2601.05777v2](https://arxiv.org/html/2601.05777v2)，页面标注 2026-04-20 | 本次只核论文 | 经验检索驱动的运行中提前终止和成本/成功率评价，不是运行前 token 预测。 |
| Tokenmaxxing（边界） | [arXiv:2607.22807v1](https://arxiv.org/html/2607.22807v1) | 本次只核论文 | 对成功轨迹事后定位首个正确方案及其后输出 token；不可把最终失败直接等同从未成功。 |
| AgencyBench（边界） | [arXiv:2601.11044v4](https://arxiv.org/html/2601.11044v4) | 本次只核论文 | 长任务/场景级表现与平均 token 效率；顺序子任务不能当独立运行前样本。 |
| Prompt-Induced Waste（边界） | [arXiv:2608.01347v6](https://arxiv.org/html/2608.01347v6) | 本次只核论文 | 受控 prompt、模型、effort、harness 的端到端资源差异，帮助界定配置和计量。 |
| MarketBench（补查候选） | [arXiv:2604.23897v1](https://arxiv.org/html/2604.23897v1) | 本轮未依赖作者代码 | 运行前自报单次成功概率与 token 估计，属于相邻直接自估证据。 |

作者仓库固定 SHA 是本轮 2026-09-29 只读查询取得的公开 HEAD；没有执行作者代码、下载作者轨迹或复现结果。固定源码行链接在下文证据卡中。TokenCast 论文写明公开代码计划，但固定仓库目前只有 README，因此其实现层证据等级低于论文说明。

## 详细证据卡

### D01 — Self-Prediction：已存在允许仓库探索的运行前自估

论文 §2 使用 OpenHands × 8 个模型，在 SWE-bench Verified 的 500 个问题上每题每配置 4 次独立运行；文中 token 相关分析会把多次运行的 token 汇总。§6 的预测实验把正在执行任务的 coding agent 本身用作预测器：它保留完整工具能力，可看仓库、执行初步命令并思考执行路径，但提示它输出预测而不修复；输出分 input、output、total token，另用同题 3 次独立预测，报告与实际值的 Pearson 相关和预测成本/实际成本比。[论文 §2、§6](https://arxiv.org/html/2604.22750v2#S6)

因此，“我们是执行前预测”或“我们允许探索仓库”都不足以区分本项目。D01 的输入时点是任务交付后、agent 可先做有限/开放式仓库检查但尚未开始修复，不是严格静态 task-only。它将 input/output/total 分开；作者目标的实际数据聚合与预测真值是否经过成功筛选则不是同一个问题。

代码能证实的生成链只到一部分：get_usage_average.py 对空值、None 和不能转成数字的文本返回 0，再把 total_prompt_tokens_run1..4、total_completion_tokens_run1..4 等列固定除以 4 形成均值；字面 nan 能被 Python 浮点解析成 NaN，不能概括为“所有坏值都置零”。[固定代码：均值转换/聚合](https://github.com/LongjuBai/agent_token_consumption_analysis/blob/335ecf2a29607bbfe8b13708f10b7b9091bcba45/dataset/get_usage_average.py#L13-L23)；[固定代码：四次 run 除以 4](https://github.com/LongjuBai/agent_token_consumption_analysis/blob/335ecf2a29607bbfe8b13708f10b7b9091bcba45/dataset/get_usage_average.py#L43-L52)。准确度脚本把报告中的 resolved id 加成 acc_runN 字段，但这段本身不按成功过滤。[固定代码：成功标记](https://github.com/LongjuBai/agent_token_consumption_analysis/blob/335ecf2a29607bbfe8b13708f10b7b9091bcba45/dataset/get_accuracy.py#L92-L104)

相关性脚本要求 ground-truth input/output、任务成本和预测字段存在后加入统计，但代码路径没有查看 success 标记；这只能证明这段 correlation 函数没有成功筛选，不能证明它收到的 ground-truth CSV 上游从未筛过成功运行。它对三个预测 run 的相关统计后求均值。[固定代码：纳入条件与相关计算](https://github.com/LongjuBai/agent_token_consumption_analysis/blob/335ecf2a29607bbfe8b13708f10b7b9091bcba45/self_prediction_analysis/calculate_correlations.py#L119-L172)。数据 CSV、原始交互到 gt_*_avg 的完整转换链、相关分析真实分母，以及目标行是否已只留成功运行：**未知**；检查了论文 §6、固定 repo 的 README、均值脚本和 correlation 脚本，缺少生成 CSV/分母的受版本控制输入和连接步骤。D01 的报告不能被重新表述成“单次成功成本预测”。跨 run 平均属于目标聚合选择；它只有在预测输入偷看未来 run结果时才是泄漏，目前没有此证据。

### BAGEN — 初始点、运行前缀自估与独立估计器并存

BAGEN §2 与附录在初始状态/首 turn 处请求预算估计。作者另有基于历史 rollout 的 prefix replay 自估实验；独立估计器则是在 Sokoban 轨迹 probe 上单独训练/强化学习的设置。因此既不能说它“只有 online 前缀预测”，也不能说“独立预测器”是天然差异。附录明确 initial probe 在任何 action 前，初始输入只有 system prompt 与初始 grid/状态。[论文 §2、附录 B/E](https://arxiv.org/html/2606.00198v1)

这些实验的目标和计量口径必须分开。第一，论文有 agent 首轮/无动作时点的总 token 预测；第二，独立 Sokoban SFT/RL probe 预测剩余用量或可行性；第三，SWE-bench 估计实验使用 provider usage 字段；第四，Warehouse 的预算轴是时间、库存周转（item-weeks）和美元等外部单位。不能把 BAGEN 概括成所有环境都在估 provider 全请求 input+output tokens。Sokoban 示例有 2,500-token cap，Search-R1 示例有 3,500-token cap，SWE-bench 另有 turn 上限。论文指出主实验 rollout 不受 token budget 约束；在已生成轨迹上进行的 prefix/replay 预算评估不等于运行时真实受该预算限制。[论文环境与策略](https://arxiv.org/html/2606.00198v1#S3)

作者对 impossible 的定义不是“观测时间右删失”。独立 Sokoban probe 数据中，标签只有原 rollout 成功且已用量加未来观测用量符合预算才判 possible；未成功或超预算都判 impossible。[作者代码：probe 标签构造](https://github.com/mll-lab-nu/BAGEN/blob/8418bb2c4e4b388687829356ba0435a07a2959d1/scripts/budget-rl/prepare_budget_probe.py#L267-L371)。对该 probe，user 消息按 fresh-message 重新分词，assistant 优先采用记录的 API output；k=0 只展示 system 与初始 user 消息，remaining 标签从其后 assistant output 和后续 user 消息累加，不把已展示的 system/初始 user 算进 remaining。[作者代码：token口径与 k=0](https://github.com/mll-lab-nu/BAGEN/blob/8418bb2c4e4b388687829356ba0435a07a2959d1/scripts/budget-rl/prepare_budget_probe.py#L290-L340)。这与首点的总量预测、SWE provider usage 不是一个标签口径。

SWE 对话准备脚本分别读取 provider input/output/total usage，缺总数时仅在可用分项基础上合计，并关联 resolved label；它保留成功/失败字段，不等价于把失败删失。[固定代码：usage 与 resolved 标签](https://github.com/mll-lab-nu/BAGEN/blob/8418bb2c4e4b388687829356ba0435a07a2959d1/scripts/budget-estimation-benchmark/prepare_swebench_dialogues.py#L89-L99)；[代码：成功和 token 总量字段](https://github.com/mll-lab-nu/BAGEN/blob/8418bb2c4e4b388687829356ba0435a07a2959d1/scripts/budget-estimation-benchmark/prepare_swebench_dialogues.py#L315-L354)。SFT/RL ablation 的 794 个 SFT training probes、380 个 held-out evaluation probes，均为单一 Sokoban 6×6/一箱子任务里的 probe，不是独立任务数；按 deterministic trajectory split 分为 40% SFT、50% RL、10% held-out evaluation。轨迹分组不等于 task-disjoint。[论文附录 E](https://arxiv.org/html/2606.00198v1#appendix.E)

### EarlyEval — prefix 成败预测与评估早停，不预测成功 token 目标

EarlyEval 为每条已完成 trajectory 的前缀 k=0,…,T 赋上终局 benchmark 成败标签，以 LightGBM 分别预测 success/failure；预测达到阈值时停止实际评测运行，目标是保留 agent resolve rate 和排序同时省成本。论文将短于 10 步轨迹从训练中剔除，不能把此项扩展成测试集也排除。[论文 III-B/III-C](https://arxiv.org/html/2609.02783v1#S3)

特征时点包括：静态 task prompt；当前/此前动作、工具反馈、思考与行为计数/顺序/错误和测试状态；在有 ground-truth patch 的 SWE-bench Verified 上，还包括 gold patch 属性及当前 prefix 对 gold 文件/API/test 的结构重叠。TerminalBench 和 Toolathlon 没有逐题 reference solution，禁用 reference family，只用行为和文本特征。论文的“无 reference 仍有效”结论和无 gold 的 benchmark结果支持其参考特征并非全方法依赖；SWE 的 w/o Reference 消融也不能反向推广为所有变体都读取参考解。[论文 feature 定义与消融](https://arxiv.org/html/2609.02783v1#S3)

论文 IV-B 明确的主协议是 leave-one-agent-out；§VI另称 task-partitioned leave-one-agent-out。现有公开证据没有把这两段文字与主结果表的具体数据入口/配置关联起来，因此主表训练/测试是否共享同一 task 的其他-agent轨迹，**unknown**。固定仓库配置明确描述其 leave_one_test_model_known_task 设置允许 test-model 的 instances 与其他模型的 train/valid instances 重叠；这只能证明该固定配置的行为，不能证明论文主表使用了它。[论文 IV-B/VI](https://arxiv.org/html/2609.02783v1#S4)；[固定配置：该 split 的行为](https://github.com/inphotoo/earlyeval/blob/7fd1a8e5b755e1f7ab642bcae77473b53e2bf1d0/configs/earlyeval.yaml#L118-L141)。仓库配置还记载共享预拟合特征器对 held-out model 的文本做 transductive 特征编码；这是该配置的限制，也不能泛化成论文主表实现。[固定配置：feature engineering](https://github.com/inphotoo/earlyeval/blob/7fd1a8e5b755e1f7ab642bcae77473b53e2bf1d0/configs/earlyeval.yaml#L151-L165)

省下的 tokens 是提前停掉的实际轨迹尾段 input/output token 量（SWE 主阈值报告约 32.7% input、28.7% output），不是模型对成功成本的预测误差或预测量。实现代码计数的是决策点之后的 prefix rows/steps；论文另基于 trajectory 的 token 数据报告 token savings。停止规则可预测终局成功或失败；未观察到其估计一次成功任务最终 token 数或潜在成功总量。[论文指标](https://arxiv.org/html/2609.02783v1#S4)；[固定代码：决定与 saved steps](https://github.com/inphotoo/earlyeval/blob/7fd1a8e5b755e1f7ab642bcae77473b53e2bf1d0/earlyeval/policies/safe_stop.py#L161-L207)。预测器为每步 CPU LightGBM，论文称单次推理低于毫秒量级；reference 特征的准备成本不应被说成完整系统的全部开销。[论文架构与 overhead](https://arxiv.org/html/2609.02783v1#S3)

### TokenCast — 最近的直接反例与仍未对齐之处

TokenCast v1 于 2026-09-28 首发，显式定义四种预测时点：Task Start 在执行前预测任务总 consumption；Call Start、In-call Update、Task Update 在运行中预测当前调用或剩余消费。模型组合段表示，以 LightGBM 预测，另做量化预测区间；无需额外 LLM 调用。消费定义是 provider-accounted input + output tokens；每次完整任务终止可以是完成、失败或运行限制，因此目标是实际终止时观测到的消费，不是条件于成功的目标。[论文摘要/§3](https://arxiv.org/html/2609.35760v1#S3)

运行设置覆盖四套任务集、六种 agent LLM 和两个 harness，11,712 条 trace/240 个任务。SWE 任务每模型重复两次，其余任务四次，部分 anchor 更多；同一 task 的 run 全部放在同一 fold，重复三套随机划分后按任务权重汇总指标。这不是把每个任务预先压成跨 run 均值作为预测标签。论文 Table 6 的 token 中位数仅在 usage 完整的 runs 上计算，而正确率分母是全部尝试；不能从“completed traces”字眼推断训练逐行筛掉失败。[论文 §4、Appendix C.1–C.2](https://arxiv.org/html/2609.35760v1#S4)；[同 task 分组、重复及统计分母](https://arxiv.org/html/2609.35760v1#appendix.C)

Task Start 输入是 task statement 的文本表示；如果 benchmark 提供 difficulty label，则将其接在 statement 前。故它是运行前预测，但静态输入可用性仍须与 HAL 的 task-only 特征契约逐项比对，不能假设 benchmark difficulty 在 HAL 可用。[论文附录 B.1 特征](https://arxiv.org/html/2609.35760v1#appendix.B)。它直接覆盖“运行前、task×agent 级的实际 token 消费预测”和普通 task-level 模型/历史中位数比较。它没有证明成功条件 token 目标已被完整解决：预测对象包含失败和资源限制终止的实际消费，作者报告 Task Start 的跨划分 MAE结果且总体上执行中信息更增益，但没有与成功终点定义对齐的目标和评价。作者仓库代码未公开，使输入字段、训练标签行筛选、usage缺失处理无法独立复现核查；必须把这三项保持 unknown。

TokenCast 的 baseline 在 Task Start 使用 Self-Prediction，且允许 agent 检查任务环境；这进一步削弱“已有 self-estimate 没有强 baseline”的说法。论文将任务分组、预测开销计入预算控制 replay，也明确 trace-complete 指到达记录终点，不代表任务解决成功。[论文 baseline/分组](https://arxiv.org/html/2609.35760v1#S4)；[预算控制成功语义](https://arxiv.org/html/2609.35760v1#S4.2)。

## 对齐矩阵

“证据等级”表示公开材料对这一行主张的可核查程度，不代表论文质量。unknown 后附所查出处/缺失项。运行前目标均以预测点所见输入界定；终点目标聚合与输入泄漏分别评价。

| 工作 | 目标 / estimand | 输入时点与允许输入 | 群体、单位、模型 / scaffold | 失败/停止语义 | Token 计量 | 分组拆分与指标 | 预测开销 | 证据等级；直接重合与候选差异 |
|---|---|---|---|---|---|---|---|---|
| D01 | 运行前自报 input/output/total，和观测 run usage 比相关；实际真值由四次独立 run usage 均值构成。上游均值是否成功条件化 unknown。 | 修复前；执行 agent 可看 repository、跑 preliminary commands、思考路径；不尝试修复。不是 task-only。 | SWE-bench Verified，500题；OpenHands固定 scaffold × 8 LLM。预测端每题/模型3个估计run，真值端执行4 run后均值。 | 预测本身不说明失败如何建模；真值行状态筛选 unknown。 | predictor prompt分别估 input/output/total；脚本将 prompt/completion token 四run取固定均值；actor之外 token含义未从本文推定。 | 论文报告 Pearson correlation、预测token cost/实际task cost。预测run平均相关。跨任务原始行、结果分母/有效数 unknown：repo CSV未提供，脚本缺上游样本生成链。 | 报告 prediction cost / task cost；未见系统级延迟测量。 | 论文+两个脚本可核；预测和四次平均直接重合。与本项目有别之处尚须证明成功条件与预测价值，不是因均值天然泄漏。 |
| BAGEN | 首轮无动作时点总token预测；Sokoban独立probe估剩余token/可行性；其他环境另有budget-feasibility和区间estimand。 | 首轮总量点在任何action前；Sokoban k=0展示system+初始user，剩余量不含已展示消息，后续prefix才追加已用状态。 | Sokoban、Search-R1、SWE、Warehouse；5 frontier LLM自估；SFT/RL独立估计器单一Sokoban设定。样本单位是trajectory probes，不是任务数。 | impossible = rollout未成功或预算不满足；不是右删失标签。SWE cap可按turn；各环境约束不同。 | 首轮 total-token自估；Sokoban fresh user-message重新分词 + API assistant output的remaining；SWE provider input/output/total usage；Warehouse时间、item-weeks、美元等。不能统一成全请求token。 | feasible/impossible macro-F1、失败早停和成功且判feasible时评分的remaining interval；Sokoban probe依轨迹40%/50%/10%分SFT/RL/held-out。 | predictor是执行模型本身或另训练SFT/RL模型；调用/训练成本不是统一报告的forecast overhead。 | 论文、附录及核心脚本可核；初始点、prefix和独立训练均覆盖。与成功目标有差异，但不能宣称只online、只区间或impossible等价删失。 |
| EarlyEval | 预测已完成trajectory的终局成功/失败概率；早停以保留benchmark resolve rate/排序并节省执行资源。不预测成功token数。 | 每步前缀 k=0…T（包括初始k=0）；任务prompt、到当前步的行为/动作/反馈/文本；仅SWE允许gold patch描述/重叠。 | SWE: 单mini-SWE-agent ×16 LLM；TerminalBench 37 agent config；Toolathlon 22 LLM × native scaffold；多trajectory/task。 | 训练标签是完整run终局判分；测试中预测后停止或继续，短于10步过滤仅明确用于训练。 | 运行的input/output token实际节省量；策略代码主计prefix/step saved；未预测单次完整成功成本。 | 论文称leave-one-agent-out，§VI另称task-partitioned；TerminalBench额外no-same-model/no-same-scaffold。主表同题跨agent重叠关系unknown；仓库known-task配置允许重叠，但与主表关联未证。指标为分类准确率/coverage、token/step saves和resolve-rate distortion。 | LightGBM每步CPU <1 ms；reference特征工程开销另有处理。 | 一手论文、配置和策略可核；与运行中outcome classifier高度邻接，不覆盖目标token回归。参考解只在有gold的benchmark。 |
| TokenCast | 实际已观测provider token consumption：任务终止于完成/失败/限制；运行前总消费及运行中剩余消费。不是success-conditional potential cost。 | Task Start用任务文本；可包含benchmark difficulty label。之后可见已完成调用/当前文本前缀/工具结果/usage history。 | 4 suites ×6 agent LLM ×2 harness；240 task、11,712 run。同一task内重复。 | 成功、失败、资源上限到记录终点都终止。预算控制是trace-complete replay，不是解决率。Table 6 “usage complete”统计中位数口径，不等于训练筛选规则已知。 | provider-accounted input+output按logical call汇总；reasoning是否单列视provider返回。 | 同题重复runs同fold；task-weighted MAE/WAPE/coverage/MIS，对照history median、Self-Prediction等。 | 无新增LLM调用；Task Start预测成本另报/预算replay计入overhead。 | 一手全文/附录强，代码仅README；这是对泛化“task-level pre-run forecast”最强直接重合。条件成功estimand、成功行筛选与HAL静态字段对应unknown。 |
| EET | 在agent执行过程中决定何时停patch generation/selection；比较整体成功率与总消耗。 | 运行中代码改动、测试反馈、trajectory与检索成功经验。 | SWE-bench Verified；Agentless/Mini-SWE-Agent/Trae × GPT-5-mini/DeepSeek-V3.2；6 configs。 | 策略改变运行终止点，并报告resolved；经验库只存成功解。 | benchmark总input/output token、API calls、美元等聚合。 | 对比启用/关闭策略、resolved rate与总成本变化。 | 引入检索和判断调用；非纯成本预测。 | 原文完整；边界工作，不直接预测运行前token成功量。 |
| Tokenmaxxing | 观察生成token到首次正确solution及其之后；只对成功轨迹拆分首次正确前后。 | 已执行trajectory的patch snapshot和测试结果，事后逐snapshot测判正确。 | MiniLCB题目×模型×语言配置。 | 只分析成功轨迹中的首个正确方案；最终失败不能据此推断从未成功。 | 主结果为output token；作者称reasoning亦纳入有计费的output。 | 按任务控制difficulty，报告语言/模型层面token及前后solution中位数。 | 额外人工/测试回溯属于事后测量，不是预测开销。 | 一手论文可核；成功时间点与最终停止token不同，提示标签语义风险，不覆盖运行前预测。 |
| AgencyBench | 场景级得分/效率，Tok为每scenario平均token。 | 多步agent运行；场景后序信息依赖前序交互。 | 长上下文任务场景，多模型对比另含小规模模型×framework实验。 | 以完整场景结果计分；停止细节不是运行前目标。 | 场景平均token，不是单一成功run token estimand。 | 报告平均score、attempt、token效率；场景/子任务有序依赖。 | 未报告同类预测器开销。 | 一手论文可核；配置-成本相关背景，不是预测直接对照。 |
| Prompt-Induced Waste | 控制prompt/model/effort/harness后衡量任务成功和消耗；非成功token预测。 | 任务运行时固定prompt与harness协议，采集实际provider usage和成功。 | 24个确定性coding task，模型、PI.DEV/Claude Code harness、prompt variants；扩展campaign另行分母。 | final evaluation结果；各campaign应分开。 | provider输入/输出/缓存/reasoning和成本分类按论文口径；不能把美元直接换成无条件token。 | 16 development/8 holdout；模型、prompt、harness对照及成本/成功统计。 | 执行成本研究，不是预测开销。 | 一手v6可核；支持必须控制agent配置/计量，不覆盖预测问题。 |
| MarketBench | 运行前自报一次尝试的成功概率与总token，用于校准/auction收益；不是成功条件下的潜在成本。 | 看到task ID、标题、完整问题和acceptance commands；尚未执行时自报。 | 93 SWE-bench Lite任务×6模型，558 model-task行；实际成功标签来自外部强scaffold运行。 | 一次尝试pass/fail分别观察；token estimate与独立外部运行成本对照。 | 自报token；realized token由该run美元成本除以模型混合每token价推回。 | Brier skill/概率校准、token估计/实际误差与auction机制；同题划分本轮未用于主结论。 | 单次语言模型自估成本包含在预测者调用中；具体单位开销未在所核段单独给出。 | 原文可核、实现未核；进一步反驳“预运行自估空白”，但跟预测run用的外部强scaffold不同。 |

## 有界补查日志

**日期：2026-09-29。** 起始查询来自固定文献综述及本轮检索：2026 agent pre-execution token consumption prediction task success cost agent benchmark arxiv；2026 predicting agent token cost before execution budget estimate LLM agents independent estimator benchmark；site:arxiv.org 2026 “token consumption” agent prediction coding tasks；site:arxiv.org 2026 agent budget prediction token cost task-level。查询后对候选回到 arXiv 版本页/原文、附录与相关公开作者仓库；不把搜索摘要当证据。

只补查两篇新增候选（上限五篇）：

1. **TokenCast，纳入最近工作比较。** arXiv 版本历史显示 v1 于 9月28日17:59 UTC发布；精读其§3、§4、附录B/C与README。它更接近“执行前任务总token预测”的一般贡献主张，故优先核查。方法实现、特征和训练样本过滤因仓库代码未公开而未知。
2. **MarketBench，纳入相邻边界。** §3/Phase I显示运行前自报单次成功概率和token数，覆盖同题多模型，提供有力的自评校准反例；它的应用是一次尝试的市场估值，realized usage来自外部强scaffold运行，不等于同一agent成功条件成本回归。

已查到但不再增列候选：Tokenomics在检索结果呈现为已执行token使用描述/成本分析，不能从题名当成运行前成功token预测；不追加到矩阵。没有继续泛化检索或为了数量凑满五篇；这不是系统综述或原创性证明。

## 对旧说法的修正

| 固定旧输入中的说法/容易产生的印象 | 一手证据与定位 | 本报告修正 |
|---|---|---|
| D01被描述为“多次执行均值”；可能被误读成该均值的成功筛选已知。 | 四run固定除以4脚本；resolved脚本只添加acc字段；相关函数只按usage/prediction字段可用性纳入，不查success。[usage脚本](https://github.com/LongjuBai/agent_token_consumption_analysis/blob/335ecf2a29607bbfe8b13708f10b7b9091bcba45/dataset/get_usage_average.py#L43-L52)；[accuracy脚本](https://github.com/LongjuBai/agent_token_consumption_analysis/blob/335ecf2a29607bbfe8b13708f10b7b9091bcba45/dataset/get_accuracy.py#L92-L104)；[相关函数](https://github.com/LongjuBai/agent_token_consumption_analysis/blob/335ecf2a29607bbfe8b13708f10b7b9091bcba45/self_prediction_analysis/calculate_correlations.py#L119-L172)。 | “相关函数未成功筛选”不等于“上游未筛成功”。实际关联CSV、有效分母和成功筛选保持unknown。四run均值属于目标聚合差异；只有预测输入偷看未来run结果才是泄漏，目前无此证据。 |
| D01仍允许明确执行前/静态输入区别。 | §6允许agent进入repo并运行初步命令。[原文](https://arxiv.org/html/2604.22750v2#S6)。 | 记为执行前但允许环境探索，不归类成严格task-only。 |
| BAGEN可能被压缩成“前缀剩余预算、impossible早停”。 | §2/附录B/E与probe构造表明有初始无动作估计、在线prefix、独立SFT/RL probe；possible条件依赖最终rollout成功及budget。[论文](https://arxiv.org/html/2606.00198v1)；[代码](https://github.com/mll-lab-nu/BAGEN/blob/8418bb2c4e4b388687829356ba0435a07a2959d1/scripts/budget-rl/prepare_budget_probe.py#L309-L371)。 | 明列三个任务/训练设置。impossible是成功与预算的合成标签，不是停止机制可识别的右删失。 |
| EarlyEval新增后容易被描述为“没有运行前点”或“参考答案是通用特征”。 | 原文构造prefix k=0,…,T；gold reference仅SWE可用，其他两套禁用。[prefix定义](https://arxiv.org/html/2609.02783v1#S3)；[reference availability](https://arxiv.org/html/2609.02783v1#S3)。 | 承认存在k=0静态前缀；区分其成功/失败分类目标与token预测。reference-feature结果不得扩展到无答案变体。 |
| EarlyEval的“held-out agent”可能被等同“held-out task”，或反向推断主表存在同题跨-agent重叠。 | 主文 IV-B 写 leave-one-agent-out、§VI另称 task-partitioned；固定配置说明特定 known-task split允许实例重叠，但未建立其与主表的关联。[论文协议](https://arxiv.org/html/2609.02783v1#S4)；[固定配置](https://github.com/inphotoo/earlyeval/blob/7fd1a8e5b755e1f7ab642bcae77473b53e2bf1d0/configs/earlyeval.yaml#L118-L141)。 | 主协议明确holdout agent；task-partitioned文字与主表样本关联仍未核清。仓库配置只描述自身行为，不能替主表作证。 |
| “近作尚未覆盖任务级运行前token forecast”在TokenCast出现后不成立。 | TokenCast §3.1、§4、Appendix C已有Task Start、run级实际input/output总token、同task runs分组、history/Self-Prediction baseline。[原文](https://arxiv.org/html/2609.35760v1)。 | 放弃宽泛空白主张。待证差异限定为成功条件目标及其对HAL可观察字段/评估价值是否构成必要且可验证的问题。 |

## 最强反例、建议结论与翻转条件

**最强反例是 TokenCast。** 它于本审计前一天发布，直接把运行前任务总token预测作为一种正式预测点，在重复运行、多benchmark、多agent LLM、task-group split上用学习式模型评估，且对照Self-Prediction与history median。如果本项目只主张“首个运行前task×agent总token回归”“首个使用task历史和配置做预测”或“首个任务分组评估”，这个反例足以否定宽泛新颖性主张。MarketBench另证明运行前自报total token与success probability已有真实校准研究。

**当前文献判断：INCONCLUSIVE。** 阻止本轮在 GAP_SURVIVES 与 OVERLAP_NO_CLAIM 间作出更确定判断的核心比较尚未定义到可对齐：本项目的“成功完成所需token”尚未选定是单次成功run usage、成功runs的聚合目标，还是潜在延续到成功的资源；最近的 TokenCast 预测在成功、失败或限额终止时观察到的run consumption，公开论文没有说明其模型训练行是否只留某种终局，因此不能据现有材料认定两者 estimand 相同，也不能认定成功条件化带来实质差别。D01的实际真值分母/上游成功筛选同样未核清。这两项具体比较未确定，才使当前标签为 INCONCLUSIVE；它不是由任意一项代码未公开自动触发。

**a. 影响文献判断的决定性缺项。** 要回答最近工作是否已覆盖项目目标，须先把本项目成功目标落到明确可观察/可陈述的 estimand，再与 TokenCast 的终止消费目标、D01 的预测真值分母逐项比较。不同终点的术语差别本身不证明研究缺口；反过来，若目标与用法相同，也不因本地有不同数据就保留独立主张。TokenCast仓库实现未发布是复核限制；它不推翻论文明确覆盖一般任务级运行前消费预测这一事实。

**b. 不阻塞定位的复现限制。** D01 CSV生成与有效分母未知；TokenCast作者代码只公开README，故具体训练筛选、特征和缺失用量处理未知；EarlyEval主表是否采用仓库known-task配置以及同题跨agent轨迹关系未知。这些限制降低可复现的实现级断言强度，但不妨碍确认D01存在探索式自估、TokenCast存在Task Start预测、EarlyEval做早期结果分类、BAGEN有首点和probe等论文明确覆盖范围。检索没有穷尽所有论文也不是新颖性证明。

**c. 后续阶段的研究问题。** 若M1经Astra验收保留一个候选，M2再判断HAL现有记录支持哪一可观察目标、任务/配置覆盖与分区；M3选择强基线、输入控制和能区分目标的最小反证；M4由师兄训练并独立核查结果；M5才判断增量、稳健性和科学重要性。M1不要求已证明实际预测增量、跨划分效果或survival有效。训练与结果门槛不会反向定义文献重合。

在三选一中，**GAP_SURVIVES**仅表示一个重要且可证伪的研究候选经过最近工作反证后仍值得进入M2/M3检查；它不表示方法有效或预测已有增量。若文献证据能确定相同 estimand、群体、时点和评价已由近作覆盖，且没有另一个有意义的目标差异，则为 **OVERLAP_NO_CLAIM**。当上述关键目标/分母比较仍未确定时，使用 **INCONCLUSIVE** 并写清卡住的比较，而非无限等待代码发布。

当前翻转条件：若固定本项目目标后，论文证据表明TokenCast/D01评估的其实就是同一目标、同一输入时点和群体，则转为 OVERLAP_NO_CLAIM；若对应目标、成功终点和评价群体明确不同，且差别足以构成重要、可证伪候选，则转为 GAP_SURVIVES，再把可识别性与效果留给后续阶段验证。若只补出代码但estimand仍未定义，分类不自动改变。

## HAL 与 M2 未知

现有 HAL 可以检查的最低限度问题是：每个归档运行能否关联到 benchmark/task identity、模型、scaffold/agent配置及已有 token 字段；真实计量是 input/output/total 哪一类，缺失/actor口径如何；终局结果和可记录停止事实是否足以挑出可观察成功run。若通过，HAL至少可能支持仅在已有观测成功runs上的描述性目标/预测可行性诊断，或检查不同既有配置是否可作为分组变量。此文献审计没有重新读取 HAL 原始数据、复算候选量或赋予任何 run 新标签。

M2应先判断：HAL每条既有记录的task/model/scaffold关联和usage字段是否支持哪个目标；运行前合法特征是什么；可观察成功run的任务/配置支持度；失败/停止事实中哪些可直接观察、哪些仍未知；同题同配置来源重复如何分组。成功run单次usage与聚合、潜在成功成本须分别决定。M0交接验收给出的四项删失判断是 unknown，训练准入为0；不得将其升格为失败可作删失。[#11验收评论](https://github.com/shuo19mo/prediciton-token/issues/11#issuecomment-5883042271)。损失函数、概率校准、强基线/容量对照和预测增量实验属于后续M3/M4设计及结果判断；M5再审视稳健性与重要性，不是本轮或M2的预设清单。作者论文的运行数只描述作者实验，不计入 HAL 本项目样本。

## 可复核入口与限制

所有作者代码仅以固定提交的 blob/<SHA>/<path>#L... 链接标出可复核行。对关键结果，优先看论文原文/附录，再看对应静态源码。公开页面/仓库缺少的数据不以搜索摘要、脚本名或推断填补。本报告未运行论文代码、benchmark、agent、判分器或训练；未获取任何原始/受限逐题真值；未写论文初稿；不对创新成立、投稿或录用作保证。
