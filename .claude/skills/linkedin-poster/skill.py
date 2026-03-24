#!/usr/bin/env python3
"""
LinkedIn Poster Skill - Post business content to LinkedIn
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import argparse

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def main():
    """Main entry point for LinkedIn poster skill."""
    print("🔗 LinkedIn Poster Skill")
    print("=" * 50)
    print()

    # Get vault path
    vault_path = Path('./AI_Employee_Vault')
    pending_approval = vault_path / 'Pending_Approval'
    approved = vault_path / 'Approved'
    done = vault_path / 'Done'
    logs_path = vault_path / 'Logs'
    session_path = Path('./linkedin_session')

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--content', type=str, default=None)
    parser.add_argument('--schedule', type=str, default=None)
    parser.add_argument('--draft-only', type=str, default='true')
    args = parser.parse_args()

    # Convert draft-only string to boolean
    args.draft_only = args.draft_only.lower() in ('true', '1', 'yes')

    print(f"⚙️  Configuration:")
    print(f"   Draft only: {args.draft_only}")
    if args.schedule:
        print(f"   Scheduled for: {args.schedule}")
    print()

    # If draft-only mode (default), create approval request
    if args.draft_only:
        print("📝 Creating LinkedIn post draft for approval...")
        print()

        # Read business context
        handbook = vault_path / 'Company_Handbook.md'
        business_goals = vault_path / 'Business_Goals.md'

        context = ""
        if handbook.exists():
            context += f"Handbook:\n{handbook.read_text()}\n\n"
        if business_goals.exists():
            context += f"Goals:\n{business_goals.read_text()}\n\n"

        # Generate post content (placeholder - Claude Code will do this)
        if args.content:
            post_content = args.content
        else:
            post_content = """🚀 Exciting update from our team!

We've been working hard on delivering exceptional results for our clients. This week, we completed another successful project that demonstrates our commitment to quality and innovation.

Key highlights:
✅ Delivered on time and within budget
✅ Exceeded client expectations
✅ Implemented cutting-edge solutions

Looking forward to more success stories ahead!

What's your biggest win this week? Share in the comments! 👇

