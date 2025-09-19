#!/usr/bin/env python3
"""Build script for receipt-processor package."""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from receipt_processor._version import __version__
except ImportError:
    __version__ = "0.0.0"


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    return result


def clean_build_dirs():
    """Clean build directories."""
    print("Cleaning build directories...")
    dirs_to_clean = ["build", "dist", "*.egg-info", "htmlcov", ".coverage", "coverage.xml"]
    
    for pattern in dirs_to_clean:
        if "*" in pattern:
            # Use glob for patterns
            import glob
            for path in glob.glob(pattern):
                if os.path.exists(path):
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
        else:
            if os.path.exists(pattern):
                if os.path.isdir(pattern):
                    shutil.rmtree(pattern)
                else:
                    os.remove(pattern)


def run_tests():
    """Run the test suite."""
    print("Running tests...")
    run_command([sys.executable, "-m", "pytest", "tests/", "-v", "--cov=src/receipt_processor", "--cov-report=html"])


def run_linting():
    """Run linting checks."""
    print("Running linting...")
    run_command([sys.executable, "-m", "flake8", "src/", "tests/"])
    run_command([sys.executable, "-m", "black", "--check", "src/", "tests/"])
    run_command([sys.executable, "-m", "isort", "--check-only", "src/", "tests/"])
    run_command([sys.executable, "-m", "mypy", "src/"])


def run_security_checks():
    """Run security checks."""
    print("Running security checks...")
    run_command([sys.executable, "-m", "bandit", "-r", "src/"])
    run_command([sys.executable, "-m", "safety", "check"])


def build_package():
    """Build the package."""
    print("Building package...")
    clean_build_dirs()
    
    # Build source distribution
    run_command([sys.executable, "-m", "build", "--sdist"])
    
    # Build wheel
    run_command([sys.executable, "-m", "build", "--wheel"])
    
    print("Package built successfully!")


def install_package():
    """Install the package in development mode."""
    print("Installing package in development mode...")
    run_command([sys.executable, "-m", "pip", "install", "-e", "."])


def upload_package():
    """Upload package to PyPI."""
    print("Uploading package to PyPI...")
    
    # Check if we're in a clean state
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if result.stdout.strip():
        print("Warning: Working directory is not clean. Commit changes before uploading.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Upload cancelled.")
            return
    
    # Upload to PyPI
    run_command([sys.executable, "-m", "twine", "upload", "dist/*"])


def create_docker_image():
    """Create Docker image for the package."""
    print("Creating Docker image...")
    
    # Create Dockerfile if it doesn't exist
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        create_dockerfile()
    
    # Build Docker image
    image_tag = f"receipt-processor:{__version__}"
    run_command(["docker", "build", "-t", image_tag, "."])
    
    print(f"Docker image created: {image_tag}")


def create_dockerfile():
    """Create a Dockerfile for the package."""
    dockerfile_content = f"""FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy source code
COPY src/ ./src/
COPY README.md ./
COPY docs/ ./docs/

# Create non-root user
RUN useradd -m -u 1000 receiptprocessor
USER receiptprocessor

# Expose port (if needed)
EXPOSE 8000

# Set default command
CMD ["receipt-processor", "--help"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    print("Dockerfile created.")


def main():
    """Main build function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/build.py <command>")
        print("Commands:")
        print("  clean       - Clean build directories")
        print("  test        - Run tests")
        print("  lint        - Run linting")
        print("  security    - Run security checks")
        print("  build       - Build package")
        print("  install     - Install package in development mode")
        print("  upload      - Upload package to PyPI")
        print("  docker      - Create Docker image")
        print("  all         - Run all checks and build")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "clean":
        clean_build_dirs()
    elif command == "test":
        run_tests()
    elif command == "lint":
        run_linting()
    elif command == "security":
        run_security_checks()
    elif command == "build":
        build_package()
    elif command == "install":
        install_package()
    elif command == "upload":
        upload_package()
    elif command == "docker":
        create_docker_image()
    elif command == "all":
        print("Running full build process...")
        clean_build_dirs()
        run_linting()
        run_security_checks()
        run_tests()
        build_package()
        print("Full build process completed!")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
