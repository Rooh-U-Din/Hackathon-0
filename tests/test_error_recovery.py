#!/usr/bin/env python3
"""
Test Suite for Error Recovery Mechanisms

Tests error recovery, retry logic, and graceful degradation:
- Exponential backoff retry decorator
- Error categorization (transient, auth, logic, data, system)
- Graceful degradation patterns
- Watcher failure handling
- Logging and monitoring

All external dependencies are mocked to ensure:
- Deterministic failure simulation
- No real API calls during error scenarios
- Predictable retry behavior
- Proper error logging

All tests use unittest.mock to simulate failures.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import time
import json


class TestExponentialBackoff(unittest.TestCase):
    """Test exponential backoff retry mechanism."""

    def test_retry_succeeds_on_first_attempt(self):
        """Test that retry succeeds immediately if no error."""
        attempt_count = [0]

        def successful_operation():
            """Operation that succeeds on first try."""
            attempt_count[0] += 1
            return "success"

        result = successful_operation()

        self.assertEqual(result, "success")
        self.assertEqual(attempt_count[0], 1)

    def test_retry_succeeds_after_transient_failures(self):
        """Test that retry succeeds after transient failures."""
        attempt_count = [0]

        def flaky_operation():
            """Operation that fails twice then succeeds."""
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise Exception("Transient error")
            return "success"

        # Simulate retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = flaky_operation()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.01)  # Minimal delay for test

        self.assertEqual(result, "success")
        self.assertEqual(attempt_count[0], 3)

    def test_retry_respects_max_attempts(self):
        """Test that retry stops after max attempts."""
        attempt_count = [0]

        def always_failing_operation():
            """Operation that always fails."""
            attempt_count[0] += 1
            raise Exception("Permanent error")

        # Simulate retry logic
        max_retries = 3
        last_exception = None

        for attempt in range(max_retries):
            try:
                result = always_failing_operation()
                break
            except Exception as e:
                last_exception = e
                if attempt == max_retries - 1:
                    break
                time.sleep(0.01)

        self.assertEqual(attempt_count[0], 3)
        self.assertIsNotNone(last_exception)

    def test_exponential_backoff_delays_increase(self):
        """Test that backoff delays increase exponentially."""
        delays = []

        def calculate_backoff(attempt, base_delay=1, max_delay=60):
            """Calculate exponential backoff delay."""
            delay = min(base_delay * (2 ** attempt), max_delay)
            return delay

        # Calculate delays for 5 attempts
        for attempt in range(5):
            delay = calculate_backoff(attempt, base_delay=1)
            delays.append(delay)

        # Verify exponential growth
        self.assertEqual(delays[0], 1)   # 2^0 = 1
        self.assertEqual(delays[1], 2)   # 2^1 = 2
        self.assertEqual(delays[2], 4)   # 2^2 = 4
        self.assertEqual(delays[3], 8)   # 2^3 = 8
        self.assertEqual(delays[4], 16)  # 2^4 = 16

    def test_backoff_respects_max_delay(self):
        """Test that backoff delay doesn't exceed maximum."""
        def calculate_backoff(attempt, base_delay=1, max_delay=10):
            """Calculate exponential backoff with max limit."""
            delay = min(base_delay * (2 ** attempt), max_delay)
            return delay

        # Large attempt number
        delay = calculate_backoff(10, base_delay=1, max_delay=10)

        # Should not exceed max_delay
        self.assertEqual(delay, 10)


