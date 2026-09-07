---
name: codebase-audit
description: "Review existing codebases for architectural problems, design flaws, and refactoring opportunities. Produces prioritized issue list + actionable refactoring plan. Also supports structured QA reports with severity ratings, test coverage analysis, and file:line references."
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [code-review, architecture, audit, refactoring, design-review, workflow, pr, git, lifecycle]
    related_skills: [systematic-debugging, requesting-code-review, writing-plans, receiving-code-review, github-code-review, codebase-qa]
---

# Codebase Audit

## Overview

Architectural code review is different from debugging or PR review. You're not looking for a specific bug — you're evaluating the overall design approach, implementation strategy, and long-term maintainability of a codebase.

**Core questions:**
- Is this the right tool/approach for the problem?
- Are there simpler, more robust alternatives?
- What will break when dependencies change?
- How much tech debt is baked in?

## Mandatory: Karpathy Coding Standards

Apply during any refactoring recommendations:
1. **Think Before Coding** — Understand what the code actually does before recommending changes.
2. **Simplicity First** — Recommend the minimum viable refactoring, not a full rewrite.
3. **Surgical Changes** — Audit findings should target specific problems, not wide cleanup.
4. **Goal-Driven Execution** — Each recommendation should have a clear verification criterion.

## When to Use

- User asks "what's wrong with this project?"
- User shares an unfamiliar codebase and asks for assessment
- Before starting a major refactoring
- First-time analysis of a project someone else built
- Retrospective on a completed project

## The Audit Process

### Phase 1: Surface-Level Assessment (5 min read)

First pass — get the lay of the land without deep diving:

1. **Check file count and sizes** — use `search_files` or `wc -l` on key files
2. **Read README / docs** — understand the stated purpose
3. **Scan project structure** — is it organized? Are there naming conventions?
4. **Check dependencies** — `requirements.txt`, `package.json`, config files
5. **Look for obvious smells**: hardcoded paths, credentials in code, dead code, debug artifacts (screenshots, test HTML dumps)
6. **Verify claimed fixes** — If the project README/docs claim something was fixed (e.g., "removed all `as any`", "lint clean", "all TS errors resolved"), grep for the residual pattern. One `grep -rn 'as any' src/` or `tsc --noEmit 2>&1 | head -20` exposes whether the claim holds.

### Phase 2: Architecture Analysis

Identify the fundamental approach and evaluate it against alternatives:

1. **What pattern is being used?** (Playwright browser automation, raw API, CLI wrapper, etc.)
2. **What would the ideal solution look like?** Start from zero design.
3. **What's the gap?** List concrete differences between current and ideal.
4. **Assess fragility**: What breaks when an external dependency changes? (e.g., website frontend redesign, API version bump, library deprecation)

**Key insight:** Browser automation (Playwright/Selenium) for operations that have a dedicated API is almost always the wrong choice — it's 10x more code, 100x less reliable, and triggers anti-bot measures.

### Phase 3: Deep Dive — Read the Core Logic

Focus on the main entry points and the most complex functions:

1. **Follow the error handling** — is it `except: pass` everywhere? Are errors swallowed?
2. **Trace data flow** — how does input become output? Are there unnecessary transformations?
3. **Check state management** — is state persisted correctly? Are there race conditions?
4. **Look for copy-paste** — repeated blocks that should be functions
5. **Evaluate abstractions** — are they the right level? Too leaky? Too rigid?
6. **Check ID generation** — Look for `Math.random()` based sequence numbers (`grep -rn 'Math.random.*10000\|Math.random.*padStart' src/`). Production IDs should use DB sequences (PostgreSQL SEQUENCE) or Redis INCR, not random ranges with collision risk.
7. **Verify declared fixes** — Cross-reference claims in README/CHANGELOG against actual code. Common patterns: grep `as any` for TS strict cleanup claims, check for ORM `synchronize: true` when the project says it's production-ready, look for leftover `.env` with default secrets when security fixes were claimed.

### Phase 4: Categorize and Prioritize

