#!/usr/bin/env python3
"""
Send Final Project Email via Gmail API
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
    subject = "🚀 Personal AI Employee System - Platinum Tier Complete!"
    body = """Hello!

I'm excited to share that I've successfully completed my Personal AI Employee System - a Platinum Tier autonomous business assistant built for the Panaversity Hackathon 0!

🎯 PROJECT HIGHLIGHTS

This AI-powered system demonstrates the future of business automation with:

✅ Intelligent Email Triage - Monitors Gmail 24/7, automatically drafts responses
✅ Social Media Management - Automated posting to LinkedIn, Facebook, and Twitter with human approval
✅ Business Intelligence - Generates weekly CEO briefings with actionable insights
✅ Cloud-Local Hybrid Architecture - Secure design with proper security boundaries
✅ Complete Audit Trail - Full compliance and transparency for all actions

🔧 TECHNICAL ACHIEVEMENTS

• Built with Claude Code and Python
• 106 automated tests with 100% pass rate
• OAuth 2.0 integration for Gmail API
• Playwright browser automation for social platforms
• MCP (Model Context Protocol) servers for modular integrations
• Human-in-the-loop approval workflow for sensitive actions

🏗️ ARCHITECTURE

The system uses a sophisticated cloud-local hybrid architecture:
- Cloud Agent: Runs 24/7, drafts responses (no sensitive actions)
- Local Agent: Handles approvals and executes sensitive operations
- Vault Sync: Git-based synchronization with security boundaries
- No secrets ever stored on cloud infrastructure

📊 CAPABILITIES

Email Management:
- Automatic Gmail monitoring and triage
- Intelligent response drafting
- Duplicate detection and filtering

Social Media:
- LinkedIn, Facebook, Twitter posting
- Draft creation with approval workflow
- Session persistence for seamless operation

Business Operations:
- Weekly CEO briefings with metrics
- Task completion tracking
- Bottleneck identification
- Proactive suggestions

Integration:
- Gmail API with OAuth 2.0
- WhatsApp monitoring (local only)
- Odoo ERP integration
- Calendar management

🧪 TESTING & QUALITY

- Comprehensive test suite: 106 tests, 100% passing
- All watchers tested and operational
- All MCP servers validated
- Social media posters fully functional
- Platinum tier demo successfully executed

🔒 SECURITY

- Human-in-the-loop approval for all sensitive actions
- Security boundaries enforced (cloud drafts only, local executes)
- Complete audit trail for compliance
- No credentials in git repository
- Session files excluded from sync

📱 LIVE DEMONSTRATION

I've just posted about this project on:
- LinkedIn (full professional post)
- Facebook (complete project overview)
- Twitter (concise summary)

All posts were created and published automatically by the AI Employee system itself!

🎓 TECH STACK

- Claude Code (Anthropic) - Primary reasoning engine
- Python 3.14 - Backend automation
- Playwright - Browser automation
- OAuth 2.0 - Secure authentication
- MCP Protocol - Modular integrations
- Obsidian Vault - Knowledge management
- Git - Vault synchronization

📈 PROJECT METRICS

- Total markdown files: 56 (professionally organized)
- Agent Skills: 12 (fully documented)
- MCP Servers: 4 (operational)
- Test Coverage: 100%
- Documentation: Comprehensive (18 guides)

🎯 HACKATHON TIER: PLATINUM

This project exceeds all requirements for the Platinum Tier:
✅ Cloud agent (draft-only operations)
✅ Local agent (execution with approval)
✅ Vault sync system (Git-based)
✅ Platinum demo (minimum passing gate achieved)
✅ Complete audit trail
✅ Security boundaries enforced

The system demonstrates how AI can augment business operations without replacing human oversight. The cloud agent drafts, the local agent executes, and humans approve sensitive actions.

This is the future of business automation - AI that works FOR you, not INSTEAD of you.

🔗 REPOSITORY

The complete project with all documentation, tests, and implementation is ready for review.

Thank you for following this journey! This email was sent automatically by the Personal AI Employee system as a demonstration of its email sending capabilities.

Best regards,
Personal AI Employee System

---
🤖 Sent automatically by AI Employee
⚡ Powered by Claude Code
🏆 Panaversity Hackathon 0 - Platinum Tier
"""

    sys.exit(send_email(recipient, subject, body))
