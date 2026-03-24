#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Watcher Agent Skill
Monitors Gmail inbox and creates markdown files in /Inbox/ for new emails
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import logging

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gmail_watcher')


class GmailWatcher:
    """Gmail watcher that monitors inbox and creates files in /Inbox/"""

    def __init__(self, vault_path: Path, credentials_path: Path):
        """
        Initialize Gmail watcher.

        Args:
            vault_path: Path to Obsidian vault
            credentials_path: Path to Gmail API credentials.json
        """
        self.vault_path = vault_path
        self.inbox_path = vault_path / 'Inbox'
        self.logs_path = vault_path / 'Logs'
        self.credentials_path = credentials_path
        self.token_path = Path('token.json')
        self.processed_ids_file = vault_path / '.gmail_processed_ids.json'
        self.processed_ids = self._load_processed_ids()

        # Ensure directories exist
        self.inbox_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)

    def _load_processed_ids(self) -> set:
        """Load previously processed email IDs."""
        if self.processed_ids_file.exists():
            try:
                data = json.loads(self.processed_ids_file.read_text())
                return set(data)
            except Exception as e:
                logger.warning(f"Could not load processed IDs: {e}")
        return set()

    def _save_processed_ids(self):
        """Save processed email IDs to file."""
        try:
            self.processed_ids_file.write_text(
                json.dumps(list(self.processed_ids), indent=2)
            )
        except Exception as e:
            logger.error(f"Could not save processed IDs: {e}")

    def authenticate(self):
        """Authenticate with Gmail API."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

            creds = None

            # Load existing token
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    str(self.token_path), SCOPES
                )

            # Refresh or get new token
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired token...")
                    creds.refresh(Request())
                else:
                    logger.info("Starting OAuth flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save token
                self.token_path.write_text(creds.to_json())
                logger.info("Token saved successfully")

            # Build service
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API authenticated successfully")
            return True

        except ImportError:
            logger.error("Gmail API libraries not installed")
            logger.error("Run: pip install google-auth google-auth-oauthlib google-api-python-client")
            return False
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def fetch_new_emails(self, max_results=10, query='is:unread'):
        """
        Fetch new unread emails from Gmail.

        Args:
            max_results: Maximum number of emails to fetch
            query: Gmail search query

        Returns:
            List of new email message objects
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            # Filter out already processed emails
            new_messages = [
                msg for msg in messages
                if msg['id'] not in self.processed_ids
            ]

            logger.info(f"Found {len(messages)} unread, {len(new_messages)} new")
            return new_messages

        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")
            return []

    def get_email_details(self, message_id):
        """
        Get full details of an email message.

        Args:
            message_id: Gmail message ID

        Returns:
            Dictionary with email details or None
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Extract headers
            headers = {
                h['name']: h['value']
                for h in message['payload']['headers']
            }

            # Get snippet (preview)
            snippet = message.get('snippet', '')

            # Get thread ID
            thread_id = message.get('threadId', '')

            return {
                'id': message_id,
                'thread_id': thread_id,
                'from': headers.get('From', 'Unknown'),
                'to': headers.get('To', ''),
                'subject': headers.get('Subject', 'No Subject'),
                'date': headers.get('Date', ''),
                'snippet': snippet,
                'labels': message.get('labelIds', [])
            }

        except Exception as e:
            logger.error(f"Failed to get email details for {message_id}: {e}")
            return None

    def create_inbox_file(self, email_details):
        """
        Create markdown file in /Inbox/ for the email.

        Args:
            email_details: Dictionary with email details

        Returns:
            Path to created file or None
        """
        try:
            # Create safe filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'EMAIL_{timestamp}_{email_details["id"][:8]}.md'
            filepath = self.inbox_path / filename

            # Create markdown content
            content = f"""---
type: email
source: gmail
message_id: {email_details['id']}
thread_id: {email_details['thread_id']}
from: {email_details['from']}
to: {email_details['to']}
subject: {email_details['subject']}
date: {email_details['date']}
received: {datetime.now().isoformat()}
status: new
---

