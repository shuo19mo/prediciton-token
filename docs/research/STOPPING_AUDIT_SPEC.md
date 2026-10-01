# Issue #9：停止证据索引的实现与验收规格

规格版本：2026-09-29-v1。对应 [Issue #9](https://github.com/shuo19mo/prediciton-token/issues/9) 和 [M0](https://github.com/shuo19mo/prediciton-token/milestone/1)。这是静态交接规格；执行状态、问题和验收只在 issue 记录。

> 历史规格，#9 已执行并验收，不是当前实现或重新开工指令。文中的工作区、命令、输出和下一步仅适用于当时。现行路线见[滚动路线](ROLLING_ROADMAP.md)，当前协议见[#15](https://github.com/shuo19mo/prediciton-token/issues/15)。

## 1. 要解决的问题与分工

现有解析器只从顶层输出字符串识别 `TIMEOUT` / `ERROR:`。它给出的 unknown 不能代表整个原始归档没有停止证据。本项要把现有记录中“配置了什么规则、实际发生了什么、最终如何判分、还缺什么”分别追到来源，再供研究负责人判断失败是否支持潜在成功成本下界。

实现者负责只读提取、关联、来源索引、汇总与测试；研究负责人负责科学解释和最终验收；师兄负责将来经批准的模型实现、训练与调参。本项没有训练依赖。实现者提交结果后保留 issue 开放，由研究负责人复查后决定是否关闭和下一项任务。

研究主目标仍为运行前预测成功完成所需 token。此处不选择 survival 模型，不把目标改成普通终止消耗。允许调查得到“证据不足”或“统一删失编码不成立”，不能为了正结论补造停止原因。

## 2. 开始前先找到正确的工作区

公开仓库 `main` 保存经过审查的管理文件、工具和聚合证据，并不含完整历史实现与数据。只有干净 clone 时，不能声称完成真实数据验收。

受控数据根目录和本地历史实现版本见仅保存在本地的 `data/derived/stopping_audit/IMPLEMENTER_LOCAL_CONTEXT.md`。本地历史分支只供读取；不得推送、合并整个历史分支或使用 `push --all`。在公开 main 基础上的 `codex/` 分支实现，工具通过明确的 `--data-root` 读取本地材料。若 GitHub main 已更新，读取最新 issue 与本规格，不让本地旧文档覆盖它们。

先记录代码基线，并验证下表文件存在。路径相对 `--data-root`：

| 输入 | 用途与注意事项 |
|---|---|
| `configs/hal_research_manifest.json` | 17份归档的固定 URL、版本、大小、SHA256、local_path；必须核验字节，不能只检查文件存在 |
| `data/derived/existing_runs/runs.jsonl` | 1197行的既有 episode_id、归档hash、task关联、benchmark、scaffold、历史commit和观察事实；保持原ID |
| `data/derived/existing_runs/label_candidates.jsonl` | 按 episode_id 关联 A/B 候选资格；同一episode可能有多个协议行，不可按整表长度计算样本数 |
| `data/derived/existing_runs/protocol_summary.json` | 冻结派生文件指纹；核验本项读取的派生输入，输出不得覆盖这些旧文件 |
| manifest 中各 `local_path` | 原始归档，只读；不执行归档中的代码、工具调用或shell文本 |
| `tools/hal_pipeline.py` | 阅读 `parse_archive`、`outcomes` 了解现有映射；不重跑整条旧pipeline、不重写token计量或标签 |
| `research_plan/src/haldata.py` | `read_archive(path)` 可读取已有HAL上传格式；仅复用经审查的读取部分，不运行旧pilot或导入训练入口 |
| `docs/evidence/hal_review_2026-09-28/historical_code_receipts.json` | 已保存SAB、Generalist、CORE历史源码回执；路径相对该回执目录 |
| `docs/evidence/hal_implementation/historical_code/receipts.json` | 已保存另外两个历史版本；验证内容hash后复用 |
| `docs/handoff/label_decisions.md`、`docs/research/papers/HAL.md` | 本地历史研究解释；其中旧方法建议不等于当前批准方案 |

公开 [事实复核](../../reports/research_audit/current_evidence.json) 是比对基线，不能充当原始输入。缺少本地数据时，列出确切缺失路径，可继续写工具和合成fixture测试；停止真实数据部分，保持未验收。不要索要GPU、下载替代数据集、自动扩大采样或伪造记录。缺历史源码可按已经记录的确切commit只读获取，保存URL/字节数/SHA256回执；无需运行它。

## 3. 研究负责人已定位的证据和待核点

### 3.1 分母与覆盖

旧事实审计记录17归档、1197运行、312任务身份；整次token cap均未知。B含603个失败候选：SAB 478、CORE 48、SWE 77；其中已解析2个timeout，其他601个没有顶层停止标记。SAB的478失败中460个有评估日志。所有这些数字都是待复算基线，不能写进程序作为输出常数；差异必须定位来源或映射，不能改数据凑数。

建立覆盖所有1197运行的事实索引，同时独立报告603个B失败子集；保留SciCode和TAU的来源核查，但不能将其自动纳入主实验。按benchmark/scaffold/历史commit汇总，不能把不同配置当成独立任务。

### 3.2 历史源码入口

以下12个HAL历史commit从现有事实表定位，归档到commit的关联仍应由新工具交叉核验 `git_info.commit`。URL中的commit固定，不能用仓库当前main的默认值填补历史缺失。源码中存在规则，不证明某条运行实际触发。

| 范围 | HAL历史commit | 需要阅读的路径与分支 |
|---|---|---|
| SAB Self-Debug，2份归档 | `23fc5665d6804fa72240f479e38f73fb53600002` | `agents/sab_example_agent/science_agent.py`：`write_program`、`step`、`solve_task` |
| SAB Self-Debug，2份归档 | `eb094b928198c6e1029a8e0c247576c78a1fe9f7` | 同上；验证文件内容是否与前项相同，不能只凭scaffold名称继承 |
| SAB Self-Debug，1份归档 | `edfe626b0e96fbf92fb8a41a705e31205d716e1e` | 同上；已有本地回执 |
| SAB Generalist，1份归档 | `bc575cd58bdb0a203c08952169df7e5d3330b8d8` | `agents/hal_generalist_agent/main.py`：费用回调、agent参数、最终返回 |
| CORE，1份归档 | `c7354ebd3ce3d284e3c89150e1218836c42eccac` | `agents/core_agent/main.py`：max_steps、可选budget和运行返回 |
| CORE，1份归档 | `7e56e6688e288e8db86b3612b551370330ae218d` | 同上；已有本地回执 |
| SWE Generalist，1份归档 | `8a0e2933c7e2b6162c149810aff02a3d4cbcd48c` | `agents/hal_generalist_agent/main.py`：历史max_steps及回调是否存在 |
| SWE Generalist，1份归档 | `6a44aedf5ca8bfc81f9354658a4f66553eee730d` | 同上；不可把SAB配置或另一SWE版本套入 |
| SWE-Agent，1份归档 | `02a2500e9883ecc022b3eeae29bc5b557788b3c7` | `.gitmodules`、`agents/SWE-agent-v1.0` 的gitlink；进入确切子模块版本查费用异常和autosubmit |
| SWE-Agent，1份归档 | `85513dbe3ac92d135c304cd9ef5920e5a78f436f` | 同上；配置覆盖值优先与归档 `agent_args` 对照 |
| SciCode，3份归档 | `0ac45fa43a60658ec037b354b5039d3131317069` | `agents/scicode_example_agent/main.py`、`hal/benchmarks/scicode.py`；区分生成过程与评估进程 |
| TAU airline，2份归档 | `b64fc7cc5c0aa7ea2fbf197d835805460bcf2e7b` | `agents/taubench_tool_calling/tool_calling.py`、`pyproject.toml`；从pin继续查tau依赖的solve和env.step |

HAL源码入口格式：`https://github.com/princeton-pli/hal-harness/blob/<commit>/<path>`。将真正读取的完整URL、文件hash、相关行号及依赖pin记录进来源注册表。子模块仓库不能猜测，按对应版本的 `.gitmodules` 和gitlink核实。

已复核的初步机制解释见 [STOPPING_EVIDENCE_AUDIT.md](STOPPING_EVIDENCE_AUDIT.md)：SAB Self-Debug有代码无变化、程序执行/输出文件等提前结束分支；Generalist费用回调曾把输入token计数用于输出计数；CORE配置40步不能当成实际触发证据。三者都有对应历史源码回执。

另外两项是必须复查的疑点，当前不当作已验收结论：SciCode评估脚本的运行超时可能与agent停止处在不同阶段；TAU依赖中solve的默认步数与归档taken_actions长度可能不一致。后者应先核对wrapper传参、依赖pin、动作计数方式和运行版本，记录矛盾；不能直接将动作数解释为步数上限触发，也不能擅自修改默认上限。若疑点不成立，明确报告纠正依据。

## 4. 按顺序执行的工作包

1. **预检和冻结。** 核验17归档、实际读取的派生输入与源码回执。建立 episode_id → 归档hash/task键的唯一映射。重复ID、候选悬空、commit不一致、hash漂移均应清楚报错；不生成部分文件后仍报告通过。
2. **来源注册表。** 对照上表核实每份归档的scaffold与实际commit。可合并内容相同的源码blob，但仍保留每个历史commit的绑定；记录哪些依赖版本可确定、哪些运行版本无法核实。
3. **逐运行提取。** 从归档直接保存来源定位符和观察类别；覆盖规则、任务层终止标记、调用层finish_reason、最终评估diagnostics、中间成功检查可见性。实现确定性的关联，不靠任务文本相似度或列表位置猜join。
4. **分层汇总。** 全部1197运行与B失败子集分别给分母；标明哪些数据已检查但缺字段、哪些尚未检查、哪些相互矛盾。反例定位保存在本地，不在公开报告中输出任务标识或正文。
5. **解释与交接。** 报告能支持和不能支持的判断，为每项解释提供来源；不可确定则保留unknown及原因。提交实现、测试、聚合结果和本地回执，交研究负责人逐项验收。

不要开展新模型实验、补采轨迹、重跑判分器、改A/B纳入规则、重算旧token事实、改数据划分、生成论文或创建下一issue。

## 5. 输出契约

建议CLI入口为 `tools/audit_stopping_evidence.py`。内部函数、文件拆分和实现方法可由实现者选择，但必须满足下列接口与证据语义。

### 5.1 可提交的输出

- `configs/hal_stopping_sources.json`：历史源码注册表。包括repository、commit、path、URL、SHA256、相关行号、规则范围、依赖pin、缺口。不得包含逐题数据。若某源码未获得，hash保持null并标未核实，不补造。
- `reports/research_audit/stopping_evidence_summary.json`：固定输入hash、工具版本、完整覆盖/缺失/矛盾数量、分层分母和四个识别条件的证据覆盖。只含安全聚合；不输出episode_id/task_id/提示词/答案/逐题结果或用量/日志摘录/本机绝对路径。
- `docs/research/STOPPING_EVIDENCE_AUDIT.md`：更新版本、可核查发现、未知、反例类型、对研究方向的影响和解释限制。引用注册表、聚合报告及固定源码链接，不把初核意见直接改成验收结论。
- 新工具、必要的合成fixture测试与运行说明。读取加密上传格式时只复用经检查的最小读取逻辑，记录依赖，不把整套历史pilot复制进公开仓库。

### 5.2 本地输出

在受控根目录的 `data/derived/stopping_audit/` 保存：

- `run_evidence.internal.jsonl`：每个既有episode恰好一行，共1197行；同一运行的多个证据项放在同一行。保留原episode_id和task关联，仅在本地使用。
- `source_receipts.internal.json`：实际输入路径/文件大小/hash、获取或复核记录、归档内部JSON成员位置、证据索引hash、命令和退出状态。
- `review_examples.internal.json`：按证据类型选择的可定位样例及疑点，优先覆盖两条timeout、评估日志存在但停止未知、不同版本规则、源/运行矛盾。只读引用，不执行其中代码。

这些输出应为新路径，不覆盖 `existing_runs/` 下冻结文件。忽略规则必须生效；公开汇总采用字段白名单，不能序列化整条原记录后删几个字段。

### 5.3 私有索引最低字段

| 字段 | 含义及约束 |
|---|---|
| `schema_version`, `episode_id`, `benchmark`, `scaffold`, `config_id` | 绑定版本及既有身份；config_id不是独立任务ID |
| `archive_sha256`, `code_commit`, `raw_record_pointer` | 精确归档、历史代码和原始JSON定位；不能只写论文链接 |
| `in_B_failure_subset` | 由既有候选表唯一关联得到；不改变纳入规则 |
| `configured_rules` | 每条规则带scope、unit、value、来源；例如per_call/token、run/USD、run/steps，未知值用null |
| `observations` | 证据项列表；每项含layer、code、source_ref、field_pointer、presence、interpretation_scope；必要原文摘录只留本地 |
| `task_termination` | 实际任务终止的观察类别、证据引用或unknown；必须与配置规则和最终判分分开 |
| `source_runtime_consistency` | compatible / conflicting / unknown，记录依据；compatible不证明源码绝对就是运行版本 |
| `identification_assessment` | `T_gt_U`、`same_continuation`、`first_success_visibility`、`conditional_independence` 四项分开，每项status为supported/contradicted/unknown，并有理由、evidence_refs和判断来源 |
| `limitations`, `approved_for_training` | 限制明确；本issue始终不批准训练 |

`presence` 至少区分 present / absent / empty / uninspected；已核查的原字段没有数据才可标absent/empty。unknown不等于false。判断层由明确研究依据支持，程序不得从“success=false”“存在预算”“有timeout”“最终可成功”自动填supported。没有逐运行证据支持时四项可以保持unknown；研究负责人检查其理由与覆盖，而不是要求所有格子都填成确定结论。

层级至少区分 configuration_rule、task_runtime_marker、call_finish_reason、evaluation_diagnostic、intermediate_success_observation；一个evaluator timeout应落在evaluation_diagnostic，不能直接变成agent runtime cutoff。SAB log_info是评估diagnostics，LLM finish_reason是单调用事实。保留原有顶层TIMEOUT识别，同时核对其产生阶段，不能仅凭字符串认定删失成立。

## 6. 必须证明的行为

测试使用人工构造的小JSON，不复制真实任务、答案或测试标签。每项验证一个易造成错误科学结论的边界：

1. 仅存在 `max_tokens` 时，记录单调用限制，整次token cap仍未知；美元/步数限制也不转换为token cap。
2. 有非空评估log_info而无任务终止标记时，保留diagnostics，不能推断已观察到agent停止原因。
3. 最终输出带TIMEOUT或ERROR时，保留显式观察；四个识别条件不会因此自动supported。
4. finish_reason只改变单调用证据；评估进程超时不自动改变agent停止类别。
5. 缺失与空值不填零、不当作否定；未检查不能伪装为检查后缺失。
6. 候选表的A/B多行不会复制运行；重复episode、悬空关联或不唯一join必须报错。
7. 来源hash/大小/commit不符时失败并记录缺口；不能静默使用最新源码。
8. 源码规则与运行观察冲突时保留矛盾，不能强行把运行归入该规则；用虚构的步数/动作例子验证即可。
9. 公共汇总采用白名单，不能带出私有ID、原文、逐题真值/用量或本地绝对路径；日志同样如此。
10. 相同输入再次运行得到相同证据内容hash；时间戳等运行元数据与确定性内容分离。输入文件hash前后不变。

不为每个字典字段写一条机械测试；重点覆盖上述语义边界与失效处理。可复用已有测试设施，公开clone应能在无真实数据时运行这些测试。

## 7. 可执行命令与交回格式

以下是实现完成后应支持的接口，当前还不是已经存在的命令。将 `/path/to/controlled-workspace` 替换为本地交接说明中的受控根目录；不要在公开issue、日志或报告中写出真实路径：

```sh
python3 -m unittest discover -s checks -p 'test_stopping_evidence.py' -v
python3 tools/audit_stopping_evidence.py \
  --data-root '/path/to/controlled-workspace' \
  --source-index configs/hal_stopping_sources.json \
  --private-output '/path/to/controlled-workspace/data/derived/stopping_audit' \
  --public-output reports/research_audit/stopping_evidence_summary.json
```

真实数据运行默认离线；缺源码或版本映射清楚报错/标未核实，不在审计过程中静默下载或改写输入。工具退出状态要区分输入损坏/关联失败与科学证据unknown；后者可成功产出调查，但不得成为科学通过。

完成后在 #9 评论交回：实现提交/PR链接、运行命令与退出状态、输入/输出hash、全量和B子集分母、每类证据覆盖、偏离旧数字的解释、四项识别判断、反例与未解决问题、公开文件清单及相对 `--data-root` 的本地回执位置。提交信息用 `Refs #9`，避免 `Closes #9` 提前自动关闭。不要自动推送受控历史分支或发布本地输出。

研究负责人验收时至少检查：全部归档和运行的覆盖与唯一性；证据定位可回查；上述关键反例；已知计数差异；未知和矛盾是否被隐藏；公开输出边界。仅测试通过或文档写完均不足以关闭。调查验收不批准训练、不自动关闭M0；在 #9 验收后才决定并创建下一issue。