Classify each issue:

| Severity | Label | Criteria | Action |
|----------|-------|----------|--------|
| Critical | **Wrong approach** | The fundamental strategy is flawed (e.g., DOM automation when API exists) | Recommend rewrite of affected module |
| High | **Fragile** | Breaks on minor upstream changes (CSS class renames, HTML structure tweaks) | Isolate behind adapter, or replace approach |
| High | **Silent failure** | Errors are caught and ignored (`except: pass`) — user gets wrong output with no warning | Add proper error propagation |
| Medium | **Hardcoded constraint** | Paths, versions, credentials baked in | Extract to config/env |
| Medium | **Dead weight** | Debug screenshots, unused imports/comments, duplicated files | Delete |
| Low | **Style/readability** | Naming, formatting, comments | Clean up when touching |

### Phase 5: Produce the Output

Deliver in this order:

1. **Bottom line** (1-2 sentences: "This project needs a fundamental rewrite. Here's why.")
2. **Issue list** sorted by severity, with clear reasoning
3. **Refactoring plan** — numbered steps, ordered by dependency (do step 1 before step 2)
4. **For each step**: what to do, what files to touch, expected outcome

### Phase 6: Apply Prioritized Fixes (optional — user-driven)

When the user says "fix them" or "apply in priority order":

1. **Create a todo** — use `todo` to track progress, one item per fix, ordered by priority
2. **Apply each fix independently** — independent fixes can be done in parallel; dependent ones must be sequential
3. **Verify each fix immediately** — syntax check (`python -m py_compile` for Python; `tsc --noEmit` for TS), then re-read the file to confirm correctness
4. **Mark done and move to next** — update `todo` status as you go
5. **Final pass** — re-check that no fix broke another, no dead imports/variables were left behind

**Pitfall:** Don't batch-edit without verifying in between. A subtle bug in one fix can cascade into confusion about which change caused it.

### Phase 6a: Priority-Tier Organization (for large fix sets)

When the audit produces 10+ issues, organize them into **priority tiers** to avoid overwhelming the user:

| Tier | Label | Criteria | Example |
|------|-------|----------|---------|
| **Phase A** | Must fix | Breaks actual business flow. Bug in core logic (approval flows break, data goes missing, auth fails). | Missing rejection remarks, missing approval tiers, dead config entries, unused but structurally declared features. |
| **Phase B** | Enhancement | Feature not implemented but explicitly required. Missing functionality (reports, automation, management CRUD). | Financial statements, auto-cost amortization, maintenance plans. |
| **Phase C** | External | Requires third-party SDK, service, or physical integration. Cannot be done in current environment. | SMS push, GPS tracking, OCR, WeChat mini-program. |

Group fixes by tier when presenting to the user: "Phase A (3-4 days), Phase B (1-2 weeks), Phase C (external)". Apply all of Phase A first, then Phase B, and flag Phase C for the user.

Within each phase, apply in dependency order — fixes that unblock other fixes go first.

### Phase 6b: Final Verification (batch — after ALL fixes in a tier)

After completing a priority tier, run a **comprehensive verification** in a single batch. Do NOT verify only in between individual fixes:

```
1. TypeScript compilation — `npx tsc` (or `python -m py_compile` / `ruff check`)
2. Unit tests — `npm test` / `pytest` / `jest`
3. API smoke test — curl a core endpoint (e.g., login)
4. Frontend rebuild — if source files changed, `npx vite build` (or appropriate build command)
5. Service restart — `lsof -ti:PORT | xargs kill -9; node dist/main.js` (or systemd restart)
6. API re-verify after restart — curl login again to confirm service came up clean
7. **JWT config timing check** — If auth worked in dev but fails after a build/restart cycle, verify that the JWT token is signed with the real secret (not a fallback). See `references/nestjs-jwt-auth-troubleshooting.md` in the nestjs-logistics-system skill for the detection script. This is a silent failure mode: login returns 200 with a token, but all authenticated endpoints return 401 because the JWT strategy's secret differs from the signer's secret due to `.env` loading order.
```

