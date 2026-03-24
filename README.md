# Personal AI Employee - Platinum Tier ✅

A cloud-local hybrid AI employee system built with Claude Code and Obsidian for autonomous task management, business intelligence, and 24/7 operation.

**Status:** Platinum Tier Complete (Bronze ✅ | Silver ✅ | Gold ✅ | Platinum ✅)

## Overview

The Personal AI Employee is a production-ready autonomous system that monitors your business and personal affairs 24/7, processes tasks according to your rules, and provides proactive insights through weekly CEO briefings.

### Key Features

#### Gold Tier Features
- **15 Agent Skills** - Modular automation across email, social media, and business intelligence
- **5 MCP Servers** - External integrations for email, accounting, messaging, and calendar
- **CEO Briefing Generator** - Weekly business audit with revenue analysis and cost optimization
- **Social Media Integration** - Twitter, Facebook, Instagram monitoring and posting
- **Odoo Accounting** - Real-time financial data via JSON-RPC API
- **Error Recovery** - Exponential backoff retry and graceful degradation
- **Audit Logging** - Complete action tracking for compliance
- **Ralph Wiggum Loop** - Autonomous multi-step task completion
- **Process Monitoring** - Watchdog for automatic restart and health checks

#### Platinum Tier Features (NEW)
- **Cloud-Local Hybrid Architecture** - 24/7 cloud operation with local execution
- **Vault Synchronization** - Git-based sync between cloud and local with security boundaries
- **Draft-Only Cloud Agent** - Cloud creates drafts, never executes sensitive actions
- **Approval Workflow** - Human-in-the-loop for all sensitive operations
- **Work-Zone Specialization** - Cloud handles drafts, local handles execution
- **Security Boundaries** - Secrets never leave local machine
- **Agent Coordination** - Claim-by-move pattern prevents double-work
- **Offline Handling** - Cloud operates even when local machine is offline
- **Oracle Cloud Deployment** - Free tier VM deployment with automated setup
- **Complete Documentation** - Deployment guides, security architecture, and troubleshooting

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 24+
- Claude Code CLI
- Obsidian (optional, for GUI)

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd Hackathon-0

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Install MCP server dependencies
cd mcp-servers/odoo-mcp && npm install && cd ../..
cd mcp-servers/whatsapp-mcp && npm install && cd ../..
cd mcp-servers/calendar-mcp && npm install && cd ../..
```

### First Run

```bash
# 1. Test Gmail watcher (requires credentials.json)
python .claude/skills/gmail-watcher/skill.py --max-emails 3

# 2. Test CEO briefing generator
python .claude/skills/ceo-briefing/skill.py

# 3. Start the scheduler
python scheduler.py
```

## Architecture

### Platinum Tier: Cloud-Local Hybrid

```
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD VM (24/7)                          │
│  - Draft-only operations (no sending/posting)               │
│  - Email triage and reply drafting                          │
│  - Social post drafting                                     │
│  - Read-only Odoo access                                    │
│  - Writes to /Updates/ folder                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              VAULT SYNCHRONIZATION (Git)                    │
│  - Syncs every 5 minutes                                    │
│  - Excludes secrets (.env, sessions, tokens)                │
│  - Conflict resolution with rebase                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  LOCAL MACHINE (On-Demand)                  │
│  - Approval workflow processing                             │
│  - WhatsApp sessions (LOCAL ONLY)                           │
│  - Payment execution (LOCAL ONLY)                           │
│  - Final send/post actions                                  │
│  - Merges /Updates/ into Dashboard.md                       │
└─────────────────────────────────────────────────────────────┘
```

### Gold Tier: Local-First System

```
External Sources (Gmail, LinkedIn, Twitter, Facebook, Instagram, Odoo)
    ↓
Perception Layer (15 Agent Skills - Watchers + Posters + Generators)
    ↓
Storage Layer (Obsidian Vault - /Inbox → /Needs_Action → /Done)
    ↓
