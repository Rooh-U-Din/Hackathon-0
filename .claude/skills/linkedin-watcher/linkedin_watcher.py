#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Watcher Agent Skill
Monitors LinkedIn notifications/messages and creates markdown files in /Inbox/
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import logging
import re

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('linkedin_watcher')


class LinkedInWatcher:
    """LinkedIn watcher that monitors notifications and creates files in /Inbox/"""

    def __init__(self, vault_path: Path, session_path: Path):
        """
        Initialize LinkedIn watcher.

        Args:
            vault_path: Path to Obsidian vault
            session_path: Path to store LinkedIn session data
        """
        self.vault_path = vault_path
        self.inbox_path = vault_path / 'Inbox'
        self.logs_path = vault_path / 'Logs'
        self.session_path = session_path
        self.processed_ids_file = vault_path / '.linkedin_processed_ids.json'
        self.processed_ids = self._load_processed_ids()

        # Ensure directories exist
        self.inbox_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
        self.session_path.mkdir(exist_ok=True)

    def _load_processed_ids(self) -> set:
        """Load previously processed notification IDs."""
        if self.processed_ids_file.exists():
            try:
                data = json.loads(self.processed_ids_file.read_text())
                return set(data)
            except Exception as e:
                logger.warning(f"Could not load processed IDs: {e}")
        return set()

    def _save_processed_ids(self):
        """Save processed notification IDs to file."""
        try:
            self.processed_ids_file.write_text(
                json.dumps(list(self.processed_ids), indent=2)
            )
        except Exception as e:
            logger.error(f"Could not save processed IDs: {e}")

    def _create_notification_id(self, notification_text: str, timestamp: str) -> str:
        """Create a unique ID for a notification."""
        # Use hash of text + timestamp for uniqueness
        import hashlib
        content = f"{notification_text}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def launch_browser(self, headless=False):
        """
        Launch Playwright browser with persistent session.

        Args:
            headless: Run browser in headless mode

        Returns:
            Tuple of (browser_context, page) or (None, None) on failure
        """
        try:
            from playwright.sync_api import sync_playwright

            self.playwright = sync_playwright().start()

            # Launch persistent context to maintain LinkedIn session
            browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=headless,
                args=['--disable-blink-features=AutomationControlled']
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            logger.info("Browser launched successfully")
            return browser, page

        except ImportError:
            logger.error("Playwright not installed")
            logger.error("Run: pip install playwright && playwright install chromium")
            return None, None
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            return None, None

    def check_login_status(self, page):
        """
        Check if user is logged into LinkedIn.

        Args:
            page: Playwright page object

        Returns:
            True if logged in, False otherwise
        """
        try:
            page.goto('https://www.linkedin.com/feed/', timeout=30000)
            page.wait_for_timeout(3000)

            # Check for login indicators in URL
            if 'login' in page.url or 'authwall' in page.url or 'checkpoint' in page.url:
                logger.warning("Not logged in to LinkedIn")
                return False

            # If we're on /feed/ and not redirected to login, we're likely logged in
            if '/feed' in page.url:
                logger.info("LinkedIn login verified (on feed page)")
                return True

            # Try multiple selectors as additional verification
            selectors_to_try = [
                'nav.global-nav',  # Navigation bar
                '[data-test-id="feed-tab"]',  # Feed tab
                '.global-nav__me',  # Profile menu
                '.feed-identity-module',  # Feed identity
                'button[aria-label*="Me"]',  # Me button
                '.scaffold-layout__main'  # Main layout
            ]

            for selector in selectors_to_try:
                try:
                    if page.query_selector(selector):
                        logger.info(f"LinkedIn login verified (found {selector})")
                        return True
                except:
                    continue

            logger.warning("Could not verify LinkedIn login")
            return False

        except Exception as e:
            logger.error(f"Failed to check login status: {e}")
            return False

    def fetch_notifications(self, page, max_notifications=10):
        """
        Fetch new notifications from LinkedIn.

        Args:
            page: Playwright page object
            max_notifications: Maximum notifications to fetch

        Returns:
            List of notification dictionaries
        """
        try:
            logger.info("Fetching LinkedIn notifications...")

            # Navigate to notifications page
            page.goto('https://www.linkedin.com/notifications/', timeout=30000)
            page.wait_for_timeout(3000)

            # Wait for notifications to load
            try:
                page.wait_for_selector('.notifications-list', timeout=10000)
            except:
                logger.warning("Notifications list not found")
                return []

            # Get notification elements
            notifications = []
            notification_elements = page.query_selector_all('.notification-card')

            for elem in notification_elements[:max_notifications]:
                try:
                    # Extract notification text
                    text_elem = elem.query_selector('.notification-card__text')
                    text = text_elem.inner_text() if text_elem else "No text"

                    # Extract timestamp
                    time_elem = elem.query_selector('.notification-card__time')
                    timestamp = time_elem.inner_text() if time_elem else "Unknown time"

                    # Extract actor (who triggered the notification)
                    actor_elem = elem.query_selector('.notification-card__actor-text')
                    actor = actor_elem.inner_text() if actor_elem else "Unknown"

                    # Create unique ID
                    notif_id = self._create_notification_id(text, timestamp)

                    # Skip if already processed
                    if notif_id in self.processed_ids:
                        continue

                    notifications.append({
                        'id': notif_id,
                        'text': text.strip(),
                        'actor': actor.strip(),
                        'timestamp': timestamp.strip(),
                        'type': 'notification'
                    })

                except Exception as e:
                    logger.warning(f"Failed to parse notification: {e}")
                    continue

            logger.info(f"Found {len(notifications)} new notifications")
            return notifications

        except Exception as e:
            logger.error(f"Failed to fetch notifications: {e}")
            return []

    def fetch_messages(self, page, max_messages=5):
        """
        Fetch new messages from LinkedIn.

        Args:
            page: Playwright page object
            max_messages: Maximum messages to fetch

        Returns:
            List of message dictionaries
        """
        try:
            logger.info("Fetching LinkedIn messages...")

            # Navigate to messaging page
            page.goto('https://www.linkedin.com/messaging/', timeout=30000)
            page.wait_for_timeout(3000)

            # Wait for message list
            try:
                page.wait_for_selector('.msg-conversations-container', timeout=10000)
            except:
                logger.warning("Message list not found")
                return []

            # Get unread conversations
            messages = []
            conversation_elements = page.query_selector_all('.msg-conversation-listitem--unread')

            for elem in conversation_elements[:max_messages]:
                try:
                    # Extract sender name
                    name_elem = elem.query_selector('.msg-conversation-listitem__participant-names')
                    sender = name_elem.inner_text() if name_elem else "Unknown"

                    # Extract message preview
                    preview_elem = elem.query_selector('.msg-conversation-listitem__message-snippet')
                    preview = preview_elem.inner_text() if preview_elem else "No preview"

                    # Extract timestamp
                    time_elem = elem.query_selector('.msg-conversation-listitem__time-stamp')
                    timestamp = time_elem.inner_text() if time_elem else "Unknown time"

                    # Create unique ID
                    msg_id = self._create_notification_id(f"{sender}_{preview}", timestamp)

                    # Skip if already processed
                    if msg_id in self.processed_ids:
                        continue

                    messages.append({
                        'id': msg_id,
                        'sender': sender.strip(),
                        'preview': preview.strip(),
                        'timestamp': timestamp.strip(),
                        'type': 'message'
                    })

                except Exception as e:
                    logger.warning(f"Failed to parse message: {e}")
                    continue

            logger.info(f"Found {len(messages)} new messages")
            return messages

        except Exception as e:
            logger.error(f"Failed to fetch messages: {e}")
            return []

    def create_inbox_file(self, item):
        """
        Create markdown file in /Inbox/ for the LinkedIn item.

        Args:
            item: Dictionary with notification or message details

        Returns:
            Path to created file or None
        """
        try:
            # Create safe filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            item_type = item['type'].upper()
            filename = f'LINKEDIN_{item_type}_{timestamp}_{item["id"]}.md'
            filepath = self.inbox_path / filename

            # Create markdown content based on type
            if item['type'] == 'notification':
                content = f"""---
type: linkedin_notification
source: linkedin
notification_id: {item['id']}
actor: {item['actor']}
timestamp: {item['timestamp']}
received: {datetime.now().isoformat()}
status: new
---

# LinkedIn Notification

**From:** {item['actor']}
**Time:** {item['timestamp']}

## Content

{item['text']}

## Next Steps

This LinkedIn notification has been detected and placed in the Inbox for processing.
The AI Employee will:
1. Read this file from /Inbox
2. Analyze the content and determine action
3. Create an action item in /Needs_Action if needed
4. Process according to Company_Handbook.md rules

---
*Created by LinkedIn Watcher Agent Skill*
"""
            else:  # message
                content = f"""---
type: linkedin_message
source: linkedin
message_id: {item['id']}
sender: {item['sender']}
timestamp: {item['timestamp']}
received: {datetime.now().isoformat()}
status: new
---

# LinkedIn Message

**From:** {item['sender']}
**Time:** {item['timestamp']}

## Preview

{item['preview']}

## Next Steps

This LinkedIn message has been detected and placed in the Inbox for processing.
The AI Employee will:
1. Read this file from /Inbox
2. Analyze the message content
3. Create an action item in /Needs_Action
4. Draft a response if needed (requires approval)

---
*Created by LinkedIn Watcher Agent Skill*
"""

            # Write file
            filepath.write_text(content, encoding='utf-8')
            logger.info(f"Created inbox file: {filename}")

            return filepath

        except Exception as e:
            logger.error(f"Failed to create inbox file: {e}")
            return None

    def log_activity(self, activity_type, details):
        """
        Log watcher activity.

        Args:
            activity_type: Type of activity (check, new_item, error)
            details: Dictionary with activity details
        """
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'activity': activity_type,
                **details
            }

            log_file = self.logs_path / f'{datetime.now().strftime("%Y-%m-%d")}_linkedin_watcher.json'

            # Load existing logs
            logs = []
            if log_file.exists():
                logs = json.loads(log_file.read_text())

            # Append new entry
            logs.append(log_entry)

            # Save logs
            log_file.write_text(json.dumps(logs, indent=2))

        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

    def run(self, max_notifications=10, max_messages=5, headless=True):
        """
        Run the watcher - check for new notifications and messages.

        Args:
            max_notifications: Maximum notifications to process
            max_messages: Maximum messages to process
            headless: Run browser in headless mode

        Returns:
            Number of new items processed
        """
        logger.info("Starting LinkedIn watcher...")

        # Launch browser
        browser, page = self.launch_browser(headless=headless)
        if not browser or not page:
            return 0

        try:
            # Check login status
            if not self.check_login_status(page):
                if not headless:
                    # In visible mode, wait for manual login
                    logger.warning("Not logged in to LinkedIn")
                    logger.info("=" * 60)
                    logger.info("PLEASE LOG IN TO LINKEDIN IN THE BROWSER WINDOW")
                    logger.info("You have 120 seconds to complete the login...")
                    logger.info("=" * 60)

                    # Wait for user to log in
                    import time
                    for i in range(12):  # 12 * 10 = 120 seconds
                        time.sleep(10)
                        logger.info(f"Waiting for login... ({(i+1)*10}/120 seconds)")

                        # Check if logged in now
                        if self.check_login_status(page):
                            logger.info("Login successful! Continuing...")
                            break
                    else:
                        # Still not logged in after waiting
                        logger.error("Login timeout - still not logged in after 120 seconds")
                        browser.close()
                        return 0
                else:
                    # In headless mode, can't log in manually
                    logger.error("Not logged in to LinkedIn")
                    logger.info("Please run with --headless false to log in manually")
                    browser.close()
                    return 0

            # Fetch notifications
            notifications = self.fetch_notifications(page, max_notifications)

            # Fetch messages
            messages = self.fetch_messages(page, max_messages)

            # Combine all items
            all_items = notifications + messages

            if not all_items:
                logger.info("No new items to process")
                self.log_activity('check', {
                    'new_notifications': 0,
                    'new_messages': 0
                })
                browser.close()
                return 0

            # Process each item
            processed_count = 0
            for item in all_items:
                try:
                    # Create inbox file
                    filepath = self.create_inbox_file(item)
                    if not filepath:
                        continue

                    # Mark as processed
                    self.processed_ids.add(item['id'])
                    processed_count += 1

                    logger.info(f"Processed {item['type']}: {item.get('text', item.get('preview', ''))[:50]}")

                except Exception as e:
                    logger.error(f"Error processing item {item['id']}: {e}")
                    continue

            # Save processed IDs
            self._save_processed_ids()

            # Log activity
            self.log_activity('check', {
                'new_notifications': len(notifications),
                'new_messages': len(messages),
                'total_processed': processed_count
            })

            logger.info(f"LinkedIn watcher complete: {processed_count} items processed")

            browser.close()
            return processed_count

        except Exception as e:
            logger.error(f"Watcher failed: {e}")
            if browser:
                browser.close()
            return 0


