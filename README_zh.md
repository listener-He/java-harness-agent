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
├── rules/                     # 路由、生命周期、钩子、派遣、安全、写回、技能优先级、TaskList
│   ├── lifecycle.md           # 执行模式 + 风险分级 + 各阶段细节（Explorer → Propose → Review → Implement → QA → Archive）+ 阶段门禁与钩子（在 CLAUDE.md 通过 `@` import 强加载）
│   ├── policy.md              # 硬约束 + 提交策略 + WAL 写回 + Agent 派遣（内联角色 vs 子智能体）
│   ├── dispatch-template.md   # 子智能体 prompt 标准骨架（每次派遣必须使用）
│   ├── skill-precedence.md    # 同一触发窗口多个 MANDATORY 技能冲突时的优先级仲裁
│   └── tasklist-policy.md     # 何时使用 Claude Code 内置 TaskList（白名单：EPIC 子任务 / AC ≥ 4 / Approval Gate / 紧急热修复审计锚点）
├── agents/                    # 13 个 agent — 每个 .md 含 Claude Code frontmatter（name/description/tools/model），可通过 Agent 工具调用
│   ├── ambiguity-gatekeeper.md   # 歧义守门员 · Ambiguity Gatekeeper — 阻断模糊输入，强制 definition-of-ready（清晰范围 + 可测试结果 + 显式 AC）。返回 [Status]: PASS|FAIL；FAIL 携带 [Must-Ask Questions]。工作阶段：Phase 1 Step B（Idea/Feedback/Compliance/Security 类输入）。
│   ├── requirement-engineer.md   # 需求工程师 · Requirement Engineer — 将原始 Idea/Feedback/Compliance/Security 输入翻译为 Given/When/Then 可测试 AC + 结构化 Must-Ask 问题清单。不调用 AskUserQuestion（子智能体无此工具）。工作阶段：Phase 1 Explorer。
│   ├── system-architect.md       # 系统架构师 · System Architect — 在编码前设计架构：高层交互、库表设计、API 契约、不可逆决策（ADR）。EPIC 场景担任 Foreman，按 INVEST 拆分大任务到子智能体。工作阶段：Phase 2 Propose（HIGH 风险 / Scenario EPIC / GREENFIELD / B2）。
│   ├── lead-engineer.md          # 首席工程师 · Lead Engineer — 按 task_brief Machine Section 编写 Java/Maven 可编译代码：允许范围 + ACs + 硬约束 → TDD（RED→GREEN→REFACTOR）。主智能体对 MEDIUM 且 AC ≤ 3 单域任务优先选择内联。工作阶段：Phase 4 Implement。
│   ├── java-build-resolver.md    # Java 构建错误解析器 · Java Build Resolver — 诊断 mvn compile / test-compile / javac 失败，返回 [Root Cause] + [Suggested Fix]；主智能体应用修复并重跑（同一 root cause 最多派遣 2 次）。Model: haiku。工作阶段：Phase 4 编译失败时。
│   ├── test-runner.md            # 测试运行器 · Test Runner — 在变更模块范围内运行 JUnit/Surefire，解析输出，返回 AC-id → 测试方法 → PASS|FAIL|SKIP 映射 + 最小失败片段。不修改代码。Model: haiku。工作阶段：Phase 5 QA（AC ≥ 4 或 HIGH 风险时）。
│   ├── database-reviewer.md      # 数据库审查员 · Database Reviewer — 对 MyBatis mapper XML / *Mapper.java / 迁移 SQL 按 mybatis-sql-standard 审查（反 JOIN、${} 注入、审计列、最左前缀、N+1、手写 tenant_id 过滤）。HIGH/MEDIUM 发现阻断 Archive。工作阶段：Phase 5 QA 命中 mapper/SQL 变更时。
│   ├── code-reviewer.md          # 代码审查员 · Code Reviewer — 对新写代码（diff）做正确性/性能/安全/可维护性审查，独立 sub-agent 干净上下文。不做设计审查（用 system-architect）或 SQL 审查（用 database-reviewer）。工作阶段：Phase 4 Implement 之后，MEDIUM/HIGH STANDARD。
│   ├── security-sentinel.md      # 安全哨兵 · Security Sentinel — 跑确定性脚本扫描密钥泄漏 + 授权绕过风险，纯工具调用，不做主观安全审计。HIGH 置信命中阻断 Archive。工作阶段：QA → Archive gate + Scenario A（紧急热修复）。
│   ├── knowledge-extractor.md    # 知识提取器 · Knowledge Extractor — 从完成的代码变更中提取稳定知识到 WAL 碎片。只写用户在 h-archive Step 3b 选中的维度（Domain/API/Rules/Data/Architecture）。Model: haiku。工作阶段：Phase 6 Archive。
│   ├── documentation-curator.md  # 文档管理员 · Documentation Curator — 编写基于真实源码的文档：README、API/Javadoc、迁移指南、runbook、ADR explainer、能力矩阵。每个声明可追溯到文件路径或 commit。Model: haiku。工作阶段：用户请求（"写文档"、"draft README"、能力矩阵）。
│   ├── librarian.md              # 图书管理员 · Librarian — 维护 wiki 健康两种 flow：**Compact**（合并 WAL 碎片到稳定索引 + GC）和 **Distill**（扫描 + 计划 + 人工批准后删除）。工作阶段：Maintenance（用户请求 wiki 合并 / 过期清理）。
│   └── knowledge-architect.md    # 知识架构师 · Knowledge Architect — wiki 索引文件超过 3000 行（wiki_linter.py cap）时执行拆分到聚焦子文档 + 原文件重写为精简路由图。工作阶段：Maintenance（由 linter 溢出触发）。
├── commands/                    # 用户可调用的 slash 命令（h- 前缀，避免与 Claude Code 内置命令冲突）
│   ├── h-from-ticket.md         # GitHub/Jira/Linear ticket → task_brief 骨架 + launch_spec 行（跑 ambiguity-gatekeeper + input-classifier）
│   ├── h-decompose.md           # PRD/EPIC 预校验 → task-decomposition-guide 拆解 → N 个 brief 骨架 → DAG 绑定 launch_spec
│   ├── h-brief.md               # 按 schema 生成 task_brief + 双向绑定 launch_spec
│   ├── h-design.md              # 用严格 Source Documents 契约派遣 system-architect → HIGH 写 ≥2 ADR → 填 brief §8/§9
│   ├── h-research.md            # 脚手架 RESEARCH 模式报告（按 schema 渲染 7 个章节）；--scope quick|deep 决定 §3 findings 配额；launch_spec 绑定为 RES/Research/IN_PROGRESS
│   ├── h-resume.md              # 只读：定位 IN_PROGRESS 任务 + 恢复 Machine Section + 给出 Next Action（自动检测 COLLAB 阻断状态）
│   ├── h-status.md              # 全局队列快照——列出所有 launch_spec 行（PENDING/IN_PROGRESS/WAITING_APPROVAL/DONE/FAILED）+ 可并行的下一步建议
│   ├── h-fix-bug.md             # ticket/手动输入 → root-cause-debug Phase 1（必须完成）→ 按风险创建 launch_spec 行；p1/p2 触发 h-incident
│   ├── h-gates.md               # Phase/Scenario 感知的 gate 套件 + failure_memory 失败记录
│   ├── h-archive.md             # Plan Deviation Reflection → knowledge-extractor → 归档 brief → wiki_linter → 标记 DONE
│   ├── h-collab.md              # 从 task_brief 生成跨团队协作文档（api/process/data/integration/custom）+ collab 状态文件 + launch_spec COLLAB 标记
│   ├── h-collab-update.md       # 记录外部反馈 → 更新文档 → --signoff 移除 COLLAB 标记；BLOCKED 状态仅记录不阻断
│   ├── h-pr.md                  # secrets_linter + scope_guard → gh pr create → PR URL 写回 task_brief；launch_spec → WAITING_APPROVAL
│   ├── h-test-handoff.md        # 基于代码变更或 bug 修复生成给测试团队的交接文档（复现步骤、影响范围、推荐测试范围、回滚方案、待澄清问题）
│   ├── h-ci.md                  # 拉取 CI 运行数据 → 分类失败（编译/测试/安全/覆盖率）→ failure_memory + 路由建议
│   ├── h-release.md             # 发布前门禁（队列/工作区/分支/密钥）→ WAL changelog → mvn 版本设置 → tag + push；支持 --dry-run
│   └── h-incident.md            # 包装 ingest_incident.py + 按 TEMPLATE 写 incident .md（强制 "提醒未来 LLM" 质量自检）
├── skills/                          # 28 个 active skill，每次会话被 Claude Code 自动加载
│   ├── skill-index/                 # 中央导航（active 集合 + archive 索引）
│   ├── ac-verify/                   # 归档前端到端的 AC 验证，含通过/失败证据
│   ├── adversarial-review/          # 单轮对抗性审查（HIGH risk Review 阶段）
│   ├── ai-slop-cleaner/             # 回归安全清理：死代码、重复、过度抽象
│   ├── architecture-decision-records/ # 将架构决策记录为结构化 ADR
│   ├── brainstorming/               # 将想法/需求转化为含 ADR 格式备选方案的设计
│   ├── code-review-checklist/       # 交付前强制代码审查，对照全部项目标准
│   ├── cognitive-bias-checklist/    # 防止设计决策中的幻觉和过度自信
│   ├── decision-frameworks/         # SWOT、5-Why、第一性原理用于根因分析和架构选择
│   ├── impl-plan/                   # 将规格分解为检查点驱动的实现计划
│   ├── input-classifier/            # 将原始输入（PRD、想法、bug、ticket）规范化为结构化意图+范围+AC
│   ├── java-architecture-standards/ # 强制：三层架构、API 设计、POJO、反 JOIN、错误码
│   ├── java-coding-style/           # 强制：Checkstyle、Javadoc、工具类边界、函数式模式
│   ├── java-testing-standards/      # 强制：测试隔离、Mock 规范、三场景覆盖规则
│   ├── local-code-intelligence/     # 零成本本地工具：BM25 wiki 搜索、符号索引、失败记忆
│   ├── mybatis-sql-standard/        # 反 JOIN、索引利用、隐式类型转换预防
│   ├── product-manager-expert/      # PRD 生成和 PRD 消化→技术需求+验收标准
│   ├── remember/                    # 将发现的知识归入正确的持久化层
│   ├── root-cause-debug/            # 强制：任何修复前必须完成根因调查（Phase 1 必须完成）
│   ├── security-review-checklist/   # 密钥、授权、IDOR、数据泄露、依赖安全清单
│   ├── skill-creator/               # 为可重复工作流创建或更新 SKILL.md
│   ├── skill-graph-manager/         # 强制：维护双向技能知识图谱
│   ├── spec-quality-checklist/      # AI 生成文档的自纠门禁（Python 门禁脚本之前运行）
│   ├── stakeholder-conflict-resolver/ # 检测并解决多方利益冲突的需求
│   ├── task-decomposition-guide/    # 通过 INVEST 准则和垂直切片分解大型 PRD/EPIC
│   ├── test-driven-development/     # 在实现前从 AC 编写失败测试
│   ├── ultraqa/                     # 结构化 QA 循环，含证据映射表（AC↔测试↔结果）
│   └── wal-documentation-rules/     # 强制：在 Archive 阶段将稳定知识提取为 WAL 片段
├── skills-archive/                  # 13 个低频 skill — 不自动加载；由需要它的 rule / agent 在文件中直接 inline 引用路径
│   ├── ai-pipeline/                 # 完整 AI 工程流水线编排（Scenario PIPELINE）
│   ├── blueprint/                   # 多会话、多 agent 项目计划（Scenario EPIC）
│   ├── deepinit/                    # 新仓库深度初始化（Scenario GREENFIELD）
│   ├── dispatching-parallel-agents/ # 并行子 agent 派发（Scenario EPIC）
│   ├── eval-harness/                # 形式化 AC eval / pass@k 基准（Scenario PIPELINE）
│   ├── external-research/           # CVE / 合规 / 平台期外部调研（Scenario D, PIPELINE）
│   ├── greenfield-scaffold/         # 从零开始的项目脚手架（Scenario GREENFIELD）
│   ├── incident-response/           # 生产事故分诊 + 复盘（Scenario A）
│   ├── linter-severity-standard/    # 门禁脚本的 FAIL/WARN/IGNORE 严重级别标准
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
│   ├── gates/                                  # 21 个确定性门禁脚本（block / warn / pass 三级输出）
│   │   ├── _severity.py                        # 严重度分类辅助（内部）
│   │   ├── _severity_audit.py                  # 严重度输出审计 harness
│   │   ├── ambiguity_gate.py                   # 输入歧义探测（UserPromptSubmit hook）
│   │   ├── api_breaking_gate.py                # public API 破坏性变更检查（Scenario C）
│   │   ├── bypass_audit_gate.py                # 审计绕过安全的尝试（--no-verify 等）
│   │   ├── comment_linter_java.py              # Java 注释风格校验
│   │   ├── consistency_gate.py                 # 跨文件一致性检查
│   │   ├── delivery_capsule_gate.py            # 交付包验证
│   │   ├── dependency_gate.py                  # pom.xml 依赖检查（Scenario E）
│   │   ├── impact_gate.py                      # 变更影响半径评估
│   │   ├── linter.py                           # 通用 linter runner
│   │   ├── migration_gate.py                   # SQL 迁移检查（Scenario B1/B2）
│   │   ├── research_report_gate.py             # research_report.md 校验（Phase R3 门禁）
│   │   ├── run.py                              # 门禁套件 runner
│   │   ├── scope_guard.py                      # Allowed Scope 强制（PreToolUse hook + /h-gates）
│   │   ├── secrets_linter.py                   # 密钥泄漏扫描（PostToolUse hook + PR 前 + 发版前）
│   │   ├── skill_index_linter.py               # SKILL.md 索引一致性检查
│   │   ├── subagent_return_gate.py             # 校验 sub-agent 的结构化返回格式
│   │   ├── task_brief_gate.py                  # task_brief.md 结构校验（Propose→Implement 边界）
│   │   ├── wal_template_gate.py                # WAL fragment 模板合规
│   │   └── writeback_gate.py                   # Archive WAL 存在性检查（支持 --accept-stub 对应 None）
│   ├── harness/                                # 7 个运行时入口（Claude Code hooks + engine）
│   │   ├── engine.py                           # 中央运行时：门禁分派 + 严重度聚合
│   │   ├── find_active_task_brief.py           # 从 launch_spec 的 IN_PROGRESS 行定位活跃 task_brief
│   │   ├── post_tool_use_hook.py               # PostToolUse hook 入口（对改动文件跑 secrets_linter）
│   │   ├── pre_tool_use_hook.py                # PreToolUse hook 入口（Edit/Write 前跑 scope_guard）
│   │   ├── stop_hook.py                        # Stop hook（每轮结束检查）
│   │   ├── subagent_stop_hook.py               # SubagentStop hook（校验 sub-agent 返回）
│   │   └── user_prompt_submit_hook.py          # UserPromptSubmit hook（注入 failure-memory + ambiguity + triage）
│   ├── local_intel/                            # 8 个零成本本地情报工具
│   │   ├── code_index.py                       # Java 符号索引 + --impact-of 调用方枚举
│   │   ├── failure_memory.py                   # 门禁失败台账（query / record / summary）
│   │   ├── incident_hint.py                    # PostToolUse 辅助：编辑相关文件时浮出 incident.md
│   │   ├── ingest_incident.py                  # 事故原始事实摄取 + 输出模板提示
│   │   ├── skill_hint.py                       # PostToolUse 辅助：浮出相关 SKILL.md
│   │   ├── triage_probe.py                     # UserPromptSubmit 分流：5 信号 → suggested_profile
│   │   ├── turn_health_check.py                # 每轮健康诊断
│   │   └── wiki_search.py                      # BM25 搜索 .claude/wiki/
│   ├── tools/                                  # 6 个辅助脚本（一次性操作）
│   │   ├── archive_session_artifacts.py        # 把 task_brief 从 runs/ 移到 wiki/archive/
│   │   ├── bootstrap.py                        # 首次项目引导
│   │   ├── brief_from_decomposition.py         # 从拆分文件生成每个子任务的 brief 骨架
│   │   ├── import_external_skills.py           # 从外部源导入 skill
│   │   └── librarian_gc.py                     # Wiki GC 编排器（由 `librarian` Compact flow 调用）
│   └── wiki/                                   # 9 个 wiki 维护脚本
│       ├── compactor.py                        # WAL fragment 合并到主 wiki
│       ├── distill_threshold.py                # 计算 distill 的过期阈值
│       ├── distill.py                          # 提取 + 删除过期或重复的知识文件
│       ├── graph_checker.py                    # 知识图链接完整性
│       ├── pref_tag_checker.py                 # 偏好标签一致性
│       ├── schema_checker.py                   # Wiki 文档 schema 校验
│       ├── wiki_compactor.py                   # Wiki 级压缩编排器
│       ├── wiki_linter.py                      # Wiki 体检（死链 / 超长 / 孤岛）
│       └── zero_residue_audit.py               # 零残留清理审计（distill 之后）
├── workflow/
│   ├── agent_matrix.json      # 智能体到阶段的挂载表
│   ├── EXAMPLES.md            # STANDARD 任务的端到端示例
│   └── artifacts/             # 产物模板
├── runs/                      # 运行时产物 — 必须 git-ignore（task-briefs、launch-specs、缓存）
└── settings.json              # 权限和钩子配置
```

> ⚠️ **Git 忽略要求 — `.claude/runs/`**
>
> `.claude/runs/` 是**每次会话的运行时工作区**：活动的 `task_brief.md`、`launch_spec_*.md` 任务队列、distill 计划、研究草稿、`local_intel` 缓存索引（BM25、code-index、failure-memory）等。这些文件是临时的、机器相关的、被 hook 频繁重写——**绝对不能提交到 git**。
>
> 仓库的 `.gitignore` 已包含：
> ```gitignore
> ### Runtime artifacts (not committed) ###
> .claude/runs/
> ```
>
> 当你 fork 本仓库或把框架复制到新项目时，**请务必确认 `.gitignore` 保留该行**。一旦 `runs/` 被提交，会导致：跨机器状态污染、本地会话的 PII 泄露、每次 `task_brief.md` 修改产生合并冲突。
>
> Archive 流程：完成的 task_brief 通过 `archive_session_artifacts.py` 从 `.claude/runs/task-briefs/` 移动到 `.claude/wiki/archive/`，**后者是提交到 git 的**。只有归档快照进入 git 历史；活动工作区永不进入。

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
| **角色** | `ambiguity-gatekeeper`（前置门禁）, `requirement-engineer`, `system-architect`（Propose 阶段） |
| **技能** | `input-classifier`, `brainstorming`, `product-manager-expert`, `task-decomposition-guide` |
| **活动** | ① `input-classifier` 内联运行：分类原始输入 → 输出 `[Intake]` 块（含 `Input-Type` 和 `Route`） |
| | ② **Idea/Feedback/Compliance/Security 类输入**：优先派遣 `ambiguity-gatekeeper` — FAIL 时阻断直到输入收紧；PASS 后派遣 `requirement-engineer` |
| | ③ **规格推断**：`Current: [X]. Required: [Y]. Delta: [Z]` — 差距即真正的范围 |
| | ④ **BDD — AC 测试化翻译（强制）**：将每条需求转为 `Given [precondition], when [action], then [observable, measurable result]` — 模糊表述（"正确处理"、"正常工作"）被阻止 |
| | ⑤ 影响分析：`code_index.py --impact-of <target>` → 识别隐藏依赖 |
| | ⑥ 对抗性审查 Category A（仅 HIGH）："我们在解决正确的问题吗？" |
| **产出** | Spec Gap + AC 清单（Given/When/Then 格式）+ Hidden Scope → 输入 task_brief Machine Section |

### Phase 2: Propose — 架构设计与 Spec

| 项目 | 详情 |
|------|------|
| **角色** | `system-architect` |
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
| **角色** | `system-architect` |
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
| **角色** | `lead-engineer`（scope_guard.py PreToolUse hook 强制执行 Allowed Scope） |
| **技能** | `test-driven-development`, `java-architecture-standards`, `java-coding-style`, `mybatis-sql-standard`, `impl-plan` |
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
| **角色** | `code-reviewer` |
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
| **角色** | `knowledge-extractor`, `documentation-curator` |
| **技能** | `wal-documentation-rules`, `ac-verify` |
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

**触发**: "整理 wiki", "合并碎片", "做 GC", "wiki 合并", "WAL 合并"

| 步骤 | 操作 | 角色 |
|------|------|------|
| ① 聚合 | `librarian_gc.py --aggregate` — 收集所有未合并的 WAL 碎片 | `librarian` |
| ② 合并 | 将聚合的知识合并到正确的领域索引文件 | `librarian` |
| ③ 清理 | `librarian_gc.py --clean` — 删除已合并的碎片 | `librarian` |
| ④ 检查 | 如有文件超过 3000 行 → 触发文档拆分 | `knowledge-architect` |
| **门禁** | `wiki_linter.py` — 无死链 | — |

### Wiki Refresh — 知识提取与沉淀

**触发**: "提取知识", "沉淀 wiki", "刷新知识库", "milestone WAL 刷新"

| 步骤 | 操作 | 角色 |
|------|------|------|
| ① 差异 | `git diff` 识别自上次更新以来的变更 | `knowledge-extractor` |
| ② 提取 | 将稳定知识提取为结构化 WAL 碎片：[Domain], [API], [Rules] (+ [Data] 如有 schema) | `knowledge-extractor` |
| ③ 写入 | 写入碎片到 `wiki/domain/wal/`, `wiki/api/wal/` 等 | `knowledge-extractor` |
| **门禁** | `writeback_gate.py`（3 个必需章节）+ `wiki_linter.py` | — |

### Document Split — 文档拆分（防膨胀）

**触发**: wiki 文件超过 3000 行，或 "拆分文档", "index 太大"

| 步骤 | 操作 | 角色 |
|------|------|------|
| ① 检查 | 验证文件超过 3000 行限制；未超过则中止 | `knowledge-architect` |
| ② 去重 | 移除膨胀文件中的重复条目 | `knowledge-architect` |
| ③ 拆分 | 按主题拆分为专注的子文档 | `knowledge-architect` |
| ④ 重写 | 将原文件重写为精简的路由索引（仅含链接） | `knowledge-architect` |
| **门禁** | `wiki_linter.py` — 无死链，无文件仍超过 3000 行 | — |

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

用户可直接调用的快捷指令，将多步固定流程封装为一次调用。本项目所有自建命令使用 `h-` 前缀（harness 缩写），避免与 Claude Code 内置命令（`/init`、`/review`、`/security-review` 等）冲突。命令文件位于 `.claude/commands/<name>.md`，Claude Code 启动时自动加载——通过 `/h-<name> [args]` 调用。

### 需求接入 & 规划

| 命令 | 阶段 | 效果 | 使用时机 |
|------|------|------|---------|
| `/h-from-ticket <source> [<slug>]` | Explorer 入口 | 拉取 GitHub/Jira/Linear ticket → `input-classifier` + `ambiguity-gatekeeper` → task_brief 骨架 + launch_spec 行（Explore 阶段）；ticket_ref/ticket_url 写入 frontmatter 供 PR 自动关闭 | Ticket 驱动开发；字段直接映射到 brief 各章节 |
| `/h-decompose <slug> <prd-path>` | Explorer → Propose | PRD/EPIC 预校验 → task-decomposition-guide 拆解 → N 个 brief 骨架 → DAG 绑定 launch_spec | EPIC/PRD 涉及 ≥3 个域，需要 INVEST 合规切片 |
| `/h-brief <slug>` | Propose 入口 | 按 schema 生成 task_brief + 1 行 launch_spec | 单个 STANDARD 任务起步（范围已知） |
| `/h-design [slug]` | Propose 设计 | 用严格 Source Documents 契约派遣 system-architect；HIGH 写 ≥2 ADR；填 brief §8/§9 | HIGH/EPIC 需要设计备选方案；MEDIUM 需要 1 个显式选项 |
| `/h-research <slug> [--scope quick\|deep]` | RESEARCH 入口 | 按 schema 脚手架 `research_report.md`（7 个章节）+ launch_spec 绑定为 `RES`/`Research`/`IN_PROGRESS`；`--scope` 决定 §3 findings 配额（5 vs 15 条） | 调研 / 分析 / 可行性 / 基线评估；`[triage]` 建议 RESEARCH；交付物是报告不是代码 |

### 日常开发

| 命令 | 阶段 | 效果 | 使用时机 |
|------|------|------|---------|
| `/h-resume` | 任意时刻 | 只读：定位 IN_PROGRESS 任务 + 恢复 Machine Section 上下文 + 给出 Next Action；自动检测 COLLAB 阻断状态 | 会话中断后恢复 |
| `/h-status [--all] [--days <N>] [--slug <prefix>]` | 任意时刻 | 只读：列出 launch_spec 所有行，按状态分组（IN_PROGRESS / WAITING_APPROVAL / PENDING 可并行 / PENDING 被阻塞 / DONE / FAILED），按优先级链算出 Next Action | 全局队列视图；忘了在做什么时、`/h-release` 前（要求队列清空）、待办积压时 |
| `/h-fix-bug [<issue-url>] [--priority p1\|p2\|p3]` | Explorer | GitHub issue 或手动输入 → `failure_memory` 查询 → `root-cause-debug` Phase 1（必须完成，才能写修复代码）→ launch_spec 行；p1/p2 触发 `h-incident`，且禁止走 inline-PATCH 路径 | QA 提的 bug 或线上反馈；优先级决定风险等级及是否创建 incident 文件 |
| `/h-gates [--phase X] [--scenario Y]` | 阶段边界 / commit 前 | 跑所有适用 gate（scope、secrets、task_brief、scenario B/C/E）；失败记录到 failure_memory | Phase 转换或 commit 前的完整 diff 审计 |
| `/h-archive` | Phase 6 | Plan Deviation Reflection → knowledge-extractor → 归档 brief → wiki_linter → 标记 launch_spec DONE | STANDARD 任务收尾 |

### 跨团队协作

| 命令 | 阶段 | 效果 | 使用时机 |
|------|------|------|---------|
| `/h-collab <slug> [--type api\|process\|data\|integration\|custom]` | Propose 与 Implement 之间 | 从 task_brief 生成结构化协作文档；类型未指定时自动推断；创建 collab 状态文件 + launch_spec COLLAB 标记；外部交付为手动操作 | 任务需要与外部团队（前端、第三方、QA、运维）对齐后才能编码 |
| `/h-collab-update <slug> [--signoff] [--reviewer <name>]` | 任意时刻（跨会话） | 收集反馈（批准/问题/变更请求/阻断）→ 更新文档 → 更新 collab 状态；`--signoff` 移除 COLLAB 标记；BLOCKED 状态仅记录，不改变 launch_spec | 收到外部团队对协作文档的反馈后 |

### 交付

| 命令 | 阶段 | 效果 | 使用时机 |
|------|------|------|---------|
| `/h-pr [slug]` | QA 完成后 | `secrets_linter` + `scope_guard` 前置门禁 → `gh pr create`（含 Human Section + AC 清单）；PR URL 写回 task_brief；launch_spec → WAITING_APPROVAL；有 ticket_url 时自动添加 Closes # | STANDARD 任务完成后创建 PR |
| `/h-test-handoff [slug] [--bug-fix] [--commits <range>] [--ticket <ref>]` | QA 完成后（合并前 / 发版前） | 读取 task_brief + git diff +（bug 修复时读 incident 文件）→ 生成给测试团队的交接文档：复现步骤、影响面、正/负向用例、回归风险点、不需测试范围、回滚方案、待澄清问题 → 输出到 `.claude/runs/qa-handoffs/<date>_<slug>_qa_handoff.md` | 测试团队与开发分离时把变更交接给 QA；高风险变更合并前再次校对 |
| `/h-ci [--run-id <id>] [--from-file <log>]` | push 后 | 拉取 CI 运行数据 → 按类型/严重度分类失败 → `failure_memory` 记录 → 路由建议（flake 判断 / 修复任务 / 告警） | push 后或 PR 反馈中分析 CI 失败 |
| `/h-release <version> [--dry-run]` | 发布时 | 前置门禁（队列完整性、工作区干净、发布分支、密钥扫描）→ WAL changelog → `mvn versions:set` → `mvn test` → tag + push；`--dry-run` 仅打印计划，不执行 git 操作 | 切发布版本 |

### 生产

| 命令 | 阶段 | 效果 | 使用时机 |
|------|------|------|---------|
| `/h-incident <source> <slug>` | 任意时刻 | 包装 `ingest_incident.py` + 按 TEMPLATE 写结构化 incident `.md`；强制 `## 提醒未来 LLM` 质量自检 | 真实生产事故（Sentry/Jira/oncall/复盘）进入记忆系统 |

