# Architecture Document

**Feature:** Automated API Documentation Sync  
**Based On:** `docs/sdlc/requirements.md`  
**Source PRD:** PRD-001: Automated API Documentation Sync (Confluence page `3112961`, Draft, High priority)  
**Date:** 2026-10-07  
**Agent:** architecture-agent  
**Stage:** 2 - Architecture

---

## Architecture Overview

Docsync is an offline Python CLI that reads an OpenAPI 3.0 or 3.1 JSON file and an existing Markdown document, computes endpoint-level changes, then renders the synchronized document and a human-readable or JSON report. It does not import or change the FastAPI application, contact external services, or modify the schema. Its parser, Markdown boundary handling, differ, renderer, and CLI have separate responsibilities so they can be tested independently.

---

## Module Structure

### Proposed Modules

```
docsync/
├── __init__.py              # Package initialization
├── models.py                # Typed schema, endpoint, document, and change records
├── parser.py                # OpenAPI 3.0/3.1 JSON parsing and local $ref resolution
├── markdown_parser.py       # Endpoint extraction and custom-content boundaries
├── generator.py             # Markdown merge/rendering and sync report formatting
├── diff_engine.py           # Schema-to-document endpoint change detection
├── cli.py                   # Required sync CLI and orchestration
└── utils.py                 # Local file handling, atomic writes, and logging

tests/
├── test_parser.py           # Parser unit tests
├── test_markdown_parser.py  # Markdown section and preservation tests
├── test_generator.py        # Generator unit tests
├── test_diff_engine.py     # Diff engine unit tests
├── test_cli.py              # CLI integration tests
└── conftest.py              # Test fixtures
```

### Module Relationships
The CLI invokes both input parsers, passes their endpoint records to the difference engine, then sends the changes and preserved document parts to the renderer. `models.py` is shared by the domain modules; `utils.py` supports local file operations.

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI (main entry)                      │
└──────────────┬──────────────────┬──────────────┬──────────────┘
               │                  │              │
               ▼                  ▼              ▼
         ┌─────────┐        ┌──────────┐   ┌────────────┐
         │ Parser  │        │Generator │   │ DiffEngine │
         └────┬────┘        └────┬─────┘   └─────┬──────┘
              │                  │              │
              └──────────┬───────┴──────────────┘
                         ▼
                    ┌────────────┐
                    │  Models    │
                    │  + Utils   │
                    └────────────┘
```

### Module Descriptions

#### Supporting module: **models.py** (Data Layer)
Defines lightweight data models using Python dataclasses.

**Responsibility:**
 Define core data structures (Endpoint, Parameter, Response, Schema, Document, DocumentBlock, and Changes)
- Provide type hints for entire system
- Enable serialization/deserialization

**Key Classes:**
```python
@dataclass
class Parameter:
    name: str
    location: str
    type: str
    required: bool
    description: str = ""
    schema: Optional[dict] = None

@dataclass
class Response:
    status_code: int
    description: str
    schema: Optional[dict] = None

@dataclass
class Endpoint:
    path: str
    method: str
    summary: str
    description: str
    parameters: List[Parameter]
    request_body: Optional[dict]
    responses: Dict[int, Response]
    tags: List[str]
    examples: Dict[str, object]

@dataclass
class Schema:
    title: str
    version: str
    endpoints: List[Endpoint]

@dataclass
class DocumentBlock:
    raw_markdown: str
    endpoint: Optional[Endpoint] = None

@dataclass
class Document:
    blocks: List[DocumentBlock]
    parse_warnings: List[str]

    @property
    def endpoints(self) -> List[Endpoint]:
        return [block.endpoint for block in self.blocks if block.endpoint is not None]

@dataclass
class Changes:
    added: List[Endpoint]
    modified: List[tuple[Endpoint, Endpoint]]  # (old, new)
    removed: List[Endpoint]
```

**Dependencies:** None (stdlib only)  
**Size:** ~150 lines

---

#### 1. **OpenAPI Parser** (`parser.py`)
Parses and normalizes OpenAPI 3.0 and 3.1 JSON schemas.

**Responsibility:**
- Read JSON files and parse OpenAPI structure
- Extract endpoint metadata, request bodies, responses, examples, and nested schemas
- Resolve local JSON Pointer `$ref` values, including nested references, with cycle detection
- Validate schema structure and supported OpenAPI version
- Handle errors gracefully

**Key Functions:**
```python
def parse_openapi(file_path: str) -> Schema:
    """Parse OpenAPI JSON file and return normalized Schema object."""
    
