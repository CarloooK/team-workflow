# NestJS / TypeScript Development Patterns

Generic class-level patterns extracted from real project audits. These apply to any NestJS + TypeORM + Vue/React project.

## 1. JWT Auth: The .env Loading Order Trap

**Symptom:** Login returns a valid token, but all `@UseGuards(JwtAuthGuard)` protected routes return 401. Token decodes and verifies fine in isolation.

**Root cause:** `JwtModule.register({ secret: process.env.JWT_SECRET || 'default-secret' })` evaluates at **import time** (module decorator evaluation), before `dotenv.config()` runs in `main.ts`. The secret used for signing and verification both fall back to `'default-secret'`, but if ConfigModule loads `.env` during NestJS bootstrap, the token issuer (JwtService) may pick up the real secret while the strategy still uses the default.

**Fix — use `registerAsync` + `ConfigService`:**

```ts
// auth.module.ts
JwtModule.registerAsync({
  inject: [ConfigService],
  useFactory: (config: ConfigService) => ({
    secret: config.get('JWT_SECRET', 'default-secret'),
    signOptions: { expiresIn: config.get('JWT_EXPIRES_IN', '7d') },
  }),
})

// jwt.strategy.ts — same pattern
constructor(config: ConfigService) {
  super({
    jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
    secretOrKey: config.get<string>('JWT_SECRET', 'default-secret'),
  })
}
```

**Also:** Remove manual `passport.use()` + `app.use(passport.initialize())` from `main.ts` — NestJS PassportModule handles this. Dual registration causes state pollution and test fragility.

**Detection script:**
```python
import json, base64, hmac, hashlib
token = json.load(open('/tmp/login.json'))['data']['accessToken']
parts = token.split('.')
msg = (parts[0] + '.' + parts[1]).encode()
sig = parts[2]
for secret in ['default-secret', 'actual-from-.env']:
    expected = base64.urlsafe_b64encode(hmac.new(secret.encode(), msg, hashlib.sha256).digest()).decode().rstrip('=')
    print(f'{secret}: {"MATCH" if sig == expected else "mismatch"}')
```

## 2. Jest Mock: Shared Object Reference Contamination

**Symptom:** Tests pass individually but fail when run together. A `findOne.mockResolvedValue(pendingTask)` returns a mutated object in the second test.

**Root cause:** `mockResolvedValue(sharedObj)` returns the **same object reference** every time. If the service modifies the object (e.g., `task.status = 'in_transit'`), subsequent tests see the mutation.

**Fix patterns:**

```ts
// ❌ Shared reference (first test's mutations persist)
const pendingTask = { status: 'pending' };
taskRepo.findOne.mockResolvedValue(pendingTask);

// ✅ Template constant + spread on each call
const PENDING_TASK = { status: 'pending' };
taskRepo.findOne.mockResolvedValue({ ...PENDING_TASK });

// ✅ Factory function for complex states
const makeDispatched = () => ({
  ...PENDING_TASK,
  status: 'dispatched',
  vehicleId: 1,
  driverId: 1,
});

// ✅ mockImplementation for dynamic state
let currentState: any;
const mock = {
  save: jest.fn().mockImplementation(async (e) => { currentState = e; return e; }),
  findOne: jest.fn().mockImplementation(() => Promise.resolve(currentState)),
};
```

**Also applies to `save` mock:** `jest.fn((e: any) => Promise.resolve(e))` returns a reference. Use `{ ...e }` to create a copy.

**Key rules:**
- Factory functions for mock data (`beforeEach` creates fresh instances)
- `mockResolvedValue` for repeated calls; `mockResolvedValueOnce` only for ordered single-use
- Shared state mock pattern (`currentState`) for save→findOne callback chains

## 3. Frontend-Backend API Field Mapping

**Three categories of mismatch (all silent — no JS error, just empty tables):**

### 3a. Sidebar path ≠ Router path
```js
// layout/index.vue (sidebar)
{ path: '/users', title: '用户管理' }

// router/index.js
{ path: '/user', component: ... }  // ❌ mismatch — page blank, no error
```

### 3b. Table column prop ≠ API field name
```vue
<!-- API returns { routeName: '...' } but prop="name" → blank column -->
<el-table-column prop="name" label="线路名称" />
```

### 3c. API path ≠ Controller path
```js
// Frontend: api='account-subjects' → /api/v1/account-subjects
// Backend: @Controller('accounts') → /api/v1/accounts  ❌ 404
```