每个命令文件都是强约束的：步骤顺序固定、STOP 条件明确、Allowed Edit 边界显式。完整契约见 `.claude/commands/h-<name>.md`。

### 命令使用指南

当你卡在"该用哪个命令"或"下一步跳哪个"时翻这一节。上面的表格说明每个命令**做什么**；本节帮你决定**用哪个**。

#### 入口决策树 ——"我手上有什么？"

| 起点 | 跑哪个命令 |
|---|---|
| GitHub Issue / Jira / Linear ticket | `/h-from-ticket` |
| PRD / EPIC（多需求文档） | `/h-decompose` |
| Bug（不知道根因 / 报错） | `/h-fix-bug` |
| "调研 / 评估 / 可行性 / 分析" | `/h-research` |
| 生产事故（已发生，要记录） | `/h-incident` |
| CI 挂了（要分类 + 路由） | `/h-ci` |
| 对话中已经讨论清楚需求 | `/h-brief` |
| 会话断了 / 切机器重连 | `/h-resume` |
| 忘了在做什么 / 看全局队列 | `/h-status` |
| 发版打 tag | `/h-release` |

> **Vibe / Patch（TRIVIAL/LOW）不走任何 `/h-*` 命令。** 直接说"修一下 X"即可，主 agent 内联处理；TaskList/WAL/brief 都不需要。`/h-*` 是 MEDIUM/HIGH/RESEARCH/EPIC 才走的"结构化通道"。

