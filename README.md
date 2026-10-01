# 运行前预测成功完成所需 token

本项目面向 NeurIPS／ICML／ICLR 正式主会，研究目标是预测成功完成任务所需的 token 数量；当前首轮采用可直接观测的成功运行终点作为操作化。目标不保证录用，也不自动改投 workshop。研究进度以 [GitHub Issues](https://github.com/shuo19mo/prediciton-token/issues) 与 [Milestones](https://github.com/shuo19mo/prediciton-token/milestones) 为准，当前执行项为 [#15](https://github.com/shuo19mo/prediciton-token/issues/15)，归属 [M3 · 强基线与最小实证](https://github.com/shuo19mo/prediciton-token/milestone/4)。

## 当前协议与已验收数据

- [冻结实验协议](docs/handoff/SUCCESS_ENDPOINT_EXPERIMENT_V1.md)：与 #15 一致，绑定代码版本 `480e548f340f12d854064bbf8208d90b008893ef`。
- [#14 数据准入验收](https://github.com/shuo19mo/prediciton-token/issues/14#issuecomment-5901809512)：PASS 仅表示达到首轮实验的数据准入条件，不代表师兄已确认、模型已训练或研究贡献已成立。
- [数据就绪证据](docs/research/DATA_READINESS_2026-09.md)：来源、计数、指纹、分组和限制。
- [滚动研究路线](docs/research/ROLLING_ROADMAP.md)：七个阶段的问题与验收边界。
- [GitHub 工作流](docs/research/GITHUB_WORKFLOW.md)：角色、状态和文件边界。

## 研究边界

本轮标签 `actor_total_tokens_observed` 表示成功运行记录终点的 actor token 用量；失败记录不作删失样本，也不推断其潜在成功成本。不同 token 阈值内的成功概率是主实验有效后的可选扩展。模型实现、训练与调参由师兄负责；Astra 规划并独立验收，Luna 检查交接接口并独立评价，主代理管理工作区和 GitHub。论文写作暂停，待证据和贡献审查后再议。

只复用已有 benchmark 运行记录；不重跑任务、benchmark 或原判分器，不生成新轨迹，不公开原始记录、逐题真值、参考答案、凭据或受控训练/审阅包。

## 文档入口

- [项目范围与分工](docs/PROJECT_CONTEXT.md)
- [进度导航](docs/STATUS.md)
- [R00–R07 阶段映射](docs/EXECUTION_PLAN.md)
- [研究文档目录](docs/research/README.md)
