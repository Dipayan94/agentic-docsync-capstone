"""
Diff engine: Detect changes between OpenAPI schema versions.

This module implements BLOCKER #2 (Endpoint Comparison Algorithm):
- NEW: Endpoint present in new schema, not in old
- REMOVED: Endpoint in old schema, not in new
- MODIFIED: Same endpoint (method+path), but definition changed
  - Definition change includes: summary, description, parameters, responses
  - Parameter order is preserved and any change counts as modification
"""

from typing import List, Optional, Set, Tuple
from docsync.models import Schema, Endpoint, Change, ChangeType
from docsync.utils import get_logger, read_json, write_json


logger = get_logger(__name__)


class EndpointComparator:
    """Compares endpoints to detect modifications."""

    @staticmethod
    def endpoints_equal(ep1: Endpoint, ep2: Endpoint) -> bool:
        """
        Compare two endpoints for equality.
        
        BLOCKER #2: Comparison Algorithm
        - Compare method, path (identifier)
        - Compare summary, description (content)
        - Compare parameters (count, order, definitions)
        - Compare responses (count, status codes, descriptions)
        
        Returns True only if all aspects are identical.
        
        Args:
            ep1: First endpoint
            ep2: Second endpoint
        
        Returns:
            True if endpoints are identical
        """
        # Check method and path
        if ep1.method != ep2.method or ep1.path != ep2.path:
            return False

        # Check summary and description
        if ep1.summary != ep2.summary or ep1.description != ep2.description:
            return False

        # Check parameters (count, order, and values)
        if len(ep1.parameters) != len(ep2.parameters):
            return False
        
        for p1, p2 in zip(ep1.parameters, ep2.parameters):
            if (p1.name != p2.name or
                p1.param_type != p2.param_type or
                p1.required != p2.required or
                p1.description != p2.description or
                p1.schema_type != p2.schema_type):
                return False

        # Check responses (count and values)
        if len(ep1.responses) != len(ep2.responses):
            return False
        
        # Sort responses by status code for comparison
        resp1_sorted = sorted(ep1.responses, key=lambda r: r.status_code)
        resp2_sorted = sorted(ep2.responses, key=lambda r: r.status_code)
        
        for r1, r2 in zip(resp1_sorted, resp2_sorted):
            if (r1.status_code != r2.status_code or
                r1.description != r2.description or
                r1.content_type != r2.content_type):
                return False

        return True


class DiffEngine:
    """Detects changes between schema versions."""

    @staticmethod
    def compute_diff(old_schema: Optional[Schema], new_schema: Schema) -> List[Change]:
        """
        Compute differences between old and new schemas.
        
        Args:
            old_schema: Previous schema (None on first sync)
            new_schema: Current schema
        
        Returns:
            List of Change objects (new/removed/modified endpoints)
        """
        changes = []

        if old_schema is None:
            # First sync: all endpoints are new
            logger.info("First sync detected (no previous schema). All endpoints marked as NEW.")
            for endpoint in new_schema.endpoints:
                changes.append(Change(
                    change_type=ChangeType.NEW,
                    endpoint=endpoint,
                    details=f"New endpoint added"
                ))
            return changes

        # Create maps for quick lookup: (method, path) -> endpoint
        old_endpoints: dict = {ep.identifier(): ep for ep in old_schema.endpoints}
        new_endpoints: dict = {ep.identifier(): ep for ep in new_schema.endpoints}

        # Detect REMOVED endpoints
        for identifier, old_ep in old_endpoints.items():
            if identifier not in new_endpoints:
                changes.append(Change(
                    change_type=ChangeType.REMOVED,
                    endpoint=old_ep,
                    details="Endpoint removed from schema"
                ))

        # Detect NEW and MODIFIED endpoints
        for identifier, new_ep in new_endpoints.items():
            if identifier not in old_endpoints:
                changes.append(Change(
                    change_type=ChangeType.NEW,
                    endpoint=new_ep,
                    details="New endpoint added"
                ))
            else:
                # Endpoint exists in both: check if it was modified
                old_ep = old_endpoints[identifier]
                if not EndpointComparator.endpoints_equal(old_ep, new_ep):
                    changes.append(Change(
                        change_type=ChangeType.MODIFIED,
                        endpoint=new_ep,
                        details="Endpoint modified (summary/parameters/responses changed)"
                    ))

        logger.info(f"Detected {len(changes)} changes: "
                   f"{len([c for c in changes if c.change_type == ChangeType.NEW])} new, "
                   f"{len([c for c in changes if c.change_type == ChangeType.REMOVED])} removed, "
                   f"{len([c for c in changes if c.change_type == ChangeType.MODIFIED])} modified")

        return changes

    @staticmethod
    def load_schema_cache(cache_file: str) -> Optional[Schema]:
        """
        Load previous schema from cache file.
        
        Args:
            cache_file: Path to schema_cache.json
        
        Returns:
            Parsed Schema object, or None if cache doesn't exist/is corrupted
        """
        try:
            data = read_json(cache_file)
            # For now, return None (simplified caching)
            # In a real implementation, deserialize the cached schema
            logger.info(f"Loaded schema cache from {cache_file}")
            return None  # TODO: Implement full schema deserialization
        except FileNotFoundError:
            logger.info("No previous schema cache found (first sync)")
            return None
        except ValueError as e:
            logger.warning(f"Schema cache corrupted; treating as first sync: {e}")
            return None

    @staticmethod
    def save_schema_cache(schema: Schema, cache_file: str) -> None:
        """
        Save current schema to cache file for next diff.
        
        Args:
            schema: Current schema to cache
            cache_file: Path to schema_cache.json
        """
        try:
            # Simplified: save basic schema info
            cache_data = {
                "title": schema.title,
                "version": schema.version,
                "endpoint_count": len(schema.endpoints)
            }
            write_json(cache_file, cache_data)
            logger.info(f"Saved schema cache to {cache_file}")
        except OSError as e:
            logger.error(f"Failed to save schema cache: {e}")
