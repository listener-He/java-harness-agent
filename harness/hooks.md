# Harness 生命周期拦截器 (Hooks)

## 🎯 钩子规范

所有的生命周期状态流转前后，都可能触发对应的 Hook 脚本或 Skill，用于拦截、修正或日志记录。这里我们将现有的细粒度规范技能深度绑定到各个 Hook 中。

### 1. `pre_hook` (前置拦截)
- **触发时机**：进入新阶段前。
- **绑定技能**：
  - `[global-backend-standards](/.trae/skills/global-backend-standards/SKILL.md)`
  - `[java-backend-guidelines](/.trae/skills/java-backend-guidelines/SKILL.md)`
- **主要用途**：装载特定的规则集。例如进入 `Implement` 阶段前，加载团队的防守型编程规范和偏好记忆。

### 2. `guard_hook` (执行守卫)
- **触发时机**：执行核心动作时（如生成代码、写 SQL）。
- **绑定技能**：
  - `[checkstyle](/.trae/skills/checkstyle/SKILL.md)`
  - `[java-javadoc-standard](/.trae/skills/java-javadoc-standard/SKILL.md)`
  - `[java-data-permissions](/.trae/skills/java-data-permissions/SKILL.md)`
- **主要用途**：
  - **规范守卫**：在代码输出时，确保强制符合 Google/Sun 混合标准、数据权限过滤逻辑。
  - **领域边界守卫 (Domain Boundary Guard)**：严禁越权修改！如果当前意图属于 `trade` 域，Agent 在修改 `user` 域的文件前，必须主动抛出警告并确认该跨域修改在 `openspec.md` 中被明确授权，否则禁止操作。

### 3. `post_hook` (后置清理与审计)
- **触发时机**：阶段执行完毕准备流转前。
- **绑定技能**：
  - `[api-documentation-rules](/.trae/skills/api-documentation-rules/SKILL.md)`
  - `[database-documentation-sync](/.trae/skills/database-documentation-sync/SKILL.md)`
- **主要用途**：确保代码变更后，关联的 API 文档和 DB 文档已同步更新，并在 `catalog/lifecycle_log.md` 追加执行日志。

### 4. `fail_hook` (失败回退)
- **触发时机**：任何测试、审查或编译失败时。
- **绑定技能**：
  - `[code-review-checklist](/.trae/skills/code-review-checklist/SKILL.md)`
- **主要用途**：
  - **状态降级**：自动将状态机降级回上一阶段，并在原 `openspec.md` 或相关任务单中追加失败原因。必须修复 checklist 中的所有 fail 项。
  - **最大重试防线 (Max Retries = 3)**：为了防止大模型陷入“修复失败->再次尝试->代码越写越乱”的无限死循环，如果同一阶段（如单元测试）连续失败 3 次，Agent **必须强制终止操作**，并向人类报告：“已达到最大重试次数，请介入排查问题。”

### 5. 🔄 `loop_hook` (循环与并发守卫)
- **触发时机**：处于 `Phase 6: Archive` 结束时，或意图网关初始发车时。
- **主要用途**：
  - **队列消费**：读取 `launch_spec_{timestamp}.md` 中的意图队列。
  - **并发控制**：判断队列中的下一个意图是否可以并行执行（如 `Propose.API` 与 `Propose.Data` 可并行）。
  - **闭环重启**：提取下一个意图，调用相应的 `devops-*` 技能，重新进入对应的 Lifecycle Phase 进行下一轮工作，直至队列为空。
