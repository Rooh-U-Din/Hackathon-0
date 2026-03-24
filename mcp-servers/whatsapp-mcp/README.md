# WhatsApp MCP Server

## Overview

The WhatsApp MCP Server provides WhatsApp messaging capabilities via browser automation using Playwright. It enables Claude Code to send messages and retrieve unread messages from WhatsApp Web.

**⚠️ IMPORTANT: This MCP server should ONLY be used on the LOCAL AGENT, never on cloud agents. WhatsApp sessions contain sensitive authentication data and must remain local.**

## Features

- **Send Messages**: Send WhatsApp messages to contacts
- **Get Unread Messages**: Retrieve unread messages
- **Session Persistence**: Login once, reuse session across runs
- **Browser Automation**: Uses Playwright for WhatsApp Web interaction

## Installation

### Prerequisites

1. **Node.js 18+** installed
2. **Playwright** installed
3. **WhatsApp account** with phone access for QR code scanning

### Setup

```bash
cd mcp-servers/whatsapp-mcp

# Install dependencies
npm install

# Install Playwright browsers
npx playwright install chromium

# Set environment variables (optional)
export WHATSAPP_SESSION_PATH="./whatsapp_session"

# Test the server
node index.js
```

## Configuration

### Environment Variables

```bash
# .env file
WHATSAPP_SESSION_PATH=./whatsapp_session
```

### Claude Code MCP Configuration

**⚠️ LOCAL AGENT ONLY - Add to local machine's mcp.json:**

```json
{
  "servers": [
    {
      "name": "whatsapp",
      "command": "node",
      "args": ["/path/to/mcp-servers/whatsapp-mcp/index.js"],
      "env": {
        "WHATSAPP_SESSION_PATH": "./whatsapp_session"
      }
    }
  ]
}
```

**❌ DO NOT add to cloud agent's mcp.json**

## Available Tools

### 1. send_message

Send a WhatsApp message to a contact.

**Parameters:**
- `contact` (string, required): Contact name or phone number
- `message` (string, required): Message text to send

**Example:**
```javascript
{
  "contact": "John Doe",
  "message": "Hi John, the project is ready for review."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Message sent successfully"
}
```

### 2. get_unread_messages

Get unread WhatsApp messages.

**Parameters:**
- `limit` (number): Maximum number of messages to return (default: 10)

**Example:**
```javascript
{
  "limit": 10
}
```

**Response:**
```json
{
  "success": true,
  "messages": [
    {
      "text": "Contact Name\nMessage preview..."
    }
  ]
}
```

## First Run - Authentication

On first run, the server will:
1. Launch a visible Chrome browser
2. Navigate to WhatsApp Web
3. Display QR code for scanning
4. Wait for you to scan with your phone
5. Save session for future use

**Steps:**
1. Run the MCP server
2. Open WhatsApp on your phone
3. Go to Settings > Linked Devices
4. Tap "Link a Device"
5. Scan the QR code displayed in browser
6. Wait for WhatsApp Web to load

**After first authentication, you won't need to scan again.**

## How It Works

1. **Session Management**: Uses Playwright's persistent context to maintain WhatsApp Web session
2. **Browser Automation**: Interacts with WhatsApp Web DOM elements
3. **Message Sending**: Searches for contact, opens chat, types message, clicks send
4. **Message Retrieval**: Scans chat list for unread indicators

## Security Considerations

### ⚠️ CRITICAL SECURITY WARNINGS

1. **LOCAL AGENT ONLY**: Never use on cloud agents
2. **Session Storage**: WhatsApp session stored in `whatsapp_session/` directory
3. **Never Sync**: Add `whatsapp_session/` to `.gitignore`
4. **Account Risk**: Browser automation may violate WhatsApp ToS
5. **Detection Risk**: WhatsApp may detect automation and ban account

### Security Best Practices

1. **Never commit session files** to git
2. **Use on local machine only** (never cloud)
3. **Limit usage frequency** to avoid detection
4. **Monitor for WhatsApp warnings** about unusual activity
5. **Have backup communication method** in case of ban

### .gitignore Entry

```
# WhatsApp session (NEVER sync to cloud)
whatsapp_session/
**/whatsapp_session/
```

## Limitations

1. **No Headless Mode**: WhatsApp Web requires visible browser
2. **Detection Risk**: Browser automation detectable by WhatsApp
3. **Rate Limiting**: Too many messages may trigger WhatsApp limits
4. **Session Expiry**: Sessions may expire after long periods
5. **Manual Login**: Requires phone access for initial QR scan

## Troubleshooting

### Error: QR Code Timeout

**Problem**: QR code not scanned within 60 seconds

**Solution**:
1. Ensure phone has internet connection
2. Open WhatsApp on phone quickly
3. Scan QR code within timeout period
4. Increase timeout in code if needed

### Error: Session Expired

**Problem**: WhatsApp session no longer valid

**Solution**:
1. Delete `whatsapp_session/` directory
2. Restart MCP server
3. Scan QR code again

### Error: Element Not Found

**Problem**: WhatsApp Web UI changed

**Solution**:
1. Check if WhatsApp Web updated
2. Update selectors in code
3. Report issue to maintainer

### Error: Browser Launch Failed

**Problem**: Playwright browser not installed

**Solution**:
```bash
npx playwright install chromium
```

## Performance

- **Message Send Time**: ~2-3 seconds per message
- **Unread Check Time**: ~1-2 seconds
- **Session Load Time**: ~3-5 seconds (first load)
- **Memory Usage**: ~200-300 MB (browser process)

## Integration with Personal AI Employee

### Local Agent Usage

```python
# In local_agent.py
# Send WhatsApp message after approval

def send_whatsapp_message(contact, message):
    result = mcp_client.call_tool('whatsapp', 'send_message', {
        'contact': contact,
        'message': message
    })
    return result
```

### Approval Workflow

1. Cloud agent drafts message in `/Updates/`
2. User approves in `/Pending_Approval/`
3. Local agent sends via WhatsApp MCP
4. Result logged in `/Logs/`

## Alternatives

If WhatsApp MCP is too risky, consider:

1. **Twilio API**: Official WhatsApp Business API
2. **WhatsApp Business API**: Requires business verification
3. **Manual Sending**: AI drafts, human sends
4. **Email Fallback**: Use Email MCP instead

## Future Enhancements

- Group message support
- Media sending (images, documents)
- Message status tracking (delivered, read)
- Contact management
- Chat history retrieval

---

**Part of Gold Tier - Personal AI Employee**
**WhatsApp Integration via MCP**

**⚠️ Use with caution - Account ban risk**
**✅ LOCAL AGENT ONLY - Never on cloud**
