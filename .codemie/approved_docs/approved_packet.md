FEATURE_BRANCH: feature/capstone-prd_docsync-cli-report
```markdown
# APPROVED PACKET (HITL Approved)

## Repo
- url: https://github.com/Dipayan94/agentic-docsync-capstone
- base_branch: main

## Feature Branch
feature/capstone-prd_docsync-cli-report

## In Scope
- Implement DocsSync CLI MVP to generate/update markdown API docs from an OpenAPI JSON file:
  - Command: `docsync sync --schema <path> --docs <path> --output <path> [--dry-run] [--verbose] [--format json|markdown]`
  - (Implementation may use `python -m docsync ...` via `docsync/__main__.py` rather than packaging console_scripts.)
- Generate a deterministic markdown output describing endpoints from OpenAPI 3.x schema:
  - For each endpoint: path + HTTP method, summary/description (if present), parameters, responses.
- Produce a sync report to stdout in:
  - Human-readable markdown (default), and
  - JSON when `--format json` is provided.
- Preserve custom documentation content using marker-based generated region insertion/replacement.
- Add local unit tests with pytest (fixtures + CLI behavior tests).

## Out of Scope
- Full markdown diff engine that parses arbitrary existing docs and computes added/modified/removed endpoints.
- Advanced OpenAPI `$ref` dereferencing / deep schema rendering (MVP may render shallow types or `$ref` as-is).
- Fetching schema from URL / running FastAPI to retrieve `/openapi.json` (offline local-file schema only).
- Deployment steps or CI/CD changes beyond adding pytest dependency locally.

## Locked Decisions
- url_timeout_seconds: 5
- markers:
  begin: <!-- DOCSYNC:BEGIN GENERATED -->
  end: <!-- DOCSYNC:END GENERATED -->
- marker_policy:
  - markers_exist: replace content strictly between begin/end markers
  - no_markers: append a new generated block at end of file (do not overwrite existing content)
  - malformed_markers: exit code 2 (validation failure) with a clear error message
- exit_codes:
  0: success
  1: operational error
  2: validation failure

## Stories + Acceptance Criteria

### Story 1 — CLI MVP: Generate/sync markdown docs from OpenAPI JSON
As an API developer, I want a CLI command to generate/update markdown API docs from an OpenAPI JSON file, so that documentation stays consistent with the API.

**Acceptance Criteria**
1. Running `docsync sync --schema <valid_openapi.json> --docs <existing_or_new_docs.md> --output <out.md>` produces a markdown file at `<out.md>` (unless `--dry-run`).
2. The output markdown includes, for each endpoint:
   - Path + HTTP method
   - Summary/description when present
   - Parameters (name, location if available, required flag, schema type if available)
   - Responses (HTTP status codes; description if present)
3. With `--dry-run`, the CLI does **not write** `<out.md>` but still prints a report to stdout; exit code is 0.
4. If the schema path is missing/unreadable, exit code is **1** and error message includes the file path.
5. If schema JSON is malformed OR fails basic OpenAPI structural validation (e.g., missing `openapi` or `paths`), exit code is **2** with clear validation error.

**Edge Cases**
- Empty `paths` → output still created (unless dry-run) with header + “no endpoints found”; exit 0.
- Missing `parameters`/`responses` fields → render consistently (e.g., “None” or omitted).
- Multiple methods per path → render each method separately.

---

### Story 2 — Sync report to stdout in human-readable + JSON formats
As an API developer, I want a sync report that summarizes what documentation was generated/updated, so that I can quickly understand changes.

**Acceptance Criteria**
1. Default stdout report is human-readable and contains:
   - Timestamp (consistent format; local or UTC acceptable)
   - Total endpoints processed
   - Deterministic ordering of endpoint list (sort by path then method)
2. With `--format json`, stdout is valid JSON including at least:
   - `timestamp`
   - `endpoints_total`
   - `endpoints` list (method + path identifiers)
3. Report generation works with `--dry-run` (does not depend on writing output).
4. Unsupported `--format` value triggers exit code **2** with a clear validation error.

## Unit Test Plan (pytest)
- dependency:
  - ensure pytest is present in requirements.txt (Agent 04 will add if missing)
- structure:
  - create tests/ folder at repo root
- commands:
  - {{test_command}} = `python -m pytest -q`
- pass_criteria:
  - all tests pass locally before push/PR
- evidence:
  - create `.codemie/approved_docs/test_report.md`

**Planned Tests (minimum)**
- `tests/test_openapi_parser.py`
  - Valid OpenAPI fixture loads and endpoints are sorted by path then method
  - Invalid JSON triggers validation failure behavior (exit 2 via CLI test)
  - Missing required keys (e.g., `paths`) triggers validation failure
- `tests/test_markdown_generator.py`
  - Markdown includes expected method/path for fixture endpoints
  - Parameters/responses sections render consistently
- `tests/test_markers.py`
  - Both markers exist → only generated region replaced
  - No markers → generated block appended
  - Malformed markers (only begin or only end, or inverted) → ValidationError (exit 2 via CLI test)
- `tests/test_cli.py`
  - `--dry-run` does not write output file; exit 0
  - Non-dry-run writes output file; exit 0
  - `--format json` outputs parseable JSON with required fields
  - Invalid `--format` exits 2

## Gherkin (Final)
```gherkin
Feature: DocSync CLI generates markdown from OpenAPI schema

  Scenario: Generate markdown from a valid OpenAPI schema
    Given a valid OpenAPI 3.x JSON file "tests/fixtures/sample_openapi.json"
    When I run "docsync sync --schema tests/fixtures/sample_openapi.json --docs docs/api/api.md --output /tmp/api.md"
    Then the exit code should be 0
    And the file "/tmp/api.md" should exist
    And the markdown should contain "GET /items"
    And the markdown should contain "POST /items/{item_name}/{quantity}"

  Scenario: Dry run does not write output file
    Given a valid OpenAPI 3.x JSON file "tests/fixtures/sample_openapi.json"
    When I run "docsync sync --schema tests/fixtures/sample_openapi.json --docs docs/api/api.md --output /tmp/api.md --dry-run"
    Then the exit code should be 0
    And the file "/tmp/api.md" should not exist
    And stdout should contain "Report"

  Scenario: Invalid JSON schema returns validation failure
    Given an invalid JSON file "tests/fixtures/invalid_openapi.json"
    When I run "docsync sync --schema tests/fixtures/invalid_openapi.json --docs docs/api/api.md --output /tmp/api.md"
    Then the exit code should be 2
    And stderr should contain "Invalid JSON"

