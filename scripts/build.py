#!/usr/bin/env python3
"""
Build script for the Research System.

This script:
1. Increments the build number in version.py
2. Updates build date
3. Captures git revision
4. Optionally creates a new release

Usage:
    python scripts/build.py [--major|--minor|--patch] [--no-git]
    
Options:
    --major      Increment major version (breaking changes)
    --minor      Increment minor version (new features)
    --patch      Increment patch version (bug fixes)
    --no-git     Skip git operations
    --release    Create a release tag
"""

import os
import re
import sys
import subprocess
import datetime
import argparse
from typing import Tuple, Optional

# Path to version.py file
VERSION_FILE = os.path.join('src', 'research_system', 'version.py')

def read_version_file() -> str:
    """Read the contents of the version file."""
    with open(VERSION_FILE, 'r') as f:
        return f.read()

def write_version_file(content: str) -> None:
    """Write the updated contents to the version file."""
    with open(VERSION_FILE, 'w') as f:
        f.write(content)

def get_current_version() -> Tuple[str, str]:
    """
    Extract the current version and build number from version.py.
    
    Returns:
        Tuple[str, str]: (version, build_number)
    """
    content = read_version_file()
    
    # Extract version
    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not version_match:
        raise ValueError("Could not find __version__ in version.py")
    version = version_match.group(1)
    
    # Extract build number
    build_match = re.search(r'BUILD_NUMBER\s*=\s*["\']([^"\']+)["\']', content)
    if not build_match:
        raise ValueError("Could not find BUILD_NUMBER in version.py")
    build_number = build_match.group(1)
    
    return version, build_number

def increment_version(version: str, increment_type: str) -> str:
    """
    Increment the version number based on the specified type.
    
    Args:
        version: Current version in format "major.minor.patch"
        increment_type: Type of increment ('major', 'minor', or 'patch')
    
    Returns:
        str: New version number
    """
    major, minor, patch = map(int, version.split('.'))
    
    if increment_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif increment_type == 'minor':
        minor += 1
        patch = 0
    elif increment_type == 'patch':
        patch += 1
    
    return f"{major}.{minor}.{patch}"

def increment_build_number(build_number: str) -> str:
    """
    Increment the build number.
    
    Args:
        build_number: Current build number as a string (e.g., "001")
    
    Returns:
        str: New build number
    """
    # Determine format (number of digits)
    num_digits = len(build_number)
    
    # Convert to integer, increment, and format back to string
    new_build = int(build_number) + 1
    return f"{new_build:0{num_digits}d}"

def update_version_file(new_version: Optional[str] = None, new_build: Optional[str] = None) -> Tuple[str, str]:
    """
    Update the version.py file with new version and build number.
    
    Args:
        new_version: New version number (optional)
        new_build: New build number (optional)
    
    Returns:
        Tuple[str, str]: (new_version, new_build)
    """
    content = read_version_file()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Get current version and build number
    current_version, current_build = get_current_version()
    
    # Use provided values or keep current ones
    new_version = new_version or current_version
    new_build = new_build or current_build
    
    # Update version
    if new_version != current_version:
        content = re.sub(
            r'__version__\s*=\s*["\']([^"\']+)["\']',
            f'__version__ = "{new_version}"',
            content
        )
    
    # Update build number
    if new_build != current_build:
        content = re.sub(
            r'BUILD_NUMBER\s*=\s*["\']([^"\']+)["\']',
            f'BUILD_NUMBER = "{new_build}"',
            content
        )
    
    # Update build date
    content = re.sub(
        r'BUILD_DATE\s*=\s*["\']([^"\']+)["\']',
        f'BUILD_DATE = "{today}"',
        content
    )
    
    # Write updated content back to the file
    write_version_file(content)
    
    return new_version, new_build

def create_git_tag(version: str, build: str) -> None:
    """
    Create a git tag for the release.
    
    Args:
        version: Version number
        build: Build number
    """
    tag_name = f"v{version}-{build}"
    tag_message = f"Release {version} (Build {build})"
    
    subprocess.run(['git', 'tag', '-a', tag_name, '-m', tag_message])
    print(f"Created git tag: {tag_name}")
    print("Don't forget to push the tag: git push origin --tags")

def main():
    parser = argparse.ArgumentParser(description="Research System build script")
    version_group = parser.add_mutually_exclusive_group()
    version_group.add_argument('--major', action='store_true', help='Increment major version')
    version_group.add_argument('--minor', action='store_true', help='Increment minor version')
    version_group.add_argument('--patch', action='store_true', help='Increment patch version')
    parser.add_argument('--no-git', action='store_true', help='Skip git operations')
    parser.add_argument('--release', action='store_true', help='Create a release tag')
    
    args = parser.parse_args()
    
    # Get current version and build number
    current_version, current_build = get_current_version()
    
    # Determine new version if needed
    new_version = current_version
    if args.major:
        new_version = increment_version(current_version, 'major')
    elif args.minor:
        new_version = increment_version(current_version, 'minor')
    elif args.patch:
        new_version = increment_version(current_version, 'patch')
    
    # Always increment build number
    new_build = increment_build_number(current_build)
    
    # Update version file
    updated_version, updated_build = update_version_file(new_version, new_build)
    
    # Print results
    print(f"Updated version: {updated_version} (build {updated_build})")
    
    # Create git tag if requested
    if args.release and not args.no_git:
        create_git_tag(updated_version, updated_build)

if __name__ == '__main__':
    main()