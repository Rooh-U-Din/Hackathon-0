#!/usr/bin/env python3
"""
Test Suite for Vault Coordination Rules

Tests the critical coordination rules that prevent conflicts between agents:
- Claim-by-move rule: First agent to move file owns it
- Single-writer rule: Only local agent writes to Dashboard.md
- File state transitions: Proper movement through vault folders
- Atomic operations: No race conditions

All tests use isolated temporary vaults to ensure deterministic behavior.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import threading
import time
import json


class TestClaimByMoveRule(unittest.TestCase):
    """Test the claim-by-move coordination pattern."""

    def setUp(self):
        """Set up test vault with proper folder structure."""
        self.test_vault = tempfile.mkdtemp()
        self.needs_action = Path(self.test_vault) / "Needs_Action" / "email_triage"
        self.in_progress_cloud = Path(self.test_vault) / "In_Progress" / "cloud"
        self.in_progress_local = Path(self.test_vault) / "In_Progress" / "local"
        self.done = Path(self.test_vault) / "Done"

        for path in [self.needs_action, self.in_progress_cloud, self.in_progress_local, self.done]:
            path.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_first_agent_claims_task_successfully(self):
        """Test that first agent to move file successfully claims it."""
        # Create task file
        task_file = self.needs_action / "TASK_001.md"
        task_file.write_text("---\ntype: task\n---\nTask content", encoding='utf-8')

        # Agent 1 claims by moving to In_Progress
        claimed_file = self.in_progress_cloud / "TASK_001.md"
        task_file.rename(claimed_file)

        # Verify claim
        self.assertTrue(claimed_file.exists())
        self.assertFalse(task_file.exists())

    def test_second_agent_cannot_claim_already_claimed_task(self):
        """Test that second agent cannot claim task already in progress."""
        # Create task file
        task_file = self.needs_action / "TASK_002.md"
        task_file.write_text("---\ntype: task\n---\nTask content", encoding='utf-8')

        # Agent 1 claims
        claimed_file_cloud = self.in_progress_cloud / "TASK_002.md"
        task_file.rename(claimed_file_cloud)

        # Agent 2 tries to claim (file no longer in Needs_Action)
        task_file_check = self.needs_action / "TASK_002.md"
        self.assertFalse(task_file_check.exists())

        # Agent 2 should check In_Progress before claiming
        in_progress_files = list(self.in_progress_cloud.glob("TASK_002.md"))
        self.assertEqual(len(in_progress_files), 1)

    def test_claim_by_move_is_atomic(self):
        """Test that claim-by-move operation is atomic (no partial states)."""
        task_file = self.needs_action / "TASK_003.md"
        task_file.write_text("---\ntype: task\n---\nTask content", encoding='utf-8')

        # Move operation should be atomic
        claimed_file = self.in_progress_cloud / "TASK_003.md"
        task_file.rename(claimed_file)

        # File should exist in exactly one location
        self.assertTrue(claimed_file.exists())
        self.assertFalse(task_file.exists())

        # No duplicate files
        all_task_files = list(Path(self.test_vault).rglob("TASK_003.md"))
        self.assertEqual(len(all_task_files), 1)

    def test_concurrent_claim_attempts_only_one_succeeds(self):
        """Test that concurrent claim attempts result in only one success."""
        task_file = self.needs_action / "TASK_004.md"
        task_file.write_text("---\ntype: task\n---\nTask content", encoding='utf-8')

        results = []

        def try_claim(agent_name, target_dir):
            """Simulate agent trying to claim task."""
            try:
                source = self.needs_action / "TASK_004.md"
                if source.exists():
                    dest = target_dir / "TASK_004.md"
                    source.rename(dest)
                    results.append((agent_name, True))
                else:
                    results.append((agent_name, False))
            except FileNotFoundError:
                results.append((agent_name, False))

        # Simulate two agents trying to claim simultaneously
        thread1 = threading.Thread(target=try_claim, args=("cloud", self.in_progress_cloud))
        thread2 = threading.Thread(target=try_claim, args=("local", self.in_progress_local))

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # Only one should succeed
        successful_claims = [r for r in results if r[1]]
        self.assertEqual(len(successful_claims), 1)

    def test_agent_checks_in_progress_before_claiming(self):
        """Test that agents check In_Progress folder before claiming from Needs_Action."""
        # Task already in progress
        in_progress_file = self.in_progress_cloud / "TASK_005.md"
        in_progress_file.write_text("---\ntype: task\n---\nTask content", encoding='utf-8')

        # Agent should check In_Progress first
        def is_task_available(task_name):
            """Check if task is available to claim."""
            # Check if in any In_Progress folder
            cloud_claimed = (self.in_progress_cloud / task_name).exists()
            local_claimed = (self.in_progress_local / task_name).exists()
            return not (cloud_claimed or local_claimed)

        self.assertFalse(is_task_available("TASK_005.md"))


class TestSingleWriterRule(unittest.TestCase):
    """Test the single-writer rule for Dashboard.md."""

    def setUp(self):
        """Set up test vault."""
        self.test_vault = tempfile.mkdtemp()
        self.dashboard = Path(self.test_vault) / "Dashboard.md"
        self.updates_dir = Path(self.test_vault) / "Updates"
        self.updates_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_only_local_agent_writes_to_dashboard(self):
        """Test that only local agent writes directly to Dashboard.md."""
        # Local agent writes to Dashboard.md
        dashboard_content = f"""# AI Employee Dashboard

Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## System Status

