# DocSync

DocSync synchronizes an existing local Markdown document from an OpenAPI 3.0 or
3.1 JSON file. It uses only the Python standard library at runtime and does not
import the FastAPI application or access network resources.

```text
python -m docsync.cli sync --schema openapi.json --docs docs/api.md \
  --output docs/api.md --format markdown
```

The `--docs` option and its input file are required. Omitting the option is a
usage/validation error (exit 2); a named file that does not exist is an
operational error (exit 1). To start with no existing documentation, provide an
existing empty Markdown file. `--output` may be the same file as `--docs`; it
must not overwrite the read-only schema input. The complete result is rendered
before an atomic replacement. `--dry-run` performs no output write.

The synchronization report is written to stdout in Markdown by default or JSON
with `--format json`. Synchronized documentation is written only to `--output`.
Diagnostics and recoverable Markdown warnings go to stderr. `--verbose` enables
detailed diagnostics. Exit codes are 0 for success or dry-run, 1 for operational
or file errors, and 2 for usage or validation failures.

## Managed Markdown

DocSync uses one region delimited by these exact standalone lines:

```markdown
<!-- docsync:managed:start -->
<!-- docsync:managed:end -->
```

Each generated endpoint has endpoint-start, base64 JSON metadata, rendered
content, and endpoint-end comments inside the region. The metadata preserves
all schema-derived fields for later comparison. Do not edit those marker or
metadata lines. Markdown outside the region is preserved exactly. Nonblank
unrecognized content inside a valid region is retained, reported as a warning,
and placed after endpoint sections. Malformed or ambiguous markers and invalid
endpoint metadata are validation failures; no output is written.

New and modified endpoint sections are rendered from the schema. Unchanged
sections retain their exact source Markdown. Removed endpoints remain in the
managed region with `[DEPRECATED]`. A method change is reported as one removal
and one addition. Object key order does not count as a change; text and array
order do.

Only in-document JSON Pointer references such as
`#/components/schemas/Item` are resolved. Remote and separate local-file
references are rejected without access. YAML, schema caches, and missing-docs
defaults are not supported.
