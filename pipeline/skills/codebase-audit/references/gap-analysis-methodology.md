# Gap Analysis: Requirements vs Implementation

Methodology for systematically comparing a PRD/requirements document against actual code.

## When to Use

- User pushes new requirements docs and asks "what's the gap?"
- Before starting a new feature phase
- After upstream changes to requirements

## Process

### Phase 1: Load Both Sides

1. Read the requirements document (PRD, spec, user stories)
2. Catalog every functional requirement with ID (T01, B01, etc.)
3. Identify what the codebase actually implements

### Phase 2: Three-Way Comparison

Compare against three sources simultaneously:
- Requirements Doc
- Prototype (if exists)
- Codebase

Each gap gets: requirement ID, current status, expected behavior, actual behavior, fix scope.

### Phase 3: Categorize Gaps

| Gap Type | Meaning | Action |
|----------|---------|--------|
| Missing feature | Required but not built | Implement |
| Behavior mismatch | Built but works differently | Fix to match spec |
| API change | Interface changed | Update all consumers |
| Deprecated | Removed from reqs but code still has | Remove code |
| New requirement | Added after code was built | Implement |

### Phase 4: Impact Analysis

For each gap:
- Test impact (how many break?)
- Flutter impact (what UI changes?)
- Backend impact (routes/models/services?)
- Migration needed (DB schema?)

## Phase 5: Produce Deliverable

Write the report to one of these locations (in preference order):
1. `docs/gap-analysis-<version>.md` — if project has a `docs/` directory
2. `.hermes/plans/<topic>-gap-analysis.md` — if project uses `.hermes/` for planning artifacts
3. Project root `<topic>-gap-analysis.md` — fallback for projects with no structured docs

Sections to include:
- Change Summary table
- Scoring/State Machine/UI Changes
- Test Status (before/after)
- Fix Priority Order

### Concrete Example (V1.1 gap analysis)

From the FamilyBoard V1.0→V1.1 migration, the gap analysis produced this structure:

```markdown
# Gap Analysis: V1.1 Requirements vs Current Code

## 1. Scoring Change (5→4 levels)
| Old | New | Impact |
|-----|-----|--------|
| unsatisfied 0.6x | removed | engine/__init__.py |
| rejected 0x | failed 0x | rename + Flutter |
| passable 0.8x | passable 0.6x | coefficient change |

## 2. State Machine Change  
| Old | New | Impact |
|-----|-----|--------|
| create→OPEN | create→DRAFT→publish→OPEN | 20 tests fail |

## 3. Test Status
| Suite | Before | After |
|-------|--------|-------|
| task_repo | 9 pass | 0 pass (all fail) |
| API | 9 pass | 5 pass |
| Edge cases | 6 pass | 2 pass |
```

## Tools

```markdown
| Old (implemented) | New (required) | Impact |
|-------------------|----------------|--------|
| 5-level rating    | 4-level rating | engine + Flutter |
| OPEN status       | DRAFT->OPEN    | 20 tests fail |
```

## Tools

- `git diff --stat` — See what changed upstream
- `pytest --tb=line -q` — Rapid test failure categorization
- `grep -rn` across routes, models, Flutter files
