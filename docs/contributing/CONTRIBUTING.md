# Contributing to TriplePlay-Sentinel

Thank you for your interest in contributing to TriplePlay-Sentinel! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Documentation Standards](#documentation-standards)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct that promotes a welcoming and inclusive environment. By participating, you agree to uphold this standard.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- **Git** for version control
- **Docker & Docker Compose** for development environment
- **Python 3.9+** for local development
- **Basic understanding** of network monitoring, Zabbix, and MikroTik devices

### Areas for Contribution

We welcome contributions in the following areas:

- 🐛 **Bug fixes** and issue resolution
- ✨ **New features** and enhancements
- 📚 **Documentation** improvements
- 🧪 **Test coverage** expansion
- 🔧 **Performance** optimizations
- 🛡️ **Security** improvements
- 🌐 **Internationalization** support

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/flicl/TriplePlay-Sentinel.git
cd TriplePlay-Sentinel

# Add upstream remote
git remote add upstream https://github.com/flicl/TriplePlay-Sentinel.git
```

### 2. Development Environment

#### Option A: Docker Development (Recommended)
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Access development container
docker exec -it tripleplay-dev bash
```

#### Option B: Local Development
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r src/collector/requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Verify Setup

```bash
# Run tests to ensure everything works
./run_tests.sh

# Start local development server
./start_local.sh

# Verify health check
curl http://localhost:5000/api/health
```

## Contributing Process

### 1. Issue Tracking

Before starting work:

1. **Check existing issues** to avoid duplication
2. **Create an issue** for bugs or feature requests
3. **Discuss major changes** before implementation
4. **Get assignment** on the issue to avoid conflicts

### 2. Branch Strategy

We use Git Flow branching model:

```bash
# Create feature branch from develop
git checkout develop
git pull upstream develop
git checkout -b feature/your-feature-name

# Create bugfix branch from main
git checkout main
git pull upstream main
git checkout -b bugfix/issue-description
```

### Branch Naming Conventions

- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical production fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test improvements

### 3. Development Workflow

```bash
# Make your changes
# Write tests for new functionality
# Update documentation if needed

# Run tests frequently
./run_tests.sh

# Commit changes with clear messages
git commit -m "feat: add connection retry logic"

# Keep your branch updated
git fetch upstream
git rebase upstream/develop
```

## Code Style Guidelines

### Python Code Style

We follow **PEP 8** with some project-specific conventions:

#### Code Formatting
```python
# Use Black formatter (automatically applied via pre-commit)
black src/

# Import organization
import os
import sys
from typing import Dict, List, Optional

import redis
import paramiko
from flask import Flask, request, jsonify

from .models import TestResult
from .config import Config
```

#### Naming Conventions
```python
# Classes: PascalCase
class MikroTikConnector:
    pass

# Functions and variables: snake_case
def execute_ping_test():
    test_result = {}
    return test_result

# Constants: UPPER_SNAKE_CASE
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Private methods: leading underscore
def _validate_connection(self):
    pass
```

#### Documentation Strings
```python
def execute_test(host: str, test_type: str, target: str) -> TestResult:
    """
    Execute network connectivity test on MikroTik device.
    
    Args:
        host: MikroTik device IP address
        test_type: Type of test ('ping' or 'traceroute')
        target: Target IP or hostname to test
        
    Returns:
        TestResult object containing test results and metadata
        
    Raises:
        ConnectionError: When SSH connection fails
        ValidationError: When input parameters are invalid
        
    Example:
        >>> result = execute_test('192.168.1.1', 'ping', '8.8.8.8')
        >>> print(result.success)
        True
    """
    pass
```

### Configuration Style

#### YAML Configuration
```yaml
# Use 2-space indentation
# Descriptive keys with underscores
collector:
  host: 0.0.0.0
  port: 5000
  
cache:
  redis_host: redis
  cache_ttl: 30
  
mikrotik:
  ssh_timeout: 30
  max_retries: 3
```

#### Environment Variables
```bash
# Use SCREAMING_SNAKE_CASE
# Group related variables with prefixes
COLLECTOR_HOST=0.0.0.0
COLLECTOR_PORT=5000

REDIS_HOST=redis
REDIS_PASSWORD=secret

MIKROTIK_SSH_TIMEOUT=30
MIKROTIK_MAX_RETRIES=3
```

## Testing Requirements

### Test Types

#### Unit Tests
```python
# Test individual functions and methods
# Location: tests/unit/
# File naming: test_*.py

import pytest
from src.collector.mikrotik import MikroTikConnector

def test_connection_validation():
    """Test SSH connection parameter validation."""
    connector = MikroTikConnector()
    
    # Test valid parameters
    assert connector.validate_connection('192.168.1.1', 'admin', 'password')
    
    # Test invalid parameters
    with pytest.raises(ValueError):
        connector.validate_connection('invalid-ip', 'admin', 'password')
```

#### Integration Tests
```python
# Test component interactions
# Location: tests/integration/
# Require running services

def test_api_ping_integration():
    """Test complete ping workflow through API."""
    response = client.post('/api/test', json={
        'mikrotik_host': '192.168.1.1',
        'mikrotik_user': 'admin',
        'mikrotik_password': 'password',
        'target': '8.8.8.8',
        'test_type': 'ping'
    })
    
    assert response.status_code == 200
    assert response.json['status'] == 'success'
```

#### End-to-End Tests
```python
# Test complete user workflows
# Location: tests/e2e/
# Test against real or mocked MikroTik devices

def test_zabbix_monitoring_workflow():
    """Test complete Zabbix → Collector → MikroTik workflow."""
    # Setup test environment
    # Execute Zabbix HTTP Agent call
    # Verify results
    pass
```

### Test Execution

```bash
# Run all tests
./run_tests.sh

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=src/collector tests/

# Run performance tests
pytest tests/performance/ -v
```

### Test Coverage Requirements

- **Minimum coverage**: 80% for new code
- **Critical components**: 95% coverage required
- **Integration tests**: Required for all API endpoints
- **Documentation**: All public APIs must have usage examples

## Documentation Standards

### Code Documentation

#### API Documentation
```python
# Use OpenAPI/Swagger compatible docstrings
@app.route('/api/test', methods=['POST'])
def test_connectivity():
    """
    Execute network connectivity test.
    
    ---
    tags:
      - Connectivity Tests
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            mikrotik_host:
              type: string
              description: MikroTik device IP address
              example: "192.168.1.1"
    responses:
      200:
        description: Test completed successfully
        schema:
          $ref: '#/definitions/TestResult'
    """
    pass
```

### User Documentation

#### Markdown Standards
```markdown
# Use clear hierarchical structure
# Include code examples with syntax highlighting
# Add screenshots for UI elements
# Provide troubleshooting sections

## Section Title

Brief description of the section.

### Subsection

Step-by-step instructions:

1. **Step 1**: Description
   ```bash
   command example
   ```

2. **Step 2**: Description
   - Sub-point 1
   - Sub-point 2

### Example

```python
# Provide working code examples
result = execute_test('192.168.1.1', 'ping', '8.8.8.8')
print(f"Test result: {result.success}")
```

### ⚠️ Important Notes

Use callout boxes for important information.
```

### Documentation Updates

When contributing:

1. **Update relevant documentation** for any feature changes
2. **Add new documentation** for new features
3. **Update API documentation** for endpoint changes
4. **Include examples** for new functionality
5. **Update troubleshooting guides** for known issues

## Submitting Changes

### Pre-Submission Checklist

Before submitting a pull request:

- [ ] **Tests pass**: All tests execute successfully
- [ ] **Code style**: Follows project style guidelines
- [ ] **Documentation**: Updated for any changes
- [ ] **Changelog**: Entry added to CHANGELOG.md
- [ ] **Commit messages**: Follow conventional commit format
- [ ] **Branch updated**: Rebased on latest upstream/develop

### Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
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
```bash
feat(api): add connection retry logic
fix(cache): resolve Redis connection timeout
docs(setup): update Docker installation guide
test(mikrotik): add SSH connection tests
```

### Pull Request Process

1. **Create pull request** from your feature branch to `develop`
2. **Fill out template** with all required information
3. **Request review** from maintainers
4. **Address feedback** and update as needed
5. **Squash commits** if requested
6. **Wait for approval** and merge

### Pull Request Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance impact assessed

## Documentation
- [ ] Code comments updated
- [ ] API documentation updated
- [ ] User documentation updated
- [ ] Changelog updated

## Screenshots (if applicable)
Add screenshots for UI changes.
```

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Workflow

1. **Feature freeze** on develop branch
2. **Create release branch** from develop
3. **Update version numbers** and changelog
4. **Final testing** and bug fixes
5. **Merge to main** and tag release
6. **Deploy to production** environments
7. **Update documentation** and announcements

### Pre-Release Testing

- [ ] **Unit tests**: 100% pass rate
- [ ] **Integration tests**: All scenarios covered
- [ ] **Performance tests**: No regressions
- [ ] **Security scan**: No critical vulnerabilities
- [ ] **Documentation review**: All docs updated
- [ ] **Deployment test**: Successful in staging environment

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Request Comments**: Code review discussions
- **Documentation**: Check docs/ directory first

### Maintainer Response Times

- **Bug reports**: 2-3 business days
- **Feature requests**: 1 week
- **Pull requests**: 3-5 business days
- **Security issues**: 24-48 hours

### Escalation Process

For urgent issues:
1. Create GitHub issue with "urgent" label
2. Contact maintainers directly if security-related
3. Provide detailed reproduction steps
4. Include environment information

---

Thank you for contributing to TriplePlay-Sentinel! Your efforts help make network monitoring better for everyone.