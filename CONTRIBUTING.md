<!--
SPDX-License-Identifier: MPL-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Contributing to python-nss-ng

Thank you for your interest in contributing to python-nss-ng! This document
provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [CI/CD Workflows](#cicd-workflows)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/).
Please be respectful and constructive in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up your development environment (see below)
4. Create a feature branch from `main`
5. Make your changes
6. Test your changes
7. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.10 or later
- NSS 3.100+ development libraries
- NSPR 4.35+ development libraries
- pkg-config
- Meson build system
- Ninja build tool
- C compiler (GCC or Clang)

### Quick Setup

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

```bash
# Clone the repository
git clone https://github.com/lfreleng-actions/python-nss-ng.git
cd python-nss-ng

# Install system dependencies (Ubuntu/Debian)
make deps-nss deps-test

# Create virtual environment and install in editable mode
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest test/ -v
```

## CI/CD Workflows

This project uses multiple GitHub Actions workflows for different purposes:

### `compatibility.yaml` - Platform Compatibility Testing

**Purpose:** Validates compatibility with system-provided NSS/NSPR packages
across different platforms and distributions.

**What it tests:**

- Fedora Linux (x86_64 and aarch64) with NSS 3.117+
- macOS (Apple Silicon) with Homebrew NSS/NSPR
- Python versions: 3.10, 3.11, 3.12, 3.14 (Linux), 3.10-3.14 (macOS)

**When it runs:**

- On pull requests
- On push to `main`, `master`, or `develop` branches
- Manual workflow dispatch

**Use cases:**

- Verifying compatibility with newer NSS versions
- Testing system package integration (for distro maintainers)
- Validating macOS Homebrew builds
- Quick platform smoke tests

### `build-test.yaml` - Production CI/CD Pipeline

**Purpose:** Creates production-ready artifacts with comprehensive testing,
security scanning, and quality checks.

**What it includes:**

- **Build jobs:** Creates manylinux_2_38 wheels for x86_64 and aarch64
- **Test jobs:** Runs pytest with coverage reporting
- **Audit jobs:** Security auditing with pip-audit
- **SBOM jobs:** Generates Software Bill of Materials (CycloneDX format)
- **Security scanning:** Grype vulnerability scanning

**When it runs:**

- On pull requests to `main` or `master`
- Manual workflow dispatch (with optional cache clearing)

**Artifacts generated:**

- Python wheels (`.whl` files) - manylinux compatible
- Coverage reports (XML and HTML)
- SBOM files (JSON and XML)
- Security scan results (SARIF and text)

**Required to pass:** All pull requests must pass this workflow before merging.

### `build-test-release.yaml` - Release Pipeline

**Purpose:** Automated release process for publishing to PyPI.

**When it runs:**

- On tag push (e.g., `v1.0.2`)

**What it does:**

- Validates tag and version
- Builds wheels and source distribution for all platforms
- Runs all tests and audits
- Generates SBOM
- Publishes to Test PyPI (for validation)
- Publishes to PyPI (production)
- Attaches artifacts to GitHub release
- Promotes draft release to published

**Credentials required:**

- `TEST_PYPI_CREDENTIAL` (GitHub secret)
- `PYPI_CREDENTIAL` (GitHub secret)

### Understanding the Workflows

```text
┌─────────────────────────────────────────────────────────────┐
│ Pull Request Opened                                         │
└───────────┬─────────────────────────────────────────────────┘
            │
            ├──► compatibility.yaml (Platform Testing)
            │    ├─ Fedora x64 + ARM64 (Python 3.10-3.14)
            │    └─ macOS ARM64 (Python 3.10-3.14)
            │
            └──► build-test.yaml (Production CI/CD)
                 ├─ Extract metadata
                 ├─ Build wheels (x64 + ARM64)
                 ├─ Run tests with coverage
                 ├─ Security audit
                 └─ Generate SBOM + scan

┌─────────────────────────────────────────────────────────────┐
│ Tag Pushed (e.g., v1.0.2)                                   │
└───────────┬─────────────────────────────────────────────────┘
            │
            └──► build-test-release.yaml (Release Pipeline)
                 ├─ Validate tag
                 ├─ Build all artifacts
                 ├─ Run comprehensive tests
                 ├─ Publish to Test PyPI
                 ├─ Publish to PyPI
                 └─ Create GitHub release
```

## Testing

### Running Tests Locally

```bash
# Run all tests
pytest test/ -v

# Run with coverage
pytest test/ -v --cov=nss --cov-report=html

# Run specific test file
pytest test/test_cipher.py -v

# Run tests in parallel (faster)
pytest test/ -v -n auto
```

### Test Requirements

- All new features must include tests
- Maintain or improve code coverage
- Tests must pass on all supported Python versions
- Tests should be platform-independent where possible

### Writing Tests

- Place tests in the `test/` directory
- Name test files as `test_*.py`
- Use descriptive test function names: `test_feature_behavior()`
- Add docstrings explaining complex test scenarios
- Use pytest fixtures for setup/teardown

## Submitting Changes

### Pull Request Process

1. **Create a feature branch:**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clear, concise commit messages
   - Follow the coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Test locally:**

   ```bash
   pytest test/ -v
   make lint  # Run code quality checks
   ```

4. **Push and create PR:**

   ```bash
   git push origin feature/your-feature-name
   ```

   - Open a pull request on GitHub
   - Fill out the PR template
   - Link related issues

5. **CI/CD checks:**
   - Both `compatibility.yaml` and `build-test.yaml` must pass
   - Address any failures or review comments
   - Keep your branch up to date with `main`

6. **Review process:**
   - At least one maintainer approval required
   - All CI checks must pass
   - No merge conflicts

### Commit Message Guidelines

```text
type(scope): Brief description (50 chars or less)

More detailed explanation if needed (wrap at 72 characters).
Explain the problem this commit solves and why this approach
was chosen.

Fixes #123
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

## Coding Standards

### Python Code Style

- **PEP 8** compliance (enforced by ruff)
- **Line length:** 100 characters maximum
- **Type hints:** Use where appropriate
- **Docstrings:** Required for all public functions/classes

### Code Quality Tools

We use the following tools (configured in `pyproject.toml`):

- **ruff:** Linting and code formatting
- **mypy:** Static type checking
- **pytest:** Testing framework
- **pytest-cov:** Coverage reporting

### Pre-commit Hooks

Install pre-commit hooks to catch issues early:

```bash
pip install pre-commit
pre-commit install
```

This will automatically run checks before each commit.

### C Code Guidelines

For C extensions in `src/`:

- Follow existing code style
- Use descriptive variable names
- Add comments for complex logic
- Ensure no memory leaks
- Handle all error cases
- Maintain Python C API compatibility

## Documentation

- Update `README.md` for user-facing changes
- Update `QUICKSTART.md` for setup/installation changes
- Add docstrings to new Python code
- Update `doc/ChangeLog` for notable changes
- Keep `CONTRIBUTING.md` current

## Release Process

Releases are handled automatically via `build-test-release.yaml`:

1. Update version in `pyproject.toml`
2. Update `src/__init__.py` `__version__`
3. Update `doc/ChangeLog`
4. Create and push annotated tag:

   ```bash
   git tag -s v1.0.2 -m "Release 1.0.2"
   git push origin v1.0.2
   ```

5. Workflow automatically builds, tests, and publishes to PyPI
6. Workflow creates GitHub release with artifacts

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/lfreleng-actions/python-nss-ng/issues)
- **Discussions:** Use GitHub Discussions for questions
- **Email:** Maintainers listed in `pyproject.toml`

## License

By contributing to python-nss-ng, you agree that your contributions will be
licensed under the project's license (MPL-2.0 OR GPL-2.0-or-later OR
LGPL-2.0-or-later).

Thank you for contributing! 🎉
