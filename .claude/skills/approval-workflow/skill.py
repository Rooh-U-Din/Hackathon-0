#!/usr/bin/env python3
"""
Approval Workflow Skill - Human-in-the-loop approval system
"""
import sys
from pathlib import Path
from datetime import datetime
import json
import shutil

def main():
    """Main entry point for approval workflow skill."""
    print("✅ Approval Workflow Skill")
    print("=" * 50)
    print()

    # Get vault path
    vault_path = Path('./AI_Employee_Vault')
    pending = vault_path / 'Pending_Approval'
    approved = vault_path / 'Approved'
    rejected = vault_path / 'Rejected'
    done = vault_path / 'Done'
    logs_path = vault_path / 'Logs'

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', type=str, default='check',
                       choices=['check', 'approve', 'reject', 'execute'])
    parser.add_argument('--file', type=str, default=None)
    args = parser.parse_args()

    print(f"⚙️  Action: {args.action}")
    if args.file:
        print(f"   Target file: {args.file}")
    print()

    # Action: Check pending approvals
    if args.action == 'check':
        pending_files = list(pending.glob('*.md'))

        if not pending_files:
            print("✅ No pending approvals")
            return 0

        print(f"📋 {len(pending_files)} item(s) pending approval:")
        print()

        for i, file in enumerate(pending_files, 1):
            content = file.read_text(encoding='utf-8')

            # Extract metadata
            lines = content.split('\n')
            metadata = {}
            in_frontmatter = False
            for line in lines:
                if line.strip() == '---':
                    in_frontmatter = not in_frontmatter
                    continue
                if in_frontmatter and ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

            approval_type = metadata.get('type', 'unknown')
            priority = metadata.get('priority', 'medium')
            expires = metadata.get('expires', 'none')

            print(f"{i}. {file.name}")
            print(f"   Type: {approval_type}")
            print(f"   Priority: {priority}")
            print(f"   Expires: {expires}")
            print()
            print(f"   To approve: /approval-workflow --action approve --file \"{file.name}\"")
            print(f"   To reject:  /approval-workflow --action reject --file \"{file.name}\"")
            print()

        print(f"💡 Review items and move to /Approved or /Rejected folder")
        print(f"   Then run: /approval-workflow --action execute")

        return 0

    # Action: Approve specific file
    if args.action == 'approve':
        if not args.file:
            print("❌ Error: --file parameter required for approve action")
            return 1

        source = pending / args.file
        if not source.exists():
            print(f"❌ Error: File not found in Pending_Approval: {args.file}")
            return 1

        dest = approved / args.file
        shutil.move(str(source), str(dest))

        print(f"✅ Approved: {args.file}")
        print(f"   Moved to: /Approved")
        print()
        print(f"💡 Run /approval-workflow --action execute to process")

        # Log approval
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'approval_granted',
            'file': args.file,
            'approved_by': 'human'
        }

        log_file = logs_path / f'{datetime.now().strftime("%Y-%m-%d")}_approvals.json'
        logs = []
        if log_file.exists():
            logs = json.loads(log_file.read_text())
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))

        return 0

    # Action: Reject specific file
    if args.action == 'reject':
        if not args.file:
            print("❌ Error: --file parameter required for reject action")
            return 1

        source = pending / args.file
        if not source.exists():
            print(f"❌ Error: File not found in Pending_Approval: {args.file}")
            return 1

        dest = rejected / args.file
        shutil.move(str(source), str(dest))

        print(f"❌ Rejected: {args.file}")
        print(f"   Moved to: /Rejected")
        print()
        print(f"💡 Add rejection reason to the file if needed")

        # Log rejection
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'approval_rejected',
            'file': args.file,
            'rejected_by': 'human'
        }

        log_file = logs_path / f'{datetime.now().strftime("%Y-%m-%d")}_approvals.json'
        logs = []
        if log_file.exists():
            logs = json.loads(log_file.read_text())
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))

        return 0

    # Action: Execute approved items
    if args.action == 'execute':
        approved_files = list(approved.glob('*.md'))

        if not approved_files:
            print("✅ No approved items to execute")
            return 0

        print(f"🚀 Executing {len(approved_files)} approved item(s)...")
        print()

        for file in approved_files:
            print(f"📄 Processing: {file.name}")

            content = file.read_text(encoding='utf-8')

            # Extract metadata
            lines = content.split('\n')
            metadata = {}
            in_frontmatter = False
            for line in lines:
                if line.strip() == '---':
                    in_frontmatter = not in_frontmatter
                    continue
                if in_frontmatter and ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

            approval_type = metadata.get('type', 'unknown')

            print(f"   Type: {approval_type}")

            # Execute based on type
            if approval_type == 'email_send':
                print(f"   📧 Email sending requires MCP server")
                print(f"   ⚠️  Placeholder: Would send email here")

            elif approval_type == 'payment':
                print(f"   💰 Payment processing requires payment system")
                print(f"   ⚠️  Placeholder: Would process payment here")

            elif approval_type == 'linkedin_post':
                print(f"   🔗 LinkedIn posting requires Playwright")
                print(f"   💡 Use: /linkedin-poster --draft-only false")

            elif approval_type == 'file_deletion':
                print(f"   🗑️  File deletion")
                print(f"   ⚠️  Placeholder: Would delete files here")

            else:
                print(f"   ⚠️  Unknown type: {approval_type}")

            # Move to done
            dest = done / file.name
            shutil.move(str(file), str(dest))
            print(f"   ✅ Moved to /Done")
            print()

            # Log execution
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'action': 'approval_executed',
                'type': approval_type,
                'file': file.name,
                'status': 'completed'
            }

            log_file = logs_path / f'{datetime.now().strftime("%Y-%m-%d")}_approvals.json'
            logs = []
            if log_file.exists():
                logs = json.loads(log_file.read_text())
            logs.append(log_entry)
            log_file.write_text(json.dumps(logs, indent=2))

        print(f"✅ Execution complete: {len(approved_files)} item(s) processed")

        return 0

if __name__ == '__main__':
    sys.exit(main())
