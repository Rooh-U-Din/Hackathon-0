#!/usr/bin/env python3
"""
Twitter (X) Watcher - Monitors mentions, DMs, and notifications
Uses Playwright for browser automation
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('twitter_watcher')

class TwitterWatcher:
    """Monitors Twitter for mentions, DMs, and notifications."""

    def __init__(self, vault_path: Path, session_path: Path):
        self.vault_path = vault_path
        self.inbox_path = vault_path / 'Inbox'
        self.logs_path = vault_path / 'Logs'
        self.session_path = session_path
        self.processed_ids_file = vault_path / '.twitter_processed_ids.json'

        # Ensure directories exist
        self.inbox_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
        self.session_path.mkdir(exist_ok=True)

        # Load processed IDs
        self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self) -> set:
        """Load previously processed notification IDs."""
        if self.processed_ids_file.exists():
            try:
                content = self.processed_ids_file.read_text(encoding='utf-8')
                return set(json.loads(content))
            except Exception as e:
                logger.warning(f"Failed to load processed IDs: {e}")
        return set()

    def _save_processed_ids(self):
        """Save processed notification IDs."""
        try:
            self.processed_ids_file.write_text(
                json.dumps(list(self.processed_ids), indent=2),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"Failed to save processed IDs: {e}")

    def check_login_status(self, page) -> bool:
        """Check if user is logged in to Twitter."""
        try:
            # Check for login indicators
            page.wait_for_selector('[data-testid="SideNav_AccountSwitcher_Button"]', timeout=5000)
            return True
        except PlaywrightTimeout:
            return False

    def fetch_notifications(self, page, max_notifications: int = 10) -> list:
        """Fetch notifications from Twitter."""
        notifications = []

        try:
            logger.info("Navigating to notifications...")
            page.goto('https://twitter.com/notifications', wait_until='networkidle')
            page.wait_for_timeout(2000)

            # Find notification elements
            notification_elements = page.query_selector_all('[data-testid="cellInnerDiv"]')
            logger.info(f"Found {len(notification_elements)} notification elements")

            for elem in notification_elements[:max_notifications]:
                try:
                    # Extract notification text
                    text_content = elem.inner_text()

                    if not text_content or len(text_content.strip()) < 5:
                        continue

                    # Generate unique ID from content hash
                    notification_id = str(hash(text_content))

                    # Skip if already processed
                    if notification_id in self.processed_ids:
                        continue

                    # Extract notification details
                    notification = {
                        'id': notification_id,
                        'content': text_content[:500],  # Limit length
                        'timestamp': datetime.now().isoformat(),
                        'type': 'notification'
                    }

                    notifications.append(notification)
                    logger.info(f"Captured notification: {notification_id}")

                except Exception as e:
                    logger.warning(f"Failed to parse notification: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to fetch notifications: {e}")

        return notifications

    def fetch_mentions(self, page, max_mentions: int = 10) -> list:
        """Fetch mentions from Twitter."""
        mentions = []

        try:
            logger.info("Navigating to mentions...")
            page.goto('https://twitter.com/notifications/mentions', wait_until='networkidle')
            page.wait_for_timeout(2000)

            # Find mention elements
            mention_elements = page.query_selector_all('[data-testid="tweet"]')
            logger.info(f"Found {len(mention_elements)} mention elements")

            for elem in mention_elements[:max_mentions]:
                try:
                    # Extract mention text
                    text_content = elem.inner_text()

                    if not text_content or len(text_content.strip()) < 5:
                        continue

                    # Generate unique ID
                    mention_id = str(hash(text_content))

                    # Skip if already processed
                    if mention_id in self.processed_ids:
                        continue

                    # Extract author if possible
                    author = "Unknown"
                    try:
                        author_elem = elem.query_selector('[data-testid="User-Name"]')
                        if author_elem:
                            author = author_elem.inner_text().split('\n')[0]
                    except:
                        pass

                    mention = {
                        'id': mention_id,
                        'author': author,
                        'content': text_content[:500],
                        'timestamp': datetime.now().isoformat(),
                        'type': 'mention'
                    }

                    mentions.append(mention)
                    logger.info(f"Captured mention from {author}")

                except Exception as e:
                    logger.warning(f"Failed to parse mention: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to fetch mentions: {e}")

        return mentions

    def create_inbox_file(self, item: dict) -> Path:
        """Create markdown file in Inbox for a Twitter item."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        item_id = item['id'][:8]
        filename = f"TWITTER_{timestamp}_{item_id}.md"
        filepath = self.inbox_path / filename

        # Determine title based on type
        if item['type'] == 'mention':
            title = f"Twitter Mention from {item.get('author', 'Unknown')}"
        else:
            title = "Twitter Notification"

        content = f"""---
type: twitter_{item['type']}
source: twitter
item_id: {item['id']}
author: {item.get('author', 'N/A')}
timestamp: {item.get('timestamp', 'N/A')}
received: {datetime.now().isoformat()}
status: new
---

# {title}

**From:** {item.get('author', 'N/A')}
**Time:** {item.get('timestamp', 'N/A')}

## Content

{item['content']}

## Next Steps

This Twitter {item['type']} has been detected and placed in the Inbox for processing.
The AI Employee will:
1. Read this file from /Inbox
2. Analyze the content and priority
3. Create an action item in /Needs_Action if required
4. Process according to Company_Handbook.md rules

---
*Created by Twitter Watcher Agent Skill*
"""

        try:
            filepath.write_text(content, encoding='utf-8')
            logger.info(f"Created inbox file: {filename}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to create inbox file: {e}")
            return None

    def log_activity(self, activity: dict):
        """Log watcher activity."""
        log_file = self.logs_path / f"{datetime.now().strftime('%Y-%m-%d')}_twitter_watcher.json"

        try:
            # Append to existing log
            if log_file.exists():
                content = log_file.read_text(encoding='utf-8')
                logs = json.loads(content) if content.strip() else []
            else:
                logs = []

            logs.append(activity)
            log_file.write_text(json.dumps(logs, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

    def run(self, headless: bool = True, max_notifications: int = 10, max_mentions: int = 10) -> int:
        """Run the Twitter watcher."""
        logger.info("Starting Twitter watcher...")

        with sync_playwright() as p:
            try:
                # Launch browser with persistent context
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=headless,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Check login status
                page.goto('https://twitter.com/home', wait_until='networkidle')

                if not self.check_login_status(page):
                    logger.error("Not logged in to Twitter")
                    logger.info("Please run with --headless false to log in")
                    browser.close()
                    return 0

                logger.info("Twitter login verified")

                # Fetch notifications
                notifications = self.fetch_notifications(page, max_notifications)
                logger.info(f"Found {len(notifications)} new notifications")

                # Fetch mentions
                mentions = self.fetch_mentions(page, max_mentions)
                logger.info(f"Found {len(mentions)} new mentions")

                # Combine all items
                all_items = notifications + mentions
                new_count = 0

                # Create inbox files
                for item in all_items:
                    filepath = self.create_inbox_file(item)
                    if filepath:
                        self.processed_ids.add(item['id'])
                        new_count += 1

                # Save processed IDs
                self._save_processed_ids()

                # Log activity
                self.log_activity({
                    'timestamp': datetime.now().isoformat(),
                    'activity': 'check',
                    'new_notifications': len(notifications),
                    'new_mentions': len(mentions),
                    'total_new': new_count
                })

                logger.info(f"Twitter watcher complete: {new_count} items processed")

                browser.close()

                print()
                print(f"[SUCCESS] Processed {new_count} new Twitter item(s)")
                print(f"[INFO] Files created in: {self.inbox_path}")

                return 0

            except Exception as e:
                logger.error(f"Twitter watcher failed: {e}", exc_info=True)
                if 'browser' in locals():
                    browser.close()
                return 1

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Twitter Watcher Agent Skill')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault',
                       help='Path to Obsidian vault')
    parser.add_argument('--session', type=str, default='./twitter_session',
                       help='Path to browser session directory')
    parser.add_argument('--headless', type=str, default='true',
                       help='Run browser in headless mode (true/false)')
    parser.add_argument('--max-notifications', type=int, default=10,
                       help='Maximum notifications to process')
    parser.add_argument('--max-mentions', type=int, default=10,
                       help='Maximum mentions to process')

    args = parser.parse_args()

    print("Twitter Watcher Agent Skill")
    print("=" * 50)
    print()

    vault_path = Path(args.vault)
    session_path = Path(args.session)
    headless = args.headless.lower() == 'true'

    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return 1

    watcher = TwitterWatcher(vault_path, session_path)
    return watcher.run(headless, args.max_notifications, args.max_mentions)

if __name__ == '__main__':
    sys.exit(main())
