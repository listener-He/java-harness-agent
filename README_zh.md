# Java Harness Agent

一套面向 AI 编程助手的行为约束框架，用于实现结构化、可持续的软件工程流程。它通过规则、角色、技能和生命周期阶段，引导 AI 助手完成从需求接收到代码生成、测试验证到知识归档的完整开发流程。

[![English](https://img.shields.io/badge/English-available-red.svg)](README.md)

---

## 这是什么

本仓库**不是**一个 Java 库或应用程序。它是位于人类开发者和 AI 编程助手之间的一套协议和工具集，用于约束助手的行为，从而产出正确、可追溯、可审查的工程结果。

入口文件：**[CLAUDE.md](CLAUDE.md)** — 每次会话启动时首先阅读。

---

## 目录结构

```
CLAUDE.md                      # 唯一入口
.claude/
├── rules/                     # 路由、生命周期、钩子、派遣、安全、写回、技能优先级
│   ├── lifecycle.md           # 执行模式 + 风险分级 + 各阶段细节（Explorer → Propose → Review → Implement → QA → Archive）+ 阶段门禁与钩子
│   ├── policy.md              # 硬约束 + 提交策略 + WAL 写回 + Agent 派遣（内联角色 vs 子智能体）
│   ├── dispatch-template.md   # 子智能体 prompt 标准骨架（每次派遣必须使用）
│   └── skill-precedence.md    # 同一触发窗口多个 MANDATORY 技能冲突时的优先级仲裁
├── agents/                    # 角色目录 — 每个 .md 含 Claude Code frontmatter（name/description/tools/model），可通过 Agent 工具调用
│   ├── ambiguity-gatekeeper.md   # 歧义守门员 · Ambiguity Gatekeeper — 阻断模糊输入，强制执行"就绪定义"三要素（动作动词 + 可识别目标 + 可度量结果）。探索超过 3 步未收敛即终止。工作阶段：Explorer 前。
│   ├── requirement-engineer.md   # 需求工程师 · Requirement Engineer — 将原始用户需求翻译为 Given/When/Then 可测试验收标准。挑战模糊形容词（"快"、"好"），为每条需求定义快乐路径 + 2 个边界场景，最终执行认知偏差检查。工作阶段：Explorer。
│   ├── system-architect.md       # 系统架构师 · System Architect — 在编码前设计技术方案，产出 task_brief.md（允许范围 + 验收标准 + 硬约束 + 任务依赖 DAG）。HIGH 风险时生成 ≥2 个 ADR 备选方案（含优缺点/失败条件）。EPIC 场景担任 Foreman。工作阶段：Propose → Review。
│   ├── lead-engineer.md          # 首席工程师 · Lead Engineer — 将 task_brief Machine Section 转化为可编译、可测试的代码。遵循 TDD：RED（基于 AC 写失败测试）→ GREEN（最小实现）→ REFACTOR（清理重构）。严格遵循允许范围，每次变更后执行编译检查（最多重试 2 次）。工作阶段：Implement。
│   ├── focus-guard.md            # 专注守卫 · Focus Guard — 范围边界强制执行。确保所有代码变更不超出 task_brief 允许范围。不审查代码质量，只检查边界合规。越界变更被阻止并输出 [Scope Violation]；必要的跨边界修改需发起 [Boundary Exception Request] 等待人工审批。工作阶段：Implement（伴随守卫）。
│   ├── code-reviewer.md          # 代码审查员 · Code Reviewer — Tech-Lead 级代码审查，对照五维评分标准：正确性、安全性、性能、设计与可维护性、代码风格。输出 CRITICAL（阻断合并）/ MAJOR（应修复）/ MINOR（锦上添花）三级报告，附 file:line 精确定位。工作阶段：QA。
│   ├── knowledge-extractor.md    # 知识提取器 · Knowledge Extractor — 从完成的代码变更中提取稳定知识，归类为 Domain（领域概念）、API（接口契约）、Rules（约束模式）、Data（数据模型）四个维度，写入 wal/ 目录为 WAL 碎片。不直接编辑共享的 index.md，合并工作留给 Librarian。工作阶段：Archive。
│   ├── documentation-curator.md  # 文档管理员 · Documentation Curator — 维护面向用户的文档（README、Javadoc、API 文档）与代码保持同步。处理新增/变更/废弃的公开 API，遵循 Javadoc 规范（@param, @return, @throws）。不负责 wiki/WAL 内容。工作阶段：Archive。
│   ├── skill-graph-curator.md    # 技能图谱管理员 · Skill Graph Curator — 维护技能索引一致性。确保每个技能目录有 SKILL.md、每份 SKILL.md 在索引中有记录。检测死链、重复项、孤立技能。执行 skill_index_linter 门禁。工作阶段：Archive。
│   ├── knowledge-architect.md    # 知识架构师 · Knowledge Architect — 当 wiki 索引文件超过 500 行上限时，执行去重→按主题拆分→创建聚焦子文档→将父索引重写为精简路由图。必要时更新 KNOWLEDGE_GRAPH.md。工作阶段：Maintenance（由 GC 溢出触发）。
│   ├── librarian.md              # 图书管理员 · Librarian — Wiki 健康维护者。收集分散的 WAL 碎片→合并到稳定的领域索引→垃圾回收已合并的碎片。发现索引超 500 行时自动调用 Knowledge Architect 拆分。触发方式：@gc / @librarian。工作阶段：Maintenance。
│   └── security-sentinel.md      # 安全哨兵 · Security Sentinel — 确定性安全门禁。运行自动化扫描（secrets_linter.py）检测硬编码凭据、令牌、密钥、云凭证。仅报告客观通过/失败结果，不做主观安全审计。每次 Archive 前 + Scenario A（紧急热修复）触发。
├── commands/                    # 用户可调用的 slash 命令（h- 前缀，避免与 Claude Code 内置命令冲突）
│   ├── h-decompose.md           # PRD/EPIC 预校验 → task-decomposition-guide 拆解 → N 个 brief 骨架 → DAG 绑定 launch_spec
│   ├── h-brief.md               # 按 schema 生成 task_brief + 双向绑定 launch_spec
│   ├── h-design.md              # 用严格 Source Documents 契约派遣 system-architect → HIGH 写 ≥2 ADR → 填 brief §8/§9
│   ├── h-resume.md              # 只读：定位 IN_PROGRESS 任务 + 恢复 Machine Section + 给出 Next Action
│   ├── h-gates.md               # Phase/Scenario 感知的 gate 套件 + failure_memory 失败记录
│   ├── h-archive.md             # Plan Deviation Reflection → knowledge-extractor → 归档 brief → wiki_linter → 标记 DONE
│   └── h-incident.md            # 包装 ingest_incident.py + 按 TEMPLATE 写 incident .md（强制 "提醒未来 LLM" 质量自检）
├── skills/                          # 29 个 active skill，每次会话被 Claude Code 自动加载
│   ├── skill-index/                 # 中央导航（active 集合 + archive 索引）
│   ├── adversarial-review/          # 单轮对抗性审查（HIGH risk Review 阶段）
│   ├── ai-slop-cleaner/             # 回归安全清理：死代码、重复、过度抽象
│   ├── architecture-decision-records/ # 将架构决策记录为结构化 ADR
│   ├── brainstorming/               # 将想法/需求转化为含 ADR 格式备选方案的设计
│   ├── code-review-checklist/       # 交付前强制代码审查，对照全部项目标准
│   ├── cognitive-bias-checklist/    # 防止设计决策中的幻觉和过度自信
│   ├── decision-frameworks/         # SWOT、5-Why、第一性原理用于根因分析和架构选择
│   ├── java-architecture-standards/ # 强制：三层架构、API 设计、POJO、反 JOIN、错误码
│   ├── java-coding-style/           # 强制：Checkstyle、Javadoc、工具类边界、函数式模式
│   ├── java-testing-standards/      # 强制：测试隔离、Mock 规范、三场景覆盖规则
│   ├── linter-severity-standard/    # 门禁脚本的 FAIL/WARN/IGNORE 严重级别标准
│   ├── local-code-intelligence/     # 零成本本地工具：BM25 wiki 搜索、符号索引、失败记忆
│   ├── mybatis-sql-standard/        # 反 JOIN、索引利用、隐式类型转换预防
│   ├── product-manager-expert/      # PRD 生成和 PRD 消化→技术需求+验收标准
│   ├── remember/                    # 将发现的知识归入正确的持久化层
│   ├── requirement-intake/          # 将原始输入（PRD、想法、bug）规范化为结构化意图+范围+AC
│   ├── security-review-checklist/   # 密钥、授权、IDOR、数据泄露、依赖安全清单
│   ├── skill-creator/               # 为可重复工作流创建或更新 SKILL.md
│   ├── skill-graph-manager/         # 强制：维护双向技能知识图谱
│   ├── spec-quality-checklist/      # AI 生成文档的自纠门禁（Python 门禁脚本之前运行）
│   ├── stakeholder-conflict-resolver/ # 检测并解决多方利益冲突的需求
│   ├── systematic-debugging/        # 强制：任何修复前必须完成根因调查
│   ├── task-decomposition-guide/    # 通过 INVEST 准则和垂直切片分解大型 PRD/EPIC
│   ├── test-driven-development/     # 在实现前从 AC 编写失败测试
│   ├── ultraqa/                     # 结构化 QA 循环，含证据映射表（AC↔测试↔结果）
│   ├── verify/                      # 归档前端到端的 AC 验证，含通过/失败证据
│   ├── wal-documentation-rules/     # 强制：在 Archive 阶段将稳定知识提取为 WAL 片段
│   └── writing-plans/               # 将规格分解为检查点驱动的实现计划
├── skills-archive/                  # 12 个低频 skill — 不自动加载；由需要它的 rule / agent 在文件中直接 inline 引用路径
│   ├── ai-pipeline/                 # 完整 AI 工程流水线编排（Scenario PIPELINE）
│   ├── blueprint/                   # 多会话、多 agent 项目计划（Scenario EPIC）
│   ├── deepinit/                    # 新仓库深度初始化（Scenario GREENFIELD）
│   ├── dispatching-parallel-agents/ # 并行子 agent 派发（Scenario EPIC）
│   ├── eval-harness/                # 形式化 AC eval / pass@k 基准（Scenario PIPELINE）
│   ├── external-research/           # CVE / 合规 / 平台期外部调研（Scenario D, PIPELINE）
│   ├── greenfield-scaffold/         # 从零开始的项目脚手架（Scenario GREENFIELD）
│   ├── incident-response/           # 生产事故分诊 + 复盘（Scenario A）
│   ├── migration-planner/           # A→B 迁移 + 等价测试（Scenario B）
│   ├── release/                     # 发布前门禁验证 + 分步执行（Scenario RELEASE）
│   ├── self-improve/                # 锦标赛迭代优化 + 平台期检测（Scenario PIPELINE）
│   └── using-git-worktrees/         # 隔离 worktree 用于 HIGH risk 并行实验（lead-engineer）
├── wiki/                      # 知识图谱（基于文件系统，无向量数据库）
│   ├── KNOWLEDGE_GRAPH.md     # 根索引
│   ├── purpose.md             # 设计哲学
│   ├── schema/                # 契约模板（task_brief、subagent_contract）
│   └── wiki/                  # 领域、API、数据、架构、规格、测试、审查、偏好
├── scripts/
│   ├── gates/                 # 确定性门禁脚本（scope_guard、secrets_linter 等）
│   ├── wiki/                  # Wiki 维护（压缩、检查、schema 校验）
│   ├── tools/                 # 引导、归档、GC 辅助
│   ├── local_intel/           # 零成本本地搜索（wiki_search、code_index、failure_memory）
│   └── harness/               # 引擎
├── workflow/
│   ├── role_matrix.json       # 角色到阶段的挂载表
│   ├── EXAMPLES.md            # STANDARD 任务的端到端示例
│   └── artifacts/             # 产物模板
├── runs/                      # 运行时产物（task-briefs、launch-specs、缓存）
└── settings.json              # 权限和钩子配置
```

---

## 工作流过程（STANDARD）

STANDARD 生命周期实现 **PDD → BDD → SDD/SPEC → TDD → BDD** 闭环：

- **PDD（计划驱动开发）**在最前端：任务依赖、并行约束、成功指标在编码前已声明
- **BDD（行为驱动开发）**在两端：Explorer 以 Given/When/Then 编写可执行规格；QA 基于同一规格验证行为
- **SDD/SPEC（规格驱动开发）**贯穿全流程：每个阶段锚定 `task_brief.md` 契约
- **TDD（测试驱动开发）**在核心：从 AC 衍生失败测试驱动实现

```
         ┌── PDD ──┐  ┌──── BDD ────┐                                     ┌──── BDD ────┐
         │依赖+并行  │  │ 写可执行规格  │                                     │ 行为验证     │
         │ DAG      │  │ Given/When/  │    ┌── SDD (契约驱动) ──┐           │ AC↔测试↔结果 │
         ▼          ▼  ▼              ▼    ▼                     ▼           ▼              ▼
输入 ─→ Explorer ─→ Propose ─→ Review ─→ [Approval] ─→ Implement ─→ QA ─→ Archive
         │              │          │                       │          │         │
        需求澄清      架构设计   设计审查               TDD实现    测试验证   知识沉淀
         │              │          │    │                  │          │         │
         ▼              ▼          ▼    ▼                  ▼          ▼         ▼
      Spec Gap     task_brief  Plan   Approved        Red→Green   Evidence   WAL
      + AC list     +依赖+并行  Review Contract         →Refactor   Mapping    +偏差回顾
```

### Phase 1: Explorer — 需求澄清 + BDD 规格编写

| 项目 | 详情 |
|------|------|
| **角色** | `@Ambiguity Gatekeeper`, `@Requirement Engineer`, `@Focus Guard` |
| **技能** | `requirement-intake`, `brainstorming`, `product-manager-expert`, `task-decomposition-guide` |
| **活动** | ① 通过意图信号矩阵分类输入 → 确定风险等级（TRIVIAL/LOW/MEDIUM/HIGH） |
| | ② **规格推断**：`Current: [X]. Required: [Y]. Delta: [Z]` — 差距即真正的范围 |
| | ③ **BDD — AC 测试化翻译（强制）**：将每条需求转为 `Given [precondition], when [action], then [observable, measurable result]` — 模糊表述（"正确处理"、"正常工作"）被阻止 |
| | ④ 影响分析：`code_index.py --impact-of <target>` → 识别隐藏依赖 |
| | ⑤ 对抗性审查 Category A（仅 HIGH）："我们在解决正确的问题吗？" |
| **产出** | Spec Gap + AC 清单（Given/When/Then 格式）+ Hidden Scope → 输入 task_brief Machine Section |

### Phase 2: Propose — 架构设计与 Spec

| 项目 | 详情 |
|------|------|
| **角色** | `@System Architect` |
| **技能** | `brainstorming`, `java-architecture-standards`, `task-decomposition-guide`, `decision-frameworks`, `cognitive-bias-checklist` |
| **活动** | ① **PDD — 计划作为一等产物**：声明任务依赖，≥3 个任务时绘制依赖图（DAG）；设定并行约束（软上限：3） |
| | ② 生成 ≥2 个设计备选方案（HIGH：ADR 格式，含优缺点/失败条件） |
| | ③ 选定方案 → 发出 **约束清单**（约束所有下游工作的决策） |
| | ④ 定义 **Allowed Scope** — 显式文件白名单，约束实现范围 |
| | ⑤ 撰写 `task_brief.md` — **通用契约**： |
| | &nbsp;&nbsp;&nbsp; • Machine Section（英文）：Allowed Scope + ACs + Task Dependencies + Hard Constraints |
| | &nbsp;&nbsp;&nbsp; • Human Section（中文）：做什么/为什么 + 怎么做 + 待确认项 |
| **产出** | `task_brief.md` — 所有 Agent 和人类共享的唯一产物 |

### Phase 3: Review — 设计审查

| 项目 | 详情 |
|------|------|
| **角色** | `@System Architect` |
| **技能** | `code-review-checklist`, `java-architecture-standards`, `adversarial-review`（HIGH）, `spec-quality-checklist` |
| **活动** | ① 对照项目标准和架构约束审查设计 |
| | ② **Plan Review Checklist（PDD）**：完整性 → 一致性 → 可行性 → 风险覆盖 → 依赖合理性（≥3 个任务） |
| | ③ 对抗性批判 Category B（仅 HIGH）："我们以正确的方式解决吗？" — 仅一轮 |
| | ④ **Approval Gate**（仅 HIGH）：以业务语言展示 Human Section → 等待显式签字 |
| | ⑤ CRITICAL 发现 → 回滚到 Phase 2。MINOR → 标注 AC，继续 |
| **产出** | 已批准的 `task_brief.md`（HIGH）或 FYI 摘要（MEDIUM） |

### Phase 4: Implement — TDD 驱动实现

| 项目 | 详情 |
|------|------|
| **角色** | `@Lead Engineer`, `@Focus Guard` |
| **技能** | `test-driven-development`, `java-architecture-standards`, `java-coding-style`, `mybatis-sql-standard`, `writing-plans` |
| **活动** | ① 阅读 `task_brief.md` Machine Section — Allowed Scope + ACs + Hard Constraints |
| | ② **RED**：从 AC 编写失败测试（在写任何实现代码前必须看到测试失败） |
| | ③ **GREEN**：在 Allowed Scope 内实现 — `scope_guard.py` 强制边界 |
| | ④ **REFACTOR**：应用编码风格，提取魔法数字，确保 SOLID 合规 |
| | ⑤ 左移：每次变更后 `mvn compile` + `secrets_linter.py`（最多重试 2 次） |
| | ⑥ **YIELD**：停止并请求人类许可进入 QA |
| **产出** | 已修改的源文件，通过的测试，编译通过 |

### Phase 5: QA — 测试验证 + BDD 行为验证

| 项目 | 详情 |
|------|------|
| **角色** | `@Code Reviewer` |
| **技能** | `java-testing-standards`, `code-review-checklist`, `ultraqa`, `security-review-checklist`（HIGH） |
| **活动** | ① 确保编译通过（`shift_left_hook`） |
| | ② 运行测试套件 → 验证所有 AC 通过 |
| | ③ **BDD — 证据映射表**（AC ≥ 4 或 HIGH 风险）：每个 Given/When/Then AC 映射到测试方法 → 预期 → 实际 → 状态 — 确保 Phase 1 声明的每一条行为都得到验证 |
| | ④ 代码审查：N+1 检查、边界条件、魔法数字、SOLID 合规 |
| | ⑤ 最多重试 2 次 → 第 3 次失败：停止，请求人类介入 |
| **产出** | 测试证据，审查报告（所有 AC PASS） |

### Phase 6: Archive — 知识沉淀

| 项目 | 详情 |
|------|------|
| **角色** | `@Knowledge Extractor`, `@Documentation Curator`, `@Skill Graph Curator` |
| **技能** | `wal-documentation-rules`, `verify` |
| **活动** | ① 从完成的 task_brief 中提取稳定知识 |
| | ② 将 **WAL 片段**写入领域目录：`api/wal/`, `data/wal/`, `domain/wal/` |
| | ③ **Plan Deviation Reflection（PDD）**：对比计划与实际执行 — 范围漂移、依赖准确性、计划作废、AC 覆盖；显著偏差写入 `plan_deviation.md` |
| | ④ 将 `task_brief.md` 移至 `wiki/archive/`（冷存储） |
| | ⑤ 如果队列非空，从 `launch_spec.md` 分派下一个 PENDING 任务 |
| **产出** | WAL 片段（domain + api + rules；如有 schema 变更则 + data），计划偏差记录，归档的 task_brief |

---

## 维护工作流（非代码操作）

当用户请求纯知识/wiki 维护类操作（整理、提取、扫描、拆分、GC），任务路由到 **MAINTENANCE** 模式 — 无代码阶段、无 task_brief、无编译检查。

### WAL Compaction (GC) — 碎片整理

**触发**: `@gc`, `@librarian`, 或 "整理 wiki", "合并碎片", "做 GC"

| 步骤 | 操作 | 角色 |
|------|------|------|
| ① 聚合 | `librarian_gc.py --aggregate` — 收集所有未合并的 WAL 碎片 | `@Librarian` |
| ② 合并 | 将聚合的知识合并到正确的领域索引文件 | `@Librarian` |
| ③ 清理 | `librarian_gc.py --clean` — 删除已合并的碎片 | `@Librarian` |
| ④ 检查 | 如有文件超过 500 行 → 触发文档拆分 | `@Knowledge Architect` |
| **门禁** | `wiki_linter.py` — 无死链 | — |

### Wiki Refresh — 知识提取与沉淀

**触发**: `@wiki-update`, `@milestone`, 或 "提取知识", "沉淀 wiki", "刷新知识库"

| 步骤 | 操作 | 角色 |
|------|------|------|
| ① 差异 | `git diff` 识别自上次更新以来的变更 | `@Knowledge Extractor` |
| ② 提取 | 将稳定知识提取为结构化 WAL 碎片：[Domain], [API], [Rules] (+ [Data] 如有 schema) | `@Knowledge Extractor` |
| ③ 写入 | 写入碎片到 `wiki/domain/wal/`, `wiki/api/wal/` 等 | `@Knowledge Extractor` |
| **门禁** | `writeback_gate.py`（3 个必需章节）+ `wiki_linter.py` | — |

### Document Split — 文档拆分（防膨胀）

**触发**: wiki 文件超过 500 行，或 "拆分文档", "index 太大"

| 步骤 | 操作 | 角色 |
|------|------|------|
| ① 检查 | 验证文件超过 500 行限制；未超过则中止 | `@Knowledge Architect` |
| ② 去重 | 移除膨胀文件中的重复条目 | `@Knowledge Architect` |
| ③ 拆分 | 按主题拆分为专注的子文档 | `@Knowledge Architect` |
| ④ 重写 | 将原文件重写为精简的路由索引（仅含链接） | `@Knowledge Architect` |
| **门禁** | `wiki_linter.py` — 无死链，无文件仍超过 500 行 | — |

### Project Scan — 项目扫描

**触发**: "扫描项目", "审计代码库", "分析代码结构"

| 步骤 | 操作 | 角色 |
|------|------|------|
| ① 索引 | `code_index.py --build` — 重建符号索引 | Explorer (inline) |
| ② 搜索 | `wiki_search.py` — 找出相关 wiki 上下文 | Explorer (inline) |
| ③ 记忆 | `failure_memory.py query` — 找出历史失败记录 | Explorer (inline) |
| ④ 报告 | 生成结构化扫描报告（目录、模块、关键符号、风险） | Explorer (inline) |

---

## Slash 命令

用户可直接调用的快捷指令，将多步固定流程封装为一次调用。本项目所有自建命令使用 `h-` 前缀（harness 缩写），避免与 Claude Code 内置命令（`/init`、`/review`、`/security-review` 等）和 skill 注册命令冲突。命令文件位于 `.claude/commands/<name>.md`，Claude Code 启动时自动加载——通过 `/h-<name> [args]` 调用。

| 命令 | 阶段 | 效果 | 使用时机 |
|------|------|------|---------|
| `/h-decompose <slug> <prd-path>` | Explorer → Propose | PRD/EPIC 预校验 → task-decomposition-guide 拆解 → N 个 brief 骨架 → DAG 绑定 launch_spec | EPIC/PRD 涉及 ≥3 个域，需要 INVEST 合规切片 |
| `/h-brief <slug>` | Propose 入口 | 按 schema 生成 task_brief + 1 行 launch_spec | 单个 STANDARD 任务起步（范围已知） |
| `/h-design [slug]` | Propose 设计 | 用严格 Source Documents 契约派遣 system-architect；HIGH 写 ≥2 ADR；填 brief §8/§9 | HIGH/EPIC 需要设计备选方案；MEDIUM 需要 1 个显式选项 |
| `/h-resume` | 任意时刻 | 只读：定位 IN_PROGRESS 任务 + 恢复 Machine Section 上下文 + 给出 Next Action | 会话中断后恢复 |
| `/h-gates [--phase X] [--scenario Y]` | 阶段边界 / commit 前 | 跑所有适用 gate（scope、secrets、task_brief、scenario B/C/E）；失败记录到 failure_memory | Phase 转换或 commit 前的完整 diff 审计 |
| `/h-archive` | Phase 6 | Plan Deviation Reflection → knowledge-extractor → 归档 brief → wiki_linter → 标记 launch_spec DONE | STANDARD 任务收尾 |
| `/h-incident <source> <slug>` | 任意时刻 | 包装 `ingest_incident.py` + 按 TEMPLATE 写结构化 incident `.md`；强制 `## 提醒未来 LLM` 质量自检 | 真实生产事故（Sentry/Jira/oncall/复盘）进入记忆系统 |

每个命令文件都是强约束的：步骤顺序固定、STOP 条件明确、Allowed Edit 边界显式。完整契约见 `.claude/commands/h-<name>.md`。

---

## 执行模式

每个用户请求被分类为**意图**并路由到对应的**执行模式**：

| 模式 | 适用场景 | 生命周期 | 写回 | 产物 |
|------|---------|---------|------|------|
| **LEARN** | 阅读/理解代码 | 无 | 否 | 无 |
| **PATCH** (TRIVIAL) | 拼写、日志、空检查、单域 bug 修复（≤3 文件，不动公开 API/DB/认证） | `Implement → QA → Archive` | 否 | 无 |
| **PATCH** (LOW) | 跨两个相关域的小 bug 修复（4–6 文件，仍不动公开 API/DB/认证） | `Implement → QA → Archive` | 否 | 无 |
| **STANDARD** (MEDIUM) | 功能开发、新 API、跨模块调用 | 完整 6 阶段（无门禁） | 是 (WAL) | `task_brief.md` |
| **STANDARD** (HIGH) | 核心流程、DB schema、认证、破坏性 API | 完整 6 阶段 + Approval Gate | 是 (WAL) | `task_brief.md` + ADR |
| **MAINTENANCE** | Wiki GC、知识提取、文档拆分、项目扫描 | 角色特定（见维护工作流） | 是 (WAL/合并) | WAL 碎片、合并后的索引、扫描报告 |

---

## 关键机制

| 机制 | 作用 |
|------|------|
| **行为原则** | `CLAUDE.md` 中四条跨场景 LLM 准则（先思考再编码、简洁优先、外科手术式修改、目标驱动执行）—— 在 mode/profile 选择前对每轮对话生效 |
| **上下文漏斗** | 结构化导航：根索引 → 领域索引 → 具体文档；杜绝盲目搜索 |
| **依赖图（DAG）** | 任务在 `launch_spec.md` 中声明上游依赖；分派受依赖满足度门控 |
| **Scope Guard** | 强制代码修改不超出声明的允许范围 |
| **Shift-Left Hook** | 每次代码修改后运行编译检查；最多重试 2 次，超出则上报人类 |
| **Secrets Lint** | 每次编辑后扫描变更文件中的密钥泄露 |
| **Plan Review Checklist** | 完整性、一致性、可行性、风险覆盖、依赖合理性 — 退出 Review 前必须通过（≥3 个任务） |
| **Plan Deviation Reflection** | Archive 时对比计划与实际 — 范围漂移、依赖准确性、AC 覆盖 |
| **钩子系统** | pre_hook（进入阶段）、guard_hook（编辑中）、shift_left_hook（编辑后）、post_hook（退出阶段）、fail_hook（回滚）、loop_hook（队列循环） |
| **Local Intelligence** | BM25 wiki 搜索、Java 符号索引、失败记忆 — 导航文件前的零成本上下文获取 |
| **Gate Scripts** | 确定性 Python 脚本，阻断或警告质量/安全/合规问题 |

---

## 快速上手

1. **阅读 [CLAUDE.md](CLAUDE.md)** — 唯一入口文件。
2. AI 助手会自动对你的请求进行分类并路由到正确模式。
3. STANDARD 任务会创建 `launch_spec.md`（含任务依赖图）和 `task_brief.md` 作为共享契约。
4. HIGH 风险变更会在编码前要求你显式确认。
5. 实现完成后度量计划偏差（PDD），并将稳定知识提取到 wiki 中供后续会话使用。

---

## 相关文档

- [CLAUDE.md](CLAUDE.md) — 项目入口
- [README.md](README.md) — English version
- [.claude/workflow/EXAMPLES.md](.claude/workflow/EXAMPLES.md) — STANDARD 任务端到端示例
- [.claude/wiki/KNOWLEDGE_GRAPH.md](.claude/wiki/KNOWLEDGE_GRAPH.md) — 知识图谱根节点
- [.claude/skills/skill-index/SKILL.md](.claude/skills/skill-index/SKILL.md) — 技能导航
- [.claude/wiki/purpose.md](.claude/wiki/purpose.md) — 设计哲学
