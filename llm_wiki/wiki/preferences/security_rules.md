# 安全与合规红线 (Security Baseline)

> **⚠️ Agent 纪律**：本文件是所有 `openspec.md` 设计阶段和代码 Review 阶段的【绝对禁忌清单】。任何违反本清单的设计和代码，必须在 `guard_hook` 或 `fail_hook` 中被拦截并打回重写。

## 1. 凭证与密钥 (Secrets & Credentials)
- `[Security-Secret]` **禁止硬编码**：绝对禁止在代码中硬编码任何密码、AK/SK、Token 或私钥。
- `[Security-Secret]` **禁止日志明文**：绝对禁止将包含密码、手机号、身份证、完整银行卡号等敏感信息的对象直接打印到日志中。
- `[Security-Secret]` **配置脱敏**：`application.yml` 或配置类中引用的敏感凭证必须使用环境变量（如 `${DB_PASSWORD}`）或加密值，严禁出现明文。

## 2. 权限与隔离 (Authorization & Isolation)
- `[Security-Auth]` **越权防护**：任何涉及到资源增删改查的接口，必须验证当前操作者是否有权限操作目标 ID，防止水平越权（ID 遍历）。
- `[Security-Auth]` **数据权限 (租户/组织)**：查询列表时，必须默认带上当前用户的数据权限过滤条件（如 `tenant_id` 或 `org_id`），防止数据泄露。

## 3. 防护与限流 (Protection & Throttling)
- `[Security-Limit]` **暴露面控制**：未明确要求对外暴露的接口或服务，默认不配置对公网的路由。
- `[Security-Limit]` **防重放/幂等**：所有非查询接口（POST/PUT/DELETE），在设计时必须考虑幂等性。禁止同一请求多次发送导致数据错乱。
- `[Security-Limit]` **导出限制**：涉及数据导出的接口，必须有限流控制和最大条数限制，防止内存溢出 (OOM) 或拖垮数据库。

## 4. 数据安全 (Data Security)
- `[Security-Data]` **防注入**：必须使用参数化查询（如 MyBatis 的 `#{}`），严禁使用拼接字符串（如 `${}`）拼接 SQL，除非能 100% 保证输入安全。
- `[Security-Data]` **软删除**：核心业务数据表默认使用软删除（逻辑删除），禁止物理删除记录。