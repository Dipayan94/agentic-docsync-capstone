"""Render synchronized Markdown and independent change reports."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .diff_engine import endpoints_equal
from .markdown_parser import ENDPOINT_END, ENDPOINT_START, MANAGED_END, MANAGED_START, encode_endpoint
from .models import Changes, Document, DocumentBlock, Endpoint


def _identity(endpoint: Endpoint) -> Tuple[str, str]:
    return endpoint.path, endpoint.method.upper()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


def _endpoint_body(endpoint: Endpoint, deprecated: bool = False) -> str:
    """Render only endpoint details represented in the OpenAPI model."""
    heading = f"### {endpoint.method.upper()} {endpoint.path}"
    if deprecated:
        heading += " [DEPRECATED]"
    lines = [heading, ""]
    if endpoint.summary:
        lines.extend([f"**{endpoint.summary}**", ""])
    if endpoint.description:
        lines.extend([endpoint.description, ""])
    if endpoint.tags:
        lines.extend(["Tags: " + ", ".join(endpoint.tags), ""])
    if endpoint.parameters:
        lines.extend(["#### Parameters", "", "| Name | Location | Type | Required | Description |",
                      "| --- | --- | --- | --- | --- |"])
        for parameter in endpoint.parameters:
            lines.append("| {} | {} | {} | {} | {} |".format(
                _cell(parameter.name), _cell(parameter.location), _cell(parameter.type),
                "yes" if parameter.required else "no", _cell(parameter.description)))
        lines.append("")
        for parameter in endpoint.parameters:
            if parameter.schema is not None:
                lines.extend([f"##### {parameter.name} ({parameter.location}) Schema", "",
                              "```json", _json(parameter.schema), "```", ""])
    if endpoint.request_body is not None:
        lines.extend(["#### Request Body", "", "```json", _json(endpoint.request_body), "```", ""])
    if endpoint.responses:
        lines.extend(["#### Responses", "", "| Status | Description |",
                      "| --- | --- |"])
        for code, response in sorted(endpoint.responses.items()):
            lines.append(f"| {_cell(code)} | {_cell(response.description)} |")
        lines.append("")
        for code, response in sorted(endpoint.responses.items()):
            if response.content:
                for media_type, media in sorted(response.content.items()):
                    lines.extend([f"##### {code} {media_type}", "", "```json", _json(media), "```", ""])
            elif response.schema is not None:
                lines.extend([f"##### {code} Schema", "", "```json", _json(response.schema), "```", ""])
    if endpoint.examples:
        lines.extend(["#### Examples", ""])
        for name, example in sorted(endpoint.examples.items()):
            lines.extend([f"##### {name}", "", "```json", _json(example), "```", ""])
    return "\n".join(lines).rstrip() + "\n"


def _endpoint_block(endpoint: Endpoint, deprecated: bool = False) -> str:
    body = _endpoint_body(endpoint, deprecated)
    return (f"{ENDPOINT_START}\n<!-- docsync:endpoint:metadata {encode_endpoint(endpoint)} -->\n"
            f"{body}{ENDPOINT_END}\n")


def _single_line_marker(block: DocumentBlock, marker: str) -> bool:
    return block.raw_markdown.rstrip("\r\n") == marker


def render_document(document: Document, current_endpoints: List[Endpoint], changes: Changes) -> str:
    """Merge current endpoints into source-preserving document blocks."""
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    for index, block in enumerate(document.blocks):
        if _single_line_marker(block, MANAGED_START):
            start_index = index
        elif _single_line_marker(block, MANAGED_END):
            end_index = index

    if start_index is None or end_index is None:
        prefix = "".join(block.raw_markdown for block in document.blocks)
        suffix = ""
        custom_blocks: List[DocumentBlock] = []
        existing: Dict[Tuple[str, str], DocumentBlock] = {}
    else:
        prefix = "".join(block.raw_markdown for block in document.blocks[:start_index])
        suffix = "".join(block.raw_markdown for block in document.blocks[end_index + 1:])
        custom_blocks = [block for block in document.blocks[start_index + 1:end_index]
                         if block.endpoint is None]
        existing = {_identity(block.endpoint): block for block in document.blocks
                    if block.endpoint is not None}

    ordered_current = sorted(current_endpoints, key=lambda endpoint: (endpoint.path, endpoint.method.upper()))
    rendered = []
    current_keys = {_identity(endpoint) for endpoint in ordered_current}
    for endpoint in ordered_current:
        block = existing.get(_identity(endpoint))
        if block is not None and endpoints_equal(block.endpoint, endpoint):
            rendered.append(block.raw_markdown)
        else:
            rendered.append(_endpoint_block(endpoint))
    deprecated = sorted((endpoint for endpoint in changes.removed
                         if _identity(endpoint) not in current_keys),
                        key=lambda endpoint: (endpoint.path, endpoint.method.upper()))
    rendered.extend(_endpoint_block(endpoint, deprecated=True) for endpoint in deprecated)
    custom = "".join(block.raw_markdown for block in custom_blocks)

    if start_index is None or end_index is None:
        separator = "" if not prefix or prefix.endswith(("\n", "\r")) else "\n"
        prefix += separator
        prefix += f"{MANAGED_START}\n"
        ending = f"{MANAGED_END}\n"
        return prefix + "".join(rendered) + custom + ending + suffix
    start_block = document.blocks[start_index].raw_markdown
    end_block = document.blocks[end_index].raw_markdown
    return prefix + start_block + "".join(rendered) + custom + end_block + suffix


def _endpoint_reference(endpoint: Endpoint) -> Dict[str, str]:
    return {"path": endpoint.path, "method": endpoint.method.upper()}


def format_report(changes: Changes, report_format: str = "markdown",
                  metadata: Optional[Dict[str, Any]] = None) -> str:
    """Format an independent Markdown or JSON report with timestamp/version data."""
    if report_format not in {"json", "markdown"}:
        raise ValueError("Report format must be 'json' or 'markdown'")
    details = dict(metadata or {})
    timestamp = details.get("timestamp") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report = {
        "timestamp": timestamp,
        "schema_version": details.get("schema_version", ""),
        "schema_title": details.get("schema_title", ""),
        "openapi_version": details.get("openapi_version", ""),
        "added": [_endpoint_reference(endpoint) for endpoint in changes.added],
        "modified": [{"from": _endpoint_reference(old), "to": _endpoint_reference(new)}
                     for old, new in changes.modified],
        "removed": [_endpoint_reference(endpoint) for endpoint in changes.removed],
    }
    if report_format == "json":
        return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    lines = ["# DocSync Report", "", f"- Timestamp: {timestamp}",
             f"- Schema: {report['schema_title']} (version {report['schema_version']}; OpenAPI {report['openapi_version']})", ""]
    for label in ("added", "modified", "removed"):
        entries = report[label]
        lines.extend([f"## {label.title()} ({len(entries)})", ""])
        if not entries:
            lines.extend(["- None", ""])
            continue
        for entry in entries:
            if label == "modified":
                source, target = entry["from"], entry["to"]
                lines.append(f"- `{source['method']} {source['path']}` updated")
            else:
                lines.append(f"- `{entry['method']} {entry['path']}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
