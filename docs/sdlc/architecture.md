# Architecture Design

**Date:** September 10, 2026  
**Agent:** architecture-agent  
**Stage:** 2 - Architecture  
**Source:** docs/sdlc/requirements.md

---

## Executive Summary

The **Automated Documentation Sync** system is designed as a lightweight, modular CLI tool that synchronizes OpenAPI 3.1.0 schema with markdown documentation. The architecture focuses on simplicity and maintainability by decomposing the problem into four core components:

1. **Parser** - Reads and normalizes OpenAPI JSON schemas
2. **Generator** - Produces markdown documentation with built-in validation
3. **Diff Engine** - Compares schema versions to identify changes
4. **CLI** - Provides user interface and orchestrates the workflow

This design leverages Python stdlib as much as possible (json, argparse, pathlib) to minimize external dependencies while maintaining clean separation of concerns. The system operates entirely offline with no external service dependencies.

---

## Module Structure

### Proposed Modules

```
docsync/
├── __init__.py              # Package initialization
├── models.py                # Data models (lightweight)
├── parser.py                # OpenAPI schema parsing
├── generator.py             # Markdown generation + validation
├── diff_engine.py           # Schema change detection
├── cli.py                   # CLI interface & orchestration
└── utils.py                 # Shared utilities (path handling, logging)

tests/
├── test_parser.py           # Parser unit tests
├── test_generator.py        # Generator unit tests
├── test_diff_engine.py      # Diff engine unit tests
├── test_cli.py              # CLI integration tests
└── conftest.py              # Test fixtures
```

### Module Relationships

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

#### 1. **models.py** (Data Layer)
Defines lightweight data models using Python dataclasses.

**Responsibility:**
- Define core data structures (Endpoint, Parameter, Response, Schema, Changes)
- Provide type hints for entire system
- Enable serialization/deserialization

**Key Classes:**
```python
@dataclass
class Parameter:
    name: str
    type: str
    required: bool
    description: str = ""

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

@dataclass
class Schema:
    title: str
    version: str
    endpoints: List[Endpoint]

@dataclass
class Changes:
    added: List[Endpoint]
    modified: List[tuple[Endpoint, Endpoint]]  # (old, new)
    removed: List[Endpoint]
```

**Dependencies:** None (stdlib only)  
**Size:** ~150 lines

---

#### 2. **parser.py** (Input Layer)
Parses and normalizes OpenAPI 3.1.0 JSON schemas.

**Responsibility:**
- Read JSON files and parse OpenAPI structure
- Extract and normalize endpoint metadata
- Validate schema structure
- Handle errors gracefully

**Key Functions:**
```python
def parse_openapi(file_path: str) -> Schema:
    """Parse OpenAPI JSON file and return normalized Schema object."""
    
def extract_endpoints(openapi_dict: dict) -> List[Endpoint]:
    """Extract endpoints from OpenAPI paths object."""
    
def extract_parameters(operation: dict, param_type: str) -> List[Parameter]:
    """Extract parameters from operation (path, query, header, body)."""
    
def extract_responses(responses: dict) -> Dict[int, Response]:
    """Extract response definitions from operation."""
    
def normalize_endpoint(path: str, method: str, operation: dict) -> Endpoint:
    """Normalize a single operation into Endpoint object."""
```

**Error Handling:**
- Validate JSON structure before processing
- Check required OpenAPI fields
- Provide clear error messages for malformed schemas
- Log warnings for missing optional fields

**Dependencies:** json (stdlib), models.py  
**Size:** ~200 lines

---

#### 3. **generator.py** (Processing + Output Layer)
Generates markdown documentation from parsed schema.

**Responsibility:**
- Convert Endpoint objects to markdown format
- Organize documentation logically (by tags/paths)
- Validate completeness of generated docs
- Handle special cases (arrays, nested objects, examples)

**Key Functions:**
```python
def generate_docs(schema: Schema, output_dir: str) -> None:
    """Generate complete markdown documentation from schema."""
    
def generate_endpoint_markdown(endpoint: Endpoint) -> str:
    """Generate markdown section for a single endpoint."""
    
def generate_toc(endpoints: List[Endpoint]) -> str:
    """Generate table of contents."""
    
def validate_documentation(endpoints: List[Endpoint], output_dir: str) -> ValidationResult:
    """Validate that all endpoints have documentation."""
    
def format_parameters(parameters: List[Parameter]) -> str:
    """Format parameters table in markdown."""
    
def format_responses(responses: Dict[int, Response]) -> str:
    """Format responses table in markdown."""
```

