# 知识漏斗与自主检索 (Context Funnel & Agentic Search)

## 🎯 核心哲学：双向游走 (Bidirectional Search)
大模型（Agent）不会被硬塞大段代码，必须像人类开发者一样，**沿着索引图谱自主寻找知识 (正向漏斗)**，并且在完成任务时**沿着索引寻找挂载点写回知识 (反向漏斗)**。

## 🧭 正向漏斗：检索打法规范 (Navigation Rules)

### 1. 强制入口 (The Root)
任何需求的上下文收集，**必须且只能**从读取以下文件开始：
👉 `[sitemap.md](/.trae/llm_wiki/sitemap.md)`

### 2. 逐层下钻 (Drill-down)
1. **看全貌**：在 `sitemap.md` 中，找到对应的局部索引链接（如 `[domain/index.md](/.trae/llm_wiki/wiki/domain/index.md)`）。
2. **看局部**：调用 `Read` 工具读取该局部 `index.md`。
3. **定点阅读**：在局部 `index.md` 中找到具体的文档链接（如 `[[user_login_spec.md]]`），再次调用 `Read` 读取该文档。

### 3. 兜底搜索权 (Fallback Search)
仅当通过索引树实在找不到特定概念时，Agent 才有权使用 `Grep` 或 `SearchCodebase` 工具在 `llm_wiki/wiki/` 目录下进行关键词搜索。

---

## 🏗️ 反向漏斗：写回打法规范 (Write-back Rules)
在 `Archive` 归档阶段，Agent 需要提取知识并写入 Wiki，此时必须**反向应用**知识漏斗。

1. **寻找挂载点**：读取 `[sitemap.md](/.trae/llm_wiki/sitemap.md)`，判断新增的 API 属于哪个业务域（如 `trade` 还是 `user`）。
2. **更新局部索引**：找到该域的局部 `index.md`，将提取的 API 签名或数据库表结构**追加**进去。
3. **拆分阈值**：如果更新后的局部 `index.md` 超过 500 行，主动创建一个子目录（如 `wiki/api/trade/index.md`），将原文件内容拆分，并在上一级 `index.md` 中补充指向新子目录的链接。

## ⚠️ 纪律约束 (Constraints)
- **绝对路径标准**：生成或读取的任何 Markdown 链接，必须采用从项目根目录出发的绝对路径（如 `/.trae/llm_wiki/wiki/...`）或相对于根目录的格式。
- **技能联动**：如果在游走过程中发现不知道如何解析复杂的 ER 图或流程图，允许调用 `[trae-skill-index](/.trae/skills/trae-skill-index/SKILL.md)` 寻找帮助。
- **Index 摘要要求**：所有 `index.md` 文件在指向子文档时，必须包含 1-2 句话的摘要说明。
