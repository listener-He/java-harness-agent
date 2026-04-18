# Agent Harness 重构方案

## 设计原则

**从"预防式管控"转向"信任+智能刹车"**

| 原设计 | 新设计 |
|--------|--------|
| 硬预算限制 (wiki=3, code=8) | 动态预算 + 收益检测自动停止 |
| 强制读取多个规范文件 | 单一入口 + 按需展开 |
| 6阶段完整流程 | 3档简化流程 |
| 门控脚本强制检查 | 软检查 + 事后审计 |
| 人工 Approval Gate | 风险自动检测 + 可选审批 |

---

## 一、新架构总览

```
CLAUDE.md (唯一入口，200行以内)
    │
    ├── 快速模式 (@quick)     → 直接执行，仅记录审计日志
    ├── 标准模式 (@standard)  → 理解 → 执行 → 归档
    └── 审慎模式 (@careful)   → 理解 → 设计 → 审批 → 执行 → 归档

.agents/
    ├── context/           # 知识库 (简化后的wiki)
    │   ├── QUICK_REF.md   # 速查手册 (常用规范一页纸)
    │   ├── domain/        # 业务领域知识
    │   ├── standards/     # 工程规范
    │   └── archive/       # 历史归档
    │
    ├── skills/            # 技能库 (保留但简化索引)
    │
    └── guards/            # 智能护栏 (替代门控脚本)
        ├── drift_detector.py    # 注意力漂移检测
        ├── risk_classifier.py   # 风险自动分级
        └── audit_logger.py      # 审计日志
```

---

## 二、核心机制重设计

### 2.1 智能刹车替代硬预算

**原方案的问题**：
- `wiki=3, code=8` 一刀切，无法适应任务复杂度
- Agent 频繁输出 `<Confidence_Assessment>` 申请扩展，打断心流

**新方案：收益递减自动停止**

```python
# guards/drift_detector.py 核心逻辑

class DriftDetector:
    def __init__(self):
        self.reads = []           # 记录每次读取
        self.useful_reads = 0     # 有收益的读取次数
        self.consecutive_no_gain = 0  # 连续无收益次数

    def record_read(self, file_path: str, gained_info: bool):
        """Agent 每次读取后自我评估是否有收益"""
        self.reads.append(file_path)
        if gained_info:
            self.useful_reads += 1
            self.consecutive_no_gain = 0
        else:
            self.consecutive_no_gain += 1

    def should_stop(self) -> tuple[bool, str]:
        # 规则1: 连续3次无收益 → 建议停止搜索
        if self.consecutive_no_gain >= 3:
            return True, "连续3次读取无新收益，建议开始执行"

        # 规则2: 总读取超过15次且有效率<30% → 强制停止
        if len(self.reads) > 15 and self.useful_reads / len(self.reads) < 0.3:
            return True, "搜索效率过低，请重新聚焦目标"

        # 规则3: 检测循环读取
        if self._detect_loop():
            return True, "检测到重复读取相同文件，请总结已知信息"

        return False, ""

    def _detect_loop(self) -> bool:
        """检测是否在循环读取相同的几个文件"""
        if len(self.reads) < 6:
            return False
        recent = self.reads[-6:]
        return len(set(recent)) <= 2  # 最近6次只读了2个文件
```

**Agent 端的使用方式**（写入 CLAUDE.md）：

```markdown
## 搜索自检规则

每次读取文件后，快速自问：
- 这次读取是否解答了我的疑问？ (是=有收益)
- 我是否还需要继续搜索？

如果连续3次读取都没有新收获 → 停止搜索，用已有信息开始执行
如果发现自己在反复读同样的文件 → 停止，总结已知信息
```

---

### 2.2 三档简化流程

**原方案**：LEARN/PATCH/STANDARD 三档 + 6阶段流程
**新方案**：三档流程，但每档内部大幅简化

#### @quick (快速模式)
**适用**：单文件修改、明确的小任务、紧急修复

