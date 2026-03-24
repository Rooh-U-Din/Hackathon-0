#!/usr/bin/env python3
"""
Email MCP Server - Send emails via Gmail API
Model Context Protocol server for Claude Code
"""
import sys
import json
import os
from pathlib import Path
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def send_email_tool(params):
    """Send an email via Gmail API."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        # Get credentials
        creds_file = os.getenv('GMAIL_CREDENTIALS', 'credentials.json')
        token_file = os.getenv('GMAIL_TOKEN', 'token.json')

        if not Path(creds_file).exists():
            return {
                'error': 'Gmail credentials not found',
                'message': f'Please set up {creds_file}'
            }

        # Load token
        creds = None
        if Path(token_file).exists():
            creds = Credentials.from_authorized_user_file(token_file)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                return {
                    'error': 'Gmail authentication required',
                    'message': 'Run gmail-watcher skill first to authenticate'
                }

        # Build service
        service = build('gmail', 'v1', credentials=creds)

        # Create message
        message = MIMEMultipart()
        message['to'] = params['to']
        message['subject'] = params['subject']

        if 'cc' in params:
            message['cc'] = params['cc']
        if 'bcc' in params:
            message['bcc'] = params['bcc']

        # Add body
        body = MIMEText(params['body'], 'plain')
        message.attach(body)

        # Add attachments if provided
        if 'attachments' in params:
            for filepath in params['attachments']:
                if Path(filepath).exists():
                    with open(filepath, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={Path(filepath).name}'
                        )
                        message.attach(part)

        # Encode message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send message
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        return {
            'message_id': result['id'],
            'status': 'sent',
            'to': params['to'],
            'subject': params['subject']
        }

    except ImportError:
        return {
            'error': 'Gmail API libraries not installed',
            'message': 'Run: pip install google-auth google-api-python-client'
        }
    except Exception as e:
        return {
            'error': str(e),
            'status': 'failed'
        }

def draft_email_tool(params):
    """Create a draft email without sending."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds_file = os.getenv('GMAIL_CREDENTIALS', 'credentials.json')
        token_file = os.getenv('GMAIL_TOKEN', 'token.json')

        creds = Credentials.from_authorized_user_file(token_file)
        service = build('gmail', 'v1', credentials=creds)

        # Create message
        message = MIMEText(params['body'])
        message['to'] = params['to']
        message['subject'] = params['subject']

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create draft
        draft = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw}}
        ).execute()

        return {
            'draft_id': draft['id'],
            'status': 'draft_created'
        }

    except Exception as e:
        return {
            'error': str(e),
            'status': 'failed'
        }

def handle_request(request):
    """Handle MCP tool request."""
    method = request.get('method')
    params = request.get('params', {})

    if method == 'tools/list':
        return {
            'tools': [
                {
                    'name': 'send_email',
                    'description': 'Send an email via Gmail',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'to': {'type': 'string', 'description': 'Recipient email'},
                            'subject': {'type': 'string', 'description': 'Email subject'},
                            'body': {'type': 'string', 'description': 'Email body'},
                            'cc': {'type': 'string', 'description': 'CC recipients'},
                            'bcc': {'type': 'string', 'description': 'BCC recipients'},
                            'attachments': {'type': 'array', 'description': 'File paths'}
                        },
                        'required': ['to', 'subject', 'body']
                    }
                },
                {
                    'name': 'draft_email',
                    'description': 'Create a draft email without sending',
                    'inputSchema': {
                        'type': 'object',
                        'properties': {
                            'to': {'type': 'string'},
                            'subject': {'type': 'string'},
                            'body': {'type': 'string'}
                        },
                        'required': ['to', 'subject', 'body']
                    }
                }
            ]
        }

    elif method == 'tools/call':
        tool_name = params.get('name')
        tool_params = params.get('arguments', {})

        if tool_name == 'send_email':
            return send_email_tool(tool_params)
        elif tool_name == 'draft_email':
            return draft_email_tool(tool_params)
        else:
            return {'error': f'Unknown tool: {tool_name}'}

    else:
        return {'error': f'Unknown method: {method}'}

def main():
    """Main MCP server loop."""
    print("Email MCP Server starting...", file=sys.stderr)

    # Test mode
    if '--test' in sys.argv:
        print("Test mode - listing tools", file=sys.stderr)
        response = handle_request({'method': 'tools/list'})
        print(json.dumps(response, indent=2))
        return 0

    # MCP protocol loop
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception as e:
            error_response = {'error': str(e)}
            print(json.dumps(error_response))
            sys.stdout.flush()

    return 0

if __name__ == '__main__':
    sys.exit(main())
