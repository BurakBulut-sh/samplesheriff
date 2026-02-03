# Contributing to SampleSheriff

Thank you for your interest in contributing to SampleSheriff! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/your-username/samplesheriff.git
cd samplesheriff
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Code Style

We use the following tools for code quality:

- **ruff**: Linting and formatting
- **mypy**: Type checking
- **pytest**: Testing

Run all checks before committing:
```bash
ruff check src tests
ruff format --check src tests
mypy src
pytest
```

## Adding New Features

### Adding a New Validation Rule

1. Create a new rule class in `src/samplesheriff/rules/`:
```python
from samplesheriff.rules.engine import ValidationRule, ValidationContext
from samplesheriff.schema import ValidationIssue

class MyRule(ValidationRule):
    def validate(self, context, row, row_number):
        issues = []
        # Your validation logic here
        return issues
```

2. Add the rule to the CLI in `src/samplesheriff/cli.py`

3. Add tests in `tests/test_rules.py`

### Adding a New Built-in Schema

1. Create a YAML file in `src/samplesheriff/schemas/`
2. Follow the existing schema structure
3. The schema will be automatically discovered

## Testing

- All new features must include tests
- Aim for high test coverage
- Use pytest fixtures for setup

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=samplesheriff --cov-report=html

# Run specific test
pytest tests/test_schema.py::TestColumnSchema -v
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Ensure all tests pass
4. Update documentation if needed
5. Submit a pull request with a clear description

## Code Review

All submissions require review. We aim to respond to PRs within a few days.

## Reporting Issues

When reporting bugs, please include:
- SampleSheriff version (`samplesheriff --version`)
- Python version
- Sample sheet snippet that reproduces the issue
- Expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
