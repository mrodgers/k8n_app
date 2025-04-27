# Developer Documentation Guide

*Last updated: April 27, 2025*

This guide helps developers navigate the project documentation, identifying which documents are essential to review and which may contain outdated or superseded information.

## Critical Documentation

These documents represent the current state of the project and should be reviewed thoroughly by all developers:

| Document | Purpose | Priority |
|----------|---------|----------|
| [CLAUDE.md](/CLAUDE.md) | Guide for Claude Code when working with this project | High |
| [RESEARCH_SYSTEM_DEV_PLAN.md](/docs/RESEARCH_SYSTEM_DEV_PLAN.md) | Current comprehensive development plan | High |
| [architecture.md](/docs/architecture.md) | System architecture diagrams and descriptions | High |
| [api.md](/docs/api.md) | API documentation | High |
| [DATABASE.md](/docs/DATABASE.md) | Database implementation and configuration | High |
| [DATABASE_TESTING.md](/docs/DATABASE_TESTING.md) | Database testing best practices | High |
| [CODE_REVIEW_202504270919pacific.md](/docs/CODE_REVIEW_202504270919pacific.md) | Latest code review (April 27, 2025) | Medium |
| [claude_code_advice.md](/docs/claude_code_advice.md) | Code development best practices | Medium |
| [CONTRIBUTING.md](/docs/CONTRIBUTING.md) | Guidelines for project contributions | Medium |

## Secondary Documentation

These documents provide supplementary information but are not essential for day-to-day development work:

| Document | Purpose | Notes |
|----------|---------|-------|
| [docs/README.md](/docs/README.md) | Index of documentation files | Useful for navigating documentation |
| [docs/images/README.md](/docs/images/README.md) | Explains the purpose of the images directory | Reference only |

## Archived/Deprecated Documentation

These documents have been superseded by newer documentation or are no longer relevant to the current project state:

| Document | Status | Replacement |
|----------|--------|-------------|
| [docs/archive/phase_1_researcher_dev.md](/docs/archive/phase_1_researcher_dev.md) | Superseded | [RESEARCH_SYSTEM_DEV_PLAN.md](/docs/RESEARCH_SYSTEM_DEV_PLAN.md) |
| [docs/archive/researcher_dev_plan.md](/docs/archive/researcher_dev_plan.md) | Superseded | [RESEARCH_SYSTEM_DEV_PLAN.md](/docs/RESEARCH_SYSTEM_DEV_PLAN.md) |
| [docs/archive/VIBE_GUIDE_phase1.md](/docs/archive/VIBE_GUIDE_phase1.md) | Outdated | [claude_code_advice.md](/docs/claude_code_advice.md) |
| [docs/archive/SETUP_GITHUB_REPO.md](/docs/archive/SETUP_GITHUB_REPO.md) | One-time use | N/A - Repository setup complete |
| [README.md Older version](/README.md) | Updated | Now includes database and testing information |

## Documents to Be Created

The following documentation would be valuable additions to the project:

| Document | Purpose | Priority |
|----------|---------|----------|
| Kubernetes Deployment Guide | Detailed instructions for K8s deployment | Medium |
| Development Environment Setup | Local development environment configuration | Medium |

## Documentation Update Process

When updating documentation:

1. Always check if related documents need concurrent updates
2. Add a "Last updated" date at the top of the document
3. Move outdated documentation to the `/docs/archive/` directory
4. Update this guide when creating new documentation or deprecating existing documents
5. Ensure new documentation follows the established Markdown format

## Pre-Commit Documentation Verification

Before committing code changes, verify:

1. Documentation accurately reflects your changes
2. No conflicting information exists across documents
3. This guide is updated if you've added, modified, or deprecated any documentation

Remember that clear, accurate documentation is as important as quality code. Invest time in maintaining both.
