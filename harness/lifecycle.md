# Harness 生命周期与状态机 (Lifecycle & Hooks)

> **⚠️ 引擎驱动纪律 (Agent as Engine)**：大模型（Agent）是生命周期的主引擎！
> - 你必须自行根据上下文和本文件的规范，判断当前所处的 Phase，并决定下一步动作。
> - 在流转到下一阶段前，你必须主动应用 `[hooks.md](hooks.md)` 中的守卫纪律（如防重试死循环、人类确认防线）。
> - 你可以选择手动更新 `launch_spec.md` 的任务 Checkbox，或者在需要严格记录失败次数时，可选调用 `python ../scripts/harness/engine.py` 辅助脚本。
> - 无论采用何种方式，**单向流转、强制拦截与防暴走纪律**是绝对不可打破的红线！

## 🔄 六大核心生命周期与闭环机制

本架构定义了从需求到归档的单向状态机，受主控编排技能 `[devops-lifecycle-master](../skills/devops-lifecycle-master/SKILL.md)` 统一调度。Agent 必须严格按顺序流转，并在 `Archive` 阶段实现队列闭环：

### Phase 1: Explorer (探索与分析)
- **挂载技能**：`[product-manager-expert](../skills/product-manager-expert/SKILL.md)`, `[devops-requirements-analysis](../skills/devops-requirements-analysis/SKILL.md)`, `[prd-task-splitter](../skills/prd-task-splitter/SKILL.md)`
- **动作**：执行 `pre_hook`，查阅 `../llm_wiki/wiki/preferences/index.md`。对原始自然语言需求进行澄清，将 PRD 拆解为开发任务。
- **产出**：输出 `explore_report.md`，明晰需求边界与影响面。

### Phase 2: Propose (方案提案 / 系统设计)
- **挂载技能**：`[devops-system-design](../skills/devops-system-design/SKILL.md)`, `[devops-task-planning](../skills/devops-task-planning/SKILL.md)`
- **动作**：严格遵循 `../llm_wiki/schema/openspec_schema.md` 的契约模板。进行数据库表设计、ER图绘制、API与架构可扩展性设计。
- **产出**：在 `../llm_wiki/wiki/specs/` 下生成涵盖接口、数据模型、业务逻辑的 `openspec.md`。

### Phase 3: Review (技术审查)
- **挂载技能**：`[devops-review-and-refactor](../skills/devops-review-and-refactor/SKILL.md)`, `[global-backend-standards](../skills/global-backend-standards/SKILL.md)`
- **审查矩阵**：
  - 架构与工程：`[java-engineering-standards](../skills/java-engineering-standards/SKILL.md)`, `[java-backend-guidelines](../skills/java-backend-guidelines/SKILL.md)`
  - 接口与数据：`[java-backend-api-standard](../skills/java-backend-api-standard/SKILL.md)`, `[mybatis-sql-standard](../skills/mybatis-sql-standard/SKILL.md)`
  - 安全与权限：`[error-code-standard](../skills/error-code-standard/SKILL.md)`, `[java-data-permissions](../skills/java-data-permissions/SKILL.md)`
- **降级**：如果不符合规范，触发 `fail_hook` 打回 Phase 2 重写。

### Phase 3.5: Approval (人类防线与全栈交接点 - HITL & Handoff)
- **强拦截点 (Human-in-the-Loop)**：为了防止大模型带着错误的架构设计一路狂奔写出 500 行废代码，在 `Review` 内部通过后，Agent 必须**主动停下来**。
- **动作**：将 `openspec.md` 的摘要呈现给人类用户，并询问：“方案已通过机审，请问是否可以进入代码实现阶段？”
- **流转与广播 (Broadcast)**：人类确认后，该 `openspec.md` 即被视为**“已冻结的契约”**。此时：
  - 后端 Agent 进入 Phase 4 (Implement) 写代码。
  - **前端 Agent** 可被唤醒，读取该契约中的 `API Contract` 开始写 UI 和 Mock 联调。
  - **QA Agent** 可被唤醒，读取该契约中的 `Acceptance Criteria` 开始写自动化测试脚本。
  - 如果人类提出修改意见，后端退回 Phase 2 重写。

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
2. **知识提取 (反向漏斗)**：参照 `../intent/context-funnel.md` 的反向漏斗规则，将 `openspec.md` 中的接口与表结构提取合并到对应的域索引中。
3. **冷数据归档**：提取完毕后，将原 `openspec.md` 移入 `../llm_wiki/archive/`。
4. **自进化**：复杂需求必须请求人类打分（1-10分），沉淀到 `../llm_wiki/wiki/preferences/index.md`。
5. **🔄 触发 Loop Hook (闭环检查)**：读取当前的 `launch_spec_{timestamp}.md`，检查任务队列。如果还有未完成的意图，立即跳回对应的 Phase 继续执行；如果队列为空，结束本次任务循环并向人类汇报。
