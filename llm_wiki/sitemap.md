# LLM Wiki 全局知识图谱 (Sitemap)

## 📌 根节点导航 (The Root)
欢迎来到 LLM Wiki。这里是整个系统知识图谱的根节点。请根据任务需求，点击对应的链接进行**逐层下钻**。

> **⚠️ Agent 纪律**：禁止越级瞎猜文件路径，必须通过阅读以下链接进行探索。所有新增知识也必须挂载到这棵树上。

### 0. 项目级规则入口 (Project Rules)
*这是本仓库的“总入口规则”。任何 Agent 应先阅读该文件，再进入 Sitemap 下钻。*
- 📌 **[Project Rules](../project-rules.md)**：后端开发主流程的规则入口（检索纪律、生命周期、纠偏与归档）。

### 1. 核心愿景与规范 (Philosophy & Schema)
*了解我们为何而建，以及必须遵守的代码与设计模板。*
- 🎯 **[系统愿景与设计原则 (Purpose)](purpose.md)**：开发前的必读哲学，防过度设计。
- 📑 **[全局规范与契约模板 (Schema)](schema/openspec_schema.md)**：所有提案和设计的骨架标准。
- 🛠️ **[系统能力与技能大盘 (Skills)](../skills/trae-skill-index/SKILL.md)**：当前可用的所有专有 Agent 技能（如系统设计、Java 规范、文档同步等）汇总。

### 2. 活跃知识域 (Active Domains)
*按业务与技术切分的子域入口（一级节点）。需要什么上下文，点进哪个 Index。*

- 🧠 **[领域模型与业务字典 (Domain)](wiki/domain/index.md)**：包含业务名词解释、状态机、行业数据字典等。
- 🔌 **[API 契约 (API)](wiki/api/index.md)**：系统所有对外暴露的接口定义与入参出参汇总。
- 🗄️ **[数据模型 (Data)](wiki/data/index.md)**：数据库表结构、索引设计、ER 图。
- 🏗️ **[架构决策 (Architecture)](wiki/architecture/index.md)**：核心架构图、安全基线、ADR (架构决策记录)。
- 📝 **[活跃需求 (Specs)](wiki/specs/index.md)**：当前正在开发或近期完成的 `openspec.md` 需求文档集。
- 🧪 **[测试与证据 (Testing)](wiki/testing/index.md)**：单元测试规范、客观测试证据落盘标准。
- 🚦 **[动态偏好与禁忌 (Preferences)](wiki/preferences/index.md)**：人类主观打分沉淀的历史经验、安全红线和代码禁忌。*(注意：当偏好库超过 500 行时，Agent 必须主动将其按域或技术栈拆分为子文件)*

### 3. 冷数据区 (Cold Storage)
*已失效或被提取后的历史资料。*
- 🧊 **[归档区 (Archive)](archive/index.md)**：已完成提取的过期需求文档和废弃规范。
