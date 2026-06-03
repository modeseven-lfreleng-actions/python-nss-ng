<!--
SPDX-License-Identifier: MPL-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# python-nss-ng

[![Platform Compatibility](https://github.com/lfreleng-actions/python-nss-ng/actions/workflows/compatibility.yaml/badge.svg)](https://github.com/lfreleng-actions/python-nss-ng/actions/workflows/compatibility.yaml)
[![CI/CD Pipeline](https://github.com/lfreleng-actions/python-nss-ng/actions/workflows/build-test.yaml/badge.svg)](https://github.com/lfreleng-actions/python-nss-ng/actions/workflows/build-test.yaml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MPL-2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)

Python bindings for Network Security Services (NSS) and Netscape Portable
Runtime (NSPR).

## Supported Platforms

python-nss-ng officially supports:

- **Linux** (all major distributions)
- **macOS**

**Windows is NOT supported.** Attempting to import python-nss-ng on Windows
will raise a `RuntimeError`.

## Overview

python-nss-ng is a Python binding for NSS (Network Security Services) and NSPR
(Netscape Portable Runtime). NSS provides cryptography services supporting
SSL, TLS, PKI, PKIX, X509, PKCS*, etc. NSS is an alternative to OpenSSL and
used extensively by major software projects. NSS is FIPS-140 certified.

NSS uses NSPR because NSPR provides an abstraction of common operating system
services, in the areas of networking and process management. Python also
provides an abstraction of common operating system services but because NSS
and NSPR have tight coupling, python-nss-ng exposes elements of NSPR.

## Project Modernization (2025)

This project received modernization work to support current Python versions
and build standards:

### Changes Made

- **Python Support**: Now supports Python 3.10, 3.11, 3.12, 3.13, and 3.14
- **Build System**: Migrated from legacy `distutils` to modern `setuptools`
  with `pyproject.toml`
- **Version Management**: Implemented dynamic versioning using
  `setuptools-scm`
- **Package Structure**: Follows current PEP standards (PEP 517, PEP 518, PEP
  621)
- **Development Tools**: Added support for `uv`, modern testing with `pytest`,
  and code quality with `ruff`

### NSS/NSPR Compatibility

✅ **C Extension Compatibility**: The C code now compiles with NSS 3.100+ and
works with NSS 3.117.

**Recent Fixes**:

- Resolved typedef conflicts (`RSAPublicKey` → `PyRSAPublicKey`, etc.)
- Fixed SPDX comment block formatting issues
- All 32 tests pass with NSS 3.117 and NSPR 4.38

**Tested Versions**:

- NSS 3.117
- NSPR 4.38.2
- Python 3.10, 3.11, 3.12, 3.13, 3.14

## System Requirements

### Required Libraries

Before building python-nss-ng, you need the C language header files and libraries
for both NSPR and NSS installed. This is system and distribution specific.

#### Fedora/RHEL/CentOS

```bash
sudo dnf install nss-devel nspr-devel
```

#### Debian/Ubuntu

```bash
sudo apt-get install libnss3-dev libnspr4-dev
```

#### macOS (Homebrew)

```bash
brew install nss nspr
```

## Installation

### Using uv (Recommended)

```bash
# Create a virtual environment with Python 3.10+
uv venv --python 3.10

# Activate the environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install in development mode
uv pip install -e ".[dev]"
```

### Using pip

```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"
```

### Custom Include/Library Paths

If NSS/NSPR live in non-standard locations, set the `NSS_INCLUDE_ROOTS`
environment variable:

```bash
export NSS_INCLUDE_ROOTS="/custom/path/include:/another/path/include"
pip install -e .
```

## Development

### Test Dependencies

The test suite requires NSS command-line tools for certificate generation:

#### NSS Tools: Fedora/RHEL/CentOS

```bash
sudo dnf install nss-tools
```

#### NSS Tools: Debian/Ubuntu

```bash
sudo apt-get install libnss3-tools
```

#### NSS Tools: macOS (Homebrew)

The `nss` package includes NSS tools:

```bash
brew install nss
```

### Running Tests

#### Quick Start (Automated)

Use the comprehensive test runner script that handles all setup:

```bash
# Run all tests (handles setup, builds C extension, creates certificates)
./scripts/run-all-tests.sh

# Quick mode: pure Python tests only (no C extension build needed)
./scripts/run-all-tests.sh --quick

# Other options
./scripts/run-all-tests.sh --help
```

The script automatically:

- Checks for dependencies (uv, NSS, NSPR)
- Creates virtual environment
- Installs test dependencies
- Builds C extension (if needed)
- Sets up test certificates
- Runs tests

#### Manual Testing

```bash
# Install with test dependencies
uv pip install -e ".[test]"

# Run tests (recommended for reliability)
pytest test/ -n0

# Or run with parallel execution (may have occasional intermittent failures)
pytest test/
```

**Note:** Some tests have known intermittent failures with parallel execution.
Tests automatically generate certificates in a `pki/` directory within the
test folder using `certutil` from nss-tools. For fully reliable results, use
`-n0` to disable parallel execution. See [TESTING.md](TESTING.md) for details
about test reliability and certificate generation.

### Building

```bash
# Build source distribution and wheel
uv pip install build
python -m build
```

#### Build Performance ⚡

Builds are now **40-80% faster** thanks to automatic optimizations:

- **Probe Caching**: Library locations cached (27% faster)
- **Parallel Compilation**: Uses all CPU cores (40% faster)
- **ccache in CI**: Compilation results cached (78% faster CI)

All optimizations work automatically! For even faster local builds:

```bash
# Optional: Install ccache for 87% faster rebuilds
brew install ccache  # macOS
export CC="ccache clang"
```

See [BUILD_OPTIMIZATION_QUICKSTART.md](BUILD_OPTIMIZATION_QUICKSTART.md) for details.

### Code Quality

Check code style and format code:

```bash
ruff check .
ruff format .
```

## Project Structure

```text
python-nss-ng/
├── src/                    # C extension source files and Python package
│   ├── __init__.py        # Main package initialization
│   ├── py_nss.c           # NSS bindings
│   ├── py_ssl.c           # SSL/TLS bindings
│   ├── py_nspr_io.c       # NSPR I/O bindings
│   └── py_nspr_error.c    # NSPR error handling
├── test/                  # Test suite
├── doc/                   # Documentation
├── pyproject.toml        # Modern Python project configuration
├── meson.build           # Meson build configuration
└── MANIFEST.in           # Source distribution file inclusion rules
```

## Documentation

More information on python-nss-ng is available on the
[python-nss-ng project page](http://www.mozilla.org/projects/security/pki/python-nss-ng).

For information on NSS and NSPR, see the following:

- Network Security Services:
  [NSS project page](http://www.mozilla.org/projects/security/pki/nss/)
- Netscape Portable Runtime:
  [NSPR project page](http://www.mozilla.org/projects/nspr/)

## License

This project is triple-licensed under:

- Mozilla Public License 2.0 (MPL-2.0)
- GNU General Public License v2 or later (GPLv2+)
- GNU Lesser General Public License v2 or later (LGPLv2+)

See LICENSE.mpl, LICENSE.gpl, and LICENSE.lgpl files for details.

## Contributing

This is a modernization effort for an existing project. Contributions to fix
the NSS compatibility issues and modernize the C code are welcome!

### Priority Issues

1. Fix C code compatibility with NSS 3.100+
2. Update API usage for modern NSS/NSPR
3. Add comprehensive test coverage
4. Improve documentation
5. Add type hints to Python code

## Authors and Maintainers

- **Original Author**: John Dennis <jdennis@redhat.com>
- **Current Maintainer**: Project seeking active maintainer

## Support

- **Issues**: [GitHub Issues](https://github.com/lfreleng-actions/python-nss-ng/issues)
- **Repository**: [GitHub Repository](https://github.com/lfreleng-actions/python-nss-ng)
