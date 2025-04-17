#!/usr/bin/env python3
"""
Test runner for KoeLingo.

This module provides a centralized way to run all or specific tests
for the KoeLingo application.

Usage:
    python -m tests.run_tests          # Run all tests
    python -m tests.run_tests audio    # Run only audio tests
    python -m tests.run_tests stt      # Run only speech-to-text tests
"""

import sys
import unittest
import argparse
import importlib
import os
from tests.custom_test_runner import CustomTestRunner


def discover_tests(test_module=None):
    """
    Discover tests based on the provided module name.

    Args:
        test_module: Optional module name to run specific tests

    Returns:
        unittest.TestSuite: The test suite to run
    """
    if test_module:
        # Try to import and get the module's tests
        try:
            # Try direct module import first
            module_path = f"tests.{test_module}"
            try:
                module = importlib.import_module(module_path)
                print(f"Imported module: {module_path}")
                return unittest.defaultTestLoader.loadTestsFromModule(module)
            except ImportError:
                print(f"Module {module_path} not found directly, trying submodules...")

            # If direct import fails, try to discover tests in the module directory
            test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), test_module)
            if os.path.isdir(test_dir):
                print(f"Discovering tests in directory: {test_dir}")
                # Use pattern that matches both TestXXX and XXXTest classes
                return unittest.defaultTestLoader.discover(test_dir, pattern="test_*.py")
            else:
                print(f"Error: Test directory 'tests/{test_module}' not found.")
                sys.exit(1)

        except Exception as e:
            print(f"Error discovering tests for module '{test_module}': {e}")
            sys.exit(1)
    else:
        # Discover all tests
        start_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Discovering all tests in: {start_dir}")
        return unittest.defaultTestLoader.discover(start_dir)


def main():
    """Run the tests based on command line arguments."""
    parser = argparse.ArgumentParser(description="Run KoeLingo tests")
    parser.add_argument("module", nargs="?", help="Specific test module to run (e.g., audio, stt)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    verbosity = 2 if args.verbose else 1
    runner = CustomTestRunner(verbosity=verbosity)

    test_suite = discover_tests(args.module)
    result = runner.run(test_suite)

    # Exit with non-zero code if there were failures
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()