---
name: hermes-multi-agent-pipeline
description: "Full multi-agent software development pipeline with Hermes Discord bots. Architecture: 1 human (Carlo) + 4 bots (Xiaoxin/coordinator, XPS/systems-engineer, Mela/QA, CarloMac/implementer). Workflow: discuss → plan → human approval → execute → release. Communication via Discord channels, artifacts stored on GitHub."
version: 2.2.0
author: Carlo
---

# Hermes Multi-Agent Pipeline

> **源仓库**: https://github.com/CarloooK/team-workflow
> **同步**: `cd ~/team-workflow && git pull && bash setup.sh`
> **修改后记得同步回仓库**: `cp SKILL.md ~/team-workflow/pipeline/ && cd ~/team-workflow && git commit && git push`

A complete software development pipeline with **1 human + 4 Discord bots**
collaborating via Discord channels and GitHub repositories.

## Team

| Name | Machine | Role |
|------|---------|------|
| **Carlo** (human) | Any PC | Requirements, Final approval |
| **Xiaoxin** (bot) | Lenovo WSL | Coordinator, Config, Release, Docs |
| **XPS** (bot) | Dell PC | Systems engineer, Requirements analysis |
| **Mela** (bot) | Cloud server | QA, Testing, Code review |
| **CarloMac** (bot) | MacMini | Implementation, Creative coding |

## Pipeline Flow

```
① DISCUSS ──────────────────────────────────────
   Carlo → 发需求
   XPS → 可行性分析 + 🔍CRG status → @CarloMac
   CarloMac → 实现方案 + 🔍CRG detect-changes → @Mela
   Mela → 风险评估 + 🔍CRG blast radius → @Xiaoxin
   Xiaoxin → 总结（每 bot 最多 2 轮）

② PLAN ─────────────────────────────────────────
   Xiaoxin → 写 docs/plans/xxx.md → git push
           → "@Carlo 请审批 [链接]"

③ APPROVE ──────────────────────────────────────
   Carlo → "批准" → 执行
   Carlo → "修改" → XPS 调整 → 重新审批

④ EXECUTE ──────────────────────────────────────
   CarloMac → 代码 → 🔍CRG detect-changes
           → gh pr create → @Mela Review
   Mela → 🔍CRG detect-changes → Approve → Xiaoxin merge PR

⑤ RELEASE ──────────────────────────────────────
   Xiaoxin → 🔍CRG status 录入 release notes
           → gh release create → 写纪要
           → "@Carlo 发布完成"
```

> 🔍 = 执行 `code-review-graph` 命令。详见 `Full Cycle Walkthrough` 和 `references/crg-integration.md`。

---

## ⚠️ Critical Pitfalls

### 1. Discord @mention is NOT plain text

**The LLM writes `@XPS` as text.** Discord needs `<@USER_ID>` format for
a real mention. Without this, the @mentioned bot never receives the message
(because `DISCORD_ALLOW_BOTS=mentions` requires actual mentions).

**Fix:** Edit `gateway/platforms/discord.py` — add `_resolve_text_mentions()`
that scans outgoing messages for `@Name` patterns, looks them up in the
guild member list, and replaces with proper `<@ID>` syntax. See
`references/discord-mention-fix.md` for the exact patch.

**Test:** A real @mention shows the user/bot name in blue, clickable.
Plain text `@Name` stays black and is not clickable.

### 2. Auto-thread breaks multi-bot communication

`discord.auto_thread: true` causes Xiaoxin to create a new Discord thread
for each response. **Other bots are NOT added to that thread** and won't
see messages sent there.

**Fix:** Set `discord.auto_thread: false` in config.yaml:
```bash
hermes config set discord.auto_thread false
```
Then restart the gateway. All messages go to the main channel where every
bot can see them.

### 3. Files must go to GitHub, not local paths

**XPS on Dell PC wrote files to `~/projects/auto-backup/docs/` — these
are invisible to Xiaoxin on WSL. **All bots must share files through
GitHub.** Use `git clone`, `git pull`, then write, then `git push`.

### 4. A commit on one machine ≠ visible on another machine

Even when XPS commits to the repo locally, if `git push` fails (auth/permission
error), the files exist only on Dell PC. Xiaoxin running `git log` or
looking for the files on WSL will find nothing.

**This is a two-step failure**: (a) files written to repo → OK. (b) push
succeeded → must verify.

**Fix:** After any bot claims to have pushed, the next bot in the pipeline
(usually Xiaoxin) should **verify with `git pull`** before proceeding:
```bash
cd ~/<repo> && git pull --rebase && ls docs/plans/<expected-file>
```
If `git pull` reveals the file is missing, the push failed — report this
to Carlo in the summary instead of posting a Plan link that returns 404.

