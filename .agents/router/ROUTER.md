# Intent Gateway Router

This document is the routing contract. It selects an execution profile, then optionally launches a lifecycle queue.

For lifecycle rules, see [LIFECYCLE.md](../workflow/LIFECYCLE.md).

## Guiding Principle
Do not create more intent codes to represent every micro-scenario.

Instead:
- Keep a small set of top-level intents.
- Use profiles + parameters to express the differences in execution.

## 0) Shortcuts (Explicit Routing)
If the user provides an explicit shortcut, it MUST override automatic routing.

Supported shortcuts:
- `@read` / `@learn`: force Profile `LEARN` (read-only)
- `@patch` / `@quickfix`: force Profile `PATCH` (small change / bugfix)
- `@standard`: force Profile `STANDARD` (full lifecycle)

### Shortcut DSL (Composable)
Shortcuts can be composed with flags to express common workflows as a small DSL.

Syntax:
```text
@<profile> <flags...> -- <natural language request or question>
```

Profiles:
- `@learn`: read-only explanation (no launch, no write-back)
- `@patch`: small change / bugfix (minimal artifacts, hooks still apply)
- `@standard`: full delivery lifecycle

Flags (order-independent):
- Scope / read:
    - `--scope <path|glob|symbol>`: explicit scope (file/dir/symbol)
    - `--direct`: force direct reads (do not start with Knowledge Graph drill-down)
    - `--funnel`: force the funnel even if scope is explicit
    - `--depth shallow|normal|deep`: explanation depth (LEARN only)
- Risk / artifacts:
    - `--risk low|medium|high`: explicit risk override
    - `--slim`: force Slim Spec (PATCH only, or STANDARD with `--risk low`)
    - `--changelog`: use Change Log only (PATCH only)
    - `--evidence required|optional|none`: evidence requirement (default: PATCH=required)
- Launch / write-back:
    - `--launch`: force lifecycle launch (STANDARD only)
    - `--no-launch`: force no launch
    - `--writeback`: allow wiki/WAL write-back (not allowed for LEARN)
    - `--no-writeback`: forbid write-back (LEARN only; PATCH/STANDARD require write-back)
- Verification:
    - `--test "<cmd>"`: required verification command + evidence
    - `--no-test`: skip tests (LEARN only; PATCH requires an explicit justification)
- DocQA actionize:
    - `--actionize`: convert DocQA into an executable STANDARD queue (requires confirmation)
    - `--yes`: auto-confirm `--actionize` / `--launch` (team use with caution)

Conflict rules (MUST enforce):
- `@learn` MUST NOT be combined with `--launch` or `--writeback`.
- `--launch` MUST be used with `@standard` only.
- `--slim` requires `--risk low` (or implied low risk in PATCH).
- `--actionize` MUST ask for confirmation unless `--yes` is present.

Examples:
```text
@learn --scope src/foo/bar.ts --direct --depth deep -- explain this file
@patch --risk low --slim --test "mvn test -Dtest=OrderServiceTest" -- fix NPE in createOrder
@standard --risk high --launch -- implement tenant permission checks for order list API
@learn --funnel -- what is the API design standard? --actionize
```

## 1) Profiles (Execution Modes)

### Profile: LEARN (Read-only)
Use when the goal is to understand code or explain behavior.
- No launch spec.
- No wiki write-back.
- No lifecycle phases.
- Direct read is allowed and preferred when scope is explicit.

### Profile: PATCH (Small change / bugfix)
Use when the change is small and risk is LOW.
- Minimal artifacts: Slim Spec or Change Log + objective verification evidence.
- No full `Propose -> Review -> Approval` chain by default.
- Hooks still apply (guard/fail/max retries).
- Archive write-back is REQUIRED (Domain/API/Rules WAL at minimum).

### Profile: STANDARD (Full delivery)
Use for MEDIUM/HIGH risk changes and any change with wide blast radius.
- Uses the full lifecycle (Explorer -> Propose -> Review -> Approval Gate -> Implement -> QA -> Archive).
- Requires `openspec.md` (full schema for MEDIUM/HIGH).

## 2) Top-level intents (keep this list small)

| Intent | When to use | Default Profile | Launch spec | Write-back |
|---|---|---|---|---|
| `Learn` | “Explain/read/understand this code” with explicit scope | LEARN | No | No |
| `Change` | “Modify code” (feature, refactor, bugfix) | PATCH or STANDARD | Yes (STANDARD only) | Required (Archive via WAL) |
| `DocQA` | “What is the rule/process/template?” | LEARN | No | No (unless actionized) |
| `Audit` | “Assess the codebase” (read-only review/risk scan) | LEARN | No | No |

## 2.5) Intent Signal Words — 意图信号词矩阵

> 当用户未使用显式 shortcut 时，Agent **必须**通过以下信号词矩阵确定 Intent 和 Profile，并在回复开头输出一行意图确认：
> `[Intent Check] 识别为 @{profile} | 风险 {LOW/MEDIUM/HIGH} | 触发原因：{信号词}`
> 用户可以纠正，否则继续执行。

### → LEARN（只读）
**信号词**：解释、explain、看一下、what is、how does、怎么理解、读一下、分析这个文件、这个是什么、帮我理解  
**规则**：用户没有要求修改任何文件，或任务明确是”理解/查看/审查”类型 → 强制 LEARN，禁止写代码

### → PATCH（小改动，LOW 风险）
**信号词**：修复、fix、改一下、bug、报错、NPE、空指针、一处、单个、修改一个方法、加一个字段  
**规则**：明确单点修改 + 影响范围可预估 ≤ 3 个文件 + 风险可自评为 LOW → Profile PATCH