# Email: {email_details['subject']}

**From:** {email_details['from']}
**Date:** {email_details['date']}

## Preview

{email_details['snippet']}

## Next Steps

This email has been detected and placed in the Inbox for processing.
The AI Employee will:
1. Read this file from /Inbox
2. Analyze the content and priority
3. Create an action item in /Needs_Action
4. Process according to Company_Handbook.md rules

---
*Created by Gmail Watcher Agent Skill*
"""

            # Write file
            filepath.write_text(content, encoding='utf-8')
            logger.info(f"Created inbox file: {filename}")

            return filepath

        except Exception as e:
            logger.error(f"Failed to create inbox file: {e}")
            return None

    def log_activity(self, activity_type, details):
        """
        Log watcher activity.

        Args:
            activity_type: Type of activity (check, new_email, error)
            details: Dictionary with activity details
        """
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'activity': activity_type,
                **details
            }

            log_file = self.logs_path / f'{datetime.now().strftime("%Y-%m-%d")}_gmail_watcher.json'

            # Load existing logs
            logs = []
            if log_file.exists():
                logs = json.loads(log_file.read_text())

            # Append new entry
            logs.append(log_entry)

            # Save logs
            log_file.write_text(json.dumps(logs, indent=2))

        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

    def run(self, max_emails=10):
        """
        Run the watcher - check for new emails and create inbox files.

        Args:
            max_emails: Maximum number of emails to process

        Returns:
            Number of new emails processed
        """
        logger.info("Starting Gmail watcher...")

        # Authenticate
        if not self.authenticate():
            return 0

        # Fetch new emails
        new_messages = self.fetch_new_emails(max_results=max_emails)

        if not new_messages:
            logger.info("No new emails to process")
            self.log_activity('check', {'new_emails': 0})
            return 0

        # Process each new email
        processed_count = 0
        for message in new_messages:
            try:
                # Get email details
                email_details = self.get_email_details(message['id'])
                if not email_details:
                    continue

                # Create inbox file
                filepath = self.create_inbox_file(email_details)
                if not filepath:
                    continue

                # Mark as processed
                self.processed_ids.add(message['id'])
                processed_count += 1

                logger.info(f"Processed email: {email_details['subject'][:50]}")

            except Exception as e:
                logger.error(f"Error processing message {message['id']}: {e}")
                continue

        # Save processed IDs
        self._save_processed_ids()

        # Log activity
        self.log_activity('check', {
            'new_emails': processed_count,
            'total_checked': len(new_messages)
        })

        logger.info(f"Gmail watcher complete: {processed_count} emails processed")
        return processed_count


def main():
    """Main entry point for Gmail watcher skill."""
    print("Gmail Watcher Agent Skill")
    print("=" * 50)
    print()

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Gmail Watcher Agent Skill')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault',
                       help='Path to Obsidian vault')
    parser.add_argument('--credentials', type=str, default='./credentials.json',
                       help='Path to Gmail credentials.json')
    parser.add_argument('--max-emails', type=int, default=10,
                       help='Maximum emails to process')
    args = parser.parse_args()

    # Validate paths
    vault_path = Path(args.vault)
    credentials_path = Path(args.credentials)

    if not vault_path.exists():
        print(f"[ERROR] Vault not found: {vault_path}")
        return 1

    if not credentials_path.exists():
        print(f"[ERROR] Credentials not found: {credentials_path}")
        print("Please create credentials.json from Google Cloud Console")
        print("See: GMAIL_SETUP_GUIDE.md")
        return 1

    # Create and run watcher
    try:
        watcher = GmailWatcher(vault_path, credentials_path)
        count = watcher.run(max_emails=args.max_emails)

        print()
        print(f"[SUCCESS] Processed {count} new email(s)")
        print(f"[INFO] Files created in: {vault_path / 'Inbox'}")
        print()

        return 0

    except KeyboardInterrupt:
        print("\n[STOPPED] Watcher interrupted by user")
        return 0
    except Exception as e:
        print(f"[ERROR] Watcher failed: {e}")
        logger.exception("Watcher failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