#### 阶段流程图 ——"已经在做任务，下一步跳哪个？"

```
启动                Propose           Implement         交付         归档
────────          ──────────         ──────────       ───────      ──────
/h-from-ticket  → /h-brief    →    （写代码） →     /h-pr    →   /h-archive
/h-decompose      /h-design                          （建 PR）    （移到 wiki/archive,
/h-fix-bug        （HIGH 强制）                                    写 WAL, 标记 DONE）
                      │
                      └── /h-collab  ←→  /h-collab-update    （任何 phase 都可插）
                                         （跨团队对齐时）

旁路工具（不在主链路上，按需触发）：
  /h-gates     跑全套 gate（commit / phase 切换 / PR 前）
  /h-resume    单任务深度恢复
  /h-status    全局队列概览（每任务一行）
  /h-ci        CI 挂了之后吃 log 进系统
  /h-incident  已经修完的事故记录到 wiki/incidents/
  /h-release   发版（要求 launch_spec 队列清空）

RESEARCH 路径（无代码）：
  /h-research  →  （调研 §3 Findings）  →  /h-archive
```

##### "下一步该跑哪个" —— 阶段速判

| 当前状态 | 下一步 |
|---|---|
| 刚达成需求共识 | `/h-from-ticket`（有 issue）或 `/h-brief`（凭对话） |
| `/h-brief` 跑完，骨架已有 | `/h-design <slug>`（HIGH 必走，MEDIUM 看是否声明 `tech_arch`/`patterns`） |
| `/h-design` 跑完，进入 Review | 内联 review；HIGH 走 Approval Gate |
| Approval 通过，开始写代码 | 不用跑命令，直接写；用 `/h-gates --phase implement` 跑 compile/test |
| 代码 + 测试都过了 | `/h-pr` |
| PR 合并 | `/h-archive` |
| 哪一步都不知道自己在哪 | `/h-resume`（单任务）或 `/h-status`（全局） |

