# 速查手册

> 一页纸了解项目核心信息。如需更多细节，按需查阅 skills 目录。

## 项目结构

```
src/main/java/com/xxx/
├── controller/    # 控制器层 (HTTP 入口)
├── service/       # 服务层 (业务逻辑)
│   └── impl/      # 服务实现
├── mapper/        # 数据访问层 (MyBatis)
├── domain/        # 领域对象
│   ├── entity/    # 数据库实体
│   ├── dto/       # 数据传输对象
│   ├── vo/        # 视图对象
│   └── query/     # 查询条件对象
├── config/        # 配置类
├── common/        # 通用组件
│   ├── exception/ # 异常定义
│   ├── result/    # 响应封装
│   └── utils/     # 工具类
└── security/      # 安全相关

src/main/resources/
├── mapper/        # MyBatis XML 映射文件
├── application.yml
└── application-{env}.yml
```

## 分层调用规则

```
Controller → Service → Mapper
     ↓           ↓
   DTO/VO     Entity
```

- Controller 只做参数校验和响应封装
- Service 处理业务逻辑，可调用多个 Mapper
- Mapper 只做数据库操作
- **禁止**: Controller 直接调用 Mapper
- **禁止**: Service 之间循环依赖

## 常用基类/注解

| 类/注解 | 用途 |
|---------|------|
| `BaseController` | 控制器基类，提供通用方法 |
| `BaseEntity` | 实体基类，包含 id/createTime/updateTime |
| `@RequiresPermission("xxx:yyy")` | 权限校验 |
| `@DataScope` | 数据范围过滤 |
| `@SkipTenant` | 跳过租户隔离 |
| `@Log` | 操作日志记录 |

## 响应格式

```java
// 成功
Result.success(data)

// 失败
Result.error(ErrorCode.XXX, "错误信息")

// 分页
PageResult.of(list, total)
```

## 异常处理

```java
// 业务异常 (可预期的业务规则违反)
throw new BizException(ErrorCode.ORDER_NOT_FOUND);
throw new BizException(ErrorCode.PARAM_ERROR, "订单金额不能为负");

// 系统异常 (不捕获，由全局处理器处理)
// 不要 catch Exception 然后 return null
```

## 错误码范围

| 范围 | 类型 |
|------|------|
| 1000-1999 | 系统错误 |
| 2000-2999 | 参数校验错误 |
| 3000-3999 | 通用业务错误 |
| 4000-4999 | 用户/认证错误 |
| 5000-5999 | 权限错误 |
| 10000+ | 各业务模块错误 |

## 常用工具类

```java
// 字符串
StringUtils.isBlank(str)
StringUtils.isNotBlank(str)
StringUtils.defaultIfBlank(str, "default")

// 集合
CollectionUtils.isEmpty(list)
CollectionUtils.isNotEmpty(list)
Lists.newArrayList(...)

// 日期
DateUtils.parseDate("2024-01-01", "yyyy-MM-dd")
DateUtils.format(date, "yyyy-MM-dd HH:mm:ss")
DateUtils.addDays(date, 7)

// Bean 转换
BeanUtils.copyProperties(source, target)
BeanConvertUtils.convert(source, TargetClass.class)

// 当前用户
SecurityUtils.getUserId()
SecurityUtils.getUsername()
SecurityUtils.getTenantId()
SecurityUtils.getDeptId()

// 断言
Assert.notNull(obj, "xxx 不能为空")
Assert.notBlank(str, "xxx 不能为空")
```

## SQL 规范

```xml
<!-- 禁止 -->
<select id="findAll">
    SELECT * FROM order
</select>

<!-- 正确 -->
<select id="findByUserId">
    SELECT id, order_no, status, amount, create_time
    FROM t_order
    WHERE user_id = #{userId}
      AND deleted = 0
    ORDER BY create_time DESC
    LIMIT #{offset}, #{limit}
</select>
```

**要点**:
- 表名加前缀 `t_`
- 明确列出字段，不用 `*`
- 必须有 `deleted = 0` 软删除条件
- 大表必须分页
- WHERE 条件必须走索引

## 权限

```java
// 1. 接口权限
@RequiresPermission("order:create")
public Result createOrder(OrderDTO dto) { ... }

// 2. 数据权限 (自动过滤)
@DataScope(deptAlias = "d", userAlias = "u")
public List<Order> selectOrderList(OrderQuery query) { ... }

// 3. 跳过租户 (慎用)
@SkipTenant
public Order getByOrderNo(String orderNo) { ... }
```

## 配置

```yaml
# application.yml
spring:
  profiles:
    active: ${SPRING_PROFILES_ACTIVE:dev}

# 敏感信息使用环境变量
database:
  password: ${DB_PASSWORD}

# 或使用配置中心
# apollo/nacos 配置
```

**禁止**: 在代码或配置文件中硬编码密钥/密码

## 事务

```java
@Transactional(rollbackFor = Exception.class)
public void createOrderWithItems(Order order, List<OrderItem> items) {
    orderMapper.insert(order);
    orderItemMapper.batchInsert(items);
}
```

**要点**:
- 必须指定 `rollbackFor = Exception.class`
- 避免大事务，只包含必要的数据库操作
- 事务方法必须是 public

## 日志

```java
@Slf4j
public class OrderService {
    public void createOrder(OrderDTO dto) {
        log.info("创建订单, userId={}, amount={}", dto.getUserId(), dto.getAmount());
        // ...
        log.debug("订单详情: {}", order);
    }
}
```

**要点**:
- 使用 `@Slf4j` 注解
- 用占位符 `{}`，不用字符串拼接
- 不要打印敏感信息 (密码、token)
