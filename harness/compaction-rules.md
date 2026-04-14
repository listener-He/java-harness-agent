# 🗜️ 知识提取与防膨胀规则 (Compaction Rules)

**Focus**: 定义在生命周期的 `Archive` 阶段，如何将单次特性的 `openspec.md` 拆解、压缩并合并到长期的全局知识图谱中，防止文件无限增多和膨胀。

---

## 1. 核心目标 (Core Objectives)
- **去重 (De-duplication)**：将分散在各个需求文档里的同类知识（如所有涉及 User 的表结构）聚合到一处。
- **瘦身 (Slimming)**：当聚合文档过长时，进行自动拆分。
- **冷热分离 (Cold/Hot Separation)**：活跃需求提取完毕后，必须转入冷宫（Archive）。

---

## 2. 知识提取协议 (Extraction Protocol)

在 `Archive` 阶段的 `post_hook` 中，大模型必须对本轮的 `openspec.md` 执行以下提取动作：

### 2.1 业务领域提取 (Domain Extraction)
- **扫描**：`openspec.md` 中的【业务上下文与意图】章节。
- **动作**：如果出现新的业务名词、枚举状态或角色定义，将其提炼为简短的定义（Key-Value 格式），**追加**到 `.trae/llm_wiki/wiki/domain/index.md` 或该域下的具体字典文件中。

### 2.2 数据模型提取 (Data Extraction)
- **扫描**：`openspec.md` 中的【数据模型】章节。
- **动作**：将新增的表结构定义（无需完整的 SQL，提炼为表名、核心字段、索引策略），合并到 `.trae/llm_wiki/wiki/data/index.md` 或对应的聚合文件中。

### 2.3 接口契约提取 (API Extraction)
- **扫描**：`openspec.md` 中的【接口契约】章节。
- **动作**：将新增或修改的接口签名（Method + Path + 核心出入参简述），更新到 `.trae/llm_wiki/wiki/api/index.md`。

---

## 3. 归档与死链清理 (Archiving & Cleanup)

1. **移动文件**：知识提取完成后，将当前 Session 的 `openspec.md` 移动到 `.trae/llm_wiki/archive/` 目录下（重命名为 `YYYYMMDD_特性名称.md`）。
2. **清理活跃索引**：打开 `.trae/llm_wiki/wiki/specs/index.md`，将该特性的链接从中删除，或移至底部的“已归档”区块。

---

## 4. 防膨胀硬约束 (Anti-Bloat Hard Limits)

> **⚠️ 500 行自动拆分规则**
> 
> 在执行知识合并时，如果发现目标文件（例如 `api/index.md`）的长度**超过 500 行**，必须立即触发重构：
> 1. 按业务模块（如 `User`, `Trade`, `Order`）创建子目录及新的 `index.md`。
> 2. 将原文件内容拆分到各个子域的 `index.md` 中。
> 3. 更新原文件，使其仅保留指向子域的目录链接。
> 4. **同步更新根节点**：如果改变了一级目录结构，必须同步更新 `.trae/llm_wiki/sitemap.md`。