#### 容易混淆的"双胞胎"

| 用哪个 | 区分关键 |
|---|---|
| `h-brief` **vs** `h-from-ticket` | 对话中已说清需求 → `h-brief`；从 GitHub/Jira/Linear 拉 → `h-from-ticket` |
| `h-brief` **vs** `h-decompose` | 单个任务 → `h-brief`；多需求 PRD/EPIC → `h-decompose` |
| `h-fix-bug` **vs** `h-from-ticket` | bug + 不知道根因 → `h-fix-bug`（强制根因分析）；ticket + 已知做什么 → `h-from-ticket` |
| `h-incident` **vs** `h-fix-bug` | 还没修，要找根因 → `h-fix-bug`；已经修完，沉淀给未来 → `h-incident` |
| `h-design` **vs** 自然 Propose | MEDIUM/HIGH + 声明了 `tech_arch`/`patterns` dimension → `h-design`；纯 CRUD 不需要 |
| `h-research` **vs** `h-brief` | 产物是**报告**（决策依据，不写代码）→ `h-research`；产物是**代码** → `h-brief` |
| `h-pr` **vs** `h-archive` | `h-pr` = 建 PR（IN_PROGRESS 保持）；`h-archive` = PR 合并后收尾（IN_PROGRESS → DONE） |
| `h-gates` **vs** PreToolUse hook | hook 是每次 Edit 单文件 tripwire；`h-gates` 是 phase 切换 / commit 前的全量审计 |
| `h-collab` **vs** `h-collab-update` | 第一次起跨团队文档 → `h-collab`；外部回了反馈，要记录 → `h-collab-update` |
| `h-resume` **vs** `h-status` | `h-resume` = 单任务深度恢复（读 task_brief Machine Section）；`h-status` = 全局浅扫（每任务一行），回答"我现在有几个任务、卡在哪、能并行哪个" |

