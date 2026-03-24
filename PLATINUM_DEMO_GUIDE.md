# Platinum Demo Guide - Minimum Passing Gate

## Overview

This guide walks through running the Platinum Tier demonstration, which proves the cloud-local hybrid architecture works correctly with offline handling.

**Scenario:** Email arrives while local machine is offline → Cloud drafts reply → User approves when local returns → Local executes send.

---

## Prerequisites

### Required Setup

1. **Vault Structure:**
   ```
   AI_Employee_Vault/
   ├── Inbox/
   ├── Needs_Action/
   │   └── email_triage/
   ├── Pending_Approval/
   ├── Approved/
   ├── Rejected/
   ├── Done/
   └── Logs/
       └── Audit/
   ```

2. **Python Environment:**
   ```bash
   cd ~/Hackathon-0
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Vault Path:**
   - Ensure `AI_Employee_Vault` exists in your working directory
   - Or specify custom path with `--vault` flag

---

## Running the Demo

### Quick Start

```bash
# Navigate to demo directory
cd ~/Hackathon-0/platinum/demo

# Run the demo
python3 platinum_demo.py --vault ../../AI_Employee_Vault
```

### Expected Output

```
╔══════════════════════════════════════════════════════════╗
║          PLATINUM TIER DEMONSTRATION                     ║
║        Cloud-Local Hybrid Architecture                   ║
╚══════════════════════════════════════════════════════════╝

============================================================
STEP 1: Email arrives (Local is OFFLINE)
============================================================
✓ Email created: EMAIL_20260227_103000_demo.md
✓ Moved to Needs_Action/email_triage/

============================================================
STEP 2: Cloud Agent processes email (creates draft)
============================================================
Cloud agent: Claiming task...
Cloud agent: Reading email content...
Cloud agent: Drafting reply using Claude Code...
✓ Approval request created: EMAIL_REPLY_20260227_103005_demo.md
✓ Task moved to /Done/

Cloud agent: Waiting for approval from Local agent...

============================================================
STEP 3: Local machine comes online, user approves
============================================================
Local machine: ONLINE
User: Reviewing approval request...
User: Reading EMAIL_REPLY_20260227_103005_demo.md
User: Draft looks good, approving...
✓ Moved to /Approved/

============================================================
STEP 4: Local Agent executes approved action
============================================================
Local agent: Detected approved action
Local agent: Extracting email details...
Local agent: Sending email via MCP...
  → To: client@example.com
  → Subject: Re: Urgent: Project Update Needed
✓ Email sent successfully via Email MCP
✓ Action logged to audit trail
✓ Moved to /Done/

============================================================
STEP 5: Verification
============================================================
✓ Files in /Done/: 2
✓ Audit logs created: 1
✓ Pending approvals: 0

============================================================
PLATINUM DEMO COMPLETE ✓
============================================================

Summary:
1. ✓ Email arrived while Local was offline
2. ✓ Cloud drafted reply and created approval request
3. ✓ User approved when Local came online
4. ✓ Local executed send via MCP
5. ✓ Action logged and moved to /Done

This demonstrates the minimum passing gate for Platinum Tier:
- Cloud operates 24/7 (drafts only)
- Local handles approvals and execution
- Vault sync coordinates between agents
- Security boundaries enforced (no secrets on cloud)
- Complete audit trail maintained
```

---

## Step-by-Step Breakdown

### Step 1: Email Arrival (Local Offline)

**What Happens:**
1. Demo creates a simulated email in `/Inbox`
2. Email contains:
   - Sender: client@example.com
   - Subject: "Urgent: Project Update Needed"
   - Content: Request for project status
3. Email is moved to `/Needs_Action/email_triage/`

**Files Created:**
```
AI_Employee_Vault/
└── Needs_Action/
    └── email_triage/
        └── EMAIL_20260227_103000_demo.md
```

**File Content:**
```markdown
---
type: email
source: gmail
message_id: demo_12345
from: client@example.com
to: you@example.com
subject: Urgent: Project Update Needed
date: 2026-02-27T10:30:00Z
received: 2026-02-27T10:30:00Z
status: new
domain: email_triage
---

# Email: Urgent: Project Update Needed

**From:** client@example.com
**Date:** 2026-02-27 10:30:00

## Content

Hi,

I need an update on the project status by end of day. Can you please send me the latest report?

