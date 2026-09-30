from pathlib import Path

import pytest

from docsync.exceptions import DocSyncError, ValidationError
from docsync.openapi_parser import load_openapi_schema, parse_endpoints

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_valid_schema():
    schema = load_openapi_schema(str(FIXTURES / "valid_openapi.json"))
    assert schema["openapi"].startswith("3.")
    assert "paths" in schema


def test_load_missing_file_raises_docsync_error():
    with pytest.raises(DocSyncError):
        load_openapi_schema(str(FIXTURES / "does_not_exist.json"))


def test_load_invalid_json_raises_validation_error():
    with pytest.raises(ValidationError):
        load_openapi_schema(str(FIXTURES / "invalid.json"))


def test_load_non_openapi3_raises_validation_error():
    with pytest.raises(ValidationError):
        load_openapi_schema(str(FIXTURES / "not_openapi3.json"))


def test_load_missing_paths_raises_validation_error():
    with pytest.raises(ValidationError):
        load_openapi_schema(str(FIXTURES / "missing_paths_openapi.json"))


def test_parse_endpoints_extracts_all_methods_sorted():
    schema = load_openapi_schema(str(FIXTURES / "valid_openapi.json"))
    endpoints = parse_endpoints(schema)

    assert [(e.path, e.method) for e in endpoints] == [
        ("/users", "GET"),
        ("/users", "POST"),
        ("/users/{id}", "GET"),
    ]


def test_parse_endpoints_captures_parameters_and_responses():
    schema = load_openapi_schema(str(FIXTURES / "valid_openapi.json"))
    endpoints = parse_endpoints(schema)
    get_users = next(e for e in endpoints if e.path == "/users" and e.method == "GET")

    assert get_users.summary == "List users"
    assert get_users.parameters[0].name == "limit"
    assert get_users.parameters[0].location == "query"
    assert {r.status_code for r in get_users.responses} == {"200", "500"}


def test_parse_endpoints_empty_paths_returns_empty_list():
    schema = load_openapi_schema(str(FIXTURES / "empty_paths_openapi.json"))
    assert parse_endpoints(schema) == []
