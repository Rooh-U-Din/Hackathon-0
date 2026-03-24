# Approval Workflow Skill

Human-in-the-loop approval system for sensitive actions requiring human oversight.

## What this skill does

This skill manages the approval workflow:
1. Monitors /Pending_Approval folder for approval requests
2. Presents items to human for review
3. Processes approved items in /Approved folder
4. Handles rejected items in /Rejected folder
5. Executes approved actions safely
6. Logs all approval decisions

## When to use

Run this skill:
- To check pending approvals
- To execute approved actions
- As part of scheduled workflow
- Before sensitive operations

## Usage

```bash
# Check pending approvals
/approval-workflow --action check

# Execute all approved actions
/approval-workflow --action execute

# Approve specific item (moves to /Approved)
/approval-workflow --action approve --file "PAYMENT_client_a.md"

# Reject specific item (moves to /Rejected)
/approval-workflow --action reject --file "EMAIL_draft_123.md"
```

## Workflow

### 1. Check Pending Approvals

```bash
/approval-workflow --action check
```

**Output:**
- Lists all items in /Pending_Approval
- Shows priority, type, and summary
- Highlights items near expiration
- Provides quick approve/reject commands

### 2. Human Reviews and Decides

**To Approve:**
- Move file from /Pending_Approval to /Approved
- Or use: `/approval-workflow --action approve --file "filename.md"`

**To Reject:**
- Move file from /Pending_Approval to /Rejected
- Add rejection reason in file comments
- Or use: `/approval-workflow --action reject --file "filename.md"`

### 3. Execute Approved Actions

```bash
/approval-workflow --action execute
```

**Process:**
- Reads all files in /Approved
- Executes actions based on type
- Moves to /Done when complete
- Logs all executions

## Approval Request Types

### Email Sending
```markdown
---
type: email_send
to: client@example.com
subject: Invoice for January
priority: medium
expires: 2026-02-28T23:59:59Z
---

## Email Draft
[Email content]

## To Approve
Move to /Approved folder

## To Reject
Move to /Rejected folder with reason
```

### Payment Processing
```markdown
---
type: payment
amount: 500.00
recipient: Client A
account: XXXX1234
priority: high
expires: 2026-02-27T17:00:00Z
---

## Payment Details
- Amount: $500.00
- To: Client A
- Reference: Invoice #1234

## To Approve
Move to /Approved folder

## To Reject
Move to /Rejected folder with reason
```

### LinkedIn Post
```markdown
---
type: linkedin_post
priority: medium
scheduled_for: 2026-02-28T10:00:00Z
---

## Post Content
[Post text]

## To Approve
Move to /Approved folder

## To Reject
Move to /Rejected folder with feedback
```

### File Deletion
```markdown
---
type: file_deletion
files: ["old_data.csv", "temp_backup.zip"]
priority: low
---

## Files to Delete
- old_data.csv (2.5 MB)
- temp_backup.zip (150 MB)

## Reason
Cleanup old temporary files

## To Approve
Move to /Approved folder

## To Reject
Move to /Rejected folder
```

## Approval Rules (Company Handbook)

**Always Require Approval:**
- External communications (emails, messages)
- Financial transactions (payments, invoices)
- File deletions (permanent actions)
- Social media posts (public visibility)
- API calls to external services
- Database modifications

**Auto-Approve (No approval needed):**
- File organization (moving, renaming)
- Report generation (read-only)
- Dashboard updates (internal)
- Log entries (audit trail)
- Task status updates (workflow)

**Conditional Approval:**
- Small payments (< $50) to known vendors: Auto-approve
- Replies to known contacts: Auto-approve
- Scheduled posts (reviewed in advance): Auto-approve

## Expiration Handling

Approval requests can have expiration times:

```markdown
expires: 2026-02-27T17:00:00Z
```

**When expired:**
- Automatically moved to /Rejected
- Marked with "EXPIRED" status
- Logged for review
- Notification sent (if configured)

## Safety Features

**Pre-execution Validation:**
- Verify file is in /Approved folder
- Check approval timestamp is recent
- Validate action parameters
- Confirm no conflicts

**Dry-run Mode:**
- Test execution without actual action
- Log what would happen
- Verify safety

**Rollback Support:**
- Some actions support undo
- Logged for manual rollback
- Backup created when possible

## Execution by Type

### Email Sending
1. Read approved email draft
2. Connect to email MCP server
3. Send email via API
4. Log sent email
5. Move to /Done

### Payment Processing
1. Read approved payment request
2. Verify amount and recipient
3. Connect to payment system
4. Execute payment (or create draft)
5. Log transaction
6. Move to /Done

### LinkedIn Post
1. Read approved post content
2. Connect to LinkedIn (Playwright)
3. Create post
4. Verify published
5. Log post URL
6. Move to /Done

### File Deletion
1. Read approved deletion request
2. Verify files exist
3. Create backup (optional)
4. Delete files
5. Log deletion
6. Move to /Done

## Logging

All approval decisions are logged:

```json
{
  "timestamp": "2026-02-27T10:30:00Z",
  "action": "approval_granted",
  "type": "email_send",
  "file": "EMAIL_client_draft.md",
  "approved_by": "human",
  "executed": true,
  "result": "success"
}
```

## Configuration

Edit `Company_Handbook.md` to customize:
- Approval requirements by type
- Auto-approve thresholds
- Expiration times
- Notification preferences

## Security

- All approvals require human action
- No automatic approvals for sensitive actions
- Audit trail for all decisions
- Expiration prevents stale approvals
- Validation before execution

## Troubleshooting

**Approval not executing:**
- Verify file is in /Approved folder
- Check file format is correct
- Review logs for errors
- Ensure required services available

**Items expiring too quickly:**
- Adjust expiration times
- Check system clock
- Review approval frequency

**Accidental approval:**
- Move back to /Pending_Approval
- Or move to /Rejected
- Execution only happens on explicit command