**Key insight:** Frontend dist files are NOT auto-rebuilt. After editing any Vue/JS/CSS files under `admin/src/`, run `npx vite build` to regenerate `admin/dist/`. The backend serves `admin/dist/` statically — stale dist = stale code in browser. If the user reports 200-from-curl but problems in browser, rebuild is the first thing to check.

**Pitfall: test mocks drift from production code.** After changing service constructors (adding/removing `@InjectRepository`), methods (changing sync→async), or data access patterns (adding `repository.query()` for PG sequences), the existing `.spec.ts` files will fail. Expect this and budget time to update mocks — it's not a regression, it's maintenance. Follow the `nestjs-test-recovery.md` patterns for NestJS projects.

### Phase 7: Save findings as session reference

After audit + fix cycle completes:
- Save a condensed reference file under `references/<project-name>-audit.md`
- Include the architecture pattern, key issues found, and the fixes applied
- Helps future sessions recognize similar patterns without re-auditing from scratch

---

## Part D: QA-Style Structured Report (Static Analysis)

Use this section when the user asks for a "QA audit", "structured review", or wants a formal report with severity ratings across all dimensions (not just architecture). This is for repos you've cloned, not live running apps (those go to `dogfood`).

This part focuses on **systematic static analysis** — evaluating test coverage, security, code quality, documentation, and CI/CD — and producing a structured report with file:line references.

### Workflow

#### D1. Reconnaissance (clone & inventory)

When auditing a remote repo:

```bash
cd /tmp && git clone <repo_url>
cd <repo>

# Inventory
find . -type f -not -path './.git/*' -not -path '*/node_modules/*' -not -path '*/venv/*' | sort

# Tech stack
cat pyproject.toml / package.json / Cargo.toml / go.mod 2>/dev/null | head -30
cat requirements.txt / Gemfile 2>/dev/null | head -20
```

Read the README and any `docs/` directory. Then proceed with the Phase 1-7 audit process above.

#### D2. Dimension Evaluation Matrix

For each major component, evaluate across these dimensions:

| Dimension | What to check |
|-----------|--------------|
| **Architecture** | Layering, module separation, dependency injection, async/sync mismatch |
| **Testing** | What exists, what's missing, test quality (mocks, edge cases, temp dirs) |
| **Security** | CORS, API keys in logs, input validation, sensitive data, env vars |
| **Code Quality** | DRY violations, global state, exception handling, type hints |
| **CI/CD** | What runs in CI, coverage reporting, lint strictness |
| **Docs** | README completeness, inline docs, known issues tracking |

For FastAPI projects, use `references/fastapi-audit-checklist.md` for 9 additional dimensions: auth completeness, concurrency safety, state machine integrity, DB migration chain, and frontend-contract consistency.

**Key files to always read**: entry points, core lib modules, config files, test files (directory structure + conftest + coverage), CI config (`.github/workflows/`), issue tracking docs.

#### D3. Classify Findings (Severity × Category)

Assign every finding both a **severity** and a **category**:

**Severity**:
- **高 (High)** — User-facing bug, data loss risk, security vulnerability, architecture flaw that blocks features
- **中 (Medium)** — Can cause intermittent failures, degrades UX, missing error handling, significant tech debt
- **低 (Low)** — Minor code quality, naming, duplication, documentation gaps

**Category**: Functional / Architecture / Testing / Security / Code Quality / Docs / CI

**Every finding must include**: file:line reference, diagnosis (not just symptom), and concrete impact.

#### D4. Report Template

Write the report to the repo root as `qa-report.md`. Structure:

