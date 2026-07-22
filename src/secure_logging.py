# SPDX-License-Identifier: MPL-2.0
# SPDX-FileCopyrightText: Copyright (c) 2010-2025 python-nss-ng contributors

"""
Secure logging utilities for python-nss-ng.

This module provides security-conscious logging wrappers that help prevent
accidental logging of sensitive cryptographic material.

The intentional use of both print() and logging in python-nss-ng:
- print() is used for control flow and status messages in examples to avoid
  accidental capture by log handlers that might leak sensitive information
- logging is used for diagnostics and errors in library code with careful
  attention to what is logged

This module helps enforce these patterns and provides utilities for secure logging.
"""

import logging
from collections.abc import Callable
from enum import Enum
from typing import Any


class LogSensitivity(Enum):
    """Classification of log message sensitivity."""

    PUBLIC = "public"
    """Safe for logging - contains no sensitive information."""

    SENSITIVE = "sensitive"
    """Contains sensitive information - should not be logged."""

    REDACTED = "redacted"
    """Should be logged in redacted form only."""


# Items that should NEVER be logged
FORBIDDEN_LOG_PATTERNS = {
    "private key",
    "priv_key",
    "private_key",
    "password",
    "passwd",
    "passphrase",
    "secret",
    "pin",
    "token",
    "key_material",
    "symmetric_key",
    "session_key",
    "master_secret",
}


def secure_log(
    logger_fn: Callable[[str], None], message: str, *, sensitive: bool = False, redact: bool = False
) -> None:
    """
    Securely log a message with sensitivity awareness.

    Args:
        logger_fn: The logging function to call (e.g., logger.debug, logger.error)
        message: The message to log
        sensitive: If True, the message will not be logged at all
        redact: If True, attempt to redact sensitive parts of the message

    Examples:
        >>> logger = logging.getLogger(__name__)
        >>> secure_log(logger.info, "Operation successful", sensitive=False)
        >>> secure_log(logger.debug, "Private key loaded", sensitive=True)  # Not logged
        >>> secure_log(logger.info, "Key size: 2048", redact=True)
    """
    if sensitive:
        # Drop sensitive messages entirely
        return

    if redact:
        message = redact_message(message)

    logger_fn(message)


def redact_message(message: str) -> str:
    """
    Redact potentially sensitive information from a log message.

    This is a basic implementation that replaces common patterns.
    For production use, consider more sophisticated redaction.

    Args:
        message: The message to redact

    Returns:
        The redacted message
    """
    import re

    # Redact things that look like base64 encoded data (common for keys)
    # Base64 can end with = or == padding, which hex never has
    # Check for base64 with padding first (= is not a word char, so use lookahead)
    message = re.sub(r"\b[A-Za-z0-9+/]{40,}={1,2}(?!\w)", "[REDACTED_BASE64]", message)

    # Then check for base64 without padding but with non-hex characters
    # Must contain at least one non-hex character (g-z, G-Z, +, /) to distinguish from hex
    message = re.sub(r"\b(?=.*[g-zG-Z+/])[A-Za-z0-9+/]{40,}\b", "[REDACTED_BASE64]", message)

    # Redact things that look like hex keys (long hex strings - only 0-9a-fA-F)
    # Must have at least 32 characters and ONLY hex characters
    message = re.sub(r"\b[0-9a-fA-F]{32,}\b", "[REDACTED_HEX]", message)

    # Redact password-like patterns
    return re.sub(
        r"(password|passwd|pwd|pin)\s*[:=]\s*\S+", r"\1: [REDACTED]", message, flags=re.IGNORECASE
    )


def check_message_safety(message: str) -> LogSensitivity:
    """
    Check if a message appears to contain sensitive information.

    Args:
        message: The message to check

    Returns:
        LogSensitivity classification
    """
    message_lower = message.lower()

    for pattern in FORBIDDEN_LOG_PATTERNS:
        if pattern in message_lower:
            return LogSensitivity.SENSITIVE

    # Check for long base64 strings (likely encoded keys)
    # Base64 can end with = or == padding, which hex never has
    import re

    if re.search(r"\b[A-Za-z0-9+/]{40,}={1,2}(?!\w)", message):
        return LogSensitivity.REDACTED

    # Base64 without padding but with non-hex characters
    if re.search(r"\b(?=.*[g-zG-Z+/])[A-Za-z0-9+/]{40,}\b", message):
        return LogSensitivity.REDACTED

    # Check for long hex strings (likely keys)
    if re.search(r"\b[0-9a-fA-F]{32,}\b", message):
        return LogSensitivity.REDACTED

    return LogSensitivity.PUBLIC


