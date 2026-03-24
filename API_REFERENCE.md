# API Reference - Personal AI Employee System

## Overview

This document lists all external APIs and integrations used in the Personal AI Employee system, along with their file paths and purposes.

---

## 1. Gmail API (Google)

**Purpose:** Email monitoring, reading, and sending

**Authentication:** OAuth 2.0

**Scopes Used:**
- `https://www.googleapis.com/auth/gmail.readonly` - Read emails
- `https://www.googleapis.com/auth/gmail.send` - Send emails

**Files Using Gmail API:**

### Core Implementation
- **`.claude/skills/gmail-watcher/gmail_watcher.py`** (320 lines)
  - Monitors Gmail inbox for new emails
  - Creates markdown files in vault
  - Duplicate detection via `.gmail_processed_ids.json`

### MCP Server
- **`mcp-servers/email-mcp/server.py`** (Python MCP server)
  - Provides email sending capability via MCP protocol
  - Used by local agent for approved email sends

### Utility Scripts
- **`send_email.py`** (Email sending script)
  - Sends emails to external recipients
  - Used for testing and demonstrations

- **`send_final_email.py`** (Project announcement email)
  - Sends comprehensive project summary
  - Demonstrates email automation

- **`test_email_send.py`** (Testing script)
  - Tests Gmail API authentication
  - Validates OAuth token and scopes

**Required Files:**
- `credentials.json` (OAuth client credentials from Google Cloud Console)
- `token.json` (Generated OAuth access token)

**Setup Guide:** `GMAIL_SETUP_GUIDE.md`

---

## 2. Playwright Browser Automation

**Purpose:** Browser automation for social media platforms

**Type:** Headless/headed browser control

**Platforms Automated:**
- LinkedIn
- Facebook
- Twitter/X
- Instagram
- WhatsApp Web

### LinkedIn Integration

**Files:**
- **`.claude/skills/linkedin-poster/skill.py`** (16,616 bytes)
  - Posts content to LinkedIn
  - Session persistence via `linkedin_session/`
  - Multiple selector fallbacks for reliability

- **`.claude/skills/linkedin-watcher/linkedin_watcher.py`** (Python)
  - Monitors LinkedIn notifications
  - Detects new messages and connection requests

**Session Directory:** `linkedin_session/`

### Facebook Integration

**Files:**
- **`.claude/skills/facebook-poster/facebook_poster.py`** (Python)
  - Posts content to Facebook
  - Session persistence via `facebook_session/`
  - Handles Facebook's dynamic UI

- **`.claude/skills/facebook-watcher/facebook_watcher.py`** (Python)
  - Monitors Facebook notifications
  - Detects messages and updates

**Session Directory:** `facebook_session/`

### Twitter/X Integration

**Files:**
- **`.claude/skills/twitter-poster/twitter_poster.py`** (Python)
  - Posts tweets to Twitter/X
  - 280 character limit handling
  - Session persistence via `twitter_session/`
  - Multiple posting methods (button click, keyboard shortcut)

- **`.claude/skills/twitter-watcher/twitter_watcher.py`** (Python)
  - Monitors Twitter timeline
  - Detects mentions and DMs

**Session Directory:** `twitter_session/`

### Instagram Integration

**Files:**
- **`.claude/skills/instagram-poster/instagram_poster.py`** (Python)
  - Posts images to Instagram
  - Session persistence via `instagram_session/`
  - Image upload handling

- **`.claude/skills/instagram-watcher/instagram_watcher.py`** (Python)
  - Monitors Instagram notifications
  - Detects comments and DMs

**Session Directory:** `instagram_session/`

**Note:** Instagram not in original requirements, partially implemented

### WhatsApp Web Integration

**Files:**
- **`.claude/skills/whatsapp-watcher/skill.py`** (Python)
  - Monitors WhatsApp Web for messages
  - QR code authentication
  - Session persistence

- **`mcp-servers/whatsapp-mcp/index.js`** (Node.js MCP server)
  - Provides WhatsApp message sending via MCP
  - Uses whatsapp-web.js library
  - **SECURITY WARNING:** LOCAL ONLY, never deploy to cloud

**Session Directory:** `whatsapp_session/`

**Documentation:** `mcp-servers/whatsapp-mcp/README.md`

### Playwright MCP Server

**Files:**
- **`.claude/skills/browsing-with-playwright/SKILL.md`** (Documentation)
  - General browser automation skill
  - Used for custom web scraping tasks

**Scripts:**
- `.claude/skills/browsing-with-playwright/scripts/start-server.sh`
- `.claude/skills/browsing-with-playwright/scripts/stop-server.sh`
- `.claude/skills/browsing-with-playwright/scripts/verify.py`
- `.claude/skills/browsing-with-playwright/scripts/mcp-client.py`

