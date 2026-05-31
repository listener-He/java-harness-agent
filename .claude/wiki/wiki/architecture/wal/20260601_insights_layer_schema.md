---
title: insights.jsonl Insight Layer schema
date: 2026-06-01
category: architecture
status: active
origin: human-design
---

# insights.jsonl — 自动模式识别产出流

## 用途

Insight Layer 是 Sensor/Policy/Enforce 三层架构之上的**第四层**：从 events.jsonl + failure_memory + memory + incidents 里识别**复发模式**、**协同编辑簇**、**衰减知识**、**override 趋势**，输出供 agent / 人审阅的结构化 insight。

```
Sensor (events.jsonl + failure_memory + ...)
       ↓
► Insight Detector (扫数据, 产 insights) ◄  ← 本 layer
       ↓
Policy (/h-context-check surface 高优先 insight; /h-evolve 转规则变更 proposal)
       ↓
Enforce (人审过的规则变更通过 git commit 进入生效)
```

**关键纪律**：Insight Detector **只观察、不强制**。任何规则变更必须人审 → /h-evolve → git commit；插件不直接改 CLAUDE.md / hook / 配置。

## 文件位置

```
.claude/runs/local_intel/insights.jsonl
```

- gitignored（隶属 `.claude/runs/`）
- append-only JSONL
- 单文件 >5MB rotate 为 `insights.jsonl.YYYY-MM-DD`

## 通用字段（每条 insight 必有）

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | UUID-like 短 hash（detector kind + ts + summary 哈希前 8 位） |
| `ts` | string | ISO 8601 + tz, detection 时间 |
| `kind` | string | 5 类之一（见下） |
| `confidence` | string | `high` / `medium` / `low` |
| `summary` | string | 一行人类可读描述（≤120 字符） |
| `suggested_action` | string | 一行建议动作（≤200 字符），通常以动词起始 |
| `evidence` | list | 证据来源指针：file:line / event ts / failure_memory key 列表 |
| `status` | string | `new` / `acknowledged` / `acted_on` / `dismissed`（默认 new） |

可选字段：`detector` (产出此 insight 的检测器名)、`tags` (主题标签列表)。

## 5 类 insight schema

### `recurring_failure_cluster`
| 字段 | 必有 | 说明 |
|---|---|---|
| `gate` | ✓ | 失败的 gate 名 (e.g., `scope_guard`) |
| `pattern` | ✓ | failure_memory 中的 pattern 文本 |
| `count` | ✓ | 复发次数 (≥3 才生成 insight) |
| `days_span` | ✓ | 第一次到最近一次跨度天数 |

**confidence 规则**：count≥10 → high; count≥5 → medium; count≥3 → low

### `co_edit_cluster`
| 字段 | 必有 | 说明 |
|---|---|---|
| `files` | ✓ | 共编辑文件列表（2-5 个） |
| `co_edit_count` | ✓ | 30d 内共改次数 |
| `time_span_days` | ✓ | 跨度 |

**confidence**：count≥10 → high; ≥5 → medium; ≥3 → low

### `decayed_knowledge`
| 字段 | 必有 | 说明 |
|---|---|---|
| `file_path` | ✓ | 候选过期文件 |
| `last_read_days` | ✓ | 距上次 read 多少天（usage_tracker） |
| `file_age_days` | ✓ | 文件 mtime 距今多少天 |
| `reason` | ✓ | "未读 ≥90d" / "被引用文件已不存在" 等 |

**confidence**：last_read ≥180d → high; ≥90d → medium; ≥60d → low

### `override_drift`
| 字段 | 必有 | 说明 |
|---|---|---|
| `env_var` | ✓ | CLAUDE_SCOPE_GUARD_BYPASS / CLAUDE_SECRETS_BYPASS 等 |
| `count_30d` | ✓ | 30d 内使用次数 |
| `top_contexts` | — | 最常出现的 file_path 前 3（说明哪类 gate 阈值可能太严） |

