# 项目范围与分工

项目总体研究目标是预测成功完成任务所需的 token 数量，面向 NeurIPS／ICML／ICLR 正式主会。本轮首轮实验采用一项可观测目标：对 benchmark evaluator 标记成功的运行，预测其记录终点的 actor token 用量。失败记录作为事实保留，不作为删失标签，也不推断其潜在成功成本。

当前执行项为 [#15](https://github.com/shuo19mo/prediciton-token/issues/15)，归属 [M3 · 强基线与最小实证](https://github.com/shuo19mo/prediciton-token/milestone/4)；当前协议见[冻结实验协议](handoff/SUCCESS_ENDPOINT_EXPERIMENT_V1.md)，路线见[滚动研究路线](research/ROLLING_ROADMAP.md)。[#14 验收](https://github.com/shuo19mo/prediciton-token/issues/14#issuecomment-5901809512)仅表示 M2 数据准入通过。数据准入通过不等于师兄授权训练、模型效果已知或研究贡献成立。

按 #15 分工：Astra 规划并独立验收；Luna 检查返回接口并独立评价；师兄确认协议和受控数据范围，负责模型实现、训练和调参；主代理管理工作区与 GitHub。任何人不得代替师兄确认或签字。

只复用已有 benchmark 运行记录。不重跑任务、benchmark 或原判分器，不生成新轨迹。数据准备步骤不训练模型。原始记录、逐题真值、参考答案、凭据和受控训练/评价包不公开。论文写作暂停，待证据与贡献审查后再决定。
