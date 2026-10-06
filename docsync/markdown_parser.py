"""Parse DocSync-managed Markdown while retaining every source block exactly."""

import base64
import binascii
import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

from .models import Document, DocumentBlock, Endpoint, Parameter, Response, ValidationError

MANAGED_START = "<!-- docsync:managed:start -->"
MANAGED_END = "<!-- docsync:managed:end -->"
ENDPOINT_START = "<!-- docsync:endpoint:start -->"
ENDPOINT_END = "<!-- docsync:endpoint:end -->"
METADATA_PATTERN = re.compile(r"^<!-- docsync:endpoint:metadata ([A-Za-z0-9+/=]+) -->$")
_RESERVED_MARKERS = {MANAGED_START, MANAGED_END, ENDPOINT_START, ENDPOINT_END}
_METADATA_PREFIX = "<!-- docsync:endpoint:metadata"


def encode_endpoint(endpoint: Endpoint) -> str:
    """Encode complete endpoint metadata for an invisible Markdown comment."""
    value = {
        "path": endpoint.path,
        "method": endpoint.method.upper(),
        "summary": endpoint.summary,
        "description": endpoint.description,
        "parameters": [parameter.__dict__ for parameter in endpoint.parameters],
        "request_body": endpoint.request_body,
        "responses": {key: response.__dict__ for key, response in endpoint.responses.items()},
        "tags": endpoint.tags,
        "examples": endpoint.examples,
    }
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return base64.b64encode(payload.encode("utf-8")).decode("ascii")


def _endpoint_from_metadata(payload: str) -> Endpoint:
    try:
        value = json.loads(base64.b64decode(payload, validate=True).decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"Invalid endpoint metadata: {error}") from error
    if not isinstance(value, dict):
        raise ValidationError("Endpoint metadata must decode to a JSON object")
    required = {"path", "method", "summary", "description", "parameters",
                "request_body", "responses", "tags", "examples"}
    if set(value) != required:
        raise ValidationError("Endpoint metadata has missing or unknown fields")
    if not isinstance(value["path"], str) or not value["path"].startswith("/"):
        raise ValidationError("Endpoint metadata path must be an absolute API path")
    if not isinstance(value["method"], str) or not value["method"].isalpha():
        raise ValidationError("Endpoint metadata method must contain letters only")
    if not all(isinstance(value[key], str) for key in ("summary", "description")):
        raise ValidationError("Endpoint metadata summary and description must be strings")
    if not isinstance(value["parameters"], list) or not isinstance(value["responses"], dict):
        raise ValidationError("Endpoint metadata parameters/responses have invalid types")
    if not isinstance(value["tags"], list) or not all(isinstance(tag, str) for tag in value["tags"]):
        raise ValidationError("Endpoint metadata tags must be strings")
    if not isinstance(value["examples"], dict):
        raise ValidationError("Endpoint metadata examples must be an object")
    try:
        parameters = [Parameter(**item) for item in value["parameters"]]
        responses = {key: Response(**item) for key, item in value["responses"].items()}
        if any(not isinstance(item, dict) for item in value["parameters"]):
            raise TypeError("parameter entries must be objects")
        if any(not isinstance(item, dict) for item in value["responses"].values()):
            raise TypeError("response entries must be objects")
        for key, response in responses.items():
            if response.status_code != key:
                raise ValueError("response key must match its status_code")
        return Endpoint(
            path=value["path"], method=value["method"].upper(), summary=value["summary"],
            description=value["description"], parameters=parameters,
            request_body=value["request_body"], responses=responses,
            tags=value["tags"], examples=value["examples"],
        )
    except (TypeError, ValueError) as error:
        raise ValidationError(f"Invalid endpoint metadata fields: {error}") from error


def _line_table(content: str) -> Tuple[List[str], List[int]]:
    lines = content.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    return lines, offsets


def _marker(line: str) -> str:
    return line.rstrip("\r\n")