def extract_endpoints(openapi_dict: dict) -> List[Endpoint]:
    """Extract endpoints from OpenAPI paths object."""
    
def extract_parameters(operation: dict) -> List[Parameter]:
    """Extract path, query, header, and cookie parameters."""
    
def extract_responses(responses: dict) -> Dict[int, Response]:
    """Extract response definitions from operation."""
    
def normalize_endpoint(path: str, method: str, operation: dict) -> Endpoint:
    """Normalize a single operation into Endpoint object."""
```

**Error Handling:**
- Validate JSON structure before processing
- Check required OpenAPI fields and support versions 3.0 and 3.1
- Resolve references within the input document; do not fetch external references
- Provide clear error messages for malformed schemas
- Reject invalid references and reference cycles as validation errors

**Dependencies:** json (stdlib), models.py  
**Size:** ~200 lines

---

#### 2. **Markdown Parser and Section Manager** (`markdown_parser.py`)
Parses existing Markdown into an ordered `Document`. Each `DocumentBlock` retains its exact source Markdown; blocks recognized as managed endpoint sections also carry a parsed `Endpoint`. Unmanaged, malformed, or ambiguous content remains as raw Markdown without an endpoint, and parser warnings are exposed through `Document.parse_warnings`. The exact marker/heading convention remains a planning decision.

**Responsibilities:**
- Identify endpoint headings and metadata using the agreed Markdown convention
- Separate generated sections from surrounding headers, footers, and custom sections
- Leave malformed or ambiguous existing content untouched and report it for user attention

**Key Function:**
```python
def parse_document(file_path: str) -> Document:
    """Parse Markdown into ordered source-preserving blocks and endpoint records."""
```

**Dependencies:** Python standard library and internal models only.

#### 4. **Markdown Renderer and Report Formatter** (`generator.py`)
Generates endpoint Markdown, merges it into the parsed document, and formats the sync report.

**Responsibility:**
- Render endpoint path/method, parameters, request body, response schemas, and examples when present
- Update or add managed sections while preserving non-managed content
- Retain removed endpoints and mark them `[DEPRECATED]`
- Format added, modified, and removed/deprecated changes as Markdown or JSON with timestamp/version

**Key Functions:**
```python
def render_document(document: Document, current_endpoints: List[Endpoint], changes: Changes) -> str:
    """Merge rendered endpoint sections into preserved Markdown content."""
    
def generate_endpoint_markdown(endpoint: Endpoint) -> str:
    """Generate markdown section for a single endpoint."""
    
def format_report(changes: Changes, report_format: str, metadata: dict) -> str:
    """Format a human-readable or JSON synchronization report."""
    
def format_parameters(parameters: List[Parameter]) -> str:
    """Format parameters table in markdown."""
    
def format_responses(responses: Dict[int, Response]) -> str:
    """Format responses table in markdown."""
```

Examples and optional descriptions are rendered only when present in the schema; the generator does not invent API details.

**Dependencies:** json, pathlib (stdlib), models.py  
**Size:** ~300 lines

---

#### 3. **Difference Engine** (`diff_engine.py`)
Detects differences between schema endpoints and endpoint records parsed from existing Markdown.

**Responsibility:**
- Index schema and `documented.endpoints` by `(path, method)`
- Identify added, modified, removed endpoints
- Compare descriptions, parameters, request bodies, response schemas, examples, and nested referenced schema data
- Keep removed endpoint records for deprecation rather than deletion

**Key Functions:**
```python
def detect_changes(documented: Document, current: List[Endpoint]) -> Changes:
    """Compare documented endpoint data with current schema endpoints."""
    
def endpoints_equal(ep1: Endpoint, ep2: Endpoint) -> bool:
    """Check if two endpoints are equivalent."""
    
def parameters_equal(p1: Parameter, p2: Parameter) -> bool:
    """Check if two parameters are equivalent."""
    
def find_endpoint(path: str, method: str, endpoints: List[Endpoint]) -> Optional[Endpoint]:
    """Find endpoint by path and method."""
```

**Change Detection Logic:**
- Added: Endpoint in schema but not in existing documentation
- Removed: Documented endpoint absent from schema; retained and marked deprecated
- Modified: Same path+method with changed schema-derived documentation fields

**Dependencies:** models.py  
**Size:** ~150 lines

---

#### 5. **CLI and File Orchestrator** (`cli.py`)
Implements the required `sync` command and orchestrates the workflow.

**Responsibility:**
- Parse command-line arguments
- Orchestrate workflow
- Provide user feedback and logging
- Handle exit codes and error reporting

**Key Functions:**
```python
def main() -> int:
    """Main entry point for CLI."""
    