### → STANDARD（完整流程，MEDIUM 风险）
**信号词**：实现、implement、新增功能、开发、feature、重构、refactor、整体优化、跨模块  
**规则**：影响多文件或逻辑边界不明确 → Profile STANDARD，默认 MEDIUM 风险

### → 自动升级为 HIGH 风险（Auto-Escalate，无论用户如何表述）
以下任一条件触发，**强制**升级为 STANDARD HIGH，进入完整审批流程：

| 触发条件 | 原因 |
|----------|------|
| 关键词含：数据库、migration、schema、表结构、字段、DDL | 数据变更不可逆 |
| 关键词含：权限、permission、auth、security、加密、鉴权 | 安全边界变更 |
| 关键词含：breaking change、接口不兼容、废弃接口、移除字段 | 影响外部消费方 |
| 关键词含：上线、deploy、production、灰度、发布 | 生产影响 |
| 估算修改文件数 > 10 | 大范围重构，爆炸半径大 |
| 修改 `application*.yml` 的核心配置项 | 环境配置变更风险高 |

### → 特殊场景路由
| 场景 | 路由 | 说明 |
|------|------|------|
| 紧急热修（P0 故障）| `@patch --emergency` | 跳过 Explorer，直接 Implement，Archive 延迟但不可跳过 |
| 性能调优 | `@read --audit performance` | 先输出 performance_report.md，再决定是否 @patch |
| 依赖升级（pom.xml）| `@patch` MEDIUM | 自动附加 dependency_gate.py 检查 |
| 数据库 Migration | `@standard HIGH` | 必须包含 rollback 方案，触发 migration_gate.py |
| 破坏性 API 变更 | `@standard HIGH` | openspec 必须列出影响消费方和版本策略 |

## 3) Routing rules (Automatic)

### Rule 1: If scope is explicit and the user wants to learn, do Direct Read (MUST)
If the user provides an explicit scope (file path, directory, class/method name, or pasted snippet) and the goal is learning/explanation:
- Select `Learn` + Profile `LEARN`.
- DO NOT start with Knowledge Graph drill-down.
- Use the funnel only if you need background context after the first read.

### Rule 2: Otherwise, use the Context Funnel (MUST)
DO NOT start with full-text search.

The Agent MUST:
1. Read the root: [KNOWLEDGE_GRAPH.md](../llm_wiki/KNOWLEDGE_GRAPH.md)
2. Drill down via: [CONTEXT_FUNNEL.md](CONTEXT_FUNNEL.md)
3. If you cannot pick a specialist skill, consult: [trae-skill-index](../skills/trae-skill-index/SKILL.md)

### Rule 3: Change intent selects profile by risk
- LOW -> Profile `PATCH` (Slim Spec allowed)
- MEDIUM/HIGH -> Profile `STANDARD` (full schema + Approval Gate)

### Rule 3.1: Budgeted Navigation (MUST)
For `Change` and `Audit` intents, uncontrolled exploration is forbidden.
- The Agent MUST apply the forward constraints defined in [CONTEXT_FUNNEL.md](CONTEXT_FUNNEL.md) before any heavy wiki/code exploration.
- Default budgets:
  - Wiki budget: 3 documents
  - Code budget: 8 files
  - Pagination reads within the same file do NOT count as additional file reads.
- If budgets are exhausted and success criteria are not met, the Agent MUST stop and file an Escalation Request (see `Escalation Protocol` in [CONTEXT_FUNNEL.md](CONTEXT_FUNNEL.md)).

### Rule 4: Actionize DocQA into STANDARD is an explicit opt-in
DocQA is read-only by default.
The Agent MUST NOT launch a lifecycle queue unless:
- the user explicitly requests actionize (via `--actionize` or an equivalent natural language request), and
- the user confirms (or uses `--yes`).

## 4) Internal lifecycle queue codes (used only when launching STANDARD)
When Profile is `STANDARD`, the `Change` intent is expanded into a lifecycle queue using these internal codes:

| Code | Phase | Notes |
|---|---|---|
| `Explore.Req` | Explorer | Clarify requirements + scope anchors |
| `Propose.API` | Propose -> Review | API contract and design |
| `Propose.Data` | Propose -> Review | Database schema changes |
| `Implement.Code` | Implement -> QA | Code changes |
| `QA.Test` | QA | Tests + evidence |

## 5) Launch Spec (STANDARD only)
When launching a lifecycle queue:
1. Persist to `router/runs/launch_spec_{timestamp}.md`
2. Drive transitions by updating only `Status/Phase/Failed_Reason`
3. Optional helper: `python3 ../scripts/harness/engine.py init "..."` can create and maintain the file

After each `Archive` phase, the Agent MUST re-read the launch spec to decide whether to continue with the next intent.

### Launch Spec Template
Status enum: `PENDING`, `IN_PROGRESS`, `DONE`, `WAITING_APPROVAL`, `FAILED`

```markdown
# Launch Spec - {YYYYMMDD_HHMMSS}

## State Machine
| Intent | Status | Phase | Artifact/Log | Failed_Reason |
|---|---|---|---|---|
| Explore.Req | IN_PROGRESS | 1_Explorer | `explore_report.md` | - |
| Propose.API | PENDING | - | - | - |
| Implement.Code | PENDING | - | - | - |

## Resume
- If the session is interrupted, the first action is to read this file and restore from `Status/Phase`.
- If any row is `WAITING_APPROVAL`, stop and wait for human approval; then switch back to `IN_PROGRESS` and continue.
- If any row is `FAILED`, stop and report `Failed_Reason`.
```