Feature: DocSync report formats

  Scenario: Report outputs JSON when requested
    Given a valid OpenAPI 3.x JSON file "tests/fixtures/sample_openapi.json"
    When I run "docsync sync --schema tests/fixtures/sample_openapi.json --docs docs/api/api.md --output /tmp/api.md --dry-run --format json"
    Then the exit code should be 0
    And stdout should be valid JSON
    And the JSON should include field "endpoints_total"
```

## Implementation Plan
- [ ] Create `docsync/` package (minimal MVP)
  - [ ] `docsync/__init__.py`
  - [ ] `docsync/__main__.py` to support `python -m docsync ...`
  - [ ] `docsync/exceptions.py` (ValidationError, DocSyncError)
  - [ ] `docsync/models.py` (dataclasses for Endpoint, Parameter, ResponseSummary, SyncReport)
- [ ] Implement OpenAPI loader + validator
  - [ ] `docsync/openapi_parser.py`
    - [ ] Load JSON from `--schema` path
    - [ ] Validate `openapi` and `paths`
    - [ ] Extract endpoints (path + method) and basic metadata
    - [ ] Deterministic ordering: sort by path then method
- [ ] Implement deterministic Markdown generator
  - [ ] `docsync/markdown_generator.py`
    - [ ] Render stable header + endpoint sections
    - [ ] Render summary/description, parameters, responses
- [ ] Implement marker-based merge to preserve custom content
  - [ ] `docsync/markers.py`
    - [ ] If both markers exist: replace only generated region
    - [ ] If no markers: append generated block at end
    - [ ] If malformed markers: raise ValidationError (exit 2)
- [ ] Implement reporting
  - [ ] `docsync/reporting.py`
    - [ ] Produce report object (timestamp, endpoints_total, endpoints list)
    - [ ] Output markdown (default) or JSON via `--format json`
- [ ] Implement CLI entrypoint and exit code mapping
  - [ ] `docsync/cli.py` using `argparse`
    - [ ] `sync` subcommand with `--schema --docs --output --dry-run --verbose --format`
    - [ ] Map errors to exit codes (0/1/2) per Locked Decisions
- [ ] Update README with usage examples (including marker explanation)
- [ ] Add pytest + tests + fixtures
  - [ ] Add fixtures under `tests/fixtures/`
  - [ ] Ensure `python -m pytest -q` passes locally
  - [ ] Write `.codemie/approved_docs/test_report.md` after local run

## Commit Plan (3–6 commits)
1. **[DocsSync] Scaffold package + exceptions/models + __main__**
2. **[DocsSync] Implement OpenAPI parser + markdown generator**
3. **[DocsSync] Add marker merge + reporting**
4. **[DocsSync] Implement CLI sync with exit codes and args validation**
5. **[Test] Add pytest dependency + tests/fixtures + unit tests**
6. **[Docs] Update README with DocSync usage and marker policy**

## Definition of Done
- Feature implemented on branch `feature/capstone-prd_docsync-cli-report` from `main`.
- CLI supports `sync` with required args and flags; behaves per Acceptance Criteria.
- Marker policy implemented exactly as Locked Decisions.
- Exit codes implemented exactly as Locked Decisions:
  - 0 success, 1 operational error, 2 validation failure.
- Local unit tests exist under `tests/` and pass:
  - Run: `python -m pytest -q`
- Evidence produced:
  - `.codemie/approved_docs/test_report.md` created/updated after running tests locally.
- Changes committed in 3–6 commits and branch pushed to origin (ready for Agent 05 PR creation).

Reminder: Copy this entire Approved Packet to {{approved_packet_local_path}}, then implement locally, run tests, commit, and push the branch.
```