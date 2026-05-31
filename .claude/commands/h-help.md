---
description: Scenario-driven menu of /h-* commands. Use when you're not sure which command fits your current situation. TRIGGER: user asks "which command should I use" / "help" / "怎么用" / new user onboarding. NOT FOR: detailed how-to of a specific command (read that command's own file).
argument-hint: [--scenario <keyword>]
---

Render a flat, scenario-driven catalog of `/h-*` commands so a new (or rusty) user can pick the right one without reading every command file.

## Step 1 — Parse args

| Arg | Effect |
|---|---|
| `--scenario <keyword>` | Only show the group(s) matching the keyword (case-insensitive substring match against group titles). E.g. `--scenario bug` → only Debug group. |
| (no args) | Print all groups. |

## Step 2 — Print the scenario tree

Print the following block to stdout, then exit. **Do not summarize**, do not "interpret" — emit the catalog verbatim so the user can scan and pick.

```
[h-help] 命令场景速查表

🆕 开始新工作
  新功能 / 大改动           /h-brief --slug <s> --risk <low|medium|high>
  单文件小改 / 紧急         直接说 (or @vibe shortcut), 跳过 brief
  不确定 risk               /h-context-check     (先看上下文)
  从 GitHub issue 来        /h-from-ticket <url>
  调研 / 评估 / 可行性      /h-research --slug <s>
  拆 PRD / EPIC             /h-decompose
  HIGH-risk 设计阶段        /h-design <slug>

📋 工作进行中
  看任务队列                /h-status
  看当前上下文 + 模式       /h-context-check
  resume 未完成的任务       /h-resume
  phase 边界过 gate         /h-gates --phase <implement|qa|archive>
  外部反馈来了              /h-collab-update <slug>

🐛 出问题 / 修复
  bug 报告                  /h-fix-bug
  CI 失败                   /h-ci
  生产事故记录              /h-incident <slug>
  让 QA 团队跑测试          /h-test-handoff <slug>

✅ 收尾 / 交付
  任务完成 → 开 PR          /h-pr [<existing-number>]
  archive DONE 任务          /h-archive [<slug>]
  发版本                    /h-release
  跨团队协作 doc            /h-collab <slug>
  会话复盘                  /h-reflect

📚 知识 / wiki / 学习
  wiki 对照代码核对         /h-distill-from-code
  清理过时 wiki             /h-distill
  insight → 团队知识 (公开) /h-publish-insight --insight-id <id>
  insight → 规则改动 (本地) /h-evolve --insight-id <id>

🔍 兜底
  这里没找到合适的          说明你的场景, agent 应能直接做或建议加新命令

💡 提示
  - 命令前缀 h- 是本项目约定 (区别于 Claude Code 内置 /init /review 等)
  - @-shortcut: @vibe / @patch / @learn / @research / @standard 直接覆盖路由判断
  - env bypass: CLAUDE_SECRETS_BYPASS=1 / CLAUDE_SCOPE_GUARD_BYPASS=1 紧急逃生
  - 不知道用哪个 → /h-context-check 总是安全选择 (read-only, 零副作用)
```

## Step 3 — Final report

After printing the catalog, emit:

```
[Help Status]: PRINTED | FILTERED
[Filter]: <keyword> | none
[Groups Shown]: <N of 6>
[Next Action]: 选一个命令直接调; 不确定就先 /h-context-check
```

## Hard constraints

| Constraint | Rule |
|---|---|
| **Allowed edit set** | None — read-only, prints to stdout only. |
| **Source-code edits FORBIDDEN** | Never edit any file. |
| **Anti-loop** | Single print per invocation. Re-run is idempotent. |
| **Skip-path semantics** | Unrecognized `--scenario` keyword → print all + note `[Filter]: <keyword> (no match — showing all)`. |
| **Idempotency** | Pure print; no state, no events, no side effect. |
| **No data dependence** | Catalog content is hardcoded in this file; does NOT query events.jsonl / failure_memory / wiki. Stays up-to-date by manual edit of this command file when /h-* set changes. |
| **Sub-agent dispatch** | None. |

## Out of scope

- Listing skills (not commands) — those are auto-loaded by Claude Code from `.claude/skills/`
- Listing sub-agents — those are in `.claude/agents/` and dispatched via `Agent` tool, not `/`
- Full how-to of any one command — read that command's own `.md`
- Tracking command usage stats — would require event capture / different feature

## Maintenance

When a new `/h-*` command is added (or one is removed/renamed), update the catalog in Step 2 manually. The list is authored — not auto-generated from `.claude/commands/` — to keep curated grouping and prevent partial-info noise.
