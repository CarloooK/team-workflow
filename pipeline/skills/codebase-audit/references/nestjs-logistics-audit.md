# NestJS 物流管理系统 — 真实审计案例

> 项目：NestJS 11 + Vue 3 + Flutter 物流管理系统
> 规模：Server 5625 行 TS + Admin 2868 行 Vue/JS
> 审查时间：2026-04-30

## 发现的模式

### 1. 声明修复与实际不一致

项目 README 声称"已移除全部 40 处 `as any`"，但实际仍有：
- `auth.module.ts:20` — `(process.env.JWT_EXPIRES_IN || '7d') as any`
- 6+ service 文件使用 `const where: any = {}` 进行动态查询
- `all-exception.filter.ts:20` — `(message as any).message`
- `main.ts:25` — `(payload: any`

**教训：** 声明修复后，必须 grep 验证。TypeORM 动态查询 + strict 模式是已知难题，需要 QueryBuilder 方案替代。

### 2. 认证双通路（NestJS 常见陷阱）

`main.ts` 第 14-27 行同时存在两套 Passport 策略：
- **通路 A：** 手动 `require('passport')` + `passport.use(new JwtStrategy(...))` + `app.use(passport.initialize())`
- **通路 B：** NestJS `PassportModule.register()` + JwtStrategy class 注入

问题：两个策略实例并行存在，验证结果不确定，`require()` 绕过 NestJS DI。

### 3. 编号生成并发冲突

三个服务使用同模式：
```ts
const seq = String(Math.floor(Math.random() * 10000)).padStart(4, '0');
return `EXP-${dateStr}-${seq}`;
// 同样的：TASK-{date}-{seq}、PAY-{date}-{seq}
```

`Math.random()` 不是并发安全的，虽然 unique constraint 兜底但会导致 500 错误。推荐 PostgreSQL SEQUENCE 或 Redis INCR。

### 4. 前端 CRUD 通用模板字段不全

所有 CRUD 页面共享同一个生成模板，但：
- `formFields` 只包含 3 个文本字段（prop、label、type）
- 缺少 select/date 等复杂字段类型配置
- 关键关联字段（如 customerId、routeId）缺失
- 自动生成的字段（taskNo）出现在表单中

**教训：** 代码生成模板需要手工审查和补全，不能直接投产。

### 5. 测试 mock 过于简化

- 仅 expense(10用例) + receivable(7用例) 两个测试文件
- `createQueryBuilder` 被完全 mock 返回硬编码值
- 核心业务（报警引擎 6 种规则）无测试

## 优先级排序

| 优先级 | 问题 | 修复方式 |
|--------|------|----------|
| H1 | 认证双通路 | 删 main.ts 14-27 行 + passport.initialize() |
| H2 | as any 残留 | 改用 QueryBuilder 条件拼接替代动态 where |
| H3 | 无数据库迁移 | 初始化 TypeORM migrations |
| H4 | 编号冲突 | 改用 PG SEQUENCE |
| H5 | 前端字段不全 | 逐个视图补全关联字段 |

## 参考

此项目的完整审查报告在项目目录 `审查报告.md`。
