"""
Orchestrator - Main coordination script for AI Employee
This script manages the overall workflow and coordinates between watchers and Claude Code.
"""
import time
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('AI_Employee_Vault/Logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)

class Orchestrator:
    """Main orchestrator for the AI Employee system."""

    def __init__(self, vault_path: str = './AI_Employee_Vault'):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.logger = logging.getLogger('Orchestrator')

    def check_pending_tasks(self) -> int:
        """Check for pending tasks in Needs_Action folder."""
        tasks = list(self.needs_action.glob('*.md'))
        return len(tasks)

    def check_approved_actions(self) -> int:
        """Check for approved actions ready to execute."""
        actions = list(self.approved.glob('*.md'))
        return len(actions)

    def update_dashboard(self):
        """Update the Dashboard.md with current status."""
        dashboard_path = self.vault_path / 'Dashboard.md'

        pending_count = self.check_pending_tasks()
        approved_count = self.check_approved_actions()
        done_count = len(list(self.done.glob('*.md')))

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        content = f"""# AI Employee Dashboard

---
last_updated: {timestamp}
status: active
---

## System Status
- **Watchers Running:** File System Watcher
- **Pending Actions:** {pending_count}
- **Approved Actions:** {approved_count}
- **Completed Today:** {done_count}

## Recent Activity
- [{timestamp}] Dashboard updated by Orchestrator

## Pending Tasks
"""

        if pending_count > 0:
            tasks = list(self.needs_action.glob('*.md'))
            for task in tasks[:5]:  # Show first 5
                content += f"- {task.name}\n"
        else:
            content += "*No pending tasks*\n"

        content += f"""
## Quick Stats
- **Tasks Completed This Week:** {done_count}
- **Files Processed:** {done_count}
- **Approvals Pending:** {approved_count}

## Notes
This dashboard is automatically updated by your AI Employee.
"""

        dashboard_path.write_text(content, encoding='utf-8')
        self.logger.info(f'Dashboard updated: {pending_count} pending, {approved_count} approved')

    def run(self, interval: int = 300):
        """Main orchestration loop."""
        self.logger.info('🤖 AI Employee Orchestrator started')
        self.logger.info(f'📁 Vault: {self.vault_path.absolute()}')
        self.logger.info(f'⏰ Check interval: {interval} seconds')

        try:
            while True:
                self.update_dashboard()

                pending = self.check_pending_tasks()
                approved = self.check_approved_actions()

                if pending > 0:
                    self.logger.info(f'📋 {pending} pending task(s) - waiting for Claude Code processing')

                if approved > 0:
                    self.logger.info(f'✅ {approved} approved action(s) - ready for execution')

                time.sleep(interval)

        except KeyboardInterrupt:
            self.logger.info('🛑 Orchestrator stopped by user')

if __name__ == '__main__':
    orchestrator = Orchestrator()
    orchestrator.run()
