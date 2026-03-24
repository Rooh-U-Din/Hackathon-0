# Quick Start Guide

## Bronze Tier - 5 Minute Setup

### Step 1: Install Dependencies
```bash
python setup.py
```

### Step 2: Start the Watcher
Open a terminal and run:
```bash
python watchers/filesystem_watcher.py AI_Employee_Vault
```

Keep this terminal open - it will monitor for new files.

### Step 3: Test the System
Open a new terminal and drop a test file:
```bash
echo "This is a test document" > AI_Employee_Vault/Inbox/test.txt
```

Check that an action file was created:
```bash
ls AI_Employee_Vault/Needs_Action/
```

### Step 4: Process with Claude Code
Navigate to the vault and run the skill:
```bash
cd AI_Employee_Vault
claude "Use the process-tasks skill to handle all pending items in Needs_Action folder. Read Company_Handbook.md for rules, process each task, and move completed items to Done folder. Update Dashboard.md with the results."
```

### Step 5: Verify Results
Check the Dashboard:
```bash
cat AI_Employee_Vault/Dashboard.md
```

Check completed tasks:
```bash
ls AI_Employee_Vault/Done/
```

## What Just Happened?

1. **Watcher** detected a new file in Inbox
2. **Watcher** created an action item in Needs_Action
3. **Claude Code** read the action item
4. **Claude Code** processed it according to handbook rules
5. **Claude Code** moved it to Done and updated Dashboard

## Next Steps

### Customize Your AI Employee
1. Edit `AI_Employee_Vault/Company_Handbook.md` with your rules
2. Add your business context and priorities
3. Define what requires approval vs auto-execution

### Add More Watchers (Silver Tier)
- Gmail watcher for email monitoring
- WhatsApp watcher for message monitoring
- Custom watchers for your specific needs

### Create More Skills
- Email response skill
- Report generation skill
- Social media posting skill

## Troubleshooting

**Watcher not detecting files?**
- Make sure you're dropping files in the Inbox folder
- Check the watcher terminal for error messages
- Verify folder permissions

**Claude Code not processing?**
- Make sure you're in the AI_Employee_Vault directory
- Check that the skill files exist in .claude/skills/
- Try running Claude Code directly with a prompt

**Files not moving to Done?**
- Claude Code needs explicit instruction to move files
- Check the Company_Handbook.md for processing rules
- Review the logs in /Logs folder

## Bronze Tier Checklist

- [x] Obsidian vault structure created
- [x] Dashboard.md and Company_Handbook.md exist
- [x] File system watcher implemented
- [x] Claude Code can read/write to vault
- [x] Basic workflow: Inbox → Needs_Action → Done
- [x] Agent skill created (process-tasks)

**🎉 Bronze Tier Complete!**

Ready to advance to Silver Tier? Add:
- Gmail or WhatsApp watcher
- MCP server for external actions
- Human-in-the-loop approval workflow
- Scheduled task automation
