# AI_BountyBoard PRD Gap Analysis (V1.4)

**Project**: AI_BountyBoard (Family Board) — FastAPI + Flutter full-stack
**PRD Version**: V1.4 (2026-07-09, 家庭名称显示与多家庭加入)
**Prior Analysis**: V1.3 gaps were resolved during prior sessions — this covers V1.4 delta
**Method**: Full codebase walkthrough — backend (14 Python modules), frontend (18 Dart modules), database ORM schema

## Architecture Structure

```
backend/
  app/
    api/v1/        — auth, family, tasks, wishes, redemptions, others, ws, deps
    core/models/   — Pydantic models (task, member, points, family, wish, redemption, reward, pet)
    core/orm/      — SQLAlchemy ORM (all 11 tables in __init__.py)
    core/engine/   — Pure functions (state machine, ratings, XP calc, level config)
    service/       — task_service, auth_service, xp_service, points_service, engine_service, ai_service
    repository/    — Data access layer (task_repo, member_repo, points_repo, etc.)
frontend/
  lib/
    features/auth/     — Login, family create/join, auth provider
    features/tasks/    — Parent home (5 tabs), kid home (2 tabs), task provider
    features/wishes/   — Wish/redemption providers
    features/points/   — Radar chart, member provider
    models/models.dart — Task, Member, Wish, Redemption, RewardItem
    core/network/      — API client + WebSocket client
```

## Key Findings at a Glance

| Severity | Count | Top Issues |
|----------|-------|------------|
| 🔴 Severe | 2 | M12 `/family/join` backend missing, M11 family name not in AppBar |
| 🟡 Medium | 5 | T05 late-submission rating cap, B04 delay days display, W02 auto-shelve, M02 PIN guard, K04 no wish tab |
| 🔵 Minor | 4 | W01 image placeholder, M03 add-form simplified, K02 badge wall, N02 non-pessimistic lock |
| ⚫ NFR | 3 | N01 no perf data, N05 compliance absent, 6.1 double-entry not implemented |
| 📋 Forward | 2 | 6.2 JSONB fields missing, 6.3 LLM adapter missing |

## 🔴 Severe Gaps (Frontend calls non-existent backend API)

### M12: 「加入此家庭」后端缺失
- **Issue**: `family_selector_widget.dart` line 85 calls `POST /family/join` with `family_id, name, role, pin` — but **no such route exists** on the backend. `grep -rn "join" backend/app/` finds only the event type constant `MEMBER_JOINED` in `ws.py`.
- **Impact**: Users who select a family and click "不是以上成员？加入此家庭" will get a 404 from the API. The join form renders but submission always fails.
- **Fix**: Add `POST /family/join` to `backend/app/api/v1/family.py`. Creates a new MemberOrm under the given family_id with specified role/pin, returns `member_id`. Must enforce M13 (name uniqueness per family).

### M11: 家庭名称未显示在 AppBar
- **Issue**: PRD requires format「🏠 家庭名 · 用户名」. Backend returns `family_name` in login response (auth_service line 28). Frontend `AuthState` stores it (`familyName`). But `parent_home_page.dart` line 27 renders:
  ```dart
  title: Text(auth.memberName ?? '家长面板'),
  ```
  Missing `auth.familyName` entirely.
- **Fix**: Change to `Text('🏠 ${auth.familyName ?? ""} · ${auth.memberName ?? "家长面板"}')`.

## 🟡 Medium Gaps (Partial implementation)

### T05: 延期提交评分限制未实施
- Backend: `task_service.submit()` correctly sets `is_late_submission = 1` when overdue.
- Backend: `task_service.review()` does NOT check `is_late_submission` before allowing Delight. Needs to cap max rating to "satisfied".
- Frontend: `_PendingReviewSection` buttons in `parent_home_page.dart` line 530+ don't gray out "惊喜(120%)" for late tasks.

### B04: 延期天数不显示 + Delight 按钮不禁用
- Frontend: `task_card` shows "已延期" badge but no `延期 X 天` count text.
- Frontend: When `_is_overdue == true`, Delight button should be grayed/disabled — currently still clickable.

### W02: 愿望非自动架店
- PRD: "定价后自动包装为专属商品上架". Current: requires separate `POST /wishes/{id}/publish` call (manual step).
- Fix: Merge `setpoints` + `publish` into a single endpoint or make `PUT /wishes/{id}/setpoints` also publish when points > 0.

