# Implementation Plan

**Date:** September 10, 2026  
**Agent:** planning-agent  
**Stage:** 4 - Planning  
**Source:** docs/sdlc/requirements.md, docs/sdlc/architecture.md, docs/sdlc/design-review.md

---

## Executive Summary

This plan breaks down the approved Automated Documentation Sync architecture into **8 implementation phases** with **15 discrete tasks**, ordered by dependencies. The implementation follows a foundation-first approach: establishing data models and validation rules before building business logic, then integrating via CLI, and finally validating with comprehensive tests.

**Key Constraints Addressed:**
- 3 critical blockers from design review are baked into Phase 1-2 (validation rules, comparison algorithm, markdown format)
- Dependencies ordered to unblock downstream tasks
- Testing integrated at each phase (unit tests before integration tests)
- Atomic writes pattern enforced at the CLI/Generator level

**Estimated Total Effort:** 25-32 hours (~3-4 days with testing and debugging)

**Critical Path:**
1. Models + Utils (foundation)
2. Parser + Validation (data input)
3. Generator + Markdown Format (data output)
4. DiffEngine + Comparison Algorithm (change detection)
5. CLI + Integration (user interface)
6. Tests (quality assurance)

**Phases:** 8  
**Total Tasks:** 15  
**Blockers Addressed:** 3 (CRITICAL from design review)  
**Improvements Included:** 4 additional (SHOULD-FIX recommendations)

---

## Critical Blockers from Design Review

The following three blockers **MUST** be addressed during implementation:

| Blocker | Task | Status |
|---------|------|--------|
| **Blocker 1:** Schema Validation Rules | TASK-003 (parser.py) | ✅ Included |
| **Blocker 2:** Endpoint Comparison Algorithm | TASK-005 (diff_engine.py) | ✅ Included |
| **Blocker 3:** Markdown Format Specification | TASK-004 (generator.py) | ✅ Included |

**Definition of "Blocker Resolution":**
- Blocker 1: Parser explicitly validates OpenAPI 3.1.0 structure (required fields, types, operations) before processing
- Blocker 2: Diff engine has formally documented comparison rules (what constitutes added/modified/removed)
- Blocker 3: Generator produces strict markdown format with defined sections and tables

---

## Phase Overview

```
┌─ Phase 1: Foundation (4-5 hrs) ───────────────────┐
│ TASK-001: models.py                               │
│ TASK-002: utils.py                                │
└───────────────────────────────────────────────────┘
                        ↓
┌─ Phase 2: Parser & Validation (5-6 hrs) ─────────┐
│ TASK-003: parser.py [BLOCKER #1]                  │
│ TASK-003-test: test_parser.py                     │
└───────────────────────────────────────────────────┘
                        ↓
┌─ Phase 3: Generator & Format (5-6 hrs) ─────────┐
│ TASK-004: generator.py [BLOCKER #3]               │
│ TASK-004-test: test_generator.py                  │
└───────────────────────────────────────────────────┘
                        ↓
┌─ Phase 4: Diff Engine (4-5 hrs) ──────────────────┐
│ TASK-005: diff_engine.py [BLOCKER #2]             │
│ TASK-005-test: test_diff_engine.py                │
└───────────────────────────────────────────────────┘
                        ↓
┌─ Phase 5: CLI Interface (4-5 hrs) ────────────────┐
│ TASK-006: cli.py + orchestration                  │
│ TASK-006-test: test_cli.py                        │
└───────────────────────────────────────────────────┘
                        ↓
┌─ Phase 6: Integration & E2E (3-4 hrs) ────────────┐
│ TASK-007: test_integration.py                     │
│ TASK-008: test_edge_cases.py                      │
└───────────────────────────────────────────────────┘
                        ↓
┌─ Phase 7: Security & Robustness (2-3 hrs) ────────┐
│ TASK-009: Path traversal protection                │
│ TASK-010: Cache recovery mechanism                │
└───────────────────────────────────────────────────┘
                        ↓
┌─ Phase 8: Documentation & Cleanup (1-2 hrs) ─────┐
│ TASK-011: requirements.txt                        │
│ TASK-012: Module docstrings                       │
│ TASK-013: README setup instructions               │
└───────────────────────────────────────────────────┘
```

---

## Detailed Task Breakdown

### PHASE 1: Foundation (4-5 Hours)

**Objective:** Establish type-safe data models and shared utilities that all other modules depend on.

---

#### TASK-001: Data Models (`models.py`)

**Module:** `docsync/models.py`  
**Priority:** CRITICAL (foundation for all modules)  
**Complexity:** Low  
**Estimated Effort:** 2-3 hours  
**Dependencies:** None  
**Blocks:** TASK-003, TASK-004, TASK-005, TASK-006  

**Description:**
Define immutable dataclasses for type-safe data modeling. These models form the data contract between parser, generator, and diff_engine.

**Key Deliverables:**
```python
# Core domain models (frozen dataclasses with type hints)
- Parameter
  - name: str
  - type: str (e.g., "string", "integer", "array")
  - required: bool
  - description: str = ""

- Response
  - status_code: int
  - description: str
  - schema: Optional[dict] = None (raw schema dict)

- Endpoint
  - path: str
  - method: str (GET, POST, PUT, DELETE, PATCH)
  - summary: str
  - description: str = ""
  - parameters: List[Parameter]
  - request_body: Optional[dict] = None
  - responses: Dict[int, Response]
  - tags: List[str] = field(default_factory=list)

- Schema
  - title: str
  - version: str
  - endpoints: List[Endpoint]

- ValidationError (exception for structured errors)
  - message: str
  - context: Optional[dict] = None
```

**Acceptance Criteria:**
- [ ] All models use `@dataclass(frozen=True)` (immutable)
- [ ] Type hints on every field
- [ ] Docstrings with usage examples
- [ ] Field defaults properly specified
- [ ] Can serialize/deserialize to JSON (no circular refs)
- [ ] Equality (`==`) works correctly for comparisons
- [ ] No business logic in models (data container only)
- [ ] test_models.py passes with ≥95% coverage
- [ ] Total lines: ~120

**Definition of Done:**
When all acceptance criteria pass and models are ready for import by parser/generator/diff_engine.

**Testing (TASK-001-test):**
- test_models.py (15-20 test cases)
  - Instantiation with valid data
  - Field defaults work
  - Immutability enforced (frozen=True)
  - Equality comparisons
  - JSON serialization/deserialization
  - Required fields validation

**Notes:**
- Keep models as simple data containers (no methods beyond `__init__`, `__repr__`, `__eq__`)
- Use dataclass defaults to minimize boilerplate
- Enable IDE autocompletion with type hints

---

#### TASK-002: Shared Utilities (`utils.py`)

