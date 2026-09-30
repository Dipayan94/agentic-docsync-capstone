# Test Report — DocSync CLI MVP (Dry-Run + Atomic Write)

- **Date/time:** 2026-09-30T04:32:42Z
- **Branch:** feature/capstone-prd_docsync-cli-mvp
- **Approved packet:** `.codemie/approved_docs/approved_packet.md` (fetched from Confluence page 1146881)
- **Python:** 3.9.6
- **Pytest:** 8.4.2

## Commands executed

```bash
python3 -m pytest -q
```

## Results summary

```
.................................                                        [100%]
33 passed in 0.03s
```

All 33 tests passed. No failures, no skips.

## Coverage of approved packet requirements

- `tests/test_openapi_parser.py` — schema loading/validation (missing file → exit 1 path,
  invalid JSON, non-3.x `openapi` version, missing `paths`), endpoint extraction/sorting,
  parameter/response capture, empty-paths case.
- `tests/test_markdown_generator.py` — deterministic markdown template, marker wrapping,
  empty-endpoint skeleton output.
- `tests/test_doc_writer.py` — marker policy (`markers_exist` replace, `no_markers` append,
  malformed-marker rejection), atomic write success and failure-leaves-original-untouched.
- `tests/test_report.py` — report always populates `added` only (MVP; no deep diff), JSON
  shape has `added`/`modified`/`removed` keys.
- `tests/test_cli.py` — end-to-end `docsync sync` behavior matching the approved Gherkin:
  first-run generation, `--format json`, `--dry-run` (no file write), invalid-schema exit 2,
  missing-schema exit 1, missing-openapi-keys exit 2, empty-paths exit 0 with 0 endpoints,
  marker-preserving merge, malformed-marker exit 2.

## Notes / limitations

- Per the approved packet's Definition of Done, the MVP sync report only populates `added`
  (no diffing against a previous run's state — that is explicitly out of scope).
  `modified`/`removed` are always empty lists in this MVP.
- The locked decision `url_timeout_seconds: 5` is not exercised by any code path: remote
  schema fetching from URLs is explicitly out of scope for this packet, so no HTTP/timeout
  logic was implemented.
- Tests were run with the system `python3` (3.9.6) rather than the repo's `.venv`; `pytest`
  was already available in that interpreter and all tests passed. `pytest==8.4.2` was added
  to `requirements.txt` to match the tested version.
