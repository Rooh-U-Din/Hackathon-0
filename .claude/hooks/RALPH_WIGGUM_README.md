# Ralph Wiggum Loop - Autonomous Task Completion

## Overview

The Ralph Wiggum Loop is a stop hook pattern that keeps Claude Code working autonomously until a task is complete. It prevents Claude from exiting after processing a prompt, re-injecting the task until completion is detected.

## How It Works

1. **Orchestrator creates state file** with task prompt
2. **Claude works on task** and tries to exit
3. **Stop hook intercepts exit** and checks completion
4. **If incomplete**: Block exit, re-inject prompt, Claude continues
5. **If complete**: Allow exit, clean up state
6. **Repeat** until complete or max iterations reached

## Completion Strategies

### 1. File Movement (Recommended for Gold Tier)

Task is complete when file moves to `/Done` folder.

**Advantages:**
- More reliable (completion is natural part of workflow)
- No special output format required
- Works with existing vault structure

**Usage:**
```bash
python .claude/hooks/ralph_loop_start.py \
  "Process all files in /Needs_Action, move to /Done when complete" \
  --completion-mode file \
  --task-file "AI_Employee_Vault/Needs_Action/TASK_123.md" \
  --max-iterations 10
```

### 2. Promise-Based (Simple)

Claude outputs `<promise>TASK_COMPLETE</promise>` when done.

**Advantages:**
- Simple to implement
- Explicit completion signal

**Usage:**
```bash
python .claude/hooks/ralph_loop_start.py \
  "Analyze data and output TASK_COMPLETE when done" \
  --completion-mode promise \
  --completion-promise "TASK_COMPLETE" \
  --max-iterations 10
```

## Installation

### 1. Configure Claude Code Hook

Add to `~/.config/claude-code/hooks.json`:

```json
{
  "hooks": {
    "stop": {
      "command": "python",
      "args": ["/path/to/.claude/hooks/ralph_wiggum_stop.py"],
      "enabled": true
    }
  }
}
```

### 2. Set Environment Variables

```bash
export RALPH_VAULT_PATH="./AI_Employee_Vault"
export RALPH_STATE_FILE="./.ralph_state.json"
export RALPH_MAX_ITERATIONS="10"
export RALPH_COMPLETION_MODE="file"
```

## Usage Examples

### Example 1: Process Inbox Files

```bash
# Start Ralph loop
python .claude/hooks/ralph_loop_start.py \
  "Process all files in /Needs_Action according to Company_Handbook.md. Move completed tasks to /Done." \
  --completion-mode file \
  --max-iterations 15

# Then invoke Claude
claude "Process all files in /Needs_Action according to Company_Handbook.md. Move completed tasks to /Done."
```

### Example 2: Multi-Step Analysis

```bash
# Start Ralph loop with promise mode
python .claude/hooks/ralph_loop_start.py \
  "Analyze all transactions, categorize expenses, generate report. Output ANALYSIS_COMPLETE when done." \
  --completion-mode promise \
  --completion-promise "ANALYSIS_COMPLETE" \
  --max-iterations 10

# Then invoke Claude
claude "Analyze all transactions, categorize expenses, generate report. Output ANALYSIS_COMPLETE when done."
```

### Example 3: Orchestrator Integration

```python
# In orchestrator.py
import subprocess
from pathlib import Path

def process_with_ralph_loop(task_file: Path, prompt: str):
    """Process a task with Ralph loop."""

    # Start Ralph loop
    subprocess.run([
        'python', '.claude/hooks/ralph_loop_start.py',
        prompt,
        '--completion-mode', 'file',
        '--task-file', str(task_file),
        '--max-iterations', '10'
    ])

    # Invoke Claude
    subprocess.run(['claude', prompt])

    # Check if task completed
    if (Path('AI_Employee_Vault/Done') / task_file.name).exists():
        print(f"Task completed: {task_file.name}")
        return True
    else:
        print(f"Task incomplete after max iterations: {task_file.name}")
        return False
```

## State File Format

The Ralph loop maintains state in `.ralph_state.json`:

```json
{
  "prompt": "Process all files in /Needs_Action...",
  "vault_path": "./AI_Employee_Vault",
  "task_file": "AI_Employee_Vault/Needs_Action/TASK_123.md",
  "completion_promise": "TASK_COMPLETE",
  "completion_mode": "file",
  "max_iterations": 10,
  "iteration": 3,
  "started": "2026-02-27T10:30:00Z",
  "last_check": "2026-02-27T10:35:00Z"
}
```

## How the Stop Hook Works

When Claude tries to exit:

1. **Hook is triggered** by Claude Code
2. **Read state file** to get task details
3. **Check completion**:
   - File mode: Check if task file in `/Done`
   - Promise mode: Check if output contains promise
4. **If complete**: Delete state file, allow exit (return 0)
5. **If incomplete**: Update iteration count, block exit (return 1)
6. **Claude continues** with same prompt

## Safety Features

### Maximum Iterations

Prevents infinite loops:
```bash
--max-iterations 10  # Stop after 10 iterations
```

### Iteration Tracking

State file tracks iterations:
```json
{
  "iteration": 5,
  "max_iterations": 10
}
```

### Graceful Failure

If state file is corrupted or missing, hook allows exit.

## Integration with Gold Tier

### CEO Briefing Generation

```bash
python .claude/hooks/ralph_loop_start.py \
  "Generate CEO briefing for this week, save to /Briefings, output BRIEFING_COMPLETE" \
  --completion-mode promise \
  --completion-promise "BRIEFING_COMPLETE"
```

### Multi-Task Processing

```bash
python .claude/hooks/ralph_loop_start.py \
  "Process all tasks in /Needs_Action. For each: read, analyze, take action, move to /Done." \
  --completion-mode file \
  --max-iterations 20
```

### Accounting Audit

```bash
python .claude/hooks/ralph_loop_start.py \
  "Audit all transactions via Odoo MCP, categorize, generate report, output AUDIT_COMPLETE" \
  --completion-mode promise \
  --completion-promise "AUDIT_COMPLETE"
```

## Troubleshooting

**Loop doesn't start**
- Check hook is configured in `hooks.json`
- Verify Python path is correct
- Check environment variables are set

**Loop exits too early**
- Verify completion detection logic
- Check task file path is correct
- Review Claude's output for promise string

**Loop runs forever**
- Check max iterations setting
- Verify completion condition is achievable
- Review state file for iteration count

**State file not found**
- Ensure `ralph_loop_start.py` ran successfully
- Check file permissions
- Verify working directory

## Performance

- **Overhead per iteration**: ~100ms (state file I/O)
- **Typical iterations**: 3-5 for simple tasks
- **Maximum recommended**: 20 iterations

## Security

- State file contains task details (not sensitive)
- No credentials stored
- Local file system only
- Automatic cleanup on completion

## Future Enhancements

- Progress tracking UI
- Parallel task processing
- Dynamic iteration limits
- Completion prediction
- Integration with task management

---

**Part of Gold Tier - Personal AI Employee**
**Autonomous Multi-Step Task Completion**
**Reference: github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum**