#### 常见卡壳

**Q：刚说完任务，到底跑 `/h-brief` 还是直接干？**
看 `[triage]` 块的 `suggested:`：VIBE/PATCH → 直接干；STANDARD-MEDIUM/HIGH → `/h-brief`；RESEARCH → `/h-research`。没看到 `[triage]`？自问："这事改的是 auth/migration/error code 吗？多于 5 个文件吗？"——任一是 → `/h-brief`。

**Q：`/h-brief` 问我 risk，我不知道选哪个**
- **HIGH**：动 auth、动 schema 修改（ALTER/DROP/RENAME）、动 lifecycle/policy/error code、动 secrets。**注意**：纯 `CREATE TABLE` 不是 HIGH，是 B1 / LOW。
- **MEDIUM**：影响 ≥ 7 个文件，或动 public API/Controller，或失败历史已出现 ≥ 3 次相关 pattern。
- **LOW**：其它所有情况。

**Q：`/h-brief` 问我 dimensions，schema 关键字是哪些？**
只有 5 个：`api`（controller/Mapping/DTO）、`data`（mapper/entity/SQL）、`domain`（service/event/saga/业务规则/状态机）、`tech_arch`（新组件/部署/依赖）、`patterns`（Strategy/Factory/Saga/Outbox/ACL）。可单选、多选；空数组（纯 refactor）也合法。

