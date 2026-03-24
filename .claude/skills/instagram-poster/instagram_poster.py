#!/usr/bin/env python3
"""
Instagram Poster - Posts images and captions to Instagram
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
logger = logging.getLogger('instagram_poster')

class InstagramPoster:
    """Posts images and captions to Instagram."""

    def __init__(self, vault_path: Path, session_path: Path):
        self.vault_path = vault_path
        self.logs_path = vault_path / 'Logs'
        self.session_path = session_path
        self.logs_path.mkdir(exist_ok=True)
        self.session_path.mkdir(exist_ok=True)

    def check_login_status(self, page) -> bool:
        try:
            page.wait_for_selector('[aria-label="Home"]', timeout=5000)
            return True
        except PlaywrightTimeout:
            return False

    def post_update(self, page, caption: str, image_path: str = None) -> bool:
        """Post an update to Instagram."""
        try:
            # Check if we're already on Instagram
            if 'instagram.com' not in page.url:
                logger.info("Navigating to Instagram...")
                page.goto('https://www.instagram.com/', timeout=60000, wait_until='load')
                page.wait_for_timeout(3000)
            else:
                logger.info("Already on Instagram")
                page.wait_for_timeout(2000)

            if image_path:
                # Click create button
                logger.info("Clicking create button...")
                create_button = page.wait_for_selector('[aria-label="New post"]', timeout=10000)
                create_button.click()
                page.wait_for_timeout(1000)

                # Upload image
                logger.info(f"Uploading image: {image_path}")
                file_input = page.wait_for_selector('input[type="file"]', timeout=5000)
                file_input.set_input_files(image_path)
                page.wait_for_timeout(2000)

                # Click next
                next_button = page.wait_for_selector('button:has-text("Next")', timeout=5000)
                next_button.click()
                page.wait_for_timeout(1000)

                # Click next again (filters)
                next_button = page.wait_for_selector('button:has-text("Next")', timeout=5000)
                next_button.click()
                page.wait_for_timeout(1000)

                # Add caption
                logger.info("Adding caption...")
                caption_box = page.wait_for_selector('[aria-label="Write a caption..."]', timeout=5000)
                caption_box.fill(caption)
                page.wait_for_timeout(1000)

                # Click share
                logger.info("Clicking share button...")
                share_button = page.wait_for_selector('button:has-text("Share")', timeout=5000)
                share_button.click()
                page.wait_for_timeout(3000)

                logger.info("Post published successfully")
                return True
            else:
                logger.warning("Image path required for Instagram posts")
                return False

        except Exception as e:
            logger.error(f"Failed to post update: {e}")
            return False

    def log_activity(self, activity: dict):
        """Log posting activity."""
        log_file = self.logs_path / f"{datetime.now().strftime('%Y-%m-%d')}_instagram_poster.json"
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

    def run(self, caption: str, image_path: str = None, headless: bool = True) -> int:
        """Run the Instagram poster."""
        logger.info("Starting Instagram poster...")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=headless,
                    args=['--disable-blink-features=AutomationControlled']
                )

                page = browser.pages[0] if browser.pages else browser.new_page()

                logger.info("Navigating to Instagram...")
                page.goto('https://www.instagram.com/', timeout=60000, wait_until='load')
                page.wait_for_timeout(3000)

                if not self.check_login_status(page):
                    if not headless:
                        # In visible mode, wait for manual login
                        logger.warning("Not logged in to Instagram")
                        print()
                        print("=" * 60)
                        print("PLEASE LOG IN TO INSTAGRAM IN THE BROWSER WINDOW")
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
                        logger.error("Not logged in to Instagram")
                        logger.info("Please run with --headless false to log in")
                        browser.close()
                        return 0

                logger.info("Instagram login verified")
                success = self.post_update(page, caption, image_path)

                self.log_activity({
                    'timestamp': datetime.now().isoformat(),
                    'activity': 'post',
                    'has_image': image_path is not None,
                    'success': success
                })

                browser.close()

                if success:
                    print()
                    print("[SUCCESS] Posted update to Instagram")
                    return 0
                else:
                    print()
                    print("[ERROR] Failed to post to Instagram")
                    return 1

            except Exception as e:
                logger.error(f"Instagram poster failed: {e}", exc_info=True)
                if 'browser' in locals():
                    browser.close()
                return 1

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Instagram Poster Agent Skill')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault')
    parser.add_argument('--session', type=str, default='./instagram_session')
    parser.add_argument('--caption', type=str, required=True)
    parser.add_argument('--image', type=str, help='Path to image file')
    parser.add_argument('--headless', type=str, default='true')
    args = parser.parse_args()

    print("Instagram Poster Agent Skill")
    print("=" * 50)
    print()

    vault_path = Path(args.vault)
    session_path = Path(args.session)
    headless = args.headless.lower() == 'true'

    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return 1

    if args.image and not Path(args.image).exists():
        logger.error(f"Image not found: {args.image}")
        return 1

    poster = InstagramPoster(vault_path, session_path)
    return poster.run(args.caption, args.image, headless)

if __name__ == '__main__':
    sys.exit(main())