**Validation Rules:**
- Every endpoint must have a description
- Every parameter must have a type and description
- Every response must have a description
- Output file must be valid markdown
- Check for broken internal links

**Dependencies:** json, pathlib (stdlib), models.py  
**Size:** ~300 lines

---

#### 4. **diff_engine.py** (Change Detection Layer)
Detects and reports differences between schema versions.

**Responsibility:**
- Compare two Schema objects
- Identify added, modified, removed endpoints
- Detect changes to parameters and responses
- Generate change summary

**Key Functions:**
```python
def detect_changes(old_schema: Schema, new_schema: Schema) -> Changes:
    """Compare two schemas and return changes."""
    
def endpoints_equal(ep1: Endpoint, ep2: Endpoint) -> bool:
    """Check if two endpoints are equivalent."""
    
def parameters_equal(p1: Parameter, p2: Parameter) -> bool:
    """Check if two parameters are equivalent."""
    
def generate_change_report(changes: Changes) -> str:
    """Generate human-readable change summary."""
    
def find_endpoint(path: str, method: str, endpoints: List[Endpoint]) -> Optional[Endpoint]:
    """Find endpoint by path and method."""
```

**Change Detection Logic:**
- Added: Endpoint in new_schema but not in old_schema (by path+method)
- Removed: Endpoint in old_schema but not in new_schema
- Modified: Same path+method but different summary/description/parameters/responses

**Dependencies:** models.py  
**Size:** ~150 lines

---

#### 5. **cli.py** (User Interface Layer)
Command-line interface for all operations.

**Responsibility:**
- Parse command-line arguments
- Orchestrate workflow
- Provide user feedback and logging
- Handle exit codes and error reporting

**Key Functions:**
```python
def main() -> int:
    """Main entry point for CLI."""
    
def parse_command(args: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    
def cmd_parse(args) -> int:
    """parse <schema-file> - Parse schema and show info."""
    
def cmd_generate(args) -> int:
    """generate <schema-file> <output-dir> - Generate markdown."""
    
def cmd_diff(args) -> int:
    """diff <old-schema> <new-schema> - Show schema changes."""
    
def cmd_sync(args) -> int:
    """sync <schema-file> <docs-dir> - Full sync operation."""
    
def cmd_validate(args) -> int:
    """validate <docs-dir> - Validate documentation completeness."""
    
def log_error(message: str) -> None:
    """Log error with context."""
    
def log_success(message: str) -> None:
    """Log success message."""
```

**Supported Commands:**
```
docsync parse <schema-file>
    ├─ Output: Schema summary (# endpoints, versions, etc.)
    └─ Exit: 0=success, 1=error

docsync generate <schema-file> <output-dir>
    ├─ Output: Generated markdown files in output-dir/
    └─ Exit: 0=success, 1=error

docsync diff <old-schema> <new-schema>
    ├─ Output: Change report (added/modified/removed)
    └─ Exit: 0=no changes, 1=has changes, 2=error

docsync sync <schema-file> <docs-dir>
    ├─ Steps: parse → compare old vs new → generate → validate → report
    ├─ Output: Updated markdown + sync report
    └─ Exit: 0=success, 1=error

docsync validate <docs-dir>
    ├─ Output: Validation report
    └─ Exit: 0=valid, 1=invalid, 2=error
```

**Error Handling:**
- File not found → Exit 1, clear message
- Invalid JSON → Exit 1, JSON parse error
- Permission denied → Exit 1, permission message
- Validation failure → Exit 1, detailed report

**Dependencies:** argparse (stdlib), json (stdlib), pathlib (stdlib), models.py, parser.py, generator.py, diff_engine.py  
**Size:** ~250 lines

---

#### 6. **utils.py** (Shared Utilities)
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

### Scenario 1: Parse Command
```
User: docsync parse openapi.json
  │
  ▼
CLI.parse_command()
  │
  ▼
Parser.parse_openapi(openapi.json)
  │
  ├─ Read JSON file
  ├─ Validate structure
  ├─ Extract endpoints
  └─ Return Schema object
  │
  ▼
CLI.cmd_parse()
  │
  ├─ Display: # endpoints, versions, summary
  └─ Exit 0
```

