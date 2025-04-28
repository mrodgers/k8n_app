"""
Version information for the Research System.

This module maintains version information including:
- Semantic version (major.minor.patch)
- Build number (incremented with each release)
- Build date
- Git commit hash (if available)

This information is used for:
- API responses
- Logging
- Health checks
- Ensuring correct installation
"""

import os
import datetime
import subprocess
from typing import Dict, Any, Optional

# Semantic version - manually updated for releases
__version__ = "1.0.0"

# Build number - incremented with each release or significant update
# This should be updated using a CI/CD pipeline or release script
BUILD_NUMBER = "001"

# Build date - automatically set to current date when package is built
BUILD_DATE = datetime.datetime.now().strftime("%Y-%m-%d")

def get_git_revision() -> Optional[str]:
    """Get the current git revision hash, if available."""
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            stderr=subprocess.STDOUT
        ).decode('utf-8').strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return None

# Git commit hash - automatically determined if in a git repository
GIT_REVISION = get_git_revision()

def get_version_info() -> Dict[str, Any]:
    """
    Get complete version information as a dictionary.
    
    Returns:
        Dict[str, Any]: Version information including semantic version,
                      build number, build date, and git revision
    """
    return {
        "version": __version__,
        "build_number": BUILD_NUMBER,
        "build_date": BUILD_DATE,
        "git_revision": GIT_REVISION,
    }

def get_version_string() -> str:
    """
    Get version as a formatted string for display.
    
    Returns:
        str: Formatted version string (e.g., "1.0.0 (build 001)")
    """
    return f"{__version__} (build {BUILD_NUMBER})"

# Additional utilities for version comparison can be added here
def is_compatible_with(required_version: str) -> bool:
    """
    Check if the current version is compatible with the required version.
    
    Args:
        required_version: Minimum required version in format "major.minor.patch"
        
    Returns:
        bool: True if current version is compatible, False otherwise
    """
    current = [int(x) for x in __version__.split('.')]
    required = [int(x) for x in required_version.split('.')]
    
    # Check major version match first (breaking changes)
    if current[0] != required[0]:
        return current[0] > required[0]
    
    # Check minor version (new features)
    if current[1] != required[1]:
        return current[1] > required[1]
    
    # Check patch version (bug fixes)
    return current[2] >= required[2]