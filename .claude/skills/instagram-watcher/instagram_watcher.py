#!/usr/bin/env python3
"""
Instagram Watcher - Monitors DMs, comments, and mentions
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
logger = logging.getLogger('instagram_watcher')

class InstagramWatcher:
    """Monitors Instagram for DMs, comments, and mentions."""

    def __init__(self, vault_path: Path, session_path: Path):
        self.vault_path = vault_path
        self.inbox_path = vault_path / 'Inbox'
        self.logs_path = vault_path / 'Logs'
        self.session_path = session_path
        self.processed_ids_file = vault_path / '.instagram_processed_ids.json'

        self.inbox_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
        self.session_path.mkdir(exist_ok=True)
        self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self) -> set:
        if self.processed_ids_file.exists():
            try:
                content = self.processed_ids_file.read_text(encoding='utf-8')
                return set(json.loads(content))
            except Exception as e:
                logger.warning(f"Failed to load processed IDs: {e}")
        return set()

    def _save_processed_ids(self):
        try:
            self.processed_ids_file.write_text(
                json.dumps(list(self.processed_ids), indent=2),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"Failed to save processed IDs: {e}")

    def check_login_status(self, page) -> bool:
        try:
            page.wait_for_selector('[aria-label="Home"]', timeout=5000)
            return True
        except PlaywrightTimeout:
            return False

    def fetch_notifications(self, page, max_notifications: int = 10) -> list:
        notifications = []
        try:
            logger.info("Checking Instagram notifications...")
            page.goto('https://www.instagram.com/', wait_until='networkidle')
            page.wait_for_timeout(2000)

            # Click notifications icon
            try:
                notif_button = page.wait_for_selector('[aria-label*="Notifications"]', timeout=5000)
                notif_button.click()
                page.wait_for_timeout(2000)

                # Get notification items
                notif_elements = page.query_selector_all('[role="menuitem"]')
                logger.info(f"Found {len(notif_elements)} notification elements")

                for elem in notif_elements[:max_notifications]:
                    try:
                        text_content = elem.inner_text()
                        if not text_content or len(text_content.strip()) < 5:
                            continue

                        notification_id = str(hash(text_content))
                        if notification_id in self.processed_ids:
                            continue

                        notification = {
                            'id': notification_id,
                            'content': text_content[:500],
                            'timestamp': datetime.now().isoformat(),
                            'type': 'notification'
                        }
                        notifications.append(notification)
                        logger.info(f"Captured notification: {notification_id}")
                    except Exception as e:
                        logger.warning(f"Failed to parse notification: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Could not access notifications: {e}")

        except Exception as e:
            logger.error(f"Failed to fetch notifications: {e}")

        return notifications

    def create_inbox_file(self, item: dict) -> Path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        item_id = item['id'][:8]
        filename = f"INSTAGRAM_{timestamp}_{item_id}.md"
        filepath = self.inbox_path / filename

        content = f"""---
type: instagram_{item['type']}
source: instagram
item_id: {item['id']}
timestamp: {item.get('timestamp', 'N/A')}
received: {datetime.now().isoformat()}
status: new
---

# Instagram Notification

**Time:** {item.get('timestamp', 'N/A')}

## Content

{item['content']}

## Next Steps

This Instagram {item['type']} has been detected and placed in the Inbox for processing.
The AI Employee will:
1. Read this file from /Inbox
2. Analyze the content and priority
3. Create an action item in /Needs_Action if required
4. Process according to Company_Handbook.md rules

---
*Created by Instagram Watcher Agent Skill*
"""

        try:
            filepath.write_text(content, encoding='utf-8')
            logger.info(f"Created inbox file: {filename}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to create inbox file: {e}")
            return None

    def log_activity(self, activity: dict):
        log_file = self.logs_path / f"{datetime.now().strftime('%Y-%m-%d')}_instagram_watcher.json"
        try:
            if log_file.exists():
                content = log_file.read_text(encoding='utf-8')
                logs = json.loads(content) if content.strip() else []
            else:
                logs = []
            logs.append(activity)
            log_file.write_text(json.dumps(logs, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

    def run(self, headless: bool = True, max_notifications: int = 10) -> int:
        logger.info("Starting Instagram watcher...")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=headless,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser.pages[0] if browser.pages else browser.new_page()
                page.goto('https://www.instagram.com/', wait_until='networkidle')

                if not self.check_login_status(page):
                    logger.error("Not logged in to Instagram")
                    logger.info("Please run with --headless false to log in")
                    browser.close()
                    return 0

                logger.info("Instagram login verified")
                notifications = self.fetch_notifications(page, max_notifications)
                logger.info(f"Found {len(notifications)} new notifications")

                new_count = 0
                for item in notifications:
                    filepath = self.create_inbox_file(item)
                    if filepath:
                        self.processed_ids.add(item['id'])
                        new_count += 1

                self._save_processed_ids()
                self.log_activity({
                    'timestamp': datetime.now().isoformat(),
                    'activity': 'check',
                    'new_notifications': len(notifications),
                    'total_new': new_count
                })

                logger.info(f"Instagram watcher complete: {new_count} items processed")
                browser.close()

                print()
                print(f"[SUCCESS] Processed {new_count} new Instagram item(s)")
                print(f"[INFO] Files created in: {self.inbox_path}")
                return 0

            except Exception as e:
                logger.error(f"Instagram watcher failed: {e}", exc_info=True)
                if 'browser' in locals():
                    browser.close()
                return 1

def main():
    parser = argparse.ArgumentParser(description='Instagram Watcher Agent Skill')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault')
    parser.add_argument('--session', type=str, default='./instagram_session')
    parser.add_argument('--headless', type=str, default='true')
    parser.add_argument('--max-notifications', type=int, default=10)
    args = parser.parse_args()

    print("Instagram Watcher Agent Skill")
    print("=" * 50)
    print()

    vault_path = Path(args.vault)
    session_path = Path(args.session)
    headless = args.headless.lower() == 'true'

    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return 1

    watcher = InstagramWatcher(vault_path, session_path)
    return watcher.run(headless, args.max_notifications)

if __name__ == '__main__':
    sys.exit(main())
