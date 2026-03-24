#!/usr/bin/env python3
"""
Ralph Wiggum Loop Starter
Initiates autonomous task completion loop
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

def start_ralph_loop(
    prompt: str,
    vault_path: Path,
    task_file: str = None,
    completion_promise: str = "TASK_COMPLETE",
    completion_mode: str = "file",
    max_iterations: int = 10
) -> int:
    """
    Start a Ralph Wiggum autonomous task loop.

    Args:
        prompt: Task prompt for Claude
        vault_path: Path to vault
        task_file: Task file to track (for file completion mode)
        completion_promise: Promise string to look for (for promise mode)
        completion_mode: 'file' or 'promise'
        max_iterations: Maximum iterations before stopping

    Returns:
        Exit code
    """
    state_file = Path('.ralph_state.json')

    # Create state file
    state = {
        'prompt': prompt,
        'vault_path': str(vault_path),
        'task_file': task_file,
        'completion_promise': completion_promise,
        'completion_mode': completion_mode,
        'max_iterations': max_iterations,
        'iteration': 0,
        'started': datetime.now().isoformat()
    }

    try:
        state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')
        print(f"[RALPH] Loop started with max {max_iterations} iterations")
        print(f"[RALPH] Completion mode: {completion_mode}")
        print(f"[RALPH] Prompt: {prompt}")
        print()

        # Set environment variables for hook
        import os
        os.environ['RALPH_VAULT_PATH'] = str(vault_path)
        os.environ['RALPH_STATE_FILE'] = str(state_file)
        os.environ['RALPH_MAX_ITERATIONS'] = str(max_iterations)
        os.environ['RALPH_COMPLETION_PROMISE'] = completion_promise
        os.environ['RALPH_COMPLETION_MODE'] = completion_mode

        # Now invoke Claude with the prompt
        # In practice, this would be done by the orchestrator
        print("[RALPH] Ready to invoke Claude Code")
        print(f"[RALPH] Use: claude '{prompt}'")

        return 0

    except Exception as e:
        print(f"[RALPH] Failed to start loop: {e}", file=sys.stderr)
        return 1

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Ralph Wiggum Loop Starter')
    parser.add_argument('prompt', type=str, help='Task prompt for Claude')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault',
                       help='Path to vault')
    parser.add_argument('--task-file', type=str,
                       help='Task file to track (for file completion mode)')
    parser.add_argument('--completion-promise', type=str, default='TASK_COMPLETE',
                       help='Promise string for completion')
    parser.add_argument('--completion-mode', type=str, default='file',
                       choices=['file', 'promise'],
                       help='Completion detection mode')
    parser.add_argument('--max-iterations', type=int, default=10,
                       help='Maximum iterations')

    args = parser.parse_args()

    vault_path = Path(args.vault)
    if not vault_path.exists():
        print(f"Error: Vault not found: {vault_path}", file=sys.stderr)
        return 1

    return start_ralph_loop(
        prompt=args.prompt,
        vault_path=vault_path,
        task_file=args.task_file,
        completion_promise=args.completion_promise,
        completion_mode=args.completion_mode,
        max_iterations=args.max_iterations
    )

if __name__ == '__main__':
    sys.exit(main())
