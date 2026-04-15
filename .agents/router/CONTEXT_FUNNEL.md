# 知识漏斗与自主检索 (Context Funnel & Agentic Search)

## 🎯 核心哲学：双向游走 (Bidirectional Search)
大模型（Agent）不会被硬塞大段代码，必须像人类开发者一样，**沿着索引图谱自主寻找知识 (正向漏斗)**，并且在完成任务时**沿着索引寻找挂载点写回知识 (反向漏斗)**。

## 🧭 正向漏斗：检索打法规范 (Navigation Rules)

### 1. 强制入口 (The Root)
任何需求的上下文收集，**必须且只能**从读取以下文件开始：
👉 `[KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md)`

### 2. 逐层下钻 (Drill-down)
1. **看全貌**：在 `KNOWLEDGE_GRAPH.md` 中，找到对应的局部索引链接（如 `[domain/index.md](../llm_wiki/wiki/domain/index.md)`）。
2. **看局部**：调用 `Read` 工具读取该局部 `index.md`。
3. **定点阅读**：在局部 `index.md` 中找到具体的文档链接（如 `[[user_login_spec.md]]`），再次调用 `Read` 读取该文档。

### 3. 兜底搜索权 (Fallback Search)
仅当通过索引树实在找不到特定概念时，Agent 才有权使用 `Grep` 或 `SearchCodebase` 工具在 `llm_wiki/wiki/` 目录下进行关键词搜索。

---

## 🏗️ 反向漏斗：写回打法规范 (Write-back Rules)
在 `Archive` 归档阶段，Agent 需要提取知识并写入 Wiki，此时必须**反向应用**知识漏斗。

1. **寻找挂载点**：读取 `[KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md)`，判断新增的 API 属于哪个业务域（如 `trade` 还是 `user`）。
2. **WAL 碎片化写回（并发安全）**：禁止直接修改公共 `index.md`。将提取出的知识以“碎片文件”形式写入对应域的 `wal/` 目录（例如 `../llm_wiki/wiki/api/wal/20260415_feature_x_api_append.md`）。
3. **合并与拆分**：全局索引的合并由人类定期合并，或使用可选脚本在低冲突窗口合并。若合并后 `index.md` 超过阈值，再执行拆分。

## ⚠️ 纪律约束 (Constraints)
- **链接标准**：`.agents/` 体系内文档优先使用相对路径（相对当前文件），避免 `.agents/...` 形式的路径幻觉。
- **技能联动**：如果在游走过程中发现不知道如何解析复杂的 ER 图或流程图，允许调用 `[trae-skill-index](../skills/trae-skill-index/SKILL.md)` 寻找帮助。
- **Index 摘要要求**：所有 `index.md` 文件在指向子文档时，必须包含 1-2 句话的摘要说明。
