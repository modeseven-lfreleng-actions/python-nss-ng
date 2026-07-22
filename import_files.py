#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
# SPDX-FileCopyrightText: Copyright (c) 2010-2025 python-nss-ng contributors

"""
Safe file importer: Copies files from source to destination only if they don't exist.
This script is a legacy utility from the repository migration.
Repository has been renamed to python-nss-ng.
NO files will be overwritten.
"""

import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class CopyStats:
    """Accumulates the outcome of a recursive copy operation."""

    copied_files: List[Path] = field(default_factory=list)
    copied_dirs: List[Path] = field(default_factory=list)
    skipped: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


SCRIPT_DIR = Path(__file__).parent.absolute()
SOURCE_DIR = SCRIPT_DIR.parent / "python-nss-ng"
DEST_DIR = SCRIPT_DIR

# Directories and patterns to exclude from copying
EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "*.egg-info",
    ".eggs",
    "venv",
    "env",
    ".venv",
    ".env",
}

# File patterns to exclude
EXCLUDE_FILES = {
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".coverage",
    "coverage.xml",
    "*.log",
}


def should_exclude(path: Path, relative_path: Path) -> bool:
    """Check if a path should be excluded from copying."""
    # Check if any parent directory is in exclude list
    for part in relative_path.parts:
        if part in EXCLUDE_DIRS:
            return True
        for exclude in EXCLUDE_DIRS:
            if "*" in exclude and path.is_dir() and path.name.endswith(exclude.replace("*", "")):
                return True

    # Check if file matches exclude patterns
    if path.is_file():
        for pattern in EXCLUDE_FILES:
            if "*" in pattern:
                if path.name.endswith(pattern.replace("*", "")):
                    return True
            elif path.name == pattern:
                return True

    return False


def copy_if_not_exists(src: Path, dest: Path, relative_path: Path, stats: CopyStats) -> None:
    """
    Recursively copy files and directories from src to dest,
    but only if they don't already exist in dest.
    """
    if should_exclude(src, relative_path):
        print(f"EXCLUDED: {relative_path}")
        return

    # Check symlinks first: is_dir()/is_file() follow symlinks, so a symlink
    # to a directory or file would otherwise be traversed, or its target
    # copied, instead of the link itself being reproduced.
    if src.is_symlink():
        # exists() is False for broken symlinks, so also check is_symlink()
        # to honour the no-overwrite contract for existing destinations.
        if dest.exists() or dest.is_symlink():
            stats.skipped.append(Path(relative_path))
            print(f"SKIPPED (exists): {relative_path}")
            return

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            linkto = os.readlink(src)
            os.symlink(linkto, dest)
            stats.copied_files.append(Path(relative_path))
            print(f"COPIED SYMLINK: {relative_path} -> {linkto}")
        except Exception as e:
            message = f"copying symlink {relative_path}: {e}"
            stats.errors.append(message)
            print(f"ERROR {message}", file=sys.stderr)

    elif src.is_dir():
        # A destination that is itself a symlink must not be traversed:
        # recursing would write through the link into an unexpected target,
        # and a broken link would fail mkdir. Treat it as already present.
        if dest.is_symlink():
            stats.skipped.append(Path(relative_path))
            print(f"SKIPPED (exists): {relative_path}")
            return

        dest_exists = dest.exists()

        if not dest_exists:
            try:
                dest.mkdir(parents=True, exist_ok=True)
                stats.copied_dirs.append(Path(relative_path))
                print(f"CREATED DIR: {relative_path}")
            except Exception as e:
                message = f"creating directory {relative_path}: {e}"
                stats.errors.append(message)
                print(f"ERROR {message}", file=sys.stderr)
                return
        else:
            print(f"DIR EXISTS: {relative_path} (checking contents...)")

        # Recurse regardless of whether the directory already existed
        for item in src.iterdir():
            new_relative_path = relative_path / item.name
            copy_if_not_exists(item, dest / item.name, new_relative_path, stats)

    elif src.is_file():
        # exists() is False for broken destination symlinks; treat an existing
        # symlink as already present so it is never overwritten.
        if dest.exists() or dest.is_symlink():
            stats.skipped.append(Path(relative_path))
            print(f"SKIPPED (exists): {relative_path}")
            return

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            stats.copied_files.append(Path(relative_path))
            print(f"COPIED FILE: {relative_path}")
        except Exception as e:
            message = f"copying file {relative_path}: {e}"
            stats.errors.append(message)
            print(f"ERROR {message}", file=sys.stderr)


def main():
    """Main function to orchestrate the file copying."""
    print("=" * 80)
    print("SAFE FILE IMPORTER")
    print("=" * 80)
    print(f"Source:      {SOURCE_DIR}")
    print(f"Destination: {DEST_DIR}")
    print("=" * 80)

    # Verify source directory exists
    if not SOURCE_DIR.exists():
        print(f"ERROR: Source directory does not exist: {SOURCE_DIR}", file=sys.stderr)
        sys.exit(1)

    if not SOURCE_DIR.is_dir():
        print(f"ERROR: Source is not a directory: {SOURCE_DIR}", file=sys.stderr)
        sys.exit(1)

    # Verify destination directory exists
    if not DEST_DIR.exists():
        print(f"ERROR: Destination directory does not exist: {DEST_DIR}", file=sys.stderr)
        sys.exit(1)

    stats = CopyStats()

    print("\nStarting recursive copy operation...")
    print("NOTE: Only files that DO NOT exist in destination will be copied.")
    print("      Existing directories will be checked for new files.")
    print("=" * 80)
    print()

    for item in SOURCE_DIR.iterdir():
        relative_path = Path(item.name)
        dest_path = DEST_DIR / item.name

        copy_if_not_exists(item, dest_path, relative_path, stats)

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Directories created: {len(stats.copied_dirs)}")
    print(f"Files copied:        {len(stats.copied_files)}")
    print(f"Items skipped:       {len(stats.skipped)}")
    print(f"Errors:              {len(stats.errors)}")
    print("=" * 80)

    if stats.copied_files:
        print("\nCopied files:")
        for f in sorted(stats.copied_files):
            print(f"  - {f}")

    if stats.copied_dirs:
        print("\nCreated directories:")
        for d in sorted(stats.copied_dirs):
            print(f"  - {d}")

    if stats.skipped:
        print("\nSkipped (already exist):")
        for s in sorted(stats.skipped):
            print(f"  - {s}")

    if stats.errors:
        print("\nErrors encountered:", file=sys.stderr)
        for message in stats.errors:
            print(f"  - {message}", file=sys.stderr)
        print(
            f"\nCompleted with {len(stats.errors)} error(s); "
            "no existing files were overwritten.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\nOperation completed successfully!")
    print("No existing files were overwritten.")


if __name__ == "__main__":
    main()
