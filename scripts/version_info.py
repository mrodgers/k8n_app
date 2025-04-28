#!/usr/bin/env python3
"""
Simple script to display version information.
This script doesn't require importing the main package.
"""

import os
import re
import sys
import subprocess
from datetime import datetime

def get_version_from_file():
    """Read version information directly from version.py file."""
    version_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        'src', 'research_system', 'version.py'
    )
    
    if not os.path.exists(version_file):
        return {
            "version": "unknown",
            "build_number": "unknown",
            "build_date": "unknown",
            "git_revision": "unknown"
        }
    
    with open(version_file, 'r') as f:
        content = f.read()
    
    # Extract version values
    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    version = version_match.group(1) if version_match else "unknown"
    
    build_match = re.search(r'BUILD_NUMBER\s*=\s*["\']([^"\']+)["\']', content)
    build_number = build_match.group(1) if build_match else "unknown"
    
    date_match = re.search(r'BUILD_DATE\s*=\s*["\']([^"\']+)["\']', content)
    build_date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
    
    # Get git revision directly
    try:
        git_revision = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.STDOUT
        ).decode('utf-8').strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        git_revision = "unknown"
    
    return {
        "version": version,
        "build_number": build_number,
        "build_date": build_date,
        "git_revision": git_revision
    }

def main():
    """Display version information."""
    info = get_version_from_file()
    
    print(f"  Version:      {info['version']}")
    print(f"  Build Number: {info['build_number']}")
    print(f"  Build Date:   {info['build_date']}")
    print(f"  Git Revision: {info['git_revision']}")

if __name__ == "__main__":
    main()