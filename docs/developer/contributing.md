# Contributing

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Set up development environment (see [Building](building.md))
4. Make your changes
5. Run tests: `pytest tests/`
6. Run linters: `flake8` and `black --check`
7. Commit and push
8. Open a Pull Request

## Code Style

- Python: follow PEP 8, use `black` formatter (line length 120)
- Use type hints throughout
- Write docstrings for all public classes and functions
- All new features need tests

## Testing Requirements

- Unit tests for all new functionality in `tests/unit/`
- Integration tests for storage/manager interactions in `tests/integration/`
- Security tests for any input validation in `tests/security/`
- Maintain >80% test coverage

## Security Guidelines

- Never use `shell=True` with user-supplied input
- Always validate activity names with `storage.validate_name()`
- Use atomic writes for all file operations
- Keep config directory permissions at 0o700

## Commit Messages

Use conventional commits:
```
feat: add support for activity icons
fix: resolve atomic write race condition
docs: update installation instructions
test: add security tests for path traversal
```

## Reporting Issues

Use [GitHub Issues](https://github.com/gortazar/gnome-activities/issues).
Include:
- OS and GNOME version
- Python version
- Steps to reproduce
- Expected vs actual behavior