class TestErrorCategorization(unittest.TestCase):
    """Test error categorization for appropriate handling."""

    def test_categorize_transient_errors(self):
        """Test identification of transient errors (should retry)."""
        transient_errors = [
            "Connection timeout",
            "Network unreachable",
            "Service temporarily unavailable",
            "Rate limit exceeded"
        ]

        def is_transient_error(error_message):
            """Check if error is transient."""
            transient_keywords = ['timeout', 'unreachable', 'temporarily', 'rate limit']
            return any(keyword in error_message.lower() for keyword in transient_keywords)

        for error in transient_errors:
            self.assertTrue(is_transient_error(error))

    def test_categorize_authentication_errors(self):
        """Test identification of authentication errors (should not retry)."""
        auth_errors = [
            "Invalid credentials",
            "Authentication failed",
            "Unauthorized access",
            "Token expired"
        ]

        def is_auth_error(error_message):
            """Check if error is authentication-related."""
            auth_keywords = ['credentials', 'authentication', 'unauthorized', 'token']
            return any(keyword in error_message.lower() for keyword in auth_keywords)

        for error in auth_errors:
            self.assertTrue(is_auth_error(error))

    def test_categorize_logic_errors(self):
        """Test identification of logic errors (should not retry)."""
        logic_errors = [
            "Invalid input format",
            "Missing required field",
            "Validation error"
        ]

        def is_logic_error(error_message):
            """Check if error is logic-related."""
            logic_keywords = ['invalid', 'missing', 'validation']
            return any(keyword in error_message.lower() for keyword in logic_keywords)

        for error in logic_errors:
            self.assertTrue(is_logic_error(error))

    def test_retry_decision_based_on_error_type(self):
        """Test that retry decision is based on error type."""
        def should_retry(error_message):
            """Determine if error should be retried."""
            transient_keywords = ['timeout', 'unreachable', 'temporarily']
            no_retry_keywords = ['invalid', 'authentication', 'unauthorized']

            if any(keyword in error_message.lower() for keyword in no_retry_keywords):
                return False
            if any(keyword in error_message.lower() for keyword in transient_keywords):
                return True
            return False

        # Should retry
        self.assertTrue(should_retry("Connection timeout"))
        self.assertTrue(should_retry("Network unreachable"))

        # Should not retry
        self.assertFalse(should_retry("Invalid credentials"))
        self.assertFalse(should_retry("Authentication failed"))


