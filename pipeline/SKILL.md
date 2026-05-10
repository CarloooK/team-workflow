---
name: hermes-multi-agent-pipeline
description: "Full multi-agent software development pipeline with Hermes Discord bots. Architecture: 1 human (Carlo) + 4 bots (Xiaoxin/coordinator, XPS/systems-engineer, Mela/QA, CarloMac/implementer). Workflow: discuss → plan → human approval → execute → release. Communication via Discord channels, artifacts stored on GitHub."
version: 2.6.0
author: Carlo
---

# Hermes Multi-Agent Pipeline

> **源仓库**: https://github.com/CarloooK/team-workflow
> **同步**: `cd ~/team-workflow && git pull && bash setup.sh`
> **自动巡检**: cron 每 30 分钟检查一次 remote 更新 → 自动拉取 + 通知 Carlo
> **修改后必须同步回仓库**（协议规则，全员遵守）
>
> ### 同步协议（全员必须遵守）
>
> **当你修改了 pipeline skill 或相关配置文件后：**
>
> 1. 先提交到本地 team-workflow 仓库
>    ```bash
>    cp ~/.hermes/skills/software-development/hermes-multi-agent-pipeline/SKILL.md ~/team-workflow/pipeline/
>    cd ~/team-workflow && git add -A && git commit -m "update: <请简述修改内容>"
>    ```
>
> 2. **不要直接 push** — Carlo 需要在合并前审批（Human-in-the-Loop）
>
> 3. 通知 Carlo:
>    ```
>    @Carlo 流程有更新，请审批推送：
>    cd ~/projects/team-workflow && git push
>    改动内容: <简单描述改了哪里>
>    ```
>
> 4. Carlo 批准后，执行 `git push`。其他机器会在下个 30 分钟 cron 周期自动拉取。
>
> 5. 如果 Carlo 要求你先不推送（还需要修改），保持本地提交即可，cron 不会自动推送未提交的内容。
>
> **例外 — 紧急修复（CI 挂了、流程阻塞）：**
> - 可直接 push 并在 Discord 说明：「紧急修复，已直接推送」
> - 非紧急情况一律等 Carlo 审批

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
   Xiaoxin → 📖 查 docs/knowledge/ 关联历史
           → 转发给 Carlo
   Carlo → 发需求
   XPS → 可行性分析 + 🔍CRG status → @CarloMac
   CarloMac → 实现方案 + 🔍CRG detect-changes → @Mela
   Mela → 风险评估 + 🔍CRG blast radius → @Xiaoxin
   Xiaoxin → 总结（每 bot 最多 2 轮）

② PLAN ─────────────────────────────────────────
   Xiaoxin → 写 docs/plans/xxx.md
           → 写 docs/knowledge/xxx.md 🧠
           → git push
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

## CLI Direct Mode (non-Discord)

When Carlo talks to Xiaoxin directly in the **terminal** (not Discord),
the multi-bot pipeline is bypassed. This is faster for focused tasks:

```
Carlo (terminal) -> Xiaoxin implements + tests + docs + push
```

**When to use CLI vs Discord:**

| Situation | Mode | Reason |
|-----------|------|--------|
| New feature, needs discussion | Discord | XPS/CarloMac/Mela participate in design |
| Bug fix, small change | CLI | Faster, no coordination overhead |
| Migration/refactor (e.g. MCP -> DingTalk) | CLI | Plan approved, then execute in one session |
| Emergency fix | CLI | Fastest path |
| Carlo doesn't know the solution | Discord | Multiple perspectives needed |

