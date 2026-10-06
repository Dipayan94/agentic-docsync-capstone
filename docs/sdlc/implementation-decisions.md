# Implementation Decisions

**Based On:** `docs/sdlc/requirements.md`, revised `docs/sdlc/architecture.md`, approved `docs/sdlc/design-review.md`, and `docs/sdlc/impl-plan.md`  
**Date:** 2026-10-07  
**Stage:** 5 - Implementation

This note records the behavior choices required by TASK-002. It does not change the approved architecture or requirements.

## P1: Markdown Warnings and Validation Failures

The Markdown parser returns a `Document` with deterministic warnings for nonblank, unrecognized content inside a well-formed managed region. Such content remains raw and is reproduced byte-for-byte after generated endpoint blocks; synchronization may continue.

Malformed or ambiguous DocSync structure is a validation failure (CLI exit 2): only one managed start/end pair is allowed; the pair must be ordered and balanced; endpoint start/end and metadata markers must be complete; metadata must decode to a valid endpoint; and endpoint identities `(path, method)` must be unique. A failure prevents output writing. A warning never licenses dropping source text.

Examples:

- Accepted with a warning: a complete managed region contains a hand-written paragraph between generated endpoint blocks. The paragraph is retained exactly and emitted after generated endpoint blocks.
- Rejected: a managed start marker has no end marker, or two endpoint metadata blocks identify `GET /items`. The parser raises a validation error and the CLI does not write output.
- Preserved without a warning: arbitrary Markdown outside the managed region, including an unmarked document with no generated sections.

## P2: Offline Reference Scope

Only JSON Pointer references beginning with `#` and resolving within the input JSON document are supported. Their fragments are percent-decoded and JSON Pointer escapes (`~1`, `~0`) are resolved recursively; invalid pointers and cycles are validation failures. Remote URLs and references to separate local files are both out of scope and rejected without access.

Examples:

- Accepted: `"$ref": "#/components/schemas/Item"` resolves against the loaded JSON object.
- Rejected: `"$ref": "https://example.test/item.json#/Item"` and `"$ref": "./schemas/item.json"`; neither triggers a network or filesystem read.

## P3: Managed Markdown and Comparison

The managed region is delimited by the exact standalone lines `<!-- docsync:managed:start -->` and `<!-- docsync:managed:end -->`. Each generated endpoint block has an exact standalone `<!-- docsync:endpoint:start -->` line, one `<!-- docsync:endpoint:metadata BASE64_JSON -->` line, rendered Markdown, and an exact standalone `<!-- docsync:endpoint:end -->` line. The base64 payload is UTF-8 JSON for the complete endpoint model; it is comparison metadata, not user-facing API content.

Content outside those delimiters is unmanaged and remains byte-for-byte in its original order. In-region nonblank content that is not a valid endpoint block is retained byte-for-byte, warned about, and emitted after managed endpoint blocks. Whitespace-only separators are retained. With no managed region, the complete existing document is unmanaged; the managed region is appended, adding only the newline needed to keep its start marker on a separate line. Generated endpoints are ordered by path and then uppercase method; retained deprecated endpoints follow, in the same order. An unchanged endpoint block is emitted exactly as sourced; a changed/new endpoint is rendered from the current schema, and a removed endpoint is retained and rendered with `[DEPRECATED]`.

Endpoint identity is the exact path plus case-normalized HTTP method. Thus changing a method is one removal and one addition. Comparison ignores JSON object key ordering, normalizes method case, and otherwise compares values exactly: strings and array order are significant, including parameter order. No prose, examples, or API details are inferred from custom Markdown.

Examples:

- Accepted: `GET /items` and `get /items` have the same identity; reordering keys inside a schema object alone does not mark the endpoint modified.
- Classified as changes: `GET /items` becoming `POST /items` is a removal plus an addition; changing parameter order or description text is a modification.
- Preserved: a custom `## Notes` section before or after the managed markers is emitted exactly where it was. A nonblank paragraph inside the markers is retained exactly, warned about, and placed after the generated endpoint blocks.

## Missing `--docs` Input

The `--docs` option is required. Omitting the option is a CLI usage/validation failure (exit 2); a supplied path that does not exist is an operational file error (exit 1), as specified by the architecture error table. Neither case is treated as an empty document or creates a new source document. To start from no prior API docs, provide an existing empty Markdown file; synchronization writes only to `--output`.

Examples:

- Rejected with exit 2: `docsync sync --schema openapi.json --output api.md` (`--docs` omitted).
- Rejected with exit 1: `docsync sync --schema openapi.json --docs missing.md --output api.md` (input file absent).
- Accepted: `--docs empty.md` where `empty.md` exists and is empty; generated documentation is written to the requested output after successful validation and rendering.
