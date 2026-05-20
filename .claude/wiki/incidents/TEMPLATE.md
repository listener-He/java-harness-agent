# Incident Record Template

> Copy this file as `<YYYY-MM-DD>_<slug>.md`. **DELETE** this top heading and the anti-pattern reference at the bottom from the copy — keep only frontmatter + 5 sections.

---
date: <YYYY-MM-DD>
slug: <kebab-case-slug>
severity: P1 | P2 | P3
source: sentry | jira | log | manual
status: resolved | ongoing | watch
---

## 现象
<One line. User-visible or monitoring-visible symptom. Specific and measurable.>

## 根因
<One line. The WHY, not the stack trace. What invariant was violated?>

## 受影响代码栈
<Bullet list of concrete references. Use file:line, class.method, table name, mapper XML id. Anything `incident_hint.py` can grep on later.>

- `src/main/java/com/example/.../XxxService.java#methodName`
- `src/main/resources/mapper/XxxMapper.xml` (statement `findByY`)
- table `t_xxx`

## 修复
<One line. PR / commit / config change / rollback. Link if available.>

## 提醒未来 LLM
**下次改这片代码时考虑：** <1-2 sentences. Actionable. This is the line that gets injected into `[failure-memory]`. Write it as if briefing a colleague who is about to edit the file.>

---

## ❌ ✅ Anti-pattern reference (DELETE this section from your copy)

| Section | ❌ Don't write | ✅ Write |
|---|---|---|
| 现象 | "服务挂了" / "用户报错" | "login API p99 从 100ms 飙到 2s, 5xx 占比 30%, 持续 12 min" |
| 根因 | full stack trace pasted | "findByEmail 用 LOWER(email) 触发索引失效，DB CPU 打满" |
| 受影响代码栈 | "user 模块" | "UserMapper.xml#findByEmail, table t_user (idx_email)" |
| 修复 | "已修复" | "PR #1234: 改用大小写敏感存储 + 应用层 toLowerCase" |
| 提醒未来 LLM | "注意性能" | "查 email 不要用 `LOWER()` 或 `LIKE` 通配前缀 — 索引失效；用应用层 normalize" |

The "提醒未来 LLM" line is the **single highest-value field** — it's the one the next LLM session reads. Optimize for that.
