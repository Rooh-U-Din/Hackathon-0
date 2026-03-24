"""Installation and setup script for AI Employee."""
import subprocess
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n[*] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"[+] {description} - Done")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] {description} - Failed")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Main setup function."""
    print("=" * 60)
    print("AI Employee - Bronze Tier Setup")
    print("=" * 60)

    # Check Python version
    print(f"\n[i] Python version: {sys.version}")
    if sys.version_info < (3, 13):
        print("[!] Warning: Python 3.13+ recommended")

    # Install dependencies
    if not run_command("pip install watchdog", "Installing watchdog"):
        return 1

    # Create .env from example if it doesn't exist
    env_file = Path('.env')
    env_example = Path('.env.example')

    if not env_file.exists() and env_example.exists():
        print("\n[*] Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print("[+] .env file created - please review and update values")

    # Verify vault structure
    vault = Path('AI_Employee_Vault')
    required_folders = ['Inbox', 'Needs_Action', 'Done', 'Plans', 'Logs',
                       'Pending_Approval', 'Approved', 'Rejected']

    print("\n[*] Verifying vault structure...")
    all_exist = True
    for folder in required_folders:
        folder_path = vault / folder
        if folder_path.exists():
            print(f"   [+] {folder}")
        else:
            print(f"   [-] {folder} - Missing!")
            all_exist = False

    if not all_exist:
        print("\n[!] Some folders are missing. Run the setup again.")
        return 1

    # Check for required files
    print("\n[*] Checking required files...")
    required_files = [
        'AI_Employee_Vault/Dashboard.md',
        'AI_Employee_Vault/Company_Handbook.md',
        'watchers/filesystem_watcher.py',
        '.claude/skills/process-tasks/SKILL.md'
    ]

    for file in required_files:
        file_path = Path(file)
        if file_path.exists():
            print(f"   [+] {file}")
        else:
            print(f"   [-] {file} - Missing!")
            all_exist = False

    print("\n" + "=" * 60)
    if all_exist:
        print("[SUCCESS] Setup Complete!")
        print("\nNext Steps:")
        print("   1. Review and update .env file")
        print("   2. Customize AI_Employee_Vault/Company_Handbook.md")
        print("   3. Start the watcher: python watchers/filesystem_watcher.py")
        print("   4. Test by dropping a file in AI_Employee_Vault/Inbox/")
        print("   5. Process tasks: cd AI_Employee_Vault && claude '/process-tasks'")
    else:
        print("[FAILED] Setup incomplete - please fix the issues above")
        return 1

    print("=" * 60)
    return 0

if __name__ == '__main__':
    sys.exit(main())
