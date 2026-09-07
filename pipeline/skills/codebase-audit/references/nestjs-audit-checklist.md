# NestJS + TypeScript 审计模式库

> 多个审计会话积累的 NestJS 特定模式，按审计发现频率排序。

---

## 1. JWT 认证 — 双策略注册（最常见）

**检查项：** `main.ts` 中是否手动注册了 passport strategy。

```ts
// ❌ 有害模式
const passport = require('passport');
passport.use(new JwtStrategy({...}, (payload, done) => { ... }));
app.use(passport.initialize());

// ❌ 同时 auth.module.ts 也有 PassportModule 注册
@Global() @Module({ imports: [PassportModule.register({...})] })
```

**问题：** 两个独立的 passport 策略实例导致认证行为不确定。修复见下方。

**修复检查列表：**
- [ ] `main.ts` 不含 `require('passport')`
- [ ] `main.ts` 不含手动 `passport.use(...)` 策略注册
- [ ] `main.ts` 不含 `app.use(passport.initialize())`
- [ ] `auth.module.ts` 有 `@Global()` + `exports: [PassportModule]`
- [ ] `jwt.strategy.ts` 正常继承 `PassportStrategy(Strategy)`
- [ ] `AuthGuard` 来自 `@nestjs/passport` 而非直接引用 passport

---

## 2. 跨模块实体访问模式

**检查项：** service 是否用 `@InjectDataSource() + dataSource.getRepository()` 获取跨模块实体。

```ts
// ❌ 绕过 DI 的可测试性问题
constructor(@InjectDataSource() private ds: DataSource) {
  this.studentRepo = ds.getRepository(Student);
}
```

**标准修复（3 个步骤）：**
1. 使用方 module 的 `TypeOrmModule.forFeature()` 添加需要的实体
2. Service 用 `@InjectRepository()` 注入
3. 清理 `@InjectDataSource()` 和 `dataSource.getRepository()`

```ts
// ✅ 标准模式
// module: TypeOrmModule.forFeature([OwnEntity, CrossEntityA, CrossEntityB])
// service:
constructor(
  @InjectRepository(OwnEntity)     private ownRepo: Repository<OwnEntity>,
  @InjectRepository(CrossEntityA)  private crossRepoA: Repository<CrossEntityA>,
) {}
```

---

## 3. synchronize → 迁移迁移

**检查项：** `TypeOrmModule.forRootAsync` 中 `synchronize` 是否为 `true`。

**问题：** 开发环境 `synchronize: true` 每次启动可能覆盖 schema 变更导致数据丢失。无法追溯 schema 变更历史。

**迁移步骤：**
1. 创建 `data-source.ts` 供 CLI 使用（用 `dotenv` 加载 `.env`）
2. `package.json` 添加迁移命令
3. 用 `typeorm migration:create` 创建空基线（已有数据库时）
4. 设置 `synchronize: false` + `migrationsRun: true` + migrations 路径
5. 基线迁移运行后，后续用 `migration:generate` 生成增量

**注意：** 首次 `migration:generate` 如果数据源已存在所有表，只会生成实体与数据库的差异。对于已有全量表的项目，用 `migration:create` 建空基线。

**data-source.ts 模板：**
```ts
import { DataSource } from 'typeorm';
import { config } from 'dotenv';
import { resolve } from 'path';
config({ path: resolve(__dirname, '../.env') });
export default new DataSource({
  type: 'postgres',
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432', 10),
  username: process.env.DB_USERNAME || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
  database: process.env.DB_DATABASE || 'logistics',
  entities: ['src/**/*.entity.ts'],
  migrations: ['src/migrations/*.ts'],
  migrationsTableName: 'migrations_project',
});
```

---

## 4. 非并发安全的编号生成

**检查项：** `Math.random()` 或 `Date.now()` + 随机数拼接的业务编号（单号/订单号）。