**Protocol:**
1. Bot commits → `git push`
2. Bot reports in Discord: `已提交，文件在 xxx`
3. **Next bot in pipeline** does `git pull` to confirm the file is actually on GitHub
4. If `git pull` shows "Already up to date" but the new file is absent → push failed
5. Report to Carlo: `git push 失败 — 凭证问题，文件仅存在于本地`
6. **During stalemate**: Xiaoxin recreates the files locally from conversation content (see `references/credential-stalemate-protocol.md`), then pushes everything in one batch when credentials arrive

**Coordinator project audit**: When Carlo asks to review an existing project's status, see `references/project-status-audit.md` for the 6-layer survey procedure

### 5. Xiaoxin speaks last, not first

Coordinator SOUL.md must enforce: "NEVER analyze a requirement — that is
XPS/CarloMac/Mela's job." Xiaoxin tends to jump in early. See the
Xiaoxin template for the exact wording that works.

### 6. ⛔ Stop Protocol — Carlo says stop, bots must stop IMMEDIATELY

**Real failure (2026-05-06 test):** Carlo posted "停止所有动作" at 1:31.
Xiaoxin replied "收到 @mentions。但我还缺一个关键信息..." and proceeded
to write code, run tests, and review for the next 2 minutes — 10+ tool
calls after the stop signal.

**Fix:** When Carlo says "停止" / "停" / "停止所有动作" / "stop":
1. No new tool calls — not even "先确认一下是哪个 PR"
2. Reply with EXACTLY ONE word: `收到，已停止。`
3. Wait for Carlo's next instruction
4. This overrides ALL other rules — including pending tasks, questions, and discussion flow

The same applies to "撤回合并请求": do not ask for PR number, default
to the most recently discussed relevant PR and act on it.

### 7. 🤐 No Standby Noise

**Real failure (2026-05-06 test):** 20+ messages of "收到，待命中" /
"明白" / "保持静默" / empty messages — zero information content.

**Fix:** If you have nothing substantive to say, say nothing. No echo
of other bots' standby messages. No empty replies. Exception: Carlo
asks "你在吗?" → one-word "在".

### 8. 🚫 Xiaoxin Does Not Implement Code

**Real failure (2026-05-06 test):** Xiaoxin wrote scripts/dirsize.py
entirely from scratch — write_file, test, review, bugfix. This is
CarloMac's job (implementation) or Mela's job (testing).

**Fix:** Xiaoxin's deliverables are plans (docs/plans/) and meeting
minutes (docs/meetings/). Coding (write_file of .py/.js/.ts) is
CarloMac's job. If Carlo says stop and Xiaoxin is mid-implementation,
drop it immediately — do not finish the file, do not push.

Exception: Trivial scripts under 50 lines that are pre-approved in a
plan, and only when no other bot is online.

### 9. 📋 Discussion Must Close Formally

**Real failure (2026-05-06 test):** After XPS + Xiaoxin exchanged
technical review on dirsize.py, nobody produced a formal summary plan.
No docs/plans/, no @Carlo with a link, no approval request. The
discussion just dissipated into standby messages.

**Fix:** After discussion converges (all bots spoken OR 2 min silence):
1. Xiaoxin writes a formal plan document to docs/plans/
2. Push to GitHub
3. Post link: `@Carlo 方案已完成：<URL> 请审批`
4. Never leave a discussion hanging — no plan = it didn't happen

### 10. 🔗 Bot @mention is text, not real Discord mention (multi-machine)

**The root issue:** Each bot's SOUL.md says `@Xiaoxin 请分析` as text.
Discord ignores text `@Name` — only `<@USER_ID>` triggers mention delivery.

**On Xiaoxin's machine** (has the `_resolve_text_mentions` patch in
gateway/discord.py): text `@Name` gets auto-converted to `<@ID>` before
sending. This works.

**On other machines** (Mela on cloud, XPS on Dell, CarloMac on MacMini):
No patch. Text `@Xiaoxin` stays as text. The @mentioned bot never sees
the message.

**Fix per machine:**
1. **Best:** Apply the `_resolve_text_mentions` patch to every bot's
   gateway/discord.py. See references/discord-mention-fix.md.
2. **Workaround (template only):** Put actual Discord IDs in SOUL.md:
   ```
   <@1500778215860604990> 请分析
   ```
   This works without any patch but requires knowing each bot's user ID.

**How to find bot/user Discord IDs:**
```bash
# Method 1: Check gateway log for <@ID> patterns
grep -o '<@[0-9]*>' ~/.hermes/logs/gateway.log | sort -u

# Method 2: Guild Members API (see discord-bot-mention-fix skill for full command)
```

**Current known IDs (LogisticSystem team):**
- Carlo: `<@1500751058958417961>`
- Xiaoxin: `<@1500758163522322525>`
- XPS: `<@1500778215860604990>`
- Mela: `<@1501072897383469258>`
- CarloMac: `<@1501220920772263977>`

