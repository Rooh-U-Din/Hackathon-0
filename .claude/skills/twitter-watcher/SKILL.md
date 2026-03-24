# Twitter (X) Watcher Agent Skill

## Overview

The Twitter Watcher monitors your Twitter/X account for mentions, notifications, and direct messages. It uses Playwright browser automation to access Twitter and creates markdown files in your vault's Inbox for processing.

## Features

- **Mention Monitoring**: Tracks when others mention your account
- **Notification Tracking**: Captures likes, retweets, follows, and replies
- **Persistent Session**: Maintains login across runs
- **Duplicate Prevention**: Tracks processed items to avoid duplicates
- **Activity Logging**: Records all monitoring activity
- **Markdown Output**: Creates structured files for AI processing

## Installation

### Prerequisites

```bash
# Install Playwright
pip install playwright

# Install Chromium browser
playwright install chromium
```

## Usage

### First Run (Login Required)

```bash
# Run with visible browser to log in
python .claude/skills/twitter-watcher/skill.py --headless false

# Log in to Twitter when browser opens
# Session will be saved for future runs
```

### Subsequent Runs

```bash
# Run in headless mode (uses saved session)
python .claude/skills/twitter-watcher/skill.py

# Process more items
python .claude/skills/twitter-watcher/skill.py --max-notifications 20 --max-mentions 20

# Custom vault and session paths
python .claude/skills/twitter-watcher/skill.py --vault /path/to/vault --session /path/to/session
```

### Scheduled Usage

Add to scheduler for automatic monitoring:

```python
# In scheduler.py
def check_twitter():
    """Check Twitter every 30 minutes."""
    return run_skill("twitter-watcher", "--max-notifications 10 --max-mentions 10")

schedule.every(30).minutes.do(check_twitter)
```

## Output Format

### Notification File

```markdown
---
type: twitter_notification
source: twitter
item_id: abc123def
author: N/A
timestamp: 2026-02-27T10:30:00Z
received: 2026-02-27T10:30:15.123456Z
status: new
---

# Twitter Notification

**From:** N/A
**Time:** 2026-02-27T10:30:00Z

## Content

@username liked your tweet: "Great insights on AI automation!"

## Next Steps

This Twitter notification has been detected and placed in the Inbox for processing.
The AI Employee will:
1. Read this file from /Inbox
2. Analyze the content and priority
3. Create an action item in /Needs_Action if required
4. Process according to Company_Handbook.md rules

---
*Created by Twitter Watcher Agent Skill*
```

### Mention File

```markdown
---
type: twitter_mention
source: twitter
item_id: xyz789abc
author: John Doe
timestamp: 2026-02-27T10:30:00Z
received: 2026-02-27T10:30:15.123456Z
status: new
---

# Twitter Mention from John Doe

**From:** John Doe
**Time:** 2026-02-27T10:30:00Z

## Content

@yourusername This is a great thread on AI agents! Have you considered...

## Next Steps

This Twitter mention has been detected and placed in the Inbox for processing.
The AI Employee will:
1. Read this file from /Inbox
2. Analyze the content and priority
3. Create an action item in /Needs_Action if required
4. Process according to Company_Handbook.md rules

---
*Created by Twitter Watcher Agent Skill*
```

## State Management

### Session Persistence

Browser session is saved in `twitter_session/` directory:
- Maintains login across runs
- No need to re-authenticate
- Session expires after ~30 days of inactivity

### Processed IDs

Tracks processed items in `.twitter_processed_ids.json`:
```json
[
  "abc123def456",
  "xyz789abc012",
  "def456ghi789"
]
```

## Integration

### With Bronze Tier

```
Twitter → Twitter Watcher → /Inbox/TWITTER_*.md → File System Watcher → /Needs_Action/
```

### With Scheduler

```python
# Automated monitoring every 30 minutes
schedule.every(30).minutes.do(check_twitter)
```

### With Company Handbook

Define Twitter response rules in `Company_Handbook.md`:

```markdown
## Twitter Response Rules

- Respond to mentions within 2 hours during business hours
- Thank users for positive feedback
- Address questions with helpful information
- Flag negative sentiment for human review
- Ignore spam and promotional mentions
```

## Error Handling

### Not Logged In

```
ERROR - Not logged in to Twitter
INFO - Please run with --headless false to log in
```

**Solution**: Run with visible browser and log in manually.

### Session Expired

```
ERROR - Session expired or invalid
```

**Solution**: Delete session folder and re-login:
```bash
rm -rf twitter_session
python .claude/skills/twitter-watcher/skill.py --headless false
```

### Rate Limiting

Twitter may rate limit if checking too frequently. Recommended intervals:
- Minimum: 15 minutes between checks
- Recommended: 30 minutes
- Conservative: 60 minutes

## Security

- **Local Session**: All session data stored locally
- **No API Keys**: Uses browser automation (no Twitter API required)
- **Read-Only**: Only reads notifications and mentions
- **No Credentials in Code**: Login handled through browser

## Performance

- **Startup Time**: ~5-8 seconds (with cached session)
- **Per Item**: ~0.3 seconds
- **10 Items**: ~8-10 seconds total
- **Memory**: ~150MB (browser process)

## Limitations

- Requires manual login on first run
- Session expires after inactivity
- Rate limiting by Twitter
- Browser automation may break with Twitter UI changes
- Cannot access DMs (requires Twitter API)

## Troubleshooting

**Browser won't start**
```bash
# Reinstall Chromium
playwright install chromium
```

**Can't find notifications**
- Verify you're logged in
- Check Twitter has notifications
- Try increasing max-notifications parameter

**Files not created**
- Check vault path is correct
- Verify /Inbox directory exists
- Check file permissions

## Future Enhancements

- Direct message monitoring (requires Twitter API)
- Sentiment analysis on mentions
- Automated reply drafting
- Thread tracking
- Analytics dashboard

---

**Part of Gold Tier - Personal AI Employee**
**Social Media Monitoring**
