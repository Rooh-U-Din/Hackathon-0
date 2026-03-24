#!/usr/bin/env python3
"""
Vault Synchronization System
Git-based sync between cloud and local agents with security boundaries
"""
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import json
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vault_sync')

class VaultSync:
    """Manages vault synchronization between cloud and local."""

    def __init__(self, vault_path: Path, remote_url: str, branch: str = "main"):
        self.vault_path = vault_path
        self.remote_url = remote_url
        self.branch = branch
        self.sync_log = vault_path / 'Logs' / 'vault_sync.json'

    def ensure_git_initialized(self) -> bool:
        """Ensure vault is a git repository."""
        git_dir = self.vault_path / '.git'

        if not git_dir.exists():
            logger.info("Initializing git repository...")
            try:
                subprocess.run(
                    ['git', 'init'],
                    cwd=self.vault_path,
                    check=True,
                    capture_output=True
                )

                # Set remote
                subprocess.run(
                    ['git', 'remote', 'add', 'origin', self.remote_url],
                    cwd=self.vault_path,
                    check=True,
                    capture_output=True
                )

                logger.info("Git repository initialized")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to initialize git: {e}")
                return False

        return True

    def ensure_gitignore(self) -> bool:
        """Ensure .gitignore excludes sensitive files."""
        gitignore_path = self.vault_path / '.gitignore'

        # Critical: Never sync these files
        sensitive_patterns = [
            # Secrets and credentials
            '.env',
            '*.env',
            'credentials.json',
            'token.json',
            '*.key',
            '*.pem',

            # Session files (local only)
            '*_session/',
            'whatsapp_session/',
            'linkedin_session/',
            'twitter_session/',
            'facebook_session/',
            'instagram_session/',

            # Processed IDs (environment-specific)
            '.gmail_processed_ids.json',
            '.linkedin_processed_ids.json',
            '.twitter_processed_ids.json',
            '.facebook_processed_ids.json',
            '.instagram_processed_ids.json',

            # Temporary files
            '*.tmp',
            '*.swp',
            '.DS_Store',
            'Thumbs.db',

            # PIDs and state
            'pids/',
            '*.pid',
            '.ralph_state.json',

            # Queues (environment-specific)
            'email_queue/',
            'task_queue/',
            'temp_vault/',

            # Node modules
            'node_modules/',
            'package-lock.json',

            # Python cache
            '__pycache__/',
            '*.pyc',
            '.pytest_cache/',
        ]

        try:
            existing_patterns = set()
            if gitignore_path.exists():
                existing_patterns = set(gitignore_path.read_text().strip().split('\n'))

            # Add missing patterns
            new_patterns = set(sensitive_patterns) - existing_patterns
            if new_patterns:
                with gitignore_path.open('a') as f:
                    f.write('\n# Platinum Tier - Security Boundaries\n')
                    for pattern in sorted(new_patterns):
                        f.write(f'{pattern}\n')

                logger.info(f"Added {len(new_patterns)} patterns to .gitignore")

            return True
        except Exception as e:
            logger.error(f"Failed to update .gitignore: {e}")
            return False

    def pull(self) -> bool:
        """Pull changes from remote."""
        try:
            logger.info("Pulling changes from remote...")

            # Fetch latest
            subprocess.run(
                ['git', 'fetch', 'origin', self.branch],
                cwd=self.vault_path,
                check=True,
                capture_output=True
            )

            # Check for conflicts
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.vault_path,
                check=True,
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                logger.warning("Local changes detected, stashing...")
                subprocess.run(
                    ['git', 'stash'],
                    cwd=self.vault_path,
                    check=True,
                    capture_output=True
                )

            # Pull with rebase
            subprocess.run(
                ['git', 'pull', '--rebase', 'origin', self.branch],
                cwd=self.vault_path,
                check=True,
                capture_output=True
            )

            # Pop stash if we stashed
            if result.stdout.strip():
                try:
                    subprocess.run(
                        ['git', 'stash', 'pop'],
                        cwd=self.vault_path,
                        check=True,
                        capture_output=True
                    )
                except subprocess.CalledProcessError:
                    logger.warning("Stash pop failed, manual merge may be needed")

            logger.info("Pull completed successfully")
            self._log_sync('pull', 'success')
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Pull failed: {e}")
            self._log_sync('pull', 'failure', str(e))
            return False

    def push(self, message: str = None) -> bool:
        """Push changes to remote."""
        try:
            # Check if there are changes
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.vault_path,
                check=True,
                capture_output=True,
                text=True
            )

            if not result.stdout.strip():
                logger.info("No changes to push")
                return True

            logger.info("Pushing changes to remote...")

            # Add all tracked files
            subprocess.run(
                ['git', 'add', '-u'],
                cwd=self.vault_path,
                check=True,
                capture_output=True
            )

            # Add new markdown files only
            subprocess.run(
                ['git', 'add', '*.md'],
                cwd=self.vault_path,
                check=False,  # May not find any
                capture_output=True
            )

            # Commit
            commit_message = message or f"Vault sync - {datetime.now().isoformat()}"
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=self.vault_path,
                check=True,
                capture_output=True
            )

            # Push
            subprocess.run(
                ['git', 'push', 'origin', self.branch],
                cwd=self.vault_path,
                check=True,
                capture_output=True
            )

            logger.info("Push completed successfully")
            self._log_sync('push', 'success')
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Push failed: {e}")
            self._log_sync('push', 'failure', str(e))
            return False

    def sync(self) -> bool:
        """Full sync: pull then push."""
        logger.info("Starting full vault sync...")

        if not self.ensure_git_initialized():
            return False

        if not self.ensure_gitignore():
            return False

        # Pull first to get latest changes
        if not self.pull():
            logger.error("Pull failed, aborting sync")
            return False

        # Push local changes
        if not self.push():
            logger.error("Push failed")
            return False

        logger.info("Full sync completed successfully")
        return True

    def _log_sync(self, operation: str, status: str, error: str = None):
        """Log sync operation."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'status': status,
            'error': error
        }

        try:
            logs = []
            if self.sync_log.exists():
                content = self.sync_log.read_text()
                logs = json.loads(content) if content.strip() else []

            logs.append(log_entry)

            # Keep last 1000 entries
            logs = logs[-1000:]

            self.sync_log.write_text(json.dumps(logs, indent=2))
        except Exception as e:
            logger.error(f"Failed to log sync: {e}")

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Vault Synchronization System')
    parser.add_argument('--vault', type=str, default='./AI_Employee_Vault',
                       help='Path to vault')
    parser.add_argument('--remote', type=str, required=True,
                       help='Git remote URL')
    parser.add_argument('--branch', type=str, default='main',
                       help='Git branch')
    parser.add_argument('--operation', type=str, choices=['pull', 'push', 'sync'],
                       default='sync', help='Sync operation')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously with interval')
    parser.add_argument('--interval', type=int, default=300,
                       help='Sync interval in seconds (default: 300)')

    args = parser.parse_args()

    vault_path = Path(args.vault)
    if not vault_path.exists():
        logger.error(f"Vault not found: {vault_path}")
        return 1

    sync = VaultSync(vault_path, args.remote, args.branch)

    if args.continuous:
        logger.info(f"Starting continuous sync with {args.interval}s interval")
        while True:
            try:
                if args.operation == 'pull':
                    sync.pull()
                elif args.operation == 'push':
                    sync.push()
                else:
                    sync.sync()

                time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Stopping continuous sync")
                break
            except Exception as e:
                logger.error(f"Sync error: {e}")
                time.sleep(args.interval)
    else:
        if args.operation == 'pull':
            success = sync.pull()
        elif args.operation == 'push':
            success = sync.push()
        else:
            success = sync.sync()

        return 0 if success else 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
