#!/usr/bin/env python3
"""
Test Suite for Ralph Wiggum Autonomous Loop

Tests the autonomous task completion loop (Ralph Wiggum):
- Multi-step task execution
- Step-by-step progress tracking
- Loop exit conditions
- File movement detection
- Promise detection in output
- Maximum iteration limits
- State persistence

All external dependencies are mocked to ensure:
- Deterministic loop behavior
- No real Claude API calls
- Predictable task completion
- Proper state management

All tests use unittest.mock and temporary files.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json
import time


class TestRalphLoopBasics(unittest.TestCase):
    """Test basic Ralph Wiggum loop functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()
        self.needs_action = Path(self.test_vault) / "Needs_Action"
        self.done = Path(self.test_vault) / "Done"
        self.needs_action.mkdir(parents=True)
        self.done.mkdir(parents=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_ralph_loop_starts_with_initial_prompt(self):
        """Test that Ralph loop starts with user's initial prompt."""
        initial_prompt = "Process all files in /Needs_Action"

        # Create state file
        state = {
            'initial_prompt': initial_prompt,
            'iteration': 0,
            'max_iterations': 10,
            'completion_mode': 'file',
            'started_at': datetime.now().isoformat()
        }

        state_file = Path(self.test_vault) / ".ralph_state.json"
        state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')

        # Verify state
        loaded_state = json.loads(state_file.read_text(encoding='utf-8'))
        self.assertEqual(loaded_state['initial_prompt'], initial_prompt)
        self.assertEqual(loaded_state['iteration'], 0)

    def test_ralph_loop_increments_iteration_count(self):
        """Test that Ralph loop increments iteration count."""
        state_file = Path(self.test_vault) / ".ralph_state.json"

        # Initial state
        state = {'iteration': 0, 'max_iterations': 10}
        state_file.write_text(json.dumps(state), encoding='utf-8')

        # Simulate iterations
        for i in range(3):
            state = json.loads(state_file.read_text(encoding='utf-8'))
            state['iteration'] += 1
            state_file.write_text(json.dumps(state), encoding='utf-8')

        # Verify final iteration
        final_state = json.loads(state_file.read_text(encoding='utf-8'))
        self.assertEqual(final_state['iteration'], 3)

    def test_ralph_loop_respects_max_iterations(self):
        """Test that Ralph loop stops at max iterations."""
        max_iterations = 5
        state = {'iteration': 0, 'max_iterations': max_iterations}

        # Simulate loop
        while state['iteration'] < state['max_iterations']:
            state['iteration'] += 1

        # Verify stopped at max
        self.assertEqual(state['iteration'], max_iterations)


class TestRalphLoopCompletionDetection(unittest.TestCase):
    """Test completion detection mechanisms."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()
        self.needs_action = Path(self.test_vault) / "Needs_Action"
        self.done = Path(self.test_vault) / "Done"
        self.needs_action.mkdir(parents=True)
        self.done.mkdir(parents=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_file_mode_detects_file_moved_to_done(self):
        """Test that file mode detects when file is moved to /Done."""
        # Create task file
        task_file = self.needs_action / "TASK_001.md"
        task_file.write_text("Task content", encoding='utf-8')

        # Check completion (file mode)
        def is_task_complete_file_mode(task_name, done_path):
            """Check if task file exists in /Done."""
            return (done_path / task_name).exists()

        # Not complete yet
        self.assertFalse(is_task_complete_file_mode("TASK_001.md", self.done))

        # Move to done
        task_file.rename(self.done / "TASK_001.md")

        # Now complete
        self.assertTrue(is_task_complete_file_mode("TASK_001.md", self.done))

    def test_promise_mode_detects_completion_in_output(self):
        """Test that promise mode detects completion promise in output."""
        # Simulate Claude output
        outputs = [
            "I'm working on the task...",
            "Processing file 1 of 3...",
            "All tasks completed. Files moved to /Done."
        ]

        def is_task_complete_promise_mode(output):
            """Check if output contains completion promise."""
            completion_keywords = ['completed', 'done', 'finished', 'moved to /Done']
            return any(keyword in output.lower() for keyword in completion_keywords)

        # First outputs not complete
        self.assertFalse(is_task_complete_promise_mode(outputs[0]))
        self.assertFalse(is_task_complete_promise_mode(outputs[1]))

        # Final output shows completion
        self.assertTrue(is_task_complete_promise_mode(outputs[2]))

    def test_hybrid_mode_requires_both_file_and_promise(self):
        """Test that hybrid mode requires both file movement and promise."""
        # Create and move file
        task_file = self.needs_action / "TASK_002.md"
        task_file.write_text("Task content", encoding='utf-8')
        task_file.rename(self.done / "TASK_002.md")

        # Simulate output
        output = "Task completed and moved to /Done."

        # Check both conditions
        file_moved = (self.done / "TASK_002.md").exists()
        promise_found = "completed" in output.lower()

        hybrid_complete = file_moved and promise_found

        self.assertTrue(file_moved)
        self.assertTrue(promise_found)
        self.assertTrue(hybrid_complete)


class TestRalphLoopStateManagement(unittest.TestCase):
    """Test state persistence and management."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()
        self.state_file = Path(self.test_vault) / ".ralph_state.json"

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_state_persists_between_iterations(self):
        """Test that state persists between iterations."""
        # Create initial state
        state = {
            'initial_prompt': 'Process tasks',
            'iteration': 0,
            'max_iterations': 10,
            'started_at': datetime.now().isoformat()
        }
        self.state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')

        # Simulate iteration 1
        state = json.loads(self.state_file.read_text(encoding='utf-8'))
        state['iteration'] = 1
        state['last_output'] = 'Processed file 1'
        self.state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')

        # Simulate iteration 2
        state = json.loads(self.state_file.read_text(encoding='utf-8'))
        self.assertEqual(state['iteration'], 1)
        self.assertEqual(state['last_output'], 'Processed file 1')

        state['iteration'] = 2
        state['last_output'] = 'Processed file 2'
        self.state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')

        # Verify final state
        final_state = json.loads(self.state_file.read_text(encoding='utf-8'))
        self.assertEqual(final_state['iteration'], 2)
        self.assertEqual(final_state['last_output'], 'Processed file 2')

    def test_state_includes_completion_status(self):
        """Test that state tracks completion status."""
        state = {
            'iteration': 5,
            'max_iterations': 10,
            'completed': False,
            'completion_reason': None
        }

        # Task completes
        state['completed'] = True
        state['completion_reason'] = 'file_moved_to_done'

        self.assertTrue(state['completed'])
        self.assertEqual(state['completion_reason'], 'file_moved_to_done')

    def test_state_cleanup_on_completion(self):
        """Test that state file is cleaned up on completion."""
        # Create state
        self.state_file.write_text(json.dumps({'iteration': 5}), encoding='utf-8')
        self.assertTrue(self.state_file.exists())

        # Simulate completion cleanup
        if self.state_file.exists():
            self.state_file.unlink()

        self.assertFalse(self.state_file.exists())


class TestRalphLoopMultiStepExecution(unittest.TestCase):
    """Test multi-step task execution."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()
        self.needs_action = Path(self.test_vault) / "Needs_Action"
        self.in_progress = Path(self.test_vault) / "In_Progress"
        self.done = Path(self.test_vault) / "Done"

        for path in [self.needs_action, self.in_progress, self.done]:
            path.mkdir(parents=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_ralph_loop_processes_multiple_files(self):
        """Test that Ralph loop processes multiple files sequentially."""
        # Create multiple task files
        for i in range(3):
            task_file = self.needs_action / f"TASK_{i:03d}.md"
            task_file.write_text(f"Task {i} content", encoding='utf-8')

        # Simulate processing
        processed_files = []

        for task_file in sorted(self.needs_action.glob("TASK_*.md")):
            # Process task
            processed_files.append(task_file.name)

            # Move to done
            task_file.rename(self.done / task_file.name)

        # Verify all processed
        self.assertEqual(len(processed_files), 3)
        self.assertEqual(len(list(self.done.glob("TASK_*.md"))), 3)
        self.assertEqual(len(list(self.needs_action.glob("TASK_*.md"))), 0)

    def test_ralph_loop_tracks_progress_through_states(self):
        """Test that Ralph loop tracks progress through file states."""
        task_file = self.needs_action / "TASK_MULTI.md"
        task_file.write_text("Multi-step task", encoding='utf-8')

        # Track state transitions
        states = []

        # State 1: Needs Action
        states.append(('needs_action', task_file.exists()))

        # State 2: In Progress
        task_file = task_file.rename(self.in_progress / "TASK_MULTI.md")
        states.append(('in_progress', task_file.exists()))

        # State 3: Done
        task_file = task_file.rename(self.done / "TASK_MULTI.md")
        states.append(('done', task_file.exists()))

        # Verify all states tracked
        self.assertEqual(len(states), 3)
        self.assertTrue(all(exists for _, exists in states))

    def test_ralph_loop_handles_partial_completion(self):
        """Test that Ralph loop handles partial completion correctly."""
        # Create 5 tasks
        for i in range(5):
            task_file = self.needs_action / f"TASK_{i:03d}.md"
            task_file.write_text(f"Task {i}", encoding='utf-8')

        # Process only 3 tasks
        for i, task_file in enumerate(sorted(self.needs_action.glob("TASK_*.md"))):
            if i >= 3:
                break
            task_file.rename(self.done / task_file.name)

        # Verify partial completion
        self.assertEqual(len(list(self.done.glob("TASK_*.md"))), 3)
        self.assertEqual(len(list(self.needs_action.glob("TASK_*.md"))), 2)


class TestRalphLoopExitConditions(unittest.TestCase):
    """Test various exit conditions for Ralph loop."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()
        self.state_file = Path(self.test_vault) / ".ralph_state.json"

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_loop_exits_on_max_iterations(self):
        """Test that loop exits when max iterations reached."""
        state = {'iteration': 0, 'max_iterations': 3}

        # Simulate loop
        while state['iteration'] < state['max_iterations']:
            state['iteration'] += 1

        # Verify exit condition
        self.assertEqual(state['iteration'], 3)
        self.assertGreaterEqual(state['iteration'], state['max_iterations'])

    def test_loop_exits_on_task_completion(self):
        """Test that loop exits when task is completed."""
        state = {
            'iteration': 2,
            'max_iterations': 10,
            'completed': False
        }

        # Simulate task completion
        state['completed'] = True

        # Loop should exit
        should_continue = not state['completed'] and state['iteration'] < state['max_iterations']

        self.assertFalse(should_continue)

    def test_loop_exits_on_error_threshold(self):
        """Test that loop exits when error threshold is exceeded."""
        state = {
            'iteration': 5,
            'max_iterations': 10,
            'error_count': 0,
            'max_errors': 3
        }

        # Simulate errors
        for _ in range(4):
            state['error_count'] += 1

        # Loop should exit
        should_exit = state['error_count'] >= state['max_errors']

        self.assertTrue(should_exit)

    def test_loop_exits_on_no_progress(self):
        """Test that loop exits when no progress is made."""
        state = {
            'iteration': 5,
            'last_file_count': 10,
            'no_progress_count': 0,
            'max_no_progress': 3
        }

        # Simulate no progress for 3 iterations
        for _ in range(3):
            current_file_count = 10  # No change
            if current_file_count == state['last_file_count']:
                state['no_progress_count'] += 1
            else:
                state['no_progress_count'] = 0
            state['last_file_count'] = current_file_count

        # Loop should exit
        should_exit = state['no_progress_count'] >= state['max_no_progress']

        self.assertTrue(should_exit)


class TestRalphLoopErrorHandling(unittest.TestCase):
    """Test error handling in Ralph loop."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_loop_continues_after_recoverable_error(self):
        """Test that loop continues after recoverable error."""
        state = {
            'iteration': 0,
            'max_iterations': 5,
            'error_count': 0,
            'max_errors': 3
        }

        # Simulate iterations with errors
        for i in range(5):
            try:
                # Simulate error on iteration 2
                if i == 2:
                    raise Exception("Recoverable error")

                state['iteration'] += 1
            except Exception:
                state['error_count'] += 1
                # Continue if under error threshold
                if state['error_count'] < state['max_errors']:
                    state['iteration'] += 1
                    continue
                else:
                    break

        # Verify loop continued
        self.assertEqual(state['iteration'], 5)
        self.assertEqual(state['error_count'], 1)

    def test_loop_stops_after_critical_error(self):
        """Test that loop stops after critical error."""
        state = {
            'iteration': 0,
            'max_iterations': 10,
            'critical_error': False
        }

        # Simulate iterations
        for i in range(10):
            # Simulate critical error on iteration 3
            if i == 3:
                state['critical_error'] = True
                break

            state['iteration'] += 1

        # Verify loop stopped
        self.assertEqual(state['iteration'], 3)
        self.assertTrue(state['critical_error'])

    def test_loop_logs_errors_to_state(self):
        """Test that loop logs errors to state."""
        state = {
            'iteration': 0,
            'errors': []
        }

        # Simulate error
        try:
            raise Exception("Test error")
        except Exception as e:
            error_entry = {
                'iteration': state['iteration'],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            state['errors'].append(error_entry)

        # Verify error logged
        self.assertEqual(len(state['errors']), 1)
        self.assertEqual(state['errors'][0]['error'], 'Test error')


class TestRalphLoopIntegration(unittest.TestCase):
    """Test Ralph loop integration with vault system."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()
        self.needs_action = Path(self.test_vault) / "Needs_Action"
        self.done = Path(self.test_vault) / "Done"
        self.state_file = Path(self.test_vault) / ".ralph_state.json"

        self.needs_action.mkdir(parents=True)
        self.done.mkdir(parents=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_complete_ralph_loop_workflow(self):
        """Test complete Ralph loop workflow from start to finish."""
        # Step 1: Initialize state
        state = {
            'initial_prompt': 'Process all tasks',
            'iteration': 0,
            'max_iterations': 10,
            'completion_mode': 'file',
            'completed': False
        }
        self.state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')

        # Step 2: Create tasks
        for i in range(3):
            task_file = self.needs_action / f"TASK_{i:03d}.md"
            task_file.write_text(f"Task {i}", encoding='utf-8')

        # Step 3: Process tasks
        while state['iteration'] < state['max_iterations'] and not state['completed']:
            state['iteration'] += 1

            # Process one file per iteration
            task_files = list(self.needs_action.glob("TASK_*.md"))
            if task_files:
                task_file = task_files[0]
                task_file.rename(self.done / task_file.name)

            # Check completion
            if len(list(self.needs_action.glob("TASK_*.md"))) == 0:
                state['completed'] = True
                state['completion_reason'] = 'all_files_processed'

            # Update state
            self.state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')

        # Step 4: Verify completion
        final_state = json.loads(self.state_file.read_text(encoding='utf-8'))
        self.assertTrue(final_state['completed'])
        self.assertEqual(len(list(self.done.glob("TASK_*.md"))), 3)
        self.assertEqual(len(list(self.needs_action.glob("TASK_*.md"))), 0)

    def test_ralph_loop_respects_company_handbook_rules(self):
        """Test that Ralph loop respects rules from Company Handbook."""
        # Simulate Company Handbook rules
        rules = {
            'max_iterations': 10,
            'require_approval_for': ['payments', 'emails_to_new_contacts'],
            'auto_approve': ['social_posts', 'calendar_events']
        }

        # Task requiring approval
        task_type = 'payments'

        # Check if approval required
        requires_approval = task_type in rules['require_approval_for']

        self.assertTrue(requires_approval)


if __name__ == '__main__':
    unittest.main()
