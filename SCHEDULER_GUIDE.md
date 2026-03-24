# AI Employee Scheduler

Automated scheduling system for running AI Employee skills on a schedule.

## What this does

The scheduler runs your AI Employee skills automatically:
- Checks Gmail every 15 minutes
- Checks WhatsApp every 5 minutes
- Processes tasks every 30 minutes
- Generates plans every hour
- Checks approvals every 2 hours
- Creates LinkedIn drafts 3x per week
- Runs morning, afternoon, and evening routines

## Prerequisites

- Python 3.10+
- All skills installed and working
- Credentials configured

## Installation

```bash
pip install schedule
```

## Usage

### Run the scheduler

```bash
python scheduler.py
```

The scheduler will run continuously until stopped (Ctrl+C).

### Run as background service

**Windows (Task Scheduler):**

1. Open Task Scheduler
2. Create Basic Task
3. Name: "AI Employee Scheduler"
4. Trigger: At startup
5. Action: Start a program
6. Program: `python`
7. Arguments: `D:\vsCode\CLI\Hackathon-0\scheduler.py`
8. Start in: `D:\vsCode\CLI\Hackathon-0`

**Linux/Mac (cron):**

```bash
# Edit crontab
crontab -e

# Add this line (runs at startup)
@reboot cd /path/to/Hackathon-0 && python scheduler.py >> scheduler.log 2>&1
```

**Using PM2 (recommended):**

```bash
# Install PM2
npm install -g pm2

# Start scheduler
pm2 start scheduler.py --interpreter python3 --name ai-employee-scheduler

# Save configuration
pm2 save

# Set to start on boot
pm2 startup
```

## Schedule Configuration

Edit `scheduler.py` to customize:

```python
# Change frequency
schedule.every(30).minutes.do(check_gmail)  # Every 30 min instead of 15

# Change time
schedule.every().day.at("09:00").do(morning_routine)  # 9 AM instead of 8 AM

# Add new task
schedule.every().day.at("12:00").do(lunch_routine)

# Remove task
# Comment out or delete the line
```

## Default Schedule

| Task | Frequency | Time |
|------|-----------|------|
| Morning routine | Daily | 8:00 AM |
| Gmail check | Every 15 min | Work hours |
| WhatsApp check | Every 5 min | Work hours |
| Task processing | Every 30 min | All day |
| Plan generation | Every hour | All day |
| Approval check | Every 2 hours | All day |
| Afternoon routine | Daily | 1:00 PM |
| Evening routine | Daily | 6:00 PM |
| LinkedIn drafts | Mon/Wed/Fri | 9:00 AM |

## Routines

### Morning Routine (8:00 AM)
- Check Gmail
- Check WhatsApp
- Process tasks
- Generate plans
- Check approvals

### Afternoon Routine (1:00 PM)
- Check Gmail
- Check WhatsApp
- Process tasks

### Evening Routine (6:00 PM)
- Check Gmail
- Process tasks
- Check approvals

## Monitoring

The scheduler logs all activity to stdout:

```
[2026-02-27 08:00:00] Running: gmail-watcher
  ✅ Success
[2026-02-27 08:00:15] Running: whatsapp-watcher
  ✅ Success
```

**Save logs to file:**

```bash
python scheduler.py >> scheduler.log 2>&1
```

**View logs:**

```bash
tail -f scheduler.log
```

## Work Hours Configuration

To limit checks to work hours only, modify the scheduler:

```python
import datetime

def is_work_hours():
    """Check if current time is during work hours."""
    now = datetime.datetime.now()
    # Monday-Friday, 8 AM - 6 PM
    if now.weekday() >= 5:  # Weekend
        return False
    if now.hour < 8 or now.hour >= 18:
        return False
    return True

def check_gmail():
    """Check Gmail only during work hours."""
    if is_work_hours():
        return run_skill("gmail-watcher")
```

## Error Handling

The scheduler:
- Continues running if a skill fails
- Logs all errors
- Has 5-minute timeout per skill
- Retries on next scheduled run

## Stopping the Scheduler

**Interactive mode:**
- Press Ctrl+C

**PM2:**
```bash
pm2 stop ai-employee-scheduler
```

**Task Scheduler (Windows):**
- Open Task Scheduler
- Find "AI Employee Scheduler"
- Right-click → End

## Troubleshooting

**Scheduler not running:**
- Check Python is in PATH
- Verify all skills work independently
- Review error logs

**Skills failing:**
- Test each skill manually first
- Check credentials are valid
- Verify network connectivity

**High CPU usage:**
- Increase check intervals
- Reduce concurrent operations
- Check for infinite loops in skills

## Advanced Configuration

### Custom Schedule File

Create `schedule_config.json`:

```json
{
  "gmail_check_interval": 15,
  "whatsapp_check_interval": 5,
  "task_processing_interval": 30,
  "morning_routine_time": "08:00",
  "evening_routine_time": "18:00",
  "work_days": [0, 1, 2, 3, 4],
  "work_hours_start": 8,
  "work_hours_end": 18
}
```

### Conditional Scheduling

Run tasks only when conditions are met:

```python
def smart_check_gmail():
    """Check Gmail only if there are pending tasks."""
    vault = Path('./AI_Employee_Vault')
    pending = len(list((vault / 'Needs_Action').glob('*.md')))

    if pending < 5:  # Only check if not overwhelmed
        check_gmail()
```

## Integration with Other Tools

The scheduler can trigger:
- Webhooks
- Slack notifications
- Email reports
- Custom scripts

Example:

```python
import requests

def notify_slack(message):
    """Send notification to Slack."""
    webhook_url = os.getenv('SLACK_WEBHOOK')
    if webhook_url:
        requests.post(webhook_url, json={'text': message})

def morning_routine():
    """Morning routine with notification."""
    notify_slack("🌅 Starting morning routine")
    # ... run tasks ...
    notify_slack("✅ Morning routine complete")
```