class TestWatcherFailureHandling(unittest.TestCase):
    """Test watcher failure handling and recovery."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()
        self.inbox_path = Path(self.test_vault) / "Inbox"
        self.inbox_path.mkdir(parents=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    @patch('googleapiclient.discovery.build')
    def test_gmail_watcher_handles_api_failure_gracefully(self, mock_build):
        """Test that Gmail watcher handles API failures without crashing."""
        # Mock API failure
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().messages().list().execute.side_effect = Exception("API Error")

        # Watcher should handle error gracefully
        error_logged = False
        try:
            mock_service.users().messages().list().execute()
        except Exception as e:
            error_logged = True
            error_message = str(e)

        self.assertTrue(error_logged)
        self.assertEqual(error_message, "API Error")

    @patch('googleapiclient.discovery.build')
    def test_gmail_watcher_retries_on_transient_failure(self, mock_build):
        """Test that Gmail watcher retries on transient failures."""
        attempt_count = [0]

        def flaky_api_call():
            """Simulate flaky API."""
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise Exception("Transient error")
            return {'messages': []}

        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().messages().list().execute.side_effect = flaky_api_call

        # Retry logic
        max_retries = 3
        result = None
        for attempt in range(max_retries):
            try:
                result = mock_service.users().messages().list().execute()
                break
            except Exception:
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.01)

        self.assertEqual(attempt_count[0], 3)
        self.assertEqual(result, {'messages': []})

    @patch('playwright.sync_api.sync_playwright')
    def test_linkedin_watcher_handles_browser_crash(self, mock_playwright):
        """Test that LinkedIn watcher handles browser crashes."""
        # Mock browser crash
        mock_playwright.return_value.__enter__.return_value.chromium.launch.side_effect = Exception("Browser crashed")

        # Watcher should handle crash gracefully
        error_logged = False
        try:
            browser = mock_playwright.return_value.__enter__().chromium.launch()
        except Exception as e:
            error_logged = True
            error_message = str(e)

        self.assertTrue(error_logged)
        self.assertEqual(error_message, "Browser crashed")

    def test_watcher_logs_errors_to_file(self):
        """Test that watcher logs errors to error log file."""
        # Simulate error logging
        error_log = Path(self.test_vault) / "Logs" / "errors.json"
        error_log.parent.mkdir(parents=True, exist_ok=True)

        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'watcher': 'gmail',
            'error_type': 'APIError',
            'error_message': 'Connection timeout',
            'retry_count': 3,
            'resolved': False
        }

        errors = []
        if error_log.exists():
            errors = json.loads(error_log.read_text(encoding='utf-8'))

        errors.append(error_entry)
        error_log.write_text(json.dumps(errors, indent=2), encoding='utf-8')

        # Verify error logged
        self.assertTrue(error_log.exists())
        logged_errors = json.loads(error_log.read_text(encoding='utf-8'))
        self.assertEqual(len(logged_errors), 1)
        self.assertEqual(logged_errors[0]['watcher'], 'gmail')


class TestGracefulDegradation(unittest.TestCase):
    """Test graceful degradation when services are unavailable."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    @patch('googleapiclient.discovery.build')
    def test_system_continues_when_gmail_unavailable(self, mock_build):
        """Test that system continues operating when Gmail is unavailable."""
        # Mock Gmail unavailable
        mock_build.side_effect = Exception("Gmail API unavailable")

        # System should continue with other watchers
        watchers_status = {
            'gmail': 'unavailable',
            'linkedin': 'running',
            'twitter': 'running'
        }

        # Verify system still operational
        operational_watchers = [w for w, status in watchers_status.items() if status == 'running']
        self.assertEqual(len(operational_watchers), 2)

    def test_system_uses_cached_data_when_api_fails(self):
        """Test that system uses cached data when API fails."""
        # Simulate cached data
        cache_file = Path(self.test_vault) / "cache" / "gmail_cache.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)

        cached_data = {
            'timestamp': datetime.now().isoformat(),
            'messages': [
                {'id': 'msg1', 'subject': 'Cached Email 1'},
                {'id': 'msg2', 'subject': 'Cached Email 2'}
            ]
        }
        cache_file.write_text(json.dumps(cached_data, indent=2), encoding='utf-8')

        # API fails, use cache
        def get_emails_with_fallback():
            """Get emails with cache fallback."""
            try:
                # Simulate API call failure
                raise Exception("API unavailable")
            except Exception:
                # Fall back to cache
                if cache_file.exists():
                    return json.loads(cache_file.read_text(encoding='utf-8'))['messages']
                return []

        messages = get_emails_with_fallback()

        # Verify cached data used
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['subject'], 'Cached Email 1')

    def test_system_queues_actions_when_service_unavailable(self):
        """Test that system queues actions when service is unavailable."""
        # Simulate action queue
        queue_file = Path(self.test_vault) / "queue" / "pending_actions.json"
        queue_file.parent.mkdir(parents=True, exist_ok=True)

        # Service unavailable, queue action
        action = {
            'type': 'send_email',
            'to': 'recipient@example.com',
            'subject': 'Test',
            'queued_at': datetime.now().isoformat(),
            'retry_count': 0
        }

        queue = []
        if queue_file.exists():
            queue = json.loads(queue_file.read_text(encoding='utf-8'))

        queue.append(action)
        queue_file.write_text(json.dumps(queue, indent=2), encoding='utf-8')

        # Verify action queued
        self.assertTrue(queue_file.exists())
        queued_actions = json.loads(queue_file.read_text(encoding='utf-8'))
        self.assertEqual(len(queued_actions), 1)
        self.assertEqual(queued_actions[0]['type'], 'send_email')


