"""
Data models for docsync: OpenAPI schema, endpoints, changes, and errors.

This module defines all data structures used throughout the docsync pipeline.
Type-safe dataclasses prevent runtime errors and document the data contract.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Literal
from enum import Enum


class ChangeType(str, Enum):
    """Types of schema changes detected by diff engine."""
    NEW = "new"
    REMOVED = "removed"
    MODIFIED = "modified"


@dataclass
class Parameter:
    """HTTP request/response parameter or field."""
    name: str
    param_type: str  # 'query', 'path', 'header', 'body'
    required: bool = False
    description: str = ""
    schema_type: str = "string"  # 'string', 'integer', 'boolean', 'array', etc.

    def __str__(self) -> str:
        required_marker = "[required]" if self.required else "[optional]"
        return f"{self.name} ({self.schema_type}) {required_marker} - {self.description}"


@dataclass
class Response:
    """HTTP response schema."""
    status_code: str  # '200', '404', '500', etc.
    description: str = ""
    content_type: str = "application/json"
    schema_description: str = ""

    def __str__(self) -> str:
        return f"{self.status_code}: {self.description}"


@dataclass
class Endpoint:
    """API endpoint metadata extracted from OpenAPI schema."""
    method: str  # 'GET', 'POST', 'PUT', 'DELETE', 'PATCH'
    path: str  # '/items/{item_id}', '/items', etc.
    summary: str = ""
    description: str = ""
    parameters: List[Parameter] = field(default_factory=list)
    responses: List[Response] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.method:6} {self.path:40} - {self.summary}"

    def identifier(self) -> str:
        """Unique identifier for this endpoint (method + path)."""
        return f"{self.method} {self.path}".lower()


@dataclass
class Schema:
    """Parsed OpenAPI schema containing all endpoints."""
    title: str = "API Documentation"
    version: str = "1.0.0"
    description: str = ""
    base_url: str = ""
    endpoints: List[Endpoint] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.title} v{self.version} ({len(self.endpoints)} endpoints)"

    def endpoint_count(self) -> int:
        """Return count of endpoints in schema."""
        return len(self.endpoints)

    def endpoints_by_path(self) -> Dict[str, List[Endpoint]]:
        """Group endpoints by path for documentation organization."""
        grouped = {}
        for ep in self.endpoints:
            if ep.path not in grouped:
                grouped[ep.path] = []
            grouped[ep.path].append(ep)
        return grouped


@dataclass
class Change:
    """Represents a single change detected between schema versions."""
    change_type: ChangeType
    endpoint: Endpoint
    details: str = ""

    def __str__(self) -> str:
        return f"[{self.change_type.upper()}] {self.endpoint.method} {self.endpoint.path}: {self.details}"


@dataclass
class ValidationError:
    """Structured error for schema validation failures."""
    message: str
    code: str = "VALIDATION_ERROR"  # e.g., 'MISSING_FIELD', 'INVALID_TYPE', 'MALFORMED_JSON'
    context: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"
