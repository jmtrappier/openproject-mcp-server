#!/usr/bin/env python3
"""Test runner for OpenProject MCP Server tests."""
import sys
import subprocess
import os
from pathlib import Path


def run_tests():
    """Run all tests with pytest."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Change to project root
    os.chdir(project_root)
    
    # Install test dependencies if pytest is not available
    try:
        import pytest
    except ImportError:
        print("Installing test dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"], check=True)
    
    # Run tests
    test_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "-x",  # Stop on first failure
        "tests/"  # Test directory
    ]
    
    # Add coverage if available
    try:
        import pytest_cov
        test_args.extend(["--cov=src", "--cov-report=term-missing"])
    except ImportError:
        print("pytest-cov not available, skipping coverage report")
    
    # Run the tests
    print("Running OpenProject MCP Server tests...")
    result = subprocess.run([sys.executable, "-m", "pytest"] + test_args)
    
    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
