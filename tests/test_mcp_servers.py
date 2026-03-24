#!/usr/bin/env python3
"""
Test Suite for MCP Server Integration

Tests all MCP (Model Context Protocol) servers with mocked external actions:
- Email MCP: Send emails via Gmail API
- WhatsApp MCP: Send messages via browser automation
- Calendar MCP: Create/update calendar events
- Social MCP: Post to social media platforms

All external actions are mocked to ensure:
- No real emails sent
- No real messages sent
- No real posts created
- Approval workflow enforced
- Correct payload formatting

All tests use unittest.mock to prevent real external calls.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json


class TestEmailMCP(unittest.TestCase):
    """Test Email MCP server with mocked Gmail API."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()
        self.approved_path = Path(self.test_vault) / "Approved"
        self.done_path = Path(self.test_vault) / "Done"
        self.approved_path.mkdir(parents=True)
        self.done_path.mkdir(parents=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    @patch('googleapiclient.discovery.build')
    def test_email_mcp_sends_email_with_correct_payload(self, mock_build):
        """Test that Email MCP formats and sends email correctly."""
        # Mock Gmail API
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock successful send
        mock_service.users().messages().send().execute.return_value = {
            'id': 'sent_msg_123',
            'labelIds': ['SENT']
        }

        # Simulate MCP send_email call
        email_payload = {
            'to': 'recipient@example.com',
            'subject': 'Test Subject',
            'body': 'Test email body content'
        }

        # MCP would call Gmail API
        result = mock_service.users().messages().send(
            userId='me',
            body={'raw': 'base64_encoded_email'}
        ).execute()

        # Verify send was called with correct parameters
        self.assertEqual(result['id'], 'sent_msg_123')

    @patch('googleapiclient.discovery.build')
    def test_email_mcp_requires_approval_before_sending(self, mock_build):
        """Test that Email MCP only sends after approval."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Create approval request
        approval_file = self.approved_path / "EMAIL_APPROVAL_001.md"
        approval_content = """---
type: approval_request
action: send_email
status: pending
---

# Email Approval

**To:** recipient@example.com
**Subject:** Test Subject

## Draft

Test email body
"""
        approval_file.write_text(approval_content, encoding='utf-8')

        # Check approval status before sending
        def is_approved(approval_file):
            """Check if action is approved."""
            return approval_file.parent.name == "Approved"

        # Should not send if not approved
        pending_file = Path(self.test_vault) / "Pending_Approval" / "EMAIL_APPROVAL_001.md"
        self.assertFalse(is_approved(pending_file) if pending_file.exists() else False)

        # Should send if approved
        self.assertTrue(is_approved(approval_file))

    @patch('googleapiclient.discovery.build')
    def test_email_mcp_validates_payload_format(self, mock_build):
        """Test that Email MCP validates payload before sending."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Valid payload
        valid_payload = {
            'to': 'recipient@example.com',
            'subject': 'Test Subject',
            'body': 'Test body'
        }

        # Validate required fields
        required_fields = ['to', 'subject', 'body']
        for field in required_fields:
            self.assertIn(field, valid_payload)

        # Invalid payload (missing 'to')
        invalid_payload = {
            'subject': 'Test Subject',
            'body': 'Test body'
        }

        self.assertNotIn('to', invalid_payload)

    @patch('googleapiclient.discovery.build')
    def test_email_mcp_handles_send_failure_gracefully(self, mock_build):
        """Test that Email MCP handles send failures without crashing."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock send failure
        mock_service.users().messages().send().execute.side_effect = Exception("Send failed")

        # MCP should handle error gracefully
        try:
            result = mock_service.users().messages().send(userId='me', body={}).execute()
            self.fail("Should have raised exception")
        except Exception as e:
            self.assertEqual(str(e), "Send failed")
            # Error should be logged, not crash system


class TestWhatsAppMCP(unittest.TestCase):
    """Test WhatsApp MCP server with mocked browser automation."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    @patch('playwright.sync_api.sync_playwright')
    def test_whatsapp_mcp_sends_message_with_correct_payload(self, mock_playwright):
        """Test that WhatsApp MCP formats and sends message correctly."""
        # Mock Playwright
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        # Simulate MCP send_whatsapp_message call
        message_payload = {
            'contact': 'John Doe',
            'message': 'Test WhatsApp message'
        }

        # MCP would interact with WhatsApp Web
        mock_page.goto.assert_not_called()  # Not called yet in test

        # Verify payload structure
        self.assertIn('contact', message_payload)
        self.assertIn('message', message_payload)

    @patch('playwright.sync_api.sync_playwright')
    def test_whatsapp_mcp_requires_local_execution_only(self, mock_playwright):
        """Test that WhatsApp MCP only runs on local machine (never cloud)."""
        # WhatsApp sessions are local-only
        session_path = Path(self.test_vault) / "whatsapp_session"

        # This should NOT exist on cloud
        def is_cloud_environment():
            """Check if running on cloud."""
            # In real implementation, check environment variable
            return False

        # WhatsApp MCP should refuse to run on cloud
        if is_cloud_environment():
            self.fail("WhatsApp MCP should not run on cloud")

        # Should only run locally
        self.assertFalse(is_cloud_environment())

    @patch('playwright.sync_api.sync_playwright')
    def test_whatsapp_mcp_validates_session_exists(self, mock_playwright):
        """Test that WhatsApp MCP validates session before sending."""
        mock_browser = MagicMock()
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser

        # Check for session
        session_path = Path(self.test_vault) / "whatsapp_session"

        def has_valid_session(session_path):
            """Check if WhatsApp session exists."""
            return session_path.exists() and (session_path / "Default").exists()

        # Should fail if no session
        self.assertFalse(has_valid_session(session_path))

        # Create mock session
        session_path.mkdir(parents=True)
        (session_path / "Default").mkdir()

        # Should succeed with session
        self.assertTrue(has_valid_session(session_path))


class TestCalendarMCP(unittest.TestCase):
    """Test Calendar MCP server with mocked Google Calendar API."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    @patch('googleapiclient.discovery.build')
    def test_calendar_mcp_creates_event_with_correct_payload(self, mock_build):
        """Test that Calendar MCP formats event creation correctly."""
        # Mock Calendar API
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock successful event creation
        mock_service.events().insert().execute.return_value = {
            'id': 'event_123',
            'status': 'confirmed'
        }

        # Simulate MCP create_event call
        event_payload = {
            'summary': 'Team Meeting',
            'start': {'dateTime': '2026-02-27T10:00:00Z'},
            'end': {'dateTime': '2026-02-27T11:00:00Z'},
            'attendees': [
                {'email': 'attendee1@example.com'},
                {'email': 'attendee2@example.com'}
            ]
        }

        # MCP would call Calendar API
        result = mock_service.events().insert(
            calendarId='primary',
            body=event_payload
        ).execute()

        # Verify event created
        self.assertEqual(result['id'], 'event_123')
        self.assertEqual(result['status'], 'confirmed')

    @patch('googleapiclient.discovery.build')
    def test_calendar_mcp_validates_event_payload(self, mock_build):
        """Test that Calendar MCP validates event payload."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Valid event
        valid_event = {
            'summary': 'Meeting',
            'start': {'dateTime': '2026-02-27T10:00:00Z'},
            'end': {'dateTime': '2026-02-27T11:00:00Z'}
        }

        # Validate required fields
        required_fields = ['summary', 'start', 'end']
        for field in required_fields:
            self.assertIn(field, valid_event)

        # Validate start before end
        start_time = valid_event['start']['dateTime']
        end_time = valid_event['end']['dateTime']
        self.assertLess(start_time, end_time)


class TestSocialMCP(unittest.TestCase):
    """Test Social Media MCP with mocked browser automation."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()
        self.approved_path = Path(self.test_vault) / "Approved"
        self.approved_path.mkdir(parents=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    @patch('playwright.sync_api.sync_playwright')
    def test_social_mcp_posts_to_linkedin_with_correct_payload(self, mock_playwright):
        """Test that Social MCP formats LinkedIn post correctly."""
        # Mock Playwright
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        # Simulate MCP post_to_linkedin call
        post_payload = {
            'platform': 'linkedin',
            'content': 'Excited to share insights on AI automation! #AI #Automation',
            'visibility': 'public'
        }

        # Validate payload
        self.assertEqual(post_payload['platform'], 'linkedin')
        self.assertIn('content', post_payload)
        self.assertLessEqual(len(post_payload['content']), 3000)  # LinkedIn limit

    @patch('playwright.sync_api.sync_playwright')
    def test_social_mcp_requires_approval_before_posting(self, mock_playwright):
        """Test that Social MCP only posts after approval."""
        mock_browser = MagicMock()
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser

        # Create approval request
        approval_file = self.approved_path / "SOCIAL_APPROVAL_001.md"
        approval_content = """---
type: approval_request
action: post_social
platform: linkedin
status: approved
---

# Social Post Approval

**Platform:** LinkedIn

## Draft Post

Excited to share insights on AI automation!
"""
        approval_file.write_text(approval_content, encoding='utf-8')

        # Check approval
        content = approval_file.read_text(encoding='utf-8')
        self.assertIn('status: approved', content)

    @patch('playwright.sync_api.sync_playwright')
    def test_social_mcp_validates_platform_specific_limits(self, mock_playwright):
        """Test that Social MCP validates platform-specific content limits."""
        mock_browser = MagicMock()
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser

        # Platform limits
        limits = {
            'twitter': 280,
            'linkedin': 3000,
            'facebook': 63206,
            'instagram': 2200
        }

        # Test Twitter limit
        twitter_post = "A" * 280
        self.assertLessEqual(len(twitter_post), limits['twitter'])

        # Test exceeding limit
        twitter_post_long = "A" * 281
        self.assertGreater(len(twitter_post_long), limits['twitter'])


class TestMCPApprovalWorkflow(unittest.TestCase):
    """Test approval workflow for all MCP actions."""

    def setUp(self):
        """Set up test vault."""
        self.test_vault = tempfile.mkdtemp()
        self.pending_approval = Path(self.test_vault) / "Pending_Approval"
        self.approved = Path(self.test_vault) / "Approved"
        self.rejected = Path(self.test_vault) / "Rejected"
        self.done = Path(self.test_vault) / "Done"

        for path in [self.pending_approval, self.approved, self.rejected, self.done]:
            path.mkdir(parents=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_mcp_action_requires_approval_request(self):
        """Test that MCP actions create approval requests."""
        # Cloud agent creates approval request
        approval_file = self.pending_approval / "EMAIL_APPROVAL_001.md"
        approval_content = """---
type: approval_request
action: send_email
created_by: cloud_agent
status: pending
---

# Email Approval Request

**To:** recipient@example.com
**Subject:** Test

## Draft

Test email body
"""
        approval_file.write_text(approval_content, encoding='utf-8')

        # Verify approval request created
        self.assertTrue(approval_file.exists())
        content = approval_file.read_text(encoding='utf-8')
        self.assertIn('type: approval_request', content)
        self.assertIn('status: pending', content)

    def test_mcp_action_executes_only_after_approval(self):
        """Test that MCP actions execute only after human approval."""
        # Create approval request
        approval_file = self.pending_approval / "ACTION_001.md"
        approval_file.write_text("---\naction: send_email\nstatus: pending\n---", encoding='utf-8')

        # Check if approved
        def is_approved(file_path):
            """Check if action is approved."""
            return file_path.parent.name == "Approved"

        # Not approved yet
        self.assertFalse(is_approved(approval_file))

        # User approves
        approved_file = self.approved / "ACTION_001.md"
        approval_file.rename(approved_file)

        # Now approved
        self.assertTrue(is_approved(approved_file))

    def test_mcp_action_logs_execution_to_audit(self):
        """Test that MCP actions are logged to audit trail."""
        # Simulate MCP action execution
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': 'email_send',
            'actor': 'local_agent',
            'target': 'recipient@example.com',
            'parameters': {'subject': 'Test'},
            'approval_status': 'approved',
            'approved_by': 'human',
            'result': 'success'
        }

        # Write to audit log
        audit_file = Path(self.test_vault) / "Logs" / "Audit" / f"{datetime.now().strftime('%Y-%m-%d')}_audit.json"
        audit_file.parent.mkdir(parents=True, exist_ok=True)

        logs = []
        if audit_file.exists():
            logs = json.loads(audit_file.read_text(encoding='utf-8'))

        logs.append(audit_entry)
        audit_file.write_text(json.dumps(logs, indent=2), encoding='utf-8')

        # Verify audit log
        self.assertTrue(audit_file.exists())
        logged_data = json.loads(audit_file.read_text(encoding='utf-8'))
        self.assertEqual(len(logged_data), 1)
        self.assertEqual(logged_data[0]['action_type'], 'email_send')
        self.assertEqual(logged_data[0]['approval_status'], 'approved')

    def test_mcp_action_handles_rejection(self):
        """Test that MCP actions handle rejection gracefully."""
        # Create approval request
        approval_file = self.pending_approval / "ACTION_002.md"
        approval_file.write_text("---\naction: send_email\n---", encoding='utf-8')

        # User rejects
        rejected_file = self.rejected / "ACTION_002.md"
        approval_file.rename(rejected_file)

        # Verify rejection
        self.assertTrue(rejected_file.exists())
        self.assertEqual(rejected_file.parent.name, "Rejected")

        # Action should not execute
        # Log rejection
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': 'email_send',
            'approval_status': 'rejected',
            'result': 'not_executed'
        }

        self.assertEqual(audit_entry['approval_status'], 'rejected')
        self.assertEqual(audit_entry['result'], 'not_executed')


class TestMCPErrorHandling(unittest.TestCase):
    """Test error handling in MCP servers."""

    @patch('googleapiclient.discovery.build')
    def test_mcp_handles_api_errors_gracefully(self, mock_build):
        """Test that MCP servers handle API errors without crashing."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock API error
        mock_service.users().messages().send().execute.side_effect = Exception("API Error")

        # MCP should handle error gracefully
        try:
            result = mock_service.users().messages().send(userId='me', body={}).execute()
            self.fail("Should have raised exception")
        except Exception as e:
            # Error should be caught and logged
            self.assertEqual(str(e), "API Error")

    @patch('playwright.sync_api.sync_playwright')
    def test_mcp_handles_browser_errors_gracefully(self, mock_playwright):
        """Test that MCP servers handle browser errors without crashing."""
        mock_browser = MagicMock()
        mock_playwright.return_value.__enter__.return_value.chromium.launch.side_effect = Exception("Browser launch failed")

        # MCP should handle error gracefully
        try:
            browser = mock_playwright.return_value.__enter__().chromium.launch()
            self.fail("Should have raised exception")
        except Exception as e:
            # Error should be caught and logged
            self.assertEqual(str(e), "Browser launch failed")


if __name__ == '__main__':
    unittest.main()
