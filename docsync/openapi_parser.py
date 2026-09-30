"""Load and parse OpenAPI 3.x JSON schemas into Endpoint models."""
import json
from pathlib import Path
from typing import List

from docsync.exceptions import DocSyncError, ValidationError
from docsync.models import Endpoint, Parameter, ResponseSummary

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "options", "head", "trace")


def load_openapi_schema(schema_path: str) -> dict:
    """Load and validate an OpenAPI 3.x schema file.

    Raises DocSyncError (exit 1) for missing/unreadable files, and
    ValidationError (exit 2) for invalid JSON or a non-OpenAPI-3.x shape.
    """
    path = Path(schema_path)

    if not path.exists() or not path.is_file():
        raise DocSyncError(f"Schema file not found: {schema_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Schema file is not valid JSON: {e}")
    except OSError as e:
        raise DocSyncError(f"Cannot read schema file {schema_path}: {e}")

    if not isinstance(schema, dict):
        raise ValidationError("Schema must be a JSON object")

    openapi_version = schema.get("openapi")
    if not isinstance(openapi_version, str) or not openapi_version.startswith("3."):
        raise ValidationError(
            "Schema missing or invalid 'openapi' field; expected an OpenAPI 3.x document "
            f"(got: {openapi_version!r})"
        )

    if "paths" not in schema or not isinstance(schema["paths"], dict):
        raise ValidationError("Schema missing required 'paths' object")

    return schema


def parse_endpoints(schema: dict) -> List[Endpoint]:
    """Extract Endpoint objects from an already-validated OpenAPI schema."""
    endpoints: List[Endpoint] = []

    for path, path_item in schema.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue

        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue

            parameters = []
            for param in operation.get("parameters", []):
                if not isinstance(param, dict):
                    continue
                param_schema = param.get("schema")
                parameters.append(
                    Parameter(
                        name=param.get("name", ""),
                        location=param.get("in"),
                        required=bool(param.get("required", False)),
                        schema_type=param_schema.get("type") if isinstance(param_schema, dict) else None,
                        description=param.get("description"),
                    )
                )

            responses = []
            for status_code, response in operation.get("responses", {}).items():
                if not isinstance(response, dict):
                    continue
                responses.append(
                    ResponseSummary(
                        status_code=str(status_code),
                        description=response.get("description"),
                    )
                )

            endpoints.append(
                Endpoint(
                    path=path,
                    method=method.upper(),
                    summary=operation.get("summary"),
                    description=operation.get("description"),
                    parameters=parameters,
                    responses=responses,
                )
            )

    endpoints.sort(key=Endpoint.sort_key)
    return endpoints
