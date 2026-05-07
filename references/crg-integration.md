# code-review-graph Integration Guide

[code-review-graph](https://github.com/tirth8205/code-review-graph) — local knowledge graph
for AI coding tools. Installed in the LogisticSystem project on Xiaoxin's WSL machine.

## Current Installation

| Item | Value |
|------|-------|
| Install method | `uv tool install code-review-graph` |
| Version | 2.3.2 |
| Graph location | `~/projects/LogisticSystem/.code-review-graph/graph.db` |
| Graph data | 198 files, 1,205 nodes, 5,943 edges (TypeScript/JS/Vue/Dart/Bash) |
| .gitignore | `.code-review-graph/` added |

## How the Pipeline Uses It (per bot)

### XPS (pre-design)
```bash
code-review-graph status  # quick health check of current module structure
```

### CarloMac (post-implementation — MANDATORY)
```bash
code-review-graph detect-changes --base HEAD --brief
# Output format:
#   Analyzed N changed file(s):
#     - X changed function(s)/class(es)
#     - Y affected flow(s)
#     - Z test gap(s)
#     - Overall risk score: 0.XX

# Attach the summary to the PR description before `gh pr create`
```

### Mela (pre-review — MANDATORY)
```bash
code-review-graph detect-changes --base main
# Outputs JSON with every changed function + risk score.
# Key fields to extract:
#   risk_score    — overall (0.0-1.0)
#   changed_functions[].name — function/class/test name
#   changed_functions[].risk_score — per-function risk
#   changed_functions[].is_test — boolean
#   changed_functions[].file_path — full path

# Filter for "high risk": risk_score >= 0.5
# Filter for "test gap": !is_test and parent/neighbor not tested

# Quick parse:
code-review-graph detect-changes --base main 2>&1 | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(f'Risk: {d[\"risk_score\"]}')
non_test = [f for f in d['changed_functions'] if not f.get('is_test')]
print(f'Business functions changed: {len(non_test)}')
high = [f for f in d['changed_functions'] if f.get('risk_score',0)>=0.5]
if high:
    print(f'High-risk ({len(high)}):')
    for f in high: print(f'  {f[\"name\"]} ({f[\"risk_score\"]})')
"
```

### Xiaoxin (release notes)
```bash
code-review-graph status | grep -E "Nodes|Edges|Files|Languages"
# Embed in release notes as: "Graph: X nodes, Y edges across Z files"
```

## Base Branch Flags

| Flag | Use Case |
|------|----------|
| `--base HEAD` | Check what the current (unstaged/working) changes affect |
| `--base HEAD~1` | Check last commit's impact (default) |
| `--base HEAD~3` | Check last 3 commits' cumulative impact |
| `--base main` | Check all changes since branching from main (for PR review) |
| `--base <commit-sha>` | Arbitrary comparison point |

## Real-World Output (LogisticSystem, 3-commit window)

```
17 changed files, 105 changed functions (90 test / 15 business)
Risk score: 0.50
0 affected flows (TypeScript flow detection is WIP)
15 test gaps flagged
```

High-risk functions flagged: auth login validation, task route/customer
mismatch checks, duplicate phone/plate detection — all in `.spec.ts` test
files themselves (conservative scoring). Mela should prioritize verifying
the **non-test** functions with risk >= 0.5.

## Known Quirks & Limitations

1. **Jest describe/it blocks**: Tree-sitter TypeScript parsing doesn't
   fully resolve Jest `describe('name', ...)` — the block gets named
   `describe:Name@L35` instead of a clean `describe('Name')`. The `it()`
   test names work better (captured as Unicode in the JSON). Don't rely
   on clean function names from test files.

2. **Flow detection**: Only reliable for Python repos (FastAPI, Flask).
   TypeScript/Go flow detection is ~33% recall — don't trust
   `0 affected flows` as a signal that no flows were affected.

3. **Risk scoring is conservative**: The scorer flags any non-test function
   that exists alongside a test file — it over-predicts. High risk doesn't
   mean broken, just "worth looking at." Precision ~0.38, but recall is 1.0
   (never misses a real impact).

4. **Build is idempotent**: Running `code-review-graph build` again on an
   existing graph just rebuilds from scratch. No harm in re-running.

5. **One graph per repo root**: The graph lives at `<repo>/.code-review-graph/`.
   Moving the repo breaks the graph. Re-run `build` after moving.

6. **CRG_DATA_DIR env var**: Overrides the default `.code-review-graph/`
   location. Useful for ephemeral workspaces or Docker volumes.

## Standard Project Initialization

When setting up a NEW project with CRG:

```bash
# 1. Install (once per machine)
uv tool install code-review-graph

# 2. Build graph
cd ~/projects/<new-project>
code-review-graph build

# 3. Add to .gitignore
echo ".code-review-graph/" >> .gitignore
git add .gitignore && git commit -m "chore: add .code-review-graph/ to .gitignore"

# 4. Verify
code-review-graph status
# Should show: Files, Nodes, Edges, Languages

# 5. Add CRG step to project AGENTS.md
# See hermes-multi-agent-pipeline SKILL.md § Full Cycle Walkthrough (CRG-enabled)
```

## MCP Server Mode (Advanced)

If Mela or XPS want the graph accessible to their AI tools:

```bash
cd ~/projects/LogisticSystem
code-review-graph serve  # stdio MCP server, 28 tools available
```

This exposes all 28 MCP tools (query_graph, detect_changes, traffic_graph,
semantic_search, etc.) over the MCP protocol. Configure in the bot's
`config.yaml` under `mcpServers` if using Hermes native MCP client.

## Key Commands Reference

| Command | When to Use |
|---------|-------------|
| `code-review-graph build` | First time setup, or after major restructure |
| `code-review-graph update` | After git pull / checkout branch (incremental) |
| `code-review-graph status` | Quick health check: nodes, edges, languages |
| `code-review-graph detect-changes` | Pre-commit or pre-merge impact analysis |
| `code-review-graph visualize` | Generate D3.js interactive HTML graph |
| `code-review-graph visualize --format obsidian` | Export as Obsidian vault |
| `code-review-graph visualize --format graphml` | Export for Gephi/yEd |

## Reinstallation on Other Machines

Each machine (Dell PC for XPS, MacMini for CarloMac, cloud for Mela) that
wants graph access needs its own installation:

```bash
uv tool install code-review-graph
cd ~/projects/LogisticSystem && code-review-graph build  # ~10s
```

The graph is local-only (SQLite, no cloud). It's *not* committed to Git —
each machine builds its own from the same `git ls-files` source tree.
