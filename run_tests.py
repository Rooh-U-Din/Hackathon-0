#!/usr/bin/env python3
"""
Test Runner for Personal AI Employee Test Suite

Runs all tests with proper configuration and reporting.
Provides options for:
- Running all tests
- Running specific test modules
- Verbose output
- Coverage reporting
- Parallel execution

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py test_watchers      # Run specific module
    python run_tests.py --verbose          # Verbose output
    python run_tests.py --coverage         # With coverage report
"""

import unittest
import sys
import os
from pathlib import Path
import argparse


def discover_tests(test_dir='tests', pattern='test_*.py'):
    """Discover all test modules in the tests directory."""
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / test_dir
    suite = loader.discover(start_dir, pattern=pattern)
    return suite


def run_specific_module(module_name):
    """Run a specific test module."""
    loader = unittest.TestLoader()

    # Add tests directory to path
    tests_dir = Path(__file__).parent / 'tests'
    sys.path.insert(0, str(tests_dir))

    # Load the module
    try:
        suite = loader.loadTestsFromName(module_name)
        return suite
    except Exception as e:
        print(f"Error loading module '{module_name}': {e}")
        return None


def run_tests(suite, verbosity=2):
    """Run the test suite with specified verbosity."""
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    return result


def print_summary(result):
    """Print test summary."""
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 70)

    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 70)


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description='Run Personal AI Employee tests')
    parser.add_argument('module', nargs='?', help='Specific test module to run (e.g., test_watchers)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet output')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage report')
    parser.add_argument('--failfast', action='store_true', help='Stop on first failure')

    args = parser.parse_args()

    # Determine verbosity
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    # Print header
    print("=" * 70)
    print("PERSONAL AI EMPLOYEE - TEST SUITE")
    print("=" * 70)
    print()

    # Discover or load specific tests
    if args.module:
        print(f"Running module: {args.module}")
        suite = run_specific_module(args.module)
        if suite is None:
            return 1
    else:
        print("Running all tests...")
        suite = discover_tests()

    print()

    # Run tests
    result = run_tests(suite, verbosity=verbosity)

    # Print summary
    print_summary(result)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