```markdown
# QA Report: <project-name>

**Repo**: <url>
**Date**: <date>

## 1. Project Overview

| Dimension | Rating |
|-----------|--------|
| Architecture | /5 |
| Code quality | /5 |
| Testing | /5 |
| Security | /5 |
| Docs | /5 |
| CI/CD | /5 |

## 2. Test Coverage Analysis

| Test file | Modules covered | # cases | Notes |
|-----------|----------------|---------|-------|

## 3. Findings (sorted by severity)

| # | Severity | Description | File | Details |
|---|----------|-------------|------|---------|

## 4. Testing Coverage Gaps

Systematic gap analysis: which src/ files have no tests.

## 5. Functional Testing Limitations

What can't be tested in the current environment (browser, API keys, login).

## 6. Improvement Recommendations

Prioritized: High / Medium / Low, with what to do and why.

## 7. Summary

Overall assessment with 1-5 ratings across dimensions.
```

Optionally write a second file `docs/qa-suggestions.md` for cross-cutting concerns, partial-fix analysis, and multi-file refactoring recommendations.

#### D5. Deliver

1. Save the report file
2. If user owns the repo: add to git, commit, push (ask first per red-line policy)

### QA-Specific Pitfalls

- **Don't assume you can run the app** — this is static analysis only. Browser-based QA (dogfood) is separate.
- **Don't guess at login-dependent features** — note as "cannot verify without credentials".
- **File references must be precise** — "line 42-47" not "somewhere in downloader.py".
- **When a project has an `issue.md` or known-issues doc**, read it first to avoid repeating stale findings.
- **Verify claimed fixes exist in code, not just docs** — don't trust design docs; trace the code paths.
- **Check both the "new path" and the "fallback path"** — error recovery, batch operations, reconnection paths are where architecture gaps hide.
- **When auditing a refactoring branch, verify Phase-by-Phase claims against the actual code** — docs may claim "all tests pass" but a test may hang on external dependency (AI spawn, network call, DB connection). Always actually run the test suite to completion, not just start it.
- **Watch for tests that silently block** — a test that hangs on `spawnSync` of an external binary (`openclaw infer`, `which some-tool`, etc.) won't show as failed in a timeout. Run the suite with a short per-test timeout to detect stuck tests: `npx mocha 'tests/**/*.test.js' --timeout 5000`. If it hangs, grep the test for external process spawns.
- **Fix pattern for test-hangs-on-AI-spawn**: When a module calls an external AI binary (e.g., `openclaw infer model run`) via `spawnSync` and the test environment can't run it, the correct fix is to:
  1. Remove the AI path from the module entirely if pure-regex/rule-based alternatives exist (intent analysis, classification tasks)
  2. Update `sortByIntent` / equivalent functions to drop the `config` parameter if it was only used for AI prompts
  3. Re-export only the remaining functions from the module
  4. **Update ALL callers** — not just the internal usage inside the module, but also other files that import the AI function (e.g., `refresh.js` calling `analyzeIntentWithAI`). Grep all `src/` for imports of the removed functions.
  5. Update tests to cover the new pure-logic interface
  6. Run full suite to confirm no residual hangs
  Do NOT add `--no-ai` flags or mock injection points — that just perpetuates the dual-path complexity. If AI analysis is genuinely needed, use `delegate_task` with Hermes' own LLM instead of spawning an external binary.
