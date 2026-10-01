# R00–R07 阶段接口映射

本文只映射保留的工程流程和研究职责。GitHub Issues/Milestones 保存实时状态；阶段映射不表示研究或科学门槛已通过。

当前执行项是 [#15](https://github.com/shuo19mo/prediciton-token/issues/15)，归属 [M3 · 强基线与最小实证](https://github.com/shuo19mo/prediciton-token/milestone/4)。按[当前冻结实验协议](handoff/SUCCESS_ENDPOINT_EXPERIMENT_V1.md)执行；[#14 数据准入验收](https://github.com/shuo19mo/prediciton-token/issues/14#issuecomment-5901809512)及[滚动研究路线](research/ROLLING_ROADMAP.md)可供导航。

| 阶段 | 职责 | 边界 |
| --- | --- | --- |
| R00 | 研究范围纠正 | 以最新用户指令和 GitHub 当前 issue 为准；不恢复已撤销的自采路线。 |
| R01 | 已有数据覆盖表 | 描述可复用来源、基准覆盖、记录数量和已知缺口；不把汇总平均伪造成任务样本。 |
| R02 | 固定已有日志获取清单 | 固定公开来源、版本、URL、字节数和 SHA-256；数据只读保留。 |
| R03 | 统一任务级事实表 | 对齐任务、配置、结果、usage 与来源事实；缺失不填零，actor/simulator/evaluator 分列。 |
| R04 | 历史数据契约与标签候选 | 依据真实字段建立解析契约并记录标签候选及依据；survival 假设不预设，失败不自动删失。 |
| R05 | 分组、划分与输入白名单 | 同题变体和已知重复不跨分区；初始输入排除运行后结果、token 和参考答案。 |
| R06 | 受控交接 | 隔离训练与评价材料，保留未知和限制；不把 `review_ready` 当作训练授权。 |
| R07 | 返回预测与独立评价 | 检查冻结预测并依固定协议评价；模型训练与调参由师兄负责。 |

具体实施与验收范围由当前 [GitHub issue](https://github.com/shuo19mo/prediciton-token/issues) 决定。`configs/work_queue.json` 仅作为接口映射，不是动态任务队列。
