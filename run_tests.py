#!/usr/bin/env python3
"""
Test Runner for Receipt Processor

This script provides a comprehensive test runner with various options
for running different types of tests and generating reports.
"""

import argparse
import sys
import subprocess
import os
from pathlib import Path
from typing import List, Optional

def run_command(cmd: List[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False

def run_unit_tests(verbose: bool = False, coverage: bool = True) -> bool:
    """Run unit tests."""
    cmd = ["python", "-m", "pytest", "tests/test_unit_*.py"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=src/receipt_processor",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    return run_command(cmd, "Unit Tests")

def run_integration_tests(verbose: bool = False, coverage: bool = True) -> bool:
    """Run integration tests."""
    cmd = ["python", "-m", "pytest", "tests/test_integration_*.py"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=src/receipt_processor",
            "--cov-report=term-missing"
        ])
    
    return run_command(cmd, "Integration Tests")

def run_all_tests(verbose: bool = False, coverage: bool = True) -> bool:
    """Run all tests."""
    cmd = ["python", "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=src/receipt_processor",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml"
        ])
    
    return run_command(cmd, "All Tests")

def run_specific_tests(test_pattern: str, verbose: bool = False) -> bool:
    """Run specific tests matching a pattern."""
    cmd = ["python", "-m", "pytest", test_pattern]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"Tests matching '{test_pattern}'")

def run_tests_by_marker(marker: str, verbose: bool = False) -> bool:
    """Run tests by marker."""
    cmd = ["python", "-m", "pytest", "-m", marker]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"Tests with marker '{marker}'")

def run_performance_tests(verbose: bool = False) -> bool:
    """Run performance tests."""
    cmd = ["python", "-m", "pytest", "tests/test_performance_*.py", "-m", "performance"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Performance Tests")

def run_linting() -> bool:
    """Run code linting."""
    success = True
    
    # Run flake8
    if not run_command(["python", "-m", "flake8", "src/", "tests/"], "Flake8 Linting"):
        success = False
    
    # Run black check
    if not run_command(["python", "-m", "black", "--check", "src/", "tests/"], "Black Format Check"):
        success = False
    
    # Run mypy
    if not run_command(["python", "-m", "mypy", "src/"], "MyPy Type Checking"):
        success = False
    
    return success

def run_security_scan() -> bool:
    """Run security scanning."""
    success = True
    
    # Run bandit for security issues
    if not run_command(["python", "-m", "bandit", "-r", "src/"], "Bandit Security Scan"):
        success = False
    
    # Run safety for known vulnerabilities
    if not run_command(["python", "-m", "safety", "check"], "Safety Vulnerability Check"):
        success = False
    
    return success

def generate_coverage_report() -> bool:
    """Generate comprehensive coverage report."""
    cmd = [
        "python", "-m", "coverage", "combine",
        "&&", "python", "-m", "coverage", "html",
        "&&", "python", "-m", "coverage", "xml"
    ]
    
    return run_command(cmd, "Coverage Report Generation")

def clean_test_artifacts() -> bool:
    """Clean up test artifacts."""
    artifacts = [
        "htmlcov/",
        "coverage.xml",
        "test-results.xml",
        ".coverage",
        ".pytest_cache/",
        "__pycache__/",
        "**/__pycache__/",
        "*.pyc",
        "**/*.pyc"
    ]
    
    success = True
    for artifact in artifacts:
        try:
            if os.path.exists(artifact):
                if os.path.isdir(artifact):
                    import shutil
                    shutil.rmtree(artifact)
                else:
                    os.remove(artifact)
                print(f"✅ Cleaned {artifact}")
        except Exception as e:
            print(f"❌ Failed to clean {artifact}: {e}")
            success = False
    
    return success

def install_test_dependencies() -> bool:
    """Install test dependencies."""
    dependencies = [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "pytest-timeout>=2.1.0",
        "coverage>=7.0.0",
        "flake8>=6.0.0",
        "black>=23.0.0",
        "mypy>=1.0.0",
        "bandit>=1.7.0",
        "safety>=2.0.0"
    ]
    
    cmd = ["pip", "install"] + dependencies
    return run_command(cmd, "Test Dependencies Installation")

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Receipt Processor Test Runner")
    
    # Test type options
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--pattern", type=str, help="Run tests matching pattern")
    parser.add_argument("--marker", type=str, help="Run tests with specific marker")
    
    # Quality assurance options
    parser.add_argument("--lint", action="store_true", help="Run code linting")
    parser.add_argument("--security", action="store_true", help="Run security scanning")
    parser.add_argument("--quality", action="store_true", help="Run all quality checks")
    
    # Test execution options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--clean", action="store_true", help="Clean test artifacts")
    parser.add_argument("--install-deps", action="store_true", help="Install test dependencies")
    
    # Report options
    parser.add_argument("--coverage-report", action="store_true", help="Generate coverage report")
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    success = True
    
    # Install dependencies if requested
    if args.install_deps:
        if not install_test_dependencies():
            print("❌ Failed to install test dependencies")
            return 1
    
    # Clean artifacts if requested
    if args.clean:
        if not clean_test_artifacts():
            print("❌ Failed to clean test artifacts")
            return 1
    
    # Run tests based on arguments
    if args.unit:
        if not run_unit_tests(args.verbose, not args.no_coverage):
            success = False
    
    if args.integration:
        if not run_integration_tests(args.verbose, not args.no_coverage):
            success = False
    
    if args.performance:
        if not run_performance_tests(args.verbose):
            success = False
    
    if args.pattern:
        if not run_specific_tests(args.pattern, args.verbose):
            success = False
    
    if args.marker:
        if not run_tests_by_marker(args.marker, args.verbose):
            success = False
    
    if args.all:
        if not run_all_tests(args.verbose, not args.no_coverage):
            success = False
    
    # Run quality checks
    if args.lint:
        if not run_linting():
            success = False
    
    if args.security:
        if not run_security_scan():
            success = False
    
    if args.quality:
        if not run_linting():
            success = False
        if not run_security_scan():
            success = False
    
    # Generate coverage report if requested
    if args.coverage_report:
        if not generate_coverage_report():
            success = False
    
    # If no specific tests were run, run all tests by default
    if not any([args.unit, args.integration, args.all, args.performance, 
                args.pattern, args.marker, args.lint, args.security, args.quality]):
        if not run_all_tests(args.verbose, not args.no_coverage):
            success = False
    
    # Print summary
    print(f"\n{'='*60}")
    if success:
        print("✅ All tests and checks completed successfully!")
        return 0
    else:
        print("❌ Some tests or checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
