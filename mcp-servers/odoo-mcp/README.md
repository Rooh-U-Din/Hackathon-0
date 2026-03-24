# Odoo MCP Server

## Overview

The Odoo MCP Server provides accounting integration with Odoo Community Edition (19+) via JSON-RPC API. It enables Claude Code to interact with your Odoo accounting system for revenue tracking, expense management, and invoice creation.

## Features

- **Revenue Reporting**: Get revenue data for CEO briefings
- **Expense Tracking**: Monitor business expenses
- **Invoice Management**: Create draft invoices (requires human approval)
- **Draft-Only Mode**: All invoice creation requires human approval before posting
- **JSON-RPC Integration**: Uses Odoo's external API

## Installation

### Prerequisites

1. **Odoo Community Edition 19+** installed and running
2. **Node.js 18+** installed
3. **Odoo credentials** (admin or user with accounting access)

### Setup

```bash
cd mcp-servers/odoo-mcp

# Install dependencies
npm install

# Set environment variables
export ODOO_URL="http://localhost:8069"
export ODOO_DB="odoo"
export ODOO_USERNAME="admin"
export ODOO_PASSWORD="your_password"

# Test the server
node index.js
```

## Configuration

### Environment Variables

```bash
# .env file
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=your_secure_password
```

### Claude Code MCP Configuration

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "servers": [
    {
      "name": "odoo",
      "command": "node",
      "args": ["/path/to/mcp-servers/odoo-mcp/index.js"],
      "env": {
        "ODOO_URL": "http://localhost:8069",
        "ODOO_DB": "odoo",
        "ODOO_USERNAME": "admin",
        "ODOO_PASSWORD": "your_password"
      }
    }
  ]
}
```

## Available Tools

### 1. get_invoices

Get invoices from Odoo.

**Parameters:**
- `limit` (number): Maximum number of invoices to return (default: 10)
- `state` (string): Invoice state - "draft", "posted", or "cancel"

**Example:**
```javascript
{
  "limit": 10,
  "state": "posted"
}
```

**Response:**
```json
{
  "success": true,
  "invoices": [
    {
      "id": 123,
      "name": "INV/2026/0001",
      "partner_id": [45, "Client A"],
      "amount_total": 1500.00,
      "state": "posted",
      "invoice_date": "2026-02-27"
    }
  ]
}
```

### 2. create_draft_invoice

Create a draft invoice (requires human approval to post).

**Parameters:**
- `partner_id` (number, required): Customer ID
- `invoice_lines` (array, required): Invoice line items
- `invoice_date` (string): Invoice date (YYYY-MM-DD)

**Example:**
```javascript
{
  "partner_id": 45,
  "invoice_date": "2026-02-27",
  "invoice_lines": [
    {
      "product_id": 12,
      "quantity": 1,
      "price_unit": 1500.00,
      "description": "Consulting Services - February 2026"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "invoice_id": 124,
  "message": "Draft invoice created. Requires human approval to post.",
  "approval_required": true
}
```

### 3. get_revenue_report

Get revenue report for a date range.

**Parameters:**
- `start_date` (string, required): Start date (YYYY-MM-DD)
- `end_date` (string, required): End date (YYYY-MM-DD)

**Example:**
```javascript
{
  "start_date": "2026-02-01",
  "end_date": "2026-02-28"
}
```

**Response:**
```json
{
  "success": true,
  "period": {
    "start_date": "2026-02-01",
    "end_date": "2026-02-28"
  },
  "total_revenue": 12500.00,
  "invoice_count": 8,
  "invoices": [...]
}
```

### 4. get_expenses

Get expenses for a date range.

**Parameters:**
- `start_date` (string, required): Start date (YYYY-MM-DD)
- `end_date` (string, required): End date (YYYY-MM-DD)
- `limit` (number): Maximum number of expenses to return (default: 50)

**Example:**
```javascript
{
  "start_date": "2026-02-01",
  "end_date": "2026-02-28",
  "limit": 50
}
```

**Response:**
```json
{
  "success": true,
  "period": {
    "start_date": "2026-02-01",
    "end_date": "2026-02-28"
  },
  "total_expenses": 3200.00,
  "expense_count": 15,
  "expenses": [...]
}
```

## Integration with CEO Briefing

The CEO Briefing Generator can use this MCP server to get real accounting data:

```python
# In ceo_briefing_generator.py
# Use Claude Code with Odoo MCP to get revenue data

revenue_data = claude_code.use_mcp_tool('odoo', 'get_revenue_report', {
    'start_date': start_date,
    'end_date': end_date
})

expenses_data = claude_code.use_mcp_tool('odoo', 'get_expenses', {
    'start_date': start_date,
    'end_date': end_date
})
```

## Human-in-the-Loop Approval

All invoice posting requires human approval:

1. AI creates draft invoice via `create_draft_invoice`
2. Draft is saved in Odoo with state="draft"
3. AI creates approval request file in `/Pending_Approval`
4. Human reviews in Odoo and approves/rejects
5. Human moves approval file to `/Approved` or `/Rejected`
6. If approved, human posts invoice in Odoo manually

## Security

- **Read-Only by Default**: Most operations are read-only
- **Draft-Only Writes**: Invoice creation only creates drafts
- **No Auto-Posting**: Cannot post invoices without human approval
- **Credentials**: Store in environment variables, never in code
- **Local Network**: Recommended to run Odoo on local network only

## Troubleshooting

**Authentication Failed**
```
Error: Failed to authenticate with Odoo
```
- Verify ODOO_URL is correct
- Check ODOO_USERNAME and ODOO_PASSWORD
- Ensure Odoo is running

**Connection Refused**
```
Error: connect ECONNREFUSED
```
- Verify Odoo is running on specified URL
- Check firewall settings
- Ensure port 8069 is accessible

**Permission Denied**
```
Error: Access Denied
```
- User needs accounting access rights in Odoo
- Check user permissions in Odoo settings

## Odoo Setup

### Install Odoo Community Edition

```bash
# Docker installation (recommended)
docker run -d \
  --name odoo \
  -p 8069:8069 \
  -e POSTGRES_USER=odoo \
  -e POSTGRES_PASSWORD=odoo \
  odoo:19
```

### Create Database

1. Navigate to http://localhost:8069
2. Create new database
3. Install "Accounting" module
4. Configure chart of accounts

## Performance

- **API Calls**: ~100-200ms per call (local network)
- **Revenue Report**: ~500ms for 100 invoices
- **Invoice Creation**: ~300ms

## Future Enhancements

- Payment recording
- Bank reconciliation
- Customer management
- Product catalog integration
- Multi-currency support

---

**Part of Gold Tier - Personal AI Employee**
**Accounting Integration via MCP**
