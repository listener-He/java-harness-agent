# WAL 格式规范 (Write-Ahead Log Format)

> WAL 是 Wiki 自动维护的核心机制。每个知识变更以小粒度增量文件写入，定期由 compactor 合并至对应的 index.md。
> 每个维度的 `wal/` 目录下都有一个 `WAL_FORMAT.md`（本文件的副本），供 Agent 快速查阅。

---

## 文件命名规则

```
YYYYMMDD_{topic}_{dimension}_append.md
```

示例：
- `20260418_order_status_flow_domain_append.md`
- `20260418_user_login_api_api_append.md`
- `20260418_add_order_table_data_append.md`

---

## WAL 文件模板

```markdown
---
date: YYYYMMDD
task: {一句话描述本次任务}
profile: PATCH | STANDARD
dimension: domain | api | data | architecture | preferences | testing | reviews
triggered_by: {触发写回的文件或行为，如 "修改了 OrderService.java"}
---

# WAL: {date}_{topic}_{dimension}_append

## 本次新增/更新的知识

{按对应 index.md 的表格格式填写。可以是一行新记录，也可以是多行，也可以是文字描述。}

{示例 - domain 维度：}
| Order | 订单 | trade | id,tenant_id,status,amount | PENDING→PAID→DONE | 金额一旦支付不可变更 |

{示例 - preferences 维度：}
| 性能 | 禁止 for 循环内调用 RPC | 每次 RPC 约 50ms，100个对象即 5s | `for(id in ids) { rpc.get(id); }` | `rpc.batchGet(ids)` |

## 无变化确认（如本次任务无新知识）
> 本次任务未产生 {dimension} 层的新知识，确认无需更新 index.md。
> 原因：{简要说明，如 "纯配置调整，无业务逻辑变化"}

## 合并目标
`llm_wiki/wiki/{dimension}/index.md`

## 合并状态
- [ ] 待合并（compactor 执行后自动标记 ✓）
```

---

## 各维度触发条件速查

| 维度 | 必须写 WAL 的文件类型 | 典型触发场景 |
|------|--------------------|-------------|
| **domain** | `*Service.java`, `*Entity.java`, `*DO.java`, `*Enum.java` | 新实体、状态流转、业务规则 |
| **api** | `*Controller.java`, `*Client.java`, `*DTO.java`, `*Feign*.java` | 新接口、参数变更、外部集成 |
| **data** | `*Mapper.xml`, `*.sql`, `*Migration*.java`, `*Entity.java`（新字段） | 新表、Schema 变更、Migration |
| **architecture** | `*Config.java`, `application*.yml`（架构相关）, 新引入 jar | ADR、模块边界、集成拓扑 |
| **preferences** | 任意（由 Review 评分或发现触发） | 反模式、团队决策、事故归因 |
| **testing** | `*Test.java`, CI 配置 | 测试证据、Flaky 发现、覆盖率变化 |
| **reviews** | 任务完成后固定触发 | 评分记录、高频问题、重构建议 |

---

## 合并规则 (Compaction)

1. `compactor.py` 检测到某维度 `wal/` 下文件数 ≥ 5，自动合并
2. 合并方式：将 WAL 内容按表格格式追加至对应 `index.md` 的对应小节
3. 合并后，WAL 文件移入 `wal/archive/YYYY/` 目录
4. `index.md` 行数超过 400 行时，触发 Knowledge Architect 角色进行拆分重组

---

## 强制性说明

- **所有 PATCH / STANDARD 任务在 Phase 6 Archive 必须至少产出 1 个 WAL 文件**
- 即使"无新知识"，也必须写"无变化确认"行，证明 Agent 确实评估过
- `wal_template_gate.py` 会检查：WAL 文件存在 + frontmatter 完整 + 内容非空
- 检查不通过 → `fail_hook` → 任务不允许标记为 DONE
