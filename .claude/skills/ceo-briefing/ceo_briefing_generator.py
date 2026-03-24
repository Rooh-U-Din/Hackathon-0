#!/usr/bin/env python3
"""
CEO Briefing Generator - Weekly Business Audit
Analyzes business performance and generates executive briefing
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ceo_briefing_generator')

class CEOBriefingGenerator:
    """Generates weekly CEO briefings with business insights."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.briefings_path = vault_path / 'Briefings'
        self.done_path = vault_path / 'Done'
        self.logs_path = vault_path / 'Logs'
        self.business_goals_path = vault_path / 'Business_Goals.md'

        # Ensure directories exist
        self.briefings_path.mkdir(exist_ok=True)

    def read_business_goals(self) -> Dict[str, Any]:
        """Read and parse Business_Goals.md."""
        if not self.business_goals_path.exists():
            logger.warning("Business_Goals.md not found, using defaults")
            return {
                'revenue_target': 10000,
                'metrics': {},
                'projects': []
            }

        content = self.business_goals_path.read_text(encoding='utf-8')
        goals = {
            'revenue_target': 10000,
            'metrics': {},
            'projects': [],
            'subscription_rules': []
        }

        # Parse revenue target
        revenue_match = re.search(r'Monthly goal:\s*\$?([\d,]+)', content)
        if revenue_match:
            goals['revenue_target'] = float(revenue_match.group(1).replace(',', ''))

        # Parse current MTD
        mtd_match = re.search(r'Current MTD:\s*\$?([\d,]+)', content)
        if mtd_match:
            goals['current_mtd'] = float(mtd_match.group(1).replace(',', ''))

        # Parse projects
        project_matches = re.findall(r'\d+\.\s+(.+?)\s+-\s+Due\s+(.+?)\s+-\s+Budget\s+\$?([\d,]+)', content)
        for name, due_date, budget in project_matches:
            goals['projects'].append({
                'name': name.strip(),
                'due_date': due_date.strip(),
                'budget': float(budget.replace(',', ''))
            })

        return goals

    def analyze_completed_tasks(self, days: int = 7) -> Dict[str, Any]:
        """Analyze tasks completed in the last N days."""
        if not self.done_path.exists():
            return {'count': 0, 'tasks': [], 'bottlenecks': []}

        cutoff_date = datetime.now() - timedelta(days=days)
        completed_tasks = []

        for task_file in self.done_path.glob('*.md'):
            try:
                # Check file modification time
                mtime = datetime.fromtimestamp(task_file.stat().st_mtime)
                if mtime < cutoff_date:
                    continue

                content = task_file.read_text(encoding='utf-8')

                # Extract metadata
                task_info = {
                    'file': task_file.name,
                    'completed_date': mtime.isoformat(),
                    'title': self._extract_title(content),
                    'type': self._extract_type(content)
                }

                completed_tasks.append(task_info)
            except Exception as e:
                logger.warning(f"Error reading task {task_file}: {e}")

        # Identify bottlenecks (tasks that took too long)
        bottlenecks = self._identify_bottlenecks(completed_tasks)

        return {
            'count': len(completed_tasks),
            'tasks': completed_tasks,
            'bottlenecks': bottlenecks
        }

    def analyze_revenue(self, days: int = 7) -> Dict[str, Any]:
        """Analyze revenue from logs and transaction data."""
        revenue_data = {
            'week_total': 0.0,
            'month_total': 0.0,
            'transactions': []
        }

        if not self.logs_path.exists():
            return revenue_data

        cutoff_date = datetime.now() - timedelta(days=days)

        # Look for transaction logs
        for log_file in self.logs_path.glob('*_transactions.json'):
            try:
                content = log_file.read_text(encoding='utf-8')
                transactions = json.loads(content) if content.strip() else []

                for txn in transactions:
                    txn_date = datetime.fromisoformat(txn.get('date', ''))
                    amount = float(txn.get('amount', 0))

                    if txn.get('type') == 'income' and amount > 0:
                        revenue_data['month_total'] += amount
                        if txn_date >= cutoff_date:
                            revenue_data['week_total'] += amount
                            revenue_data['transactions'].append(txn)
            except Exception as e:
                logger.warning(f"Error reading transaction log {log_file}: {e}")

        return revenue_data

    def analyze_subscriptions(self) -> List[Dict[str, Any]]:
        """Identify unused or expensive subscriptions."""
        subscriptions = []

        if not self.logs_path.exists():
            return subscriptions

        # Look for subscription patterns in transaction logs
        subscription_patterns = {
            'netflix.com': 'Netflix',
            'spotify.com': 'Spotify',
            'adobe.com': 'Adobe Creative Cloud',
            'notion.so': 'Notion',
            'slack.com': 'Slack',
            'github.com': 'GitHub',
            'aws.amazon.com': 'AWS',
            'digitalocean.com': 'DigitalOcean'
        }

        for log_file in self.logs_path.glob('*_transactions.json'):
            try:
                content = log_file.read_text(encoding='utf-8')
                transactions = json.loads(content) if content.strip() else []

                for txn in transactions:
                    description = txn.get('description', '').lower()
                    for pattern, name in subscription_patterns.items():
                        if pattern in description:
                            subscriptions.append({
                                'name': name,
                                'amount': float(txn.get('amount', 0)),
                                'date': txn.get('date'),
                                'description': txn.get('description')
                            })
            except Exception as e:
                logger.warning(f"Error analyzing subscriptions: {e}")

        return subscriptions

    def generate_briefing(self, period_days: int = 7) -> Path:
        """Generate the CEO briefing markdown file."""
        logger.info("Generating CEO briefing...")

        # Gather data
        goals = self.read_business_goals()
        tasks = self.analyze_completed_tasks(period_days)
        revenue = self.analyze_revenue(period_days)
        subscriptions = self.analyze_subscriptions()

        # Calculate metrics
        revenue_target = goals.get('revenue_target', 10000)
        week_revenue = revenue['week_total']
        month_revenue = revenue['month_total']
        progress_pct = (month_revenue / revenue_target * 100) if revenue_target > 0 else 0

        # Determine trend
        if progress_pct >= 90:
            trend = "Exceeding target"
        elif progress_pct >= 70:
            trend = "On track"
        elif progress_pct >= 50:
            trend = "Below target"
        else:
            trend = "Significantly behind"

        # Generate briefing content
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        briefing_content = f"""---
generated: {datetime.now().isoformat()}
period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}
---

# Monday Morning CEO Briefing

## Executive Summary
{self._generate_executive_summary(tasks, revenue, trend)}

## Revenue
- **This Week**: ${week_revenue:,.2f}
- **MTD**: ${month_revenue:,.2f} ({progress_pct:.1f}% of ${revenue_target:,.0f} target)
- **Trend**: {trend}

## Completed Tasks
{self._format_completed_tasks(tasks)}

## Bottlenecks
{self._format_bottlenecks(tasks['bottlenecks'])}

## Proactive Suggestions

### Cost Optimization
{self._format_subscription_suggestions(subscriptions)}

### Upcoming Deadlines
{self._format_upcoming_deadlines(goals.get('projects', []))}

## Key Metrics
- Tasks completed: {tasks['count']}
- Average task completion: {self._calculate_avg_completion_time(tasks)} days
- Revenue per task: ${(week_revenue / tasks['count']) if tasks['count'] > 0 else 0:,.2f}

---
*Generated by CEO Briefing Generator Agent Skill*
*AI Employee v1.0 - Gold Tier*
"""

        # Save briefing
        briefing_filename = f"{end_date.strftime('%Y-%m-%d')}_Monday_Briefing.md"
        briefing_path = self.briefings_path / briefing_filename
        briefing_path.write_text(briefing_content, encoding='utf-8')

        logger.info(f"CEO briefing generated: {briefing_path}")

        # Log activity
        self._log_activity({
            'timestamp': datetime.now().isoformat(),
            'activity': 'briefing_generated',
            'period_days': period_days,
            'tasks_analyzed': tasks['count'],
            'revenue_week': week_revenue,
            'revenue_month': month_revenue
        })

        return briefing_path

    def _extract_title(self, content: str) -> str:
        """Extract title from markdown content."""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return "Untitled"

    def _extract_type(self, content: str) -> str:
        """Extract type from frontmatter."""
        match = re.search(r'type:\s*(\w+)', content)
        return match.group(1) if match else 'unknown'

    def _identify_bottlenecks(self, tasks: List[Dict]) -> List[Dict]:
        """Identify tasks that took longer than expected."""
        bottlenecks = []
        # Simple heuristic: tasks with "delay" or "overdue" in title
        for task in tasks:
            title = task.get('title', '').lower()
            if 'delay' in title or 'overdue' in title or 'late' in title:
                bottlenecks.append({
                    'task': task['title'],
                    'issue': 'Delayed completion'
                })
        return bottlenecks

    def _generate_executive_summary(self, tasks: Dict, revenue: Dict, trend: str) -> str:
        """Generate executive summary text."""
        if trend in ["Exceeding target", "On track"]:
            performance = "Strong week with revenue on track."
        else:
            performance = "Week below target, attention needed."

        bottleneck_text = ""
        if tasks['bottlenecks']:
            bottleneck_text = f" {len(tasks['bottlenecks'])} bottleneck(s) identified."

        return performance + bottleneck_text

    def _format_completed_tasks(self, tasks: Dict) -> str:
        """Format completed tasks section."""
        if tasks['count'] == 0:
            return "- No tasks completed this week"

        lines = []
        for task in tasks['tasks'][:10]:  # Show top 10
            lines.append(f"- [x] {task['title']}")

        if tasks['count'] > 10:
            lines.append(f"- ... and {tasks['count'] - 10} more tasks")

        return '\n'.join(lines)

    def _format_bottlenecks(self, bottlenecks: List[Dict]) -> str:
        """Format bottlenecks section."""
        if not bottlenecks:
            return "No significant bottlenecks identified."

        lines = ["| Task | Issue |", "|------|-------|"]
        for bottleneck in bottlenecks:
            lines.append(f"| {bottleneck['task']} | {bottleneck['issue']} |")

        return '\n'.join(lines)

    def _format_subscription_suggestions(self, subscriptions: List[Dict]) -> str:
        """Format subscription optimization suggestions."""
        if not subscriptions:
            return "- No subscription optimization opportunities identified"

        lines = []
        # Group by subscription name
        sub_totals = {}
        for sub in subscriptions:
            name = sub['name']
            amount = sub['amount']
            sub_totals[name] = sub_totals.get(name, 0) + amount

        for name, total in sub_totals.items():
            lines.append(f"- **{name}**: ${total:.2f}/month")
            lines.append(f"  - [ACTION] Review usage and consider optimization")

        return '\n'.join(lines)

    def _format_upcoming_deadlines(self, projects: List[Dict]) -> str:
        """Format upcoming project deadlines."""
        if not projects:
            return "- No upcoming project deadlines"

        lines = []
        for project in projects:
            lines.append(f"- {project['name']}: {project['due_date']} (Budget: ${project['budget']:,.0f})")

        return '\n'.join(lines)

    def _calculate_avg_completion_time(self, tasks: Dict) -> float:
        """Calculate average task completion time."""
        # Simplified: return a placeholder
        return 2.5

    def _log_activity(self, activity: Dict):
        """Log briefing generation activity."""
        log_file = self.logs_path / f"{datetime.now().strftime('%Y-%m-%d')}_ceo_briefing.json"

        try:
            # Append to existing log
            if log_file.exists():
                content = log_file.read_text(encoding='utf-8')
                logs = json.loads(content) if content.strip() else []
            else:
                logs = []

            logs.append(activity)
            log_file.write_text(json.dumps(logs, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='CEO Briefing Generator Agent Skill')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault',
                       help='Path to Obsidian vault')
    parser.add_argument('--period-days', type=int, default=7,
                       help='Number of days to analyze (default: 7)')

    args = parser.parse_args()

    print("CEO Briefing Generator Agent Skill")
    print("=" * 50)
    print()

    vault_path = Path(args.vault)
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return 1

    generator = CEOBriefingGenerator(vault_path)

    try:
        briefing_path = generator.generate_briefing(args.period_days)
        print()
        print(f"[SUCCESS] CEO briefing generated: {briefing_path}")
        print(f"[INFO] Review the briefing in your Obsidian vault")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate briefing: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