### M02: 切号无 PIN 码路由拦截
- PRD: "从孩子端切回家长端时，前端路由强制拦截，必须触发4位数字PIN码或本机安全生物识别校验".
- Current: `app_router.dart` has no route guards. Switching between `/kid` and `/parent` paths has no auth challenge.

### K04: 孩子端愿望无独立 Tab
- PRD: "独立的分页列表，专门用来管理自己提报的、仍处于申请或被拒状态的原始愿望".
- Current: `_WishSection` is embedded in the points tab as a Card, limited to 5 items via `.take(5)`. No expand-all or dedicated tab.

## ⚫ NFR Gaps

### N05: COPPA/GDPR 合规未实现
- No PII filtering for kid routes
- No avatar system (client-rendered cartoon vector)
- No name anonymization in API responses
- No age gate for under-13 compliance

### 6.1: 复式记账表未创建
- PRD specifies `family_economy_log` with `source_account/target_account/asset_type/reason_code`
- Current: separate `points_ledger` table (simple), XP stored directly on `members.xp`, no credit score system at all
- `operator_id` is present in `points_ledger` ✅

### 6.2: JSONB 字段缺失
- `TaskOrm`: no `ai_metadata` column
- `FamilyOrm`: no `parent_preferences` column

### 6.3: LLM 适配器未实现
- No `infrastructure/llm_client.py`
- No `request_structured_output()` interface
- `ai_service.py` exists but is empty/placeholder

## ✅ Confirmed Complete

| ID | Specification | Where |
|----|--------------|-------|
| T01 | 27 templates | `task_templates.dart` (26 with content; 宠物照料 category empty) |
| T02 | 7 category filters | Category chips in _PublishTab |
| T03 | Repeatable toggle | TemplateSettingOrm + template/settings API |
| T04 | Shared lock via UNIQUE INDEX | `UserTaskMappingOrm.__table_args__` |
| T06-T07 | 4-level rating (1.2/1.0/0.6/0.0) | `engine/__init__.py RATINGS` |
| T08-T09 | Edit/delete Open tasks | `task_repo.update_task/delete` with status check |
| T10 | Creator-only review | `task.review` checks `task.creator_id == reviewer_id` |
| B01-B07 | Kanban: 5 tabs, time filter, badges, overdue, inline rating, inline edit, updated_at | `_BoardTab` in parent_home_page.dart |
| B09 | Taker name on cards | `kid_count > 1` check in `get_board_data` |
| P01-P05 | Points system | `points_ledger` table, `PointsService`, `PointsRepository.get_by_category` (excludes wish), yearly stats, rating multiplier |
| W01-W04 | Wish CRUD + pricing + publish/reject | wish_repo, wish API routes |
| R01-R10 | Redemption lifecycle | reward_items, redemptions, fulfill/archive pattern, approve/reject with refund |
| M01 | Family creation | FamilyOrm + family_repo.create |
| M03 | Kid profile fields | MemberOrm has birth_date, gender, preferences, age |
| M04 | Dual-parent audit | `operator_id` in points_ledger |
| M08 | Pet CRUD | PetOrm, pets API, _PetManage |
| M09 | JWT middleware | `deps.py` `get_current_member/require_admin` |
| M10 | Dual token | Access + Refresh in auth_service |
| M13 | Name uniqueness | `member_repo.name_exists_in_family` + ValueError |
| K01-K02 | Kid points display + yearly stats | _PointsTab in kid_home_page.dart |
| K05 | Unified store grid | _RedeemSection in kid_home_page.dart |
| K08 | 3-state kid task board | _TasksTab filters open/claimed/done |
| N02 | Shared-task concurrency | UNIQUE INDEX `(user_id, task_id, date_str)` |
| N04 | Docker compose | docker-compose.yml with db+backend+frontend |

## Common Pitfalls for This Project

1. **M12 is highest priority** — frontend calls non-existent API, making the entire "join family" feature unusable
2. **M11 is the easiest fix** — single line change in parent AppBar
3. **Late-submission cap (T05)** requires both backend and frontend changes — backend to reject delight, frontend to disable the button
4. **Pessimistic lock (N02)** — current `UPDATE ... WHERE status='open'` is correct for Postgres (row-level lock via MVCC), but PRD explicitly asks for `SELECT FOR UPDATE`. Low risk but noted.
5. **W02 auto-shelve** is a design trade-off: manual publish gives the parent a review step, but PRD explicitly says "自动且立刻将其包装为该孩子的专属唯一商品"
