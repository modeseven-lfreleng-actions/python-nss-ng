#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 The Linux Foundation
#
# Build NSS/NSPR and install system test dependencies for python-nss-ng,
# then publish the native library path for subsequent workflow steps.
# Consumed by the reusable multi-arch workflow via its setup_script input.
set -euo pipefail

# This script assumes a Linux runner: it calls ldconfig and relies on
# Linux multiarch library paths.
if [ "$(uname -s)" != "Linux" ]; then
  echo "Error: setup-nss.sh supports Linux runners only ❌" >&2
  exit 1
fi

# GITHUB_ENV must exist so the exported library path persists to the
# steps that follow (the build/test/audit actions).
if [ -z "${GITHUB_ENV:-}" ]; then
  echo "Error: GITHUB_ENV is not set; run this under GitHub Actions ❌" >&2
  exit 1
fi

# Run from the repository root (two levels up from this script) so the
# Makefile targets resolve regardless of the caller's working directory.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${script_dir}/../.."

make deps-nss deps-test-system
sudo ldconfig

# Publish the NSS/NSPR library and pkg-config paths for the steps that
# follow, derived from INSTALL_PREFIX (the Makefile default is /usr). We
# export them here directly -- rather than via `make env-github-actions`
# -- so each variable has a single authoritative export. Prepend without
# an empty path element (a trailing ':' would add the working directory to
# the search path) and skip when already present, so repeat runs in the
# same job stay idempotent.
prefix="${INSTALL_PREFIX:-/usr}"
# Reject control characters (newlines/CRs) in the prefix: it is written to
# $GITHUB_ENV as `VAR=value` lines, so an embedded newline would be an
# environment-file injection vector.
case "${prefix}" in
  *$'\n'* | *$'\r'*)
    echo "Error: INSTALL_PREFIX must not contain newlines/CRs ❌" >&2
    exit 1 ;;
esac
lib_path="${prefix}/lib:${prefix}/lib/aarch64-linux-gnu:${prefix}/lib/x86_64-linux-gnu"
pkg_path="${prefix}/lib/pkgconfig"

# prepend_export VAR_NAME NEW_PREFIX CURRENT_VALUE
prepend_export() {
  local var="$1" add="$2" cur="${3:-}"
  # Refuse to write values containing newlines/CRs into $GITHUB_ENV
  # (environment-file injection guard, covering the inherited value too).
  case "${add}${cur}" in
    *$'\n'* | *$'\r'*)
      echo "Error: ${var} value contains newlines/CRs ❌" >&2
      exit 1 ;;
  esac
  case ":${cur}:" in
    *":${add}:"*) printf '%s=%s\n' "$var" "$cur" ;;
    "::") printf '%s=%s\n' "$var" "$add" ;;
    *) printf '%s=%s:%s\n' "$var" "$add" "$cur" ;;
  esac
}
{
  prepend_export LD_LIBRARY_PATH "$lib_path" "${LD_LIBRARY_PATH:-}"
  prepend_export PKG_CONFIG_PATH "$pkg_path" "${PKG_CONFIG_PATH:-}"
} >> "$GITHUB_ENV"
