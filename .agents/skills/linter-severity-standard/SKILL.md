---
name: "linter-severity-standard"
description: "定义本仓库各类校验（脚本/清单）的严重等级 FAIL/WARN/IGNORE 与统一判级口径，用于降低无意义重试与提升门禁可执行性。"
---

# Linter Severity Standard（FAIL / WARN / IGNORE）

本标准用于把“检查项”分成三类严重等级，以避免小问题触发反复重试，同时保证硬红线必拦截。

## 1) 等级定义

- FAIL：必须停止推进，触发 `fail_hook`，修复后才能进入下一阶段
- WARN：允许推进，但必须在交付中解释原因与处理计划（或明确接受风险）
- IGNORE：仅记录，不作为门禁条件

## 2) 统一判级（固定阈值）

### 2.1 Wiki 图谱（wiki_linter）

- FAIL
  - Markdown 死链
- WARN
  - 孤岛文件（未被任何 Markdown 引用，且非 index/purpose/root）
  - 超长文件预警（>500 行）

### 2.2 契约体检（schema_checker）

- FAIL（Full Spec）
  - 缺失关键模块：API 契约 / 数据模型 / 验收标准（BDD / Acceptance Criteria）
- WARN（Full Spec）
  - 缺少 JSON Example（如无接口/无入参/无出参可解释）
- FAIL（Slim Spec）
  - 缺失 Slim Spec 必备模块：变更摘要 / 影响面 / 风险与回滚 / 验证与证据

## 3) 与 Hook 的关系

- `Doc Consistency Gate` 必须以脚本的 exit code 为准：存在 FAIL（非 0）即触发 `fail_hook`
- WARN 不阻断，但必须输出解释与后续动作
