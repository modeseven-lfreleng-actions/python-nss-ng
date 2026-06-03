<!--
SPDX-License-Identifier: MPL-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Quick Start Guide

Get up and running with python-nss-ng development in 5 minutes.

## Prerequisites

### System Dependencies

Install NSS and NSPR development libraries:

**Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install -y libnss3-dev libnspr4-dev pkg-config
```

**Fedora/RHEL/CentOS:**

```bash
sudo dnf install -y nss-devel nspr-devel pkg-config
```

**macOS:**

```bash
brew install nss nspr pkg-config
```

### Python Requirements

- Python 3.10 or later
- pip or uv package manager

## Quick Setup

### Option 1: Using uv (Recommended - Fast)

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/lfreleng-actions/python-nss-ng.git
cd python-nss-ng

# Create virtual environment and install dependencies
uv venv --python 3.10
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install in development mode with all dependencies
uv pip install -e ".[dev]"
```

### Option 2: Using pip

```bash
# Clone the repository
git clone https://github.com/lfreleng-actions/python-nss-ng.git
cd python-nss-ng

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"
```

## Verify Installation

```bash
# Check Python version
python --version  # Should be 3.10+

# Check NSS/NSPR installation
pkg-config --modversion nss
pkg-config --modversion nspr

# Try importing (will fail until C extensions compile)
python -c "import nss.nss; print(nss.nss.nss_get_version())"
```

## Common Tasks

### Run Tests

```bash
# Run all tests
pytest test/

# Run specific test file
pytest test/test_misc.py

# Run with coverage
pytest test/ --cov=nss --cov-report=html

# Skip slow tests
pytest test/ -m "not slow"
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Run type checker
mypy .
```

### Pre-commit Hooks

```bash
# Install and enable hooks (recommended)
pip install pre-commit && pre-commit install

# Run hooks manually on all files
pre-commit run --all-files
```

### Build Package

```bash
# Build source distribution and wheel
python -m build

# Check build artifacts
ls dist/
```

### Documentation

Read the comprehensive guides:

- **README.md** - Project overview and installation
- **TODO.md** - Current status and tasks
- **CONTRIBUTING.md** - How to contribute
- **doc/TESTING.md** - Testing guide
- **doc/MIGRATION.md** - Modernization changes
- **CHANGELOG.md** - Change history

## Project Structure

```text
python-nss-ng/
├── src/                  # Source code
│   ├── *.c              # C extension files
│   ├── *.pyi            # Type stub files
│   └── __init__.py      # Python package
├── test/                # Test suite
│   ├── conftest.py      # pytest configuration
│   └── test_*.py        # Test files
├── doc/                 # Documentation
├── .github/             # GitHub Actions workflows
├── pyproject.toml       # Project configuration
└── meson.build          # Build configuration
```

## Known Issues

### C Extension Compilation

### ⚠️ Important Build Caveat

**IMPORTANT**: The C extensions do NOT compile with NSS 3.100+.

**TODO Issue #1** tracks this critical blocker for:

- Running tests
- Using the library
- Creating releases

**Workaround**: Use NSS versions < 3.100 if available.

**Status**: Awaiting fixes for:

- Struct member access issues
- API changes in modern NSS
- Python C API updates

## Development Workflow

1. **Create a branch**

   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes**
   - Write code
   - Add tests
   - Update documentation

3. **Test locally**

   ```bash
   pytest test/
   ruff check .
   mypy .
   ```

4. **Commit changes**

   ```bash
   git add .
   git commit -m "feat: add my feature"
   ```

5. **Push and create PR**

   ```bash
   git push origin feature/my-feature
   # Then create PR on GitHub
   ```

## Getting Help

- **Documentation**: Check README.md and doc/ directory
- **Issues**: <https://github.com/lfreleng-actions/python-nss-ng/issues>
- **TODO List**: See TODO.md for current tasks
- **Contributing**: See CONTRIBUTING.md for guidelines

## Next Steps

1. Read **CONTRIBUTING.md** for detailed contribution guidelines
2. Check **TODO.md** for priority tasks
3. Review **doc/TESTING.md** for testing information
4. Explore the codebase and tests

## Useful Commands Reference

```bash
# Development
uv pip install -e ".[dev]"          # Install dev dependencies
pytest test/ -v                      # Run tests verbosely
ruff format . && ruff check --fix .  # Format and lint
pre-commit run --all-files           # Run all checks

# Building
python -m build                      # Build distributions
pip install -e .                     # Install in editable mode

# Documentation
find doc -name "*.md" -exec cat {} \; # Read all docs

# Cleaning
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
rm -rf build/ dist/ .pytest_cache/
```

## Tips

- Use **uv** for faster dependency management
- Enable **pre-commit hooks** to catch issues before commit
- Run **pytest with coverage** to ensure tests are comprehensive
- Check **TODO.md** frequently for updated tasks
- Read **CHANGELOG.md** to understand recent changes

## Resources

- [NSS Documentation](https://developer.mozilla.org/en-US/docs/Mozilla/Projects/NSS)
- [NSPR Documentation](https://developer.mozilla.org/en-US/docs/Mozilla/Projects/NSPR)
- [Python Packaging Guide](https://packaging.python.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [ruff Documentation](https://docs.astral.sh/ruff/)

---

**Ready to contribute?** Read CONTRIBUTING.md and check TODO.md for priority tasks!
