# Discord @mention Resolution Fix

## Problem

When Hermes responds in Discord with text like `@XPS 请分析可行性`,
the `@XPS` is plain text — not a real Discord mention (`<@USER_ID>`).

Since all bots use `DISCORD_ALLOW_BOTS=mentions`, the @mentioned bot
never receives the message because `message.mentions` is empty.

## Detect the problem

In the Discord UI:
- **Working**: `@XPS` shows in blue, clickable, hover shows user card
- **Broken**: `@XPS` shows in black, not clickable, just plain text

## Fix: Patch discord.py

Edit `~/.hermes/hermes-agent/gateway/platforms/discord.py`

### 1. In `send_message()` method (~line 1134)

After `formatted = self.format_message(content)`, add:

```python
# Resolve plain-text @mentions to proper Discord mentions
try:
    guild = getattr(channel, "guild", None)
    if guild:
        formatted = self._resolve_text_mentions(formatted, guild)
except Exception:
    logger.debug("[%s] Failed to resolve text mentions (non-critical)", self.name)
```

### 2. Add the resolver method (after `format_message()`, ~line 2525)

```python
def _resolve_text_mentions(self, text: str, guild) -> str:
    """
    Convert plain-text @mentions (e.g. "@XPS") to proper Discord
    mention syntax (<@USER_ID>) so they actually trigger mentions
    and appear in message.mentions.
    """
    import re

    def _replace_mention(match):
        name = match.group(1)
        member = discord.utils.get(guild.members, name=name)
        if member:
            return member.mention
        member = discord.utils.get(guild.members, display_name=name)
        if member:
            return member.mention
        return match.group(0)

    return re.sub(r'(?<!\w)@(\w[\w.-]*)', _replace_mention, text)
```

### 3. Restart gateway

```bash
tmux send-keys -t gateway C-c
sleep 3
tmux send-keys -t gateway 'hermes gateway run --replace 2>&1' Enter
sleep 8
grep "Connected as" ~/.hermes/logs/gateway.log | tail -3
```

## Verify

Send a test message. The @mentioned name should appear in **blue**,
clickable, showing a user card on hover.

## Notes

- Only works in guild channels (not DMs — no guild member list)
- Regex `(?<!\w)@(\w[\w.-]*)` matches `@Username`, `@user-name`, `@user.name`
- Does NOT match `@everyone`, `@here`, or email addresses
- Unknown names are left unchanged (safe fallback)
