"""Markdown generation from OpenAPI endpoints."""

from typing import List
from docsync.openapi import Endpoint

BEGIN_MARKER = "<!-- DOCSYNC:BEGIN GENERATED -->"
END_MARKER = "<!-- DOCSYNC:END GENERATED -->"


def render_markdown(endpoints: List[Endpoint]) -> str:
    """
    Render endpoints as a markdown documentation block with markers.
    
    Args:
        endpoints: List of Endpoint objects
        
    Returns:
        Markdown string including begin/end markers
    """
    lines = [
        "# API Documentation",
        "",
        BEGIN_MARKER,
        "",
    ]
    
    for endpoint in endpoints:
        # Heading for each endpoint
        lines.append(f"## {endpoint.method} {endpoint.path}")
        lines.append("")
        
        if endpoint.summary:
            lines.append(f"**Summary:** {endpoint.summary}")
            lines.append("")
        
        if endpoint.description:
            lines.append(f"**Description:** {endpoint.description}")
            lines.append("")
        
        # Parameters section
        if endpoint.parameters:
            lines.append("### Parameters")
            lines.append("")
            for param in endpoint.parameters:
                if isinstance(param, dict):
                    name = param.get("name", "unknown")
                    location = param.get("in", "")
                    required = param.get("required", False)
                    desc = param.get("description", "")
                    req_str = " (required)" if required else ""
                    lines.append(f"- **{name}** ({location}){req_str}: {desc}")
            lines.append("")
        
        # Responses section
        if endpoint.responses:
            lines.append("### Responses")
            lines.append("")
            for status_code, response_obj in sorted(endpoint.responses.items()):
                if isinstance(response_obj, dict):
                    desc = response_obj.get("description", "")
                    lines.append(f"- **{status_code}**: {desc}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    lines.append(END_MARKER)
    
    return "\n".join(lines)