Reasoning Layer (Claude Code + Ralph Wiggum Loop)
    ↓
Action Layer (5 MCP Servers - Email, Odoo, WhatsApp, Calendar, Browser)
    ↓
Orchestration Layer (Scheduler, Watchdog, Error Recovery, Audit Logger)
```

## Agent Skills (15 Total)

### Bronze Tier (1)
1. **filesystem-watcher** - Monitors vault for new files

### Silver Tier (6)
2. **gmail-watcher** - Monitors Gmail inbox
3. **linkedin-watcher** - Monitors LinkedIn notifications
4. **linkedin-poster** - Posts to LinkedIn
5. **plan-generator** - Creates implementation plans
6. **approval-workflow** - Human-in-the-loop approvals
7. **email-mcp** - Email sending wrapper

### Gold Tier (8)
8. **ceo-briefing** - Weekly business audit and briefing
9. **twitter-watcher** - Monitors Twitter mentions
10. **twitter-poster** - Posts tweets and threads
11. **facebook-watcher** - Monitors Facebook notifications
12. **facebook-poster** - Posts to Facebook
13. **instagram-watcher** - Monitors Instagram DMs
14. **instagram-poster** - Posts to Instagram
15. **whatsapp-watcher** - Monitors WhatsApp messages

## MCP Servers (5 Total)

1. **email-mcp** - Send and manage emails via Gmail API
2. **odoo-mcp** - Accounting integration with Odoo Community Edition
3. **whatsapp-mcp** - WhatsApp messaging via browser automation
4. **calendar-mcp** - Calendar event management
5. **browser-mcp** - General browser automation (Anthropic official)

## Core Infrastructure

- **error_recovery.py** - Retry logic with exponential backoff
- **audit_logger.py** - Comprehensive action logging
- **watchdog.py** - Process health monitoring
- **scheduler.py** - Task scheduling and orchestration
- **ralph_wiggum_stop.py** - Autonomous task completion hook

## Vault Structure

```
AI_Employee_Vault/
├── Inbox/                  # New items from watchers
├── Needs_Action/           # Tasks requiring processing
├── Done/                   # Completed tasks
├── Pending_Approval/       # Awaiting human approval
├── Approved/               # Approved actions
├── Rejected/               # Rejected actions
├── Briefings/              # CEO briefings
├── Plans/                  # Implementation plans
├── Logs/                   # Activity logs
│   └── Audit/             # Audit trail
├── Company_Handbook.md     # Business rules
├── Business_Goals.md       # Targets and metrics
└── Dashboard.md           # Real-time summary
```

## Platinum Tier: Cloud Deployment

### Quick Deploy to Oracle Cloud

```bash
# 1. SSH to your Oracle Cloud VM
ssh ubuntu@<VM_PUBLIC_IP>

# 2. Clone repository
git clone <your-repo-url>
cd Hackathon-0

# 3. Run automated deployment
cd platinum/deployment
chmod +x deploy.sh
./deploy.sh

# 4. Configure credentials
nano platinum/cloud-agent/.env
# Update ODOO credentials

# 5. Restart services
sudo systemctl restart cloud-agent
sudo systemctl restart vault-sync
```

### Platinum Demo (Minimum Passing Gate)

```bash
# Run the demo to verify cloud-local coordination
python3 platinum/demo/platinum_demo.py --vault ./AI_Employee_Vault

# Expected: Email arrives → Cloud drafts → User approves → Local sends
```

### Monitor Cloud Agent

```bash
# View cloud agent logs
sudo journalctl -u cloud-agent -f

# View vault sync logs
sudo journalctl -u vault-sync -f

# Check service status
sudo systemctl status cloud-agent vault-sync
```

## Usage Examples

### CEO Briefing

```bash
# Generate weekly briefing
python .claude/skills/ceo-briefing/skill.py --period-days 7

