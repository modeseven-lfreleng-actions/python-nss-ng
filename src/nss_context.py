# SPDX-License-Identifier: MPL-2.0
# SPDX-FileCopyrightText: Copyright (c) 2010-2025 python-nss-ng contributors

"""
NSS lifecycle context manager for python-nss-ng.

This module provides context managers for proper NSS initialization and shutdown,
helping to avoid common lifecycle management issues.

NSS initialization and shutdown rules:
- nss_init() or nss_init_nodb() should be called exactly once per process
- nss_shutdown() should be called exactly once per process, not per thread
- Repeated init/shutdown in high-frequency loops should be avoided
- All NSS operations must occur after initialization and before shutdown

Example usage:
    >>> with NSSContext(db_name='sql:pki'):
    ...     # NSS is initialized, perform operations
    ...     cert = nss.find_cert_from_nickname('server_cert')
    ...     # NSS will be shut down on exit

    >>> with NSSContext():  # No database
    ...     # NSS initialized without database
    ...     digest = nss.sha256_digest(b"data")
"""

import contextlib
import logging
from collections.abc import Callable, Generator
from typing import Any

# aislop-ignore-file ai-slop/hallucinated-import -- "nss" is this package's own compiled C-extension module (built from py_nss.c)

logger = logging.getLogger(__name__)


class NSSContext:
    """
    Context manager for NSS initialization and shutdown.

    This ensures proper NSS lifecycle management with automatic cleanup.

    Args:
        db_name: Path to NSS certificate database (e.g., 'sql:pki').
                 If None, NSS is initialized without a database.
        password_callback: Optional password callback function
        flags: Optional NSS initialization flags

    Example:
        >>> with NSSContext(db_name='sql:pki'):
        ...     cert = nss.find_cert_from_nickname('my_cert')
        ...     print(cert.subject)

        >>> with NSSContext():  # No database
        ...     data = b"hello world"
        ...     digest = nss.sha256_digest(data)
    """

    def __init__(
        self,
        db_name: str | None = None,
        password_callback: Callable[..., Any] | None = None,
        flags: int = 0,
    ):
        """Initialize NSS context manager."""
        self.db_name = db_name
        self.password_callback = password_callback
        self.flags = flags
        self._initialized = False

    def __enter__(self):
        """Initialize NSS on context entry."""
        try:
            import nss.nss as nss

            if self.password_callback:
                nss.set_password_callback(self.password_callback)

            if self.db_name:
                logger.debug(f"Initializing NSS with database: {self.db_name}")
                nss.nss_init(self.db_name)
            else:
                logger.debug("Initializing NSS without database")
                nss.nss_init_nodb()

            self._initialized = True
            logger.debug("NSS initialized successfully")
            return self

        except Exception as e:
            logger.error(f"Failed to initialize NSS: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Shutdown NSS on context exit."""
        if self._initialized:
            try:
                import nss.nss as nss

                logger.debug("Shutting down NSS")
                nss.nss_shutdown()
                self._initialized = False
                logger.debug("NSS shutdown complete")
            except Exception as e:
                logger.warning(f"Error during NSS shutdown: {e}")
                # Don't raise - we're already exiting

        # Return False to propagate any exception that occurred in the with block
        return False


@contextlib.contextmanager
def nss_context(
    db_name: str | None = None,
    password_callback: Callable[..., Any] | None = None,
    flags: int = 0,
) -> Generator[None, None, None]:
    """
    Functional context manager for NSS lifecycle.

    This is a functional alternative to the NSSContext class.

    Args:
        db_name: Path to NSS certificate database or None for no database
        password_callback: Optional password callback function
        flags: Optional NSS initialization flags

    Yields:
        None - context is active while NSS is initialized

    Example:
        >>> with nss_context('sql:pki'):
        ...     # NSS operations here
        ...     pass
    """
    context = NSSContext(db_name=db_name, password_callback=password_callback, flags=flags)
    with context:
        yield