def sync_command(args: argparse.Namespace) -> int:
    """Run the schema-to-Markdown sync workflow."""
    
def log_error(message: str) -> None:
    """Log error with context."""
    
def log_success(message: str) -> None:
    """Log success message."""
```

**Command and options:**
```
docsync sync --schema <path> --docs <path> --output <path>
    [--dry-run] [--format json|markdown] [--verbose]
```

**Error Handling:**
- File not found → Exit 1, clear message
- Invalid JSON/schema or document validation failure → Exit 2, actionable message
- Permission denied → Exit 1, permission message
- Other operational I/O failure → Exit 1
- Successful sync or dry-run → Exit 0

**Dependencies:** argparse (stdlib), json (stdlib), pathlib (stdlib), models.py, parser.py, generator.py, diff_engine.py  
**Size:** ~250 lines

---

#### Supporting module: **utils.py** (Shared Utilities)
Shared utility functions.

**Responsibility:**
- File path operations
- Logging/output formatting
- Common string operations

**Key Functions:**
```python
def ensure_dir(path: str) -> None:
    """Create directory if not exists."""
    
def safe_read_file(path: str) -> str:
    """Read file with error handling."""
    
def safe_write_file(path: str, content: str) -> None:
    """Write file atomically with error handling."""
    
def format_output(title: str, content: str) -> str:
    """Format output for display."""
    
def human_readable_size(byte_size: int) -> str:
    """Convert bytes to human readable format."""
```

**Dependencies:** json (stdlib), pathlib (stdlib)  
**Size:** ~80 lines

---

## Data Flow

```text
docsync sync --schema openapi.json --docs docs/api/api.md --output docs/api/api.md
                |
                v
CLI validates arguments and local input/output paths
                |
                +--> OpenAPI parser: JSON -> validated schema + normalized endpoints
                +--> Markdown parser: source -> Document (ordered source blocks, endpoints, warnings)
                |
                v
Diff engine: compare Document.endpoints with schema endpoints by (path, method)
                |
                v
Renderer: merge updated endpoint sections; retain and deprecate removed sections
                |
                +--> Report formatter: stdout as Markdown or JSON, with timestamp/version
                +--> Atomic output write (omitted for --dry-run)
