#!/usr/bin/env python3
"""
LinkedIn Login Helper - First-time setup
Opens browser and waits for you to log in to LinkedIn
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

def main():
    print("LinkedIn Login Helper")
    print("=" * 50)
    print()
    print("This will open LinkedIn in a browser.")
    print("Please log in manually.")
    print("The browser will stay open for 3 minutes.")
    print()

    session_path = Path('./linkedin_session')
    session_path.mkdir(exist_ok=True)

    print("Opening browser...")

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        print("Navigating to LinkedIn...")
        page.goto('https://www.linkedin.com/feed/')

        print()
        print("=" * 50)
        print("PLEASE LOG IN TO LINKEDIN NOW")
        print("=" * 50)
        print()
        print("You have 3 minutes to:")
        print("1. Enter your email and password")
        print("2. Complete any 2FA if required")
        print("3. Wait for the feed page to load")
        print()
        print("The browser will close automatically after 3 minutes.")
        print("Your session will be saved for future runs.")
        print()

        # Wait 3 minutes for user to log in
        time.sleep(180)

        print()
        print("Closing browser...")
        print("Session saved to:", session_path)
        print()
        print("Now you can run the LinkedIn watcher:")
        print("python .claude/skills/linkedin-watcher/skill.py")

        browser.close()

    return 0

if __name__ == '__main__':
    sys.exit(main())
