# Recruitment Automation Audit (recruitment-automation)

**Source:** GitHub `CheeseClaw/recruitment-automation`, V3.3  
**Audit date:** 2026-05-13  
**Stack:** Python + Playwright (CDP, sync_api) + FastAPI (async) + DeepSeek LLM + Jinja2/HTMX

## Architecture Pattern

3-layer: FastAPI Routes → Service Layer → Library modules.
Browser automation via Playwright CDP connected to a shared Chrome instance.

## Key Issues Found

### Critical: Playwright sync_api in FastAPI async framework
- `lib/search.py`, `lib/communicator.py`, `lib/downloader.py` all use Playwright sync API
- API routes are async FastAPI → operations dispatched to `ThreadPoolExecutor` → shared Page object
- **Problem:** Page objects are NOT thread-safe — greenlet errors, context pollution
- **Solution (方案 D):** Independent Browser Context per operation (`browser.new_context(storage_state=...)`), close in `finally`
- **Status:** Partially implemented — folder pre-fetch uses independent context, but `collect_to_folder()` still uses shared Page

### High: RID inconsistency → HTTP 500 on collection from Web UI
- Web UI RIDs come from search API response, Playwright page may have been navigated away
- `collect_to_folder()` can't find `li[data-resumeidencode="rid"]` → timeout → 500

### Medium: Mixed path resolution strategies
- `lib/downloader.py` hardcodes `~/Downloads/recruitment` and `SCRIPTS_DIR / "records"`
- `lib/search.py` uses `init_paths(project_dir)` — PROJECT_DIR set globally
- Inconsistent — some modules respect configurable project dir, others don't

### Medium: Except: pass in critical paths
- `exporter.py` `export_excel()` wraps entire logic in try/except with silent pass
- `search_service.py` `_track_candidate()` silently swallows exceptions
- `communicator.py` multiple `except Exception: pass` in contact finding

### Low: CORS allow_origins=["*"] with --host 0.0.0.0
- Fine for local deployment, risky if accidentally exposed to LAN

## Notable Patterns (good)

1. **FolderCache with TTL** — pre-fetch folder names during search, serve from cache. Eliminates browser navigation pollution for folder reads.
2. **Scoring engine with YAML rules** — configurable keyword weights, industry/skills/boost/blacklist matching. Clean separation of logic and configuration.
3. **Resume parser fallback chain** — PyMuPDF → pdfplumber → rule-engine → LLM, with cache per file.
4. **Rate limiter with exponential backoff** — adaptive per-action intervals, daily counting, jitter.
5. **State machine tracker** — formalized status flow with VALID_TRANSITIONS dict and FOLLOWUP_DAYS for overdue detection.

## Test Coverage Gaps
- `downloader.py` — 0 unit tests (browser-dependency, but mockable via `unittest.mock`)
- `exporter.py` — 0 tests (CSV/Excel/HTML format validation)
- `rate_limiter.py` — 0 tests (backoff algorithm, jitter, daily reset)
- `api/routes/*.py` — 0 HTTP tests (FastAPI TestClient)
- `resume_parser.py` LLM path — not tested (mock the openai call)
- ~44 tests total, mostly covering pure logic (search, parser, tracker)

## Document Quality
Excellent — `issue.md` has detailed bug tracking with 6 proposed solutions evaluated in a comparison table. `docs/design/` directory has architecture design documents. Improvement plan tracks 13 items across phases.