```

The schema input is read-only. The `--docs` source is read without mutation; synchronized Markdown is written to `--output`. If source and output resolve to the same path, write only after parsing and rendering succeed, using a temporary file in the destination directory followed by an atomic replace where supported.

## Key Design Decisions

### 1. Dependency Minimalism
**Decision:** Use Python standard-library JSON, CLI, and file APIs; do not add a runtime dependency for docsync.

**Justification:**
- Keeps package lightweight
- Reduces installation complexity
- Easier to maintain and deploy
- Fewer security vulnerabilities
- Works in offline environments

**Trade-off:** Structural OpenAPI validation and Markdown boundary parsing are implemented locally; scope is limited to the requirements and the agreed Markdown convention.

---

### 2. **Dataclass Models**
**Decision:** Use Python `@dataclass` for all data structures.

**Justification:**
- Built-in to Python 3.9+
- Provides type safety without complexity
- Auto-generates `__init__`, `__repr__`, `__eq__`
- Easy to serialize/deserialize
- Clean syntax

**Trade-off:** Dataclasses do not validate values at runtime; the parser performs explicit structural validation at the input boundary.

---

### 3. **Documentation as the Comparison Baseline**
**Decision:** Compare current schema endpoints with endpoint data parsed from the supplied Markdown; do not introduce a schema cache.

**Justification:** The required CLI has schema, docs, and output paths, while the PRD requires preservation and updates of the existing documentation. An extra cache file is not specified and would add state that can drift.

---

### 4. **Markdown Generation via Templates**
**Decision:** Use Python string templates for markdown generation.

**Justification:**
- No extra dependencies (no Jinja2)
- Predictable output
- Easy to customize
- Fast execution

**Trade-off:** Less powerful than templating engines; for simple docs generation this is sufficient.

---

### 5. **Separation of Concerns**
**Decision:** Strict module boundaries (Parser, Generator, DiffEngine, CLI).

**Justification:**
- Each module has single responsibility
- Testable in isolation
- Reusable components
- Easy to extend or replace

**Trade-off:** Slightly more boilerplate, but better maintainability.

---

### 6. **Atomic Writes**
**Decision:** Render the complete result before writing and atomically replace the single output file when supported.

**Justification:**
- Prevents partial updates that break documentation
- Clear success/failure semantics
- No data loss or corruption

**Trade-off:** Atomic replacement behavior depends on the local filesystem; use a temporary file in the destination directory.

---

### 7. **CLI as Orchestrator**
**Decision:** CLI module handles workflow orchestration, not business logic.

**Justification:**
- Business logic stays in domain modules
- CLI focuses on user interaction
- Easy to test CLI separately from logic
- Can be reused by other UIs (future: API endpoint)

**Trade-off:** Additional layer, but cleaner overall design.

---

## Error Handling Strategy

### File-Level Errors

| Error | Source | Handling | Exit |
|-------|--------|----------|------|
| File not found or permission denied | Parser, CLI | Name the path and actionable cause | 1 |
| Invalid JSON | Parser | Report JSON parse location and cause | 2 |
| Invalid OpenAPI structure/version/reference | Parser | Report validation error before writing output | 2 |
| Invalid or ambiguous managed Markdown | Markdown parser | Report the location; do not overwrite source | 2 |
| Output write failure | File utility | Preserve existing destination; report I/O cause | 1 |

### Logic-Level Errors

| Error | Source | Handling | Exit |
|-------|--------|----------|------|
| Missing required schema field | Parser | Reject as validation failure; do not guess/default | 2 |
| Unsupported external reference | Parser | Reject without network access | 2 |
| Removed documented endpoint | DiffEngine/Generator | Retain section and add `[DEPRECATED]` | 0 |
| Dry run | CLI | Compute and report changes; perform no output write | 0 |

### CLI-Level Errors

| Error | Source | Handling | Exit |
|-------|--------|----------|------|
| Missing argument or invalid option | CLI | Show usage for the required `sync` command | 2 |
| Operational I/O or unexpected processing error | CLI | Clear message on stderr; verbose traceback/logging only with `--verbose` | 1 |

### Logging Strategy

```python
# Log levels
ERROR   - Fatal operational issues (exit 1)
WARNING - Recoverable notes that do not compromise correctness
INFO    - Concise progress when --verbose is enabled
DEBUG   - Detailed local processing context when --verbose is enabled
```

---

## Dependencies & Interfaces

### External Dependencies

| Package | Version | Purpose | Type |
|---------|---------|---------|------|
| json | stdlib | Parse OpenAPI JSON | Required |
| pathlib | stdlib | File path operations | Required |
| dataclasses | stdlib | Data models | Required |
| argparse | stdlib | CLI parsing | Required |
| typing | stdlib | Type hints | Required |
| logging | stdlib | Verbose diagnostics | Required |

### Internal Module Interfaces

```python
# Parser and document interfaces
from docsync.parser import parse_openapi
from docsync.markdown_parser import parse_document

schema = parse_openapi("openapi.json")
document = parse_document("docs/api/api.md")
# Returns ordered source-preserving blocks, parsed endpoints, and parse warnings

# Diff and rendering interfaces
from docsync.diff_engine import detect_changes
from docsync.generator import render_document, format_report

changes = detect_changes(document, schema.endpoints)
markdown = render_document(document, schema.endpoints, changes)
# Format the report as "json" or "markdown"; CLI owns final file/output handling

# CLI interface
from docsync.cli import main