**Local Agent:** Running
**Cloud Agent:** Running (via updates)

---
*Dashboard managed by Local Agent*
"""
        self.dashboard.write_text(dashboard_content, encoding='utf-8')

        # Verify Dashboard.md exists and has correct content
        self.assertTrue(self.dashboard.exists())
        content = self.dashboard.read_text(encoding='utf-8')
        self.assertIn('Dashboard managed by Local Agent', content)

    def test_cloud_agent_writes_to_updates_folder(self):
        """Test that cloud agent writes to /Updates/ folder, not Dashboard.md."""
        # Cloud agent writes to Updates folder
        update_file = self.updates_dir / f"cloud_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        update_content = f"""---
type: dashboard_update
agent: cloud
timestamp: {datetime.now().isoformat()}
---

# Cloud Agent Update

**Status:** Running
**Pending Approvals:** 3
**In Progress:** 2

---
*Cloud Agent Status Update*
"""
        update_file.write_text(update_content, encoding='utf-8')

        # Verify update file created in Updates folder
        self.assertTrue(update_file.exists())
        self.assertTrue(update_file.parent.name == "Updates")

        # Verify Dashboard.md not modified by cloud agent
        self.assertFalse(self.dashboard.exists())

    def test_local_agent_merges_cloud_updates_into_dashboard(self):
        """Test that local agent merges cloud updates into Dashboard.md."""
        # Cloud creates update
        update_file = self.updates_dir / "cloud_update_20260227_100000.md"
        update_file.write_text("""---
type: dashboard_update
---

# Cloud Agent Update

Cloud processed 5 tasks.
""", encoding='utf-8')

        # Local agent reads update and merges into Dashboard
        update_content = update_file.read_text(encoding='utf-8')

        if not self.dashboard.exists():
            dashboard_content = f"""# AI Employee Dashboard

Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Recent Updates

{update_content}

