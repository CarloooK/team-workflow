# Git Credential Debugging Workflow

When a bot reports "git push failed" or files can't be found on GitHub,
use this systematic workflow to diagnose and resolve.

## Diagnostic Steps (in order)

### 1. Check git config for credential helpers

```bash
git config --list | grep credential
```

Typical output on this setup:
```
credential.helper=store
credential.https://github.com.helper=
credential.https://github.com.helper=!/home/chao/.local/bin/gh auth git-credential
```

> **Gotcha:** An empty `credential.https://github.com.helper=` (second line)
> can override the `store` helper for GitHub. The `gh auth git-credential`
> line (third) should restore it, but config order matters.

#### Fix: Empty helper override

If you see `credential.https://github.com.helper=` (empty value), the `store`
helper is being overridden for GitHub. Fix in `~/.gitconfig`:

```bash
# Change the empty helper to 'store' so the credential file is checked first
git config --file ~/.gitconfig credential.https://github.com.helper store

# Or edit manually — find the section:
# [credential "https://github.com"]
#   helper = store          # ← was empty, now fixed
#   helper = !/home/chao/.local/bin/gh auth git-credential
```

**Why it breaks:** Git reads helpers in order. An empty `helper =` tells git
"don't use any default helpers for this URL pattern." The next non-empty
helper line re-adds one, but by that time git has already decided not to
fall back to the global `store` helper. The fix ensures `store` is tried
before the `gh` git-credential helper.

### 2. Read the stored credential file

```bash
cat ~/.git-credentials
```

Format: `https://<username>:<PAT>@github.com`

**Critical: always check file size after any write operation:**

When using `patch` or `write_file` to update `~/.git-credentials`, the file
can end up as 0 bytes — completely empty. This happens silently and causes
all credential lookups to fail:

```bash
# After writing/changing credentials, always verify:
wc -c ~/.git-credentials
# Should show non-zero (e.g. 69 bytes for a typical PAT entry)
# If 0 → the file is empty — no credentials will be found

# Recover from empty credential file:
echo "https://<username>:<token>@github.com" > ~/.git-credentials
```

**Why it happens:** The `patch` tool replaces a line in-place. If the old
and new content don't match in a way that causes the file to truncate,
the credential file becomes empty. Always verify file size after patching
the credential store.

### 2b. Debug credential store lookup (when store seems broken)

If `cat ~/.git-credentials` shows content but git still prompts for
credentials, test the store directly:

```bash
# Test basic credential lookup
echo -e "protocol=https\nhost=github.com\n" | git credential-store get
# Expected output: username=... password=... (the stored PAT)

# If empty output even though file has content:
# → File format might be wrong, or file is truly empty
# → Check with hexdump:
cat ~/.git-credentials | xxd | head -3
# → Should show the URL in hex; if empty after xxd, file is 0 bytes

# Test with path (required for org repos)
echo -e "protocol=https\nhost=github.com\npath=outsourc-e/hermes-workspace\n" | git credential-store get
```

If `git credential-store get` returns empty:
1. Check `wc -c ~/.git-credentials` — file might be 0 bytes
2. Check file format — must be one URL per line, no trailing whitespace
3. Try with `username=<name>` as well — some queries need exact match

### 3. Check GitHub CLI auth status

```bash
gh auth status
```

Shows: logged-in user, protocol (https/ssh), token status.

### 4. Test actual push (dry run first, then real)

```bash
# Dry run — may fail at auth prompt; add env to suppress prompt
GIT_TERMINAL_PROMPT=0 git push --dry-run 2>&1

# Enable trace logging to see which credential helper is invoked
GIT_TRACE=1 GIT_TERMINAL_PROMPT=0 git push --dry-run 2>&1 | grep -i credential
```

> **Expected trace output:**
> If using `gh auth`: `run_command: '/home/chao/.local/bin/gh auth git-credential get'`
> If using `store`: should read from `~/.git-credentials`

### 5. List repos the current token has push access to

```bash
gh repo list --limit 20 --json nameWithOwner,isPrivate
```

Or via API:
```bash
gh api user/repos --jq '.[].full_name'
```

> **Check:** Does `outsourc-e/hermes-workspace` appear in the list? If not,
> the token user (e.g. `CarloooK`) is not a collaborator on that org repo.

### 6. Check specific repo push permission via API

```bash
gh api repos/<org>/<repo> --jq '.permissions.push'
```

Returns `true` or `false`. This is the definitive answer for 403 cases.

### 7. Distinguish 401 vs 403

Both produce "Authentication failed" or "Invalid username or token" errors,
but the root cause and fix are different:

| HTTP Status | Meaning | Root cause | Fix |
|-------------|---------|------------|-----|
| **401** | Bad Credentials | PAT itself is invalid — never activated, expired, or mistyped | Carlo generates a NEW PAT and shares it |
| **403** | Permission denied | PAT is valid but user lacks push access to the org repo | Add user as collaborator or get org-scoped PAT |

**How to tell the difference:**

```bash
# Test the raw token against any endpoint — if 401, token is dead
GITHUB_TOKEN=<suspected-token> gh api repos/outsourc-e/hermes-workspace --jq '.permissions.push' 2>&1
# 401 → "Bad credentials" — token itself is invalid
# false → token works but no push permission (403-style)
```

Also check via API:
```bash
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token <TOKEN>" \
  https://api.github.com/repos/outsourc-e/hermes-workspace
# 401 = invalid token
# 200 = valid token (check .permissions.push in body for 403 insight)
```

