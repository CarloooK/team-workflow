# Credential Stalemate Protocol

When a bot has files committed locally but `git push` fails (401/403/permission
denied), and coordinator Xiaoxin on a different machine also cannot push,
you have a **tri-party stalemate**:

| Party | Has | Missing |
|-------|-----|---------|
| XPS (Dell PC) | Files committed | Push capability (PAT lacks org repo access) |
| Xiaoxin (WSL) | Git repo clone | Files + push capability |
| Carlo (human) | GitHub auth authority | Time to act on it |

## Protocol

### 1. Recognize the stalemate immediately

After confirming that **all testable machines** lack push access to the
target org repo (`gh api repos/<org>/<repo> --jq '.permissions.push'` →
`false` on every machine), stop trying to fix credentials programmatically.

**But first, test if the new PAT is even valid:**

Before assuming the stalemate is about permissions, check the HTTP status:
```bash
GITHUB_TOKEN=<new-PAT> gh api repos/outsourc-e/hermes-workspace --jq '.permissions.push' 2>&1
```
- **401 "Bad credentials"** → PAT itself is invalid (expired, never activated, or mistyped). This is NOT a stalemate — it's a bad token. Tell Carlo to generate a new one.
- **`false`** → PAT is valid but user lacks push access. This IS a stalemate — proceed with the protocol.
- **`true`** → PAT works! No stalemate — just update credentials and push.

> **Pitfall:** Both 401 and 403 produce `fatal: Authentication failed` in git.
Do NOT assume "Authentication failed" means the same thing each time.
Always test the token via `gh api` or `curl -w "%{http_code}"` before
proceeding.

**Pitfall: "加了" not actually taking effect.** When Carlo says "加了" but
the deploy key still can't authenticate, verify with a concrete probe:
```bash
ssh -i ~/.ssh/<specific-key> -o IdentitiesOnly=yes -T git@github.com
```
- "Hi CarloooK!" → key added to **personal account**, not as Deploy Key
- "Permission denied" → key not added anywhere
Report the ACTUAL probe result back, not just "it not working". The probe
distinguishes "wrong place" from "not added".

### 2. Switch to productive standby

While waiting for Carlo, the coordinator (Xiaoxin) has three productive
options:

| Option | When to use | What to do |
|--------|-------------|------------|
| **Recreate locally** | XPS has files on a different machine | Xiaoxin recreates the files from conversation content on the local repo, ready to push when credentials arrive |
| **Pre-write dependent artifacts** | Files exist locally but can't push | Write the next step artifacts (meeting notes, milestones) so push delivers maximum value |
| **Audit credential setup** | Multiple machines affected | Document which machines have which tokens and which org repos they can access — useful for Carlo's fix |

### 3. Recreate locally — detailed steps

When XPS on Dell PC has created `docs/requirements/` and `docs/design/`
files but can't push:

```bash
cd ~/hermes-workspace

# Recreate files from the conversation discussion content
cat > docs/requirements/dirsize-tool.md << 'EOF'
# ... content from Discord conversation ...
EOF

cat > docs/design/dirsize-tool.md << 'EOF'
# ... content from Discord conversation ...
EOF

git add docs/requirements/ docs/design/
git commit -m "docs: <topic> — requirements and design (recreated locally)"

# Do NOT push — wait for credentials
```

> **Why recreate instead of waiting for file transfer?**
> - No shared filesystem between Dell PC and WSL
> - No common cloud storage configured
> - Initiating file transfer (scp, rsync) requires IP + SSH access, which
>   isn't guaranteed between machines
> - Recreating from conversation is faster and more reliable

### 4. What to include in the final Carlo message

When credentials arrive, include in the push + notification:

```
凭证已收到 →
1. 写入 credentials
2. git push (所有待推送 commit)
3. `@Carlo 文档已就绪：<URL> 请审阅`
```

If the recreated files differ from XPS's originals, note:
```
⚠️ 文件是在本机从讨论内容重建的，与 XPS 原始版本可能有细节差异。
@XPS 请核对 docs/requirements/ 和 docs/design/ 准确性
```

### 5. Handle multiple successive 401 tokens

If Carlo sends 2+ PATs that all return 401:

```
Round 1: PAT-1 → 401 → "Carlo, token invalid, please regenerate"
Round 2: PAT-2 → 401 → "Carlo, also 401, please check you're clicking Generate"
Round 3: → Escalate to alternative approach
```

**At round 3, stop the PAT loop. Switch strategy:**
- "连续两个 PAT 都是 401，不是输入问题，是 token 生成流程有问题。建议换方案：选项 B（加 collaborator）最直接，或者告诉我愿意用哪种方式"

**Rationale:** 401 means the token was never properly activated/committed on GitHub's side, not a permissions issue. Continuing to ask for more PATs wastes rounds. The root cause is likely:
1. User closes the page before clicking "Generate token"
2. User doesn't have admin permissions to create tokens for this org
3. SSO/SAML is blocking without proper authorization