**Module:** `docsync/utils.py`  
**Priority:** HIGH (used by multiple modules)  
**Complexity:** Low  
**Estimated Effort:** 1-2 hours  
**Dependencies:** TASK-001  
**Blocks:** TASK-003, TASK-004, TASK-005, TASK-006  

**Description:**
Centralize common utilities for file I/O, JSON handling, logging, and path safety.

**Key Deliverables:**
```python
# File I/O functions
def read_json(file_path: str) -> dict:
    """Read and parse JSON file, raise ValueError on invalid JSON."""

def write_json(file_path: str, data: dict) -> None:
    """Write dict to JSON file, create parent directories if needed."""

def read_file(file_path: str) -> str:
    """Read text file, raise FileNotFoundError if missing."""

def write_file(file_path: str, content: str) -> None:
    """Write text file, create directories if needed."""

# Path safety
def validate_output_path(base_dir: str, relative_path: str) -> Path:
    """Prevent path traversal attacks; return validated absolute path."""
    # Returns base_dir/relative_path only if it's inside base_dir
    # Raises ValueError if path escapes base_dir

def ensure_dir(dir_path: str) -> Path:
    """Create directory and parents if needed; return Path object."""

# Logging
def get_logger(name: str, verbose: bool = False) -> logging.Logger:
    """Configure and return logger with appropriate level."""
    # If verbose=True, use DEBUG level; else INFO
    # Log format: [LEVEL] timestamp - message

def format_error(error: Exception, context: str = "") -> str:
    """Format exception for user display with context."""
```

**Acceptance Criteria:**
- [ ] All functions have type hints
- [ ] All functions have docstrings with examples
- [ ] Error messages are clear and actionable
- [ ] Path sanitization prevents directory traversal
- [ ] File I/O handles permission errors gracefully
- [ ] JSON parser handles malformed files
- [ ] Logger is configured consistently
- [ ] test_utils.py passes with ≥90% coverage
- [ ] Total lines: ~150

**Definition of Done:**
When all acceptance criteria pass and utilities are ready for import.

**Testing (TASK-002-test):**
- test_utils.py (12-15 test cases)
  - read_json with valid/invalid files
  - write_json creates directories
  - Path traversal is blocked
  - Logging configuration works
  - File I/O error handling

**Notes:**
- Maximize use of pathlib (Path) over os.path for safety
- Use built-in logging module
- Always create parent directories before writing

---

### PHASE 2: Parser & Validation (5-6 Hours)

