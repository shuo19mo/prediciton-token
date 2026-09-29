# GitHub研究管理约定

仓库：[shuo19mo/prediciton-token](https://github.com/shuo19mo/prediciton-token)。GitHub Issues/Milestones是唯一动态进度入口；Git保存详细研究产物及其演变。STATUS仅导航，work_queue仅映射R00–R07；旧状态冻结为历史快照，不与GitHub双写。

每个板块有主issue。当前阶段的子issue须包含：问题与重要性、证据与来源、待证假设、工作步骤、依赖/负责人、交付物、验收、反证、状态/结论/证据位置。后续阶段只保留概要，进入时再细化。负责人在正文写明；不能替师兄签认或未经授权联系他人。

开始时移除blocked（如果依赖确已满足），添加in-progress并评论实际工作。发现变化时评论来源/版本、结论及方向影响。完成时评论验收、限制和固定Git提交链接，再关闭issue；负结论也能完成调查。训练依赖保留开放并注明需要师兄返回什么。用literature、data、method、experiment、review区分类型，用blocked、needs-training、in-progress区分需要的状态；GitHub open/closed表示生命周期。

Milestone描述包含问题、进入条件、交付、证据门槛和重构条件。即使所有子issue关闭，仍需主issue明确给出阶段验收。问题无效/数据不足时记录重构，不把调查结束算作科学主张通过。

初始配置 `configs/github_research_bootstrap.json` 是经过审阅的GitHub创建意图与显式操作记录，不是活动任务镜像。`tools/manage_research_tracker.py`复用已存在的milestone和issue、保留后续人工修改，并用操作标记防止重复评论。初始化通过后取消push触发，只保留手动运行；后续优先使用正常GitHub界面/CLI/连接器更新状态。必要的管理操作仍须有明确授权及范围。

初始化采用仓库自有GitHub Actions的临时GITHUB_TOKEN，仅给contents:read和issues:write；无第三方action，无凭据导出，无本地数据访问，无训练或实验。此方式符合[GitHub官方的issue创建示例](https://docs.github.com/en/actions/tutorials/authenticate-with-github_token)。不得授予内容写入、管理权限或创建额外凭据来扩大范围。

研究文档、解析/核查代码、实验候选规格、来源manifest及安全聚合报告可纳入Git；有意义的提交关联issue，如 `Refs #8`。原始数据、调用正文、参考答案、逐题真实结果/用量、测试标签、训练/审阅包、凭据和第三方缓存不提交。来源URL、revision和SHA256追踪本地只读材料，仓库不是数据发布。

历史笔记中包含真实逐运行样例的页面和派生家族映射也保留本地。旧资料内指向这些页面、data/、docs/evidence/和paper/正文的链接是本地证据入口，不表示这些材料已在GitHub发布；完整本地检查需要受控工作区，干净clone只含安全子集。

正式实验前需固定数据/代码/规格版本、同题分组、输入白名单、选优规则和测试查看记录。旧SAB开发暴露不能抹去。研究负责人可保有评价真值，但训练进程不得访问；目录名字不是隔离证据。变更正式测试后必须登记探索版本和理由。

工程检查、科学问题解决、稿件完成、内部投稿审查、投稿和实际录用各有独立证据。论文写作当前暂停，不因文档、代码或GitHub任务创建完毕而解除。