**Q：跑完 `/h-design`，下一步呢？**
- **MEDIUM** → 直接进 Implement（写代码），compile/test 通过后 `/h-pr`
- **HIGH** → 先触发 Approval Gate（手动确认 Human Section），然后才能 Implement
- 忘了当前阶段 → `/h-resume` 重读 launch_spec

**Q：忘了 slug 是什么**
`/h-resume` 会打印当前 IN_PROGRESS 任务的 slug；或 `/h-status` 看全部；或 `ls .claude/runs/task-briefs/` 看文件名。大多数命令的 `[slug]` 都可省略，会自动从 launch_spec 拉。

**Q：`/h-archive` 跑出来说 "SLIM 不能跑"**
Step 1.5 守门：`spec_mode: SLIM` 任务不走 WAL 流程。手动 `mv .claude/runs/task-briefs/<file> .claude/wiki/archive/`，然后改 launch_spec 行 `IN_PROGRESS` → `DONE`。

**Q：命令 chain 里有 `/h-collab`，但我们项目不跨团队**
`/h-collab` 是可选旁路，不在主流水线上。**忽略即可**。跨团队（前端/三方/QA/ops）需要文档对齐时才用。

#### 反 anti-pattern

- **不要把 `/h-*` 当成 Vibe 的替代品**。简单改动直接说"改一下 X"，不要套 `/h-brief --slim`。
- **不要 chain 调用 `/h-*`**。它们是 LLM prompt 模板，不是可调用函数。"执行 inline" = 你（main agent）按 Steps 跑，不是 `Bash` 跑。
- **不要在 PATCH 任务上跑 `/h-archive`**。Step 1.5 会拒。
- **不要在没 `[triage] suggested: RESEARCH` 时跑 `/h-research`**（除非显式 `@research`）。它和 `/h-brief` 互斥。
- **`/h-release` 跑之前先 `/h-archive` 所有 IN_PROGRESS 任务**。否则 Gate A 会拒。