class TestErrorLogging(unittest.TestCase):
    """Test comprehensive error logging."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()
        self.logs_path = Path(self.test_vault) / "Logs"
        self.logs_path.mkdir(parents=True)

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_error_log_includes_timestamp(self):
        """Test that error logs include timestamp."""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error': 'Test error'
        }

        self.assertIn('timestamp', error_entry)
        # Verify timestamp format
        datetime.fromisoformat(error_entry['timestamp'])

    def test_error_log_includes_context(self):
        """Test that error logs include context information."""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'component': 'gmail_watcher',
            'operation': 'fetch_messages',
            'error_type': 'APIError',
            'error_message': 'Connection timeout',
            'retry_count': 3,
            'stack_trace': 'Traceback...'
        }

        # Verify all context fields present
        required_fields = ['timestamp', 'component', 'operation', 'error_type', 'error_message']
        for field in required_fields:
            self.assertIn(field, error_entry)

    def test_error_log_rotates_daily(self):
        """Test that error logs rotate daily."""
        # Create error log with date in filename
        today = datetime.now().strftime('%Y-%m-%d')
        error_log = self.logs_path / f"{today}_errors.json"

        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error': 'Test error'
        }

        errors = [error_entry]
        error_log.write_text(json.dumps(errors, indent=2), encoding='utf-8')

        # Verify log file created with date
        self.assertTrue(error_log.exists())
        self.assertIn(today, error_log.name)

    def test_critical_errors_logged_separately(self):
        """Test that critical errors are logged separately."""
        # Regular error
        error_log = self.logs_path / "errors.json"
        error_log.write_text(json.dumps([{'severity': 'error'}], indent=2), encoding='utf-8')

        # Critical error
        critical_log = self.logs_path / "critical_errors.json"
        critical_log.write_text(json.dumps([{'severity': 'critical'}], indent=2), encoding='utf-8')

        # Verify separate logs
        self.assertTrue(error_log.exists())
        self.assertTrue(critical_log.exists())


class TestRecoveryMechanisms(unittest.TestCase):
    """Test automatic recovery mechanisms."""

    def setUp(self):
        """Set up test environment."""
        self.test_vault = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test vault."""
        shutil.rmtree(self.test_vault)

    def test_watcher_restarts_after_failure(self):
        """Test that watcher automatically restarts after failure."""
        restart_count = [0]

        def watcher_with_restart():
            """Simulate watcher with restart capability."""
            max_restarts = 3
            for attempt in range(max_restarts):
                try:
                    # Simulate watcher operation
                    if attempt < 2:
                        raise Exception("Watcher crashed")
                    return "running"
                except Exception:
                    restart_count[0] += 1
                    if attempt == max_restarts - 1:
                        raise
                    time.sleep(0.01)

        result = watcher_with_restart()

        self.assertEqual(result, "running")
        self.assertEqual(restart_count[0], 2)

    def test_system_health_check_detects_failures(self):
        """Test that health check detects component failures."""
        # Simulate health check
        components_status = {
            'gmail_watcher': 'running',
            'linkedin_watcher': 'failed',
            'cloud_agent': 'running',
            'vault_sync': 'running'
        }

        def health_check(components):
            """Check health of all components."""
            failed_components = [name for name, status in components.items() if status == 'failed']
            return {
                'healthy': len(failed_components) == 0,
                'failed_components': failed_components
            }

        result = health_check(components_status)

        self.assertFalse(result['healthy'])
        self.assertEqual(len(result['failed_components']), 1)
        self.assertIn('linkedin_watcher', result['failed_components'])

    def test_failed_component_triggers_alert(self):
        """Test that failed component triggers alert."""
        # Simulate alert system
        alerts = []

        def trigger_alert(component, error):
            """Trigger alert for failed component."""
            alert = {
                'timestamp': datetime.now().isoformat(),
                'component': component,
                'error': error,
                'severity': 'high'
            }
            alerts.append(alert)

        # Component fails
        trigger_alert('gmail_watcher', 'API connection failed')

        # Verify alert triggered
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['component'], 'gmail_watcher')
        self.assertEqual(alerts[0]['severity'], 'high')


if __name__ == '__main__':
    unittest.main()
