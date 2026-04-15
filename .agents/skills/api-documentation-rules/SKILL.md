---
name: "api-documentation-rules"
description: "API接口文档规范。创建Controller接口时必须生成对应文档，文档路径为 .agents/docs/module_description/{模块名}/{ControllerName}-{方法名}.md，并关联到模块描述文档。"
---

# API接口文档规范

当创建或修改Controller接口时，必须遵循以下文档规范：

## 1. 文档路径规范

接口文档必须存放在以下路径：
```
../../docs/module_description/{模块名}/{方法名}.md
```

### 命名规则
- `{模块名}`: 模块的英文名称，如 `performance`、`rbac`、`org`
- `{ControllerName}`: Controller类名（不含包名），如 `LiveVideoController`
- `{方法名}`: 接口方法名，如 `pushVideo`、`list`、`create`

### 示例
- 业绩模块视频接收接口: `../..//docs/module_description/performance/LiveVideoController-receiveVideo.md`
- RBAC模块菜单列表接口: `../..//docs/module_description/rbac/MenuController-list.md`
- 组织模块部门创建接口: `../..//docs/module_description/org/DeptController-create.md`

## 2. 文档内容规范

每个接口文档必须包含以下章节：

```markdown
# {接口名称}

## 接口信息

| 项目 | 说明 |
|-----|------|
| 接口路径 | `{HTTP方法} {完整路径}` |
| 控制器 | {ControllerName} |
| 方法 | {方法名} |
| 认证方式 | {认证注解} |

## 接口描述

{简要描述接口功能}

## 请求参数

### {请求对象名}

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| {字段名} | {类型} | 是/否 | {说明} |

## 业务逻辑

{详细描述业务处理逻辑，可用流程图}

## 响应

{响应示例}

## 关联表

| 表名 | 说明 |
|-----|------|
| {表名} | {说明} |

## 请求示例

{JSON请求示例}
```

## 3. 关联模块描述

创建接口文档后，必须在对应的模块描述文档中添加引用。

模块描述文档路径：`../../docs/module_description/{模块名}.md`

在模块描述文档中添加「接口文档」章节（如果不存在则新建）：

```markdown
## N. 接口文档

| 接口 | 说明 | 详细文档 |
|-----|------|----------|
| {HTTP方法} {路径} | {接口说明} | [{文档文件名}](./{模块名}/{文档文件名}) |
```

## 4. 触发条件

以下操作必须同步更新接口文档：
- 创建新的Controller接口
- 修改接口的请求参数
- 修改接口的业务逻辑
- 修改接口的响应结构
- 修改接口的路径或认证方式
