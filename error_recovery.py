#!/usr/bin/env python3
"""
Error Recovery and Retry Handler
Provides comprehensive error handling with exponential backoff retry logic
"""
import time
import logging
from functools import wraps
from typing import Callable, Any, Type
from enum import Enum

logger = logging.getLogger('error_recovery')

class ErrorCategory(Enum):
    """Error categories for different handling strategies."""
    TRANSIENT = "transient"  # Network timeout, API rate limit
    AUTHENTICATION = "authentication"  # Expired token, revoked access
    LOGIC = "logic"  # Claude misinterprets message
    DATA = "data"  # Corrupted file, missing field
    SYSTEM = "system"  # Orchestrator crash, disk full

class TransientError(Exception):
    """Errors that can be retried."""
    pass

class AuthenticationError(Exception):
    """Authentication failures requiring human intervention."""
    pass

class LogicError(Exception):
    """Logic errors requiring human review."""
    pass

class DataError(Exception):
    """Data corruption or validation errors."""
    pass

class SystemError(Exception):
    """System-level failures."""
    pass

def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (TransientError,)
):
    """
    Decorator for automatic retry with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to retry

    Example:
        @with_retry(max_attempts=3, base_delay=1, max_delay=60)
        def fetch_data():
            # Code that might fail transiently
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts - 1:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    time.sleep(delay)

            # Should never reach here, but just in case
            raise last_exception

        return wrapper
    return decorator

def categorize_error(error: Exception) -> ErrorCategory:
    """
    Categorize an error for appropriate handling.

    Args:
        error: The exception to categorize

    Returns:
        ErrorCategory enum value
    """
    error_type = type(error).__name__
    error_msg = str(error).lower()

    # Transient errors
    if any(keyword in error_msg for keyword in ['timeout', 'rate limit', 'connection', 'network']):
        return ErrorCategory.TRANSIENT

    # Authentication errors
    if any(keyword in error_msg for keyword in ['auth', 'token', 'credential', 'permission']):
        return ErrorCategory.AUTHENTICATION

    # Data errors
    if any(keyword in error_msg for keyword in ['corrupt', 'invalid', 'missing field', 'parse']):
        return ErrorCategory.DATA

    # System errors
    if any(keyword in error_msg for keyword in ['disk full', 'memory', 'crash', 'killed']):
        return ErrorCategory.SYSTEM

    # Default to logic error
    return ErrorCategory.LOGIC

def get_recovery_strategy(category: ErrorCategory) -> dict:
    """
    Get recovery strategy for an error category.

    Args:
        category: ErrorCategory enum value

    Returns:
        Dictionary with recovery strategy details
    """
    strategies = {
        ErrorCategory.TRANSIENT: {
            'action': 'retry',
            'max_attempts': 3,
            'alert_human': False,
            'pause_operations': False
        },
        ErrorCategory.AUTHENTICATION: {
            'action': 'alert',
            'max_attempts': 0,
            'alert_human': True,
            'pause_operations': True
        },
        ErrorCategory.LOGIC: {
            'action': 'queue_for_review',
            'max_attempts': 0,
            'alert_human': True,
            'pause_operations': False
        },
        ErrorCategory.DATA: {
            'action': 'quarantine',
            'max_attempts': 0,
            'alert_human': True,
            'pause_operations': False
        },
        ErrorCategory.SYSTEM: {
            'action': 'restart',
            'max_attempts': 1,
            'alert_human': True,
            'pause_operations': True
        }
    }

    return strategies.get(category, strategies[ErrorCategory.LOGIC])

class GracefulDegradation:
    """
    Handles graceful degradation when components fail.
    """

    @staticmethod
    def handle_gmail_api_down(email_data: dict) -> bool:
        """
        Queue outgoing emails locally when Gmail API is down.

        Args:
            email_data: Email data to queue

        Returns:
            True if queued successfully
        """
        from pathlib import Path
        import json
        from datetime import datetime

        queue_dir = Path('./email_queue')
        queue_dir.mkdir(exist_ok=True)

        queue_file = queue_dir / f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            queue_file.write_text(json.dumps(email_data, indent=2), encoding='utf-8')
            logger.info(f"Email queued locally: {queue_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to queue email: {e}")
            return False

    @staticmethod
    def handle_banking_api_timeout() -> dict:
        """
        Never retry payments automatically on timeout.

        Returns:
            Error response requiring fresh approval
        """
        logger.error("Banking API timeout - payment NOT retried")
        return {
            'success': False,
            'error': 'Banking API timeout',
            'action_required': 'Request fresh approval for payment',
            'auto_retry': False
        }

    @staticmethod
    def handle_claude_unavailable(task_data: dict) -> bool:
        """
        Queue tasks when Claude Code is unavailable.

        Args:
            task_data: Task data to queue

        Returns:
            True if queued successfully
        """
        from pathlib import Path
        import json
        from datetime import datetime

        queue_dir = Path('./task_queue')
        queue_dir.mkdir(exist_ok=True)

        queue_file = queue_dir / f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            queue_file.write_text(json.dumps(task_data, indent=2), encoding='utf-8')
            logger.info(f"Task queued for later processing: {queue_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to queue task: {e}")
            return False

    @staticmethod
    def handle_vault_locked(data: dict) -> bool:
        """
        Write to temporary folder when vault is locked.

        Args:
            data: Data to write temporarily

        Returns:
            True if written successfully
        """
        from pathlib import Path
        import json
        from datetime import datetime

        temp_dir = Path('./temp_vault')
        temp_dir.mkdir(exist_ok=True)

        temp_file = temp_dir / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            temp_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
            logger.info(f"Data written to temp folder: {temp_file}")
            logger.info("Will sync to vault when available")
            return True
        except Exception as e:
            logger.error(f"Failed to write to temp folder: {e}")
            return False

# Example usage
if __name__ == '__main__':
    # Example: Retry transient errors
    @with_retry(max_attempts=3, base_delay=1, max_delay=10)
    def fetch_api_data():
        import random
        if random.random() < 0.7:  # 70% failure rate for demo
            raise TransientError("API timeout")
        return {"data": "success"}

    try:
        result = fetch_api_data()
        print(f"Success: {result}")
    except TransientError as e:
        print(f"Failed after retries: {e}")

    # Example: Categorize and handle error
    try:
        raise Exception("Authentication token expired")
    except Exception as e:
        category = categorize_error(e)
        strategy = get_recovery_strategy(category)
        print(f"Error category: {category}")
        print(f"Recovery strategy: {strategy}")