```markdown
流程: 直接执行 → 自动记录审计日志
约束: 无强制约束
检查: 事后审计 (audit_logger.py 记录变更)
```

#### @standard (标准模式) - 默认
**适用**：大多数开发任务

```markdown
流程:
  1. 理解 (可选读取 QUICK_REF.md)
  2. 执行 (正常开发)
  3. 归档 (可选知识回写)

约束:
  - 搜索自检规则生效
  - 修改超过5个文件时提示确认

检查:
  - risk_classifier.py 自动评估风险
  - 如果检测到高风险 → 自动升级到 @careful
```

#### @careful (审慎模式)
**适用**：数据库变更、权限逻辑、跨模块重构

```markdown
流程:
  1. 理解 (必须读取相关规范)
  2. 设计 (输出 spec.md 草案)
  3. 审批 (人工确认)
  4. 执行
  5. 归档 (必须知识回写)

约束:
  - 设计阶段禁止写代码
  - 必须通过风险检查

自动触发条件 (无需人工指定):
  - 检测到修改 *Mapper.xml / *Repository.java
  - 检测到修改 *Permission* / *Auth* / *Security*
  - 检测到新增数据库表或字段
  - 单次变更超过10个文件
```

---

### 2.3 风险自动分级

**原方案**：依赖 Agent 主观判断 HIGH/MEDIUM/LOW
**新方案**：基于文件路径和变更内容自动分级

```python
# guards/risk_classifier.py

RISK_PATTERNS = {
    "HIGH": [
        r".*Mapper\.xml$",           # MyBatis 映射
        r".*\.sql$",                  # SQL 脚本
        r".*Permission.*\.java$",    # 权限相关
        r".*Auth.*\.java$",          # 认证相关
        r".*Security.*\.java$",      # 安全相关
        r"application.*\.yml$",      # 配置文件
        r".*Migration.*\.java$",     # 数据迁移
    ],
    "MEDIUM": [
        r".*Controller\.java$",      # 对外接口
        r".*Service\.java$",         # 业务逻辑
        r".*Client\.java$",          # 外部调用
        r"pom\.xml$",                # 依赖变更
    ],
    "LOW": [
        r".*Test\.java$",            # 测试代码
        r".*\.md$",                  # 文档
        r".*DTO\.java$",             # 数据传输对象
        r".*VO\.java$",              # 视图对象
    ]
}

def classify_risk(changed_files: list[str]) -> str:
    """根据变更文件自动判定风险等级"""
    for file in changed_files:
        for pattern in RISK_PATTERNS["HIGH"]:
            if re.match(pattern, file):
                return "HIGH"
    for file in changed_files:
        for pattern in RISK_PATTERNS["MEDIUM"]:
            if re.match(pattern, file):
                return "MEDIUM"
    return "LOW"

def should_upgrade_to_careful(changed_files: list[str], file_count: int) -> bool:
    """判断是否应该自动升级到审慎模式"""
    risk = classify_risk(changed_files)
    if risk == "HIGH":
        return True
    if file_count > 10:
        return True
    return False
```

---

### 2.4 单一入口 CLAUDE.md

**目标**：Agent 只需读取一个文件即可开始工作

```markdown
# CLAUDE.md - Agent 工作指南

## 快速开始

1. 收到任务后，先判断模式：
   - 单文件小改动 → @quick (直接做)
   - 常规开发任务 → @standard (默认)
   - 涉及数据库/权限/配置 → @careful (需设计)

2. 如果不确定，就用 @standard，系统会自动检测是否需要升级。

## 搜索原则

- 优先直接读取用户指定的文件
- 如果需要背景知识，先看 `.agents/context/QUICK_REF.md`
- 连续3次搜索无收获 → 停止搜索，用已有信息行动

## 代码规范速查

(将原来分散的规范精简到这里，约50行)

- 分层: Controller → Service → Mapper，禁止跨层调用
- 命名: 驼峰，DTO/VO/Entity 后缀明确
- 异常: 业务异常用 BizException，系统异常向上抛
- SQL: 禁止 SELECT *，必须走索引
- 权限: 默认开启租户隔离，除非明确标注 @SkipTenant

## 详细规范 (按需查阅)

如需更详细的规范，查阅：
- `.agents/context/standards/` - 各类工程规范
- `.agents/context/domain/` - 业务领域知识
- `.agents/skills/` - 专项技能指南

## 知识回写 (可选)

完成任务后，如果发现了值得记录的知识：
- 写入 `.agents/context/domain/wal/` (业务知识)
- 写入 `.agents/context/standards/wal/` (工程规范)

格式: `YYYYMMDD_主题_append.md`
```

