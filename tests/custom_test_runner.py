"""
Custom test runner for KoeLingo.

This module provides a test runner that formats output similar to a gtest-style format,
showing running tests with colored status indicators.
"""

import sys
import time
import unittest
from termcolor import colored


class CustomTestResult(unittest.TestResult):
    """Custom test result implementation to match the desired format."""

    def __init__(self, verbose=0):
        super().__init__()
        self.verbose = verbose
        self.current_suite = None
        self.suite_start_time = None
        self.total_start_time = None
        self.test_start_time = None
        self.suites_run = 0
        self.suite_test_count = 0
        self.total_tests_run = 0
        self.test_times = {}  # Store test execution times

    def startTestRun(self):
        """Called when the test run starts."""
        super().startTestRun()
        self.total_start_time = time.time()
        print("Preparing to run tests...")
        print("Required tests already built. Skipping build step.")
        print("Running tests...")

    def startTest(self, test):
        """Called when a test starts."""
        super().startTest(test)

        # For verbose mode, print test docstring
        if self.verbose > 1:
            docstring = test._testMethodDoc or "No test docstring"
            print(f"{test.id()} ({docstring})")

        suite_name = type(test).__name__

        # If this is a new test suite, print suite information
        if self.current_suite != suite_name:
            if self.current_suite is not None:
                suite_time = time.time() - self.suite_start_time
                print(f"{colored('[----------]', 'green')} {self.suite_test_count} tests from {self.current_suite} ({int(suite_time * 1000)} ms total)")
                print("")

            self.current_suite = suite_name
            self.suite_start_time = time.time()
            self.suites_run += 1
            self.suite_test_count = 0

            # Count tests in this suite
            count = 0
            for method_name in dir(test):
                if method_name.startswith('test'):
                    count += 1

            print(f"{colored('[==========]', 'green')} Running {count} tests from {suite_name}.")
            print(f"{colored('[----------]', 'green')} Global test environment set-up.")
            print(f"{colored('[----------]', 'green')} {count} tests from {suite_name}")

        # Print test start information
        test_name = test._testMethodName
        print(f"{colored('[ RUN      ]', 'green')} {suite_name}.{test_name}")
        self.test_start_time = time.time()
        self.suite_test_count += 1
        self.total_tests_run += 1

    def addSuccess(self, test):
        """Called when a test succeeds."""
        super().addSuccess(test)
        test_time = time.time() - self.test_start_time
        self.test_times[test.id()] = test_time
        # For verbose mode, print a simple "ok"
        if self.verbose > 1:
            print("ok")
        msg = f"{colored('[       OK ]', 'green')} {type(test).__name__}.{test._testMethodName} ({int(test_time * 1000)} ms)"
        print(msg)

    def addError(self, test, err):
        """Called when a test raises an unexpected exception."""
        super().addError(test, err)
        test_time = time.time() - self.test_start_time
        self.test_times[test.id()] = test_time
        if self.verbose > 1:
            print("ERROR")
        msg = f"{colored('[     ERROR]', 'red')} {type(test).__name__}.{test._testMethodName} ({int(test_time * 1000)} ms)"
        print(msg)

    def addFailure(self, test, err):
        """Called when a test fails."""
        super().addFailure(test, err)
        test_time = time.time() - self.test_start_time
        self.test_times[test.id()] = test_time
        if self.verbose > 1:
            print("FAIL")
        msg = f"{colored('[   FAILED ]', 'red')} {type(test).__name__}.{test._testMethodName} ({int(test_time * 1000)} ms)"
        print(msg)

    def addSkip(self, test, reason):
        """Called when a test is skipped."""
        super().addSkip(test, reason)
        test_time = time.time() - self.test_start_time
        self.test_times[test.id()] = test_time
        if self.verbose > 1:
            print(f"skipped {reason!r}")
        msg = f"{colored('[  SKIPPED ]', 'yellow')} {type(test).__name__}.{test._testMethodName} ({int(test_time * 1000)} ms) {reason}"
        print(msg)

    def stopTestRun(self):
        """Called when the test run completes."""
        super().stopTestRun()

        if self.current_suite is not None:
            suite_time = time.time() - self.suite_start_time
            print(f"{colored('[----------]', 'green')} {self.suite_test_count} tests from {self.current_suite} ({int(suite_time * 1000)} ms total)")
            print("")

        total_time = time.time() - self.total_start_time
        print(f"{colored('[----------]', 'green')} Global test environment tear-down")
        print(f"{colored('[==========]', 'green')} {self.total_tests_run} tests from {self.suites_run} test suite ran. ({int(total_time * 1000)} ms total)")

        if self.failures or self.errors:
            result_color = 'red'
            result_text = 'FAILED'
        else:
            result_color = 'green'
            result_text = 'PASSED'

        print(f"{colored(f'[ {result_text}  ]', result_color)} {self.total_tests_run} tests.")

        if self.failures:
            print(f"{colored('[  FAILED  ]', 'red')} {len(self.failures)} tests, listed below:")
            for test, _ in self.failures:
                print(f"{colored('[  FAILED  ]', 'red')} {type(test).__name__}.{test._testMethodName}")

        if self.errors:
            print(f"{colored('[  ERROR   ]', 'red')} {len(self.errors)} tests, listed below:")
            for test, _ in self.errors:
                print(f"{colored('[  ERROR   ]', 'red')} {type(test).__name__}.{test._testMethodName}")

        # Print unittest-style summary
        if self.verbose > 0:
            print("\n----------------------------------------------------------------------")
            print(f"Ran {self.testsRun} tests in {total_time:.3f}s")

            if self.wasSuccessful():
                print("\nOK")
            else:
                print("\nFAILED", end="")
                if self.errors:
                    print(" (errors={0})".format(len(self.errors)), end="")
                if self.failures:
                    print(" (failures={0})".format(len(self.failures)), end="")
                print()


class CustomTestRunner:
    """Custom test runner that uses our custom test result class."""

    def __init__(self, verbosity=1, failfast=False, buffer=False):
        self.verbosity = verbosity
        self.failfast = failfast
        self.buffer = buffer

    def run(self, test):
        """Run the given test case or test suite."""
        # Create a test result object
        result = CustomTestResult(verbose=self.verbosity)
        result.failfast = self.failfast

        # Start the test run
        result.startTestRun()

        # Run the tests
        startTime = time.time()
        try:
            test(result)
        finally:
            stopTime = time.time()
            result.stopTestRun()

        timeTaken = stopTime - startTime

        return result