---

## 3. Odoo ERP API (JSON-RPC)

**Purpose:** Business operations integration (invoicing, customers, inventory)

**Type:** JSON-RPC 2.0 over HTTP

**Authentication:** Username/Password + API Key

**Files:**

### MCP Server
- **`mcp-servers/odoo-mcp/index.js`** (Node.js MCP server)
  - Provides Odoo integration via MCP protocol
  - Invoice operations (create, read, update)
  - Customer management
  - Product/inventory queries

**Package Configuration:**
- `mcp-servers/odoo-mcp/package.json`

**Testing:**
- `tests/test_odoo_integration.py` (Integration tests)

**API Endpoints Used:**
- `/web/session/authenticate` - Authentication
- `/web/dataset/call_kw` - Model operations (CRUD)
- `/xmlrpc/2/common` - Common operations
- `/xmlrpc/2/object` - Object operations

**Odoo Models Used:**
- `res.partner` - Customers/contacts
- `account.move` - Invoices
- `product.product` - Products
- `stock.quant` - Inventory

**Documentation:** `mcp-servers/odoo-mcp/README.md`

**Setup Requirements:**
- Odoo instance URL
- Database name
- Username
- API key/password

---

## 4. Calendar API (Custom JSON Storage)

**Purpose:** Event and appointment management

**Type:** Local JSON file storage (no external API)

**Files:**

### MCP Server
- **`mcp-servers/calendar-mcp/README.md`** (Documentation)
- **`mcp-servers/calendar-mcp/index.js`** (Node.js MCP server)
  - CRUD operations for calendar events
  - JSON file-based storage
  - No external API dependencies

**Storage Format:**
```json
{
  "events": [
    {
      "id": "uuid",
      "title": "Event Title",
      "start": "2026-02-28T10:00:00",
      "end": "2026-02-28T11:00:00",
      "description": "Event details"
    }
  ]
}
```

**Storage Location:** `calendar_data.json` (configurable)

---

## 5. Model Context Protocol (MCP)

**Purpose:** Standardized interface for AI model integrations

**Type:** Protocol specification by Anthropic

**MCP Servers Implemented:**

1. **Email MCP** (`mcp-servers/email-mcp/`)
   - Gmail API wrapper
   - Send/read operations

2. **Odoo MCP** (`mcp-servers/odoo-mcp/`)
   - Odoo JSON-RPC wrapper
   - Business operations

3. **WhatsApp MCP** (`mcp-servers/whatsapp-mcp/`)
   - WhatsApp Web wrapper
   - Message operations (LOCAL ONLY)

4. **Calendar MCP** (`mcp-servers/calendar-mcp/`)
   - Calendar operations
   - JSON storage

**Documentation:**
- Individual README.md in each MCP server directory
- `MCP_TESTING_REPORT.md` (comprehensive testing)

---

## API Usage Summary

| API | Purpose | Authentication | Files | Status |
|-----|---------|----------------|-------|--------|
| Gmail API | Email operations | OAuth 2.0 | 5 files | ✅ Operational |
| Playwright | Browser automation | Session-based | 12+ files | ✅ Operational |
| Odoo JSON-RPC | ERP integration | API Key | 3 files | ✅ Operational |
| WhatsApp Web | Messaging | QR Code | 2 files | ✅ Local only |
| Calendar (Custom) | Event management | None (local) | 2 files | ✅ Operational |

---

## Authentication Files

**Location:** Project root (excluded from git via .gitignore)

### Gmail API
- `credentials.json` - OAuth client credentials
- `token.json` - OAuth access token (auto-generated)

### Social Media Sessions
- `linkedin_session/` - LinkedIn browser session
- `facebook_session/` - Facebook browser session
- `twitter_session/` - Twitter browser session
- `instagram_session/` - Instagram browser session
- `whatsapp_session/` - WhatsApp Web session

**Security:** All session directories and credential files are excluded from git via `.gitignore`

---

## API Rate Limits & Considerations

### Gmail API
- **Quota:** 1 billion quota units per day
- **Rate Limit:** 250 quota units per user per second
- **Recommendation:** Check every 15 minutes (default in scheduler)

### Playwright (Social Media)
- **Rate Limit:** Platform-dependent (LinkedIn, Facebook, Twitter have anti-bot measures)
- **Recommendation:**
  - LinkedIn: Max 3-5 posts per day
  - Facebook: Max 5-10 posts per day
  - Twitter: Max 300 tweets per 3 hours
- **Best Practice:** Use session persistence to avoid repeated logins

