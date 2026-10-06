"""Compare documented endpoint metadata with a current OpenAPI endpoint set."""

from typing import List, Tuple

from .markdown_parser import encode_endpoint
from .models import Changes, Document, Endpoint


def _identity(endpoint: Endpoint) -> Tuple[str, str]:
    return endpoint.path, endpoint.method.upper()


def endpoints_equal(first: Endpoint, second: Endpoint) -> bool:
    """Compare all schema-derived endpoint fields with normalized object keys."""
    return encode_endpoint(first) == encode_endpoint(second)


def _index(endpoints: List[Endpoint], label: str) -> dict:
    indexed = {}
    for endpoint in endpoints:
        identity = _identity(endpoint)
        if identity in indexed:
            raise ValueError(f"Duplicate {label} endpoint: {identity[1]} {identity[0]}")
        indexed[identity] = endpoint
    return indexed


def detect_changes(documented: Document, current: List[Endpoint]) -> Changes:
    """Classify additions, modifications, and removals by exact path and method."""
    old = _index(documented.endpoints, "documented")
    new = _index(current, "schema")
    changes = Changes()
    for identity in sorted(new):
        endpoint = new[identity]
        if identity not in old:
            changes.added.append(endpoint)
        elif not endpoints_equal(old[identity], endpoint):
            changes.modified.append((old[identity], endpoint))
    for identity in sorted(old):
        if identity not in new:
            changes.removed.append(old[identity])
    return changes