def parse_document_content(content: str) -> Document:
    """Parse Markdown content into ordered exact-source blocks and warnings."""
    lines, offsets = _line_table(content)
    markers = [(index, _marker(line)) for index, line in enumerate(lines)]
    for index, marker in markers:
        if marker.startswith("<!-- docsync:") and marker not in _RESERVED_MARKERS:
            if not (marker.startswith(_METADATA_PREFIX) and METADATA_PATTERN.fullmatch(marker)):
                raise ValidationError(f"Malformed DocSync marker on Markdown line {index + 1}")
    managed_starts = [index for index, marker in markers if marker == MANAGED_START]
    managed_ends = [index for index, marker in markers if marker == MANAGED_END]
    endpoint_markers = [(index, marker) for index, marker in markers if marker in _RESERVED_MARKERS]

    if not managed_starts and not managed_ends:
        if any(marker in {ENDPOINT_START, ENDPOINT_END} or marker.startswith(_METADATA_PREFIX)
               for _, marker in markers):
            raise ValidationError("Endpoint markers require a managed Markdown region")
        return Document(blocks=[DocumentBlock(content)])
    if len(managed_starts) != 1 or len(managed_ends) != 1:
        raise ValidationError("Markdown must contain exactly one managed start/end marker pair")
    start_index, end_index = managed_starts[0], managed_ends[0]
    if start_index >= end_index:
        raise ValidationError("Managed Markdown end marker must follow its start marker")
    if any(index < start_index or index > end_index for index, marker in endpoint_markers
           if marker in {ENDPOINT_START, ENDPOINT_END}):
        raise ValidationError("Endpoint markers must be inside the managed Markdown region")

    blocks: List[DocumentBlock] = []
    warnings: List[str] = []

    def add_raw(first_line: int, after_line: int, label: str) -> None:
        raw = content[offsets[first_line]:offsets[after_line]]
        if raw:
            blocks.append(DocumentBlock(raw))
            if raw.strip() and label == "inside the managed region":
                warnings.append(
                    f"Unrecognized nonblank Markdown retained {label} starting at line {first_line + 1}"
                )

    add_raw(0, start_index, "before the managed region")
    if any(_marker(lines[index]).startswith(_METADATA_PREFIX) for index in range(start_index)):
        raise ValidationError("Endpoint metadata markers must be inside a complete endpoint block")
    blocks.append(DocumentBlock(content[offsets[start_index]:offsets[start_index + 1]]))
    cursor = start_index + 1
    index = cursor
    identities = set()
    while index < end_index:
        if _marker(lines[index]) != ENDPOINT_START:
            if _marker(lines[index]) in {ENDPOINT_END, MANAGED_START, MANAGED_END}:
                raise ValidationError(f"Unexpected DocSync marker on Markdown line {index + 1}")
            if _marker(lines[index]).startswith(_METADATA_PREFIX):
                raise ValidationError(f"Orphan endpoint metadata on Markdown line {index + 1}")
            index += 1
            continue
        add_raw(cursor, index, "inside the managed region")
        if index + 1 >= end_index:
            raise ValidationError(f"Incomplete endpoint block on Markdown line {index + 1}")
        metadata_match = METADATA_PATTERN.fullmatch(_marker(lines[index + 1]))
        if metadata_match is None:
            raise ValidationError(f"Missing or malformed endpoint metadata on Markdown line {index + 2}")
        end_candidates = [candidate for candidate in range(index + 2, end_index)
                          if _marker(lines[candidate]) == ENDPOINT_END]
        nested = [candidate for candidate in range(index + 2, end_index)
                  if _marker(lines[candidate]) == ENDPOINT_START]
        if not end_candidates or (nested and nested[0] < end_candidates[0]):
            raise ValidationError(f"Incomplete or nested endpoint block on Markdown line {index + 1}")
        block_end = end_candidates[0]
        if any(_marker(lines[candidate]).startswith(_METADATA_PREFIX)
               for candidate in range(index + 2, block_end)):
            raise ValidationError(f"Duplicate endpoint metadata on Markdown line {index + 1}")
        endpoint = _endpoint_from_metadata(metadata_match.group(1))
        identity = (endpoint.path, endpoint.method.upper())
        if identity in identities:
            raise ValidationError(f"Duplicate managed endpoint identity: {identity[1]} {identity[0]}")
        identities.add(identity)
        blocks.append(DocumentBlock(content[offsets[index]:offsets[block_end + 1]], endpoint))
        cursor = block_end + 1
        index = cursor

    add_raw(cursor, end_index, "inside the managed region")
    if any(_marker(lines[index]).startswith(_METADATA_PREFIX) for index in range(end_index + 1, len(lines))):
        raise ValidationError("Endpoint metadata markers must be inside a complete endpoint block")
    blocks.append(DocumentBlock(content[offsets[end_index]:offsets[end_index + 1]]))
    add_raw(end_index + 1, len(lines), "after the managed region")
    return Document(blocks=blocks, parse_warnings=warnings)


def parse_document(file_path: str) -> Document:
    """Read and parse an existing Markdown file without newline translation."""
    try:
        with Path(file_path).open("r", encoding="utf-8", newline="") as source:
            content = source.read()
    except UnicodeDecodeError as error:
        raise ValidationError(f"Markdown is not UTF-8 text in {file_path}: {error}") from error
    return parse_document_content(content)