### 6. Fork + PR workaround (when all else fails)

If after exhausting PATs, collaborator invites, and SSH deploy keys the
stalemate persists, use the **fork + PR** approach. This is the confirmed
working setup on Xiaoxin's WSL machine (verified 2026-05-06):

**Current remote configuration (verified working):**
```bash
$ git remote -v
origin  git@github.com-outsourc-e:outsourc-e/hermes-workspace.git  (fetch/push)  # READ-ONLY
fork    git@github.com:CarloooK/hermes-workspace.git              (fetch/push)  # WRITABLE
```

**Daily workflow with fork:**
```bash
cd ~/hermes-workspace
git pull origin main                    # pull latest from upstream (org repo)
# ... write files, commit ...
git push fork HEAD                      # push to personal fork

# Then create PR from fork → upstream:
gh pr create \
  --repo outsourc-e/hermes-workspace \
  --head CarloooK:main \
  --base main \
  --title "docs: ..." \
  --body "## Description"
```

**Verify permissions before assuming stalemate:**
```bash
gh api repos/<org>/<repo> --jq '.permissions.push'
# false → stalemate (use fork workaround)
# true  → no stalemate (fix credentials and push directly)
# 401   → bad PAT, ask Carlo for new one
```

**To set up fork from scratch:**
```bash
# Step 1: Fork the org repo to user account
curl -s -X POST \
  -H "Authorization: Bearer <PAT>" \
  "https://api.github.com/repos/<org>/<repo>/forks"
# Returns: Fork: <user>/<repo>

# Step 2: Add fork as remote
git remote add fork git@github.com:<user>/<repo>.git

# Step 3: If main branch has diverged, create feature branch
git checkout -b feat/<topic>
git push fork HEAD
```

**Pros:**
- Works without any collaborator/deploy key/permission changes
- Uses standard GitHub review workflow
- Creates a clean PR the org owner can review and merge

**Cons:**
- Only works if the upstream repo allows PRs from forks
- The PAT user needs `public_repo` scope (or fork is private)
- Merging still requires the org owner to click "Merge" on the PR page

**When to use:**
- After both PAT collaborator and SSH deploy key approaches have failed
- Fork works when Content API returns 404
- Fork preserves git history and proper PR workflow

### 7. PR merge button: "Close" vs "Merge" confusion

When the org owner says "合并了" but the PR status still shows
`state: open, merged: false`, check if they clicked the wrong button:

| Button | Color | Action | Result |
|--------|-------|--------|--------|
| **Merge pull request** | 🟢 Green | Merges code into base branch | PR shows "Merged" |
| **Close pull request** | ⚫ Grey text link (bottom right) | Closes without merging | PR shows "Closed", merged: false |

**How to distinguish via API:**
```bash
gh pr view <number> --repo <org>/<repo> --json state,merged
# Closed, merged=false → clicked "Close" instead of "Merge"
# Open, merged=false → button never clicked
# Closed, merged=true → actually merged
```

**If accidentally closed:** Reopen via API first, then guide to the green
button:
```bash
curl -s -X PATCH \
  -H "Authorization: Bearer <PAT>" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/<org>/<repo>/pulls/<number>" \
  -d '{"state":"open"}'
```

Then tell Carlo: "请找页面中间 **绿色 'Merge pull request'** 按钮，不要点灰色的 'Close pull request' 链接。"

> **Why this happens:** On GitHub's PR page, the green "Merge pull request"
> button is the prominent action, but there's also a smaller grey "Close
> pull request" link at the bottom right. A quick tap on mobile or a
> misclick can hit "Close" instead of "Merge". The fix is reopening +
> clear visual instructions.

### 8. Prevent recurrence

After stalemate is resolved, suggest to Carlo:

- Either add `CarloooK` as collaborator on the org repo (one-time fix)
- Or configure SSH key (more stable long-term)
- Or set a shared org-level PAT that all bots can use

### 9. Transitioning from PAT to SSH during stalemate

If PAT keeps failing (multiple 401 or 403), switching to SSH mid-stalemate
is valid but has its own pitfalls:

**Check 1: Did Carlo add the key to the right place?**
- `ssh -T git@github.com` → "Hi <user>!" → key added to user account, but user may lack org repo access
- `ssh -T git@github.com` → "Permission denied" → key not added anywhere yet

**Check 2: Personal key vs Deploy key conflict (see `references/git-credential-debug.md` for full detail)**
If the same key is registered as both a personal user key AND a repo deploy
key, GitHub authenticates as the user (with user-level permissions),
ignoring the deploy key's write access. Generate a dedicated deploy key.

**Check 3: Credential file may be empty after PAT→SSH transition**
After multiple PAT writes (each replacing the old one), the credential file
can end up 0 bytes. If the user goes back to HTTPS later, this will fail
silently. Verify credential file integrity after any credential operation:
```bash
wc -c ~/.git-credentials
# If 0 → rewrite with a known-good PAT
echo "https://<user>:<token>@github.com" > ~/.git-credentials
```