**Objective:** Parse OpenAPI schemas and validate structure (BLOCKER #1). Extract endpoints into typed model objects.

---

#### TASK-003: OpenAPI Parser (`parser.py`) [BLOCKER #1]

**Module:** `docsync/parser.py`  
**Priority:** CRITICAL  
**Complexity:** Medium-High  
**Estimated Effort:** 4-5 hours  
**Dependencies:** TASK-001, TASK-002  
**Blocks:** TASK-005, TASK-006  
**Design Review Condition:** ✅ "Add explicit OpenAPI schema validation"

**Description:**
Parse OpenAPI 3.1.0 JSON files, validate schema structure, and extract endpoints into strongly-typed model objects. **This task directly addresses BLOCKER #1 from design review.**

**Key Deliverables:**

```python
# Main parser function
def parse_openapi(file_path: str) -> Schema:
    """
    Parse OpenAPI 3.1.0 JSON file and return Schema object.
    
    Steps:
    1. Load JSON from file
    2. Validate OpenAPI 3.1.0 structure (BLOCKER #1)
    3. Extract endpoints from paths
    4. Return Schema object
    
    Raises:
    - FileNotFoundError if file missing
    - ValueError if JSON invalid
    - ValidationError if schema structure invalid
    """

# Schema validation (BLOCKER #1 implementation)
def validate_openapi_schema(openapi_dict: dict) -> None:
    """
    Validate OpenAPI 3.1.0 schema structure.
    
    Required fields:
    - "openapi": str (must start with "3.1")
    - "info": dict (must have "title", "version")
    - "paths": dict (must not be empty)
    
    For each path:
    - Must contain HTTP method keys (get, post, put, delete, patch, head, options)
    - Each method must have "responses" object
    - Responses must contain at least one status code
    
    Raises ValidationError with specific error message if validation fails.
    """

# Endpoint extraction
def extract_endpoints(openapi_dict: dict) -> List[Endpoint]:
    """Extract all endpoints from OpenAPI paths object."""

def normalize_endpoint(
    path: str, 
    method: str, 
    operation: dict
) -> Endpoint:
    """Convert OpenAPI operation to Endpoint model."""

# Parameter handling
def extract_parameters(operation: dict) -> List[Parameter]:
    """
    Extract parameters from operation.
    
    Handles parameter types:
    - path: {id}, {name}
    - query: ?search=value
    - header: Accept, Authorization
    - body: request payload
    """

# Response handling
def extract_responses(responses_dict: dict) -> Dict[int, Response]:
    """Extract response definitions (status codes + schemas)."""

# Schema reference handling (SHOULD-FIX but scope TBD)
def resolve_schema_ref(ref: str, components: dict) -> dict:
    """Resolve $ref: #/components/schemas/Item to actual schema."""
    # Optional: if time permits, handle $ref resolution
    # For MVP: Can skip or note as TODO
```

**Validation Rules (BLOCKER #1 SPECIFICATION):**

| Validation Rule | Error Message | Severity |
|-----------------|---------------|----------|
| "openapi" field exists | "Missing required field: 'openapi'" | CRITICAL |
| "openapi" version is 3.1.x | "Unsupported OpenAPI version: {version}" | CRITICAL |
| "info" field exists | "Missing required field: 'info'" | CRITICAL |
| "info.title" exists | "Missing 'title' in 'info' object" | CRITICAL |
| "info.version" exists | "Missing 'version' in 'info' object" | CRITICAL |
| "paths" field exists | "Missing required field: 'paths'" | CRITICAL |
| "paths" is dict | "'paths' must be an object (dict)" | CRITICAL |
| "paths" is not empty | "'paths' object is empty (no endpoints)" | WARNING |
| Each path contains HTTP methods | "Path '{path}' has no valid HTTP methods" | ERROR |
| Each method has "responses" | "Operation {method} {path} missing 'responses'" | ERROR |
| Each responses has status codes | "Responses for {method} {path} has no status codes" | ERROR |

**Acceptance Criteria:**
- [ ] parse_openapi() successfully loads and parses valid OpenAPI files
- [ ] validate_openapi_schema() checks all required OpenAPI 3.1.0 fields
- [ ] Explicit error messages for each validation failure
- [ ] extract_endpoints() returns List[Endpoint] with all data
- [ ] extract_parameters() handles all parameter types (path, query, header, body)
- [ ] extract_responses() returns Dict[int, Response]
- [ ] Handles edge cases: empty schema, single endpoint, 100+ endpoints
- [ ] No silent failures; all errors are exceptions
- [ ] test_parser.py passes with ≥90% coverage
- [ ] Total lines: ~250-300

**Definition of Done:**
When parser correctly parses valid OpenAPI files, clearly rejects invalid schemas, and all tests pass.

**Testing (TASK-003-test):**
- test_parser.py (25-30 test cases)
  - **Happy Path:** Parse valid OpenAPI with various endpoint types (GET, POST, PUT, DELETE)
  - **Valid Schemas:** Single endpoint, 10 endpoints, complex parameters
  - **Invalid Schemas:** Missing "openapi", "info", "paths"; wrong types
  - **Edge Cases:** Empty parameters, no description, deeply nested schemas
  - **Error Handling:** Missing file, invalid JSON, malformed OpenAPI
  - **Validation:** Each validation rule triggers correct error

**Validation Test Matrix:**
```
Test: parse_valid_openapi_with_3_endpoints()
Test: parse_valid_openapi_with_complex_parameters()
Test: parse_openapi_missing_openapi_field() → ValidationError
Test: parse_openapi_missing_paths() → ValidationError
Test: parse_openapi_invalid_json() → ValueError
Test: parse_openapi_empty_paths() → Warning (but parses)
Test: extract_parameters_path_params()
Test: extract_parameters_query_params()
Test: extract_parameters_body_params()
Test: extract_responses_multiple_codes()
... (25+ total)
```

**Notes:**
- BLOCKER #1 is fully resolved by validation rules in this task
- Use Python's built-in json module; no external validation library
- Path traversal is not a concern for parser (only generator reads file paths from schema)
- Consider logging warnings for non-critical issues (e.g., endpoint with no description)

**Dependencies:**
- models.py (Endpoint, Parameter, Response, Schema classes)
- utils.py (read_json, get_logger functions)

---

### PHASE 3: Generator & Markdown Format (5-6 Hours)

**Objective:** Generate markdown documentation from parsed schema. Define and implement strict markdown format (BLOCKER #3).

---

#### TASK-004: Markdown Generator (`generator.py`) [BLOCKER #3]

**Module:** `docsync/generator.py`  
**Priority:** CRITICAL  
**Complexity:** Medium  
**Estimated Effort:** 4-5 hours  
**Dependencies:** TASK-001, TASK-002  
**Blocks:** TASK-006  
**Design Review Condition:** ✅ "Define strict markdown output format"

**Description:**
Generate well-formatted markdown API documentation from Schema objects. Implement strict, consistent markdown format (BLOCKER #3). Validate completeness of generated documentation.

**Key Deliverables:**

```python
# Main generation function
def generate_docs(schema: Schema, output_dir: str) -> None:
    """
    Generate complete markdown documentation from Schema.
    
    Steps:
    1. Validate output_dir is safe (no path traversal)
    2. Create output_dir if missing
    3. Generate index.md (TOC + overview)
    4. Generate one .md file per endpoint
    5. Write all files atomically
    
    Atomic write pattern:
    - Write to temp dir first
    - If all succeed, move to output_dir
    - If any fail, raise exception without modifying output_dir
    """

def generate_index(schema: Schema) -> str:
    """Generate index.md with TOC and endpoint listing."""

def generate_endpoint_markdown(endpoint: Endpoint) -> str:
    """Generate markdown content for single endpoint."""

def generate_endpoint_file(
    endpoint: Endpoint, 
    output_dir: str
) -> None:
    """
    Generate and save markdown file for endpoint.
    
    Filename: {METHOD}_{path}.md
    Examples: GET_items.md, POST_items_create.md
    Safe handling: sanitize path before using as filename
    """

# Markdown formatting helpers
def format_parameters_table(parameters: List[Parameter]) -> str:
    """Generate markdown table for parameters."""

def format_responses_table(responses: Dict[int, Response]) -> str:
    """Generate markdown table for responses."""

def format_json_example(data: dict) -> str:
    """Format JSON object as markdown code block."""

# Validation
def validate_documentation(
    schema: Schema, 
    output_dir: str
) -> ValidationResult:
    """
    Validate generated documentation completeness.
    
    Checks:
    - All endpoints have .md files
    - All files contain required sections
    - Markdown syntax is valid
    - No broken internal links
    """
```

**Markdown Format Specification (BLOCKER #3):**

The generator produces a strict markdown format with these components:

**File: `index.md` (Generated Table of Contents)**
```markdown
# API Documentation

**OpenAPI Version:** 3.1.0
**API Title:** [from schema.title]
**API Version:** [from schema.version]
**Generated:** [ISO timestamp]

## Overview

This documentation is auto-generated from the OpenAPI schema.

## Endpoints (N endpoints)

[Table with: Method | Path | Summary]

---

## Endpoints by Method

### GET Endpoints
- [GET /items](#get_items)
- [GET /items/{item_id}](#get_items_item_id)
...
```

**File: `{METHOD}_{path}.md` (Per-Endpoint Documentation)**
```markdown
# {METHOD} {path}

**Summary:** [from endpoint.summary]

**Description:** [from endpoint.description]

## Parameters

| Name | Type | Required | Location | Description |
|------|------|----------|----------|-------------|
| id | integer | Yes | path | The item ID |
| filter | string | No | query | Optional filter |

## Request Body

**Content-Type:** application/json

[JSON schema or example]

## Responses

| Status Code | Description | Schema |
|-------------|-------------|--------|
| 200 | Success | Item object |
| 404 | Not found | Error |
| 500 | Internal error | Error |

### 200 Response Example

\`\`\`json
{
  "id": 1,
  "name": "Example",
  "created_at": "2026-09-10T00:00:00Z"
}
\`\`\`

## Related Endpoints

- [GET /items](#GET_items) - List all items
- [DELETE /items/{item_id}](#DELETE_items_item_id) - Delete item
```

**Acceptance Criteria:**
- [ ] Generates valid markdown that renders correctly on GitHub
- [ ] Follows strict format specification (above)
- [ ] All markdown has proper headers, tables, code blocks
- [ ] Endpoint filenames are sanitized (no path traversal)
- [ ] Index file lists all endpoints with TOC
- [ ] Each endpoint file has: Summary, Description, Parameters, Request Body, Responses, Examples
- [ ] Path traversal protection: validate all paths before writing files
- [ ] Atomic writes: all files succeed or none
- [ ] Validation catches incomplete documentation
- [ ] test_generator.py passes with ≥85% coverage
- [ ] Total lines: ~300-350

**Definition of Done:**
When generator produces consistent, well-formatted markdown that passes validation, and all tests pass.

**Testing (TASK-004-test):**
- test_generator.py (20-25 test cases)
  - Generate index.md with various endpoint counts
  - Generate endpoint markdown for simple and complex endpoints
  - Markdown format validation
  - Parameter table formatting
  - Response table formatting
  - JSON example formatting
  - Filename sanitization (no traversal)
  - Atomic write behavior (success and failure cases)
  - Validation catches missing sections

**Format Validation Tests:**
```
Test: generate_index_produces_valid_markdown()
Test: generate_endpoint_markdown_has_all_sections()
Test: format_parameters_table_correct_format()
Test: format_responses_table_correct_format()
Test: validate_documentation_detects_missing_files()
Test: validate_documentation_detects_missing_sections()
Test: sanitize_endpoint_filename_prevents_traversal()
Test: atomic_write_on_success()
Test: atomic_write_on_partial_failure()
... (20+ total)
```

**Notes:**
- BLOCKER #3 is fully resolved by markdown format specification
- Use pathlib for safe filename handling
- Implement atomic writes: write to temp directory, then move to target
- Markdown should be GitHub-flavored (GFM)

**Dependencies:**
- models.py (Schema, Endpoint, Parameter, Response)
- utils.py (write_file, validate_output_path, get_logger)

---

### PHASE 4: Diff Engine (4-5 Hours)

**Objective:** Detect schema changes between versions (BLOCKER #2). Implement endpoint comparison algorithm.

---

#### TASK-005: Diff Engine (`diff_engine.py`) [BLOCKER #2]

**Module:** `docsync/diff_engine.py`  
**Priority:** CRITICAL  
**Complexity:** Medium-High  
**Estimated Effort:** 3-4 hours  
**Dependencies:** TASK-001, TASK-002  
**Blocks:** TASK-006  
**Design Review Condition:** ✅ "Define endpoint comparison algorithm"

**Description:**
Compare old and new OpenAPI schemas to detect changes: added endpoints, removed endpoints, and modified endpoints. Implement formal comparison algorithm (BLOCKER #2).

**Endpoint Comparison Algorithm (BLOCKER #2 SPECIFICATION):**

```
CHANGE DETECTION ALGORITHM
==========================

Input:
  - old_schema: Schema (or None if first sync)
  - new_schema: Schema

Output:
  - changes: Changes { added: [], modified: [], removed: [] }

Process:
  1. For each endpoint in new_schema:
     a. Try to find matching endpoint in old_schema by (path, method)
     b. If not found → ADD to changes.added
     c. If found → compare using endpoints_equal()
        - If NOT equal → ADD to changes.modified as (old, new)
        - If equal → NO CHANGE

  2. For each endpoint in old_schema:
     a. Try to find matching endpoint in new_schema by (path, method)
     b. If not found → ADD to changes.removed

Endpoint Equality (endpoints_equal):
  Two endpoints are EQUAL if:
    path == path AND
    method == method AND
    summary == summary AND
    description == description AND
    parameters_equal(parameters_list) AND
    responses_equal(responses_dict)

Parameter Equality (parameters_equal):
  Two parameter lists are EQUAL if:
    - Same length AND
    - For each parameter index:
      - name == name AND
      - type == type AND
      - required == required AND
      - description == description

  Note: Parameter ORDER matters (reordering counts as change)

Response Equality (responses_equal):
  Two response dicts are EQUAL if:
    - Same set of status codes AND
    - For each status code:
      - description == description AND
      - schema == schema (deep comparison)

First Sync (no old_schema):
  - All endpoints in new_schema are "added"
  - No endpoints are "removed"
  - Result: changes.added = [all endpoints], removed = []
```

**Key Deliverables:**

```python
def detect_changes(
    old_schema: Optional[Schema],
    new_schema: Schema
) -> Changes:
    """
    Detect changes between old and new schemas.
    
    Uses algorithm above:
    1. Find added (new but not old)
    2. Find removed (old but not new)
    3. Find modified (same key, different content)
    """

def endpoints_equal(ep1: Endpoint, ep2: Endpoint) -> bool:
    """
    Check if two endpoints are equal using BLOCKER #2 algorithm.
    
    Compares:
    - path, method (if these differ, not equal)
    - summary, description
    - parameters_equal()
    - responses_equal()
    """

def parameters_equal(
    params1: List[Parameter],
    params2: List[Parameter]
) -> bool:
    """
    Check if parameter lists are equal.
    
    Order matters: [a, b] != [b, a]
    """

def responses_equal(
    resp1: Dict[int, Response],
    resp2: Dict[int, Response]
) -> bool:
    """Check if response dicts are equal."""

def find_endpoint(
    path: str,
    method: str,
    endpoints: List[Endpoint]
) -> Optional[Endpoint]:
    """Find endpoint in list by path + method."""

def generate_change_report(changes: Changes) -> str:
    """
    Generate human-readable change summary.
    
    Example:
    ---
    Changes detected: 3 added, 2 modified, 1 removed
    
    Added (3):
    - POST /items/batch → Batch create items
    - DELETE /items/{id}/cascade → Delete with cascade
    - GET /health → Health check
    
    Modified (2):
    - GET /items/{id} → Parameters added: include_details
    - PUT /items/{id} → Response schema changed
    
    Removed (1):
    - GET /items/search (deprecated)
    ---
    """

# Cache management (optional helper)
def save_schema_cache(schema: Schema, cache_path: str) -> None:
    """Serialize and save schema to JSON cache file."""

def load_schema_cache(cache_path: str) -> Optional[Schema]:
    """Load schema from JSON cache; return None if missing/invalid."""
```

**Acceptance Criteria:**
- [ ] detect_changes() correctly identifies added/modified/removed endpoints
- [ ] Endpoint comparison follows BLOCKER #2 algorithm exactly
- [ ] Parameter order matters (reordering is a change)
- [ ] Response schemas compared correctly
- [ ] First sync case handled (no old_schema = all added)
- [ ] Edge cases: empty schema, single endpoint, no changes
- [ ] generate_change_report() produces clear output
- [ ] Cache functions handle JSON serialization/deserialization
- [ ] Cache recovery: corrupt cache treated as "no previous"
- [ ] test_diff_engine.py passes with ≥85% coverage
- [ ] Total lines: ~200-250

**Definition of Done:**
When diff engine correctly detects changes using the formal algorithm, passes all test scenarios, and generates clear reports.

**Testing (TASK-005-test):**
- test_diff_engine.py (20-25 test cases)
  - **All New:** new_schema with 3 endpoints, old_schema=None
  - **Some Modified:** parameter added, description changed
  - **Some Removed:** endpoint no longer in new_schema
  - **No Changes:** old_schema == new_schema
  - **Parameter Changes:**
    - Parameter added (modification)
    - Parameter removed (modification)
    - Parameter reordered (modification)
    - Parameter description changed (modification)
  - **Response Changes:**
    - New status code added (modification)
    - Status code removed (modification)
    - Response schema changed (modification)
  - **Edge Cases:** Single endpoint, empty schema
  - **First Sync:** No old_schema provided

**Algorithm Validation Tests:**
```
Test: detect_changes_all_new_endpoints()
  Setup: old=None, new=[endpoint1, endpoint2, endpoint3]
  Expected: changes.added=[all 3], removed=[], modified=[]

Test: detect_changes_some_modified()
  Setup: old=[ep1], new=[ep1_modified]
  Expected: changes.modified=[(ep1, ep1_modified)]

Test: detect_changes_parameter_reorder_is_modified()
  Setup: old=[GET /items with [param_a, param_b]]
         new=[GET /items with [param_b, param_a]]
  Expected: changes.modified=[...] (order matters!)

Test: detect_changes_description_change_is_modified()
  Setup: old=[endpoint with description="old"]
         new=[endpoint with description="new"]
  Expected: changes.modified=[...] (description matters)

Test: endpoints_equal_same_endpoint()
  Setup: ep1=Endpoint(...), ep2=Endpoint(...) with same content
  Expected: endpoints_equal(ep1, ep2) == True

Test: endpoints_equal_different_method()
  Setup: ep1=GET /items, ep2=POST /items
  Expected: endpoints_equal(ep1, ep2) == False

... (20+ total)
```

**Notes:**
- BLOCKER #2 is fully resolved by the comparison algorithm
- Parameter order DOES matter (list comparison, not set)
- Response schema comparison is deep (not just status codes)
- Cache functions are helpers for sync workflow (see TASK-006)

**Dependencies:**
- models.py (Schema, Endpoint, Parameter, Response, Changes)
- utils.py (get_logger, read_json, write_json)

---

### PHASE 5: CLI Interface (4-5 Hours)

**Objective:** Implement command-line interface that orchestrates the workflow (parse → diff → generate → sync).

---

#### TASK-006: CLI & Orchestration (`cli.py`)

**Module:** `docsync/cli.py`  
**Priority:** CRITICAL  
**Complexity:** Medium  
**Estimated Effort:** 4-5 hours  
**Dependencies:** TASK-001, TASK-002, TASK-003, TASK-004, TASK-005  
**Blocks:** TASK-007, TASK-008  

**Description:**
Implement command-line interface for all docsync operations. Orchestrate parser, generator, and diff_engine modules. Handle user input, error reporting, and exit codes.

**Key Deliverables:**

```python
def main() -> int:
    """Main entry point for CLI."""

def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse command-line arguments for all subcommands."""

# Subcommands
def cmd_parse(args) -> int:
    """docsync parse <schema-file>
    
    Load and parse OpenAPI schema.
    Output: Schema summary (title, version, # endpoints)
    Exit: 0=success, 1=error
    """

def cmd_generate(args) -> int:
    """docsync generate <schema-file> <output-dir>
    
    Parse schema and generate markdown documentation.
    Output: Generated files in output-dir/
    Exit: 0=success, 1=error
    """

def cmd_diff(args) -> int:
    """docsync diff <old-schema-file> <new-schema-file>
    
    Compare two schemas and report changes.
    Output: Change report (added, modified, removed)
    Exit: 0=no changes, 1=has changes, 2=error
    """

def cmd_sync(args) -> int:
    """docsync sync <schema-file> <docs-dir>
    
    Full workflow: parse → load cache → diff → generate → save cache
    
    Steps:
    1. Load new schema from file
    2. Load old schema from cache (if exists)
    3. Detect changes via diff_engine
    4. Generate new markdown
    5. Save new schema as cache
    
    Output: Sync report (added X, modified Y, removed Z)
    Exit: 0=success, 1=error
    """

def cmd_validate(args) -> int:
    """docsync validate <docs-dir>
    
    Validate existing markdown documentation.
    Output: Validation report
    Exit: 0=valid, 1=invalid, 2=error
    """

# Workflow helpers
def load_schema_with_validation(file_path: str) -> Schema:
    """Load schema file with error handling."""

def save_sync_report(changes: Changes, report_path: str) -> None:
    """Save changes to sync_report.json."""

def print_summary(changes: Changes) -> None:
    """Print summary to stdout."""
```

**Supported Commands:**

| Command | Purpose | Output | Exit Code |
|---------|---------|--------|-----------|
| `parse <schema-file>` | Parse and display schema info | Schema summary | 0=ok, 1=err |
| `generate <schema> <out-dir>` | Generate markdown docs | Generated files | 0=ok, 1=err |
| `diff <old-schema> <new-schema>` | Show schema changes | Change report | 0=no changes, 1=has changes, 2=err |
| `sync <schema> <docs-dir>` | Full sync workflow | Updated docs + sync report | 0=ok, 1=err |
| `validate <docs-dir>` | Validate markdown completeness | Validation report | 0=valid, 1=invalid, 2=err |

**CLI Examples:**

```bash
# Parse schema and show info
$ docsync parse openapi.json
Parsed OpenAPI schema:
  Title: FastAPI Demo
  Version: 1.0.0
  Endpoints: 5
    GET /items
    POST /items
    GET /items/{item_id}
    ...

# Generate documentation
$ docsync generate openapi.json docs/api
Generated documentation:
  docs/api/index.md
  docs/api/GET_items.md
  docs/api/POST_items.md
  ...

# Detect changes between versions
$ docsync diff openapi_v1.json openapi_v2.json
Changes detected: 2 added, 1 modified, 0 removed
  Added:
    - POST /items/batch
    - GET /health
  Modified:
    - GET /items/{id} (parameters changed)

# Full sync workflow
$ docsync sync openapi.json docs/api
Syncing documentation...
  Loaded schema: 5 endpoints
  Previous schema: 4 endpoints
  Changes: 1 added, 0 modified, 0 removed
  Generated: docs/api/index.md, docs/api/GET_health.md, ...
  Sync report saved to: docs/api/sync_report.json
Success!

# Validate documentation
$ docsync validate docs/api
Validation Results:
  Total files: 6
  Valid: 6
  Invalid: 0
  Missing sections: 0
All documentation is valid!
```

**Acceptance Criteria:**
- [ ] All 5 commands (parse, generate, diff, sync, validate) implemented
- [ ] Command-line argument parsing works correctly
- [ ] Error messages are clear and actionable
- [ ] Exit codes: 0=success, 1=error, 2=usage/validation error
- [ ] `--verbose` flag enables DEBUG logging
- [ ] `--help` displays usage for each command
- [ ] Workflow is atomic: sync completes fully or reverts on error
- [ ] Sync report generated in JSON format
- [ ] Cache file (schema_cache.json) saved after successful sync
- [ ] test_cli.py passes with ≥80% coverage
- [ ] Total lines: ~350-400

**Definition of Done:**
When all CLI commands work, error handling is robust, and exit codes are correct.

**Testing (TASK-006-test):**
- test_cli.py (25-30 test cases)
  - Each command with valid input
  - Each command with missing file
  - Each command with invalid arguments
  - Error messages are clear
  - Exit codes are correct
  - `--verbose` flag works
  - `--help` displays usage
  - Sync workflow creates cache file
  - Multiple sync cycles (incremental changes)

**Notes:**
- Use argparse for CLI argument parsing
- Implement atomic sync: if any step fails, rollback before cache save
- Sync report should document what changed for user reference
- Consider adding `--dry-run` flag to preview changes without writing

**Dependencies:**
- All modules (parser, generator, diff_engine, models, utils)

---

### PHASE 6: Integration & End-to-End Tests (3-4 Hours)

**Objective:** Validate full workflow with comprehensive testing.

---

#### TASK-007: Integration Tests (`tests/test_integration.py`)

**Module:** `tests/test_integration.py`  
**Priority:** HIGH  
**Complexity:** Medium  
**Estimated Effort:** 2-3 hours  
**Dependencies:** All other modules  
**Blocks:** None  

**Description:**
Write end-to-end tests that exercise the full docsync workflow using real (or realistic) OpenAPI schemas.

**Test Scenarios:**

```python
# End-to-end workflow tests
def test_e2e_parse_generate_sync():
    """Full workflow: parse schema → generate docs → sync"""
    # 1. Parse openapi.json
    # 2. Generate markdown
    # 3. Verify all files created
    # 4. Verify content matches schema

def test_e2e_incremental_sync_with_changes():
    """Sync twice with schema changes in between"""
    # 1. First sync (initial docs)
    # 2. Modify schema (add endpoint, change parameter)
    # 3. Second sync (incremental)
    # 4. Verify new endpoint documented
    # 5. Verify modified endpoint updated
    # 6. Verify cache reflects changes

def test_e2e_sync_with_removed_endpoints():
    """Handle removed endpoints gracefully"""
    # 1. Initial sync with 5 endpoints
    # 2. Remove 1 endpoint from schema
    # 3. Second sync
    # 4. Verify removed endpoint no longer in docs

def test_e2e_cli_commands_workflow():
    """Test CLI commands in sequence"""
    # 1. cli.cmd_parse() - show schema info
    # 2. cli.cmd_generate() - generate docs
    # 3. cli.cmd_diff() - show changes
    # 4. cli.cmd_sync() - full sync
    # 5. cli.cmd_validate() - validate docs

def test_e2e_error_recovery():
    """Verify graceful error handling"""
    # 1. Try sync with missing schema file
    # 2. Try sync with invalid JSON
    # 3. Verify error messages are clear
    # 4. Verify no partial docs created
```

**Test Fixtures:**

- Real FastAPI `openapi.json` from main.py
- Various schema sizes: 1 endpoint, 5 endpoints, 20 endpoints
- Edge case schemas: minimal fields, complex parameters

**Acceptance Criteria:**
- [ ] E2E workflow tests pass (parse → generate → sync)
- [ ] Incremental sync handles changes correctly
- [ ] CLI commands work in sequence
- [ ] Error cases handled gracefully
- [ ] No partial/corrupted docs created
- [ ] Cache file created correctly
- [ ] Coverage of integration tests ≥80%

**Notes:**
- Use pytest fixtures for schema setup
- Mock file I/O if needed for speed
- Test with real openapi.json from main.py

---

#### TASK-008: Edge Case & Error Testing (`tests/test_edge_cases.py`)

**Module:** `tests/test_edge_cases.py`  
**Priority:** HIGH  
**Complexity:** Medium  
**Estimated Effort:** 1-2 hours  
**Dependencies:** All other modules  
**Blocks:** None  

**Description:**
Comprehensive testing of edge cases, error conditions, and robustness.

**Test Categories:**

```python
# Edge cases
def test_schema_with_single_endpoint():
    """Minimal schema with one endpoint"""

def test_schema_with_no_parameters():
    """Endpoint with no parameters"""

def test_schema_with_complex_nested_parameters():
    """Deeply nested object parameters"""

def test_large_schema_performance():
    """Parse and sync 100+ endpoints"""

# Error conditions
def test_file_not_found():
    """Missing schema file → clear error"""

def test_invalid_json():
    """Malformed JSON → clear error"""

def test_permission_denied():
    """Write to read-only directory → clear error"""

def test_corrupted_cache_file():
    """Invalid schema_cache.json → treated as first sync"""

def test_concurrent_sync():
    """Two sync processes on same directory (warning)"""

# Robustness
def test_sync_with_disk_full():
    """Simulate disk full during write (no partial data)"""

def test_large_markdown_output():
    """Generate docs for 200+ endpoints"""

def test_unicode_in_descriptions():
    """Handle emoji, special characters in docs"""
```

**Acceptance Criteria:**
- [ ] All edge cases handled without crashing
- [ ] Error messages are helpful
- [ ] No data corruption on partial failures
- [ ] Performance acceptable for large schemas
- [ ] Unicode/emoji support
- [ ] Coverage ≥80%

---

### PHASE 7: Security & Robustness (2-3 Hours)

**Objective:** Address SHOULD-FIX recommendations from design review.

---

#### TASK-009: Path Traversal Protection

**Recommendation:** "Add path traversal protection" (design review SHOULD-FIX #4)

**Module:** Updates to `generator.py` + `utils.py`  
**Priority:** HIGH  
**Complexity:** Low  
**Estimated Effort:** 1 hour  
**Dependencies:** TASK-004, TASK-002  

**Description:**
Implement validation to prevent writing files outside intended output directory.

**Implementation:**

```python
# In utils.py
def validate_output_path(base_dir: str, relative_path: str) -> Path:
    """
    Validate that relative_path doesn't escape base_dir.
    
    Raises ValueError if path tries to escape (e.g., ../../../etc/passwd)
    Returns validated absolute Path object if safe.
    """
    base = Path(base_dir).resolve()
    full = (base / relative_path).resolve()
    
    if not str(full).startswith(str(base)):
        raise ValueError(f"Path traversal detected: {relative_path}")
    
    return full

# In generator.py
def safe_write_markdown(output_dir: str, relative_path: str, content: str) -> None:
    """Write markdown file with path validation."""
    full_path = validate_output_path(output_dir, relative_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')
```

**Test:** `test_generator.py` should include path traversal test cases

---

#### TASK-010: Cache Backup & Recovery

**Recommendation:** "Implement cache backup & recovery" (design review SHOULD-FIX #6)

**Module:** Updates to `diff_engine.py` + `cli.py`  
**Priority:** MEDIUM  
**Complexity:** Low  
**Estimated Effort:** 1-2 hours  
**Dependencies:** TASK-005, TASK-006  

**Description:**
Add backup mechanism for schema cache; handle corruption gracefully.

**Implementation:**

```python
# In diff_engine.py
def save_schema_cache(schema: Schema, cache_path: str) -> None:
    """
    Save schema cache with backup.
    
    Steps:
    1. If cache exists, rename to .bak
    2. Write new cache
    3. If write fails, restore .bak
    """
    cache_path_obj = Path(cache_path)
    backup_path = cache_path_obj.parent / f"{cache_path_obj.name}.bak"
    
    # Backup existing cache
    if cache_path_obj.exists():
        cache_path_obj.rename(backup_path)
    
    try:
        # Write new cache
        data = serialize_schema(schema)  # Custom serialization
        utils.write_json(cache_path, data)
    except Exception:
        # Restore backup on failure
        if backup_path.exists():
            backup_path.rename(cache_path)
        raise

def load_schema_cache(cache_path: str) -> Optional[Schema]:
    """
    Load schema cache with error recovery.
    
    If cache is missing or corrupt:
    - Log warning
    - Return None (treat as first sync)
    - DO NOT crash
    """
    try:
        data = utils.read_json(cache_path)
        return deserialize_schema(data)
    except (FileNotFoundError, ValueError) as e:
        logger.warning(f"Cache invalid or missing: {cache_path} ({e})")
        return None
```

**Test:** `test_diff_engine.py` should include cache recovery test cases

---

### PHASE 8: Documentation & Cleanup (1-2 Hours)

**Objective:** Final documentation and setup.

---

#### TASK-011: Update `requirements.txt`

**File:** `requirements.txt`  
**Priority:** LOW  
**Complexity:** Low  
**Estimated Effort:** 15 minutes  

**Description:**
Add new test dependencies and finalize requirements.

**Content:**
```
# Existing dependencies
fastapi
uvicorn
redis
pydantic
anyio
starlette

# New dependencies for docsync
# None - all stdlib!

# Development/Testing dependencies
pytest>=7.0
pytest-cov>=4.0
```

**Acceptance Criteria:**
- [ ] All dependencies listed
- [ ] No external dependencies for docsync (stdlib only)
- [ ] Test dependencies included
- [ ] Version pinning appropriate

---

#### TASK-012: Module Docstrings & Documentation

**Files:** All `.py` modules  
**Priority:** MEDIUM  
**Complexity:** Low  
**Estimated Effort:** 1 hour  

**Description:**
Add comprehensive module-level docstrings and inline documentation.

**Modules to Document:**
- `docsync/__init__.py` - Package overview
- `docsync/models.py` - Data models with examples
- `docsync/parser.py` - OpenAPI parsing logic
- `docsync/generator.py` - Markdown generation
- `docsync/diff_engine.py` - Change detection algorithm
- `docsync/cli.py` - CLI commands and workflow
- `docsync/utils.py` - Utility functions

**Acceptance Criteria:**
- [ ] Every module has docstring
- [ ] Every class has docstring
- [ ] Every public function has docstring with examples
- [ ] Complex algorithms have inline comments
- [ ] README.md updated with setup instructions

---

#### TASK-013: README & Integration Guide

**File:** `README.md` or `docs/SETUP.md`  
**Priority:** MEDIUM  
**Complexity:** Low  
**Estimated Effort:** 30 minutes  

**Description:**
Provide clear setup and usage instructions.

**Content:**
```markdown
# Automated Documentation Sync (docsync)

Quick start, usage examples, architecture overview.

## Installation
...

## Usage
docsync parse <schema>
docsync generate <schema> <output>
docsync sync <schema> <docs>
docsync validate <docs>

## Integration with FastAPI
Example code to run docsync in your project.

## Architecture
Module overview and data flow.

## Testing
How to run tests and check coverage.
```

**Acceptance Criteria:**
- [ ] Installation instructions clear
- [ ] All CLI commands documented
- [ ] Usage examples provided
- [ ] Integration example for FastAPI
- [ ] Testing instructions included

---

## Testing Strategy

### Unit Testing (Per-Module)

Each module has comprehensive unit tests:

| Module | Tests | Coverage Target | Key Test Cases |
|--------|-------|-----------------|-----------------|
| models.py | test_models.py | ≥95% | Instantiation, serialization, equality |
| utils.py | test_utils.py | ≥90% | File I/O, path validation, logging |
| parser.py | test_parser.py | ≥90% | Valid/invalid schemas, edge cases |
| generator.py | test_generator.py | ≥85% | Markdown format, file writing, validation |
| diff_engine.py | test_diff_engine.py | ≥85% | Change detection, algorithm validation |
| cli.py | test_cli.py | ≥80% | All commands, argument parsing, error handling |

**Total Unit Tests:** ~140 test cases  
**Estimated Coverage:** 85-90% for entire codebase

### Integration Testing

- `test_integration.py`: End-to-end workflows
- `test_edge_cases.py`: Edge cases and error handling

**Total Integration Tests:** ~20 test cases

### Test Execution

```bash
# Run all tests
pytest tests/ -v --cov=docsync --cov-report=term-missing

# Run specific test file
pytest tests/test_parser.py -v

# Run with markers
pytest -m "not slow" -v  # Skip slow tests
```

### Coverage Report

Expected coverage distribution:
- **Critical modules** (parser, generator, diff_engine): ≥85%
- **Utility modules** (models, utils): ≥90%
- **CLI module**: ≥80%
- **Overall**: ≥85%

---

## Dependency Graph (Tasks)

```
TASK-001 (models.py)
  ├─ TASK-002 (utils.py)
  ├─ TASK-003 (parser.py) [BLOCKER #1]
  │   ├─ TASK-003-test (test_parser.py)
  │   └─ TASK-005 (diff_engine.py) [BLOCKER #2]
  │       ├─ TASK-005-test (test_diff_engine.py)
  │       └─ TASK-006 (cli.py)
  │           ├─ TASK-006-test (test_cli.py)
  │           └─ TASK-007 (test_integration.py)
  │
  ├─ TASK-004 (generator.py) [BLOCKER #3]
  │   ├─ TASK-004-test (test_generator.py)
  │   └─ TASK-006 (cli.py)
  │
  ├─ TASK-009 (Path traversal protection)
  └─ TASK-010 (Cache recovery)
  
TASK-011 (requirements.txt)
TASK-012 (Module docstrings)
TASK-013 (README)
TASK-008 (Edge case testing)
```

---

## Execution Order (Critical Path)

### Phase 1: Foundation (Est. 4-5 hrs)
**Tasks:** TASK-001, TASK-002  
**Parallelizable:** Yes (TASK-002 only depends on TASK-001 for imports)  
**Gate:** ✅ No approval needed

1. **TASK-001** (2-3 hrs): Implement models.py, write test_models.py
2. **TASK-002** (1-2 hrs): Implement utils.py, write test_utils.py

### Phase 2: Parser & Validation (Est. 5-6 hrs)
**Tasks:** TASK-003, TASK-003-test  
**Gate:** ✅ No approval needed  
**Blocker Resolved:** #1 (Schema Validation)

3. **TASK-003** (3-4 hrs): Implement parser.py with validation rules
4. **TASK-003-test** (1-2 hrs): Write comprehensive test_parser.py

### Phase 3: Generator & Markdown (Est. 5-6 hrs)
**Tasks:** TASK-004, TASK-004-test  
**Gate:** ✅ No approval needed  
**Blocker Resolved:** #3 (Markdown Format)

5. **TASK-004** (3-4 hrs): Implement generator.py with format spec
6. **TASK-004-test** (1-2 hrs): Write test_generator.py

### Phase 4: Diff Engine (Est. 4-5 hrs)
**Tasks:** TASK-005, TASK-005-test  
**Gate:** ✅ No approval needed  
**Blocker Resolved:** #2 (Endpoint Comparison)

7. **TASK-005** (2-3 hrs): Implement diff_engine.py with algorithm
8. **TASK-005-test** (1-2 hrs): Write test_diff_engine.py

### Phase 5: CLI & Integration (Est. 4-5 hrs)
**Tasks:** TASK-006, TASK-006-test  
**Dependencies:** TASK-003, TASK-004, TASK-005  
**Gate:** ✅ No approval needed

9. **TASK-006** (3-4 hrs): Implement cli.py with all commands
10. **TASK-006-test** (1-2 hrs): Write test_cli.py

### Phase 6: Integration & E2E (Est. 3-4 hrs)
**Tasks:** TASK-007, TASK-008  
**Dependencies:** All above  
**Gate:** ✅ No approval needed

11. **TASK-007** (2-3 hrs): Write test_integration.py (E2E)
12. **TASK-008** (1-2 hrs): Write test_edge_cases.py

### Phase 7: Security & Robustness (Est. 2-3 hrs)
**Tasks:** TASK-009, TASK-010  
**Gate:** ✅ No approval needed  
**Improvements Included:** SHOULD-FIX #4 (Path traversal), #6 (Cache recovery)

13. **TASK-009** (1 hr): Path traversal protection
14. **TASK-010** (1-2 hrs): Cache backup & recovery

### Phase 8: Documentation & Cleanup (Est. 1-2 hrs)
**Tasks:** TASK-011, TASK-012, TASK-013  
**Gate:** ✅ No approval needed

15. **TASK-011** (15 min): Update requirements.txt
16. **TASK-012** (30 min): Add module docstrings
17. **TASK-013** (30 min): Write README/SETUP

---

## Time Estimation Summary

| Phase | Tasks | Hours | Notes |
|-------|-------|-------|-------|
| 1: Foundation | 2 | 4-5 | Parallelizable |
| 2: Parser | 2 | 5-6 | BLOCKER #1 |
| 3: Generator | 2 | 5-6 | BLOCKER #3 |
| 4: Diff Engine | 2 | 4-5 | BLOCKER #2 |
| 5: CLI | 2 | 4-5 | All modules ready |
| 6: Integration | 2 | 3-4 | E2E validation |
| 7: Security | 2 | 2-3 | Robustness |
| 8: Docs | 3 | 1-2 | Final touches |
| **TOTAL** | **15** | **25-32** | **~3-4 days** |

---

## Definition of "Done" (Per Task)

Each task is considered DONE when:

1. **Implementation Complete:**
   - Code written following PEP 8
   - All type hints present
   - Docstrings with examples
   - Error handling in place

2. **Testing Complete:**
   - Corresponding test file exists
   - All acceptance criteria tests pass
   - Coverage target met
   - Edge cases covered

3. **Integration Ready:**
   - No import errors
   - Can be imported by dependent modules
   - Plays well with rest of codebase

4. **Documentation Complete:**
   - Module docstring present
   - Function docstrings present
   - Complex logic has comments
   - README updated if needed

5. **Code Review Ready:**
   - No linting errors
   - No obvious bugs
   - Performance acceptable
   - Security reviewed

---

## Design Review Conditions - Implementation Mapping

| Condition | Task | Implementation Details |
|-----------|------|------------------------|
| **BLOCKER #1** Schema Validation | TASK-003 | `validate_openapi_schema()` with 10 validation rules |
| **BLOCKER #2** Endpoint Comparison | TASK-005 | `endpoints_equal()`, `parameters_equal()`, formal algorithm |
| **BLOCKER #3** Markdown Format | TASK-004 | Strict format spec: index.md, endpoint files, sections |
| **SHOULD-FIX #4** Path Traversal | TASK-009 | `validate_output_path()` prevents directory escape |
| **SHOULD-FIX #5** Schema Refs | Future | Optional: `resolve_schema_ref()` for `$ref` resolution |
| **SHOULD-FIX #6** Cache Recovery | TASK-010 | Backup mechanism, corruption handling |

---

## Success Criteria

The implementation plan is successful when:

✅ All 15 tasks completed  
✅ All 3 blockers explicitly addressed in code  
✅ Unit test coverage ≥85% (≥90% for critical modules)  
✅ Integration tests pass (E2E workflows)  
✅ All CLI commands work  
✅ No data corruption on errors  
✅ Clear error messages  
✅ Documentation complete  
✅ Ready for code review and PR  

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Parser doesn't handle all OpenAPI variants | MEDIUM | MEDIUM | TASK-003 validation + extensive testing |
| Diff engine comparison too strict/loose | MEDIUM | MEDIUM | TASK-005 algorithm + algorithm tests |
| Markdown format not rendering on GitHub | LOW | MEDIUM | TASK-004 validation + manual check |
| Path traversal vulnerability | LOW | HIGH | TASK-009 path validation |
| Cache corruption loses sync state | MEDIUM | MEDIUM | TASK-010 backup mechanism |
| Performance degrades at scale | LOW | LOW | TASK-007 includes large schema test |

---

## Next Steps

1. **Architecture Confirmation:** Confirm plan with architecture-agent and design-review-agent
2. **Implementation Kickoff:** Start Phase 1 (Foundation) immediately after confirmation
3. **Daily Progress:** Track completion of tasks against this plan
4. **Gate Checks:** No formal approval gates; continuous validation via testing
5. **Code Review:** Once Phase 6 complete, open PR with all code for review

---

## Traceability & Artifacts

**Inputs:**
- docs/sdlc/requirements.md (functional & non-functional requirements)
- docs/sdlc/architecture.md (module design & structure)
- docs/sdlc/design-review.md (blockers, concerns, recommendations)

**Outputs:**
- docs/sdlc/implementation-plan.md (this document)
- docsync/ (module implementations)
- tests/ (test suites)
- docs/api/ (generated API documentation)
- requirements.txt (updated with dependencies)

**Next Stage:** Implementation-agent executes tasks in order, produces docsync modules and tests

---

**Planning Complete**  
**Prepared by:** planning-agent  
**Date:** September 10, 2026  
**Status:** Ready for implementation  
**Approval:** Not required (autonomous execution approved)  

*Note: Do not commit yet. This plan is ready for implementation-agent to execute.*