---

## 三、知识库简化

### 3.1 原结构 vs 新结构

```
原结构 (复杂):                    新结构 (简化):
.agents/llm_wiki/                 .agents/context/
├── KNOWLEDGE_GRAPH.md            ├── QUICK_REF.md (一页纸速查)
├── purpose.md                    ├── domain/
├── schema/                       │   ├── index.md
│   └── openspec_schema.md        │   └── wal/
├── wiki/                         ├── standards/
│   ├── domain/index.md           │   ├── index.md
│   ├── api/index.md              │   └── wal/
│   ├── data/index.md             └── archive/
│   ├── architecture/index.md
│   ├── specs/index.md
│   ├── testing/index.md
│   └── preferences/index.md
└── archive/
```

**简化要点**：
- 合并相似目录 (api+data+architecture → standards)
- 取消强制的 `index.md` 层级
- 取消复杂的 `openspec_schema.md`，用简单的 spec 模板

### 3.2 QUICK_REF.md 示例

```markdown
# 速查手册

## 项目结构
- `src/main/java/com/xxx/` - 主代码
- `src/main/resources/mapper/` - MyBatis XML
- `src/test/java/` - 测试代码

## 关键类
- `BaseController` - 控制器基类，提供通用响应封装
- `BizException` - 业务异常，携带错误码
- `DataScope` - 数据权限注解

## 常用工具类
- `StringUtils` - 字符串处理
- `DateUtils` - 日期处理
- `SecurityUtils` - 获取当前用户

## 错误码范围
- 1000-1999: 系统错误
- 2000-2999: 参数校验错误
- 3000-3999: 业务逻辑错误

## 禁止事项
- 禁止在循环中查询数据库
- 禁止硬编码密钥/密码
- 禁止 SELECT *
- 禁止跨 Service 直接调用 Mapper
```

---

## 四、流程对比

### 4.1 原流程 (复杂)

```
收到任务
    ↓
读取 AGENTS.md
    ↓
判断 Intent (Learn/Change/DocQA/Audit)
    ↓
选择 Profile (LEARN/PATCH/STANDARD)
    ↓
读取 ROUTER.md
    ↓
读取 CONTEXT_FUNNEL.md
    ↓
执行 Context Funnel (预算约束)
    ↓
[如果 STANDARD]
    ↓
Phase 1: Explorer (读取 preferences, 输出 explore_report.md)
    ↓
Phase 2: Propose (输出 openspec.md)
    ↓
Phase 3: Review (技能检查)
    ↓
Approval Gate (人工审批)
    ↓
Phase 4: Implement
    ↓
Phase 5: QA
    ↓
Phase 6: Archive (WAL 回写)
    ↓
完成
```

**问题**：启动成本高，需要读取 5+ 个文件才能开始

### 4.2 新流程 (简化)

```
收到任务
    ↓
读取 CLAUDE.md (唯一入口)
    ↓
快速判断模式:
    ├── @quick → 直接执行 → 审计日志 → 完成
    ├── @standard → 可选读 QUICK_REF.md → 执行 → 可选归档 → 完成
    └── @careful → 读规范 → 写 spec → 审批 → 执行 → 归档 → 完成

执行过程中:
    - drift_detector 自动检测搜索效率
    - risk_classifier 自动检测风险升级
```

