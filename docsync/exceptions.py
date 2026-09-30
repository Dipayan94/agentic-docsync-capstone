"""Exceptions for DocSync, mapped to the locked exit code contract."""


class DocSyncError(Exception):
    """Operational error (exit code 1): I/O, permissions, unexpected failures."""


class ValidationError(Exception):
    """Validation failure (exit code 2): invalid schema JSON/shape or malformed markers."""
