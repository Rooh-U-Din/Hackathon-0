# Gmail Watcher Agent Skill

Production-ready Gmail monitoring skill that creates markdown files in `/Inbox/` for new emails.

## Architecture

This skill follows a modular, single-responsibility design:

```
gmail-watcher/
├── skill.py              # Entry point (thin wrapper)
├── gmail_watcher.py      # Core watcher logic (modular)
├── skill.json            # Metadata
└── SKILL.md             # Documentation
```

## What It Does

1. **Authenticates** with Gmail API using credentials.json
2. **Monitors** inbox for unread emails
3. **Creates** markdown files in `/Inbox/` for each new email
4. **Tracks** processed emails to avoid duplicates
5. **Logs** all activity to `/Logs/`

## Integration with Bronze Tier

```
Gmail API
    ↓
Gmail Watcher (this skill)
    ↓
Creates: /Inbox/EMAIL_*.md
    ↓
File System Watcher (Bronze)
    ↓
Creates: /Needs_Action/ACTION_*.md
    ↓
Claude Code processes
    ↓
Moves to: /Done/
```

## File Format

Each email creates a markdown file in `/Inbox/`:

```markdown
---
type: email
source: gmail
message_id: abc123
thread_id: thread_xyz
from: sender@example.com
to: you@example.com
subject: Email subject
date: Mon, 27 Feb 2026 10:30:00 +0000
received: 2026-02-27T10:30:15Z
status: new
---

# Email: Subject line

**From:** sender@example.com
**Date:** Mon, 27 Feb 2026 10:30:00 +0000

## Preview

Email snippet/preview text...

## Next Steps

This email has been detected and placed in the Inbox for processing.
```

## Setup

### 1. Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

### 2. Get Gmail Credentials

Follow `GMAIL_SETUP_GUIDE.md` to:
1. Create Google Cloud project
2. Enable Gmail API
3. Download credentials.json
4. Place in project root

### 3. First Run (Authentication)

```bash
python skill.py
```

This will:
- Open browser for OAuth
- Save token.json
- Process any unread emails

## Usage

### Manual Run

```bash
# Default (process up to 10 emails)
python skill.py

# Custom vault path
python skill.py --vault /path/to/vault

# Process more emails
python skill.py --max-emails 20

# Custom credentials location
python skill.py --credentials /path/to/credentials.json
```

### Scheduled Run

Add to scheduler.py:

```python
def check_gmail():
    """Check Gmail every 15 minutes."""
    return run_skill("gmail-watcher", "--max-emails 10")

schedule.every(15).minutes.do(check_gmail)
```

## Error Handling

The watcher includes comprehensive error handling:

### Authentication Errors
- **Token expired:** Automatically refreshes
- **No credentials:** Clear error message with setup guide
- **Invalid credentials:** Logs error and exits gracefully

### API Errors
- **Rate limit:** Logs warning, continues on next run
- **Network error:** Logs error, retries on next scheduled run
- **Invalid message:** Skips message, continues with others

### File System Errors
- **Vault not found:** Exits with clear error
- **Permission denied:** Logs error, continues
- **Disk full:** Logs error, stops processing

## Logging

All activity is logged to:
- **Console:** INFO level messages
- **File:** `/Logs/YYYY-MM-DD_gmail_watcher.json`

Log format:
```json
{
  "timestamp": "2026-02-27T10:30:00Z",
  "activity": "check",
  "new_emails": 3,
  "total_checked": 5
}
```

## State Management

Processed email IDs are tracked in:
- **File:** `/.gmail_processed_ids.json`
- **Format:** JSON array of message IDs
- **Purpose:** Prevent duplicate processing

## Security

- ✅ Credentials stored in separate file (not in code)
- ✅ Token auto-refreshed (no manual intervention)
- ✅ Read-only Gmail access (cannot send/delete)
- ✅ All files in .gitignore
- ✅ No sensitive data in logs

## Performance

- **Startup:** ~2 seconds (with cached token)
- **Per email:** ~0.5 seconds
- **10 emails:** ~5-7 seconds total
- **Memory:** ~50MB
- **API quota:** ~5 units per email check

## Troubleshooting

### "Credentials not found"
- Ensure credentials.json exists in project root
- Check path with `--credentials` flag
- See GMAIL_SETUP_GUIDE.md

### "Authentication failed"
- Delete token.json and re-authenticate
- Check credentials.json is valid
- Verify Gmail API is enabled

### "No new emails"
- Check Gmail has unread emails
- Verify processed IDs file isn't corrupted
- Try with `--max-emails 20`

### "Permission denied"
- Check vault directory permissions
- Ensure /Inbox/ folder exists
- Run with appropriate user permissions

## Testing

Test the watcher:

```bash
# 1. Send yourself a test email
# 2. Run watcher
python skill.py --max-emails 1

# 3. Check output
ls AI_Employee_Vault/Inbox/

# 4. Verify file content
cat AI_Employee_Vault/Inbox/EMAIL_*.md
```

## Modular Design Benefits

1. **Separation of Concerns**
   - skill.py: Entry point
   - gmail_watcher.py: Core logic
   - Easy to test and maintain

2. **Reusability**
   - GmailWatcher class can be imported
   - Used in other scripts/tools
   - Testable independently

3. **Single Responsibility**
   - Only monitors Gmail
   - Only creates /Inbox/ files
   - Doesn't process or analyze

4. **Clean Integration**
   - Works with existing Bronze Tier
   - No modifications to other components
   - Clear data flow

## Future Enhancements

Potential improvements:
- Filter by labels/folders
- Priority detection (urgent keywords)
- Attachment handling
- Thread conversation tracking
- Smart batching for high volume

## Related Skills

- **process-tasks:** Processes files from /Needs_Action
- **approval-workflow:** Handles email reply approvals
- **email-mcp:** Sends email responses

---

*Part of Silver Tier - Personal AI Employee*
*Modular Agent Skill Architecture*
