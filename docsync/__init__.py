"""
docsync - CLI tool for generating and syncing API documentation from OpenAPI schemas.
"""

__version__ = "0.1.0"


class ValidationError(Exception):
    """Raised when validation fails (schema or marker issues)."""
    pass
