# Implementation Plan

**Based On:** `docs/sdlc/architecture.md` (revised 2026-10-07) + `docs/sdlc/design-review.md` (human-approved)  
**Date:** 2026-10-07  
**Agent:** planning-agent  
**Stage:** 4 - Planning

---

## Overview

This plan defines 14 dependency-ordered implementation and verification tasks for the approved offline documentation-sync design. It uses the approved `models.py`, `parser.py`, `markdown_parser.py`, `generator.py`, `diff_engine.py`, `cli.py`, and `utils.py` boundaries; it does not add a cache or runtime dependencies.

**Estimated Complexity:**
- High: 4 tasks
- Medium: 8 tasks
- Low: 2 tasks

**Total Tasks:** 14

Implementation must use Python 3.9+ and the standard library at runtime. Do not modify the input schema or import/change the FastAPI app. Render the complete result before writing; keep report output separate from documentation output. The exact behavior for missing Markdown input is deliberately a decision task, not an assumed default.

---

## Task Breakdown

### Task 1: Package Foundation and Models
**ID:** TASK-001  
**Description:** Create the approved package/test structure and define shared typed dataclasses.  
**Priority:** CRITICAL  
**Complexity:** Low  
**Estimated Effort:** 15 minutes  
**Dependencies:** None  
**Blocks:** TASK-003 through TASK-014  
**Deliverables:** `docsync/__init__.py`, `docsync/models.py`, test package/fixture foundation as needed.

**Acceptance Criteria:**
- Models include `Parameter`, `Response`, `Endpoint`, `Schema`, `DocumentBlock`, `Document`, and `Changes` per the approved architecture.
- `DocumentBlock` retains its exact `raw_markdown` and optionally a parsed endpoint; `Document` has ordered blocks, parse warnings, and an `endpoints` property derived from recognized blocks.
- Public model fields have type hints compatible with Python 3.9+, and focused model tests confirm endpoint extraction does not reorder blocks or discard raw text.

---

### Task 2: Record Open Decisions and Markdown Conventions
**ID:** TASK-002  
**Description:** Resolve and record design-review decisions before implementing input interpretation or rendering.  
**Priority:** CRITICAL (blocks behavior-dependent work)  
**Complexity:** Medium  
**Estimated Effort:** 20 minutes  
**Dependencies:** TASK-001  
**Blocks:** TASK-003, TASK-004, TASK-005, TASK-006, TASK-008, TASK-010, TASK-011, TASK-012, TASK-013

**Decisions to capture:**
- **P1, warning vs. fatal Markdown behavior:** Define which parse conditions produce `Document.parse_warnings` and may continue, and which are validation failures (exit 2) that prevent output. Align malformed/ambiguous managed-section handling with the architecture error table; retain exact source Markdown on every successful path.
- **P2, offline reference scope:** State whether references to separately bundled local files are out of scope. Keep in-document JSON Pointer resolution and cycle detection; never fetch remote references. Do not silently widen scope.
- **P3, managed Markdown and comparison conventions:** Specify exact managed-section recognition/boundaries, custom-content preservation, generated-section ordering, and comparison normalization. Preserve endpoint identity as `(path, method)`; a method change is removal plus addition.
- **Missing Markdown input:** Decide and document whether a missing `--docs` input is a validation error or is treated as an empty document. The approved artifacts do not authorize a default policy.

**Acceptance Criteria:**
- The decisions are written in a traceable implementation note or the relevant module/CLI documentation before dependent behavior is coded.
- Each decision has examples/fixtures that distinguish the accepted behavior from the rejected alternative.
- Remote references remain rejected, and no schema-cache or missing-docs policy is introduced without an explicit recorded decision.

---

### Task 3: OpenAPI Parser
**ID:** TASK-003  
**Description:** Parse and validate OpenAPI 3.0/3.1 JSON into normalized schema and endpoint models.  
**Priority:** CRITICAL  
**Complexity:** High  
**Estimated Effort:** 30 minutes  
**Dependencies:** TASK-001, TASK-002  
**Blocks:** TASK-005, TASK-008, TASK-012, TASK-014  
**Deliverables:** `docsync/parser.py`.

**Acceptance Criteria:**
- `parse_openapi(file_path) -> Schema` validates JSON structure/version and extracts paths, methods, parameters, request bodies, responses, descriptions, tags, examples, and nested schema details when present.
- In-document JSON Pointer references resolve recursively; invalid pointers and cycles produce actionable validation errors. Remote references are never accessed; bundled local-file reference behavior follows TASK-002.
- Missing required schema fields are rejected rather than guessed/defaulted; schema input remains unchanged.
- Tests cover valid OpenAPI 3.0 and 3.1 inputs, malformed JSON/structure, unsupported version, nested/local references, invalid references, and cycles.