**Diagnosis template:**
```bash
# 1. Check sidebar vs router alignment
grep "path:" layout/index.vue
grep "path:" router/index.js

# 2. Check API field names
curl -s "http://localhost:PORT/api/v1/resource?pageSize=1" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; print(list(json.load(sys.stdin)['data']['items'][0].keys()))"

# 3. Check frontend prop vs API field
grep 'el-table-column prop=' /path/to/page.vue
```

## 4. TypeORM Column Name Mapping Pitfall

**Symptom:** `entity.roleId` returns `null` despite DB having `role_id` with a value. API response shows `roleId: null`.

**Root cause:** When `synchronize: true` creates tables, TypeORM applies its naming strategy (camelCase → snake_case). When switching to `synchronize: false` + migrations, TypeORM defaults to the JS property name for column matching unless `name:` is explicitly set.

```ts
// ❌ Always null in migrations mode
@Column({ type: 'int', nullable: true })
roleId!: number;

// ✅ Works in both modes
@Column({ type: 'int', nullable: true, name: 'role_id' })
roleId!: number;
```

**Rule:** Any `@Column` where JS property name ≠ DB column name MUST have explicit `name:`. Do this from project inception to avoid migration pain.

**Check:** `\d table_name` in psql vs grep for `@Column` in entities.

## 5. TypeORM `@Column({ type: 'date' })` Returns String, Not Date

**Symptom:** `v.insuranceExpiry.getMonth()` throws `TypeError: not a function`.

**Root cause:** TypeORM may return `date` columns as strings (`'2027-01-15'`) rather than `Date` objects depending on driver configuration. TypeScript type annotation `Date` provides no runtime guarantee.

**Fix — runtime type normalization:**
```ts
const expiry = typeof v.insuranceExpiry === 'string'
  ? new Date(v.insuranceExpiry)
  : v.insuranceExpiry;
```

## 6. DTO Empty String Validation Trap

**Symptom:** API returns 400 when a query parameter is present but empty (`?startDate=`). Vue initializes `query = reactive({ startDate: '' })` and sends it as `''` not `undefined`.

**Root cause:** `@IsOptional()` only skips validation for `undefined`/`null`. The empty string `''` passes through to `@IsDateString()` which rejects it.

**Fix — `@Transform` empty to undefined:**
```ts
@IsOptional()
@Transform(({ value }) => value === '' ? undefined : value)
@IsDateString()
startDate?: string;
```

**Diagnose in browser console:**
```js
fetch('/api/v1/resource?page=1&pageSize=10&startDate=&endDate=', {
  headers: { Authorization: 'Bearer ' + localStorage.getItem('token') }
}).then(r => r.json()).then(d => console.log(d.code, d.message))
```

## 7. PostgreSQL Sequences vs Math.random() for IDs

**❌ Wrong:** `Math.random() * 10000` — not concurrency-safe, collision risk.
**✅ Right:** `SELECT nextval('seq_entity_no')` — atomic, never duplicates.

```ts
// Migration
await queryRunner.query(`CREATE SEQUENCE IF NOT EXISTS seq_entity_no START 1 INCREMENT 1`);

// Service
private async generateEntityNo(): Promise<string> {
  const now = new Date();
  const dateStr = formatDate(now);
  const [result] = await this.entityRepo.query(`SELECT nextval('seq_entity_no') as seq`);
  const seq = String(result.seq).padStart(4, '0');
  return `PREFIX-${dateStr}-${seq}`;
}
```

## 8. Global Passport Module Scope (NestJS ≤10)

If `PassportModule` is registered only in AuthModule and not marked `@Global()`, other modules' `AuthGuard('jwt')` can't find the strategy. Fix:

```ts
@Global()
@Module({
  imports: [PassportModule.register({ defaultStrategy: 'jwt' })],
  exports: [PassportModule],
})
export class AuthModule {}
```

## 9. Express Static Route Order

Static paths (`@Get('all-bindings')`) must be declared BEFORE parameterized paths (`@Get(':id')`) in the same controller. Express matches routes in declaration order.

```ts
@Get('all-bindings')  // ✅ first
async allBindings() { ... }

@Get(':id')           // ✅ second
async findOne(@Param('id') id: number) { ... }
```

## 10. Browser XHR Debugging for Silent 400/401 Errors

When a page shows no data and `catch {}` swallows errors, intercept XHR in browser console:

```js
const origSend = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.send = function(body) {
  this.addEventListener('load', function() {
    if (this.status >= 400) console.error('❌', this.status, this.responseURL);
  });
  return origSend.apply(this, arguments);
};
```

This reveals 400 validation errors, 401 auth errors, and 404 path mismatches that Vue's empty catch blocks suppress.

---

*Extracted from real-world NestJS audit sessions. Full project-specific context available in `nestjs-logistics-system` skill references.*