- **When a project replaces OpenClaw with Hermes** (or any similar agent swap): `src/email/generator.js` often retains dead code — `OPENCLAW_BIN` declaration, `spawnSync` import, and `buildAIPrompt` function that's never called. After verifying no external callers exist (`grep -rn "buildAIPrompt\|OPENCLAW" src/ --include="*.js"`), remove all of them along with their module exports. The generator may not use AI at all — it may just build template-structured emails and signatures. Verify the actual `generateEmail` code path before assuming AI is needed.
- **Check for residual inline data after "extract to shared" refactoring** — grep for patterns that should have moved (e.g., `COUNTRY_CONTINENT` dict still defined in `excel-reader.js` when `shared/countries.js` exists). This is a common Phase-2 regression in multi-module refactors.
- **Stale comments in refactored files are a signal** — `node scripts/xxx.js` usage patterns in `src/` files after CLI restructuring indicate incomplete documentation cleanup. Not high-severity but worth noting for completeness.
- **Invariant: audit branches with mock/stub data, not real connections** — When creating a test tenant for verification after audit fixes, ensure the test config explicitly disables external dependencies (SMTP/IMAP/bounce scanning) rather than hoping they don't trigger. Set `imap_smtp_skill_path: ""`, `bounce.enabled: false`, `reply_eml.enabled: false` in the test user's config.json. Run `--dry-run` to cover core logic (translation, template rendering, state machine) without network.
- **Detection pattern for silent test hangs in multifile audits**: After fixing a test-hangs-on-AI-spawn in one module, grep for SAME pattern in OTHER files that import from the same module. In the email-campaign audit, `analyzeIntentWithAI` was used in both `intent-analyzer.js` (sortByIntent) AND `email/refresh.js` (reply matching) — refresh.js was also calling the removed function and would hang if run against a real inbox. Grep `src/` not just the test file.
- **Findings without severity or actionable remediation are noise** — skip trivial style nits.
- **Trace claims to their origin, not just their latest copy** — 当一条「必做项/约束/结论」在多处文档反复转述（评审→契约→注释→backlog 的传声筒），先 grep 追到最早出处，核实源头本身是否可靠。源头可能：①自相矛盾（同一文件前后两节口径冲突）；②含未验证假设（「若支持则启用」被下游当成「已支持」）。实例：CustomerVisitRecord「写钉钉前按业务键查重」从方案骨架 §3.1 传 5 层到 backlog，但源头 §3.1 用组合键、§10.1 已升级为 visit_uuid，且「create_records 幂等参数」是「若支持则启用」的未验证假设；核实后从业务角度（概率 × 后果 vs 成本）判为过度工程，降级为「已知限制延后」。

### Reference Files from QA Module

- `references/qa-template.md` — Markdown report template (copy into output)
- `references/qa-example-report.md` — Concrete example from a real QA audit, showing multi-file output, finding format, and severity rating

---

## Common Anti-Patterns to Call Out

| Anti-pattern | Red flag | Better approach |
|---|---|---|
| Browser automation for API-backed workflows | Playwright clicking buttons to search/form/submit | Call the API directly with requests |
| Playwright sync API in async framework | Playwright sync_api used from FastAPI/Starlette via ThreadPoolExecutor | Isolate each operation in an independent Browser Context (`browser.new_context(storage_state=...)`) with unique page per call; never share Page objects across threads |
| Mixed path strategies | Some modules use auto-detected PROJECT_DIR, others hardcode `~/Downloads/recruitment` | Single source of truth for all path resolution — `init_paths(project_dir)` at startup, all modules read from a central PROJECT_DIR constant |
| Silent error swallowing | `except: pass` or `except Exception: pass` | Log + re-raise or return error state |
| Log-parsing for structured data | Regex on log lines to extract JSON-like info | Parse the original data source (API response, DB query) |
| Config-as-side-effect | MCP tools writing temp config to disk during a call | In-memory override, restore afterward |
| Dual-path state management | Login stored in both persistent profile AND auth.json, checked differently | Single source of truth |
| DOM-dependent logic with no abstraction | CSS class names and HTML selectors scattered throughout business logic | Isolate behind a thin adapter layer at minimum |
| `Math.random()` for ID/sequence numbers | `Math.random() * 10000` as order IDs, expense numbers, task codes | Use DB sequence (PostgreSQL SEQUENCE) or Redis INCR for persistent, collision-free counters |
| Dual auth path (NestJS) | `main.ts` manually registers passport strategy via `require('passport')` WHILE NestJS PassportModule also registers one | Delete the manual registration; rely fully on NestJS DI + PassportModule |
| `JwtModule.register()` with raw `process.env` | `JwtModule.register({ secret: process.env.JWT_SECRET || 'default-secret' })` in a NestJS module decorator — `.env` hasn't loaded yet, so token signing and verification both fallback to `'default-secret'` | Use `JwtModule.registerAsync({ inject: [ConfigService], useFactory: (config) => ({...}) })` so the secret is resolved after NestJS has loaded `.env` via ConfigModule |
| Database sync instead of migrations | `synchronize: true` in production OR no migration scripts at all | Use TypeORM migrations or similar versioned schema tool; synchronize only for initial dev bootstrap |
| FastAPI inline import in route handler | `from app.repository.xxx import XxxRepository` inside a route function | Import at module top; if lazy loading is needed, use DI |
| FastAPI route bypasses state machine | `orm.status = "approved"` directly in service layer | Always call `engine.transition_to(orm, new_status)` |
| FastAPI bare DB commit in route handler | `await db.commit()` scattered across handlers | One `db.commit()` per service method; route only calls svc method |