---

## SOUL.md Design Rules ⚠️

SOUL.md is loaded into the bot's system prompt on **every message**.
Every character wastes context. Follow these rules:

### DO put in SOUL.md
- Who the bot is and its role
- Team members (just names and roles)
- Precise behavioral rules (speak order, max rounds)
- What to do when triggered by specific keywords
- What deliverables it produces
- Karpathy Coding Guidelines (4 principles, adapted to role)

### DO NOT put in SOUL.md
- Deployment instructions (how to install Hermes)
- Prerequisites checklists
- API keys or tokens
- Cost/performance notes (those are for humans)
- Command references (gh, git, tmux)
- Troubleshooting guides
- Example conversation transcripts
- Any text directed at the **human operator**, not the bot

### Target size
- **~1500-2000 characters** per SOUL.md (including Karpathy section)
- If it's longer, you're mixing in human docs

---

## Step 1: Configure Each Bot

### Prerequisites (per machine)
- Hermes Agent installed
- Discord Bot Token with Message Content Intent enabled
- `gh` CLI authenticated (shared GitHub token)

### Fix #1: Disable auto-thread (Xiaoxin's machine only)

```bash
hermes config set discord.auto_thread false
```

### Fix #2: Patch Discord @mention resolution (Xiaoxin's machine only)

Edit `~/.hermes/hermes-agent/gateway/platforms/discord.py` — see
`references/discord-mention-fix.md` for the exact diff.

### Profile setup

```bash
hermes profile create <bot-name> --clone-from default
```

### .env

```ini
DISCORD_ALLOW_BOTS=mentions
DISCORD_BOT_TOKEN=<bot-specific-token>
DISCORD_ALLOWED_USERS=<Carlo's Discord ID>
DISCORD_HOME_CHANNEL=<main-channel-id>
GITHUB_TOKEN=<shared-token>
```

> Consider different LLM providers per bot:
> - XPS/Mela → cheaper models (Gemini Flash, Claude Haiku)
> - CarloMac → strong model (Claude Sonnet, DeepSeek)
> - Xiaoxin → mid-range model

### SOUL.md

Copy from the templates in `templates/` to
`~/.hermes/profiles/<bot-name>/SOUL.md`.

### Start

```bash
hermes gateway run --profile <bot-name> --replace
```

### Verify

```bash
grep "Connected as" ~/.hermes/logs/gateway.log | tail -3
```

**Send a test message in Discord.** Confirm that @mentions show as
blue/clickable links, not black text.

---

## Step 2: SOUL.md Templates

Each template is ~40-60 lines, bot-focused, includes Karpathy Guidelines.
Copy to `~/.hermes/profiles/<bot-name>/SOUL.md` and adjust @names
to match the bot's actual Discord handle.

| File | Bot | Role |
|------|-----|------|
| `templates/soul-xiaoxin.md` | Xiaoxin | Coordinator |
| `templates/soul-xps.md` | XPS | Systems engineer |
| `templates/soul-carlomac.md` | CarloMac | Implementation |
| `templates/soul-mela.md` | Mela | QA |

---

### Step 3: GitHub Repo Structure

```text
<project-name>/
├── docs/
│   ├── plans/          # Proposals (Xiaoxin)
│   ├── meetings/       # Minutes (Xiaoxin)
│   ├── requirements/   # Analysis (XPS)
│   ├── design/         # Technical specs (XPS)
│   └── tests/          # Test plans (Mela)
├── src/                # Code (CarloMac)
├── tests/              # Automated tests (CarloMac)
├── scripts/            # Lightweight CLI tools (dirsize.py, etc.) — reusable pattern
```

**Every bot must cd to the git repo before writing files.**
Do NOT write to local paths like `~/projects/` — write to `<repo>/docs/...`
and push to GitHub so all bots can access them.

### Tooling: code-review-graph

