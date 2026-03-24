# Process Tasks Skill

Process all pending tasks in the Needs_Action folder according to the Company Handbook rules.

## What this skill does

This skill automates the task processing workflow:
1. Reads all files in the `/Needs_Action` folder
2. Reviews each task according to `Company_Handbook.md` guidelines
3. Creates action plans for multi-step tasks in `/Plans`
4. Moves completed simple tasks to `/Done`
5. Creates approval requests in `/Pending_Approval` for sensitive actions
6. Updates the `Dashboard.md` with current status

## When to use

Run this skill when:
- New files appear in `/Needs_Action` (triggered by watchers)
- You want to process pending tasks manually
- After approving items in `/Approved` folder

## Usage

```bash
/process-tasks
```

Or with specific focus:

```bash
/process-tasks --priority high
```

## Workflow

1. **Read Context:**
   - Load `Company_Handbook.md` for rules
   - Load `Dashboard.md` for current state
   - Scan `/Needs_Action` for pending items

2. **Process Each Task:**
   - Determine task type and priority
   - Check if approval is required
   - Create plan if multi-step task
   - Execute or request approval

3. **Update State:**
   - Move completed tasks to `/Done`
   - Update `Dashboard.md`
   - Log actions to `/Logs`

## Examples

### Simple Task (Auto-complete)
- File organization
- Report generation
- Status updates

### Approval Required
- External communications
- Financial transactions
- File deletions

### Multi-step Task
- Complex workflows requiring planning
- Tasks with dependencies
- Long-running operations