class SecureLogger:
    """
    A wrapper around Python's logging.Logger that enforces secure logging practices.

    This logger automatically checks messages for sensitive content and handles
    them appropriately based on configuration.

    Example:
        >>> import logging
        >>> base_logger = logging.getLogger(__name__)
        >>> secure = SecureLogger(base_logger)
        >>> secure.info("Certificate loaded successfully")
        >>> secure.debug("Processing key data", sensitive=True)  # Not logged
    """

    def __init__(self, logger: logging.Logger, auto_redact: bool = True, strict: bool = False):
        """
        Initialize SecureLogger.

        Args:
            logger: The underlying Python logger to wrap
            auto_redact: If True, automatically redact suspicious content
            strict: If True, raise exception on attempt to log sensitive data
        """
        self.logger = logger
        self.auto_redact = auto_redact
        self.strict = strict

    def _log(
        self, level: int, message: str, sensitive: bool = False, *args: Any, **kwargs: Any
    ) -> None:
        """Internal logging method with sensitivity checks."""
        if sensitive:
            if self.strict:
                raise ValueError(f"Attempt to log sensitive data: {message[:50]}...")
            return

        # Automatic sensitivity detection
        if self.auto_redact:
            sensitivity = check_message_safety(message)
            if sensitivity == LogSensitivity.SENSITIVE:
                if self.strict:
                    raise ValueError(f"Potentially sensitive data detected: {message[:50]}...")
                return
            if sensitivity == LogSensitivity.REDACTED:
                message = redact_message(message)

        self.logger.log(level, message, *args, **kwargs)

    def debug(self, message: str, sensitive: bool = False, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self._log(logging.DEBUG, message, sensitive, *args, **kwargs)

    def info(self, message: str, sensitive: bool = False, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self._log(logging.INFO, message, sensitive, *args, **kwargs)

    def warning(self, message: str, sensitive: bool = False, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self._log(logging.WARNING, message, sensitive, *args, **kwargs)

    def error(self, message: str, sensitive: bool = False, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self._log(logging.ERROR, message, sensitive, *args, **kwargs)

    def critical(self, message: str, sensitive: bool = False, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self._log(logging.CRITICAL, message, sensitive, *args, **kwargs)


def get_secure_logger(name: str, auto_redact: bool = True, strict: bool = False) -> SecureLogger:
    """
    Get a SecureLogger instance.

    Args:
        name: Logger name (typically __name__)
        auto_redact: Enable automatic redaction
        strict: Enable strict mode (raises exceptions on sensitive data)

    Returns:
        A SecureLogger instance
    """
    base_logger = logging.getLogger(name)
    return SecureLogger(base_logger, auto_redact=auto_redact, strict=strict)


def log_exception_safely(
    logger_fn: Callable[[str], None],
    exc: Exception,
    context: str = "",
    *,
    include_traceback: bool = False,
) -> None:
    """
    Log an exception in a secure manner, avoiding sensitive data leakage.

    This function logs exception information while being careful not to
    expose sensitive data that might be in exception messages (e.g.,
    file paths containing key material, connection strings with passwords).

    Args:
        logger_fn: The logging function to call (e.g., logger.error)
        exc: The exception to log
        context: Additional context about where the exception occurred
        include_traceback: If True, include limited traceback info

    Example:
        >>> try:
        ...     nss.nss_init("invalid_path")
        ... except Exception as e:
        ...     log_exception_safely(logger.error, e, "NSS initialization")
    """
    exc_type = type(exc).__name__
    exc_message = str(exc)

    # Check if exception message appears sensitive
    sensitivity = check_message_safety(exc_message)

    if sensitivity == LogSensitivity.SENSITIVE:
        # Log only the exception type and context
        msg = f"{context}: {exc_type} occurred (details redacted for security)"
    elif sensitivity == LogSensitivity.REDACTED:
        msg = f"{context}: {exc_type}: {redact_message(exc_message)}"
    else:
        # Safe to log
        msg = f"{context}: {exc_type}: {exc_message}" if context else f"{exc_type}: {exc_message}"

    logger_fn(msg)

    if include_traceback:
        # Only include limited traceback info, not full stack
        import traceback

        tb_lines = traceback.format_tb(exc.__traceback__, limit=3)
        # Redact each line of traceback
        for line in tb_lines:
            logger_fn(f"  {redact_message(line.strip())}")


class SecureExceptionHandler:
    """
    Context manager for secure exception handling with logging.

    Use this to wrap code blocks where you want automatic secure
    exception logging without exposing sensitive information.

    Example:
        >>> logger = logging.getLogger(__name__)
        >>> with SecureExceptionHandler(logger, "Certificate loading"):
        ...     cert = nss.Certificate(certdata)
    """

    def __init__(
        self,
        logger: logging.Logger,
        context: str,
        reraise: bool = True,
        log_level: int = logging.ERROR,
    ):
        """
        Initialize the exception handler.

        Args:
            logger: Logger to use for exception logging
            context: Context description for the operation
            reraise: If True, re-raise the exception after logging
            log_level: Logging level to use (default: ERROR)
        """
        self.logger = logger
        self.context = context
        self.reraise = reraise
        self.log_level = log_level

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:

            def logger_fn(msg: str) -> None:
                self.logger.log(self.log_level, msg)

            log_exception_safely(logger_fn, exc_val, self.context)

            return not self.reraise
        return None


# Example usage patterns
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    logger = get_secure_logger(__name__)

    # Safe logging
    logger.info("Certificate validation successful")
    logger.debug("Key size: 2048 bits")

    # Sensitive data - not logged
    logger.debug("Private key: ABC123...", sensitive=True)

    # Auto-redacted
    logger.info("Token value: 1234567890abcdef1234567890abcdef1234567890abcdef")

    # Exception logging examples
    try:
        raise ValueError("Database path: /secret/path/to/keydb contains sensitive info")
    except ValueError as e:
        log_exception_safely(logger.error, e, "Test exception")

    # Context manager example
    base_logger = logging.getLogger("test")
    with SecureExceptionHandler(base_logger, "Demo operation", reraise=False):
        raise RuntimeError("password=secret123")

    print("\nSecure logging examples completed.")
