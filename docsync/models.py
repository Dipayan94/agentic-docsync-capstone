"""
Data models for DocsSync.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Parameter:
    """Represents an API parameter."""
    name: str
    location: Optional[str] = None  # query, path, header, cookie
    required: bool = False
    schema_type: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ResponseSummary:
    """Represents an API response."""
    status_code: str
    description: Optional[str] = None


@dataclass
class Endpoint:
    """Represents an API endpoint."""
    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Parameter] = field(default_factory=list)
    responses: List[ResponseSummary] = field(default_factory=list)

    def __lt__(self, other):
        """Support sorting by path then method."""
        if self.path != other.path:
            return self.path < other.path
        return self.method < other.method


@dataclass
class SyncReport:
    """Represents a sync operation report."""
    timestamp: str
    endpoints_total: int
    endpoints: List[Dict[str, str]] = field(default_factory=list)
