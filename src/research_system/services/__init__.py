"""
Services package for the Research System.

This package contains service-level abstractions that provide
core functionality to the application.
"""

from research_system.services.llm_service import LLMService, default_llm_service

__all__ = [
    'LLMService',
    'default_llm_service',
]