### Fix pattern: replacing spawn-to-external-skill with direct npm packages

When a Node.js project delegates SMTP/IMAP/API calls to external skill scripts via `spawnSync('node', [skillPath, ...])`:

1. **Inventory all spawn sites** — grep for `spawnSync.*script\|spawn.*skill\|_smtp_script\|_imap_script\|IMAP_SCRIPT\|SMTP_SCRIPT\|SKILL_SCRIPT` across `src/` and `scripts/`
2. **Replace SMTP** — use `nodemailer.createTransport()` with host/port/secure/user/pass directly from config. Each tenant's config carries its own SMTP credentials.
3. **Replace IMAP** — create a shared `src/email/imap-client.js` that wraps the `imap` npm package with `searchInbox(imapConfig, options)` and `downloadEml(imapConfig, uid, outputDir)`. Use `mailparser` (`simpleParser`) for parsing raw MIME.
4. **Update config schema** — add `smtp.host/port/secure/user/pass` and `imap.host/port/secure/user/pass` to each tenant config. Store runtime-compiled versions as `_smtp_config` and `_imap_config` in `config.js` loader.
5. **Update ALL report senders** — report email functions in `src/reports/summary.js` and `src/reports/bounce-reporter.js` also spawn the SMTP skill for sending digests. Convert them to nodemailer too.
6. **Remove dead config code** — after migration, `config.js` no longer needs `resolveSkillPath()` or `imap_smtp_skill_path` / `email_guardian_skill_path` fields. The tenant config fields `imap_smtp_skill_path` and `email_guardian_skill_path` can be removed from `users/_template/config.json`.

**Pitfalls:**
- `imap` npm package uses callbacks, wrap in promises
- `mailparser.simpleParser()` handles MIME parsing but is async — don't use in sync context
- Nodemailer `sendMail()` is async — the original `sender.send()` was synchronous via `spawnSync`; the new version must stay async-compatible in the caller
- 163 / other Chinese mail providers often have SSL certificate issues — set `tls: { rejectUnauthorized: false }`
- SMTP/IMAP credentials in config.json are plaintext — consider `.env` or encrypted storage for production if the user requests it
- `imap` npm package `search()` returns UID seq numbers, not email objects — you must `fetch()` each UID separately, then parse

## Carol's Preferences (when auditing)

- **No flattery.** Don't say "this is a good question" or "great project." Give direct assessment.
- **Prioritize by severity first**, then by dependency order.
- **Bottom line up front** — state the most important finding in the first paragraph.
- **Be specific about what's wrong and why**, not just "this could be better."
- **Red lines**: deleting files, modifying config, touching auth — ask first.

## Reference Files

See `references/` directory for session-specific audit reports that document real-world findings and patterns encountered in the wild.

### Parallel Delegation for Comprehensive Analysis

For large-scale audits (full PRD gap analysis + full API endpoint testing + database schema review), use `delegate_task` to run independent analysis tasks in **parallel**. This cuts end-to-end audit time by ~40% versus sequential execution.

**Pattern:**
```
1. Launch parallel tasks:
   - Task A: API endpoint testing (curl every route, verify status codes)
   - Task B: PRD gap analysis (compare each requirement against code implementation)
   - Task C: Database schema review (verify ORM matches actual DB structure)

2. Both tasks run independently, each with its own tool budget

3. Compile results into a unified report
```

