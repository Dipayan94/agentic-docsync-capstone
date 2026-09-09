"""
Markdown generator module.
"""
from typing import List

from docsync.models import Endpoint


def generate_markdown(endpoints: List[Endpoint]) -> str:
    """
    Generate markdown documentation from endpoints.
    
    Args:
        endpoints: List of Endpoint objects
        
    Returns:
        Markdown string with stable, deterministic output
    """
    lines = []
    
    # Header
    lines.append("# API Documentation")
    lines.append("")
    
    if not endpoints:
        lines.append("No endpoints found.")
        lines.append("")
        return "\n".join(lines)
    
    # Render each endpoint
    for endpoint in endpoints:
        # Method and path
        lines.append(f"## {endpoint.method} {endpoint.path}")
        lines.append("")
        
        # Summary
        if endpoint.summary:
            lines.append(f"**Summary:** {endpoint.summary}")
            lines.append("")
        
        # Description
        if endpoint.description:
            lines.append(f"**Description:** {endpoint.description}")
            lines.append("")
        
        # Parameters
        if endpoint.parameters:
            lines.append("**Parameters:**")
            lines.append("")
            for param in endpoint.parameters:
                req_str = " (required)" if param.required else ""
                type_str = f" - Type: {param.schema_type}" if param.schema_type else ""
                loc_str = f" [{param.location}]" if param.location else ""
                desc_str = f" - {param.description}" if param.description else ""
                lines.append(f"- `{param.name}`{loc_str}{req_str}{type_str}{desc_str}")
            lines.append("")
        else:
            lines.append("**Parameters:** None")
            lines.append("")
        
        # Responses
        if endpoint.responses:
            lines.append("**Responses:**")
            lines.append("")
            for response in endpoint.responses:
                desc_str = f": {response.description}" if response.description else ""
                lines.append(f"- `{response.status_code}`{desc_str}")
            lines.append("")
        else:
            lines.append("**Responses:** None")
            lines.append("")
    
    return "\n".join(lines)