---

### Task 4: Source-Preserving Markdown Parser
**ID:** TASK-004  
**Description:** Parse Markdown according to the recorded managed-section convention into an ordered `Document`.  
**Priority:** CRITICAL  
**Complexity:** High  
**Estimated Effort:** 30 minutes  
**Dependencies:** TASK-001, TASK-002  
**Blocks:** TASK-005, TASK-006, TASK-010, TASK-012, TASK-014  
**Deliverables:** `docsync/markdown_parser.py`.

**Acceptance Criteria:**
- `parse_document(file_path) -> Document` recognizes endpoint sections and their comparison metadata under the TASK-002 convention.
- Blocks preserve their exact original Markdown and source order, including headers, footers, custom sections, and unrecognized content; parse warnings are exposed on the returned document.
- Warning/fatal cases follow P1 and do not permit a failed parse to overwrite output.
- Tests cover recognized sections, unmanaged/custom content, malformed and ambiguous sections, warning/fatal disposition, and exact raw Markdown preservation.

---

### Task 5: Document-Based Difference Engine
**ID:** TASK-005  
**Description:** Compare parsed document endpoints against current schema endpoints.  
**Priority:** CRITICAL  
**Complexity:** Medium  
**Estimated Effort:** 20 minutes  
**Dependencies:** TASK-001, TASK-002, TASK-003, TASK-004  
**Blocks:** TASK-006, TASK-011, TASK-012, TASK-014  
**Deliverables:** `docsync/diff_engine.py`.

**Acceptance Criteria:**
- `detect_changes(documented: Document, current: List[Endpoint]) -> Changes` consumes `Document` and indexes endpoints by `(path, method)`.
- Added, modified, and removed endpoints are classified per architecture; removed endpoints remain available for deprecation rendering.
- Equality considers descriptions, parameters, request bodies, response schemas, examples, and nested referenced schema data, using TASK-002 comparison conventions.
- A method change yields one removal and one addition; tests cover empty/equal documents and added, modified, removed, and method-changed endpoints.

---

### Task 6: Markdown Renderer and Report Formatter
**ID:** TASK-006  
**Description:** Render synchronized documentation from the parsed document and current endpoints, and format reports independently.  
**Priority:** CRITICAL  
**Complexity:** High  
**Estimated Effort:** 30 minutes  
**Dependencies:** TASK-001, TASK-002, TASK-004, TASK-005  
**Blocks:** TASK-008, TASK-011, TASK-012, TASK-014  
**Deliverables:** `docsync/generator.py`.

**Acceptance Criteria:**
- `render_document(document: Document, current_endpoints: List[Endpoint], changes: Changes) -> str` consumes the source-preserving document and current endpoints.
- New/modified endpoints render path, method, parameters, request body, responses, and examples when present; removed endpoints remain and are marked `[DEPRECATED]`.
- Unmanaged document blocks are reproduced exactly, and managed-block placement/order follows TASK-002. No API details absent from the schema are invented.
- `format_report` supports Markdown and JSON with added/modified/removed endpoints, timestamp, and schema version; it returns report content separately from rendered documentation.
- Tests validate both report formats, generated fields, deprecation, and exact preservation of untouched Markdown blocks.

---

### Task 7: Local File Utilities and Atomic Output
**ID:** TASK-007  
**Description:** Implement the approved local file and diagnostics helpers, including safe atomic replacement.  
**Priority:** HIGH  
**Complexity:** Medium  
**Estimated Effort:** 20 minutes  
**Dependencies:** TASK-001  
**Blocks:** TASK-008, TASK-012, TASK-014  
**Deliverables:** `docsync/utils.py`.

**Acceptance Criteria:**
- File helpers provide clear path-specific errors and use only standard-library APIs.
- Atomic writes stage the complete content in a temporary file in the destination directory and replace the destination only after successful rendering/write; a failure leaves any existing destination intact.
- Tests cover same-path input/output, distinct paths, permission/I/O failures, cleanup of temporary files, and behavior on supported platforms as available in local CI.
- Logging/output helpers do not mix diagnostics with report content.

---

### Task 8: CLI Orchestration and Output Contract
**ID:** TASK-008  
**Description:** Implement `docsync sync` orchestration and the approved CLI contract.  
**Priority:** CRITICAL  
**Complexity:** Medium  
**Estimated Effort:** 25 minutes  
**Dependencies:** TASK-002, TASK-003, TASK-004, TASK-005, TASK-006, TASK-007  
**Blocks:** TASK-012, TASK-013, TASK-014  
**Deliverables:** `docsync/cli.py`.