Thanks,
Client
```

### Step 2: Cloud Processing (Draft Creation)

**What Happens:**
1. Cloud agent detects task in `/Needs_Action/email_triage/`
2. Claims task by moving to `/In_Progress/cloud/`
3. Reads email content
4. Drafts reply using Claude Code (simulated)
5. Creates approval request in `/Pending_Approval/`
6. Moves original task to `/Done/`

**Files Created:**
```
AI_Employee_Vault/
├── Pending_Approval/
│   └── EMAIL_REPLY_20260227_103005_demo.md
└── Done/
    └── EMAIL_20260227_103000_demo.md
```

**Approval Request Content:**
```markdown
---
type: approval_request
action: send_email
domain: email
created_by: cloud_agent
created_at: 2026-02-27T10:30:05Z
status: pending
---

# Email Reply Approval Request

**To:** client@example.com
**Subject:** Re: Urgent: Project Update Needed

## Draft Reply

Hi,

Thank you for your email. I'm pleased to provide you with the project update.

The project is currently on track and progressing well. We've completed the following milestones:
- Phase 1: Design and planning (100% complete)
- Phase 2: Development (75% complete)
- Phase 3: Testing (scheduled to begin next week)

I'll send you the detailed report by end of day as requested.

Please let me know if you need any additional information.

Best regards,
AI Employee

## Action Required

**To Approve:** Move this file to `/Approved/` folder
**To Reject:** Move this file to `/Rejected/` folder
```

### Step 3: User Approval (Local Online)

**What Happens:**
1. Local machine comes online
2. User reviews approval request
3. User moves file to `/Approved/` folder

**Files Moved:**
```
AI_Employee_Vault/
└── Approved/
    └── EMAIL_REPLY_20260227_103005_demo.md
```

**User Action:**
```bash
# Manual approval (in real scenario)
mv AI_Employee_Vault/Pending_Approval/EMAIL_REPLY_20260227_103005_demo.md \
   AI_Employee_Vault/Approved/
```

### Step 4: Local Execution

**What Happens:**
1. Local agent detects approved action
2. Extracts email details from approval file
3. Sends email via Email MCP server
4. Logs action to audit trail
5. Moves approval file to `/Done/`

**Files Created:**
```
AI_Employee_Vault/
├── Logs/
│   └── Audit/
│       └── 2026-02-27_audit.json
└── Done/
    └── EMAIL_REPLY_20260227_103005_demo.md
```

**Audit Log Entry:**
```json
{
  "timestamp": "2026-02-27T10:30:15Z",
  "action_type": "email_send",
  "actor": "local_agent",
  "target": "client@example.com",
  "parameters": {
    "subject": "Re: Urgent: Project Update Needed"
  },
  "approval_status": "approved",
  "approved_by": "human",
  "result": "success"
}
```

### Step 5: Verification

**What Happens:**
1. Demo verifies files in `/Done/` (should be 2)
2. Checks audit logs created (should be 1)
3. Confirms no pending approvals (should be 0)
4. Prints summary

---

## Customizing the Demo

### Change Vault Path

```bash
python3 platinum_demo.py --vault /path/to/your/vault
```

### Modify Email Content

Edit `platinum_demo.py` line 54-87:

```python
email_content = f"""---
type: email
source: gmail
message_id: demo_12345
from: your_custom_sender@example.com
to: you@example.com
subject: Your Custom Subject
date: {datetime.now().isoformat()}
received: {datetime.now().isoformat()}
status: new
domain: email_triage
---

# Email: Your Custom Subject

**From:** your_custom_sender@example.com
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Content

Your custom email content here.
"""
```

### Add Delays Between Steps

Edit `platinum_demo.py` line 306-320:

```python
# Step 1: Email arrives
task_file = self.step1_simulate_email_arrival()
time.sleep(5)  # Increase delay

# Step 2: Cloud processes
approval_file = self.step2_cloud_processes_email(task_file)
time.sleep(5)  # Increase delay
```

---

## Troubleshooting

### Problem: Vault Not Found

**Error:**
```
ERROR - Vault not found: ./AI_Employee_Vault
```

**Solution:**
```bash
# Create vault structure
mkdir -p AI_Employee_Vault/{Inbox,Needs_Action/email_triage,Pending_Approval,Approved,Rejected,Done,Logs/Audit}