def main():
    """Main entry point for LinkedIn watcher skill."""
    print("LinkedIn Watcher Agent Skill")
    print("=" * 50)
    print()

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='LinkedIn Watcher Agent Skill')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault',
                       help='Path to Obsidian vault')
    parser.add_argument('--session', type=str, default='./linkedin_session',
                       help='Path to store LinkedIn session')
    parser.add_argument('--max-notifications', type=int, default=10,
                       help='Maximum notifications to process')
    parser.add_argument('--max-messages', type=int, default=5,
                       help='Maximum messages to process')
    parser.add_argument('--headless', type=str, default='true',
                       choices=['true', 'false'],
                       help='Run browser in headless mode')
    args = parser.parse_args()

    # Validate paths
    vault_path = Path(args.vault)
    session_path = Path(args.session)

    if not vault_path.exists():
        print(f"[ERROR] Vault not found: {vault_path}")
        return 1

    headless = args.headless.lower() == 'true'

    # Create and run watcher
    try:
        watcher = LinkedInWatcher(vault_path, session_path)
        count = watcher.run(
            max_notifications=args.max_notifications,
            max_messages=args.max_messages,
            headless=headless
        )

        print()
        print(f"[SUCCESS] Processed {count} new item(s)")
        print(f"[INFO] Files created in: {vault_path / 'Inbox'}")
        print()

        return 0

    except KeyboardInterrupt:
        print("\n[STOPPED] Watcher interrupted by user")
        return 0
    except Exception as e:
        print(f"[ERROR] Watcher failed: {e}")
        logger.exception("Watcher failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
