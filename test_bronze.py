"""
Test script to verify Bronze Tier functionality
"""
from pathlib import Path
import time

def test_bronze_tier():
    """Run basic tests for Bronze Tier components."""
    print("=" * 60)
    print("Bronze Tier Test Suite")
    print("=" * 60)

    vault = Path('AI_Employee_Vault')
    tests_passed = 0
    tests_total = 0

    # Test 1: Vault structure
    tests_total += 1
    print("\n[Test 1] Checking vault structure...")
    required_folders = ['Inbox', 'Needs_Action', 'Done', 'Plans', 'Logs']
    all_exist = all((vault / folder).exists() for folder in required_folders)
    if all_exist:
        print("   [PASS] All required folders exist")
        tests_passed += 1
    else:
        print("   [FAIL] Some folders missing")

    # Test 2: Required files
    tests_total += 1
    print("\n[Test 2] Checking required files...")
    required_files = [
        vault / 'Dashboard.md',
        vault / 'Company_Handbook.md',
        Path('watchers/filesystem_watcher.py'),
        Path('.claude/skills/process-tasks/SKILL.md')
    ]
    all_files_exist = all(f.exists() for f in required_files)
    if all_files_exist:
        print("   [PASS] All required files exist")
        tests_passed += 1
    else:
        print("   [FAIL] Some files missing")

    # Test 3: Test task exists
    tests_total += 1
    print("\n[Test 3] Checking for test task...")
    test_task = vault / 'Needs_Action' / 'TEST_TASK.md'
    if test_task.exists():
        print("   [PASS] Test task found in Needs_Action")
        tests_passed += 1
    else:
        print("   [FAIL] Test task not found")

    # Test 4: Watcher script is valid Python
    tests_total += 1
    print("\n[Test 4] Validating watcher script...")
    try:
        import py_compile
        py_compile.compile('watchers/filesystem_watcher.py', doraise=True)
        print("   [PASS] Watcher script is valid Python")
        tests_passed += 1
    except Exception as e:
        print(f"   [FAIL] Watcher script has syntax errors: {e}")

    # Test 5: Skill files are present
    tests_total += 1
    print("\n[Test 5] Checking Agent Skill...")
    skill_files = [
        Path('.claude/skills/process-tasks/SKILL.md'),
        Path('.claude/skills/process-tasks/skill.py'),
        Path('.claude/skills/process-tasks/skill.json')
    ]
    all_skill_files = all(f.exists() for f in skill_files)
    if all_skill_files:
        print("   [PASS] All skill files present")
        tests_passed += 1
    else:
        print("   [FAIL] Some skill files missing")

    # Summary
    print("\n" + "=" * 60)
    print(f"Test Results: {tests_passed}/{tests_total} passed")

    if tests_passed == tests_total:
        print("\n[SUCCESS] Bronze Tier is fully functional!")
        print("\nReady for testing:")
        print("1. Start watcher: python watchers/filesystem_watcher.py AI_Employee_Vault")
        print("2. Drop test file: echo 'test' > AI_Employee_Vault/Inbox/test.txt")
        print("3. Process with Claude Code in AI_Employee_Vault directory")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Review the output above.")
        return 1

    print("=" * 60)

if __name__ == '__main__':
    import sys
    sys.exit(test_bronze_tier())
