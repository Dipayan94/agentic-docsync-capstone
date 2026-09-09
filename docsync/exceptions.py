"""
Custom exceptions for DocsSync.
"""


class DocSyncError(Exception):
    """Base exception for operational errors (exit code 1)."""
    pass


class ValidationError(Exception):
    """Exception for validation failures (exit code 2)."""
    pass