**改进**：
- 启动只需读 1 个文件
- 大多数任务走 @standard，约束很轻
- 风险任务自动升级，无需人工判断

---

## 五、角色/技能简化

### 5.1 取消复杂的角色矩阵

**原方案**：8 种角色 × 2 Profile × 6 Phase = 复杂的组合
**新方案**：按需挂载，不预定义矩阵

```markdown
## 技能调用原则

- 不确定分层架构 → 读 `skills/java-engineering-standards/`
- 不确定 API 设计 → 读 `skills/java-backend-api-standard/`
- 不确定 SQL 写法 → 读 `skills/mybatis-sql-standard/`
- 不确定权限处理 → 读 `skills/java-data-permissions/`

按需读取，不强制全部加载。
```

### 5.2 简化后的技能索引

```markdown
# 技能速查

## 工程规范
- java-engineering-standards: 分层架构、包结构
- java-backend-api-standard: API 设计、响应格式
- mybatis-sql-standard: SQL 编写规范
- checkstyle: 代码风格

## 业务规则
- java-data-permissions: 数据权限
- error-code-standard: 错误码

## 流程指南
- devops-bug-fix: 修 bug 的 SOP
- devops-feature-implementation: 开发功能的 SOP
```

---

## 六、门控脚本简化

### 6.1 取消的门控

| 原门控 | 原因 |
|--------|------|
| ambiguity_gate.py | 关键词匹配不可靠，改用 Agent 自判断 |
| focus_card_gate.py | 取消 focus_card，改用 drift_detector |
| writeback_gate.py | 改为可选归档，不强制 |
| delivery_capsule_gate.py | 取消交付胶囊概念 |

### 6.2 保留的门控 (重构)

| 门控 | 作用 | 触发时机 |
|------|------|----------|
| drift_detector.py | 搜索效率检测 | 每次文件读取后 |
| risk_classifier.py | 风险自动分级 | 提交前检查 |
| audit_logger.py | 审计日志 | 任务完成后 |
| wiki_linter.py | 知识库健康检查 | 手动触发 |

---

## 七、实施路径

### Phase 1: 精简入口 (1天)
1. 创建新的 `CLAUDE.md`，整合核心规范
2. 创建 `QUICK_REF.md` 速查手册
3. 重命名 `AGENTS.md` → `AGENTS_LEGACY.md`

### Phase 2: 简化流程 (1天)
1. 取消 6 阶段流程，改为 3 档模式
2. 取消 `launch_spec.md` 状态机
3. 取消 `role_matrix.json`

### Phase 3: 智能护栏 (2天)
1. 实现 `drift_detector.py`
2. 实现 `risk_classifier.py`
3. 实现 `audit_logger.py`

### Phase 4: 知识库重组 (1天)
1. 合并 wiki 目录结构
2. 迁移有价值的内容到新结构
3. 归档旧内容

---

## 八、预期效果

| 指标 | 原方案 | 新方案 |
|------|--------|--------|
| 启动读取文件数 | 5+ | 1-2 |
| 搜索约束方式 | 硬预算 | 智能检测 |
| 流程阶段数 | 6 | 1-3 |
| 门控脚本数 | 10+ | 3-4 |
| 人工审批触发 | 强制 (MEDIUM+) | 自动升级 (HIGH) |
| Token 开销 | 中高 | 低 |
| 灵活性 | 低 | 高 |
| 防失控能力 | 高 (但过度) | 中高 (够用) |

---

## 九、关键文件模板

### 9.1 新 CLAUDE.md 完整版

见下一节单独输出。

### 9.2 spec.md 简化模板 (@careful 模式)

```markdown
# Spec: {功能名称}

## 变更概述
一句话描述做什么、为什么

## 影响范围
- 文件: (列出将修改的文件)
- 风险等级: LOW / MEDIUM / HIGH

## 设计要点
(简要描述实现思路，3-5 条)

## 验证方式
- 单元测试:
- 手动验证:

## 审批
- [ ] 人工确认可以执行
```