# View briefing
cat AI_Employee_Vault/Briefings/2026-02-27_Monday_Briefing.md
```

### Social Media Monitoring

```bash
# Twitter (first run requires login)
python .claude/skills/twitter-watcher/skill.py --headless false

# Facebook
python .claude/skills/facebook-watcher/skill.py --headless false

# Instagram
python .claude/skills/instagram-watcher/skill.py --headless false
```

### Social Media Posting

```bash
# Post to Twitter
python .claude/skills/twitter-poster/skill.py --content "Great insights on AI automation!"

# Post to Facebook
python .claude/skills/facebook-poster/skill.py --content "Check out our latest blog post"

# Post to Instagram (requires image)
python .claude/skills/instagram-poster/skill.py --caption "New product launch" --image ./photo.jpg
```

### Odoo Integration

```bash
# Start Odoo MCP server
cd mcp-servers/odoo-mcp
ODOO_URL=http://localhost:8069 ODOO_DB=odoo ODOO_USERNAME=admin ODOO_PASSWORD=admin node index.js
```

### Ralph Wiggum Loop

```bash
# Start autonomous task completion
python .claude/hooks/ralph_loop_start.py \
  "Process all files in /Needs_Action, move to /Done when complete" \
  --completion-mode file \
  --max-iterations 10