[code-review-graph](https://github.com/tirth8205/code-review-graph) is
installed on Xiaoxin's WSL and configured for LogisticSystem. It builds
a Tree-sitter based knowledge graph of the codebase and exposes 28 MCP
tools for impact analysis, change detection, and context-aware reviews.

**When to use during pipeline:**
- **XPS** (pre-design): `code-review-graph detect-changes --base main` to
  understand current module structure and test coverage before proposing changes
- **CarloMac** (post-implementation): auto-runs on git commit via hooks
- **Mela** (pre-review): `code-review-graph detect-changes --base <merge-base>`
  to see blast radius and test gaps before diving into the diff
- **Xiaoxin** (release): include graph stats in release notes

See `references/crg-integration.md` for full commands, reinstallation on
other machines, and MCP server configuration.

---

## Full Cycle Walkthrough (CRG-enabled)

> **CRG** = `code-review-graph` — local knowledge graph for impact analysis.
> Pre-requisite: `uv tool install code-review-graph` (one time per machine).
> See `references/crg-integration.md` for full commands.

1. **Carlo posts in Discord channel (not thread):**
   `@Xiaoxin @XPS @Mela @CarloMac 我们需要一个CLI工具...`
2. **Xiaoxin** (one line only): `@XPS 请分析可行性`
3. **XPS** → feasibility analysis + CRG status to understand module structure
   → `@CarloMac`
4. **CarloMac** → implementation approach + CRG detect-changes on affected area
   → `@Mela`
5. **Mela** → risks + CRG blast radius analysis → `@Xiaoxin`
6. **Xiaoxin** → summary → writes `docs/plans/<topic>-<date>.md`
   → `git push` → `@Carlo 方案已完成：<URL> 请审批`
7. **Carlo** → "批准" (or "修改XX部分")
8. **Xiaoxin** → `@CarloMac 请开始实现` (or `@XPS 请调整方案`)
9. **CarloMac** → code → **CRG: `code-review-graph detect-changes --base HEAD`**
   → `gh pr create` → `@Mela PR #<n> 请Review` _(附 detect-changes 摘要)_
10. **Mela** → **CRG: `code-review-graph detect-changes --base main`**
    → review → `gh pr review <n> --approve` → 验证报告中包含 CRG 数据
11. **Xiaoxin** → merge PR → **CRG: `code-review-graph status` 附入 release notes**
    → `gh release create` → write minutes →
    `@Carlo v1.0 已发布`

### CRG Verification Checklist (per step)

**CarloMac (post-implementation):**
```bash
cd ~/projects/<repo>
code-review-graph detect-changes --base HEAD --brief
# 确认: 风险评分、变更函数数、测试缺口数
# 附在 PR 描述中
```

**Mela (pre-review):**
```bash
cd ~/projects/<repo>
code-review-graph detect-changes --base main
# 重点看: 高风险函数、测试缺口、影响范围
# 输出合并到验证报告的"变更影响"章节
```

**Xiaoxin (release):**
```bash
cd ~/projects/<repo>
code-review-graph status
# 将统计（节点数/边数/语言）写入 release notes

---

## Troubleshooting

| Issue | Root cause | Fix |
|-------|-----------|-----|
| Bot doesn't speak | Previous bot didn't @mention it (text vs real mention) | Check `_resolve_text_mentions` is patched |
| Other bots don't see messages | Thread created by auto_thread | Set `discord.auto_thread: false` |
| Xiaoxin analyzes instead of coordinating | SOUL.md too weak | Use strict "NEVER analyze — not your job" wording |
| XPS writes files nobody else can see | Files written to local disk | Must use GitHub repo; `git pull` before write |
| XPS commits but other bots can't find the file | `git push` failed (credential/permission) | Next bot runs `git pull` to verify; report failure to Carlo |
| Git push fails with `Authentication failed` | **Two possible causes**: 401 (invalid PAT) or 403 (valid PAT, no org access). **ALWAYS test first**: `gh api repos/<org>/<repo>` — 401 = bad token, false = no push access | 401 → Carlo generates new PAT. 403 → add collaborator or org-scoped PAT. During stalemate see `references/credential-stalemate-protocol.md` |
| Authentication succeeds but pushes to wrong user | Credential file `/home/chao/.git-credentials` may be 0 bytes after `patch` tool replaced content | Always verify after any credential write: `wc -c ~/.git-credentials`; if 0 → `echo "https://user:token@github.com" > ~/.git-credentials`; see `references/git-credential-debug.md` §2 |
| SSH says "Hi User!" but git push still denied | SSH key added to personal account, not as repo Deploy Key with write access | Generate dedicated deploy key; test with `ssh -i <key> -o IdentitiesOnly=yes -T git@github.com` — if "Hi User!" it's personal, if "Permission denied" it's not yet added anywhere |
| @mentions not working in Discord | Text `@Name` not real `<@ID>` | Patch discord.py per references |
| Discussion never ends | No round limit in SOUL.md | Add "max 2 rounds, then close" |
| Carlo slow to approve | Human delay | Xiaoxin: one reminder after 4h; during wait switch to productive standby — see `references/credential-stalemate-protocol.md` |
| Carlo slow to approve | Human delay — PR sitting open | **Pre-build during delay**: Write implementation based on approved design, stash locally. When Carlo merges, push immediately. See `references/pre-build-during-wait.md` and `references/python-cli-tool-pattern.md` for an example (dirsize.py). |
| Git conflict | Two bots push simultaneously | Feature branches; `git pull --rebase` before push |
| Discord bot offline but gateway running | state.db locked by CLI session | See `references/discord-gateway-diagnosis.md` — conflict between HERMES CLI session and gateway process sharing same state.db |
