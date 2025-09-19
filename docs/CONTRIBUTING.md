# Contributing to Receipt Processor

Thank you for your interest in contributing to the Receipt Processor project! This document provides guidelines and information for contributors.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Community Guidelines](#community-guidelines)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic knowledge of Python, Pydantic, and async programming
- Familiarity with AI/ML concepts (helpful but not required)

### Development Setup

1. **Fork the Repository:**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/your-username/receipt-processor.git
   cd receipt-processor
   ```

2. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   # Install package in development mode
   pip install -e .
   
   # Install development dependencies
   pip install -e ".[dev]"
   
   # Install pre-commit hooks
   pre-commit install
   ```

4. **Configure Environment:**
   ```bash
   # Copy example configuration
   cp .env.example .env
   
   # Edit configuration with your settings
   nano .env
   ```

5. **Run Tests:**
   ```bash
   make test
   ```

## Development Workflow

### Branch Naming

Use descriptive branch names that indicate the type of change:

- `feature/add-email-integration` - New features
- `bugfix/fix-image-validation` - Bug fixes
- `hotfix/critical-security-patch` - Critical fixes
- `docs/update-api-documentation` - Documentation updates
- `refactor/improve-error-handling` - Code refactoring
- `test/add-integration-tests` - Test additions

### Commit Messages

Follow the conventional commit format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(ai): add support for Anthropic Claude API
fix(storage): resolve JSON serialization error
docs(api): update endpoint documentation
test(integration): add email service tests
```

### Development Process

1. **Create Feature Branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes:**
   - Write code following our standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Run Quality Checks:**
   ```bash
   make lint          # Code linting
   make format        # Code formatting
   make type-check    # Type checking
   make test          # Run tests
   make security      # Security scanning
   ```

4. **Commit Changes:**
   ```bash
   git add .
   git commit -m "feat(module): add new feature"
   ```

5. **Push and Create PR:**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

## Code Standards

### Python Style

We follow PEP 8 with some project-specific modifications:

**Line Length:** 88 characters (Black default)
**Import Order:** isort configuration
**Type Hints:** Required for all functions and methods

### Code Formatting

We use automated formatting tools:

```bash
# Format code
make format

# Check formatting
make lint
```

**Tools Used:**
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

### Type Hints

All functions and methods must include type hints:

```python
from typing import List, Dict, Optional, Union
from decimal import Decimal
from datetime import datetime

def process_receipts(
    image_paths: List[str],
    config: ProcessingConfig,
    callback: Optional[callable] = None
) -> Dict[str, ReceiptData]:
    """Process multiple receipt images."""
    pass
```

### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def extract_vendor_name(text: str, confidence_threshold: float = 0.8) -> Optional[str]:
    """Extract vendor name from text with confidence threshold.
    
    Args:
        text: Input text to extract vendor name from.
        confidence_threshold: Minimum confidence score for extraction.
    
    Returns:
        Extracted vendor name or None if confidence is too low.
    
    Raises:
        ValueError: If text is empty or invalid.
    """
    pass
```

### Error Handling

Use specific exception types and provide meaningful error messages:

```python
class ProcessingError(Exception):
    """Raised when receipt processing fails."""
    pass

def process_image(image_path: str) -> ReceiptData:
    """Process receipt image."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    try:
        # Processing logic
        return result
    except Exception as e:
        raise ProcessingError(f"Failed to process image: {e}") from e
```

## Testing Guidelines

### Test Structure

**Unit Tests:** Test individual functions and methods
**Integration Tests:** Test component interactions
**End-to-End Tests:** Test complete workflows
**Performance Tests:** Test system performance

### Writing Tests

**Test Naming:**
```python
def test_function_name_with_condition_returns_expected_result():
    """Test that function behaves correctly under specific condition."""
    pass

def test_function_name_raises_exception_when_invalid_input():
    """Test that function raises appropriate exception for invalid input."""
    pass
```

**Test Organization:**
```python
class TestReceiptProcessor:
    """Test cases for ReceiptProcessor class."""
    
    def test_process_image_success(self):
        """Test successful image processing."""
        pass
    
    def test_process_image_file_not_found(self):
        """Test handling of missing image file."""
        pass
    
    def test_process_image_invalid_format(self):
        """Test handling of invalid image format."""
        pass
```

### Test Coverage

Maintain high test coverage:
- **Minimum:** 80% overall coverage
- **Critical paths:** 95% coverage
- **New code:** 100% coverage

### Running Tests

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e

# Run with coverage
make test-coverage

# Run specific test
pytest tests/test_models.py::TestReceiptData::test_creation
```

### Test Data

Use fixtures for test data:

```python
@pytest.fixture
def sample_receipt_data():
    """Sample receipt data for testing."""
    return ReceiptData(
        vendor_name="Test Restaurant",
        total_amount=Decimal("25.50"),
        confidence_score=0.95
    )

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    mock = Mock()
    mock.extract_receipt_data.return_value = sample_receipt_data()
    return mock
```

## Documentation

### Code Documentation

- Document all public functions and classes
- Include examples in docstrings
- Keep documentation up to date

### User Documentation

- Update user manual for new features
- Add troubleshooting information
- Include configuration examples

### API Documentation

- Document all API endpoints
- Include request/response examples
- Update OpenAPI schema

### README Updates

- Update installation instructions
- Add new features to feature list
- Update configuration examples

## Pull Request Process

### Before Submitting

1. **Run Quality Checks:**
   ```bash
   make lint
   make format
   make type-check
   make test
   make security
   ```

2. **Update Documentation:**
   - Update relevant documentation
   - Add examples if needed
   - Update API documentation

3. **Test Your Changes:**
   - Run all tests
   - Test manually if applicable
   - Verify no regressions

### PR Description

Use the PR template and include:

**Title:** Clear, descriptive title
**Description:** What the PR does and why
**Changes:** List of specific changes
**Testing:** How you tested the changes
**Breaking Changes:** Any breaking changes
**Screenshots:** For UI changes

**Example:**
```markdown
## Description
Add support for Anthropic Claude API as an alternative AI provider.

## Changes
- Add AnthropicProvider class
- Update AIVisionService to support multiple providers
- Add configuration options for Claude API
- Update documentation

## Testing
- Added unit tests for AnthropicProvider
- Added integration tests for Claude API
- Tested with sample receipt images
- All existing tests pass

## Breaking Changes
None - this is a backward-compatible addition.
```

### Review Process

1. **Automated Checks:** CI/CD runs quality checks
2. **Code Review:** Maintainers review code
3. **Testing:** Verify tests pass
4. **Documentation:** Check documentation updates
5. **Approval:** Maintainer approves and merges

### After Approval

- PR is merged to main branch
- CI/CD runs full test suite
- Documentation is automatically updated
- New version is tagged if applicable

## Issue Reporting

### Bug Reports

Use the bug report template:

**Title:** Brief description of the bug
**Description:** Detailed description
**Steps to Reproduce:** Clear steps
**Expected Behavior:** What should happen
**Actual Behavior:** What actually happens
**Environment:** System information
**Screenshots:** If applicable

### Feature Requests

Use the feature request template:

**Title:** Brief description of the feature
**Description:** Detailed description
**Use Case:** Why this feature is needed
**Proposed Solution:** How you think it should work
**Alternatives:** Other solutions considered

### Security Issues

For security issues, please:

1. **DO NOT** create a public issue
2. Email security@receipt-processor.com
3. Include detailed information
4. Wait for response before disclosure

## Community Guidelines

### Code of Conduct

We follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

**Be Respectful:**
- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully

**Be Collaborative:**
- Help others when possible
- Share knowledge and experience
- Work together toward common goals

**Be Professional:**
- Focus on what's best for the community
- Show empathy towards other community members
- Be patient with newcomers

### Getting Help

**Documentation:** Check existing documentation first
**Issues:** Search existing issues before creating new ones
**Discussions:** Use GitHub Discussions for questions
**Discord:** Join our Discord server for real-time help

### Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation
- Community highlights

## Development Tools

### Recommended IDE

**VS Code** with extensions:
- Python
- Pylance
- Black Formatter
- isort
- GitLens

### Useful Commands

```bash
# Development
make dev              # Start development server
make dev-watch        # Start with hot reload

# Quality
make lint             # Run linting
make format           # Format code
make type-check       # Type checking
make security         # Security scanning

# Testing
make test             # Run all tests
make test-coverage    # Run with coverage
make test-watch       # Run tests in watch mode

# Documentation
make docs             # Generate documentation
make docs-serve       # Serve documentation locally

# Maintenance
make clean            # Clean build artifacts
make update-deps      # Update dependencies
make check-updates    # Check for updates
```

### Git Hooks

Pre-commit hooks run automatically:
- Code formatting (Black)
- Import sorting (isort)
- Linting (flake8)
- Type checking (mypy)
- Security scanning (bandit)

### CI/CD

GitHub Actions runs on every PR:
- Quality checks
- Test suite
- Security scanning
- Documentation generation
- Performance tests

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):
- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes (backward compatible)

### Release Steps

1. **Update Version:** Update version in pyproject.toml
2. **Update Changelog:** Add release notes
3. **Create Tag:** Create git tag
4. **Build Package:** Build distribution packages
5. **Publish:** Publish to PyPI
6. **Announce:** Announce release

### Release Branches

- **main:** Latest stable release
- **develop:** Development branch
- **release/x.x.x:** Release preparation

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Questions?

If you have questions about contributing:

1. Check this documentation
2. Search existing issues
3. Create a new issue
4. Join our Discord server
5. Contact maintainers

Thank you for contributing to Receipt Processor! 🎉
