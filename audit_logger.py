#!/usr/bin/env python3
"""
Comprehensive Audit Logging System
Tracks all AI Employee actions for review and compliance
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger('audit_logger')

class ActionType(Enum):
    """Types of actions that can be audited."""
    EMAIL_SEND = "email_send"
    EMAIL_READ = "email_read"
    PAYMENT = "payment"
    SOCIAL_POST = "social_post"
    FILE_CREATE = "file_create"
    FILE_DELETE = "file_delete"
    FILE_MOVE = "file_move"
    API_CALL = "api_call"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    ERROR = "error"

class ApprovalStatus(Enum):
    """Approval status for actions."""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    AUTO_APPROVED = "auto_approved"

class AuditLogger:
    """Comprehensive audit logging for all AI Employee actions."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.logs_path = vault_path / 'Logs'
        self.audit_path = self.logs_path / 'Audit'

        # Ensure directories exist
        self.logs_path.mkdir(exist_ok=True)
        self.audit_path.mkdir(exist_ok=True)

    def log_action(
        self,
        action_type: ActionType,
        actor: str,
        target: str,
        parameters: Dict[str, Any],
        result: str,
        approval_status: ApprovalStatus = ApprovalStatus.NOT_REQUIRED,
        approved_by: Optional[str] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Log an action to the audit trail.

        Args:
            action_type: Type of action performed
            actor: Who/what performed the action (e.g., "claude_code", "gmail_watcher")
            target: Target of the action (e.g., email address, file path)
            parameters: Action parameters (e.g., email subject, payment amount)
            result: Result of the action ("success", "failure", "pending")
            approval_status: Approval status for the action
            approved_by: Who approved the action (if applicable)
            error: Error message if action failed

        Returns:
            True if logged successfully
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type.value,
            "actor": actor,
            "target": target,
            "parameters": parameters,
            "approval_status": approval_status.value,
            "approved_by": approved_by,
            "result": result,
            "error": error
        }

        # Determine log file (daily rotation)
        log_file = self.audit_path / f"{datetime.now().strftime('%Y-%m-%d')}_audit.json"

        try:
            # Append to existing log
            if log_file.exists():
                content = log_file.read_text(encoding='utf-8')
                logs = json.loads(content) if content.strip() else []
            else:
                logs = []

            logs.append(log_entry)
            log_file.write_text(json.dumps(logs, indent=2), encoding='utf-8')

            logger.info(f"Audit log entry created: {action_type.value} by {actor}")
            return True

        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            return False

    def log_email_send(
        self,
        to: str,
        subject: str,
        approved_by: Optional[str] = None,
        result: str = "success"
    ):
        """Log email send action."""
        return self.log_action(
            action_type=ActionType.EMAIL_SEND,
            actor="email_mcp",
            target=to,
            parameters={"subject": subject},
            result=result,
            approval_status=ApprovalStatus.APPROVED if approved_by else ApprovalStatus.AUTO_APPROVED,
            approved_by=approved_by
        )

    def log_payment(
        self,
        recipient: str,
        amount: float,
        reference: str,
        approved_by: str,
        result: str = "success"
    ):
        """Log payment action."""
        return self.log_action(
            action_type=ActionType.PAYMENT,
            actor="payment_mcp",
            target=recipient,
            parameters={
                "amount": amount,
                "reference": reference
            },
            result=result,
            approval_status=ApprovalStatus.APPROVED,
            approved_by=approved_by
        )

    def log_social_post(
        self,
        platform: str,
        content: str,
        result: str = "success"
    ):
        """Log social media post action."""
        return self.log_action(
            action_type=ActionType.SOCIAL_POST,
            actor=f"{platform}_poster",
            target=platform,
            parameters={"content": content[:100]},  # Truncate for privacy
            result=result,
            approval_status=ApprovalStatus.AUTO_APPROVED
        )

    def log_file_operation(
        self,
        operation: str,
        file_path: str,
        actor: str = "claude_code",
        result: str = "success"
    ):
        """Log file operation."""
        action_map = {
            "create": ActionType.FILE_CREATE,
            "delete": ActionType.FILE_DELETE,
            "move": ActionType.FILE_MOVE
        }

        return self.log_action(
            action_type=action_map.get(operation, ActionType.FILE_CREATE),
            actor=actor,
            target=file_path,
            parameters={"operation": operation},
            result=result,
            approval_status=ApprovalStatus.NOT_REQUIRED
        )

    def log_approval_request(
        self,
        action_type: ActionType,
        target: str,
        parameters: Dict[str, Any]
    ):
        """Log approval request creation."""
        return self.log_action(
            action_type=ActionType.APPROVAL_REQUEST,
            actor="claude_code",
            target=target,
            parameters={
                "requested_action": action_type.value,
                **parameters
            },
            result="pending",
            approval_status=ApprovalStatus.PENDING
        )

    def log_error(
        self,
        actor: str,
        error_message: str,
        context: Dict[str, Any]
    ):
        """Log error occurrence."""
        return self.log_action(
            action_type=ActionType.ERROR,
            actor=actor,
            target="system",
            parameters=context,
            result="failure",
            error=error_message
        )

    def get_audit_trail(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        action_type: Optional[ActionType] = None,
        actor: Optional[str] = None
    ) -> list:
        """
        Retrieve audit trail with optional filters.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            action_type: Filter by action type
            actor: Filter by actor

        Returns:
            List of audit log entries
        """
        all_logs = []

        # Read all audit files in date range
        for log_file in sorted(self.audit_path.glob('*_audit.json')):
            try:
                content = log_file.read_text(encoding='utf-8')
                logs = json.loads(content) if content.strip() else []

                # Apply filters
                for log in logs:
                    # Date filter
                    if start_date and log['timestamp'] < start_date:
                        continue
                    if end_date and log['timestamp'] > end_date:
                        continue

                    # Action type filter
                    if action_type and log['action_type'] != action_type.value:
                        continue

                    # Actor filter
                    if actor and log['actor'] != actor:
                        continue

                    all_logs.append(log)

            except Exception as e:
                logger.error(f"Failed to read audit log {log_file}: {e}")

        return all_logs

    def generate_audit_report(
        self,
        start_date: str,
        end_date: str,
        output_file: Optional[Path] = None
    ) -> str:
        """
        Generate human-readable audit report.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            output_file: Optional output file path

        Returns:
            Report content as string
        """
        logs = self.get_audit_trail(start_date, end_date)

        # Generate statistics
        total_actions = len(logs)
        actions_by_type = {}
        actions_by_actor = {}
        approval_stats = {
            'pending': 0,
            'approved': 0,
            'denied': 0,
            'auto_approved': 0
        }

        for log in logs:
            # Count by type
            action_type = log['action_type']
            actions_by_type[action_type] = actions_by_type.get(action_type, 0) + 1

            # Count by actor
            actor = log['actor']
            actions_by_actor[actor] = actions_by_actor.get(actor, 0) + 1

            # Count approvals
            approval = log.get('approval_status', 'not_required')
            if approval in approval_stats:
                approval_stats[approval] += 1

        # Generate report
        report = f"""# Audit Report
Period: {start_date} to {end_date}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total Actions: {total_actions}
- Pending Approvals: {approval_stats['pending']}
- Approved Actions: {approval_stats['approved']}
- Auto-Approved Actions: {approval_stats['auto_approved']}
- Denied Actions: {approval_stats['denied']}

## Actions by Type
"""

        for action_type, count in sorted(actions_by_type.items(), key=lambda x: x[1], reverse=True):
            report += f"- {action_type}: {count}\n"

        report += "\n## Actions by Actor\n"
        for actor, count in sorted(actions_by_actor.items(), key=lambda x: x[1], reverse=True):
            report += f"- {actor}: {count}\n"

        report += "\n## Recent Actions\n"
        for log in logs[-20:]:  # Last 20 actions
            report += f"\n### {log['timestamp']}\n"
            report += f"- Type: {log['action_type']}\n"
            report += f"- Actor: {log['actor']}\n"
            report += f"- Target: {log['target']}\n"
            report += f"- Result: {log['result']}\n"

        # Save to file if specified
        if output_file:
            try:
                output_file.write_text(report, encoding='utf-8')
                logger.info(f"Audit report saved to: {output_file}")
            except Exception as e:
                logger.error(f"Failed to save audit report: {e}")

        return report

# Example usage
if __name__ == '__main__':
    vault_path = Path('./AI_Employee_Vault')
    audit_logger = AuditLogger(vault_path)

    # Example: Log email send
    audit_logger.log_email_send(
        to="client@example.com",
        subject="Invoice #123",
        approved_by="human",
        result="success"
    )

    # Example: Log payment
    audit_logger.log_payment(
        recipient="Vendor A",
        amount=500.00,
        reference="Invoice #456",
        approved_by="human",
        result="success"
    )

    # Example: Generate report
    report = audit_logger.generate_audit_report(
        start_date="2026-02-01",
        end_date="2026-02-28"
    )
    print(report)
