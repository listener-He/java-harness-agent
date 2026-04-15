# Harness 生命周期拦截器 (Hooks)

## 🎯 钩子规范

所有的生命周期状态流转前后，都可能触发对应的 Hook 脚本或 Skill，用于拦截、修正或日志记录。这里我们将现有的细粒度规范技能深度绑定到各个 Hook 中。

## 🧭 会话恢复与防失忆 (Resume & Memory Anchor)

- **第一动作（断点续传）**：当 Agent 被人类回复重新唤醒，或会话疑似被上下文窗口冲刷时，第一动作先读取 `router/runs/launch_spec_*.md`，确认当前 `Status/Phase` 并恢复到对应生命周期阶段。
- **第二动作（记忆锚点）**：若存在 `explore_report.md`，后续阶段优先读取其中的“核心上下文锚点”，避免重复爬 Sitemap 且防止 Token 溢出导致的失忆。

### 1. `pre_hook` (前置拦截)
- **触发时机**：进入新阶段前。
- **绑定技能**：
  - `[global-backend-standards](../skills/global-backend-standards/SKILL.md)`
  - `[java-backend-guidelines](../skills/java-backend-guidelines/SKILL.md)`
- **主要用途**：装载特定的规则集。例如进入 `Implement` 阶段前，加载团队的防守型编程规范和偏好记忆。

### 2. `guard_hook` (执行守卫)
- **触发时机**：执行核心动作时（如生成代码、写 SQL）。
- **绑定技能**：
  - `[checkstyle](../skills/checkstyle/SKILL.md)`
  - `[java-javadoc-standard](../skills/java-javadoc-standard/SKILL.md)`
  - `[java-data-permissions](../skills/java-data-permissions/SKILL.md)`
- **主要用途**：
  - **规范守卫**：在代码输出时，确保强制符合 Google/Sun 混合标准、数据权限过滤逻辑。
  - **领域边界守卫 (Domain Boundary Guard)**：严禁越权修改！如果当前意图属于 `trade` 域，Agent 在修改 `user` 域的文件前，必须主动抛出警告并确认该跨域修改在 `openspec.md` 中被明确授权，否则禁止操作。

### 3. `post_hook` (后置清理与审计)
- **触发时机**：阶段执行完毕准备流转前。
- **绑定技能**：
  - `[api-documentation-rules](../skills/api-documentation-rules/SKILL.md)`
  - `[database-documentation-sync](../skills/database-documentation-sync/SKILL.md)`
- **主要用途**：确保代码变更后，关联的 API 文档和 DB 文档已同步更新，并在 `workflow/runs/` 下追加执行日志（如需）。

#### Explorer 阶段补丁：explore_report.md 的“核心上下文锚点”

- **约束**：Explorer 的 `post_hook` 产出的 `explore_report.md` 必须包含一个名为 `## 核心上下文锚点` 的区块。
- **内容要求**：
  - 本轮从 Sitemap/Index 下钻得到的“关键链接清单”（domain/api/data/architecture/preferences/security_rules 等）。
  - 关键业务词汇与口径（术语、枚举、状态机摘要）。
  - 明确的工程红线（禁止模式、权限策略、幂等策略、回滚动作占位）。
- **后续使用**：在 Propose/Implement 阶段，如果上下文不稳或隔了较久再继续，优先只读该锚点区块恢复最小必要上下文。

### 4. `fail_hook` (失败回退)
- **触发时机**：任何测试、审查或编译失败时。
- **绑定技能**：
  - `[code-review-checklist](../skills/code-review-checklist/SKILL.md)`
- **主要用途**：
  - **状态降级**：自动将状态机降级回上一阶段，并在原 `openspec.md` 或相关任务单中追加失败原因。必须修复 checklist 中的所有 fail 项。
  - **最大重试防线 (Max Retries = 3)**：为了防止大模型陷入“修复失败->再次尝试->代码越写越乱”的无限死循环，如果同一阶段（如单元测试）连续失败 3 次，Agent **必须强制终止操作**，并向人类报告：“已达到最大重试次数，请介入排查问题。”
  - **状态持久化**：当失败导致停止或需要人类介入时，必须将 `launch_spec.md` 对应行更新为 `FAILED` 并写入 `Failed_Reason`。

### 5. 🔄 `loop_hook` (循环与并发守卫)
- **触发时机**：处于 `Phase 6: Archive` 结束时，或意图网关初始发车时。
- **主要用途**：
  - **队列消费**：读取 `launch_spec_{timestamp}.md` 的状态机表格（`Status/Phase`），定位下一个 `PENDING` 或 `IN_PROGRESS` 的意图并恢复执行。
  - **并发控制**：判断队列中的下一个意图是否可以并行执行（如 `Propose.API` 与 `Propose.Data` 可并行）。
  - **闭环重启**：提取下一个意图，调用相应的 `devops-*` 技能，重新进入对应的 Lifecycle Phase 进行下一轮工作，直至队列为空。
