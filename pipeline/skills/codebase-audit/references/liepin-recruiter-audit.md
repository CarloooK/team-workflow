# Liepin Recruiter Automation — Audit Report

Audit date: 2026-04-29
Project: 猎聘招聘助手 (liepin-recruiter)
Codebase: ~3800-line Playwright automation for resume search + folder archiving

## Bottom Line

The project chose browser automation (Playwright DOM manipulation) for what should be API calls. 80% of the code is fragile DOM navigation logic that will break on any website redesign. The API-first rewrite would be ~300-400 lines.

## Key Issues Found

### Critical: Wrong approach (Playwright DOM automation)
- Searching resumes by filling input fields, clicking buttons, scrolling dropdowns
- Archiving by finding "收藏" buttons via CSS class names that change per deployment
- 3800 lines of code for something a single POST request could do
- Triggers anti-bot CAPTCHAs constantly (`safe.liepin.com` redirects)
- Delays everywhere (2-5s per operation) to avoid rate limiting — API calls would be instant

### High: Silent error swallowing
- ~20 instances of `except Exception: pass` throughout the codebase
- Login detection loops that silently skip errors
- Results: failures produce incomplete output with no clear error message
- Debugging requires reading debug_screenshots/ manually

### High: Log-parsing for structured data
- `_parse_resumes_from_log()` uses regex on terminal log lines to extract resume fields
- If log format changes (e.g., an empty field produces different spacing), parser returns empty list
- MCP Server reports `total_found=0` even when search may have succeeded

### High: Hardcoded macOS paths
- `mcp_server.py` has `/Users/mdb4956/.workbuddy/...` hardcoded in PYTHON_BIN, AUTOMATION_SCRIPT
- `liepin_automation.py` uses `Path.home() / ".workbuddy"` — different from deployed path `/home/admin/chao/`
- Cannot run on Linux without manual path edits

### Medium: Config mutation by read-only operations
- `liepin_search_resumes()` writes override parameters to config.yaml permanently
- Subsequent searches without overrides use the wrong configuration
- `liepin_update_config()` also has this issue — writes on every call

### Medium: Dual-path login state
- `do_login()` stores session in persistent Chromium profile (CHROMIUM_USER_DATA)
- But `get_authenticated_context()` loads from auth.json
- MCP Server `check_status` only checks auth.json -> reports "not logged in" even when profile has valid session

### Medium: No retry mechanism
- All operations (click, archive, pagination) attempt once, log fail, skip
- Network jitter or page loading delays cause silent data loss

### Low: 54 debug screenshots shipped
- debug_screenshots/ directory is development artifacts, not user-facing documentation
- Screenshots consume space and confuse first-time readers

## Refactoring Plan

### Step 1: API discovery (manual — needs user with live account)
- Open Chrome DevTools, perform search + archive manually
- Identify the actual API endpoints, request/response formats, auth mechanism
- Document endpoints in a reference file

### Step 2: Rewrite core as API client
- Replace Playwright with `requests`
- Keep config.yaml format for consistency
- Add retry (2-3 attempts) on all API calls
- No delays needed; no DOM selectors; no CAPTCHA management

### Step 3: Rebuild MCP Server
- Direct import of new core module (no subprocess)
- Parameter overrides in-memory only
- Parse from JSON API responses, not log text

### Step 4: Clean up
- Delete debug_screenshots/
- Delete duplicate liepin_automation.py at root
- Unify paths to relative or env-based

## Fallback if API has anti-scraping

If the API has signature/timestamp verification (e.g., `sign=md5(timestamp + secret)`), the clean API rewrite may not be feasible. In that case:

1. **Use Playwright only for login** — get cookies, then use those cookies with requests
2. Keep search/archive as API calls using the cookie
3. Skip DOM manipulation entirely
