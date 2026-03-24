#!/usr/bin/env python3
"""
Send Email via Gmail API
"""
import sys
from pathlib import Path
from base64 import urlsafe_b64encode
from email.mime.text import MIMEText

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def send_email(to_email, subject, body):
    """Send an email using Gmail API."""
    print("📧 Sending Email via Gmail API")
    print("=" * 50)
    print()

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send'
        ]

        credentials_path = Path('credentials.json')
        token_path = Path('token.json')

        # Load credentials
        print("🔐 Authenticating...")
        if not credentials_path.exists():
            print("❌ Error: credentials.json not found")
            return 1

        creds = None
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        # Refresh token if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                token_path.write_text(creds.to_json())
            else:
                print("❌ Error: Token not valid. Run test_email_send.py first.")
                return 1

        # Build service
        service = build('gmail', 'v1', credentials=creds)
        print("✅ Authenticated successfully")
        print()

        # Create email
        print("✍️  Creating email...")
        print(f"   To: {to_email}")
        print(f"   Subject: {subject}")
        print()

        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject

        # Encode message
        raw_message = urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        # Send email
        print("📤 Sending email...")
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        print()
        print("=" * 50)
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print("=" * 50)
        print()
        print(f"📧 Message ID: {send_message['id']}")
        print(f"📬 Sent to: {to_email}")
        print()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    # Email details
    recipient = "beastk846@gmail.com"
    subject = "🤖 Greetings from Personal AI Employee System"
    body = """Hello!

This email was automatically sent by my Personal AI Employee automation system.

I've successfully built an autonomous AI assistant that:

✅ Monitors Gmail, LinkedIn, and WhatsApp
✅ Creates and sends emails automatically
✅ Posts to social media with approval workflow
✅ Integrates with accounting systems
✅ Generates weekly business reports

The system uses Claude Code with custom Agent Skills and MCP servers. It demonstrates the power of AI automation for productivity and business operations.

Key Technologies:
- Claude Code (Anthropic)
- Gmail API with OAuth 2.0
- Playwright for browser automation
- Python for backend automation
- Obsidian vault for knowledge management

This is a demonstration of the email sending capability. The AI Employee can draft, review, and send emails based on predefined rules and approval workflows.

Best regards,
Personal AI Employee System

---
Sent automatically by AI Employee
Powered by Claude Code
"""

    sys.exit(send_email(recipient, subject, body))