---

## 日常开发工作流

命令套件覆盖从 ticket 到生产的完整循环。各步骤根据任务风险等级自由组合。

```
  [Ticket / Bug 报告]
        │
        ▼
  /h-from-ticket <url>          ← GitHub / Jira / Linear ticket → task_brief 骨架
  /h-fix-bug [<issue-url>]      ← Bug 报告 → root-cause-debug → task_brief（对应风险等级）
        │
        ▼ （STANDARD 任务）
  /h-decompose | /h-brief       ← 定义范围，创建 task_brief
  /h-design [slug]              ← 架构设计（HIGH 风险写 ADR）
        │
        ▼ （需要外部团队对齐时）
  /h-collab <slug>              ← 生成协作文档（api/process/data/integration）
        ↕  ← 手动交付，收到回复后：
  /h-collab-update <slug>       ← 记录反馈，应用变更，--signoff 解除阻断
        │
        ▼ （Implement）
  /h-resume                     ← 会话中断后恢复上下文
  /h-gates [--phase Implement]  ← Phase 转换前的门禁审计
        │
        ▼ （Archive）
  /h-archive                    ← Plan Deviation Reflection → WAL → 标记 DONE
        │
        ▼ （交付）
  /h-pr [slug]                  ← 创建 PR（先跑 secrets + scope 门禁）
  /h-ci [--run-id <id>]         ← 分析 push 后的 CI 失败
        │
        ▼ （发布）
  /h-release <version>          ← 前置门禁 → changelog → tag + push
        │
        ▼ （生产）
  /h-incident <source> <slug>   ← 将真实事故记录进 failure_memory
```

**跨会话持续性：** collab 状态（`runs/collabs/<date>_<slug>_collab.md`）和 launch_spec 中的 `COLLAB:<slug>` 标记跨会话持久存在。`/h-resume` 自动检测 COLLAB 标记并展示待处理的协作文档状态。

---

## 执行模式

每个用户请求被分类为**意图**并路由到对应的**执行模式**：

| 模式 | 适用场景 | 生命周期 | 写回 | 产物 |
|------|---------|---------|------|------|
| **LEARN** | 阅读/理解代码 | 无 | 否 | 无 |
| **RESEARCH** | 调研 / 分析 / 可行性 / 基线评估 — 交付物是报告不是代码 | `Investigate → Synthesize → Archive` | 可选（默认跳过；归档时按需启用） | `research_report.md` |
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
