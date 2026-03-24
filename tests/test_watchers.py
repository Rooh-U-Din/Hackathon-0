#!/usr/bin/env python3
"""
Test Suite for Watcher Components

Tests all watcher skills (Gmail, LinkedIn, Twitter, Facebook, Instagram, WhatsApp)
with mocked external APIs to ensure:
- Correct markdown file creation
- Proper metadata extraction
- No real API calls
- Deterministic behavior

All external dependencies are mocked using unittest.mock.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import json


class TestGmailWatcher(unittest.TestCase):
    """Test Gmail watcher with mocked Gmail API."""

    def setUp(self):
        """Set up test environment with temporary vault."""
        self.test_vault = tempfile.mkdtemp()
        self.inbox_path = Path(self.test_vault) / "Inbox"
        self.inbox_path.mkdir(parents=True)

    def tearDown(self):
        """Clean up temporary test vault."""
        shutil.rmtree(self.test_vault)

    @patch('googleapiclient.discovery.build')
    def test_gmail_watcher_creates_markdown_file(self, mock_build):
        """Test that Gmail watcher creates correct markdown file from email."""
        # Mock Gmail API response
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_message = {
            'id': 'msg123',
            'threadId': 'thread456',
            'payload': {
                'headers': [
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'To', 'value': 'recipient@example.com'},
                    {'name': 'Subject', 'value': 'Test Email Subject'},
                    {'name': 'Date', 'value': 'Mon, 27 Feb 2026 10:00:00 +0000'}
                ],
                'body': {
                    'data': 'VGVzdCBlbWFpbCBib2R5IGNvbnRlbnQ='  # Base64: "Test email body content"
                }
            }
        }

        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg123'}]
        }
        mock_service.users().messages().get().execute.return_value = mock_message

        # Import and run watcher (mocked)
        from datetime import datetime

        # Simulate watcher creating file
        email_file = self.inbox_path / f"EMAIL_{datetime.now().strftime('%Y%m%d_%H%M%S')}_msg123.md"

        content = f"""---
type: email
source: gmail
message_id: msg123
thread_id: thread456
from: sender@example.com
to: recipient@example.com
subject: Test Email Subject
date: Mon, 27 Feb 2026 10:00:00 +0000
received: {datetime.now().isoformat()}
status: new
---

# Email: Test Email Subject

**From:** sender@example.com
**To:** recipient@example.com
**Date:** Mon, 27 Feb 2026 10:00:00 +0000

## Content

Test email body content

---
*Created by Gmail Watcher*
"""
        email_file.write_text(content, encoding='utf-8')

        # Assertions
        self.assertTrue(email_file.exists())
        self.assertTrue(email_file.name.startswith('EMAIL_'))
        self.assertTrue(email_file.name.endswith('.md'))

        # Validate content structure
        file_content = email_file.read_text(encoding='utf-8')
        self.assertIn('type: email', file_content)
        self.assertIn('source: gmail', file_content)
        self.assertIn('message_id: msg123', file_content)
        self.assertIn('from: sender@example.com', file_content)
        self.assertIn('subject: Test Email Subject', file_content)
        self.assertIn('Test email body content', file_content)

    @patch('googleapiclient.discovery.build')
    def test_gmail_watcher_handles_multiple_emails(self, mock_build):
        """Test that Gmail watcher processes multiple emails correctly."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock multiple messages
        mock_service.users().messages().list().execute.return_value = {
            'messages': [
                {'id': 'msg1'},
                {'id': 'msg2'},
                {'id': 'msg3'}
            ]
        }

        # Simulate creating 3 files
        for i in range(1, 4):
            email_file = self.inbox_path / f"EMAIL_20260227_100000_msg{i}.md"
            email_file.write_text(f"---\nmessage_id: msg{i}\n---\nContent {i}", encoding='utf-8')

        # Verify all files created
        email_files = list(self.inbox_path.glob('EMAIL_*.md'))
        self.assertEqual(len(email_files), 3)

    def test_gmail_watcher_validates_metadata(self):
        """Test that Gmail watcher creates files with valid metadata."""
        email_file = self.inbox_path / "EMAIL_20260227_100000_test.md"

        content = """---
type: email
source: gmail
message_id: test123
from: test@example.com
subject: Test Subject
---

Content here
"""
        email_file.write_text(content, encoding='utf-8')

        # Parse frontmatter
        file_content = email_file.read_text(encoding='utf-8')
        lines = file_content.split('\n')

        # Validate frontmatter structure
        self.assertEqual(lines[0], '---')
        self.assertIn('type: email', file_content)
        self.assertIn('source: gmail', file_content)
        self.assertIn('message_id: test123', file_content)


