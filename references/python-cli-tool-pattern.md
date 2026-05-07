# Python CLI Tool Pattern (for `scripts/` in Hermes Workspace)

## When to Use

Build a lightweight Python CLI tool when:
- The task is too complex for a one-liner (`du -sh`, `find`, `grep`)
- The output needs to be consumable by other tools (JSON mode)
- Multiple options (exclude patterns, depth limits, units)

## Standard Interface Contract

```bash
python scripts/<tool>.py <path> [options]
```

### Exit Codes

| Code | Meaning | When |
|------|---------|------|
| 0 | Success | Normal completion |
| 1 | Permission error | Can't read path/dir (without `--ignore-permission-denied`) |
| 2 | Path not found | Path doesn't exist or isn't a directory |
| 125+ | Reserved | For future error categories |

### Always Do

- **`argparse`** for CLI parsing (standard library, no deps)
- **`--json`** flag for machine-readable output → JSON with consistent fields
- **`--help`** that shows the docstring (add `add_help=False` then handle `--help` manually to avoid exit code constraints)
- **`if __name__ == "__main__": main()`** guard
- **Python 3.10+** — no walrus operator, no match-case, no 3.11+ features (WSL2 Ubuntu 22.04 ships 3.10)

### JSON Output Contract

Always include these fields (add more as needed):

```json
{
  "path": "/absolute/path",
  "total_bytes": 123456789,
  "human_size": "117.7 MB",
  "file_count": 42,
  "elapsed_ms": 15,
  "errors": []
}
```

## Common Pitfalls

### 1. Exclude Pattern Matching

**Wrong — substring match causes false positives:**
```python
if pattern in dirname:  # --exclude "doc" matches "docs", "documentation"
```

**Right — exact match only:**
```python
if dirname == pattern:  # --exclude "node_modules" only matches exact name
```

If glob patterns are needed later, add `fnmatch.fnmatch()` as a second check.

### 2. Symlink Handling

Default to **NOT following symlinks** (`os.lstat` not `os.stat`). Circular symlinks will cause infinite loops with `os.walk(followlinks=True)`.

```python
st = os.lstat(fp)         # safe default — ignores symlinks
# st = os.stat(fp)        # follows symlinks — only if explicitly requested
```

### 3. Sparse File / Disk Usage

`os.path.getsize(fp) == os.stat(fp).st_size` reports **apparent size**. For disk usage, use `st.st_blocks * 512`.

Two modes:
- `--disk-usage` → `st.st_blocks * 512` (actual disk blocks consumed)
- default → `st.st_size` (logical file size, may overcount sparse files)

### 4. Permission Errors

`os.walk` raises `PermissionError` on directories it can't enter. Catch and decide:
- **Strict mode** (default): propagate — let the user know
- **Lenient mode** (`--ignore-permission-denied`): log error, continue

### 5. Large Directories

`os.walk` is fine up to ~1M files (~2s). Beyond that, consider:
- `os.scandir()` + recursive calls (avoids building full `dirnames`/`filenames` lists)
- `--max-depth` flag to limit recursion

## Template

```python
#!/usr/bin/env python3
"""<tool>.py — <one-line description>.

Usage:
    python scripts/<tool>.py <path> [options]

Options:
    --json     Output JSON
    --help     Show this message

Exit codes:
    0   Success
    1   Permission error
    2   Path not found
"""

import argparse
import json
import os
import sys
import time


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args()

    if args.help:
        print(__doc__)
        sys.exit(0)

    path = os.path.abspath(args.path)
    if not os.path.exists(path):
        result = {"error": f"Path not found: {path}"}
        print(json.dumps(result) if args.json else result["error"])
        sys.exit(2)

    start = time.perf_counter()
    # ... business logic ...
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    if args.json:
        print(json.dumps({
            "path": path,
            # ... result fields ...
            "elapsed_ms": elapsed_ms,
            "errors": [],
        }, indent=2))
    else:
        print(f"Result: ...")

    sys.exit(0)


if __name__ == "__main__":
    main()
```

## Concrete Example: `dirsize.py`

See `scripts/dirsize.py` in the Hermes workspace for a complete implementation:
- `~200` lines
- `argparse` with 7 options
- `os.walk` with exclusion + max-depth
- JSON + human output
- All exit codes implemented
- Permission-error handling with `--ignore-permission-denied`
