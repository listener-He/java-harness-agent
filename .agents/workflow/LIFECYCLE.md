# Harness 生命周期与状态机 (Lifecycle & Hooks)

> **⚠️ 引擎驱动纪律 (Agent as Engine)**：大模型（Agent）是生命周期的主引擎！
> - 你必须自行根据上下文和本文件的规范，判断当前所处的 Phase，并决定下一步动作。
> - 在流转到下一阶段前，你必须主动应用 `[HOOKS.md](HOOKS.md)` 中的守卫纪律（如防重试死循环、人类确认防线）。
> - 你必须维护 `launch_spec_{timestamp}.md` 的“状态机表格”（`Status/Phase/Failed_Reason`），以支持断点续传与异常恢复；或在需要时可选调用 `python ../scripts/harness/engine.py` 辅助脚本。
> - 无论采用何种方式，**单向流转、强制拦截与防暴走纪律**是绝对不可打破的红线！

## 🔄 六大阶段 + Approval Gate

本架构定义了从需求到归档的单向状态机，受主控编排技能 `[devops-lifecycle-master](../skills/devops-lifecycle-master/SKILL.md)` 统一调度。Agent 必须严格按顺序流转，并在 `Archive` 阶段实现队列闭环。`Approval` 是人类确认的强拦截点（Gate），不计入 Phase 数量：

### Phase 1: Explorer (探索与分析)
- **挂载技能**：`[product-manager-expert](../skills/product-manager-expert/SKILL.md)`, `[devops-requirements-analysis](../skills/devops-requirements-analysis/SKILL.md)`, `[prd-task-splitter](../skills/prd-task-splitter/SKILL.md)`
- **动作**：执行 `pre_hook`，查阅 `../llm_wiki/wiki/preferences/index.md`。对原始自然语言需求进行澄清，将 PRD 拆解为开发任务。
- **产出**：输出 `explore_report.md`，明晰需求边界与影响面，并包含“核心上下文锚点”（用于后续阶段防失忆）。

### Phase 2: Propose (方案提案 / 系统设计)
- **挂载技能**：`[devops-system-design](../skills/devops-system-design/SKILL.md)`, `[devops-task-planning](../skills/devops-task-planning/SKILL.md)`
- **动作**：严格遵循 `../llm_wiki/schema/openspec_schema.md` 的契约模板。进行数据库表设计、ER图绘制、API与架构可扩展性设计。
- **产出**：在 `../llm_wiki/wiki/specs/` 下生成 `openspec.md`。当 Risk Level 为 LOW 时允许使用 Slim Spec（见 `openspec_schema.md`）；MEDIUM/HIGH 必须使用完整模板。

### Phase 3: Review (技术审查)
- **挂载技能**：`[devops-review-and-refactor](../skills/devops-review-and-refactor/SKILL.md)`, `[global-backend-standards](../skills/global-backend-standards/SKILL.md)`
- **审查矩阵**：
  - 架构与工程：`[java-engineering-standards](../skills/java-engineering-standards/SKILL.md)`, `[java-backend-guidelines](../skills/java-backend-guidelines/SKILL.md)`
  - 接口与数据：`[java-backend-api-standard](../skills/java-backend-api-standard/SKILL.md)`, `[mybatis-sql-standard](../skills/mybatis-sql-standard/SKILL.md)`
  - 安全与权限：`[error-code-standard](../skills/error-code-standard/SKILL.md)`, `[java-data-permissions](../skills/java-data-permissions/SKILL.md)`
- **降级**：如果不符合规范，触发 `fail_hook` 打回 Phase 2 重写。

### Approval Gate: HITL (人类防线)
- **强拦截点 (Human-in-the-Loop)**：为了防止大模型带着错误的架构设计一路狂奔写出 500 行废代码，在 `Review` 内部通过后，Agent 必须**主动停下来**。
- **动作**：将 `openspec.md` 的摘要呈现给人类用户，并询问：“方案已通过机审，请问是否可以进入代码实现阶段？”
- **状态持久化**：将当前 `launch_spec.md` 中对应意图行更新为 `WAITING_APPROVAL`，并写入 `openspec.md` 链接（用于会话中断后的断点续传）。
- **单用户本地约束**：本仓库默认面向单用户本地开发。人类在此 Gate 中完成审查与确认；如需并行协作，由人类自行分工阅读同一份“已冻结契约”，不依赖多 Agent 常驻并行。
- **变更敏感度分级 (Risk Level)**：
  - **HIGH（必须 Approval）**：改动数据库表结构/索引、权限与鉴权策略、错误码体系、跨域修改、基础组件与通用工具、影响范围不清或改动面过大
  - **MEDIUM（必须 Approval）**：新增/修改对外接口、调整核心业务链路但不涉及 DB/权限底座
  - **LOW（可跳过 Approval）**：文档调整、纯重命名/格式化、小范围 Bugfix 且影响面明确
- **规则**：当 Risk Level 为 MEDIUM/HIGH 时，必须进入 `WAITING_APPROVAL`；当为 LOW 时允许跳过，但必须在对用户交付中写明“为何可跳过”的一句话理由。

### Phase 4: Implement (编码实现)
- **挂载技能**：`[devops-feature-implementation](../skills/devops-feature-implementation/SKILL.md)`, `[devops-bug-fix](../skills/devops-bug-fix/SKILL.md)`, `[utils-usage-standard](../skills/utils-usage-standard/SKILL.md)`, `[aliyun-oss](../skills/aliyun-oss/SKILL.md)`
- **动作**：将审查通过的 `openspec.md` 拆解为 Todo 任务列表并编写实际代码。
- **纪律**：严禁超规格的“自由发挥”，所有代码必须满足 Checkstyle 且必须应用 Java 防御性编程指南。

### Phase 5: QA Test (质量保障)
- **挂载技能**：`[devops-testing-standard](../skills/devops-testing-standard/SKILL.md)`, `[code-review-checklist](../skills/code-review-checklist/SKILL.md)`
- **动作**：编写功能代码前/后（遵循 TDD 标准），编写并运行单元测试/集成测试。基于 checklist 强制过审。
- **拦截器**：测试覆盖率与状态必须 100% 达标，代码审查清单必须全绿。失败则打回 Phase 4。

### Phase 6: Archive (归档、闭环与发车)
这是**防膨胀与自循环**的核心环节。
1. **文档同步机制**：强制触发 `[api-documentation-rules](../skills/api-documentation-rules/SKILL.md)` 和 `[database-documentation-sync](../skills/database-documentation-sync/SKILL.md)` 同步文档。
2. **知识提取 (反向漏斗)**：参照 `../router/CONTEXT_FUNNEL.md` 的反向漏斗规则，将 `openspec.md` 中的接口与表结构提取合并到对应的域索引中。
3. **冷数据归档**：提取完毕后，将原 `openspec.md` 移入 `../llm_wiki/archive/`。
4. **自进化**：复杂需求必须请求人类打分（1-10分），沉淀到 `../llm_wiki/wiki/preferences/index.md`。
5. **🔄 触发 Loop Hook (闭环检查)**：读取当前的 `launch_spec_{timestamp}.md`，检查任务队列。如果还有未完成的意图，立即跳回对应的 Phase 继续执行；如果队列为空，结束本次任务循环并向人类汇报。
