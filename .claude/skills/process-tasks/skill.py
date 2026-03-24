#!/usr/bin/env python3
"""
Process Tasks Skill - Main execution script
This script is called by Claude Code when the skill is invoked.
"""
import sys
from pathlib import Path
from datetime import datetime

def main():
    """Main entry point for the skill."""
    # Get vault path from environment or default
    vault_path = Path('./AI_Employee_Vault')

    print(f"🤖 AI Employee - Process Tasks Skill")
    print(f"📁 Vault: {vault_path}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check if vault exists
    if not vault_path.exists():
        print("❌ Error: Vault directory not found!")
        print(f"   Expected: {vault_path.absolute()}")
        sys.exit(1)

    needs_action = vault_path / 'Needs_Action'

    # Count pending tasks
    pending_files = list(needs_action.glob('*.md'))

    print(f"📋 Found {len(pending_files)} pending task(s)")
    print()

    if pending_files:
        print("Tasks to process:")
        for i, file in enumerate(pending_files, 1):
            print(f"  {i}. {file.name}")
        print()
        print("💡 Claude Code will now process these tasks...")
        print("   Reading Company_Handbook.md for rules...")
        print("   Analyzing each task...")
        print("   Creating plans or executing actions...")
    else:
        print("✅ No pending tasks. All clear!")

    print()
    print("🎯 Next: Claude Code will take over from here.")

    return 0

if __name__ == '__main__':
    sys.exit(main())
