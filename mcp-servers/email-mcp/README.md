# Email MCP Server

Model Context Protocol (MCP) server for sending emails via Gmail API.

## What this is

This is an MCP server that provides email sending capabilities to Claude Code. It exposes tools that Claude can use to send emails after approval.

## Features

- Send emails via Gmail API
- Draft emails for review
- Search sent emails
- Get email status
- Secure credential handling

## Prerequisites

- Node.js v18+ or Python 3.10+
- Gmail API credentials
- OAuth token with send permissions

## Installation

### Python Implementation

```bash
cd mcp-servers/email-mcp
pip install -r requirements.txt
```

### Node.js Implementation

```bash
cd mcp-servers/email-mcp
npm install
```

## Configuration

Add to Claude Code's MCP configuration (`~/.config/claude-code/mcp.json`):

```json
{
  "servers": [
    {
      "name": "email",
      "command": "python",
      "args": ["D:/vsCode/CLI/Hackathon-0/mcp-servers/email-mcp/server.py"],
      "env": {
        "GMAIL_CREDENTIALS": "D:/vsCode/CLI/Hackathon-0/credentials.json",
        "GMAIL_TOKEN": "D:/vsCode/CLI/Hackathon-0/token.json"
      }
    }
  ]
}
```

## Available Tools

### 1. send_email

Send an email via Gmail.

**Parameters:**
- `to` (string, required): Recipient email address
- `subject` (string, required): Email subject
- `body` (string, required): Email body (plain text or HTML)
- `cc` (string, optional): CC recipients (comma-separated)
- `bcc` (string, optional): BCC recipients (comma-separated)
- `attachments` (array, optional): File paths to attach

**Returns:**
- `message_id`: Gmail message ID
- `status`: "sent" or "error"
- `timestamp`: When email was sent

**Example:**
```json
{
  "to": "client@example.com",
  "subject": "Invoice for January 2026",
  "body": "Please find attached your invoice for January 2026.\n\nBest regards,\nYour Company",
  "attachments": ["/path/to/invoice.pdf"]
}
```

### 2. draft_email

Create a draft email without sending.

**Parameters:**
- Same as send_email

**Returns:**
- `draft_id`: Gmail draft ID
- `status`: "draft_created"

### 3. search_sent_emails

Search sent emails.

**Parameters:**
- `query` (string): Search query (Gmail search syntax)
- `max_results` (integer): Maximum results (default: 10)

**Returns:**
- Array of email summaries

### 4. get_email_status

Check if an email was delivered.

**Parameters:**
- `message_id` (string): Gmail message ID

**Returns:**
- `status`: "delivered", "pending", "failed"
- `timestamp`: Status check time

## Usage from Claude Code

Once the MCP server is configured, Claude Code can use it:

```
Claude, send an email to client@example.com with subject "Project Update"
and body "The project is complete and ready for review."
```

Claude will:
1. Create approval request in /Pending_Approval
2. Wait for human approval
3. Use the email MCP tool to send
4. Log the sent email

## Security

- Credentials stored in environment variables
- OAuth tokens with minimal permissions
- All sends logged for audit
- Approval required before sending

## Testing

Test the MCP server:

```bash
# Python
python server.py --test

# Node.js
node server.js --test
```

## Troubleshooting

**MCP server not connecting:**
- Check Claude Code logs: `~/.config/claude-code/logs/`
- Verify paths in mcp.json are absolute
- Ensure credentials.json exists
- Test server independently

**Authentication errors:**
- Regenerate OAuth token
- Check Gmail API permissions
- Verify credentials.json is valid

**Emails not sending:**
- Check Gmail API quota
- Verify recipient addresses
- Review error logs
- Test with Gmail web interface