**Example from session:**
```python
# Launch two parallel analysis tasks
delegate_task(
    goal="对所有后端 API 端点逐个做 HTTP 调用测试",
    context="项目路径 + 后端URL + 测试数据",
    toolsets=["terminal"]
)
delegate_task(
    goal="将 PRD 的每个功能需求逐一比对当前代码实现",
    context="前端+后端路径 + PRD路径",
    toolsets=["terminal", "file"]
)
```

**Prerequisites for parallel delegation:**
- The analysis domains must be **truly independent** (no shared mutable state)
- Each task must have sufficient tool budget (`max_iterations` or `exit_reason` monitoring)
- Results should be structured (summary + detail) to allow merging
- Both tasks spawn from the same session so results return to the same context

**When NOT to parallelize:**
- When one analysis depends on another's findings (e.g., gap analysis before fix)
- When both tasks modify the same files (use `process`/background for I/O instead)
- When the model context window is under strain from large codebase reads

When a requirements document is pushed alongside code changes, use `references/gap-analysis-methodology.md` to produce a structured gap document. This handles the pattern of: upstream pushes new PRD → run tests → catalog failures → categorize gaps → produce report.

### Available Reference Files

- `references/nestjs-patterns.md` — Generic NestJS/TypeScript development patterns compiled from multiple audits: JWT auth timing, Jest mock contamination, frontend-backend field mapping, DTO validation, PG sequences for IDs, passport module scope, and browser XHR debugging.
- `references/nestjs-logistics-audit.md` — NestJS 11 + Vue 3 logistics system audit: dual auth paths, claimed-fix verification, Math.random() ID collision, frontend CRUD template gaps, shallow test mocks
- `references/liepin-recruiter-audit.md` — Playwright browser automation audit: path hardcoding, Linux compatibility, login detection, popup handling
- `references/nestjs-audit-checklist.md` — NestJS/TypeScript project audit: TS strict mode, cross-module entity access, auth, test coverage
- `references/flutter-skeleton-audit-checklist.md` — Flutter skeleton project audit: Provider bugs, route registration, login flow, API layer issues
- `references/fastapi-audit-checklist.md` — FastAPI backend audit: 9 review dimensions (auth, concurrency, state machine, tests, migrations) + FastAPI-specific anti-patterns table
- `references/hr-bot-audit.md` — Python FastAPI + DingTalk + ChromaDB RAG audit: hardcoded secrets, misleading deps, collection caching, chunking quality
- `references/rag-ingestion-pitfalls.md` — RAG ingestion domain patterns: ChromaDB duplicate IDs from multi-page PDFs, ONNX vs sentence-transformers dep conflicts, pyngrok vs CLI ngrok, chunk boundary quality
- `references/rag-image-pdf-handling.md` — Handling image-only/screenshot PDFs: topic registry fallback, Chinese bigram keyword matching, skip-OCR pattern
- `references/rag-retrieval-quality.md` — RAG retrieval quality patterns: fixed-window infinite loop bug, full-text concatenation before chunking, multi-source round-robin retrieval, query expansion for weak embedding models, TOP_K tuning
- `references/qa-template.md` — Markdown QA report template (structured severity × category output)
- `references/qa-example-report.md` — Concrete QA report example from a real recruitment-automation audit
- `references/email-campaign-audit.md` — Node.js email campaign multi-tenant refactoring audit: test hangs on AI spawn, residual inline data after shared extraction, stale comments in refactored CLI paths

---

## Part B: Receiving Code Review Feedback

This section covers how to respond when receiving code review feedback. Load this section when the user shares PR feedback or review comments on your code.

### Core Principle

Code review requires technical evaluation, not emotional performance. **Verify before implementing. Ask before assuming. Technical correctness over social comfort.**

### The Response Pattern

```
WHEN receiving code review feedback:

1. READ: Complete feedback without reacting
2. UNDERSTAND: Restate requirement in own words (or ask)
3. VERIFY: Check against codebase reality
4. EVALUATE: Technically sound for THIS codebase?
5. RESPOND: Technical acknowledgment or reasoned pushback
6. IMPLEMENT: One item at a time, test each
```

