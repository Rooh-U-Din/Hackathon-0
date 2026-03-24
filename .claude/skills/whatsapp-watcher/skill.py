#!/usr/bin/env python3
"""
WhatsApp Watcher Skill - Monitor WhatsApp Web for important messages
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import re

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def main():
    """Main entry point for WhatsApp watcher skill."""
    print("WhatsApp Watcher Skill")
    print("=" * 50)
    print()

    # Get vault path
    vault_path = Path('./AI_Employee_Vault')
    needs_action = vault_path / 'Needs_Action'
    logs_path = vault_path / 'Logs'
    session_path = Path('./whatsapp_session')

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-interval', type=int, default=120)
    parser.add_argument('--keywords', type=str, default='urgent,asap,invoice,payment,help')
    parser.add_argument('--headless', type=str, default='true')
    args = parser.parse_args()

    # Convert headless string to boolean
    args.headless = args.headless.lower() in ('true', '1', 'yes')

    keywords = [k.strip().lower() for k in args.keywords.split(',')]

    print(f"⚙️  Configuration:")
    print(f"   Check interval: {args.check_interval}s")
    print(f"   Keywords: {', '.join(keywords)}")
    print(f"   Headless mode: {args.headless}")
    print(f"   Session path: {session_path}")
    print()

    try:
        from playwright.sync_api import sync_playwright

        print("🌐 Launching browser...")

        with sync_playwright() as p:
            # Launch persistent context to maintain WhatsApp session
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(session_path),
                headless=args.headless,
                args=['--disable-blink-features=AutomationControlled']
            )

            page = browser.pages[0] if browser.pages else browser.new_page()

            print("📱 Navigating to WhatsApp Web...")
            page.goto('https://web.whatsapp.com', timeout=60000)

            # Wait for either QR code or chat list
            try:
                page.wait_for_selector('[data-testid="chat-list"]', timeout=30000)
                print("✅ WhatsApp Web loaded successfully")
            except:
                print("⚠️  QR Code detected - please scan with your phone")
                print("   Waiting for authentication (5 minutes)...")
                print("   1. Open WhatsApp on your phone")
                print("   2. Tap Menu or Settings")
                print("   3. Tap Linked Devices")
                print("   4. Tap Link a Device")
                print("   5. Scan the QR code on screen")
                print()
                page.wait_for_selector('[data-testid="chat-list"]', timeout=300000)
                print("✅ Authentication successful")

            print()
            print("🔍 Scanning for unread messages...")

            # Find unread chats
            unread_chats = page.query_selector_all('[aria-label*="unread"]')

            if not unread_chats:
                print("✅ No unread messages found")
                browser.close()
                return 0

            print(f"📨 Found {len(unread_chats)} unread chat(s)")
            print()

            # Track processed messages
            processed_file = vault_path / '.whatsapp_processed.json'
            processed_messages = set()
            if processed_file.exists():
                processed_messages = set(json.loads(processed_file.read_text()))

            new_messages = 0

            for chat in unread_chats[:5]:  # Process max 5 unread chats
                try:
                    # Click on chat to open
                    chat.click()
                    page.wait_for_timeout(1000)

                    # Get contact name
                    contact_elem = page.query_selector('[data-testid="conversation-header"]')
                    contact_name = contact_elem.inner_text().split('\n')[0] if contact_elem else "Unknown"

                    # Get last message
                    messages = page.query_selector_all('[data-testid="msg-container"]')
                    if not messages:
                        continue

                    last_message = messages[-1]
                    message_text = last_message.inner_text()

                    # Create unique ID
                    message_id = f"{contact_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

                    if message_id in processed_messages:
                        continue

                    # Check for keywords
                    message_lower = message_text.lower()
                    found_keywords = [kw for kw in keywords if kw in message_lower]

                    if not found_keywords:
                        continue  # Skip if no keywords found

                    # Determine priority
                    priority = 'high' if found_keywords else 'medium'

                    print(f"💬 Processing message from: {contact_name}")
                    print(f"   Preview: {message_text[:50]}...")
                    print(f"   Priority: {priority}")
                    print(f"   Keywords: {', '.join(found_keywords)}")

                    # Create action item
                    safe_name = re.sub(r'[^\w\s-]', '', contact_name).replace(' ', '_')
                    action_file = needs_action / f'WHATSAPP_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{safe_name}.md'

                    content = f"""---
type: whatsapp
from: {contact_name}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
keywords: {', '.join(found_keywords)}
---

## Message Content
{message_text}

## Suggested Actions
- [ ] Reply to sender
- [ ] Call if urgent
- [ ] Forward to team member
- [ ] Archive after processing

## Context
- Keywords detected: {', '.join(found_keywords)}
- Requires approval: Yes (external communication)
- Contact type: Client
"""

                    action_file.write_text(content, encoding='utf-8')
                    processed_messages.add(message_id)
                    new_messages += 1

                    print(f"   ✅ Created action item: {action_file.name}")
                    print()

                except Exception as e:
                    print(f"   ⚠️  Error processing chat: {e}")
                    continue

            # Save processed messages
            processed_file.write_text(json.dumps(list(processed_messages)))

            # Log activity
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'event': 'whatsapp_check',
                'total_chats': len(unread_chats),
                'new_messages': new_messages,
                'keywords': keywords
            }

            log_file = logs_path / f'{datetime.now().strftime("%Y-%m-%d")}_whatsapp.json'
            logs = []
            if log_file.exists():
                logs = json.loads(log_file.read_text())
            logs.append(log_entry)
            log_file.write_text(json.dumps(logs, indent=2))

            print(f"✅ WhatsApp check complete: {new_messages} new message(s) processed")
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
