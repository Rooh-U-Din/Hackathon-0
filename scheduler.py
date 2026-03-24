#!/usr/bin/env python3
"""
AI Employee Scheduler - Run skills on schedule
Supports both continuous and scheduled operations
"""
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, time as dt_time
import json
import schedule

def run_skill(skill_name, args=""):
    """Run a skill and log the result."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running: {skill_name}")

    try:
        cmd = f"python .claude/skills/{skill_name}/skill.py {args}"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            print(f"  ✅ Success")
        else:
            print(f"  ❌ Failed: {result.stderr[:100]}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"  ⏱️  Timeout")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def check_gmail():
    """Check Gmail for new emails."""
    return run_skill("gmail-watcher", "--max-emails 10")

def check_whatsapp():
    """Check WhatsApp for new messages."""
    return run_skill("whatsapp-watcher")

def process_tasks():
    """Process pending tasks."""
    return run_skill("process-tasks")

def generate_plans():
    """Generate plans for complex tasks."""
    return run_skill("plan-generator")

def check_approvals():
    """Check for pending approvals."""
    return run_skill("approval-workflow", "--action check")

def create_linkedin_draft():
    """Create LinkedIn post draft."""
    return run_skill("linkedin-poster", "--draft-only true")

def morning_routine():
    """Morning routine - check everything."""
    print("\n" + "="*50)
    print("🌅 MORNING ROUTINE")
    print("="*50 + "\n")

    check_gmail()
    check_whatsapp()
    process_tasks()
    generate_plans()
    check_approvals()

def afternoon_routine():
    """Afternoon routine - lighter checks."""
    print("\n" + "="*50)
    print("☀️ AFTERNOON ROUTINE")
    print("="*50 + "\n")

    check_gmail()
    check_whatsapp()
    process_tasks()

def evening_routine():
    """Evening routine - wrap up day."""
    print("\n" + "="*50)
    print("🌙 EVENING ROUTINE")
    print("="*50 + "\n")

    check_gmail()
    process_tasks()
    check_approvals()

def main():
    """Main scheduler loop."""
    print("🤖 AI Employee Scheduler")
    print("=" * 50)
    print()
    print("Scheduling tasks...")
    print()

    # Morning routine (8:00 AM)
    schedule.every().day.at("08:00").do(morning_routine)

    # Check emails every 15 minutes during work hours
    schedule.every(15).minutes.do(check_gmail)

    # Check WhatsApp every 5 minutes during work hours
    schedule.every(5).minutes.do(check_whatsapp)

    # Process tasks every 30 minutes
    schedule.every(30).minutes.do(process_tasks)

    # Generate plans every hour
    schedule.every().hour.do(generate_plans)

    # Check approvals every 2 hours
    schedule.every(2).hours.do(check_approvals)

    # Afternoon routine (1:00 PM)
    schedule.every().day.at("13:00").do(afternoon_routine)

    # Evening routine (6:00 PM)
    schedule.every().day.at("18:00").do(evening_routine)

    # Create LinkedIn draft (Mon, Wed, Fri at 9:00 AM)
    schedule.every().monday.at("09:00").do(create_linkedin_draft)
    schedule.every().wednesday.at("09:00").do(create_linkedin_draft)
    schedule.every().friday.at("09:00").do(create_linkedin_draft)

    print("📅 Schedule configured:")
    print("  - Morning routine: 8:00 AM daily")
    print("  - Gmail check: Every 15 minutes")
    print("  - WhatsApp check: Every 5 minutes")
    print("  - Task processing: Every 30 minutes")
    print("  - Plan generation: Every hour")
    print("  - Approval check: Every 2 hours")
    print("  - Afternoon routine: 1:00 PM daily")
    print("  - Evening routine: 6:00 PM daily")
    print("  - LinkedIn drafts: Mon/Wed/Fri at 9:00 AM")
    print()
    print("🚀 Scheduler running... (Press Ctrl+C to stop)")
    print()

    # Run initial check
    print("Running initial check...")
    morning_routine()

    # Main loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n⏹️  Scheduler stopped")
        return 0

if __name__ == '__main__':
    sys.exit(main())
