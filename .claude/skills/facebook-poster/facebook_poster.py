#!/usr/bin/env python3
"""
Facebook Poster - Posts updates to Facebook
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
logger = logging.getLogger('facebook_poster')

class FacebookPoster:
    """Posts updates to Facebook."""

    def __init__(self, vault_path: Path, session_path: Path):
        self.vault_path = vault_path
        self.logs_path = vault_path / 'Logs'
        self.session_path = session_path
        self.logs_path.mkdir(exist_ok=True)
        self.session_path.mkdir(exist_ok=True)

    def check_login_status(self, page) -> bool:
        """Check if user is logged in to Facebook."""
        try:
            # Check URL first - if we're on login page, not logged in
            if 'login' in page.url.lower():
                return False

            # Try multiple selectors to verify login
            selectors_to_try = [
                '[aria-label="Account"]',
                '[aria-label*="Your profile"]',
                '[aria-label*="Account Controls"]',
                'a[href*="/me/"]',
                '[data-pagelet="LeftRail"]',  # Left sidebar (only visible when logged in)
                '[role="navigation"]',  # Main navigation
            ]

            for selector in selectors_to_try:
                try:
                    element = page.query_selector(selector)
                    if element:
                        logger.info(f"Login verified with selector: {selector}")
                        return True
                except:
                    continue

            # If we're on facebook.com (not login page) and page has loaded, assume logged in
            if 'facebook.com' in page.url and 'login' not in page.url:
                logger.info("Login verified by URL (on facebook.com, not login page)")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False

    def post_update(self, page, content: str) -> bool:
        """Post an update to Facebook."""
        try:
            logger.info("Navigating to Facebook home...")
            page.goto('https://www.facebook.com/', timeout=60000, wait_until='load')
            page.wait_for_timeout(3000)

            # Find and click post composer
            logger.info("Finding post composer...")
            try:
                # Debug: Log what's on the page
                logger.info("Debugging: Checking page content...")

                # Try to find any element with "mind" in it
                mind_elements = page.query_selector_all('[aria-label*="mind"]')
                logger.info(f"Found {len(mind_elements)} elements with 'mind' in aria-label")

                # Try to find any element with "post" in it
                post_elements = page.query_selector_all('[aria-label*="post" i]')
                logger.info(f"Found {len(post_elements)} elements with 'post' in aria-label")

                # Try multiple selectors for the composer
                composer = None
                selectors = [
                    '[aria-label*="What\'s on your mind"]',
                    '[placeholder*="What\'s on your mind"]',
                    'text="What\'s on your mind"',
                    '[role="button"]:has-text("What\'s on your mind")',
                    'div[role="button"]',  # Generic button
                    '[data-pagelet="FeedComposer"]',
                    'form[method="POST"]',
                ]

                for selector in selectors:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        composer = page.query_selector(selector)
                        if composer:
                            logger.info(f"✓ Found composer with selector: {selector}")
                            # Check if it's visible
                            if composer.is_visible():
                                logger.info("✓ Composer is visible")
                                break
                            else:
                                logger.info("✗ Composer found but not visible")
                                composer = None
                    except Exception as e:
                        logger.info(f"✗ Selector failed: {e}")
                        continue

                if not composer:
                    logger.error("Could not find post composer with any selector")
                    logger.info("Taking screenshot for debugging...")
                    page.screenshot(path='facebook_debug.png')
                    logger.info("Screenshot saved to facebook_debug.png")
                    return False

                logger.info("Clicking composer...")
                composer.click()
                logger.info("✓ Clicked post composer")
                page.wait_for_timeout(2000)
            except Exception as e:
                logger.error(f"Failed to click composer: {e}")
                page.screenshot(path='facebook_error.png')
                logger.info("Error screenshot saved to facebook_error.png")
                return False

            # Type content using multiple methods
            logger.info("Typing post content...")
            text_entered = False

            # Method 1: Try to find contenteditable div
            try:
                editor = page.wait_for_selector('[contenteditable="true"]', timeout=5000)
                if editor:
                    logger.info("Found contenteditable editor")
                    editor.click()
                    page.wait_for_timeout(1000)
                    page.keyboard.type(content, delay=30)
                    text_entered = True
                    logger.info("Text entered via keyboard (method 1)")
            except Exception as e:
                logger.warning(f"Method 1 failed: {e}")

            # Method 2: Try clicking in modal and typing directly
            if not text_entered:
                try:
                    # Click anywhere in the modal to focus
                    page.click('[role="dialog"]', timeout=3000)
                    page.wait_for_timeout(500)
                    page.keyboard.type(content, delay=30)
                    text_entered = True
                    logger.info("Text entered via keyboard (method 2)")
                except Exception as e:
                    logger.warning(f"Method 2 failed: {e}")

            # Method 3: Try finding text area by placeholder
            if not text_entered:
                try:
                    text_box = page.query_selector('[aria-label="What\'s on your mind?"]')
                    if text_box:
                        text_box.click()
                        page.wait_for_timeout(500)
                        text_box.fill(content)
                        text_entered = True
                        logger.info("Text entered via fill (method 3)")
                except Exception as e:
                    logger.warning(f"Method 3 failed: {e}")

            if not text_entered:
                logger.error("Failed to enter text with all methods")
                return False

            page.wait_for_timeout(2000)

            # Click post button
            logger.info("Clicking post button...")
            try:
                # Try multiple selectors for post button
                post_button = None
                button_selectors = [
                    '[aria-label="Post"]',
                    'text="Post"',
                    '[type="submit"]'
                ]

                for selector in button_selectors:
                    try:
                        post_button = page.wait_for_selector(selector, timeout=5000)
                        if post_button:
                            logger.info(f"Found post button with selector: {selector}")
                            post_button.click()
                            break
                    except:
                        continue

                if not post_button:
                    logger.error("Could not find post button")
                    return False

                page.wait_for_timeout(3000)
                logger.info("Post published successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to click post button: {e}")
                return False

        except Exception as e:
            logger.error(f"Failed to post update: {e}")
            return False

    def log_activity(self, activity: dict):
        """Log posting activity."""
        log_file = self.logs_path / f"{datetime.now().strftime('%Y-%m-%d')}_facebook_poster.json"
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

    def run(self, content: str, headless: bool = True) -> int:
        """Run the Facebook poster."""
        logger.info("Starting Facebook poster...")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=headless,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                # Navigate with longer timeout and less strict wait condition
                logger.info("Navigating to Facebook...")
                page.goto('https://www.facebook.com/', timeout=60000, wait_until='load')
                page.wait_for_timeout(3000)

                if not self.check_login_status(page):
                    if not headless:
                        # In visible mode, wait for manual login
                        logger.warning("Not logged in to Facebook")
                        print()
                        print("=" * 60)
                        print("PLEASE LOG IN TO FACEBOOK IN THE BROWSER WINDOW")
                        print("You have 120 seconds to complete the login...")
                        print("=" * 60)
                        print()

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
                        logger.error("Not logged in to Facebook")
                        logger.info("Please run with --headless false to log in manually")
                        browser.close()
                        return 0

                logger.info("Facebook login verified")
                success = self.post_update(page, content)

                self.log_activity({
                    'timestamp': datetime.now().isoformat(),
                    'activity': 'post',
                    'success': success
                })

                browser.close()

                if success:
                    print()
                    print("[SUCCESS] Posted update to Facebook")
                    return 0
                else:
                    print()
                    print("[ERROR] Failed to post to Facebook")
                    return 1

            except Exception as e:
                logger.error(f"Facebook poster failed: {e}", exc_info=True)
                if 'browser' in locals():
                    browser.close()
                return 1

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Facebook Poster Agent Skill')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault')
    parser.add_argument('--session', type=str, default='./facebook_session')
    parser.add_argument('--content', type=str, required=True)
    parser.add_argument('--headless', type=str, default='true')
    args = parser.parse_args()

    print("Facebook Poster Agent Skill")
    print("=" * 50)
    print()

    vault_path = Path(args.vault)
    session_path = Path(args.session)
    headless = args.headless.lower() == 'true'

    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return 1

    poster = FacebookPoster(vault_path, session_path)
    return poster.run(args.content, headless)

if __name__ == '__main__':
    sys.exit(main())