# Then invoke Claude
claude "Process all files in /Needs_Action according to Company_Handbook.md"
```

### Watchdog Monitoring

```bash
# Start process health monitor
python watchdog.py --vault ./AI_Employee_Vault --interval 60
```

## Configuration

### MCP Servers

Edit `~/.config/claude-code/mcp.json`:

```json
{
  "servers": [
    {
      "name": "email",
      "command": "python",
      "args": ["D:/vsCode/CLI/Hackathon-0/mcp-servers/email-mcp/server.py"],
      "env": {
        "GMAIL_CREDENTIALS": "D:/vsCode/CLI/Hackathon-0/credentials.json"
      }
    },
    {
      "name": "odoo",
      "command": "node",
      "args": ["D:/vsCode/CLI/Hackathon-0/mcp-servers/odoo-mcp/index.js"],
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

### Scheduler

Edit `scheduler.py` to configure check intervals:

```python
# Gmail every 15 minutes
schedule.every(15).minutes.do(check_gmail)

# LinkedIn every 30 minutes
schedule.every(30).minutes.do(check_linkedin)

# CEO briefing every Monday at 7 AM
schedule.every().monday.at("07:00").do(generate_ceo_briefing)
```

## Documentation

### Getting Started
- **README.md** (this file) - Overview and quick start
- **QUICKSTART_WATCHERS.md** - 5-minute watcher setup
- **WATCHER_INTEGRATION_GUIDE.md** - Complete integration guide

### Architecture & Design
- **ARCHITECTURE.md** - Complete system architecture
- **GOLD_TIER_COMPLETION.md** - Gold Tier deliverables summary
- **PLATINUM_TIER_COMPLETION.md** - Platinum Tier deliverables summary
- **LESSONS_LEARNED.md** - Insights and best practices

### Platinum Tier Guides
- **CLOUD_DEPLOYMENT_GUIDE.md** - Step-by-step Oracle Cloud deployment
- **VAULT_SYNC_GUIDE.md** - Vault synchronization setup and troubleshooting
- **SECURITY_ARCHITECTURE.md** - Security boundaries and threat model
- **PLATINUM_DEMO_GUIDE.md** - Running the minimum passing gate demo

### Component Documentation
- Each skill has detailed **SKILL.md** documentation
- Each MCP server has **README.md** with API reference
- **RALPH_WIGGUM_README.md** - Autonomous task completion guide

## Tier Completion Checklists

### Bronze Tier ✅
- [x] Obsidian vault with Dashboard.md and Company_Handbook.md
- [x] One working Watcher script (File System monitoring)
- [x] Claude Code can read from and write to the vault
- [x] Basic folder structure: /Inbox, /Needs_Action, /Done
- [x] All AI functionality implemented as Agent Skills

### Silver Tier ✅
- [x] All Bronze requirements
- [x] Two or more Watcher scripts (Gmail + LinkedIn + FileSystem)
- [x] LinkedIn posting automation
- [x] Plan generation for multi-step tasks
- [x] MCP server for external actions (Email)
- [x] Human-in-the-loop approval workflow
- [x] Basic scheduling (scheduler.py)
- [x] All AI functionality as Agent Skills

### Gold Tier ✅
- [x] All Silver requirements
- [x] Full cross-domain integration (Personal + Business)
- [x] Odoo accounting integration via MCP server
- [x] Facebook and Instagram integration (4 skills)
- [x] Twitter (X) integration (2 skills)
- [x] Multiple MCP servers (5 total)
- [x] Weekly CEO Briefing generation
- [x] Error recovery and graceful degradation
- [x] Comprehensive audit logging
- [x] Ralph Wiggum loop for autonomous completion
- [x] Complete documentation
- [x] All AI functionality as Agent Skills

### Platinum Tier ✅
- [x] All Gold requirements
- [x] Cloud agent running 24/7 (draft-only operations)
- [x] Local agent for approvals and execution
- [x] Vault synchronization with Git (security boundaries)
- [x] Work-zone specialization (cloud drafts, local executes)
- [x] Claim-by-move agent coordination
- [x] Security rule: secrets never sync to cloud
- [x] Odoo deployed on cloud VM (Docker)
- [x] Platinum demo (minimum passing gate)
- [x] Cloud deployment infrastructure (systemd, docker-compose)
- [x] Complete documentation (5 guides)

## Security

### Credentials Management
- All credentials in environment variables or .env files
- No credentials in code or git
- .gitignore configured for sensitive files
- Session files excluded from version control

### Approval Workflow
- Payments require human approval
- Emails to new contacts require approval
- Bulk operations require approval
- Audit trail tracks all approvals

### Audit Logging
- Every action logged with timestamp
- Actor and target identification
- Approval status tracking
- 90-day retention minimum

## Performance

### Watcher Performance
- Gmail: ~7s for 10 emails
- LinkedIn: ~8s for 10 notifications
- Twitter: ~8s for 10 mentions
- Facebook: ~8s for 10 notifications
- Instagram: ~8s for 10 items

### CEO Briefing
- Execution time: ~3-5 seconds
- Memory usage: ~30MB
- Processes 100+ tasks and 50+ transactions

## Troubleshooting

### Watchers Not Working
```bash
# Check if session exists
ls -la *_session/

# Re-login with visible browser
python .claude/skills/twitter-watcher/skill.py --headless false
```

### MCP Server Connection Failed
```bash
# Check server is running
ps aux | grep mcp

# Test server manually
node mcp-servers/odoo-mcp/index.js
```

### Ralph Wiggum Loop Not Stopping
```bash
# Check state file
cat .ralph_state.json

# Check max iterations
# Increase if needed in ralph_loop_start.py
```

## Next Steps

### Custom Extensions
- Add more watchers (Slack, Telegram, Discord)
- Integrate with more services (Notion, Airtable)
- Build custom MCP servers
- Create specialized skills for your business

### Advanced Platinum Features
- Multi-region cloud deployment for redundancy
- Mobile approval app (iOS/Android)
- Agent-to-agent communication (A2A)
- Advanced analytics and cost optimization

## Contributing

This is a hackathon project built for Panaversity Hackathon 0. Feel free to fork and customize for your needs.

## License

MIT License

## Acknowledgments

- Built with Claude Code and Anthropic's Agent Skills framework
- Inspired by the "Personal AI Employee" hackathon challenge
- Uses Playwright for browser automation
- Integrates with Odoo Community Edition for accounting

---

**Status: Platinum Tier Complete ✅**
**15 Agent Skills | 5 MCP Servers | Cloud-Local Hybrid**
**24/7 Operation | Secure | Production Ready**
