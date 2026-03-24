# Personal AI Employee - System Architecture

## Overview

This document describes the complete architecture of the Personal AI Employee system, covering all three tiers (Bronze, Silver, Gold) and explaining design decisions, data flows, and integration patterns.

---

## Architectural Principles

### 1. Local-First Design

**Principle**: All data stored locally, no cloud dependencies for core functionality.

**Benefits**:
- Complete data privacy and control
- No vendor lock-in
- Works offline
- No recurring cloud costs

**Implementation**:
- Obsidian vault as local knowledge base
- Local file system for state management
- Browser sessions stored locally
- MCP servers run locally

### 2. Modular Agent Skills

**Principle**: Each skill has single responsibility and can operate independently.

**Benefits**:
- Easy to test and debug
- Reusable components
- Clear separation of concerns
- Simple to add new skills

**Implementation**:
```
Skill Structure:
├── skill.py              # Thin entry point
├── {name}_skill.py       # Core logic class
├── skill.json            # Metadata
└── SKILL.md             # Documentation
```

### 3. Human-in-the-Loop (HITL)

**Principle**: Sensitive actions require explicit human approval.

**Benefits**:
- Safety and control
- Prevents costly mistakes
- Builds trust in automation
- Regulatory compliance

**Implementation**:
- Approval request files in /Pending_Approval
- Human moves to /Approved or /Rejected
- Orchestrator watches for approvals
- Audit log tracks all approvals

### 4. Event-Driven Architecture

**Principle**: Components react to events rather than polling continuously.

**Benefits**:
- Efficient resource usage
- Scalable design
- Loose coupling
- Easy to extend

**Implementation**:
- File system watcher detects new files
- Watchers create files that trigger processing
- MCP servers respond to tool calls
- Hooks intercept Claude Code events

---

## System Layers

### Layer 1: Perception (Watchers)

**Purpose**: Monitor external sources and create actionable files.

**Components**:
- Gmail Watcher
- LinkedIn Watcher
- Twitter Watcher
- Facebook Watcher
- Instagram Watcher
- File System Watcher

**Data Flow**:
```
External Source → Watcher → /Inbox/{TYPE}_{TIMESTAMP}_{ID}.md
```

**Design Decisions**:
- **Markdown format**: Human-readable, version-controllable
- **YAML frontmatter**: Structured metadata for parsing
- **Unique filenames**: Timestamp + ID prevents collisions
- **Processed IDs tracking**: Prevents duplicate processing

### Layer 2: Storage (Obsidian Vault)

**Purpose**: Central knowledge base and task management.

**Structure**:
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

**Design Decisions**:
- **Folder-based workflow**: Clear visual status
- **Markdown files**: Universal format, future-proof
- **Obsidian compatibility**: Rich GUI for humans
- **Git-friendly**: Version control ready

### Layer 3: Reasoning (Claude Code)

**Purpose**: Analyze tasks and make decisions.

**Components**:
- Claude Code CLI
- Ralph Wiggum Loop (autonomous execution)
- Context from vault files
- Company Handbook rules

**Processing Flow**:
```
1. Read files from /Needs_Action
2. Read Company_Handbook.md for rules
3. Analyze and decide action
4. Create plan or approval request
5. Execute or wait for approval
6. Move to /Done when complete
```

**Design Decisions**:
- **File-based context**: No database needed
- **Rule-based decisions**: Company Handbook guides behavior
- **Iterative processing**: Ralph Wiggum loop for multi-step tasks
- **Transparent reasoning**: Plans visible in /Plans folder

### Layer 4: Action (MCP Servers)

**Purpose**: Execute actions on external systems.

**Components**:
- Email MCP (send emails)
- Odoo MCP (accounting operations)
- WhatsApp MCP (messaging)
- Calendar MCP (event management)
- Browser MCP (web automation)

**Tool Call Flow**:
```
Claude Code → MCP Server → External API → Result → Claude Code
```

**Design Decisions**:
- **MCP protocol**: Standard interface for tools
- **Node.js servers**: Fast, async, good for I/O
- **JSON-RPC for Odoo**: Native Odoo integration
- **Playwright for social**: Reliable browser automation
- **Draft-only mode**: Sensitive operations require approval

### Layer 5: Orchestration

**Purpose**: Coordinate all components and ensure reliability.

