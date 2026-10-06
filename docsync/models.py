"""Typed data contracts shared by the DocSync pipeline."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class ValidationError(ValueError):
    """Raised when schema or managed Markdown input violates its contract."""


@dataclass
class Parameter:
    """An OpenAPI operation parameter."""

    name: str
    location: str
    type: str
    required: bool
    description: str = ""
    schema: Optional[Dict[str, Any]] = None


@dataclass
class Response:
    """An OpenAPI operation response."""

    status_code: str
    description: str
    schema: Optional[Dict[str, Any]] = None
    content: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Endpoint:
    """Normalized API operation data used by parsing, comparison, and rendering."""

    path: str
    method: str
    summary: str = ""
    description: str = ""
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Response] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    examples: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Schema:
    """Parsed OpenAPI metadata and normalized endpoint collection."""

    title: str
    version: str
    endpoints: List[Endpoint]
    openapi_version: str = ""
    description: str = ""


@dataclass
class DocumentBlock:
    """A source-ordered Markdown block, optionally recognized as an endpoint."""

    raw_markdown: str
    endpoint: Optional[Endpoint] = None


@dataclass
class Document:
    """Source-preserving Markdown document with recognized endpoint records."""

    blocks: List[DocumentBlock]
    parse_warnings: List[str] = field(default_factory=list)

    @property
    def endpoints(self) -> List[Endpoint]:
        """Return recognized endpoints in their original document order."""
        return [block.endpoint for block in self.blocks if block.endpoint is not None]


@dataclass
class Changes:
    """Endpoint changes between the supplied document and current schema."""

    added: List[Endpoint] = field(default_factory=list)
    modified: List[Tuple[Endpoint, Endpoint]] = field(default_factory=list)
    removed: List[Endpoint] = field(default_factory=list)
