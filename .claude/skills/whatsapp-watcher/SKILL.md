# WhatsApp Watcher Skill

Monitor WhatsApp Web for important messages and create action items automatically.

## What this skill does

This skill monitors WhatsApp Web and:
1. Detects unread messages with priority keywords
2. Filters by keywords (urgent, asap, invoice, payment, help)
3. Creates action items in `/Needs_Action` folder
4. Extracts sender, message content, and timestamp
5. Assigns priority based on content analysis
6. Maintains WhatsApp Web session

## Prerequisites

- Playwright browser automation library
- WhatsApp Web session (QR code scan on first run)
- Persistent browser context for session storage

## Setup

1. Install Playwright: `pip install playwright`
2. Install browsers: `playwright install chromium`
3. First run will open WhatsApp Web for QR code scan
4. Session saved to `whatsapp_session/` directory

## When to use

Run this skill:
- Manually to check for new messages
- Via scheduler (every 2-5 minutes)
- As part of continuous monitoring

## Usage

```bash
/whatsapp-watcher
```

With options:
```bash
/whatsapp-watcher --check-interval 120  # Check every 2 minutes
/whatsapp-watcher --keywords "urgent,invoice,payment"
```

## Workflow

1. **Launch Browser:**
   - Load persistent context (session)
   - Navigate to WhatsApp Web
   - Wait for chat list to load

2. **Scan for Unread:**
   - Find all chats with unread badge
   - Filter by keyword presence
   - Get last 5 unread priority messages

3. **Process Each Message:**
   - Extract sender name
   - Get message text
   - Analyze priority (high/medium/low)
   - Check if approval required

4. **Create Action Items:**
   - Generate unique filename: `WHATSAPP_{timestamp}_{sender}.md`
   - Add metadata (type, from, priority)
   - Include message content
   - Suggest actions (reply, call, archive)
   - Save to `/Needs_Action`

5. **Track Processed:**
   - Mark messages as seen (optional)
   - Maintain processed message list
   - Log to `/Logs`

## Action Item Format

```markdown
---
type: whatsapp
from: Contact Name
received: 2026-02-27T10:30:00Z
priority: high
status: pending
keywords: urgent, invoice
---

## Message Content
[Message text]

## Suggested Actions
- [ ] Reply to sender
- [ ] Call if urgent
- [ ] Forward to team member
- [ ] Archive after processing

## Context
- Keywords detected: urgent, invoice
- Requires approval: Yes (external communication)
- Contact type: Client
```

## Priority Rules

**High Priority:**
- Contains keywords: urgent, asap, help, critical, emergency
- From known clients or VIPs
- Invoice or payment related
- Multiple unread messages from same contact

**Medium Priority:**
- General inquiries
- Routine business messages
- No urgent keywords

**Low Priority:**
- Group messages
- Automated notifications
- Marketing messages

## Configuration

Edit `Company_Handbook.md` to customize:
- Keywords to monitor
- VIP contact list
- Auto-reply rules
- Approval requirements

## Security & Privacy

- Session stored locally (never shared)
- Browser runs in headless mode
- No message content sent to external services
- All data stays in your vault
- WhatsApp terms of service apply

## Important Notes

**WhatsApp Terms:**
- This uses WhatsApp Web automation
- Be aware of WhatsApp's terms of service
- Use responsibly and within limits
- Avoid excessive automation

**Session Management:**
- Session expires if inactive too long
- Re-scan QR code if session lost
- Keep browser context persistent

## Troubleshooting

**Session expired:**
- Delete `whatsapp_session/` folder
- Run skill again to re-authenticate
- Scan QR code with phone

**No messages detected:**
- Check keyword list
- Verify WhatsApp Web is accessible
- Review browser console for errors

**Browser crashes:**
- Restart the skill
- Check system resources
- Update Playwright browsers
