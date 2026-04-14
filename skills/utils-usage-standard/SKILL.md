# Utilities Usage Standard (核心工具类使用规范)

This skill dictates the usage of the project's custom utility classes. You **MUST** use these utilities instead of writing native Java equivalents or using third-party libraries directly.

## 1. 判空工具 (EmptyUtil)
**规则**：绝对禁止使用 `obj == null`, `list.isEmpty()`, `StringUtils.isBlank()`。全量使用 `EmptyUtil`。
- **判断空**：`EmptyUtil.isEmpty(obj)` (支持 String, Collection, Map, Array, Object)
- **判断非空**：`EmptyUtil.isNotEmpty(obj)`

## 2. 数据组装与防连表 (Complete)
**规则**：禁止使用 SQL JOIN 查询字典名或外键关联数据，必须在 Service 层使用 `Complete` 工具类在内存中组装。
- **核心语法**：`Complete.start(数据集合).build(源字段, 目标字段, 映射函数).then().over();`
- **示例**：
  ```java
  // 假设 dataList 是包含 employeeId 和 positionId 的 VO 列表
  Complete.start(dataList)
      .build(ScheduleEmployeeVO::getEmployeeId, ScheduleEmployeeVO::setEmployeeName, employeeService::getNameMap)
      .then()
      .build(ScheduleEmployeeVO::getPositionId, ScheduleEmployeeVO::setPositionName, positionService::getPositionNameMap)
      .then()
      .over();
  ```
- **注意**：映射函数（如 `getNameMap`）的入参必须是 `List<Long> ids`，返回值必须是 `Map<Long, String>` 或 `Map<Long, Object>`。

## 3. 分页查询包装器 (CustomPage)
**规则**：所有的分页查询必须使用 `CustomPage.execute` 包装，不要直接使用 MyBatis-Plus 的 `page()` 方法处理返回值。
- **示例**：
  ```java
  PageData<Entity> pageData = CustomPage.execute(request, (page, req) -> {
      return super.lambdaQuery()
          .eq(Entity::getTenantId, req.getTenantId())
          .like(EmptyUtil.isNotEmpty(req.getName()), Entity::getName, req.getName())
          .page(page);
  });
  // 转换为 VO
  PageData<EntityResponse> result = pageData.conversion(entity -> BeanUtil.copyProperties(entity, EntityResponse.class));
  ```

## 4. 大数据分批查询 (BatchQuery)
**规则**：当需要查询或处理可能超过一定数量（如 1000 条）的大量数据时（如缓存预热、全量导出、查询无尽列表），禁止一次性 `list()` 导致内存溢出，必须使用 `BatchQuery` 进行游标分批。
- **用法 1：收集并返回全量结果 (适用于万级数据以内)**
  ```java
  // idx 是上一次查询的最后一条 ID，初始为 null；limit 默认每批大小（如1000）
  List<RoomWorkScheduleDto> responses = new BatchQuery<>((limit, idx) -> {
      return workScheduleMapper.selectClientSchedules(idx, limit, tenantId, day);
  }, RoomWorkScheduleDto::getId).get(null, 100000); // 100000为保护性最大截断条数
  ```

- **用法 2：流式消费 (适用于百万级数据预热/清理)**
  ```java
  BatchQuery<Long, Role> batchQuery = new BatchQuery<>((limit, idx) -> {
      return super.lambdaQuery()
          .select(Role::getId)
          .gt(idx != null, Role::getId, idx) // 游标条件：大于上一次的 ID
          .last("limit " + limit)
          .list();
  }, Role::getId); // 第二个参数是提取下一个游标 ID 的函数

  // 消费数据，每拉取一批执行一次 consumer
  batchQuery.consumer(roleList -> {
      // 处理这批数据，例如清理 Redis
      redisTemplate.delete(cacheKeyList);
  });
  batchQuery.run();
  ```

## 5. 对象拷贝 (BeanUtil)
**规则**：禁止手动写大量的 `set` 方法进行 DTO 到 Entity 或 Entity 到 VO 的转换。必须使用 `cn.hutool.core.bean.BeanUtil`。
- **示例**：`Entity entity = BeanUtil.copyProperties(request, Entity.class);`

## 6. JSON工具 (JsonTemplate)
**规则**：禁止使用 `JSONObject`, `JSONArray`, `JSON`, `ObjectMapper` 等工具类进行 JSON 解析。必须使用 `JsonTemplate`。
- **示例1**：`JsonTemplate.toBean(json, Employee.class);`
- **示例2**：`JsonTemplate.toList(json, Employee.class);`
- **示例3**：`JsonTemplate.toJson(object);`
- **示例4**：`JsonTemplate.toMap(json);`