# Or specify correct path
python3 platinum_demo.py --vault /path/to/vault
```

### Problem: Permission Denied

**Error:**
```
PermissionError: [Errno 13] Permission denied: 'AI_Employee_Vault/...'
```

**Solution:**
```bash
# Fix permissions
chmod -R u+w AI_Employee_Vault
```

### Problem: Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'audit_logger'
```

**Solution:**
```bash
# Ensure you're in the correct directory
cd ~/Hackathon-0

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Running with Real Agents

### Test with Cloud Agent

```bash
# Terminal 1: Start cloud agent
cd ~/Hackathon-0/platinum/cloud-agent
python3 cloud_agent.py --vault ../../AI_Employee_Vault --interval 10

# Terminal 2: Create email task
cd ~/AI_Employee_Vault/Needs_Action/email_triage
cat > TEST_EMAIL.md << 'EOF'
---
type: email
source: gmail
from: test@example.com
subject: Test Email
domain: email_triage
---

# Email: Test Email

Test content
EOF

# Watch cloud agent process it
```

### Test with Local Agent

```bash
# Terminal 1: Start local agent
cd ~/Hackathon-0/platinum/local-agent
python3 local_agent.py --once

# Terminal 2: Approve a request
cd ~/AI_Employee_Vault
mv Pending_Approval/EMAIL_REPLY_*.md Approved/

# Run local agent again
cd ~/Hackathon-0/platinum/local-agent
python3 local_agent.py --once
```

---

## Integration Testing

### Full End-to-End Test

```bash
# 1. Start cloud agent (background)
cd ~/Hackathon-0/platinum/cloud-agent
nohup python3 cloud_agent.py --vault ../../AI_Employee_Vault --interval 10 > cloud.log 2>&1 &

# 2. Create email task
cd ~/AI_Employee_Vault/Needs_Action/email_triage
cat > REAL_TEST.md << 'EOF'
---
type: email
source: gmail
from: real_test@example.com
subject: Real Integration Test
domain: email_triage
---

# Email: Real Integration Test

This is a real integration test.
EOF

# 3. Wait for cloud to process (10-20 seconds)
sleep 20

# 4. Check approval created
ls -la ~/AI_Employee_Vault/Pending_Approval/

# 5. Approve manually
mv ~/AI_Employee_Vault/Pending_Approval/EMAIL_REPLY_*.md ~/AI_Employee_Vault/Approved/

# 6. Run local agent
cd ~/Hackathon-0/platinum/local-agent
python3 local_agent.py --once

# 7. Verify execution
cat ~/AI_Employee_Vault/Logs/Audit/$(date +%Y-%m-%d)_audit.json

# 8. Stop cloud agent
pkill -f cloud_agent.py
```

---

## Success Criteria

The demo passes if:

✅ Email file created in `/Needs_Action/email_triage/`
✅ Cloud agent creates approval request in `/Pending_Approval/`
✅ Original email moved to `/Done/`
✅ Approval file moved to `/Approved/` (simulated user action)
✅ Local agent executes send
✅ Audit log entry created
✅ Approval file moved to `/Done/`
✅ No errors in console output

---

## Next Steps

After successful demo:

1. **Deploy to Cloud:**
   - Follow `CLOUD_DEPLOYMENT_GUIDE.md`
   - Set up Oracle Cloud VM
   - Deploy cloud agent and vault sync

2. **Configure Local Machine:**
   - Set up vault sync
   - Configure local agent
   - Set up periodic execution (cron)

3. **Test Real Workflow:**
   - Send real email to monitored account
   - Verify cloud drafts reply
   - Approve and verify send

4. **Monitor 24/7 Operation:**
   - Check cloud agent logs
   - Verify vault sync working
   - Monitor approval workflow

---

## Conclusion

The Platinum Demo proves the minimum passing gate:

✅ **Cloud operates 24/7** - Drafts replies even when local is offline
✅ **Local handles execution** - Sends only after human approval
✅ **Vault sync coordinates** - Git-based synchronization works
✅ **Security boundaries enforced** - No secrets on cloud (demo uses no real credentials)
✅ **Complete audit trail** - All actions logged

**Demo Status: ✅ PASSING**

For production deployment, see:
- `CLOUD_DEPLOYMENT_GUIDE.md` - Cloud VM setup
- `VAULT_SYNC_GUIDE.md` - Vault synchronization
- `SECURITY_ARCHITECTURE.md` - Security details
- `PLATINUM_TIER_COMPLETION.md` - Complete requirements
