# Architecture Index (Baselines & ADRs)

This domain records architecture baselines and ADRs (Architecture Decision Records).

## Hard Rules (MUST)
- When making cross-cutting technical choices (module boundaries, middleware, global patterns), you MUST consult existing ADRs or add a new one.

## Baselines & Guards
- Security baseline: [../preferences/security_rules.md](../preferences/security_rules.md)

## ADR List

| ADR # | Title | Status | Decision Summary | Date | Doc Link |
|---|---|---|---|---|---|
| (Example) ADR-001 | Use JWT for stateless auth | Accepted | Reduce Redis dependency; validate at the gateway | 2026-04-14 | `[adr_001_jwt.md]` |

---

## Archive Extraction SOP
If `Propose` makes a global architecture decision, you MUST write it back here during `Archive`.

### Append Template
```markdown
| ADR-{XXX} | {decision title} | Accepted | {one-line reason} | {YYYY-MM-DD} | `[{doc_link}]` |
```


---

## WAL Compaction - architecture - 2026-05-06 15:26:56


### 20260424_microkernel_os_upgrade.md

# 架构升级：微内核 OS 与 11 项 Master 技能生态
- 变更日期：2026-04-24
- 核心变更：
  1. 引入微内核 OS 哲学（意图即进程，Wiki即文件系统）。
  2. 引入双轨制（Dual-Track）与 4 级风险矩阵（TRIVIAL, LOW, MEDIUM, HIGH）。
  3. 将 30 个碎片化技能收拢为 11 个高密度 Master 技能。
  4. 引入 Mingsi 认知哲学（反偏见、5-Whys）作为强制认知刹车。
  5. 全面重构 README 与 ENGINEERING_MANUAL 以匹配最新架构。
