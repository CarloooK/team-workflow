# FastAPI Backend Audit Checklist

9 review dimensions specific to Python FastAPI + SQLAlchemy async projects. Use alongside the full `codebase-audit` skill process.

## 1. Exception Handling

- [ ] bare `except: pass` / `except Exception: pass` swallowing errors (search: `except\s+(Exception)?\s*:\s*pass`)
- [ ] bare `except:` in WebSocket message handlers
- [ ] Database flush/commit exceptions uncaught or unwrapped
- [ ] async context managers missing timeout controls (`asyncio.wait_for` on long ops)
- [ ] Error responses returning internal detail vs generic messages

## 2. Authorization & Access Control

- [ ] Every mutating endpoint (POST/PUT/DELETE) has an explicit permission check
- [ ] No endpoint relies solely on "creator_id from JWT" without verifying the user owns the resource
- [ ] `require_admin` / `require_role` dependencies exist and are applied
- [ ] Deletion endpoints check ownership, not just existence
- [ ] Cross-family access prevented (member from family A cannot access family B's data)
- [ ] WebSocket JWT validation on connect, not per-message

**Common FastAPI gap:** Route handlers that accept a `family_id` from the JWT dependency but never verify the target resource belongs to that family.

## 3. Concurrency & Race Conditions

- [ ] Point/balance mutations use `SELECT ... FOR UPDATE` or conditional `UPDATE ... WHERE balance >= amount`
- [ ] Inventory deduction checks stock with row-level lock, not read-then-write
- [ ] Claim/accept operations use `UPDATE ... WHERE status='open'` (optimistic lock via affected rows)
- [ ] Shared-resource claim uses DB unique constraint, not application-layer check
- [ ] No two concurrent requests can cause double-spend on the same account
- [ ] ORM `expire_on_commit=False` is set (prevent stale object reads)

**Common FastAPI gap:** `member.points -= amount` followed by `db.commit()` — two concurrent requests read the same old balance, both decrement, one overwrite is lost.

## 4. Input Validation

- [ ] ALL Pydantic models have min/max length, regex, and ge/le constraints — not just in DTOs but in Create/Update models too
- [ ] Enum fields use Pydantic enums or `Field(pattern=...)`, not bare `str`
- [ ] Rating/status fields are constrained to known values, not free-form strings
- [ ] Negative/zero values rejected at the model level (Field(ge=0)), not in handler logic
- [ ] List endpoints validate filter params (page size, status values) and reject unknown values
- [ ] `model_dump(exclude_none=True)` is used for partial updates to avoid overwriting fields with None

**Common FastAPI gap:** `rating: str` in request body with no enum — `"invalid-rating"` passes validation and may bypass code paths intended for known values.

## 5. Code Quality — FastAPI-Specific

- [ ] Route handlers delegate business logic to Service layer, not inline DB queries
- [ ] No `__import__()` dynamic imports in route handlers
- [ ] No inline `from app.repository.xxx import XxxRepository` inside route functions (lazy import smell)
- [ ] Dependency functions are in `deps.py`, not scattered across routes
- [ ] Route ordering: static paths before parameterized paths (e.g., `/board` before `/{task_id}`) — FastAPI matches in order
- [ ] WebSocket state is dict-based, not class-based, and cleanup removes stale connections
- [ ] Unit-of-work pattern: `db.commit()` called once per service method, not scattered in routes
- [ ] State machine transitions are enforced by a central engine, not bypassed with direct `orm.status =` assignments

## 6. Frontend-API Contract Consistency

- [ ] Integration tests assert the same response shape as production routes return
- [ ] No stale group keys or field names in tests that differ from actual code
- [ ] Schema versions match between API docs (OpenAPI) and frontend expectations
- [ ] Duplicate route aliases (`/claim` + `/accept`) are intentional, not accidental
- [ ] CORS origin config is appropriate for deployment (`["*"]` for dev, specific origins for prod)

## 7. Test Coverage — Core Gaps

- [ ] Concurrent operations (two users claiming same resource, spending same balance)
- [ ] Authorization failure cases (non-owner accesses resource, kid calls admin endpoint)
- [ ] WebSocket connect/disconnect/reconnect patterns
- [ ] Expired JWT token handling
- [ ] Role-based access (parent-only, kid-only endpoints)
- [ ] Data isolation between families
- [ ] Every repository method has at least a happy-path and failure-path test
- [ ] Integration tests use a server fixture (httpx.AsyncClient with ASGITransport), not raw service calls

**Common FastAPI gap:** Service-layer tests pass but API-layer tests missing — route auth deps, middleware, and error handlers only exercised at the HTTP level.

## 8. State Machine Completeness

- [ ] Every enum value is in the transition table (no "compatibility aliases" left dangling)
- [ ] No backwards transitions from terminal states (closed, forfeited, cancelled)
- [ ] Rejected states have a path back to active (retry / resubmit)
- [ ] State machine is enforced in the engine, not bypassed with raw field assignment in service layer
- [ ] Status field in ORM matches the domain enum after every transition

## 9. Database Migrations

- [ ] Migration chain is linear (check `alembic history`)
- [ ] Every ORM column has a corresponding migration
- [ ] No `synchronize=True` in production DB config
- [ ] Seed data matches current schema
- [ ] Migration downgrades are defined or explicitly omitted with a note

## FastAPI-Specific Anti-Patterns

| Anti-Pattern | Red Flag | Fix |
|---|---|---|
| Route handler does DB logic | Route calls `db.execute(...)` directly | Delegate to Service → Repository |
| Dependencies do DB reads per call | `get_current_family` queries Memeber table | Embed `family_id` in JWT claims |
| Service creates new service instances | `svc = TaskService(self.db)` inside another service | Pass shared db session or use DI |
| async handler with sync DB call | `asyncio.to_thread(sqlalchemy.orm.session.query)` | Use async session throughout |
| Route returns raw ORM objects | Return type is `TaskOrm`, not `Task` pydantic | Use `Task.model_validate(orm)` |
| Commit in route, not service | `await db.commit()` after every repo call | One commit per service method |
| Repo.create does db.commit() + refresh() | Repo calls `await self.db.commit()` | Flush only; let service own the transaction boundary |
| Service bypasses state machine | `orm.status = "approved"` directly | Always call `engine.transition_to(orm, TaskStatus.APPROVED)` |
| Bare `except` in WebSocket | `except Exception:` with no reconnect logic | Log + cleanup + retry strategy |