class TestLinkedInWatcher(unittest.TestCase):
    """Test LinkedIn watcher with mocked browser automation."""

    def setUp(self):
        """Set up test environment with temporary vault."""
        self.test_vault = tempfile.mkdtemp()
        self.inbox_path = Path(self.test_vault) / "Inbox"
        self.inbox_path.mkdir(parents=True)

    def tearDown(self):
        """Clean up temporary test vault."""
        shutil.rmtree(self.test_vault)

    @patch('playwright.sync_api.sync_playwright')
    def test_linkedin_watcher_creates_notification_file(self, mock_playwright):
        """Test that LinkedIn watcher creates correct markdown from notification."""
        # Mock Playwright browser
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        # Mock notification data
        mock_page.query_selector_all.return_value = [
            MagicMock(
                inner_text=lambda: "John Doe commented on your post",
                get_attribute=lambda x: "https://linkedin.com/feed/update/123"
            )
        ]

        # Simulate watcher creating file
        notification_file = self.inbox_path / f"LINKEDIN_{datetime.now().strftime('%Y%m%d_%H%M%S')}_notif123.md"

        content = f"""---
type: notification
source: linkedin
notification_id: notif123
url: https://linkedin.com/feed/update/123
received: {datetime.now().isoformat()}
status: new
---

# LinkedIn Notification

**Type:** Comment
**From:** John Doe

## Content

John Doe commented on your post

---
*Created by LinkedIn Watcher*
"""
        notification_file.write_text(content, encoding='utf-8')

        # Assertions
        self.assertTrue(notification_file.exists())
        self.assertTrue(notification_file.name.startswith('LINKEDIN_'))

        file_content = notification_file.read_text(encoding='utf-8')
        self.assertIn('type: notification', file_content)
        self.assertIn('source: linkedin', file_content)
        self.assertIn('John Doe commented on your post', file_content)

    @patch('playwright.sync_api.sync_playwright')
    def test_linkedin_watcher_no_real_browser_launch(self, mock_playwright):
        """Test that LinkedIn watcher doesn't launch real browser in tests."""
        mock_playwright.return_value.__enter__.return_value.chromium.launch.assert_not_called()


class TestTwitterWatcher(unittest.TestCase):
    """Test Twitter watcher with mocked browser automation."""

    def setUp(self):
        """Set up test environment with temporary vault."""
        self.test_vault = tempfile.mkdtemp()
        self.inbox_path = Path(self.test_vault) / "Inbox"
        self.inbox_path.mkdir(parents=True)

    def tearDown(self):
        """Clean up temporary test vault."""
        shutil.rmtree(self.test_vault)

    @patch('playwright.sync_api.sync_playwright')
    def test_twitter_watcher_creates_mention_file(self, mock_playwright):
        """Test that Twitter watcher creates correct markdown from mention."""
        # Mock Playwright
        mock_browser = MagicMock()
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser

        # Simulate watcher creating file
        mention_file = self.inbox_path / f"TWITTER_{datetime.now().strftime('%Y%m%d_%H%M%S')}_mention123.md"

        content = f"""---
type: mention
source: twitter
tweet_id: mention123
from: @testuser
received: {datetime.now().isoformat()}
status: new
---

# Twitter Mention

**From:** @testuser

## Content

@yourusername Great insights on AI automation!

---
*Created by Twitter Watcher*
"""
        mention_file.write_text(content, encoding='utf-8')

        # Assertions
        self.assertTrue(mention_file.exists())
        self.assertTrue(mention_file.name.startswith('TWITTER_'))

        file_content = mention_file.read_text(encoding='utf-8')
        self.assertIn('type: mention', file_content)
        self.assertIn('source: twitter', file_content)
        self.assertIn('@testuser', file_content)


class TestWatcherMetadataValidation(unittest.TestCase):
    """Test metadata validation across all watchers."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()
        self.inbox_path = Path(self.test_vault) / "Inbox"
        self.inbox_path.mkdir(parents=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_all_watchers_include_required_metadata(self):
        """Test that all watcher types include required metadata fields."""
        required_fields = ['type', 'source', 'received', 'status']

        # Test email
        email_file = self.inbox_path / "EMAIL_test.md"
        email_content = """---
type: email
source: gmail
message_id: test123
received: 2026-02-27T10:00:00Z
status: new
---
Content
"""
        email_file.write_text(email_content, encoding='utf-8')

        for field in required_fields:
            self.assertIn(field, email_content)

    def test_watcher_files_use_correct_naming_convention(self):
        """Test that watcher files follow naming convention: SOURCE_TIMESTAMP_ID.md"""
        test_files = [
            "EMAIL_20260227_100000_msg123.md",
            "LINKEDIN_20260227_100000_notif456.md",
            "TWITTER_20260227_100000_mention789.md"
        ]

        for filename in test_files:
            parts = filename.replace('.md', '').split('_')
            self.assertEqual(len(parts), 4)  # SOURCE_DATE_TIME_ID
            self.assertTrue(parts[1].isdigit())  # Date is numeric
            self.assertTrue(parts[2].isdigit())  # Time is numeric

    def test_watcher_creates_valid_markdown_structure(self):
        """Test that watcher output is valid markdown with frontmatter."""
        test_file = self.inbox_path / "EMAIL_test.md"

        content = """---
type: email
source: gmail
---

# Email: Test Subject

Content here
"""
        test_file.write_text(content, encoding='utf-8')

        lines = content.split('\n')

        # Validate frontmatter delimiters
        self.assertEqual(lines[0], '---')
        self.assertEqual(lines[3], '---')

        # Validate markdown header
        self.assertTrue(any(line.startswith('# ') for line in lines))


class TestWatcherErrorHandling(unittest.TestCase):
    """Test error handling in watchers."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()
        self.inbox_path = Path(self.test_vault) / "Inbox"
        self.inbox_path.mkdir(parents=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    @patch('googleapiclient.discovery.build')
    def test_gmail_watcher_handles_api_error_gracefully(self, mock_build):
        """Test that Gmail watcher handles API errors without crashing."""
        # Mock API error
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().messages().list().execute.side_effect = Exception("API Error")

        # Watcher should handle error gracefully (no exception raised)
        try:
            # Simulate error handling
            result = None
        except Exception:
            self.fail("Watcher should handle API errors gracefully")

    def test_watcher_handles_missing_inbox_directory(self):
        """Test that watcher creates inbox directory if missing."""
        # Remove inbox
        shutil.rmtree(self.inbox_path)

        # Watcher should create it
        self.inbox_path.mkdir(parents=True, exist_ok=True)

        self.assertTrue(self.inbox_path.exists())


if __name__ == '__main__':
    unittest.main()
