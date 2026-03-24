#!/usr/bin/env python3
"""
Cloud Agent - Draft-Only Operations
Runs 24/7 on cloud VM, creates drafts and approval requests
Never executes sensitive actions (sending, posting, payments)
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import time
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cloud_agent')

class CloudAgent:
    """Cloud-side agent with draft-only capabilities."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.inbox_path = vault_path / 'Inbox'
        self.needs_action_path = vault_path / 'Needs_Action'
        self.pending_approval_path = vault_path / 'Pending_Approval'
        self.updates_path = vault_path / 'Updates'
        self.in_progress_path = vault_path / 'In_Progress' / 'cloud'
        self.logs_path = vault_path / 'Logs'

        # Ensure directories exist
        self.updates_path.mkdir(exist_ok=True)
        self.in_progress_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)

        # Domain ownership (cloud handles these)
        self.cloud_domains = ['email_triage', 'social_drafts', 'scheduling']

    def claim_task(self, task_file: Path) -> bool:
        """
        Claim a task by moving it to /In_Progress/cloud/.
        Returns True if successfully claimed.
        """
        try:
            # Check if task is in a cloud domain
            task_content = task_file.read_text(encoding='utf-8')

            # Extract domain from frontmatter
            domain = self._extract_domain(task_content)

            if domain not in self.cloud_domains:
                logger.debug(f"Task {task_file.name} not in cloud domain, skipping")
                return False

            # Move to in_progress (atomic claim)
            dest = self.in_progress_path / task_file.name

            if dest.exists():
                logger.debug(f"Task {task_file.name} already claimed")
                return False

            task_file.rename(dest)
            logger.info(f"Claimed task: {task_file.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to claim task {task_file.name}: {e}")
            return False

    def process_email_triage(self, task_file: Path) -> bool:
        """
        Process email triage: draft reply but don't send.
        Creates approval request for local agent.
        """
        try:
            content = task_file.read_text(encoding='utf-8')

            # Extract email details
            email_from = self._extract_field(content, 'from')
            email_subject = self._extract_field(content, 'subject')
            email_content = self._extract_section(content, 'Content')

            logger.info(f"Triaging email from {email_from}")

            # Draft reply using Claude Code (simplified - would use actual Claude)
            draft_reply = self._draft_email_reply(email_from, email_subject, email_content)

            # Create approval request
            approval_file = self.pending_approval_path / f"EMAIL_REPLY_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

            approval_content = f"""---
type: approval_request
action: send_email
domain: email
created_by: cloud_agent
created_at: {datetime.now().isoformat()}
expires_at: {(datetime.now()).isoformat()}
status: pending
---

# Email Reply Approval Request

**To:** {email_from}
**Subject:** Re: {email_subject}

## Draft Reply

{draft_reply}

## Original Email

{email_content[:500]}...

## Action Required

**To Approve:** Move this file to `/Approved/` folder
**To Reject:** Move this file to `/Rejected/` folder

---
*Drafted by Cloud Agent*
*Requires Local Agent approval to send*
"""

            approval_file.write_text(approval_content, encoding='utf-8')
            logger.info(f"Created approval request: {approval_file.name}")

            # Move task to done
            done_path = self.vault_path / 'Done' / task_file.name
            task_file.rename(done_path)

            # Log activity
            self._log_activity({
                'timestamp': datetime.now().isoformat(),
                'agent': 'cloud',
                'action': 'email_triage',
                'task': task_file.name,
                'approval_created': approval_file.name
            })

            return True

        except Exception as e:
            logger.error(f"Failed to process email triage: {e}")
            return False

    def process_social_draft(self, task_file: Path) -> bool:
        """
        Draft social media post but don't post.
        Creates approval request for local agent.
        """
        try:
            content = task_file.read_text(encoding='utf-8')

            platform = self._extract_field(content, 'platform') or 'linkedin'
            topic = self._extract_field(content, 'topic')

            logger.info(f"Drafting {platform} post about {topic}")

            # Draft post using Claude Code (simplified)
            draft_post = self._draft_social_post(platform, topic)

            # Create approval request
            approval_file = self.pending_approval_path / f"SOCIAL_POST_{platform.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

            approval_content = f"""---
type: approval_request
action: post_social
platform: {platform}
domain: social
created_by: cloud_agent
created_at: {datetime.now().isoformat()}
status: pending
---

# Social Media Post Approval

**Platform:** {platform}
**Topic:** {topic}

## Draft Post

{draft_post}

## Action Required

**To Approve:** Move this file to `/Approved/` folder
**To Reject:** Move this file to `/Rejected/` folder

---
*Drafted by Cloud Agent*
*Requires Local Agent approval to post*
"""

            approval_file.write_text(approval_content, encoding='utf-8')
            logger.info(f"Created approval request: {approval_file.name}")

            # Move task to done
            done_path = self.vault_path / 'Done' / task_file.name
            task_file.rename(done_path)

            self._log_activity({
                'timestamp': datetime.now().isoformat(),
                'agent': 'cloud',
                'action': 'social_draft',
                'platform': platform,
                'approval_created': approval_file.name
            })

            return True

        except Exception as e:
            logger.error(f"Failed to process social draft: {e}")
            return False

    def update_dashboard(self):
        """
        Write updates to /Updates/ folder (not Dashboard.md directly).
        Local agent will merge these updates.
        """
        try:
            update_file = self.updates_path / f"cloud_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

            # Gather statistics
            pending_approvals = len(list(self.pending_approval_path.glob('*.md')))
            in_progress = len(list(self.in_progress_path.glob('*.md')))

            update_content = f"""---
type: dashboard_update
agent: cloud
timestamp: {datetime.now().isoformat()}
---

# Cloud Agent Update

**Status:** Running
**Pending Approvals:** {pending_approvals}
**In Progress:** {in_progress}
**Last Check:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Recent Activity

Cloud agent is monitoring and creating drafts.
Waiting for local agent to process approvals.

---
*Cloud Agent Status Update*
"""

            update_file.write_text(update_content, encoding='utf-8')
            logger.debug("Dashboard update written to /Updates/")

        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")

    def run_cycle(self):
        """Run one processing cycle."""
        logger.info("Starting cloud agent cycle...")

        # Check for new tasks in Needs_Action
        for domain in self.cloud_domains:
            domain_path = self.needs_action_path / domain
            if not domain_path.exists():
                continue

            for task_file in domain_path.glob('*.md'):
                if self.claim_task(task_file):
                    # Process based on domain
                    if domain == 'email_triage':
                        self.process_email_triage(task_file)
                    elif domain == 'social_drafts':
                        self.process_social_draft(task_file)

        # Update dashboard
        self.update_dashboard()

        logger.info("Cloud agent cycle complete")

    def run_continuous(self, interval: int = 60):
        """Run continuously with specified interval."""
        logger.info(f"Cloud agent starting (interval: {interval}s)")
        logger.info(f"Domains: {', '.join(self.cloud_domains)}")

        while True:
            try:
                self.run_cycle()
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Cloud agent stopping...")
                break
            except Exception as e:
                logger.error(f"Cloud agent error: {e}", exc_info=True)
                time.sleep(interval)

    def _draft_email_reply(self, from_addr: str, subject: str, content: str) -> str:
        """Draft email reply (simplified - would use Claude Code)."""
        return f"""Hi,

Thank you for your email regarding "{subject}".

I've reviewed your message and will get back to you with a detailed response shortly.

Best regards,
AI Employee (Draft)

---
Note: This is a draft reply created by the cloud agent.
Please review and approve before sending.
"""

    def _draft_social_post(self, platform: str, topic: str) -> str:
        """Draft social media post (simplified - would use Claude Code)."""
        return f"""Excited to share insights on {topic}!

[Draft post content would be generated here by Claude Code]

#AI #Automation #{platform.capitalize()}

---
Note: This is a draft post created by the cloud agent.
Please review and approve before posting.
"""

    def _extract_domain(self, content: str) -> str:
        """Extract domain from frontmatter."""
        import re
        match = re.search(r'domain:\s*(\w+)', content)
        return match.group(1) if match else 'unknown'

    def _extract_field(self, content: str, field: str) -> str:
        """Extract field from frontmatter."""
        import re
        match = re.search(f'{field}:\\s*(.+)', content)
        return match.group(1).strip() if match else ''

    def _extract_section(self, content: str, section: str) -> str:
        """Extract section content."""
        import re
        match = re.search(f'## {section}\\n\\n(.+?)\\n\\n##', content, re.DOTALL)
        return match.group(1).strip() if match else ''

    def _log_activity(self, activity: dict):
        """Log cloud agent activity."""
        log_file = self.logs_path / f"{datetime.now().strftime('%Y-%m-%d')}_cloud_agent.json"

        try:
            logs = []
            if log_file.exists():
                content = log_file.read_text(encoding='utf-8')
                logs = json.loads(content) if content.strip() else []

            logs.append(activity)
            log_file.write_text(json.dumps(logs, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Cloud Agent - Draft-Only Operations')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault',
                       help='Path to vault')
    parser.add_argument('--interval', type=int, default=60,
                       help='Check interval in seconds')

    args = parser.parse_args()

    vault_path = Path(args.vault)
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return 1

    agent = CloudAgent(vault_path)
    agent.run_continuous(args.interval)

    return 0

if __name__ == '__main__':
    sys.exit(main())