**CLI mode rules:**
- Same plan -> approve -> execute cycle, but faster (Xiaoxin does all steps)
- Plan is written to `docs/plans/` as usual
- Carlo's approval is verbal ("开始做", "推进", "ok") — no need for formal link posting
- Tests must still pass before push
- Secrets rule (pitfall #12) applies equally
- If Carlo says stop, stop immediately — same as Discord mode

**Real example (2026-05-07):** fault-analysis-mcp MCP Server -> DingTalk bot
conversion. Plan approved via CLI discussion, implementation done in same
session, 106 tests written and passed, all pushed in one batch.

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

### 8. 🚫 Xiaoxin Does Not Implement Code (Discord Mode Only)

**Real failure (2026-05-06):** In Discord multi-bot mode, Xiaoxin wrote
scripts/dirsize.py from scratch instead of delegating to CarloMac. This
wastes the pipeline — CarloMac is the implementer.

**Rule (Discord mode):**
- Xiaoxin's deliverables are docs (plans, minutes, design). Coding is
  CarloMac's job.
- Exception: Trivial scripts under 50 lines, pre-approved in a plan,
  and only when no other bot is online.

**CLI mode exception (2026-05-07):** When Carlo talks to Xiaoxin
directly via terminal (not Discord / not multi-bot), this rule does
**not** apply. In CLI mode:
- There is no CarloMac available
- Xiaoxin implements everything: code changes, tests, documentation
- The pipeline is: plan -> implement -> test -> push, all in one session
- The Discord bots (XPS, CarloMac, Mela) are not involved
- Quality gates still apply: tests must pass, docs must be updated,
  secrets must never be hardcoded

**How to tell which mode you're in:**
- **Discord**: Multiple bots are @mentioned; Carlo starts with
  `@Xiaoxin @XPS @Mela @CarloMac`
- **CLI**: Carlo speaks directly in terminal; no bot @mentions; Carlo
  gives direct instructions like "开始做" / "先出方案"

**Stop rule applies in both modes:** If Carlo says stop in either mode,
stop immediately — even mid-implementation in CLI mode.

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

### 12. 🔒 Secrets must NEVER be hardcoded in code or committed to GitHub

**Real instruction (2026-05-07):** Carlo explicitly stated: "后续所有涉密信息，不能硬编码，更不能上传到Github".

**Applies to:**
- API keys, tokens, passwords → always use `.env` or environment variables
- Internal business data (fault DBs, customer info, internal config) → verify it's safe to push before committing
- Credential files (`~/.git-credentials`, `~/.ssh/*`) → added to `.gitignore` already at the system level
- SaaS SDK secrets (DingTalk ClientID/ClientSecret, Discord tokens, GitHub PATs)

**Enforcement:**
- All `.env` files are in `.gitignore` by default — do NOT override this
- If a project needs configuration templates, use `.env.example` with placeholder values
- Before `git add -A`, mentally scan: "does any file I'm adding contain a secret?"
- When wiring up a new service, the first file to create is `.env` — then reference it from code with `os.environ.get("KEY")`
- If a secret was accidentally committed, notify Carlo immediately — do not push

**Exception:** Public demo/test keys created specifically for open-source examples (e.g., Stripe test mode keys, public API demo tokens).

### 14. 🤫 Silent Wait Protocol — 等Carlo时全员闭嘴

**Real failure:** 讨论进入等待Carlo决策的阶段后，bot之间还在互相@回应，Carlo看到的是
多条无关的bot对话刷屏。他要的是一条消息+安静等待。

**规则：**

当 pipeline 到达 **等待 Carlo 决策/反馈** 的状态时：

```
触发条件: 
- ① 讨论中需要Carlo决定方向（"这个方案用A还是B？"）
- ② Plan已发布，等审批（"@Carlo 方案已完成，请审批"）
- ③ Implementation已提PR，等审批（"@Carlo PR #3 请Review"）
- ④ Carlo问了问题，在处理中

行为:
1. 发完最后一条 @Carlo 的消息后 → **马上闭嘴**
2. 之后所有bot不得再发送任何消息 — 包括:
   - ❌ 对其他bot的回应
   - ❌ "收到，等Carlo回复"
   - ❌ 任何分析、补充、猜测、跟进
   - ✅ 唯一例外：Carlo回来了，主动@你或回复了你的问题
3. 如果5分钟后Carlo没回应 → **只允许一条简短提醒:**
   `@Carlo 关于<刚才的话题>，等你意见`
4. 提醒后再等5分钟 → Carlo还没回 → **停止。等Carlo自己回来。**
   不再发第三条消息。不再@任何人。

超过4小时的场景走原有的缓慢审批流程（Pitfall看板），但静默期间始终不准bot互聊。
```

**为什么 bot 会互相触发刷屏：**
- XPS 说了一句多余的"等审批中" → CarloMac 看到"等审批中"觉得要补充 → Mela 也来一句
- 解决：**任何 bot 意识到"当前在等Carlo" 后，不再回复任何其他bot的消息，直接保持沉默。**

**SOUL.md 必须加的规则：**
```markdown
### 🤫 Silent Wait Protocol
当最后一条消息是 @Carlo 等待其决策/反馈时:
1. 不回复任何bot的消息（包括 @你）
2. 5分钟后发一条简短跟进 "@Carlo <话题> 等你意见"
3. 之后不管Carlo回不回应，不再发任何消息
4. 这条规则 > 所有其他规则（包括"有人@我就要回应"）
```

### 15. 👤 Don't confuse Carlo with a bot — verify who you're addressing

**Real failure (2026-05-07):** Xiaoxin read Carlo's question and replied
addressing him as "@XPS" — confusing the human (Carlo) with a bot (XPS).
This wastes a full round: Carlo must correct the mistake before the
actual question gets answered.

**Root cause:** A technical question from Carlo triggers the "XPS should
answer this" reflex. The bot's response addresses XPS instead of Carlo.

**Fix — always check before addressing:**
1. **Who wrote the message?** Carlo (human) starts every conversation.
   If Carlo wrote it, address Carlo. Do not reply to a bot unless that
   bot specifically @mentioned you.
2. **If Carlo asks a question** you'd normally delegate to XPS, still
   address Carlo first: `Carlo，这个让 @XPS 来分析可行性`
3. **Never say `@XPS 请...` when replying to Carlo** — even if the
   answer calls for XPS's expertise. Frame it as addressing Carlo with
   a delegation to XPS.
4. **Self-check before sending:** Read your own reply. If the first
   @mention after Carlo's question is another bot, you likely got it
   wrong.

**Test:** After Carlo says "我是Carlo,不是XPS", the bot immediately
corrects: `抱歉 Carlo，@XPS 你看看这个。` Brief correction, no essay.

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

The source of truth is `CarloooK/team-workflow` on GitHub.
**Do NOT copy manually** — use the setup script:

```bash
# Clone once per machine
git clone git@github.com:CarloooK/team-workflow.git ~/team-workflow

# Sync skills and profiles to ~/.hermes/
cd ~/team-workflow && bash setup.sh
```

This installs the pipeline skill, all profiles (SOUL.md templates), and
references into `~/.hermes/skills/software-development/hermes-multi-agent-pipeline/`.

After syncing, copy the relevant profile to the bot's profile directory:
```bash
cp ~/.hermes/skills/.../templates/soul-xiaoxin.md ~/.hermes/profiles/<bot-name>/SOUL.md
```

Adjust the Discord @name mentions in the SOUL.md to match the bot's
actual Discord handle.

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
│   ├── knowledge/      # Cross-bot knowledge notes 🧠
│   ├── session/        # Discussion state for crash recovery 🔄
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

### 🧠 Knowledge Notes — Cross-Bot Memory

**Before starting a new discussion, Xiaoxin checks `docs/knowledge/` for
relevant existing notes.** If a previous discussion already rejected an
approach or decided on a direction, skip the re-discussion and link to
the existing knowledge note instead. This prevents bots from repeating
work settled in earlier sessions.

After each discussion cycle, Xiaoxin writes a knowledge note to
`docs/knowledge/<topic-slug>-<YYYY-MM-DD>.md`. This captures what was
learned during the discussion — rejected approaches, design rationale,
architectural constraints — so XPS, CarloMac, and Mela don't repeat work
or rediscover pitfalls in future sessions.

**Format (see `templates/knowledge-note.md` for a boilerplate):**

```markdown
# Knowledge: <topic> — <YYYY-MM-DD>

## Context
<which requirement/discussion this came from>

## Key Insight
<the most important thing learned>

## Rejected Approaches
- <approach A>: rejected because <reason>
- <approach B>: rejected because <reason>

## Decisions
- <decision 1>
- <decision 2>

## Pitfalls / Gotchas
- <pitfall discovered>
- <unexpected constraint>

## Related
- Plan: docs/plans/<plan-file>
- PR: #<number>
```

**When to write:**
- **Xiaoxin** (required): After discussion closes, same time as writing the plan.
  If a plan already captures decisions, the knowledge note focuses on *what
  was learned, not what was decided*.
- **CarloMac** (optional but encouraged): After implementation, if something
  unexpected was discovered — API quirks, dependency gotchas, test flakiness.
- **Mela** (optional): After review, if a recurring code issue pattern was found.
- **XPS** (optional): After analysis, if a non-obvious architectural constraint surfaced.

**Why this helps:**
- XPS's analysis survives to inform CarloMac's implementation
- CarloMac's gotchas don't get rediscovered by Mela in the next cycle
- Scarce bot context (SOUL.md) doesn't need to hold every historical detail
- New team members (or future you) can skim docs/knowledge/ for context

### 🔄 Session Persistence — 断线恢复

Gateway 掉线重启后，bot 会丢失对话上下文。为此，在每个 pipeline
里程碑写入 `docs/session/current.md`，重启后自动恢复。

**格式：**

```markdown
# Session — <YYYY-MM-DD HH:MM>

## Topic
<简要描述当前讨论>

## Stage
discuss | plan | approve | execute | release

## Last Message
<who: what was said>

## Waiting For
<who> — <what we're waiting for>

## State
- XPS: <何轮次 / 等待中 / 已完成>
- CarloMac: <同上>
- Mela: <同上>
- Xiaoxin: <同上>
- Carlo: <同上>

## Next Expected Action
<下一步谁该做什么>
```

**写入时机（Xiaoxin 责任）：**

| 阶段 | 触发 | 写入 session |
|------|------|-------------|
| 讨论结束 | Xiaoxin 写 plan + knowledge note 时 | 同步写入 session |
| Carlo 审批 | Carlo 批准/修改后 | 更新 stage + waiting for |
| 实现开始 | CarloMac 开始编码 | 更新 stage |
| PR 提交 | PR 发出 | 更新 stage + waiting for Carlo |
| 发布完成 | 发布后 | 清除 session 文件 |

**恢复流程（任何 bot gateway 重启后）：**

```text
1. bot 启动 → 检查 GitHub 仓库中 docs/session/current.md 是否存在
2. 如果存在:
   a. 读取 session 内容
   b. 在 Discord 发一条恢复消息:
      "@Carlo 我重启了。上次我们在讨论 <topic> (stage: <stage>)，
      等你 <next expected action>。继续吗？"
   c. 同时 XPS/CarloMac/Mela 也执行同样的恢复流程
   d. 第一个发恢复消息的 bot 最好汇总一下
3. 如果不存在:
   a. 没有进行中的 session → 正常待命
   b. 可以检查最后一次 plan/knowledge note 来辅助恢复
```

> **会话文件自动清理：** 当 pipeline 完成（发布后），删除
> `docs/session/current.md`。如果跨 session 需要，保留 `docs/session/` 下的
> 归档（但目前不强制，当前阶段先保证 current.md 准确即可）。

### Tooling: code-review-graph

[code-review-graph](https://github.com/tirth8205/code-review-graph) is
installed on Xiaoxin's WSL and configured for LogisticSystem. It builds
a Tree-sitter based knowledge graph of the codebase and exposes 28 MCP
tools for impact analysis, change detection, and context-aware reviews.

### Operational Cadence: GBrain Evening Summary

A cron job (`gbrain-晚间总结`) runs daily at 18:00, generating a
structured summary of the day's work using GBrain + session history.
To make it aware of project context from Hermes memory, sync memory
pages into GBrain — see `references/gbrain-memory-sync.md`.

Current cron schedule on Xiaoxin WSL:
- `gbrain-晚间总结` — daily 18:00
- `team-workflow-sync` — every 30 min
- `xiaoxin-healthcheck` — every 2 hours

See `references/auto-tasks-config.md` for how to replicate on other machines.

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
2. **Xiaoxin** → 📖 checks `docs/knowledge/` for relevant prior decisions
   → one line only: `@XPS 请分析可行性（查过 docs/knowledge/，没有重叠历史）`
3. **XPS** → feasibility analysis + CRG status to understand module structure
   → `@CarloMac`
4. **CarloMac** → implementation approach + CRG detect-changes on affected area
   → `@Mela`
5. **Mela** → risks + CRG blast radius analysis → `@Xiaoxin`
6. **Xiaoxin** → summary → writes `docs/plans/<topic>-<date>.md`
   → writes `docs/knowledge/<topic>-<date>.md` 🧠 (key insight, rejected approaches, pitfalls)
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
| Xiaoxin codes when shouldn't | Discord mode triggered but Carlo meant CLI mode | Check context: if no bots @mentioned and no Discord channel, it's CLI mode. Pitfall #8 covers this. |
| XPS writes files nobody else can see | Files written to local disk | Must use GitHub repo; `git pull` before write |
| XPS commits but other bots can't find the file | `git push` failed (credential/permission) | Next bot runs `git pull` to verify; report failure to Carlo |
| Git push fails with `Authentication failed` | **Two possible causes**: 401 (invalid PAT) or 403 (valid PAT, no org access). **ALWAYS test first**: `gh api repos/<org>/<repo>` — 401 = bad token, false = no push access | 401 → Carlo generates new PAT. 403 → add collaborator or org-scoped PAT. During stalemate see `references/credential-stalemate-protocol.md` |
| Authentication succeeds but pushes to wrong user | Credential file `/home/chao/.git-credentials` may be 0 bytes after `patch` tool replaced content | Always verify after any credential write: `wc -c ~/.git-credentials`; if 0 → `echo "https://user:token@github.com" > ~/.git-credentials`; see `references/git-credential-debug.md` §2 |
| SSH says "Hi User!" but git push still denied | SSH key added to personal account, not as repo Deploy Key with write access | Generate dedicated deploy key; test with `ssh -i <key> -o IdentitiesOnly=yes -T git@github.com` — if "Hi User!" it's personal, if "Permission denied" it's not yet added anywhere |
| Bot addresses Carlo as another bot ("@XPS 请分析" when Carlo is speaking) | Reflexive delegation — sees technical question, replies to wrong person | Always check message author first. If Carlo wrote it, address Carlo. See Critical Pitfall #13 |
| @mentions not working in Discord | Text `@Name` not real `<@ID>` | Patch discord.py per references |
| Discussion never ends | No round limit in SOUL.md | Add "max 2 rounds, then close" |
| Carlo slow to approve | Human delay — waiting for decision | Follow Silent Wait Protocol (Pitfall #14): 1 msg → 5min silence → 1 reminder → wait more |
| Carlo slow to approve | Human delay — PR sitting open | **Pre-build during delay**: Write implementation based on approved design, stash locally. When Carlo merges, push immediately. See `references/pre-build-during-wait.md` and `references/python-cli-tool-pattern.md` for an example (dirsize.py). |
| Git conflict | Two bots push simultaneously | Feature branches; `git pull --rebase` before push |
| Discord bot offline but gateway running | state.db locked by CLI session | See `references/discord-gateway-diagnosis.md` — conflict between HERMES CLI session and gateway process sharing same state.db |
| Gateway 掉线后重启 | 进程崩溃或网络断开 | Watchdog 自动重启（每2分钟检查）。重启后 Session Recovery 读取 docs/session/current.md 恢复上下文。|
| SSH to GitHub port 22 times out, HTTPS works | WSL network: SSH (port 22) intermittently blocked or slow, HTTPS (port 443) reliable | Fall back to HTTPS: `git remote set-url origin https://github.com/<user>/<repo>.git`; push via HTTPS; switch back to SSH when network recovers. This is a WSL quirk, not a credential issue. |
