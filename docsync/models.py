"""Data models for DocSync."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Parameter:
    name: str
    location: Optional[str] = None
    required: bool = False
    schema_type: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ResponseSummary:
    status_code: str
    description: Optional[str] = None


@dataclass
class Endpoint:
    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Parameter] = field(default_factory=list)
    responses: List[ResponseSummary] = field(default_factory=list)

    def sort_key(self):
        return (self.path, self.method)


@dataclass
class SyncReport:
    """MVP report: only 'added' is populated; 'modified'/'removed' stay empty
    (deep diffing against existing docs is out of scope)."""
    added: List[Dict[str, str]] = field(default_factory=list)
    modified: List[Dict[str, str]] = field(default_factory=list)
    removed: List[Dict[str, str]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.added) + len(self.modified) + len(self.removed)
