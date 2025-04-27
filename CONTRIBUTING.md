# Contributing to K8s Python App

Thank you for your interest in contributing to the K8s Python App project! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up development environment (see the README.md)
4. Create a new branch for your work

## Development Workflow

1. Create a branch for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
   or
   ```bash
   git checkout -b fix/your-bugfix-name
   ```

2. Make your changes with clear commit messages:
   ```bash
   git commit -m "Description of the changes"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a Pull Request from your fork to the main repository

## Pull Request Guidelines

- Ensure your code passes all tests
- Add new tests for new functionality
- Update documentation as needed
- Describe your changes in the PR description
- Link to any related issues

## Testing

Run tests before submitting a PR:

```bash
pytest tests/
```

## Coding Standards

- Follow PEP 8 style guidelines for Python code
- Use meaningful variable and function names
- Add docstrings for functions and classes
- Keep functions small and focused

## Documentation

Update documentation for any user-facing changes, including:
- README.md updates
- Inline code comments
- Docstrings

## Versioning

We follow [Semantic Versioning](https://semver.org/) for version numbers:
- MAJOR version for incompatible API changes
- MINOR version for backward-compatible functionality
- PATCH version for backward-compatible bug fixes

## License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers the project.
