# Contributing Guide

Thank you for your interest in contributing to the Self-Optimizing Instruction Library! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Documentation](#documentation)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Our Standards

**Positive behaviors include:**
- Being respectful and inclusive
- Providing constructive feedback
- Focusing on what's best for the community
- Showing empathy toward others

**Unacceptable behaviors include:**
- Harassment or discrimination
- Trolling or insulting comments
- Personal or political attacks
- Publishing others' private information

### Enforcement

Report violations to the project maintainers. All reports will be reviewed confidentially.

## Getting Started

### Ways to Contribute

1. **Report Bugs** - Help identify issues
2. **Suggest Features** - Propose new functionality
3. **Improve Documentation** - Fix typos, add examples
4. **Write Code** - Fix bugs or implement features
5. **Review Pull Requests** - Provide feedback on contributions

### First Time Contributors

Look for issues labeled:
- `good first issue` - Great for newcomers
- `help wanted` - Community help needed
- `documentation` - Documentation improvements

## Development Setup

### 1. Fork the Repository

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/autonomai.git
cd autonomai
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
# Install all dependencies including dev dependencies
pip install -r requirements.txt
pip install -r requirements/dev.txt

# Install in development mode
pip install -e .
```

### 4. Set Up Pre-commit Hooks (Optional)

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

### 5. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

### 6. Run Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=src tests/
```

## Making Changes

### 1. Create a Branch

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Or bug fix branch
git checkout -b fix/bug-description
```

**Branch Naming:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes

### 2. Make Your Changes

```python
# Write clean, well-documented code
def my_new_feature(param: str) -> dict:
    """
    Brief description of what this does.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
        
    Example:
        >>> my_new_feature("test")
        {'result': 'success'}
    """
    # Implementation
    return {'result': 'success'}
```

### 3. Add Tests

```python
# tests/test_my_feature.py
import pytest
from src import my_new_feature

def test_my_new_feature():
    """Test my new feature"""
    result = my_new_feature("test")
    assert result['result'] == 'success'

def test_my_new_feature_edge_case():
    """Test edge case"""
    with pytest.raises(ValueError):
        my_new_feature("")
```

### 4. Update Documentation

```markdown
# Add to relevant documentation
## New Feature

Description of your new feature.

### Usage

```python
from src import my_new_feature

result = my_new_feature("example")
```
```

### 5. Test Your Changes

```bash
# Run tests
python -m pytest tests/

# Run linting
flake8 src/
black src/ --check
mypy src/

# Test manually
python examples/test_my_feature.py
```

## Testing

### Running Tests

```bash
# All tests
python -m pytest tests/

# Specific test file
python -m pytest tests/test_my_feature.py

# Specific test function
python -m pytest tests/test_my_feature.py::test_specific_function

# With coverage report
python -m pytest --cov=src --cov-report=html tests/
```

### Writing Tests

**Test Structure:**
```python
import pytest
from src import SelfOptimizingSystem

class TestMyFeature:
    """Test suite for my feature"""
    
    def setup_method(self):
        """Setup before each test"""
        self.system = SelfOptimizingSystem()
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        result = self.system.my_feature()
        assert result is not None
    
    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            self.system.my_feature(invalid_param=True)
    
    @pytest.mark.parametrize("input,expected", [
        ("test1", "result1"),
        ("test2", "result2"),
    ])
    def test_multiple_inputs(self, input, expected):
        """Test with multiple inputs"""
        result = self.system.my_feature(input)
        assert result == expected
```

### Test Coverage

Aim for >80% test coverage:

```bash
# Generate coverage report
python -m pytest --cov=src --cov-report=term-missing tests/

# View HTML report
python -m pytest --cov=src --cov-report=html tests/
open htmlcov/index.html
```

## Submitting Changes

### 1. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with clear message
git commit -m "Add: New feature description"
```

**Commit Message Format:**
```
Type: Brief description (50 chars or less)

More detailed explanation if needed (wrap at 72 chars).
Explain the problem and why this change solves it.

- Bullet points for multiple changes
- Reference issues: Fixes #123

Type can be:
- Add: New feature
- Fix: Bug fix
- Docs: Documentation changes
- Style: Code style changes
- Refactor: Code refactoring
- Test: Adding tests
- Chore: Maintenance tasks
```

### 2. Push to Your Fork

```bash
# Push branch
git push origin feature/your-feature-name
```

### 3. Create Pull Request

1. Go to GitHub repository
2. Click "New Pull Request"
3. Select your branch
4. Fill out the template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Updated documentation

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## Related Issues
Fixes #123
```

### 4. Address Review Feedback

```bash
# Make requested changes
git add .
git commit -m "Address review feedback"
git push origin feature/your-feature-name
```

## Code Style

### Python Style Guide

Follow PEP 8 and project conventions:

```python
# Good: Clear naming and documentation
def calculate_optimization_score(
    failure_count: int,
    success_count: int,
    threshold: float = 0.8
) -> float:
    """
    Calculate optimization score based on success rate.
    
    Args:
        failure_count: Number of failures
        success_count: Number of successes
        threshold: Minimum acceptable score
        
    Returns:
        Score between 0.0 and 1.0
    """
    total = failure_count + success_count
    if total == 0:
        return 0.0
    return success_count / total
```

### Code Formatting

```bash
# Format with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type check with mypy
mypy src/
```

### Style Guidelines

1. **Naming Conventions**
   - `snake_case` for functions and variables
   - `PascalCase` for classes
   - `UPPER_CASE` for constants
   - Descriptive names, not abbreviations

2. **Imports**
   - Standard library first
   - Third-party packages second
   - Local imports last
   - Alphabetically sorted within each group

3. **Type Hints**
   - Always use type hints
   - Use `Optional` for nullable types
   - Use `Union` for multiple types

4. **Documentation**
   - Docstrings for all public functions
   - Google-style or NumPy-style format
   - Include examples for complex functions

5. **Comments**
   - Explain "why", not "what"
   - Keep comments up to date
   - Remove commented-out code

## Documentation

### Updating Documentation

```bash
# Documentation is in /docs folder
docs/
├── README.md          # Documentation index
├── setup-guide.md     # Setup instructions
├── usage-guide.md     # Usage examples
├── api-reference.md   # API documentation
└── ...
```

### Documentation Standards

1. **Clear and Concise**
   - Use simple language
   - Provide examples
   - Include code snippets

2. **Well-Structured**
   - Use headings and subheadings
   - Include table of contents
   - Link related sections

3. **Up to Date**
   - Update docs with code changes
   - Test all examples
   - Fix broken links

### Example Documentation

```markdown
## Feature Name

Brief description of the feature.

### Usage

```python
from src import feature

# Basic usage
result = feature.do_something("param")

# Advanced usage
result = feature.do_something(
    param="value",
    option1=True,
    option2=False
)
```

### Parameters

- `param` (str): Description of parameter
- `option1` (bool, optional): Description. Default: False
- `option2` (bool, optional): Description. Default: False

### Returns

- `dict`: Dictionary containing:
  - `status` (str): Operation status
  - `result` (any): Result data

### Example

```python
result = feature.do_something("example")
print(result['status'])  # "success"
```
```

## Review Process

### What We Look For

1. **Code Quality**
   - Clean and readable
   - Well-documented
   - Follows style guide

2. **Testing**
   - Tests included
   - Good coverage
   - Tests pass

3. **Documentation**
   - Updated docs
   - Clear examples
   - No broken links

4. **Compatibility**
   - No breaking changes (or documented)
   - Backward compatible
   - Cross-platform if applicable

### Review Timeline

- Initial review within 3-5 business days
- Follow-up reviews within 1-2 business days
- Merging after approval from maintainers

## Getting Help

### Resources

- [Setup Guide](setup-guide.md) - Development setup
- [Architecture](architecture.md) - System design
- [API Reference](api-reference.md) - API docs
- [GitHub Issues](https://github.com/abxba0/autonomai/issues) - Bug reports

### Questions?

- Open a discussion on GitHub
- Ask in issue comments
- Tag maintainers (@username)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project README

Thank you for contributing! 🎉
