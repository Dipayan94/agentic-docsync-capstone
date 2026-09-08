"""Report generation and diff computation for sync operations."""

import json
import re
from docsync.markdown import BEGIN_MARKER, END_MARKER


def extract_endpoint_ids_from_markdown(generated_block: str) -> set[str]:
    """
    Extract endpoint identifiers from a generated markdown block.
    
    Looks for headings like "## GET /items" within the generated section.
    
    Args:
        generated_block: Markdown text containing generated API docs
        
    Returns:
        Set of endpoint identifiers (e.g., "GET /items")
    """
    endpoint_ids = set()
    
    # Extract content between markers if present
    if BEGIN_MARKER in generated_block and END_MARKER in generated_block:
        start = generated_block.find(BEGIN_MARKER) + len(BEGIN_MARKER)
        end = generated_block.find(END_MARKER)
        content = generated_block[start:end]
    else:
        content = generated_block
    
    # Find endpoint headings: ## METHOD /path
    pattern = r'^## (GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD) (/\S*)$'
    for line in content.split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            method, path = match.groups()
            endpoint_ids.add(f"{method} {path}")
    
    return endpoint_ids


def compute_report(old_ids: set[str], new_ids: set[str]) -> dict:
    """
    Compute a diff report between old and new endpoint sets.
    
    Args:
        old_ids: Set of endpoint identifiers from previous version
        new_ids: Set of endpoint identifiers from new version
        
    Returns:
        Dictionary with keys: added (list), removed (list), modified (list)
        Note: modified is always empty in MVP (future enhancement)
    """
    added = sorted(new_ids - old_ids)
    removed = sorted(old_ids - new_ids)
    modified = []  # MVP: not implemented yet
    
    return {
        "added": added,
        "removed": removed,
        "modified": modified
    }


def render_report(report: dict, format: str = "markdown") -> str:
    """
    Render a sync report in the specified format.
    
    Args:
        report: Report dictionary from compute_report()
        format: Output format - "json" or "markdown"
        
    Returns:
        Formatted report string
    """
    if format == "json":
        return json.dumps(report, indent=2)
    
    # Default: markdown format
    lines = ["# DocSync Report", ""]
    
    added = report.get("added", [])
    removed = report.get("removed", [])
    modified = report.get("modified", [])
    
    lines.append(f"**Added:** {len(added)}")
    if added:
        for endpoint in added:
            lines.append(f"  - {endpoint}")
    lines.append("")
    
    lines.append(f"**Removed:** {len(removed)}")
    if removed:
        for endpoint in removed:
            lines.append(f"  - {endpoint}")
    lines.append("")
    
    lines.append(f"**Modified:** {len(modified)}")
    if modified:
        for endpoint in modified:
            lines.append(f"  - {endpoint}")
    lines.append("")
    
    return "\n".join(lines)