### Odoo JSON-RPC
- **Rate Limit:** Depends on Odoo instance configuration
- **Recommendation:** Batch operations when possible

### WhatsApp Web
- **Rate Limit:** WhatsApp enforces strict anti-spam policies
- **Recommendation:**
  - Max 256 messages per day to new contacts
  - Use sparingly to avoid account ban
  - **NEVER deploy to cloud** (security risk)

---

## Testing Files

**Test Coverage:** 106 tests, 100% passing

### API-Specific Tests
- `tests/test_watchers.py` - Tests all watcher integrations
- `tests/test_mcp_servers.py` - Tests all MCP servers
- `tests/test_odoo_integration.py` - Tests Odoo JSON-RPC
- `tests/test_error_recovery.py` - Tests error handling

**Test Reports:**
- `COMPREHENSIVE_TESTING_REPORT.md`
- `FINAL_TESTING_REPORT.md`
- `MCP_TESTING_REPORT.md`
- `WATCHER_TESTING_REPORT.md`

---

## Configuration Files

### Python Dependencies
- **`requirements.txt`** - All Python package dependencies
  - google-auth
  - google-auth-oauthlib
  - google-auth-httplib2
  - google-api-python-client
  - playwright
  - Other utilities

### Node.js Dependencies
- **`mcp-servers/*/package.json`** - MCP server dependencies
  - @modelcontextprotocol/sdk
  - whatsapp-web.js (WhatsApp MCP)
  - Other MCP-specific packages

---

## Security Architecture

**Document:** `SECURITY_ARCHITECTURE.md`

### Key Security Principles

1. **No Secrets in Git**
   - All credentials excluded via `.gitignore`
   - Session files never committed

2. **Cloud-Local Separation**
   - Cloud agent: Draft-only (no API access)
   - Local agent: Execution with API access
   - Vault sync: Excludes sensitive files

3. **Human-in-the-Loop**
   - All sensitive API calls require approval
   - Approval workflow enforced via vault structure

4. **Audit Trail**
   - All API calls logged to `AI_Employee_Vault/Logs/Audit/`
   - Complete traceability

---

## Setup Guides

### Gmail API Setup
**Guide:** `GMAIL_SETUP_GUIDE.md`
1. Create Google Cloud project
2. Enable Gmail API
3. Configure OAuth consent screen
4. Download credentials.json
5. Run authentication flow

### Social Media Setup
**Guide:** Individual SKILL.md files in `.claude/skills/*/`
1. Run poster/watcher with `--headless false`
2. Manually log in to platform
3. Session persists in `*_session/` directory
4. Subsequent runs use saved session

### Odoo Setup
**Guide:** `mcp-servers/odoo-mcp/README.md`
1. Install Odoo (Community or Enterprise)
2. Create API user with appropriate permissions
3. Generate API key
4. Configure MCP server with credentials

---

## API Documentation References

### External Documentation
- **Gmail API:** https://developers.google.com/gmail/api
- **Playwright:** https://playwright.dev/python/
- **Odoo API:** https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
- **MCP Protocol:** https://modelcontextprotocol.io/

### Internal Documentation
- **Architecture:** `ARCHITECTURE.md`
- **Security:** `SECURITY_ARCHITECTURE.md`
- **Deployment:** `CLOUD_DEPLOYMENT_GUIDE.md`
- **Testing:** `COMPREHENSIVE_TESTING_REPORT.md`

---

## Troubleshooting

### Gmail API Issues
- **Error:** "insufficient authentication scopes"
  - **Solution:** Delete `token.json`, re-authenticate with correct scopes

- **Error:** "credentials.json not found"
  - **Solution:** Follow `GMAIL_SETUP_GUIDE.md` to obtain credentials

### Playwright Issues
- **Error:** "Session expired"
  - **Solution:** Delete `*_session/` directory, re-login manually

- **Error:** "Selector not found"
  - **Solution:** Platform UI may have changed, update selectors in code

### Odoo Issues
- **Error:** "Authentication failed"
  - **Solution:** Verify Odoo URL, database name, username, and API key

---

## Future API Integrations (Potential)

### Considered but Not Implemented
1. **Slack API** - Team communication
2. **Notion API** - Knowledge base integration
3. **Stripe API** - Payment processing
4. **Twilio API** - SMS notifications
5. **Google Calendar API** - Replace custom calendar with Google Calendar

---

**Last Updated:** 2026-02-28
**Status:** All APIs operational and tested
**Total APIs:** 5 major integrations (Gmail, Playwright, Odoo, WhatsApp, Calendar)

---

*Personal AI Employee - Platinum Tier*
*Complete API Reference*
