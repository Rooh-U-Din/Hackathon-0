#!/usr/bin/env python3
"""
Test Email Sending via Gmail API
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

def send_test_email():
    """Send a test email using Gmail API."""
    print("📧 Email Sending Test")
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
        print("🔐 Loading credentials...")
        if not credentials_path.exists():
            print("❌ Error: credentials.json not found")
            return 1

        creds = None
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing token...")
                creds.refresh(Request())
            else:
                print("🔐 Starting OAuth authentication flow...")
                print("   A browser window will open for you to grant permissions")
                print()
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
                print("✅ Authentication successful!")

            # Save token
            token_path.write_text(creds.to_json())
            print("💾 Token saved")

        # Build service
        print("✅ Authenticated successfully")
        service = build('gmail', 'v1', credentials=creds)

        # Get user's email address
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile['emailAddress']
        print(f"📬 Your email: {user_email}")
        print()

        # Create test email
        print("✍️  Creating test email...")
        message = MIMEText("""Hello!

This is a test email sent by your Personal AI Employee automation system.

The email sending functionality is working correctly! 🎉

Key features tested:
✅ Gmail API authentication
✅ Email composition
✅ Email sending

Your AI Employee can now:
- Send emails automatically
- Draft emails for approval
- Reply to incoming messages

Next steps:
1. Test draft email creation
2. Test email reply functionality
3. Integrate with approval workflow

---
Sent by Personal AI Employee Test Script
""")

        message['to'] = user_email
        message['subject'] = '🤖 Test Email from AI Employee - Email Sending Works!'

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
        print(f"📬 Sent to: {user_email}")
        print()
        print("🔍 Check your Gmail inbox for the test email!")
        print()

        return 0

    except ImportError:
        print("❌ Error: Gmail API libraries not installed")
        print("   Run: pip install google-auth google-auth-oauthlib google-api-python-client")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(send_test_email())