---
*Dashboard managed by Local Agent*
"""
        else:
            current = self.dashboard.read_text(encoding='utf-8')
            dashboard_content = current.replace(
                '## Recent Updates',
                f'## Recent Updates\n\n{update_content}\n'
            )

        self.dashboard.write_text(dashboard_content, encoding='utf-8')

        # Verify merge
        final_content = self.dashboard.read_text(encoding='utf-8')
        self.assertIn('Cloud processed 5 tasks', final_content)
        self.assertIn('Dashboard managed by Local Agent', final_content)

    def test_no_concurrent_dashboard_writes(self):
        """Test that Dashboard.md is never written by multiple agents concurrently."""
        # Only local agent should write
        writers = []

        def local_agent_write():
            """Simulate local agent writing."""
            self.dashboard.write_text("Local agent update", encoding='utf-8')
            writers.append("local")

        def cloud_agent_write():
            """Simulate cloud agent (should NOT write to Dashboard)."""
            # Cloud writes to Updates instead
            update_file = self.updates_dir / "update.md"
            update_file.write_text("Cloud update", encoding='utf-8')
            writers.append("cloud_to_updates")

        thread1 = threading.Thread(target=local_agent_write)
        thread2 = threading.Thread(target=cloud_agent_write)

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # Verify only local wrote to Dashboard
        self.assertTrue(self.dashboard.exists())
        self.assertEqual(self.dashboard.read_text(encoding='utf-8'), "Local agent update")

        # Verify cloud wrote to Updates
        update_files = list(self.updates_dir.glob("*.md"))
        self.assertEqual(len(update_files), 1)


class TestFileStateTransitions(unittest.TestCase):
    """Test proper file state transitions through vault folders."""

    def setUp(self):
        """Set up test vault with all folders."""
        self.test_vault = tempfile.mkdtemp()
        self.folders = {
            'inbox': Path(self.test_vault) / "Inbox",
            'needs_action': Path(self.test_vault) / "Needs_Action" / "email_triage",
            'in_progress': Path(self.test_vault) / "In_Progress" / "cloud",
            'pending_approval': Path(self.test_vault) / "Pending_Approval",
            'approved': Path(self.test_vault) / "Approved",
            'rejected': Path(self.test_vault) / "Rejected",
            'done': Path(self.test_vault) / "Done"
        }

        for folder in self.folders.values():
            folder.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_email_workflow_state_transitions(self):
        """Test complete email workflow: Inbox → Needs_Action → In_Progress → Pending_Approval → Approved → Done."""
        task_name = "EMAIL_001.md"

        # State 1: Inbox
        file = self.folders['inbox'] / task_name
        file.write_text("---\ntype: email\n---\nContent", encoding='utf-8')
        self.assertTrue(file.exists())

        # State 2: Needs_Action
        file = file.rename(self.folders['needs_action'] / task_name)
        self.assertTrue(file.exists())
        self.assertFalse((self.folders['inbox'] / task_name).exists())

        # State 3: In_Progress (claimed by cloud agent)
        file = file.rename(self.folders['in_progress'] / task_name)
        self.assertTrue(file.exists())

        # State 4: Pending_Approval (cloud creates draft)
        approval_file = self.folders['pending_approval'] / "APPROVAL_001.md"
        approval_file.write_text("---\ntype: approval\n---\nDraft reply", encoding='utf-8')

        # Original task moves to Done
        file = file.rename(self.folders['done'] / task_name)
        self.assertTrue(file.exists())

        # State 5: Approved (user approves)
        approval_file = approval_file.rename(self.folders['approved'] / "APPROVAL_001.md")
        self.assertTrue(approval_file.exists())

        # State 6: Done (local executes and moves to Done)
        approval_file = approval_file.rename(self.folders['done'] / "APPROVAL_001.md")
        self.assertTrue(approval_file.exists())

        # Verify final state
        done_files = list(self.folders['done'].glob("*.md"))
        self.assertEqual(len(done_files), 2)  # Original task + approval

    def test_rejection_workflow(self):
        """Test rejection workflow: Pending_Approval → Rejected → Done."""
        approval_file = self.folders['pending_approval'] / "APPROVAL_002.md"
        approval_file.write_text("---\ntype: approval\n---\nDraft", encoding='utf-8')

        # User rejects
        approval_file = approval_file.rename(self.folders['rejected'] / "APPROVAL_002.md")
        self.assertTrue(approval_file.exists())

        # Local agent logs rejection and moves to Done
        approval_file = approval_file.rename(self.folders['done'] / "APPROVAL_002.md")
        self.assertTrue(approval_file.exists())

    def test_file_exists_in_only_one_location(self):
        """Test that file exists in exactly one location at any time."""
        task_name = "TASK_UNIQUE.md"
        file = self.folders['inbox'] / task_name
        file.write_text("---\ntype: task\n---\nContent", encoding='utf-8')

        # Move through states
        file = file.rename(self.folders['needs_action'] / task_name)
        file = file.rename(self.folders['in_progress'] / task_name)
        file = file.rename(self.folders['done'] / task_name)

        # Verify file exists in exactly one location
        all_occurrences = list(Path(self.test_vault).rglob(task_name))
        self.assertEqual(len(all_occurrences), 1)
        self.assertEqual(all_occurrences[0].parent.name, "Done")


class TestDomainOwnership(unittest.TestCase):
    """Test domain ownership rules for agent coordination."""

    def setUp(self):
        """Set up test vault."""
        self.test_vault = tempfile.mkdtemp()
        self.needs_action = Path(self.test_vault) / "Needs_Action"

        # Create domain folders
        self.cloud_domains = ['email_triage', 'social_drafts', 'scheduling']
        self.local_domains = ['whatsapp', 'payments', 'execution']

        for domain in self.cloud_domains + self.local_domains:
            (self.needs_action / domain).mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_cloud_agent_only_claims_cloud_domains(self):
        """Test that cloud agent only claims tasks in cloud-owned domains."""
        cloud_domains = ['email_triage', 'social_drafts', 'scheduling']

        # Create tasks in various domains
        (self.needs_action / 'email_triage' / 'TASK_CLOUD.md').write_text("---\ndomain: email_triage\n---", encoding='utf-8')
        (self.needs_action / 'whatsapp' / 'TASK_LOCAL.md').write_text("---\ndomain: whatsapp\n---", encoding='utf-8')

        # Cloud agent checks domain before claiming
        def can_cloud_claim(task_file):
            """Check if cloud agent can claim this task."""
            content = task_file.read_text(encoding='utf-8')
            for line in content.split('\n'):
                if line.startswith('domain:'):
                    domain = line.split(':')[1].strip()
                    return domain in cloud_domains
            return False

        cloud_task = self.needs_action / 'email_triage' / 'TASK_CLOUD.md'
        local_task = self.needs_action / 'whatsapp' / 'TASK_LOCAL.md'

        self.assertTrue(can_cloud_claim(cloud_task))
        self.assertFalse(can_cloud_claim(local_task))

    def test_local_agent_only_claims_local_domains(self):
        """Test that local agent only claims tasks in local-owned domains."""
        local_domains = ['whatsapp', 'payments', 'execution']

        # Create tasks
        (self.needs_action / 'whatsapp' / 'TASK_LOCAL.md').write_text("---\ndomain: whatsapp\n---", encoding='utf-8')
        (self.needs_action / 'email_triage' / 'TASK_CLOUD.md').write_text("---\ndomain: email_triage\n---", encoding='utf-8')

        # Local agent checks domain
        def can_local_claim(task_file):
            """Check if local agent can claim this task."""
            content = task_file.read_text(encoding='utf-8')
            for line in content.split('\n'):
                if line.startswith('domain:'):
                    domain = line.split(':')[1].strip()
                    return domain in local_domains
            return False

        local_task = self.needs_action / 'whatsapp' / 'TASK_LOCAL.md'
        cloud_task = self.needs_action / 'email_triage' / 'TASK_CLOUD.md'

        self.assertTrue(can_local_claim(local_task))
        self.assertFalse(can_local_claim(cloud_task))


if __name__ == '__main__':
    unittest.main()