**Action:**
- **401** → Don't bother updating credentials, don't try to push again. Tell Carlo the PAT returned 401 and ask for a fresh one.
- **403/false** → Tell Carlo the PAT is valid but needs push access — Option A (new org-scoped PAT) or Option B (add collaborator).

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `could not read Username` | Credential helper can't auth non-interactively | Fix empty `helper =` override in `~/.gitconfig` |
| `fatal: Authentication failed` / `Invalid token` (401) | PAT is invalid or expired | Carlo generates new PAT |
| `remote: Permission to X denied` (403) | Token lacks org repo access | Add collaborator or get org-scoped PAT |
| Push succeeds but file not visible to others | Pushed to local branch not on remote | Check `git branch -a` for detached HEAD |
| `gh auth login` works but `git push` fails | gh helper not configured for git | `gh auth setup-git` |

## Resolution Options

### Option A: Share a valid PAT

Carlo provides a PAT with `repo` scope for the target org repo:

```bash
# Update credential file
echo "https://Carlo:NEW_PAT@github.com" > ~/.git-credentials

# Verify
gh auth login --with-token < ~/.git-credentials 2>/dev/null || true
gh api repos/outsourc-e/hermes-workspace --jq '.permissions.push'
```

> **IMPORTANT:** After receiving a new PAT, ALWAYS verify it with `gh api`
> BEFORE attempting push. If the API returns 401, pushing will also fail
> and waste time. Test the token first.

### Option B: Add user as collaborator

Carlo goes to GitHub → Repo Settings → Collaborators → Add `CarloooK`
with Write or Maintain access.

### Option C: SSH key

```bash
# Generate key
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```
→ Carlo adds the pubkey to GitHub → Settings → SSH and GPG keys.
→ Update remote:
```bash
git remote set-url origin git@github.com:outsourc-e/hermes-workspace.git
```

**⚠️ Known pitfall: Personal key vs Deploy Key conflict**

If `ssh -T git@github.com` succeeds (showing "Hi <user>!") but `git push`
still fails with "Permission denied to <org>/<repo>", the SSH key may be
caught in a **personal vs deploy key conflict**:

When the same SSH key is registered on BOTH the user's personal GitHub
account AND as a repo deploy key, GitHub authenticates as the **user**
(first priority), NOT as the deploy key. The deploy key's write access is
never used.

**Fix:** Generate a **separate key** for the deploy key that is NOT on any
personal account:

```bash
ssh-keygen -t ed25519 -C "hermes-deploy-<agent>" -f ~/.ssh/hermes_deploy -N ""
# → Give THIS key to Carlo for the Deploy Key, not the personal account key
```

**Detection in SSH verbose output:**
```bash
ssh -vT git@github.com 2>&1 | grep "Offering public key"
# Shows which key was offered to GitHub
# If it's a key you know is also in GitHub Settings → SSH keys → conflict!
```

Also set up SSH config with a host alias to force the deploy key:
```bash
cat >> ~/.ssh/config << 'EOF'
Host github.com-deploy
    HostName github.com
    User git
    IdentityFile ~/.ssh/hermes_deploy
    IdentitiesOnly yes
EOF
git remote set-url origin git@github.com-deploy:<org>/<repo>.git
```

## Fallback: GitHub Content API (bypass git push)

When ALL git push methods fail (PAT 401/403, SSH blocked, no collaborator),
the GitHub Content API can create/update files directly via HTTP without
`git push`. This requires the PAT to have `repo` scope and at least
read-level access to the repo.

### Check if Content API is available

```python
import json, base64, urllib.request

token = "ghp_..."
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json",
           "Accept": "application/vnd.github.v3+json"}

# Test: can we read the repo's ref?
req = urllib.request.Request(
    f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/main",
    headers=headers)
try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    sha = data['object']['sha']
    print(f"Ref readable: {sha}")  # API has read access
except urllib.error.HTTPError as e:
    print(f"Status {e.code}: Content API not available")
```

### Create a file via Content API

```python
# Read file content
with open('local_file.md', 'rb') as f:
    content = f.read()

payload = json.dumps({
    "message": "docs: add document",
    "content": base64.b64encode(content).decode(),
    "branch": "main"
}).encode()

req = urllib.request.Request(
    f"https://api.github.com/repos/{owner}/{repo}/contents/docs/target.md",
    data=payload, headers=headers, method='PUT')
try:
    resp = urllib.request.urlopen(req)
    print(f"Created! Status: {resp.status}")
except urllib.error.HTTPError as e:
    body = e.read().decode()[:200]
    print(f"FAILED: HTTP {e.code} — {body}")
```

### Limitations

| Limitation | Impact |
|------------|--------|
| No batch operations | Must create each file one-by-one via separate API calls |
| No git history merge | Files appear as individual commits; no PR workflow |
| 100MB file size limit | Can't push large assets |
| Only works if PAT has `repo` scope | Without it, Content API returns 404 |
| Cannot delete branches or merge PRs | Requires `public_repo` or `repo` scope + write access |

### When to use

- **Best**: Single file additions (docs, configs) when git push is blocked
- **Avoid**: Code changes that should go through PR review
- **Warning**: Creates commits under the PAT owner's name, not a branch — use only as a temporary workaround during credential stalemate

## Verification

After fixing, validate end-to-end:

```bash
echo "test-$(date +%s)" > /tmp/push-test.txt
git add /tmp/push-test.txt
git commit -m "test: verify push works"
git push
# Should succeed. Clean up:
git reset --soft HEAD~1
git push --force  # only if on feature branch
```