### Forbidden Responses

**NEVER:**
- "You're absolutely right!" (performative agreement)
- "Great point!" / "Excellent feedback!"
- "Let me implement that now" (before verification)

**INSTEAD:**
- Restate the technical requirement
- Ask clarifying questions
- Push back with technical reasoning if wrong
- Just start working (actions > words)

### Handling Unclear Feedback

```
IF any item is unclear:
  STOP - do not implement anything yet
  ASK for clarification on unclear items

WHY: Items may be related. Partial understanding = wrong implementation.
```

### Source-Specific Handling

**From your human partner:** Trusted — implement after understanding. Still ask if scope unclear. No performative agreement. Skip to action.

**From External Reviewers:** Before implementing, check: technically correct for THIS codebase? Breaks existing functionality? Reason for current implementation? Does reviewer understand full context?

**If suggestion seems wrong:** Push back with technical reasoning.

### When To Push Back

- Suggestion breaks existing functionality
- Reviewer lacks full context
- Violates YAGNI (unused feature)
- Technically incorrect for this stack
- Conflicts with your human partner's architectural decisions

**How to push back:** Use technical reasoning, not defensiveness. Ask specific questions. Reference working tests/code.

### Acknowledging Correct Feedback

When feedback IS correct:
```
✅ "Fixed. [Brief description of what changed]"
✅ "Good catch - [specific issue]. Fixed in [location]."
✅ [Just fix it and show in the code]

❌ "You're absolutely right!"
❌ "Great point!"
❌ ANY gratitude expression
```

### Implementation Order for Multi-Item Feedback

1. Clarify anything unclear FIRST
2. Then implement: Blocking issues → Simple fixes → Complex fixes
3. Test each fix individually
4. Verify no regressions

---

## Part C: Finishing a Development Branch

This section covers what to do after implementation is complete and tests pass. Load this section when the user asks "what next?" after implementation.

### Overview

Guide completion of development work by presenting clear options and handling chosen workflow. **Core principle:** Verify tests → Present options → Execute choice → Clean up.

### Step 1: Verify Tests

**Before presenting options, verify tests pass:**
```bash
npm test / cargo test / pytest / go test ./...
```

**If tests fail:** Stop. Show failures. Don't proceed.

### Step 2: Determine Base Branch
```bash
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

### Step 3: Present Exactly These 4 Options

```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

**Don't add explanation** — keep options concise.

### Step 4: Execute Choice

#### Option 1: Merge Locally
```bash
git checkout <base-branch> && git pull
git merge <feature-branch>
<test command>  # verify tests on merged result
git branch -d <feature-branch>  # if tests pass
```

#### Option 2: Push and Create PR
```bash
git push -u origin <feature-branch>
gh pr create --title "<title>" --body "## Summary\n<2-3 bullets>\n## Test Plan\n- [ ] <steps>"
```

#### Option 3: Keep As-Is
Report "Keeping branch <name>." Don't clean up worktree.

#### Option 4: Discard
**Require typed "discard" confirmation.** Then:
```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

### Step 5: Cleanup Worktree (Options 1, 2, 4)
```bash
git worktree list | grep $(git branch --show-current)
git worktree remove <worktree-path>  # if in worktree
```

### Quick Reference
| Option | Merge | Push | Keep Worktree | Cleanup Branch |
|--------|-------|------|---------------|----------------|
| 1. Merge locally | ✓ | - | - | ✓ |
| 2. Create PR | - | ✓ | ✓ | - |
| 3. Keep as-is | - | - | ✓ | - |
| 4. Discard | - | - | - | ✓ (force) |

### Red Flags

**Never:**
- Proceed with failing tests
- Merge without verifying tests on result
- Delete work without confirmation
- Force-push without explicit request

**Always:**
- Verify tests before offering options
- Present exactly 4 options
- Get typed confirmation for Option 4
- Clean up worktree for Options 1 & 4 only