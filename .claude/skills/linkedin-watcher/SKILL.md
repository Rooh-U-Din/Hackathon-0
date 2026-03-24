# LinkedIn Watcher Agent Skill

Production-ready LinkedIn monitoring skill that creates markdown files in `/Inbox/` for new notifications and messages.

## Architecture

This skill follows a modular, single-responsibility design:

```
linkedin-watcher/
├── skill.py              # Entry point (thin wrapper)
├── linkedin_watcher.py   # Core watcher logic (modular)
├── skill.json            # Metadata
└── SKILL.md             # Documentation
```

## What It Does

1. **Launches** Playwright browser with persistent session
2. **Authenticates** to LinkedIn (manual login on first run)
3. **Monitors** notifications and messages
4. **Creates** markdown files in `/Inbox/` for each new item
5. **Tracks** processed items to avoid duplicates
6. **Logs** all activity to `/Logs/`

## Integration with Bronze Tier

```
LinkedIn Web
    ↓
LinkedIn Watcher (this skill)
    ↓
Creates: /Inbox/LINKEDIN_*.md
    ↓
File System Watcher (Bronze)
    ↓
Creates: /Needs_Action/ACTION_*.md
    ↓
Claude Code processes
    ↓
Moves to: /Done/
```

## File Formats

### Notification File

```markdown
---
type: linkedin_notification
source: linkedin
notification_id: abc123
actor: John Doe
timestamp: 2h ago
received: 2026-02-27T10:30:15Z
status: new
---

# LinkedIn Notification

**From:** John Doe
**Time:** 2h ago

## Content

John Doe commented on your post: "Great insights!"

## Next Steps

This LinkedIn notification has been detected...
```

### Message File

```markdown
---
type: linkedin_message
source: linkedin
message_id: xyz789
sender: Jane Smith
timestamp: 1h ago
received: 2026-02-27T10:30:15Z
status: new
---

# LinkedIn Message

**From:** Jane Smith
**Time:** 1h ago

## Preview

Hi, I'd like to discuss a potential collaboration...

## Next Steps

This LinkedIn message has been detected...
```

## Setup

### 1. Install Dependencies

```bash
pip install playwright
playwright install chromium
```

### 2. First Run (Login)

```bash
# Run with visible browser for first-time login
python skill.py --headless false
```

This will:
- Open LinkedIn in browser
- Wait for you to log in manually
- Save session for future runs
- Process any notifications/messages

### 3. Subsequent Runs

```bash
# Run in headless mode (uses saved session)
python skill.py
```

## Usage

### Manual Run

```bash
# Default (headless, 10 notifications, 5 messages)
python skill.py

# Custom vault path
python skill.py --vault /path/to/vault

# Process more items
python skill.py --max-notifications 20 --max-messages 10

# Visible browser (for debugging)
python skill.py --headless false

# Custom session location
python skill.py --session /path/to/session
```

### Scheduled Run

Add to scheduler.py:

```python
def check_linkedin():
    """Check LinkedIn every 30 minutes."""
    return run_skill("linkedin-watcher", "--max-notifications 10")

schedule.every(30).minutes.do(check_linkedin)
```

## Error Handling

The watcher includes comprehensive error handling:

### Authentication Errors
- **Not logged in:** Prompts to run with --headless false
- **Session expired:** Clear session folder and re-login
- **Login failed:** Logs error and exits gracefully

### Browser Errors
- **Playwright not installed:** Clear error message with install command
- **Browser crash:** Logs error, closes cleanly
- **Page timeout:** Logs warning, continues with next item

### Parsing Errors
- **Element not found:** Skips item, continues with others
- **Invalid data:** Logs warning, continues
- **Network error:** Logs error, retries on next run

## Logging

All activity is logged to:
- **Console:** INFO level messages
- **File:** `/Logs/YYYY-MM-DD_linkedin_watcher.json`

Log format:
```json
{
  "timestamp": "2026-02-27T10:30:00Z",
  "activity": "check",
  "new_notifications": 3,
  "new_messages": 1,
  "total_processed": 4
}
```

## State Management

Processed item IDs are tracked in:
- **File:** `/.linkedin_processed_ids.json`
- **Format:** JSON array of hashed IDs
- **Purpose:** Prevent duplicate processing

## Security

- ✅ Session stored locally (not in code)
- ✅ No credentials in code or logs
- ✅ Session files excluded from git
- ✅ Read-only access (cannot post/send)
- ✅ Respects LinkedIn terms of service

## Performance

- **Startup:** ~5 seconds (with cached session)
- **Per notification:** ~0.3 seconds
- **Per message:** ~0.5 seconds
- **10 items:** ~8-10 seconds total
- **Memory:** ~150MB (browser)

## LinkedIn Terms of Service

**Important:** This watcher uses browser automation to access LinkedIn Web. Be aware of:
- LinkedIn's terms of service regarding automation
- Rate limiting (don't run too frequently)
- Responsible use (monitor, don't spam)
- Manual login required (no credential storage)

**Recommended frequency:** Every 30-60 minutes maximum

## Troubleshooting

### "Playwright not installed"
```bash
pip install playwright
playwright install chromium
```

### "Not logged in to LinkedIn"
```bash
# Run with visible browser to log in
python skill.py --headless false
```

### "Session expired"
```bash
# Delete session and re-login
rm -rf linkedin_session
python skill.py --headless false
```

### "No notifications found"
- Check LinkedIn has notifications
- Verify you're logged in
- Try with --headless false to see browser

### "Browser crashes"
- Update Playwright: `pip install --upgrade playwright`
- Reinstall browsers: `playwright install chromium`
- Check system resources

## Testing

Test the watcher:

```bash
# 1. Ensure you have LinkedIn notifications
# 2. Run watcher with visible browser
python skill.py --headless false --max-notifications 2

# 3. Check output
ls AI_Employee_Vault/Inbox/LINKEDIN_*

# 4. Verify file content
cat AI_Employee_Vault/Inbox/LINKEDIN_NOTIFICATION_*.md
```

## Modular Design Benefits

1. **Separation of Concerns**
   - skill.py: Entry point
   - linkedin_watcher.py: Core logic
   - Easy to test and maintain

2. **Reusability**
   - LinkedInWatcher class can be imported
   - Used in other scripts/tools
   - Testable independently

3. **Single Responsibility**
   - Only monitors LinkedIn
   - Only creates /Inbox/ files
   - Doesn't process or analyze

4. **Clean Integration**
   - Works with existing Bronze Tier
   - No modifications to other components
   - Clear data flow

## Limitations

Due to LinkedIn's API restrictions:
- Uses web scraping (not official API)
- Requires manual login
- Subject to LinkedIn UI changes
- Rate limiting recommended

## Future Enhancements

Potential improvements:
- Connection request detection
- Post engagement tracking
- Profile view notifications
- Job application updates
- Smart filtering by keywords

## Related Skills

- **process-tasks:** Processes files from /Needs_Action
- **approval-workflow:** Handles message reply approvals
- **linkedin-poster:** Posts content to LinkedIn

---

*Part of Silver Tier - Personal AI Employee*
*Modular Agent Skill Architecture*