**Components**:
- Scheduler (cron-like task scheduling)
- Watchdog (process health monitoring)
- Error Recovery (retry logic)
- Audit Logger (action tracking)

**Orchestration Flow**:
```
Scheduler → Trigger Watcher → Create Files → File System Watcher
    ↓
Detect New Files → Invoke Claude Code → Process Tasks
    ↓
Execute Actions via MCP → Log to Audit → Move to Done
    ↓
Watchdog monitors all processes → Restart on failure
```

**Design Decisions**:
- **Passive retry**: Don't hammer APIs, wait for next scheduled run
- **Process isolation**: Each watcher runs independently
- **Graceful degradation**: Queue operations when services unavailable
- **Comprehensive logging**: Every action audited

---

## Data Flow Patterns

### Pattern 1: Inbox Processing

```
External Source
    ↓
Watcher detects new item
    ↓
Create markdown file in /Inbox
    ↓
File System Watcher detects new file
    ↓
Create action item in /Needs_Action
    ↓
Claude Code processes action
    ↓
Execute via MCP or create approval request
    ↓
Move to /Done when complete
```

### Pattern 2: Approval Workflow

```
Claude identifies sensitive action
    ↓
Create approval request in /Pending_Approval
    ↓
Human reviews and moves to /Approved or /Rejected
    ↓
Orchestrator detects approval
    ↓
Execute action via MCP
    ↓
Log to audit trail
    ↓
Move to /Done
```

### Pattern 3: CEO Briefing Generation

```
Scheduler triggers weekly
    ↓
CEO Briefing skill reads:
  - Business_Goals.md (targets)
  - /Done folder (completed tasks)
  - Odoo MCP (revenue/expenses)
  - /Logs (transaction data)
    ↓
Analyze data and identify:
  - Revenue vs target
  - Bottlenecks
  - Cost optimization opportunities
    ↓
Generate briefing markdown
    ↓
Save to /Briefings folder
    ↓
Human reviews briefing
```

### Pattern 4: Ralph Wiggum Loop

```
Orchestrator creates state file
    ↓
Invoke Claude Code with task prompt
    ↓
Claude processes task
    ↓
Claude tries to exit
    ↓
Stop hook intercepts exit
    ↓
Check completion (file in /Done or promise in output)
    ↓
If incomplete: Block exit, re-inject prompt
    ↓
Claude continues working
    ↓
Repeat until complete or max iterations
```

---

## Integration Patterns

### Pattern 1: Watcher Integration

All watchers follow the same pattern:

```python
class BaseWatcher:
    def __init__(self, vault_path, session_path):
        self.inbox_path = vault_path / 'Inbox'
        self.processed_ids = self._load_processed_ids()

    def run(self):
        items = self.fetch_new_items()
        for item in items:
            if item['id'] not in self.processed_ids:
                self.create_inbox_file(item)
                self.processed_ids.add(item['id'])
        self._save_processed_ids()
```

**Benefits**:
- Consistent interface
- Easy to add new watchers
- Duplicate prevention built-in
- State persistence automatic

### Pattern 2: MCP Server Integration

All MCP servers follow the same pattern:

```javascript
class MCPServer {
    constructor() {
        this.tools = [/* tool definitions */];
    }

    async handleToolCall(toolName, params) {
        // Execute tool and return result
    }

    async start() {
        // Listen for MCP protocol messages
        process.stdin.on('data', async (data) => {
            const message = JSON.parse(data.toString());
            // Handle tools/list or tools/call
        });
    }
}
```

**Benefits**:
- Standard MCP protocol
- Easy to add new servers
- Type-safe tool definitions
- Async operation support

### Pattern 3: Skill Integration

All skills follow the same pattern:

```python
class Skill:
    def __init__(self, vault_path):
        self.vault_path = vault_path
        self.inbox_path = vault_path / 'Inbox'
        self.logs_path = vault_path / 'Logs'

    def run(self, **params):
        # Execute skill logic
        result = self.process()
        self.log_activity(result)
        return result
```

**Benefits**:
- Consistent interface
- Built-in logging
- Easy to test
- Reusable components

---

## Security Architecture

### Credential Management

**Storage**:
- Environment variables for API keys
- OS keychain for sensitive credentials
- .env files (gitignored) for local development
- Browser sessions in separate directories

