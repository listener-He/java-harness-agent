# 迁移指南

从原架构迁移到新架构的步骤。

## 一、架构对比

### 文件结构变化

```
原结构:                              新结构:
├── AGENTS.md (入口)                 ├── CLAUDE.md (唯一入口)
├── .agents/                         ├── .agents/
│   ├── router/                      │   ├── context/
│   │   ├── ROUTER.md               │   │   ├── QUICK_REF.md (速查)
│   │   └── CONTEXT_FUNNEL.md       │   │   ├── domain/
│   ├── workflow/                    │   │   ├── standards/
│   │   ├── LIFECYCLE.md            │   │   └── archive/
│   │   ├── HOOKS.md                │   │
│   │   ├── ROLE_MATRIX.md          │   ├── skills/ (保留，简化索引)
│   │   └── role_matrix.json        │   │
│   ├── llm_wiki/                    │   └── guards/
│   │   ├── KNOWLEDGE_GRAPH.md      │       ├── drift_detector.py
│   │   ├── purpose.md              │       ├── risk_classifier.py
│   │   ├── schema/                 │       └── audit_logger.py
│   │   └── wiki/                   │
│   ├── skills/                     │
│   └── scripts/                    │
│       └── gates/ (10+ 脚本)       │
```

### 概念映射

| 原概念 | 新概念 | 说明 |
|--------|--------|------|
| LEARN / PATCH / STANDARD | @quick / @standard / @careful | 简化为 3 档 |
| 6 阶段生命周期 | 按模式简化 | quick 无阶段，standard 3 步，careful 5 步 |
| 硬预算 (wiki=3, code=8) | drift_detector | 智能检测替代硬上限 |
| 人工判断 Risk | risk_classifier | 自动分级 |
| focus_card.md | 取消 | Agent 自律即可 |
| launch_spec.md | 取消 | 简单任务无需状态机 |
| openspec_schema.md | 简化 spec 模板 | 只在 @careful 模式使用 |
| role_matrix.json | 取消 | 不预定义角色组合 |
| WAL 强制写回 | 可选写回 | 有价值才写 |
| Approval Gate | 自动触发 | 高风险自动升级 |

### 流程对比

**原流程 (@standard/STANDARD)**:
```
读取 AGENTS.md
↓
读取 ROUTER.md → 选择 Profile
↓
读取 CONTEXT_FUNNEL.md → 预算约束
↓
Phase 1: Explorer → explore_report.md
↓
Phase 2: Propose → openspec.md
↓
Phase 3: Review → 技能检查
↓
Approval Gate → 人工审批
↓
Phase 4: Implement
↓
Phase 5: QA
↓
Phase 6: Archive → WAL 写回
```

**新流程 (@standard)**:
```
读取 CLAUDE.md
↓
可选读取 QUICK_REF.md (需要背景时)
↓
执行开发任务
  - drift_detector 自动检测搜索效率
  - risk_classifier 自动检测风险
↓
可选知识回写
↓
audit_logger 记录
```

---

## 二、迁移步骤

### Step 1: 备份原文件

```bash
# 重命名原入口文件
mv AGENTS.md AGENTS_LEGACY.md

# 备份原 .agents 目录
cp -r .agents .agents_backup
```

### Step 2: 部署新结构

```bash
# 复制新文件到位
cp .agents/redesign/CLAUDE.md ./CLAUDE.md

# 创建新目录结构
mkdir -p .agents/context/domain/wal
mkdir -p .agents/context/standards/wal
mkdir -p .agents/context/archive
mkdir -p .agents/guards
mkdir -p .agents/audit

# 复制核心文件
cp .agents/redesign/context/QUICK_REF.md .agents/context/
cp .agents/redesign/guards/*.py .agents/guards/
```

### Step 3: 迁移有价值的知识

从原 wiki 提取仍有价值的内容：

```bash
# 偏好设置
cp .agents/llm_wiki/wiki/preferences/index.md .agents/context/standards/preferences.md

# 安全规则
cp .agents/llm_wiki/wiki/preferences/security_rules.md .agents/context/standards/security.md

# 有用的领域知识
# (根据实际内容选择性迁移)
```

### Step 4: 保留 skills 目录

Skills 目录结构不变，但更新索引方式：

```bash
# 原索引文件保留
# 但在 CLAUDE.md 中简化引用方式
```

### Step 5: 清理废弃文件 (可选)

确认新架构运行稳定后：

```bash
# 删除废弃的 workflow 文件
rm -rf .agents/workflow/
rm -rf .agents/router/
rm -rf .agents/llm_wiki/

# 删除废弃的脚本
rm -rf .agents/scripts/gates/  # 保留需要的脚本

# 清理备份
rm -rf .agents_backup
rm AGENTS_LEGACY.md
```

---

## 三、使用方式变化

### 原方式

```
用户: 帮我实现订单导出功能

Agent:
1. 读取 AGENTS.md
2. 判断 Intent = Change
3. 读取 ROUTER.md，选择 Profile = STANDARD
4. 读取 CONTEXT_FUNNEL.md
5. 执行 Context Funnel，预算 wiki=3, code=8
6. Phase 1 Explorer...
7. Phase 2 Propose...
8. ...
```

### 新方式

```
用户: 帮我实现订单导出功能

Agent:
1. 读取 CLAUDE.md (唯一入口)
2. 判断模式 = @standard (常规开发)
3. 可选读取 QUICK_REF.md
4. 开始开发
   - 搜索时自我检测收益
   - 系统自动检测风险
5. 完成后可选知识回写
```

---

## 四、注意事项

### 保留的能力

- ✅ 防止无限搜索 (drift_detector)
- ✅ 风险检测 (risk_classifier)
- ✅ 审计追溯 (audit_logger)
- ✅ 知识沉淀 (WAL 可选写回)
- ✅ 技能按需加载 (skills 目录)

### 移除的约束

- ❌ 硬预算上限 (改为智能检测)
- ❌ 强制 6 阶段流程 (按需简化)
- ❌ 强制 Approval Gate (自动升级)
- ❌ 强制 WAL 写回 (改为可选)
- ❌ 复杂的角色矩阵 (取消)

### 迁移后的验证

1. **基本功能测试**
   - 让 Agent 执行一个简单任务 (@quick)
   - 让 Agent 执行一个常规任务 (@standard)
   - 让 Agent 执行一个涉及数据库的任务 (应自动升级到 @careful)

2. **边界测试**
   - 测试连续搜索无收益时是否正确停止
   - 测试高风险文件变更时是否正确提示

3. **审计验证**
   - 检查 audit_log.jsonl 是否正确记录

---

## 五、回滚方案

如果新架构出现问题，可以快速回滚：

```bash
# 恢复原入口
mv CLAUDE.md CLAUDE_NEW.md
mv AGENTS_LEGACY.md AGENTS.md

# 恢复原目录 (如果已删除)
cp -r .agents_backup/* .agents/
```