### Scenario 2: Generate Command
```
User: docsync generate openapi.json docs/
  │
  ▼
CLI.cmd_generate()
  │
  ├─ Parser.parse_openapi(openapi.json) → Schema
  │
  ├─ Generator.generate_docs(Schema, output_dir)
  │  ├─ For each endpoint:
  │  │  └─ Generate markdown section
  │  ├─ Create toc.md
  │  └─ Write all files to docs/
  │
  ├─ Generator.validate_documentation()
  │  └─ Check completeness
  │
  └─ Display: X files created, validation results
     Exit 0
```

### Scenario 3: Sync Command (Main Workflow)
```
User: docsync sync openapi.json docs/
  │
  ▼
CLI.cmd_sync()
  │
  ├─ Step 1: Parse new schema
  │  └─ Parser.parse_openapi(openapi.json) → new_schema
  │
  ├─ Step 2: Detect changes (if old docs exist)
  │  ├─ Parser.parse_openapi(docs/schema_cache.json) → old_schema
  │  └─ DiffEngine.detect_changes(old_schema, new_schema) → Changes
  │
  ├─ Step 3: Generate updated documentation
  │  └─ Generator.generate_docs(new_schema, docs/)
  │
  ├─ Step 4: Validate
  │  └─ Generator.validate_documentation(docs/)
  │
  ├─ Step 5: Report changes
  │  ├─ DiffEngine.generate_change_report(Changes)
  │  └─ Display: X added, Y modified, Z removed
  │
  └─ Exit 0
```

### Scenario 4: Diff Command
```
User: docsync diff old-schema.json new-schema.json
  │
  ▼
CLI.cmd_diff()
  │
  ├─ Parser.parse_openapi(old-schema.json) → old_schema
  ├─ Parser.parse_openapi(new-schema.json) → new_schema
  │
  ├─ DiffEngine.detect_changes(old_schema, new_schema) → Changes
  │
  ├─ DiffEngine.generate_change_report(Changes)
  │  ├─ Added endpoints
  │  ├─ Modified endpoints (what changed)
  │  └─ Removed endpoints
  │
  └─ Exit: 0 (no changes) or 1 (has changes)
```

---

## Key Design Decisions

### 1. **Dependency Minimalism**
**Decision:** Use only Python stdlib + pydantic for parsing.

**Justification:**
- Keeps package lightweight
- Reduces installation complexity
- Easier to maintain and deploy
- Fewer security vulnerabilities
- Works in offline environments

**Trade-off:** Manual JSON traversal instead of using a library like `jsonschema`, but the manual code is simpler and more maintainable.

---

### 2. **Dataclass Models**
**Decision:** Use Python `@dataclass` for all data structures.

**Justification:**
- Built-in to Python 3.9+
- Provides type safety without complexity
- Auto-generates `__init__`, `__repr__`, `__eq__`
- Easy to serialize/deserialize
- Clean syntax

**Trade-off:** Less flexible than Pydantic models, but sufficient for this use case.

---

### 3. **File-Based Schema Caching**
**Decision:** Store previous schema as `docs/schema_cache.json` for diff detection.

**Justification:**
- No database required
- Simple to implement and debug
- Easy to inspect and version control
- Deterministic behavior

**Trade-off:** Must manually manage cache file; no automatic cleanup.

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
**Decision:** Write all files at once; abort if any step fails.

**Justification:**
- Prevents partial updates that break documentation
- Clear success/failure semantics
- No data loss or corruption

**Trade-off:** Slower for very large documentation; acceptable for typical APIs (< 500 endpoints).

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
| File not found | Parser, CLI | Catch FileNotFoundError, display message | 1 |
| Permission denied | Parser, Generator | Catch PermissionError, suggest chmod | 1 |
| Invalid JSON | Parser | Catch json.JSONDecodeError, show line # | 1 |
| Invalid OpenAPI | Parser | Validate required fields, suggest fix | 1 |
| Disk full | Generator | Catch OSError, suggest cleanup | 1 |

### Logic-Level Errors

| Error | Source | Handling | Exit |
|-------|--------|----------|------|
| Missing required field | Parser | Skip with warning, log details | 0 (continue) or 1 (fail on --strict) |
| Invalid parameter type | Parser | Default to "string", log warning | 0 |
| Endpoint mismatch in diff | DiffEngine | Report as "modified" | 0 |
| Validation failure | Generator | Log report, continue | 0 or 1 depending on --strict |

### CLI-Level Errors