exit_code = main()
# Returns: 0 (success), 1 (operational error), or 2 (validation failure)
```

---

## Integration with Existing Application

- `main.py` creates a FastAPI application that serves its generated OpenAPI schema at `/openapi.json`. The app also depends on Redis for its item operations, but docsync does not need Redis or an import of `main.py`.
- Export or retrieve the OpenAPI JSON locally and pass its file path to the CLI. This keeps synchronization offline and leaves the running app and schema unchanged.
- `models.py` defines the app's Pydantic `ItemPayload`; it is application data, not a docsync model dependency.
- The CLI accepts caller-selected docs/output paths, typically `docs/api/api.md`.

## Architecture Validation Considerations

### Testing Strategy

- **Unit tests:** Test each module in isolation with fixtures
- **Integration tests:** Test CLI commands end-to-end
- **Fixtures:** Sample openapi.json files (small, medium, large)
- **Coverage goal:** greater than 80% unit-test coverage as required by NFR-3

### Performance Targets

| Operation | Required target |
|-----------|------------------|
| Parse up to 500 endpoints | < 2 seconds |
| Generate documentation | < 3 seconds |
| Total synchronization | < 5 seconds |

### Debugging Notes

- `--verbose` enables detailed diagnostics; normal reports remain concise
- Send diagnostics/errors to stderr and the requested report format to stdout
- Performance targets should be measured with representative 500-endpoint fixtures during verification

---

## Module Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────┐
│                   docsync/                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  cli.py  (Entry Point & Orchestration)             │   │
│  │                                                     │   │
│  │  Command: sync (--dry-run, --format, --verbose)   │   │
│  └────────┬──────────────────┬───────────┬────────────┘   │
│           │                  │           │                 │
│      ┌────▼────┐       ┌─────▼──┐   ┌───▼────────┐        │
│      │parser   │       │generator│   │diff_engine │       │
│      │         │       │         │   │            │       │
│      │Parse    │       │Generate │   │Detect      │       │
│      │OpenAPI  │       │Markdown │   │Changes     │       │
│      │         │       │Validate │   │            │       │
│      └────┬────┘       └────┬────┘   └─────┬──────┘       │
│           │                 │              │               │
│           └─────────────┬───┴──────────────┘               │
│                         │                                  │
│                     ┌───▼────────┐                         │
│                     │ models.py   │                         │
│                     │             │                         │
│                     │ Endpoint    │                         │
│                     │ Parameter   │                         │
│                     │ Response    │                         │
│                     │ Schema      │                         │
│                     │ Changes     │                         │
│                     └─────┬───────┘                         │
│                           │                                │
│                     ┌─────▼────────┐                       │
│                     │ utils.py      │                       │
│                     │               │                       │
│                     │ File ops      │                       │
│                     │ Formatting    │                       │
│                     └───────────────┘                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Dependencies (Inbound):
  models.py     ← used by: parser, generator, diff_engine, cli
  utils.py      ← used by: parser, generator, cli
  parser.py     ← used by: cli
  generator.py  ← used by: cli
  diff_engine   ← used by: cli
  cli.py        ← entry point, runs all others
```

---

## Requirements Coverage

| Requirement | Architectural coverage |
|---|---|
| FR-1 | OpenAPI 3.0/3.1 JSON parser, validation, nested schemas, local references |
| FR-2 | Markdown parser identifies endpoint sections and preserves surrounding custom content |
| FR-3 | Diff engine detects additions, modifications, and removals by path/method and compares requested fields |
| FR-4 | Renderer emits endpoint details/examples when available and retains removals as deprecated |
| FR-5 | Report formatter emits changes, timestamp, and version in Markdown or JSON |
| FR-6 | CLI implements the required `sync` arguments/options and `0`/`1`/`2` exit codes |
| NFR-1 | Indexed in-memory processing and the specified 500-endpoint timing targets |
| NFR-2 | Input validation, actionable errors, dry-run, and atomic output replacement |
| NFR-3 | Modular boundaries, verbose diagnostics, and greater-than-80% unit coverage target |
| NFR-4 | Python 3.9+, OpenAPI 3.0/3.1, and local FastAPI schema consumption |

## Decisions and Assumptions

### Architectural decisions

- Endpoint identity is `(path, method)`; compare descriptions, parameters, request bodies, responses, and nested schemas.
- Preserve non-managed Markdown and mark removed endpoint sections `[DEPRECATED]` rather than deleting them.
- Keep all inputs local; resolve in-document JSON Pointer references and never fetch remote references.
- Treat schema and docs as read-only inputs, report to stdout, and write only the selected output path. Dry-run performs no output write.
- Use the schema's `info.version` when present and an ISO-8601 UTC timestamp in reports. Include the tool version if available.
- Prefer standard-library parsing, CLI, and output with a defined Markdown structure; no new runtime dependency is proposed.

### Assumptions and unresolved questions

- The PRD does not define Markdown structure or managed-region markers. The proposal assumes generated endpoint sections can use stable markers and a documented heading/table convention. The precise convention and how to adopt existing unmarked docs require design confirmation.
- The PRD does not specify whether a missing docs file is a valid first run or a validation error. Avoid silent replacement; settle the exact behavior during design review.
- External `$ref` behavior is unspecified. This design rejects external references to uphold offline operation; confirm whether bundled external files must be supported.
- “Version information” has no specified source beyond available schema metadata. Confirm whether `info.version` plus tool version satisfies reporting expectations.
- Examples are rendered when present in the schema; no examples are invented. Confirm whether another source is expected when the schema has none.
- A Markdown library is mentioned as a dependency option, but none is specified. This proposal uses a constrained Markdown convention and stdlib; confirm whether arbitrary Markdown input must be parsed.

## Next Stage

This architecture artifact is ready for the separate Design Review stage. No design review, implementation, or commit was performed as part of this Stage 2 task.

## Traceability

- Requirements: `docs/sdlc/requirements.md`
- Source PRD: PRD-001, Confluence page `3112961` (Draft, High priority)
- Next stage: Design Review
