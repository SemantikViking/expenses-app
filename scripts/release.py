#!/usr/bin/env python3
"""Release script for receipt-processor package."""

import os
import sys
import subprocess
import re
from pathlib import Path
from typing import List, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from receipt_processor._version import __version__
except ImportError:
    __version__ = "0.0.0"


def run_command(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    return result


def get_current_version() -> str:
    """Get current version from git tags."""
    result = run_command(["git", "describe", "--tags", "--abbrev=0"], check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    return "0.0.0"


def get_next_version(current_version: str, release_type: str) -> str:
    """Calculate next version based on release type."""
    # Parse current version
    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", current_version)
    if not match:
        raise ValueError(f"Invalid version format: {current_version}")
    
    major, minor, patch = map(int, match.groups())
    
    if release_type == "major":
        return f"{major + 1}.0.0"
    elif release_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif release_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid release type: {release_type}")


def check_working_directory_clean() -> bool:
    """Check if working directory is clean."""
    result = run_command(["git", "status", "--porcelain"], check=False)
    return result.stdout.strip() == ""


def check_tests_pass() -> bool:
    """Check if tests pass."""
    print("Running tests...")
    result = run_command(["python", "-m", "pytest", "tests/", "-v"], check=False)
    return result.returncode == 0


def check_linting_passes() -> bool:
    """Check if linting passes."""
    print("Running linting...")
    result = run_command(["python", "-m", "flake8", "src/", "tests/"], check=False)
    return result.returncode == 0


def update_changelog(version: str, release_type: str):
    """Update CHANGELOG.md with new version."""
    changelog_path = Path("CHANGELOG.md")
    
    if not changelog_path.exists():
        # Create initial changelog
        changelog_content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release

## [{version}] - {get_current_date()}

### Added
- Initial release

"""
        with open(changelog_path, "w") as f:
            f.write(changelog_content)
    else:
        # Read existing changelog
        with open(changelog_path, "r") as f:
            content = f.read()
        
        # Add new version section
        new_section = f"""## [{version}] - {get_current_date()}

### Added
- New features in this release

### Changed
- Changes in this release

### Fixed
- Bug fixes in this release

### Removed
- Removed features in this release

"""
        
        # Insert after [Unreleased] section
        content = content.replace("## [Unreleased]", f"## [Unreleased]\n\n{new_section}")
        
        with open(changelog_path, "w") as f:
            f.write(content)


def get_current_date() -> str:
    """Get current date in YYYY-MM-DD format."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


def create_git_tag(version: str, message: str):
    """Create git tag for version."""
    tag_name = f"v{version}"
    run_command(["git", "tag", "-a", tag_name, "-m", message])
    print(f"Created tag: {tag_name}")


def push_changes_and_tags():
    """Push changes and tags to remote."""
    run_command(["git", "push", "origin", "main"])
    run_command(["git", "push", "origin", "--tags"])


def build_and_upload_package():
    """Build and upload package to PyPI."""
    print("Building package...")
    run_command(["python", "scripts/build.py", "build"])
    
    print("Uploading to PyPI...")
    run_command(["python", "-m", "twine", "upload", "dist/*"])


def create_github_release(version: str, release_type: str):
    """Create GitHub release."""
    tag_name = f"v{version}"
    release_title = f"Release {version}"
    
    # Generate release notes from changelog
    changelog_path = Path("CHANGELOG.md")
    if changelog_path.exists():
        with open(changelog_path, "r") as f:
            content = f.read()
        
        # Extract release notes for this version
        pattern = rf"## \[{version}\].*?(?=## \[|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            release_notes = match.group(0).strip()
        else:
            release_notes = f"Release {version}"
    else:
        release_notes = f"Release {version}"
    
    # Create GitHub release using gh CLI
    run_command([
        "gh", "release", "create", tag_name,
        "--title", release_title,
        "--notes", release_notes
    ])


def main():
    """Main release function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/release.py <release_type> [--dry-run]")
        print("Release types: major, minor, patch")
        print("Options:")
        print("  --dry-run    - Show what would be done without making changes")
        sys.exit(1)
    
    release_type = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    
    if release_type not in ["major", "minor", "patch"]:
        print("Invalid release type. Must be: major, minor, patch")
        sys.exit(1)
    
    # Get current version
    current_version = get_current_version()
    next_version = get_next_version(current_version, release_type)
    
    print(f"Current version: {current_version}")
    print(f"Next version: {next_version}")
    print(f"Release type: {release_type}")
    print(f"Dry run: {dry_run}")
    
    if dry_run:
        print("\nDry run - would perform the following actions:")
        print(f"1. Update version to {next_version}")
        print("2. Update CHANGELOG.md")
        print("3. Run tests and linting")
        print("4. Create git tag")
        print("5. Push changes and tags")
        print("6. Build and upload package")
        print("7. Create GitHub release")
        return
    
    # Confirm release
    response = input(f"\nProceed with release {next_version}? (y/N): ")
    if response.lower() != 'y':
        print("Release cancelled.")
        return
    
    # Pre-release checks
    print("\nRunning pre-release checks...")
    
    if not check_working_directory_clean():
        print("Error: Working directory is not clean. Commit or stash changes first.")
        sys.exit(1)
    
    if not check_tests_pass():
        print("Error: Tests are failing. Fix tests before releasing.")
        sys.exit(1)
    
    if not check_linting_passes():
        print("Error: Linting is failing. Fix linting issues before releasing.")
        sys.exit(1)
    
    print("Pre-release checks passed!")
    
    # Update version in pyproject.toml
    print(f"\nUpdating version to {next_version}...")
    pyproject_path = Path("pyproject.toml")
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    # Update version (if it's not dynamic)
    if 'dynamic = ["version"]' not in content:
        content = re.sub(r'version = "[^"]*"', f'version = "{next_version}"', content)
        with open(pyproject_path, "w") as f:
            f.write(content)
    
    # Update changelog
    print("Updating CHANGELOG.md...")
    update_changelog(next_version, release_type)
    
    # Commit changes
    print("Committing changes...")
    run_command(["git", "add", "pyproject.toml", "CHANGELOG.md"])
    run_command(["git", "commit", "-m", f"Release {next_version}"])
    
    # Create tag
    print("Creating git tag...")
    create_git_tag(next_version, f"Release {next_version}")
    
    # Push changes
    print("Pushing changes...")
    push_changes_and_tags()
    
    # Build and upload package
    print("Building and uploading package...")
    build_and_upload_package()
    
    # Create GitHub release
    print("Creating GitHub release...")
    create_github_release(next_version, release_type)
    
    print(f"\nRelease {next_version} completed successfully!")
    print(f"Version {next_version} is now available on PyPI and GitHub.")


if __name__ == "__main__":
    main()
