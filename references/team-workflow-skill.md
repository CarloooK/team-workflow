---
name: team-workflow-sync
description: "Multi-machine workflow sync via CarloooK/team-workflow repo. New machine setup, sync protocol, cron job configuration, and bot collaboration rules for the 4-bot pipeline."
version: 1.0.0
author: Carlo
---

# Team Workflow Sync

Central workflow repository for the 4-bot development pipeline.
All machines (Xiaoxin/WSL, XPS/Dell, CarloMac/MacMini, Mela/Cloud) share
the same pipeline skill, profiles, and references through this repo.

## Source Repository

```
https://github.com/CarloooK/team-workflow
```

## Repo Structure

```
team-workflow/
├── pipeline/
│   ├── SKILL.md          ← Pipeline skill (source of truth)
│   └── sync-guide.md     ← Cross-machine sync instructions
├── profiles/
│   ├── soul-xiaoxin.md
│   ├── soul-xps.md
│   ├── soul-carlomac.md
│   └── soul-mela.md      ← SOUL.md templates for each bot
├── references/
│   ├── crg-integration.md
│   ├── discord-mention-fix.md
│   ├── credential-stalemate-protocol.md
│   ├── git-credential-debug.md
│   ├── discord-gateway-diagnosis.md
│   ├── python-cli-tool-pattern.md
│   └── project-status-audit.md
├── setup.sh               ← One-command sync to local ~/.hermes/
└── README.md
```

## New Machine Setup

```bash
# 1. Clone
git clone git@github.com:CarloooK/team-workflow.git ~/team-workflow

# 2. Sync to local Hermes
cd ~/team-workflow && bash setup.sh

# 3. Verify
ls ~/.hermes/skills/software-development/hermes-multi-agent-pipeline/
```

The `setup.sh` script copies:
- `pipeline/SKILL.md` → `~/.hermes/skills/software-development/hermes-multi-agent-pipeline/SKILL.md`
- `profiles/*.md` → `templates/` subdirectory
- `references/*.md` → `references/` subdirectory

## Daily Sync (When Workflow Updates)

```bash
cd ~/team-workflow && git pull && bash setup.sh
```

## Automatic Sync (Cron Job)

A cron job runs every 30 minutes on Xiaoxin's WSL. It checks:

| State | Action |
|-------|--------|
| Remote has new commits | Auto `git pull` + `setup.sh` + notify Carlo |
| Local has uncommitted changes | Report diff to Carlo for approval |
| Everything in sync | Silence (no noise) |

### Script Location

`~/.hermes/scripts/team-workflow-sync.py`

### Cron Setup

```bash
# Already configured. View with:
cronjob action=list
```

## Sync Protocol (All Bots Must Follow)

After modifying the pipeline skill or any team-workflow file:

```bash
# 1. Sync local skill changes to repo
cp ~/.hermes/skills/software-development/hermes-multi-agent-pipeline/SKILL.md ~/team-workflow/pipeline/
cd ~/team-workflow && git add -A && git commit -m "update: <describe changes>"
```

**Do NOT push directly** — Carlo must approve first (human-in-the-loop).

### Approval Flow

1. Bot: `@Carlo 流程有更新，请审批推送：cd ~/projects/team-workflow && git push`
2. Carlo: says "commit" / "推" / "好" / "批准"
3. Bot: `cd ~/projects/team-workflow && git push`
4. Other machines auto-pull within next 30 min cron cycle

### Emergency Exceptions

Direct push allowed when:
- CI pipeline is broken
- Workflow is blocking progress
- Must be communicated in Discord: 「紧急修复，已直接推送」

## Key Principles

- **Human-in-the-loop**: Carlo approves all non-emergency workflow changes
- **Version-controlled**: All changes are tracked via git
- **Silent when stable**: Cron only reports when something changes
- **Distributed**: Each bot has its own local clone, sync is opt-in via setup.sh
- **Recovery**: If a machine falls behind, `cd ~/team-workflow && git pull && bash setup.sh` catches it up