**Acceptance Criteria:**
- Supports `docsync sync --schema <path> --docs <path> --output <path> [--dry-run] [--format json|markdown] [--verbose]` using `argparse`.
- Applies the recorded missing-`--docs` decision. Parses and renders fully before writing; `--dry-run` performs no output write.
- Writes synchronized Markdown only to `--output`; writes the requested report to stdout and diagnostics/errors to stderr. The schema is read-only.
- Returns 0 on success/dry-run, 1 on operational/file/permission errors, and 2 on usage or validation failures, with concise actionable errors and verbose diagnostics only when requested.
- CLI tests confirm report/document separation, dry-run, exit codes, same-path output, and no write after validation failure.

---

### Task 9: OpenAPI Parser Unit Tests
**ID:** TASK-009  
**Description:** Complete focused parser test coverage with representative and failure fixtures.  
**Priority:** HIGH  
**Complexity:** Medium  
**Estimated Effort:** 20 minutes  
**Dependencies:** TASK-003  
**Blocks:** TASK-014

**Acceptance Criteria:**
- Parser-specific tests cover all TASK-003 acceptance cases, including OpenAPI 3.0/3.1 and reference error paths.
- Tests run offline and do not require importing the application or external services.
- Parser module coverage is reported and gaps are recorded for remediation before verification sign-off.

---

### Task 10: Markdown Parser Unit Tests
**ID:** TASK-010  
**Description:** Verify managed-section extraction, warning policy, and lossless raw-block retention.  
**Priority:** HIGH  
**Complexity:** Medium  
**Estimated Effort:** 20 minutes  
**Dependencies:** TASK-002, TASK-004  
**Blocks:** TASK-014

**Acceptance Criteria:**
- Fixtures exercise every managed heading/marker form selected in TASK-002 and both P1 warning and fatal cases.
- Tests assert exact source text and order for all preserved blocks, including whitespace and line endings represented by the parser contract.
- All parser warnings are deterministic and actionable; fatal validation cases cannot proceed to output writing in the CLI integration path.

---

### Task 11: Difference and Generator Unit Tests
**ID:** TASK-011  
**Description:** Test endpoint classification, Markdown merging, and report generation together at module boundaries.  
**Priority:** HIGH  
**Complexity:** Medium  
**Estimated Effort:** 25 minutes  
**Dependencies:** TASK-005, TASK-006  
**Blocks:** TASK-014

**Acceptance Criteria:**
- Tests cover added/modified/removed classification, method-change semantics, and comparison of all specified endpoint fields.
- Renderer tests prove exact preservation of unmanaged content and deprecation rather than deletion of removed endpoint sections.
- Markdown and JSON reports contain the same change classifications plus timestamp/version metadata and are not embedded into documentation output.

---

### Task 12: CLI Integration Tests
**ID:** TASK-012  
**Description:** Exercise the full local sync workflow through the CLI.  
**Priority:** HIGH  
**Complexity:** Medium  
**Estimated Effort:** 25 minutes  
**Dependencies:** TASK-003, TASK-004, TASK-005, TASK-006, TASK-007, TASK-008  
**Blocks:** TASK-014

**Acceptance Criteria:**
- End-to-end tests cover successful sync, dry-run, Markdown/JSON report selection, all exit-code classes, missing-docs decision, and source/output path equality.
- Tests assert report stdout is separate from documentation output and diagnostics use stderr.
- Invalid schema/managed Markdown and simulated output-write failure leave the existing destination uncorrupted.
- At least one fixture derived from a locally exported FastAPI OpenAPI schema is consumed without importing or mutating the application.

---

### Task 13: User-Facing CLI and Format Documentation
**ID:** TASK-013  
**Description:** Document command usage, managed Markdown conventions, report destinations, offline/reference scope, and failure behavior.  
**Priority:** MEDIUM  
**Complexity:** Low  
**Estimated Effort:** 15 minutes  
**Dependencies:** TASK-002, TASK-008  
**Blocks:** TASK-014  
**Deliverables:** Relevant README/module documentation and a representative sample if needed.

**Acceptance Criteria:**
- Documentation matches the implemented flags, stdout/stderr and file-output separation, exit codes, missing-docs decision, preservation rules, and reference scope.
- Instructions demonstrate offline use with a local OpenAPI JSON file and do not imply network access, YAML input, cache behavior, or unsupported defaults.
- A reader can identify how warnings differ from validation failures and how deprecated endpoints are represented.

---

### Task 14: Cross-Module Verification and Release Readiness
**ID:** TASK-014  
**Description:** Verify performance, coverage/reliability, and OS compatibility obligations V1–V3; resolve failures before handoff.  
**Priority:** HIGH (verification gate)  
**Complexity:** High  
**Estimated Effort:** 45 minutes  
**Dependencies:** TASK-007 through TASK-013  
**Blocks:** Implementation handoff

