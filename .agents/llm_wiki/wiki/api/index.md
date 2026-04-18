# API Index — 接口契约

> 对外暴露的接口清单、参数规范、集成点、破坏性变更记录。
> Agent **禁止**通过扫描全量代码猜测接口契约，必须以本文件为准，再按需校验代码。

## 硬规则 (MUST)
- Archive 阶段，**必须**从 `openspec.md` 提取 API 签名追加到本文件。
- 表格超过 50 行时，**必须**按模块拆分（如 `user/api.md`、`trade/api.md`），本文件保留模块级路由。
- **破坏性变更**（方法签名、字段删除、状态码变更）**必须**填写"破坏性变更记录"并列出影响方。

---

## 1. 接口列表 (Endpoints)

| 模块 | Method | Path | 认证 | 权限码 | 限流 | 简述 | 文档链接 |
|------|--------|------|------|--------|------|------|----------|
| *(示例) 用户* | *POST* | */api/v1/user/login* | *无* | *-* | *10次/min* | *用户登录，返回 JWT* | *[user_api.md](user/user_api.md)* |

---

## 2. 请求/响应规范 (Contracts)

### 标准响应体
```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```
- `code=0` 表示成功；非 0 参见 error-code-standard
- 分页响应 `data` 结构：`{ "total": N, "pageNum": 1, "pageSize": 20, "list": [] }`

### 错误码范围
参见 [error-code-standard](../../skills/error-code-standard/SKILL.md)

---

## 3. 外部集成 (External Integrations)

| 系统名 | 方向 | 协议 | Endpoint/Topic | 认证方式 | 超时(ms) | 重试策略 | 降级方案 |
|--------|------|------|----------------|----------|----------|----------|----------|
| *(示例) 支付网关* | *下游调用* | *HTTPS* | *https://pay.xxx.com/v1/charge* | *HMAC-SHA256* | *5000* | *3次指数退避* | *返回待确认状态，异步补偿* |

---

## 4. 破坏性变更记录 (Breaking Changes)

| 日期 | 变更描述 | 影响接口 | 影响消费方 | 版本策略 | 下线时间 |
|------|----------|----------|------------|----------|----------|
| *(示例) 2026-04-01* | *移除 GET /user/info 中的 phone 字段* | *GET /user/info* | *移动端 App v3.x* | *旧字段保留至 v3 全量升级* | *2026-06-01* |

---

## Archive Extraction SOP

Archive 阶段从 `openspec.md` 提取：
- 新增/变更接口 → 追加至"接口列表"
- 新外部集成 → 追加至"外部集成"
- 破坏性变更 → **必须**填写"破坏性变更记录"

WAL 写入路径：`wal/YYYYMMDD_{topic}_api_append.md`
WAL 格式参考：[wal/WAL_FORMAT.md](wal/WAL_FORMAT.md)

**触发条件**：修改 `*Controller.java`、`*Client.java`、`*Feign*.java`、`*DTO.java`、`application*.yml` 中接口相关配置时，必须评估是否需要更新本维度。

---

## WAL Pending（待合并）

*(compactor 合并后此处自动清空)*