```ts
// ❌ 并发冲突风险
const seq = String(Math.floor(Math.random() * 10000)).padStart(4, '0');
```

**修复：PG 序列 + nextval()**

```ts
// 迁移文件
CREATE SEQUENCE IF NOT EXISTS seq_order_no START 1 INCREMENT 1;

// Service
const [result] = await this.repo.query(`SELECT nextval('seq_order_no') as seq`);
const seq = String(result.seq).padStart(4, '0');
return `ORD-${dateStr}-${seq}`;
```

---

## 5. DTO getter 属性 spread 丢失

**检查项：** 继承 `PaginationDto` 的 DTO 在 `{ ...query, extraProp }` spread 时是否丢失 `skip`/`take`。

**问题：** `PaginationDto` 的 `skip` 和 `take` 是 getter（位于原型上），`{ ...query }` 只复制 own properties，不复制 getter。

**修复：** 显式透传或使用 `as DtoType` 断言。

```ts
return this.findAll({ ...query, driverId, skip: query.skip, take: query.take } as QueryExpenseDto);
```

---

## 6. 前端 CRUD 通用模板缺陷

**检查项：** 标准 CRUD 页面的 `formFields` 是否全是 `type: 'text'`。

**常见缺陷：**
- 状态字段应为 `select` + 枚举选项
- 数字字段应为 `number` 类型
- 日期字段应为 `date` 类型
- 关联字段（foreign key）需要动态加载选项

**修复方向：**
- 硬编码枚举 → 直接写在 `formFields` 的 `options` 中
- 关联表选项 → `showDialog` 时并行加载

---

## 7. 审批流模式（费用/凭证审批检查项）

**检查项清单：**

```
[ ] 驳回时是否强制填写备注（所有驳回动作）
[ ] 大额审批是否同时检查单笔金额阈值和月累计阈值
[ ] 角色合并配置是否真的被代码使用（还是只是种子数据）
[ ] 审核流程状态机是否完整（草稿→待审→已通过/已驳回）
```

### 7.1 驳回备注强制

```ts
// 正确模式 — 每个驳回动作都要检查 remark
if (dto.action === 'reject' && !dto.remark) {
  throw new BadRequestException('驳回时必须填写备注说明');
}
```

检查所有审批方法（调度/财务/老板）的 reject 分支。

### 7.2 双重大额审批

```ts
// 需求通常有两层阈值：
// - 单笔超过 X 元 → 需上级审批
// - 月累计超过 Y 元 → 需最高级审批
// 两者同时独立检查

const forceReview = amount >= SINGLE_THRESHOLD;  // 单笔
const needBoss = await checkMonthlyTotal(amount) >= MONTHLY_THRESHOLD;  // 累计
```

### 7.3 角色合并配置

```ts
// 配置驱动：读取 approval_merge，如果 merged 则跳过中间审批环节
const mergeConfig = await configRepo.findOne({ where: { configKey: 'approval_merge' } });
const isMerged = mergeConfig?.configValue?.merge_dispatcher_finance === true;
```

---

## 8. 定金/预收款模式

**检查项：** 定金（先收款后关联运单）是否完整实现。

```
[ ] Deposit entity 存在（customerId, amount, linkedWaybillId, status）
[ ] 创建定金接口（status = unlinked）
[ ] 关联运单接口（status → linked，同时创建 partial 应收）
[ ] 尾款核销走标准 recordPayment 流程
```

### 典型流程

```ts
// 1. 创建定金
POST /deposits → { customerId, amount, depositDate }

// 2. 运单完成后关联
PATCH /deposits/:id/link → { waybillId }
// 内部逻辑：
//   - 更新定金 status = 'linked'
//   - 创建应收 receivable（totalAmount = 定金金额，receivedAmount = 已收定金）
//   - 运单尾款通过标准收款流程核销

// 3. 尾款收款
POST /record-payment → { receivableId, amount: tailAmount }
```