**Access Control**:
- Read-only API access where possible
- Minimal permissions principle
- No credentials in code or logs
- Automatic credential rotation reminders

### Approval Boundaries

| Action Type | Auto-Approve | Require Approval |
|-------------|--------------|------------------|
| Read operations | ✅ | ❌ |
| Email to known contacts | ✅ | ❌ |
| Email to new contacts | ❌ | ✅ |
| Social media posts | ✅ | ❌ |
| Payments < $50 | ❌ | ✅ |
| Payments ≥ $50 | ❌ | ✅ |
| File create/read | ✅ | ❌ |
| File delete | ❌ | ✅ |

### Audit Trail

**What is logged**:
- Every action with timestamp
- Actor (which component)
- Target (what was acted upon)
- Parameters (action details)
- Approval status
- Result (success/failure)

**Retention**:
- 90 days minimum
- Daily rotation
- JSON format for parsing
- Audit reports on demand

---

## Scalability Considerations

### Current Limits

- **Watchers**: 5-10 concurrent watchers
- **Tasks per day**: 100-500 tasks
- **Vault size**: Up to 10,000 files
- **MCP servers**: 5-10 concurrent servers

### Scaling Strategies

**Horizontal Scaling**:
- Run multiple watcher instances
- Distribute MCP servers across machines
- Use message queue for task distribution

**Vertical Scaling**:
- Increase check intervals
- Batch processing
- Optimize file I/O
- Cache frequently accessed data

**Cloud Scaling** (Platinum Tier):
- Deploy watchers to cloud VM
- Use cloud storage for vault sync
- Implement load balancing
- Add redundancy and failover

---

## Technology Stack

### Languages

- **Python 3.13+**: Watchers, skills, core infrastructure
- **Node.js 24+**: MCP servers
- **Bash**: Orchestration scripts

### Key Libraries

**Python**:
- playwright: Browser automation
- google-api-python-client: Gmail API
- psutil: Process management
- pathlib: File operations

**Node.js**:
- playwright: Browser automation
- xmlrpc: Odoo integration

### Tools

- **Claude Code**: AI reasoning engine
- **Obsidian**: Knowledge base GUI
- **Git**: Version control
- **PM2**: Process management (optional)

---

## Design Trade-offs

### Trade-off 1: Local vs Cloud

**Decision**: Local-first architecture

**Pros**:
- Complete privacy
- No recurring costs
- Works offline
- No vendor lock-in

**Cons**:
- Requires local machine running
- No automatic backups
- Limited to single machine (Bronze/Silver/Gold)

**Mitigation**: Platinum tier adds cloud option

### Trade-off 2: File-based vs Database

**Decision**: File-based storage (markdown)

**Pros**:
- Human-readable
- Version control friendly
- No database setup
- Universal format

**Cons**:
- Slower for large datasets
- No complex queries
- Manual indexing needed

**Mitigation**: Acceptable for <10,000 files

### Trade-off 3: Browser Automation vs APIs

**Decision**: Browser automation for social media

**Pros**:
- No API keys needed
- Works with any platform
- Bypasses API limitations

**Cons**:
- Slower than APIs
- Fragile (UI changes break it)
- Requires visible browser for some platforms

**Mitigation**: Use APIs where available (Gmail, Odoo)

---

## Future Architecture Evolution

### Phase 1: Current (Gold Tier)

- Local-only operation
- Single machine
- Manual monitoring

### Phase 2: Platinum Tier

- Cloud + Local hybrid
- Vault syncing
- 24/7 operation
- Health monitoring

### Phase 3: Enterprise

- Multi-user support
- Team collaboration
- Role-based access
- Centralized management

### Phase 4: AI Agent Network

- Multiple specialized agents
- Agent-to-agent communication
- Distributed task processing
- Emergent behaviors

---

## Conclusion

The Personal AI Employee architecture is designed for:

✅ **Privacy**: Local-first, no cloud dependencies
✅ **Modularity**: Easy to extend and maintain
✅ **Reliability**: Error recovery and health monitoring
✅ **Security**: HITL approvals and audit logging
✅ **Scalability**: Can grow from personal to enterprise use

The architecture balances simplicity with power, making it accessible for individual users while providing a foundation for future growth.

---

*Personal AI Employee - System Architecture*
*Gold Tier Implementation*
*Local-First, Modular, Secure*
