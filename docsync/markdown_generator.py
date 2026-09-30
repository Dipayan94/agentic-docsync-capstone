"""Render a deterministic markdown template for endpoints, wrapped in DocSync markers."""
from typing import List

from docsync.models import Endpoint

BEGIN_MARKER = "<!-- DOCSYNC:BEGIN GENERATED -->"
END_MARKER = "<!-- DOCSYNC:END GENERATED -->"


def _render_endpoint(endpoint: Endpoint) -> List[str]:
    lines = [f"## {endpoint.method} {endpoint.path}", ""]

    if endpoint.summary:
        lines += [f"**Summary:** {endpoint.summary}", ""]
    if endpoint.description:
        lines += [f"**Description:** {endpoint.description}", ""]

    if endpoint.parameters:
        lines.append("**Parameters:**")
        lines.append("")
        for param in endpoint.parameters:
            req = " (required)" if param.required else ""
            loc = f" [{param.location}]" if param.location else ""
            ptype = f" - type: {param.schema_type}" if param.schema_type else ""
            desc = f" - {param.description}" if param.description else ""
            lines.append(f"- `{param.name}`{loc}{req}{ptype}{desc}")
        lines.append("")
    else:
        lines += ["**Parameters:** None", ""]

    if endpoint.responses:
        lines.append("**Responses:**")
        lines.append("")
        for resp in endpoint.responses:
            desc = f": {resp.description}" if resp.description else ""
            lines.append(f"- `{resp.status_code}`{desc}")
        lines.append("")
    else:
        lines += ["**Responses:** None", ""]

    return lines


def generate_markdown_body(endpoints: List[Endpoint]) -> str:
    """Generate the endpoint documentation body (without markers)."""
    if not endpoints:
        return "# API Documentation\n\nNo endpoints found.\n"

    lines = ["# API Documentation", ""]
    for endpoint in endpoints:
        lines += _render_endpoint(endpoint)

    return "\n".join(lines).rstrip() + "\n"


def generate_markdown(endpoints: List[Endpoint]) -> str:
    """Generate the endpoint documentation body wrapped in the locked DocSync markers."""
    body = generate_markdown_body(endpoints)
    return f"{BEGIN_MARKER}\n{body}{END_MARKER}\n"
