#!/usr/bin/env python3
"""
Watchdog Process - Health Monitor
Monitors and restarts critical processes automatically
"""
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime
import json
import psutil
import signal
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('watchdog')

class ProcessWatchdog:
    """Monitors and restarts critical processes."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.logs_path = vault_path / 'Logs'
        self.pid_dir = Path('./pids')

        # Ensure directories exist
        self.logs_path.mkdir(exist_ok=True)
        self.pid_dir.mkdir(exist_ok=True)

        # Define critical processes to monitor
        self.processes = {
            'gmail_watcher': {
                'command': 'python .claude/skills/gmail-watcher/skill.py',
                'restart_on_failure': True,
                'max_restarts': 5,
                'restart_delay': 60
            },
            'linkedin_watcher': {
                'command': 'python .claude/skills/linkedin-watcher/skill.py',
                'restart_on_failure': True,
                'max_restarts': 5,
                'restart_delay': 60
            },
            'filesystem_watcher': {
                'command': f'python watchers/filesystem_watcher.py {vault_path}',
                'restart_on_failure': True,
                'max_restarts': 10,
                'restart_delay': 30
            }
        }

        # Track restart counts
        self.restart_counts = {name: 0 for name in self.processes.keys()}
        self.last_restart_time = {name: None for name in self.processes.keys()}

    def get_pid_file(self, process_name: str) -> Path:
        """Get PID file path for a process."""
        return self.pid_dir / f"{process_name}.pid"

    def is_process_running(self, process_name: str) -> bool:
        """Check if a process is running."""
        pid_file = self.get_pid_file(process_name)

        if not pid_file.exists():
            return False

        try:
            pid = int(pid_file.read_text().strip())

            # Check if process exists
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                # Verify it's our process (not a reused PID)
                if proc.is_running():
                    return True

            # PID file exists but process is dead
            pid_file.unlink()
            return False

        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def start_process(self, process_name: str) -> bool:
        """Start a process."""
        config = self.processes[process_name]
        command = config['command']

        try:
            logger.info(f"Starting {process_name}...")

            # Start process in background
            proc = subprocess.Popen(
                command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            # Save PID
            pid_file = self.get_pid_file(process_name)
            pid_file.write_text(str(proc.pid))

            logger.info(f"{process_name} started with PID {proc.pid}")

            # Log restart
            self.log_event({
                'timestamp': datetime.now().isoformat(),
                'event': 'process_started',
                'process': process_name,
                'pid': proc.pid
            })

            return True

        except Exception as e:
            logger.error(f"Failed to start {process_name}: {e}")
            return False

    def stop_process(self, process_name: str) -> bool:
        """Stop a process gracefully."""
        pid_file = self.get_pid_file(process_name)

        if not pid_file.exists():
            return True

        try:
            pid = int(pid_file.read_text().strip())

            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)

                # Try graceful shutdown first
                proc.terminate()

                # Wait up to 10 seconds
                try:
                    proc.wait(timeout=10)
                except psutil.TimeoutExpired:
                    # Force kill if still running
                    proc.kill()
                    proc.wait()

                logger.info(f"Stopped {process_name} (PID {pid})")

            pid_file.unlink()
            return True

        except Exception as e:
            logger.error(f"Failed to stop {process_name}: {e}")
            return False

    def restart_process(self, process_name: str) -> bool:
        """Restart a process."""
        config = self.processes[process_name]

        # Check restart limits
        if self.restart_counts[process_name] >= config['max_restarts']:
            logger.error(f"{process_name} exceeded max restarts ({config['max_restarts']})")
            self.notify_human(f"{process_name} failed repeatedly and needs attention")
            return False

        # Check restart delay
        last_restart = self.last_restart_time[process_name]
        if last_restart:
            elapsed = (datetime.now() - last_restart).total_seconds()
            if elapsed < config['restart_delay']:
                logger.info(f"Waiting {config['restart_delay'] - elapsed:.0f}s before restarting {process_name}")
                return False

        # Stop and start
        self.stop_process(process_name)
        time.sleep(2)

        if self.start_process(process_name):
            self.restart_counts[process_name] += 1
            self.last_restart_time[process_name] = datetime.now()
            return True

        return False

    def check_and_restart(self):
        """Check all processes and restart if needed."""
        for process_name, config in self.processes.items():
            if not self.is_process_running(process_name):
                logger.warning(f"{process_name} is not running")

                if config['restart_on_failure']:
                    logger.info(f"Attempting to restart {process_name}...")
                    self.restart_process(process_name)
                else:
                    self.notify_human(f"{process_name} is down and auto-restart is disabled")

    def notify_human(self, message: str):
        """Notify human of critical issues."""
        logger.critical(f"HUMAN ATTENTION REQUIRED: {message}")

        # Create alert file
        alert_file = self.vault_path / 'Needs_Action' / f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        content = f"""---
type: system_alert
priority: critical
timestamp: {datetime.now().isoformat()}
status: new
---

# System Alert

**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Issue

{message}

## Action Required

Please investigate and resolve this issue immediately.

---
*Generated by Watchdog Process Monitor*
"""

        try:
            alert_file.write_text(content, encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to create alert file: {e}")

    def log_event(self, event: dict):
        """Log watchdog events."""
        log_file = self.logs_path / f"{datetime.now().strftime('%Y-%m-%d')}_watchdog.json"

        try:
            if log_file.exists():
                content = log_file.read_text(encoding='utf-8')
                logs = json.loads(content) if content.strip() else []
            else:
                logs = []

            logs.append(event)
            log_file.write_text(json.dumps(logs, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to log event: {e}")

    def run(self, check_interval: int = 60):
        """Run the watchdog continuously."""
        logger.info("Watchdog process monitor starting...")
        logger.info(f"Monitoring {len(self.processes)} processes")
        logger.info(f"Check interval: {check_interval} seconds")

        # Handle shutdown signals
        def signal_handler(signum, frame):
            logger.info("Shutdown signal received, stopping all processes...")
            for process_name in self.processes.keys():
                self.stop_process(process_name)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Main monitoring loop
        while True:
            try:
                self.check_and_restart()
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Watchdog error: {e}", exc_info=True)
                time.sleep(check_interval)

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Watchdog Process Monitor')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault',
                       help='Path to Obsidian vault')
    parser.add_argument('--interval', type=int, default=60,
                       help='Check interval in seconds')

    args = parser.parse_args()

    vault_path = Path(args.vault)
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return 1

    watchdog = ProcessWatchdog(vault_path)
    watchdog.run(args.interval)

if __name__ == '__main__':
    sys.exit(main())