**Acceptance Criteria:**
- **V1 Performance:** With a representative fixture of up to 500 endpoints, parsing completes in under 2 seconds, generation in under 3 seconds, and total synchronization in under 5 seconds; record commands, fixture, and measurements.
- **V2 Reliability/coverage:** Run the complete suite, measure unit-test coverage greater than 80%, and verify malformed input, reference cycles, warning/fatal Markdown behavior, dry-run, failed writes, and atomic replacement do not corrupt existing documentation.
- **V3 Compatibility:** Run supported Python 3.9+ checks on macOS, Linux, and Windows. Verify CLI behavior and atomic replacement on each OS, including destination-local temporary files and replacement of an existing destination. Record any platform-specific limitation rather than claiming unverified support.
- Validate standard-library-only runtime dependencies, offline operation, report/output separation, and FastAPI-generated schema consumption.
- Publish a concise verification record with pass/fail evidence and unresolved issues; do not claim a gate passed without evidence.

---

## Dependency Graph

```text
TASK-001 (models/package)
  ├─> TASK-002 (P1-P3 + missing-docs decisions)
  │     ├─> TASK-003 (OpenAPI parser) ─────┐
  │     ├─> TASK-004 (Markdown parser) ────┼─> TASK-005 (Document-based diff)
  │     │                                  │       └─> TASK-006 (renderer/report)
  │     └──────────────────────────────────┘                │
  ├─> TASK-007 (atomic file utilities) ─────────────────────┤
  └─────────────────────────────────────────────────────────┴─> TASK-008 (CLI)

TASK-003 ─> TASK-009 (parser tests)
TASK-004 ─> TASK-010 (Markdown tests)
TASK-005 + TASK-006 ─> TASK-011 (diff/generator tests)
TASK-003..TASK-008 ─> TASK-012 (CLI integration tests)
TASK-002 + TASK-008 ─> TASK-013 (user documentation)
TASK-007..TASK-013 ─> TASK-014 (V1-V3 verification)
```

## Execution Order

1. TASK-001: Establish package and data model contracts.
2. TASK-002: Record P1-P3 and missing-Markdown-input decisions before dependent behavior is coded.
3. TASK-003 and TASK-004: Implement OpenAPI and source-preserving Markdown parsing.
4. TASK-005 and TASK-006: Implement `Document`-based comparison, rendering, and independent report formatting.
5. TASK-007 and TASK-008: Implement atomic local output and CLI orchestration/output contract.
6. TASK-009 through TASK-012: Complete module and end-to-end tests as implementation lands.
7. TASK-013: Document the implemented, decision-backed behavior.
8. TASK-014: Gather V1-V3 evidence and verify handoff criteria.

## Risk and Verification Notes

| Risk / condition | Planned control |
|---|---|
| Ambiguous or malformed Markdown could be overwritten | TASK-002 records P1; TASK-004/010 enforce it; TASK-008/012 prove failed validation does not write. |
| Reference handling could violate offline scope | TASK-002 records P2; TASK-003 rejects remote references and tests cycles/invalid pointers. |
| Markdown changes could erase custom content or create noisy diffs | TASK-002 records P3; TASK-004/006/010/011 assert exact untouched-block preservation and comparison rules. |
| Missing `--docs` behavior is unspecified | TASK-002 requires an explicit decision before CLI implementation; no implicit empty-document policy is assumed. |
| Interrupted/failed writes could corrupt documentation across platforms | TASK-007 and TASK-012 test destination preservation; TASK-014 verifies atomic replacement on macOS/Linux/Windows. |
| Performance or quality targets may be asserted without evidence | TASK-014 measures the exact V1 targets and greater-than-80% coverage and records V2/V3 evidence. |

## Traceability

- Architecture: `docs/sdlc/architecture.md` (revised module boundaries, `Document` interfaces, CLI, offline and atomic-write contracts).
- Design review: `docs/sdlc/design-review.md` (P1-P3 decisions and V1-V3 verification obligations).
- Requirements: `docs/sdlc/requirements.md` (FR-1 through FR-6; NFR-1 through NFR-4).
- Next stage: Implementation, after the explicit planning decisions in TASK-002 are recorded.

## Summary

The plan contains 14 ordered tasks, maps all seven approved modules to implementation and tests, and makes source preservation, report separation, offline behavior, and atomic replacement testable. P1-P3 and the unresolved missing-docs behavior are decision-gated; V1-V3 are explicit verification gates. No cache, YAML support, runtime dependency, implementation, or commit is included in this plan.
