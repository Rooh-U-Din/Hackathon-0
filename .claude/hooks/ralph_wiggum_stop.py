#!/usr/bin/env python3
"""
Ralph Wiggum Stop Hook
Prevents Claude from exiting until task is complete
Implements autonomous multi-step task completion
"""
import sys
import json
import os
from pathlib import Path
from datetime import datetime

def check_task_completion(state_file: Path, vault_path: Path) -> bool:
    """
    Check if task is complete by verifying file moved to /Done.

    Args:
        state_file: Path to state file tracking the task
        vault_path: Path to vault

    Returns:
        True if task is complete
    """
    if not state_file.exists():
        return False

    try:
        state = json.loads(state_file.read_text(encoding='utf-8'))
        task_file = state.get('task_file')

        if not task_file:
            return False

        # Check if task file is in /Done folder
        done_path = vault_path / 'Done'
        task_filename = Path(task_file).name

        if (done_path / task_filename).exists():
            return True

        return False

    except Exception as e:
        print(f"Error checking task completion: {e}", file=sys.stderr)
        return False

def check_promise_completion(output: str, promise: str) -> bool:
    """
    Check if Claude output contains completion promise.

    Args:
        output: Claude's output text
        promise: Promise string to look for

    Returns:
        True if promise found
    """
    return f"<promise>{promise}</promise>" in output

def main():
    """
    Stop hook entry point.
    Called when Claude tries to exit.
    """
    # Get hook context from environment
    hook_context = os.environ.get('CLAUDE_HOOK_CONTEXT', '{}')

    try:
        context = json.loads(hook_context)
    except:
        context = {}

    # Get configuration
    vault_path = Path(os.environ.get('RALPH_VAULT_PATH', './AI_Employee_Vault'))
    state_file = Path(os.environ.get('RALPH_STATE_FILE', './.ralph_state.json'))
    max_iterations = int(os.environ.get('RALPH_MAX_ITERATIONS', '10'))
    completion_promise = os.environ.get('RALPH_COMPLETION_PROMISE', 'TASK_COMPLETE')
    completion_mode = os.environ.get('RALPH_COMPLETION_MODE', 'file')  # 'file' or 'promise'

    # Check if Ralph loop is active
    if not state_file.exists():
        # No active loop, allow exit
        sys.exit(0)

    try:
        state = json.loads(state_file.read_text(encoding='utf-8'))
    except:
        # Invalid state, allow exit
        sys.exit(0)

    # Check iteration count
    current_iteration = state.get('iteration', 0)

    if current_iteration >= max_iterations:
        print(f"\n[RALPH] Maximum iterations ({max_iterations}) reached. Stopping loop.", file=sys.stderr)
        state_file.unlink()
        sys.exit(0)

    # Check completion based on mode
    is_complete = False

    if completion_mode == 'file':
        is_complete = check_task_completion(state_file, vault_path)
    elif completion_mode == 'promise':
        output = context.get('output', '')
        is_complete = check_promise_completion(output, completion_promise)

    if is_complete:
        print(f"\n[RALPH] Task complete! Exiting loop.", file=sys.stderr)
        state_file.unlink()
        sys.exit(0)

    # Task not complete, continue loop
    current_iteration += 1
    state['iteration'] = current_iteration
    state['last_check'] = datetime.now().isoformat()

    state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')

    print(f"\n[RALPH] Task not complete. Iteration {current_iteration}/{max_iterations}. Continuing...", file=sys.stderr)
    print(f"[RALPH] Re-injecting prompt: {state.get('prompt', '')[:100]}...", file=sys.stderr)

    # Block exit and re-inject prompt
    # Return non-zero to indicate Claude should continue
    sys.exit(1)

if __name__ == '__main__':
    main()
