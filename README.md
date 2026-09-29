# 运行前预测成功完成所需 token

面向 NeurIPS／ICML／ICLR 正式主会的研究项目。优先复用 HAL 已公开的历史运行记录，不重跑agent、benchmark或判分器，不保证录用。

**当前交付是研究路线、milestones和可执行issues。论文写作暂停，待真实证据和贡献验收后再开展。**

## 研究入口

- [GitHub Milestones](https://github.com/shuo19mo/prediciton-token/milestones)：整体阶段与证据验收标准。
- [GitHub Issues](https://github.com/shuo19mo/prediciton-token/issues)：唯一动态进度、讨论与验收入口；一次只执行一个issue，验收后再创建下一项。
- [滚动研究路线](docs/research/ROLLING_ROADMAP.md)：7个阶段，只细化当前M0。
- [项目现状诊断](docs/research/PROJECT_DIAGNOSIS.md)：事实、工程、假设与科学未知。
- [停止证据初核](docs/research/STOPPING_EVIDENCE_AUDIT.md)：正在继续的研究核查。
- [管理与文件边界](docs/research/GITHUB_WORKFLOW.md)：GitHub状态、Git版本及本地受控材料。

## 研究边界

主目标为运行前预测成功完成所需token。观察成功终点、失败停止用量和潜在成功成本分开；最终可成功是工作假设，不证明失败都是有效右删失。survival是候选，方法由证据决定；预算成功概率仅为可选扩展。

Codex负责文献、数据、定义、实验设计、独立评价及证据成熟后的写作；师兄负责模型实现、训练和调参。不自动投稿、联系他人、购买资源或发布原始/逐题数据。

现有R00–R07作为工程接口映射到milestones，历史完成不等于科学通过。旧实验清单和初稿仅供参考，不规定未来路线。

## 本仓库与本地工作区

本轮只同步经过逐份审查的新研究管理文件、核查代码和聚合诊断。历史研究资料、原始日志、逐运行事实、参考答案、测试标签和训练/审阅包保留本地；本仓库不是数据集发布。旧资料的本地路径不代表GitHub已包含这些内容。

已知工程基础可复用，当前没有真实预测效果证据；贡献尚未建立。当前审计数字和来源hash见[聚合复核](reports/research_audit/current_evidence.json)。

```sh
# 本仓库可独立运行的管理程序离线测试
python3 -m unittest discover -s checks -p test_tracker_management.py -v
# 下项需要本地已固定的历史数据及manifest；不会训练或执行benchmark
python3 tools/audit_research_evidence.py
```

完整本地工作区另有事实/分组/文档检查与73项离线测试；它们只证明对应工程范围，不能替代研究门槛。
