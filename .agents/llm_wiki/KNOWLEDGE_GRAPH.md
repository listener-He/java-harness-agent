# LLM Wiki Knowledge Graph (Root Index)

This file is the root of the wiki. Use it to navigate by drilling down through indexes. Do not guess paths.

## Hard Rules (MUST)
- You MUST start navigation from this file, then drill down via `index.md` files.
- You MUST NOT jump directly to random documents by guessing paths.
- Any new stable knowledge MUST be attached to this tree (via the correct domain).

## 0. Project Entry
- **[AGENTS.md](../../AGENTS.md)**: the single entry point (routing, funnel, lifecycle, write-back).

## 1. Philosophy & Templates
- **[Purpose](purpose.md)**: why this system exists and what it optimizes for.
- **[OpenSpec Schema](schema/openspec_schema.md)**: the contract template for proposals and designs.
- **[Skills Index](../skills/trae-skill-index/SKILL.md)**: available specialist skills.

## 2. Active Domains (Drill-down Indexes)

每个维度的 `wal/` 子目录存放待合并的增量写回文件，格式参见 [WAL 格式规范](schema/wal_format.md)。

| 维度 | 链接 | 内容摘要 | 典型写回触发 |
|------|------|----------|-------------|
| Domain | **[domain/index.md](wiki/domain/index.md)** | 业务实体、状态机、规则、术语表 | 修改 Service/Entity/Enum |
| API | **[api/index.md](wiki/api/index.md)** | 接口清单、外部集成、破坏性变更 | 修改 Controller/Client/DTO |
| Data | **[data/index.md](wiki/data/index.md)** | 表结构、索引、Migration、敏感数据 | 修改 Mapper.xml/SQL/Entity字段 |
| Architecture | **[architecture/index.md](wiki/architecture/index.md)** | ADR、模块地图、集成拓扑、SLA | 引入中间件、调整模块边界 |
| Preferences | **[preferences/index.md](wiki/preferences/index.md)** | 反模式、必须模式、团队决策、安全基线 | Review 发现、事故归因 |
| Testing | **[testing/index.md](wiki/testing/index.md)** | 测试分层要求、证据模板、覆盖率基线 | 每次 QA 阶段后 |
| Reviews | **[reviews/index.md](wiki/reviews/index.md)** | 评分历史、高频发现、重构 Backlog | 每次 Archive 后固定写入 |
| Specs | **[specs/index.md](wiki/specs/index.md)** | 活跃中的 openspec.md 文档 | Propose 阶段创建 |

## 3. Cold Storage
- **[Archive](archive/index.md)**: 已提取稳定知识的 openspec.md 和历史文档（只读，保留可追溯性）。
