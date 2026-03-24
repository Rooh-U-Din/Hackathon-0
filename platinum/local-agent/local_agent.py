#!/usr/bin/env python3
"""
Local Agent - Approval Processing and Execution
Runs on local machine, processes approvals and executes sensitive actions
Handles WhatsApp sessions, payments, and final send/post actions
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('local_agent')

class LocalAgent:
    """Local-side agent with approval and execution capabilities."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.pending_approval_path = vault_path / 'Pending_Approval'
        self.approved_path = vault_path / 'Approved'
        self.rejected_path = vault_path / 'Rejected'
        self.done_path = vault_path / 'Done'
        self.updates_path = vault_path / 'Updates'
        self.dashboard_path = vault_path / 'Dashboard.md'
        self.logs_path = vault_path / 'Logs'
        self.in_progress_path = vault_path / 'In_Progress' / 'local'

        # Ensure directories exist
        self.approved_path.mkdir(exist_ok=True)
        self.rejected_path.mkdir(exist_ok=True)
        self.in_progress_path.mkdir(parents=True, exist_ok=True)

        # Domain ownership (local handles these)
        self.local_domains = ['approvals', 'whatsapp', 'payments', 'execution']

    def process_approvals(self):
        """Process approved actions."""
        logger.info("Checking for approved actions...")

        for approval_file in self.approved_path.glob('*.md'):
            try:
                content = approval_file.read_text(encoding='utf-8')

                # Extract action type
                action_type = self._extract_field(content, 'action')

                logger.info(f"Processing approved action: {action_type}")

                # Execute based on action type
                if action_type == 'send_email':
                    self._execute_email_send(approval_file, content)
                elif action_type == 'post_social':
                    self._execute_social_post(approval_file, content)
                elif action_type == 'payment':
                    self._execute_payment(approval_file, content)
                else:
                    logger.warning(f"Unknown action type: {action_type}")

            except Exception as e:
                logger.error(f"Failed to process approval {approval_file.name}: {e}")

    def process_rejections(self):
        """Process rejected actions."""
        logger.info("Checking for rejected actions...")

        for rejection_file in self.rejected_path.glob('*.md'):
            try:
                logger.info(f"Logging rejection: {rejection_file.name}")

                # Log rejection
                self._log_activity({
                    'timestamp': datetime.now().isoformat(),
                    'agent': 'local',
                    'action': 'rejection',
                    'file': rejection_file.name
                })

                # Move to done
                done_file = self.done_path / rejection_file.name
                rejection_file.rename(done_file)

            except Exception as e:
                logger.error(f"Failed to process rejection {rejection_file.name}: {e}")

    def merge_cloud_updates(self):
        """Merge cloud updates into Dashboard.md."""
        logger.info("Checking for cloud updates...")

        for update_file in self.updates_path.glob('cloud_update_*.md'):
            try:
                content = update_file.read_text(encoding='utf-8')

                # Extract update info
                timestamp = self._extract_field(content, 'timestamp')
                update_content = self._extract_section(content, 'Cloud Agent Update')

                logger.info(f"Merging cloud update from {timestamp}")

                # Update Dashboard.md (single-writer rule: only local writes here)
                self._update_dashboard(update_content)

                # Archive update
                archive_path = self.vault_path / 'Logs' / 'Updates' / update_file.name
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                update_file.rename(archive_path)

            except Exception as e:
                logger.error(f"Failed to merge update {update_file.name}: {e}")

    def _execute_email_send(self, approval_file: Path, content: str):
        """Execute approved email send via MCP."""
        try:
            to_addr = self._extract_field(content, 'To')
            subject = self._extract_field(content, 'Subject')
            body = self._extract_section(content, 'Draft Reply')

            logger.info(f"Sending email to {to_addr}")

            # Execute via email MCP (simplified - would use actual MCP)
            # In production, this would call the email MCP server
            success = self._send_email_via_mcp(to_addr, subject, body)

            if success:
                logger.info("Email sent successfully")

                # Log to audit
                from audit_logger import AuditLogger, ActionType, ApprovalStatus
                audit = AuditLogger(self.vault_path)
                audit.log_action(
                    action_type=ActionType.EMAIL_SEND,
                    actor='local_agent',
                    target=to_addr,
                    parameters={'subject': subject},
                    result='success',
                    approval_status=ApprovalStatus.APPROVED,
                    approved_by='human'
                )

                # Move to done
                done_file = self.done_path / approval_file.name
                approval_file.rename(done_file)
            else:
                logger.error("Email send failed")

        except Exception as e:
            logger.error(f"Failed to execute email send: {e}")

    def _execute_social_post(self, approval_file: Path, content: str):
        """Execute approved social media post."""
        try:
            platform = self._extract_field(content, 'platform')
            post_content = self._extract_section(content, 'Draft Post')

            logger.info(f"Posting to {platform}")

            # Execute via social poster skill
            success = self._post_to_social(platform, post_content)

            if success:
                logger.info(f"Posted to {platform} successfully")

                # Log to audit
                from audit_logger import AuditLogger, ActionType, ApprovalStatus
                audit = AuditLogger(self.vault_path)
                audit.log_action(
                    action_type=ActionType.SOCIAL_POST,
                    actor='local_agent',
                    target=platform,
                    parameters={'content': post_content[:100]},
                    result='success',
                    approval_status=ApprovalStatus.APPROVED,
                    approved_by='human'
                )

                # Move to done
                done_file = self.done_path / approval_file.name
                approval_file.rename(done_file)
            else:
                logger.error(f"Post to {platform} failed")

        except Exception as e:
            logger.error(f"Failed to execute social post: {e}")

    def _execute_payment(self, approval_file: Path, content: str):
        """Execute approved payment (local only - never on cloud)."""
        try:
            recipient = self._extract_field(content, 'recipient')
            amount = float(self._extract_field(content, 'amount'))
            reference = self._extract_field(content, 'reference')

            logger.info(f"Processing payment to {recipient}: ${amount}")

            # Execute via payment MCP (local only)
            success = self._process_payment(recipient, amount, reference)

            if success:
                logger.info("Payment processed successfully")

                # Log to audit
                from audit_logger import AuditLogger, ActionType, ApprovalStatus
                audit = AuditLogger(self.vault_path)
                audit.log_action(
                    action_type=ActionType.PAYMENT,
                    actor='local_agent',
                    target=recipient,
                    parameters={'amount': amount, 'reference': reference},
                    result='success',
                    approval_status=ApprovalStatus.APPROVED,
                    approved_by='human'
                )

                # Move to done
                done_file = self.done_path / approval_file.name
                approval_file.rename(done_file)
            else:
                logger.error("Payment processing failed")

        except Exception as e:
            logger.error(f"Failed to execute payment: {e}")

    def _send_email_via_mcp(self, to: str, subject: str, body: str) -> bool:
        """Send email via MCP server (simplified)."""
        # In production, this would call the actual email MCP server
        logger.info(f"[DEMO] Would send email to {to}")
        return True

    def _post_to_social(self, platform: str, content: str) -> bool:
        """Post to social media via skill (simplified)."""
        # In production, this would call the actual social poster skill
        logger.info(f"[DEMO] Would post to {platform}")
        return True

    def _process_payment(self, recipient: str, amount: float, reference: str) -> bool:
        """Process payment via MCP (simplified)."""
        # In production, this would call the actual payment MCP
        logger.info(f"[DEMO] Would process payment: {recipient} ${amount}")
        return True

    def _update_dashboard(self, update_content: str):
        """Update Dashboard.md with cloud updates."""
        try:
            if not self.dashboard_path.exists():
                # Create initial dashboard
                dashboard_content = f"""# AI Employee Dashboard

Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## System Status

**Local Agent:** Running
**Cloud Agent:** Running (via updates)

## Recent Updates

{update_content}

---
*Dashboard managed by Local Agent*
"""
                self.dashboard_path.write_text(dashboard_content, encoding='utf-8')
            else:
                # Append update
                current = self.dashboard_path.read_text(encoding='utf-8')
                updated = current.replace(
                    '## Recent Updates',
                    f'## Recent Updates\n\n### {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n{update_content}\n'
                )
                self.dashboard_path.write_text(updated, encoding='utf-8')

            logger.info("Dashboard updated")

        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")

    def run_cycle(self):
        """Run one processing cycle."""
        logger.info("Starting local agent cycle...")

        # Process approvals
        self.process_approvals()

        # Process rejections
        self.process_rejections()

        # Merge cloud updates
        self.merge_cloud_updates()

        logger.info("Local agent cycle complete")

    def run_once(self):
        """Run once (for on-demand execution)."""
        logger.info("Local agent running once...")
        self.run_cycle()

    def _extract_field(self, content: str, field: str) -> str:
        """Extract field from content."""
        import re
        # Try frontmatter first
        match = re.search(f'{field}:\\s*(.+)', content)
        if match:
            return match.group(1).strip()
        # Try markdown bold
        match = re.search(f'\\*\\*{field}:\\*\\*\\s*(.+)', content)
        return match.group(1).strip() if match else ''

    def _extract_section(self, content: str, section: str) -> str:
        """Extract section content."""
        import re
        match = re.search(f'## {section}\\n\\n(.+?)\\n\\n##', content, re.DOTALL)
        if not match:
            match = re.search(f'## {section}\\n\\n(.+?)\\n\\n---', content, re.DOTALL)
        return match.group(1).strip() if match else ''

    def _log_activity(self, activity: dict):
        """Log local agent activity."""
        log_file = self.logs_path / f"{datetime.now().strftime('%Y-%m-%d')}_local_agent.json"

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

    parser = argparse.ArgumentParser(description='Local Agent - Approval Processing and Execution')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault',
                       help='Path to vault')
    parser.add_argument('--once', action='store_true',
                       help='Run once and exit (for on-demand execution)')

    args = parser.parse_args()

    vault_path = Path(args.vault)
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return 1

    agent = LocalAgent(vault_path)

    if args.once:
        agent.run_once()
    else:
        logger.info("Local agent running in on-demand mode")
        logger.info("Use --once flag to run a single cycle")

    return 0

if __name__ == '__main__':
    sys.exit(main())