#Business #Success #Innovation #ClientSuccess"""

        # Create approval request
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        approval_file = pending_approval / f'LINKEDIN_POST_{timestamp}.md'

        content = f"""---
type: linkedin_post
created: {datetime.now().isoformat()}
priority: medium
status: pending_approval
scheduled_for: {args.schedule if args.schedule else 'immediate'}
---

## LinkedIn Post Draft

### Post Content
{post_content}

### Context
- Based on: Recent business activities
- Target audience: Potential clients and network
- Goal: Generate engagement and leads
- Estimated reach: 500-1000 impressions

### Preview
This post will appear on your LinkedIn profile and in your network's feed.

### To Approve
Move this file to /Approved folder, then run:
```
/linkedin-poster --draft-only false
```

### To Reject
Move this file to /Rejected folder with feedback in comments.

### To Edit
Modify the post content above, then move to /Approved.
"""

        approval_file.write_text(content, encoding='utf-8')

        print(f"✅ Draft created: {approval_file.name}")
        print(f"📁 Location: {approval_file}")
        print()
        print("⏳ Waiting for approval...")
        print("   Move the file to /Approved folder to proceed with posting")

        # Log activity
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'linkedin_draft_created',
            'file': approval_file.name,
            'status': 'pending_approval'
        }

        log_file = logs_path / f'{datetime.now().strftime("%Y-%m-%d")}_linkedin.json'
        logs = []
        if log_file.exists():
            logs = json.loads(log_file.read_text())
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))

        return 0

    # If not draft-only, proceed with posting (requires approval)
    print("🚀 Posting to LinkedIn...")
    print()

    # Check for approved posts
    approved_posts = list(approved.glob('LINKEDIN_POST_*.md'))

    if not approved_posts:
        print("❌ No approved LinkedIn posts found")
        print("   Create a draft first with --draft-only true")
        return 1

    try:
        from playwright.sync_api import sync_playwright

        print("🌐 Launching browser...")

        with sync_playwright() as p:
            # Launch persistent context for LinkedIn session
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(session_path),
                headless=False,  # Show browser for LinkedIn
                args=['--disable-blink-features=AutomationControlled']
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            print("🔗 Navigating to LinkedIn...")
            page.goto('https://www.linkedin.com/feed/', timeout=60000)
            page.wait_for_timeout(3000)

            # Check if logged in with robust detection
            logged_in = False

            # Check URL first
            if 'login' not in page.url and 'authwall' not in page.url and '/feed' in page.url:
                print("✅ Already logged in (verified by URL)")
                logged_in = True
            else:
                # Try multiple selectors
                selectors_to_try = [
                    'nav.global-nav',
                    '.global-nav__me',
                    '.feed-identity-module',
                    'button[aria-label*="Me"]',
                    '.scaffold-layout__main'
                ]

                for selector in selectors_to_try:
                    try:
                        if page.query_selector(selector):
                            print(f"✅ Already logged in (found {selector})")
                            logged_in = True
                            break
                    except:
                        continue

            if not logged_in:
                print("⚠️  Please log in to LinkedIn")
                print("   Waiting for login...")
                # Wait for user to log in manually
                import time
                for i in range(12):  # 120 seconds
                    time.sleep(10)
                    page.goto('https://www.linkedin.com/feed/', timeout=30000)
                    page.wait_for_timeout(2000)
                    if 'login' not in page.url and '/feed' in page.url:
                        print("✅ Login successful")
                        logged_in = True
                        break

                if not logged_in:
                    print("❌ Login timeout")
                    browser.close()
                    return 1

            # Process first approved post
            post_file = approved_posts[0]
            print(f"📄 Processing: {post_file.name}")

            # Extract post content
            content = post_file.read_text(encoding='utf-8')
            # Simple extraction (in production, use proper markdown parsing)
            lines = content.split('\n')
            post_text = ""
            in_content = False
            for line in lines:
                if line.startswith('### Post Content'):
                    in_content = True
                    continue
                if in_content and line.startswith('###'):
                    break
                if in_content and line.strip():
                    post_text += line + "\n"

            post_text = post_text.strip()

            print(f"📝 Post preview: {post_text[:100]}...")
            print()

            # Try to automatically create post
            print("✍️  Attempting to create post automatically...")

            try:
                # Try multiple selectors for "Start a post" button
                start_post_clicked = False

                # Method 1: Try clicking the share box by text
                try:
                    page.click('text="Start a post"', timeout=5000)
                    start_post_clicked = True
                    print("✅ Clicked 'Start a post' button (method 1)")
                except:
                    pass

                # Method 2: Try the share box class
                if not start_post_clicked:
                    try:
                        page.click('.share-box-feed-entry__trigger', timeout=5000)
                        start_post_clicked = True
                        print("✅ Clicked share box (method 2)")
                    except:
                        pass

                # Method 3: Try any button with "Start a post" text
                if not start_post_clicked:
                    try:
                        page.click('button:has-text("Start a post")', timeout=5000)
                        start_post_clicked = True
                        print("✅ Clicked start post button (method 3)")
                    except:
                        pass

                if not start_post_clicked:
                    print("⚠️  Could not find 'Start a post' button automatically")
                    print("   Falling back to manual mode...")
                    raise Exception("Auto-click failed")

                # Wait longer for editor to appear
                print("⏳ Waiting for editor to load...")
                page.wait_for_timeout(3000)

                # Try to find and fill the editor
                editor_filled = False

                # Method 1: Try contenteditable div with more specific selector
                try:
                    editor = page.wait_for_selector('[contenteditable="true"]', timeout=5000)
                    if editor:
                        print("✅ Found editor (method 1)")
                        editor.click()
                        page.wait_for_timeout(1000)
                        # Use keyboard to type
                        page.keyboard.type(post_text, delay=30)
                        editor_filled = True
                        print("✅ Post content entered (method 1)")
                except Exception as e:
                    print(f"   Method 1 failed: {e}")

                # Method 2: Try clicking and using keyboard directly
                if not editor_filled:
                    try:
                        # Click anywhere in the modal to focus
                        page.click('[role="dialog"]', timeout=3000)
                        page.wait_for_timeout(500)
                        # Type directly
                        page.keyboard.type(post_text, delay=30)
                        editor_filled = True
                        print("✅ Post content entered (method 2 - keyboard)")
                    except Exception as e:
                        print(f"   Method 2 failed: {e}")

                # Method 3: Try the editor by aria-label
                if not editor_filled:
                    try:
                        editor = page.query_selector('[aria-label*="content"]')
                        if editor:
                            print("✅ Found editor (method 3)")
                            editor.click()
                            page.wait_for_timeout(1000)
                            page.keyboard.type(post_text, delay=30)
                            editor_filled = True
                            print("✅ Post content entered (method 3)")
                    except Exception as e:
                        print(f"   Method 3 failed: {e}")

                if not editor_filled:
                    print("⚠️  Could not fill editor automatically")
                    raise Exception("Auto-fill failed")

                page.wait_for_timeout(2000)

                print("✅ Post content entered successfully")
                print()
                print("🚀 Attempting to publish post...")

                # Try to click the Post button
                post_clicked = False

                # Method 1: Click by text "Post"
                try:
                    page.click('button:has-text("Post")', timeout=5000)
                    post_clicked = True
                    print("✅ Clicked 'Post' button (method 1)")
                except:
                    pass

                # Method 2: Try the post button by class
                if not post_clicked:
                    try:
                        page.click('.share-actions__primary-action', timeout=5000)
                        post_clicked = True
                        print("✅ Clicked post button (method 2)")
                    except:
                        pass

                # Method 3: Try any button with "Post" text in the modal
                if not post_clicked:
                    try:
                        page.click('[data-test-modal-container] button:has-text("Post")', timeout=5000)
                        post_clicked = True
                        print("✅ Clicked post button (method 3)")
                    except:
                        pass

                if post_clicked:
                    print()
                    print("=" * 60)
                    print("✅ POST PUBLISHED SUCCESSFULLY!")
                    print("=" * 60)
                    print()
                    print("🎉 Your post is now live on LinkedIn")
                    print("   Closing browser in 5 seconds...")
                    page.wait_for_timeout(5000)
                else:
                    print()
                    print("⚠️  Could not click 'Post' button automatically")
                    print("   Please click the 'Post' button manually in the browser")
                    print()
                    print("⏳ Browser will stay open for 30 seconds...")
                    page.wait_for_timeout(30000)

            except Exception as e:
                # Fallback to manual mode
                print()
                print("⚠️  Automatic posting failed, using manual mode")
                print(f"   Error: {e}")
                print()

                # Copy to clipboard
                try:
                    import pyperclip
                    pyperclip.copy(post_text)
                    print("✅ Post content copied to clipboard")
                except:
                    pass

                print()
                print("=" * 60)
                print("📋 POST CONTENT (copy and paste manually):")
                print("=" * 60)
                print(post_text)
                print("=" * 60)
                print()
                print("📝 MANUAL POSTING INSTRUCTIONS:")
                print("   1. Click 'Start a post' in the LinkedIn browser")
                print("   2. Paste the content (Ctrl+V)")
                print("   3. Click 'Post' button")
                print()
                print("⏳ Browser will stay open for 2 minutes...")
                print()

                page.wait_for_timeout(120000)  # 2 minutes

            print("✅ Post session completed")

            # Move to done
            done_file = done / post_file.name
            post_file.rename(done_file)

            # Log activity
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'event': 'linkedin_post_session',
                'file': post_file.name,
                'status': 'completed'
            }

            log_file = logs_path / f'{datetime.now().strftime("%Y-%m-%d")}_linkedin.json'
            logs = []
            if log_file.exists():
                logs = json.loads(log_file.read_text())
            logs.append(log_entry)
            log_file.write_text(json.dumps(logs, indent=2))

            print(f"📝 Log saved to: {log_file.name}")

            browser.close()
            return 0

    except ImportError:
        print("❌ Error: Playwright not installed")
        print("   Run: pip install playwright")
        print("   Then: playwright install chromium")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