**confidence**：count≥10 → high; ≥5 → medium; ≥3 → low

### `user_correction`（v1 已实现 — 字符串前缀启发）
| 字段 | 必有 | 说明 |
|---|---|---|
| `correction_phrase` | ✓ | 命中的纠偏短语（精确文本，e.g., "不对"） |
| `count` | ✓ | 30d 内该 phrase 出现次数 |
| `recent_excerpts` | — | 最近 3 个 prompt_excerpt 样本（agent 复盘自查用） |

**confidence**：count≥10 → high; ≥5 → medium; ≥3 → low

**已知局限**：v1 只看 prompt 前缀短语，不绑定到具体被纠的 agent 决策。如果用户经常说"actually..."但其实在补充信息（不是纠偏），会有 false positive。v2 可加 "上一轮 agent 是否做了明确分类" 这个绑定条件，但需 LLM 比对。

## status 状态机

```
new ──────────────► acknowledged (agent 在 /h-context-check 中读了)
 │                       │
 │                       ▼
 │                  acted_on (/h-evolve 应用了规则变更)
 │
 ├──────────────► published (/h-publish-insight 写成 git-tracked 团队文档)
 │
 └──────────────► dismissed (人/agent 明确拒绝)
```

只允许单向迁移：`new → {acknowledged, acted_on, published, dismissed}`；`acknowledged → {acted_on, published, dismissed}`。`published` 与 `acted_on` 互斥但都是 terminal — 同一 insight 走二选一（要么改规则、要么写团队文档；都做相当于两次记录）。状态变更通过追加 insights.jsonl 记录 `{id, ts, kind: "status_change", status: <new>}` 行（不修改原 insight 行 — 保持 append-only 不变性）。

**`published` 语义**：通过 `/h-publish-insight` 命令，把单机本地 insight 转成 git-tracked 的 `.claude/wiki/insights/<date>_<id>_<slug>.md` 文档。这是单机 expert system → 团队共享 system 的桥接点。**必须显式用户调用**，绝不自动 fire — published 是个有意识的"分享给团队"动作，不该被 hook 或 detector 触发。

## /h-evolve 输出范式

`/h-evolve --insight-id <id>` 产出（不直接改文件）：

```
[evolve-proposal] insight=<id>

Summary: <insight summary>
Suggested action: <suggested_action>

Proposed change:
  File: <path>
  Locate: <pattern or line range>
  Replace: <new content>

Rationale:
  Evidence: <bullet list of evidence>
  Risk if applied: <one-line>
  Risk if not applied: <one-line>

To apply: confirm and the agent will Edit; on confirmation status updates to acted_on.
To dismiss: say "dismiss <id>"; status updates to dismissed.
```

## insights.jsonl 与 events.jsonl 的关系

- **events.jsonl**: 原始观察（一行一事件，不做判断）
- **insights.jsonl**: 二阶推断（一条 insight = 多个 event/failure 的聚合判断）

insight 引用 event 用 `evidence: [{kind: "event", ts: "...", file_path: "..."}]` 形式；引用 failure 用 `{kind: "failure", pattern: "...", gate: "..."}`。

## 触发时机

| 入口 | 触发 |
|---|---|
| `/h-context-check` | 默认调 `insight_detector --write`（产新 insight 入流，同时 query 最近 high/medium 显示） |
| `/h-evolve` | 显式调，无需先检测 |
| 周期触发 | v1 不实现；后续可加 cron / `--auto-run` |

## 反模式（禁止）

- **不要**让 insight detector 自动修改任何配置文件 / hook 脚本 / CLAUDE.md（必须经 /h-evolve + 人审）
- **不要**用 insight 阻断 tool call（这是 enforce 层职责，insight 仅 advisory）
- **不要**在 insights.jsonl 写未经 detector 产出的手工条目（防止人工和自动数据混杂）
