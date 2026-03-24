#!/usr/bin/env python3
"""
Twitter (X) Poster - Posts tweets and threads
Uses Playwright for browser automation
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import argparse
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('twitter_poster')

class TwitterPoster:
    """Posts tweets and threads to Twitter."""

    def __init__(self, vault_path: Path, session_path: Path):
        self.vault_path = vault_path
        self.logs_path = vault_path / 'Logs'
        self.session_path = session_path

        # Ensure directories exist
        self.logs_path.mkdir(exist_ok=True)
        self.session_path.mkdir(exist_ok=True)

    def check_login_status(self, page) -> bool:
        """Check if user is logged in to Twitter."""
        try:
            page.wait_for_selector('[data-testid="SideNav_AccountSwitcher_Button"]', timeout=5000)
            return True
        except PlaywrightTimeout:
            return False

    def post_tweet(self, page, content: str) -> bool:
        """Post a single tweet."""
        try:
            # Check if we're already on home page
            if 'twitter.com/home' not in page.url:
                logger.info("Navigating to Twitter home...")
                page.goto('https://twitter.com/home', timeout=60000, wait_until='load')
                page.wait_for_timeout(3000)
            else:
                logger.info("Already on Twitter home page")
                page.wait_for_timeout(2000)

            # Find tweet compose box
            logger.info("Finding compose box...")
            compose_box = page.wait_for_selector('[data-testid="tweetTextarea_0"]', timeout=10000)

            # Click and type content
            logger.info("Typing tweet content...")
            compose_box.click()
            page.wait_for_timeout(500)

            # Use keyboard to type for better reliability
            page.keyboard.type(content, delay=30)
            page.wait_for_timeout(2000)

            # Find and click post button with multiple methods
            logger.info("Clicking post button...")
            post_clicked = False

            # Method 1: Try the inline post button
            try:
                post_button = page.wait_for_selector('[data-testid="tweetButtonInline"]', timeout=5000)
                if post_button and post_button.is_enabled():
                    post_button.click()
                    post_clicked = True
                    logger.info("✓ Clicked post button (method 1)")
            except Exception as e:
                logger.warning(f"Method 1 failed: {e}")

            # Method 2: Try the regular tweet button
            if not post_clicked:
                try:
                    post_button = page.wait_for_selector('[data-testid="tweetButton"]', timeout=3000)
                    if post_button and post_button.is_enabled():
                        post_button.click()
                        post_clicked = True
                        logger.info("✓ Clicked post button (method 2)")
                except Exception as e:
                    logger.warning(f"Method 2 failed: {e}")

            # Method 3: Use keyboard shortcut (Ctrl+Enter)
            if not post_clicked:
                try:
                    logger.info("Trying keyboard shortcut (Ctrl+Enter)...")
                    page.keyboard.press('Control+Enter')
                    post_clicked = True
                    logger.info("✓ Posted via keyboard shortcut (method 3)")
                except Exception as e:
                    logger.warning(f"Method 3 failed: {e}")

            if not post_clicked:
                logger.error("Failed to click post button with all methods")
                return False

            # Wait for tweet to post
            page.wait_for_timeout(3000)

            logger.info("Tweet posted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return False

    def post_thread(self, page, tweets: list) -> bool:
        """Post a thread of tweets."""
        try:
            logger.info(f"Posting thread with {len(tweets)} tweets...")

            for i, tweet_content in enumerate(tweets, 1):
                logger.info(f"Posting tweet {i}/{len(tweets)}...")

                if i == 1:
                    # First tweet
                    success = self.post_tweet(page, tweet_content)
                else:
                    # Reply to previous tweet
                    page.wait_for_timeout(2000)

                    # Find reply button on the last tweet
                    try:
                        reply_button = page.wait_for_selector('[data-testid="reply"]', timeout=5000)
                        reply_button.click()
                        page.wait_for_timeout(1000)

                        # Type reply
                        compose_box = page.wait_for_selector('[data-testid="tweetTextarea_0"]', timeout=5000)
                        compose_box.fill(tweet_content)
                        page.wait_for_timeout(1000)

                        # Post reply
                        post_button = page.wait_for_selector('[data-testid="tweetButton"]', timeout=5000)
                        post_button.click()
                        page.wait_for_timeout(3000)

                        logger.info(f"Thread tweet {i} posted")
                    except Exception as e:
                        logger.error(f"Failed to post thread tweet {i}: {e}")
                        return False

            logger.info("Thread posted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to post thread: {e}")
            return False

    def log_activity(self, activity: dict):
        """Log posting activity."""
        log_file = self.logs_path / f"{datetime.now().strftime('%Y-%m-%d')}_twitter_poster.json"

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

    def run(self, content: str, thread: bool = False, headless: bool = True) -> int:
        """Run the Twitter poster."""
        logger.info("Starting Twitter poster...")

        # Parse content for thread
        tweets = []
        if thread:
            # Split by newlines or numbered format
            tweets = [t.strip() for t in content.split('\n\n') if t.strip()]
        else:
            tweets = [content]

        logger.info(f"Posting {len(tweets)} tweet(s)...")

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
                logger.info("Navigating to Twitter...")
                page.goto('https://twitter.com/home', timeout=60000, wait_until='load')
                page.wait_for_timeout(3000)

                if not self.check_login_status(page):
                    if not headless:
                        # In visible mode, wait for manual login
                        logger.warning("Not logged in to Twitter")
                        print()
                        print("=" * 60)
                        print("PLEASE LOG IN TO TWITTER IN THE BROWSER WINDOW")
                        print("You have 120 seconds to complete the login...")
                        print("=" * 60)
                        print()

                        # Wait for user to log in
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
                        logger.error("Not logged in to Twitter")
                        logger.info("Please run with --headless false to log in")
                        browser.close()
                        return 0

                logger.info("Twitter login verified")

                # Post tweet or thread
                if len(tweets) == 1:
                    success = self.post_tweet(page, tweets[0])
                else:
                    success = self.post_thread(page, tweets)

                # Log activity
                self.log_activity({
                    'timestamp': datetime.now().isoformat(),
                    'activity': 'post',
                    'type': 'thread' if len(tweets) > 1 else 'tweet',
                    'tweet_count': len(tweets),
                    'success': success
                })

                browser.close()

                if success:
                    print()
                    print(f"[SUCCESS] Posted {len(tweets)} tweet(s) to Twitter")
                    return 0
                else:
                    print()
                    print("[ERROR] Failed to post to Twitter")
                    return 1

            except Exception as e:
                logger.error(f"Twitter poster failed: {e}", exc_info=True)
                if 'browser' in locals():
                    browser.close()
                return 1

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Twitter Poster Agent Skill')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault',
                       help='Path to Obsidian vault')
    parser.add_argument('--session', type=str, default='./twitter_session',
                       help='Path to browser session directory')
    parser.add_argument('--content', type=str, required=True,
                       help='Tweet content to post')
    parser.add_argument('--thread', action='store_true',
                       help='Post as thread (split by double newlines)')
    parser.add_argument('--headless', type=str, default='true',
                       help='Run browser in headless mode (true/false)')

    args = parser.parse_args()

    print("Twitter Poster Agent Skill")
    print("=" * 50)
    print()

    vault_path = Path(args.vault)
    session_path = Path(args.session)
    headless = args.headless.lower() == 'true'

    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return 1

    poster = TwitterPoster(vault_path, session_path)
    return poster.run(args.content, args.thread, headless)

if __name__ == '__main__':
    sys.exit(main())