| Error | Source | Handling | Exit |
|-------|--------|----------|------|
| Missing argument | CLI | Show usage help | 2 |
| Invalid flag | CLI | Show error, usage | 2 |
| Invalid command | CLI | Suggest available commands | 2 |

### Logging Strategy

```python
# Log levels
ERROR   - Fatal issues, task fails (exit 1)
WARNING - Non-fatal issues, task continues (exit 0)
INFO    - Progress updates (e.g., "Generated 12 endpoints")
DEBUG   - Detailed info (e.g., "Parsing path: /items/{item_id}")
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
| pydantic | ≥1.0 | Data validation (future) | Optional |
| pyyaml | ≥5.0 | YAML parsing (future) | Optional |

### Internal Module Interfaces

```python
# Parser interface
from docsync.models import Schema
from docsync.parser import parse_openapi

schema = parse_openapi("openapi.json")
# Returns: Schema(title, version, endpoints[])

# Generator interface
from docsync.generator import generate_docs, validate_documentation

generate_docs(schema, output_dir="docs/api/")
# Returns: None (writes files to output_dir)

validation_result = validate_documentation(endpoints, output_dir)
# Returns: ValidationResult(valid: bool, errors: List[str])

# DiffEngine interface
from docsync.diff_engine import detect_changes

changes = detect_changes(old_schema, new_schema)
# Returns: Changes(added[], modified[], removed[])

# CLI interface
from docsync.cli import main

exit_code = main()
# Returns: 0 (success) or 1 (error)
```

---

## Implementation Notes

### For Implementers

1. **Start with models.py**
   - Define all dataclasses first
   - Ensures type consistency across modules
   - Allows parallel development

2. **Parser.py second**
   - Test with sample openapi.json from running FastAPI app
   - Handle edge cases (missing fields, nested definitions)
   - Add verbose mode for debugging

3. **Generator.py third**
   - Implement markdown formatting incrementally
   - Test with parser output
   - Ensure consistent formatting (spaces, tables, etc.)

4. **DiffEngine.py**
   - Implement equality checks carefully
   - Handle parameter additions/removals
   - Test edge cases (reordering, type changes)

5. **CLI.py last**
   - Orchestrate existing components
   - Add comprehensive error handling
   - Test all command paths

### Testing Strategy

- **Unit tests:** Test each module in isolation with fixtures
- **Integration tests:** Test CLI commands end-to-end
- **Fixtures:** Sample openapi.json files (small, medium, large)
- **Coverage goal:** ≥80% per module, ≥85% overall

### Performance Targets

| Operation | Target | Typical |
|-----------|--------|---------|
| Parse 100 endpoints | < 1s | 0.2s |
| Generate 100 endpoints | < 2s | 0.5s |
| Diff 100 endpoints | < 1s | 0.3s |
| Memory (100 endpoints) | < 50MB | 10MB |

### Debugging Notes

- Parser validates OpenAPI structure; add `--verbose` flag to see details
- Generator logs file writes; check `docs/` directory after run
- DiffEngine prints change report; use `--show-details` for specifics
- CLI logs all errors to stderr; use `--debug` for stack traces

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
│  │  Commands: parse, generate, diff, sync, validate  │   │
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

## Summary of Architecture

This architecture achieves the project goals:

✅ **Simple:** 4 core modules + 2 supporting modules  
✅ **Modular:** Clear separation of concerns, testable in isolation  
✅ **Maintainable:** Type hints, docstrings, consistent patterns  
✅ **Extensible:** Easy to add new commands or output formats  
✅ **Performant:** Handles 500+ endpoints efficiently  
✅ **Reliable:** Comprehensive error handling, atomic writes  
✅ **Lightweight:** Uses only stdlib + dataclasses  

**Total Expected Lines of Code:** ~1,400 (including comments and docstrings)  
**Test Coverage Target:** ≥85% overall  
**Module Complexity:** Low (max 300 lines per module)

---

## Next Steps

1. **Design Review:** Review this architecture for feedback
2. **Risk Assessment:** Identify any architectural risks or gaps
3. **Approval:** Human approves to proceed with implementation

---

## Questions for Human Reviewer

- Is this module breakdown appropriate for the requirements?
- Are there any architectural concerns or gaps?
- Should validation be a separate module or part of generator.py?
- Is the CLI command structure clear and complete?
- Any additional error handling scenarios to consider?

---

**Status:** ⏳ Awaiting design review approval before proceeding to Planning stage.
