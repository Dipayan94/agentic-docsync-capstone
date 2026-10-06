"""OpenAPI 3.0/3.1 JSON validation and normalization."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import unquote

from .models import Endpoint, Parameter, Response, Schema, ValidationError

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def _resolve(value: Any, root: Dict[str, Any], stack: Tuple[str, ...] = ()) -> Any:
    """Resolve in-document references recursively and reject external/cyclic refs."""
    if isinstance(value, list):
        return [_resolve(item, root, stack) for item in value]
    if not isinstance(value, dict):
        return value
    if "$ref" in value:
        reference = value["$ref"]
        if not isinstance(reference, str) or not reference.startswith("#"):
            raise ValidationError(f"External reference is not supported: {reference!r}")
        if reference in stack:
            raise ValidationError(f"Reference cycle detected: {' -> '.join(stack + (reference,))}")
        target: Any = root
        encoded_fragment = reference[1:]
        if re.search(r"%(?![0-9A-Fa-f]{2})", encoded_fragment):
            raise ValidationError(f"Invalid JSON Pointer encoding: {reference!r}")
        fragment = unquote(encoded_fragment)
        if fragment:
            if not fragment.startswith("/"):
                raise ValidationError(f"Invalid JSON Pointer reference: {reference!r}")
            for raw_token in fragment[1:].split("/"):
                if re.search(r"~(?![01])", raw_token):
                    raise ValidationError(f"Invalid JSON Pointer escape: {reference!r}")
                pointer_segment = raw_token.replace("~1", "/").replace("~0", "~")
                if isinstance(target, list):
                    if not re.fullmatch(r"0|[1-9][0-9]*", pointer_segment):
                        raise ValidationError(f"Invalid array index in JSON Pointer: {reference!r}")
                    try:
                        target = target[int(pointer_segment)]
                    except (ValueError, IndexError) as error:
                        raise ValidationError(f"Invalid JSON Pointer reference: {reference!r}") from error
                elif isinstance(target, dict) and pointer_segment in target:
                    target = target[pointer_segment]
                else:
                    raise ValidationError(f"Invalid JSON Pointer reference: {reference!r}")
        resolved = _resolve(target, root, stack + (reference,))
        siblings = {key: item for key, item in value.items() if key != "$ref"}
        if siblings and isinstance(resolved, dict):
            resolved = dict(resolved)
            resolved.update(_resolve(siblings, root, stack))
        return resolved
    return {key: _resolve(item, root, stack) for key, item in value.items()}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _field_text(value: Any, where: str, required: bool = False) -> str:
    if value is None and not required:
        return ""
    _require(isinstance(value, str), f"{where} must be a string")
    if required:
        _require(bool(value.strip()), f"{where} must not be empty")
    return value


def _schema_type(schema: Dict[str, Any]) -> str:
    value = schema.get("type", "object" if "properties" in schema else "unspecified")
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return str(value)


def _extract_examples(value: Any, prefix: str, result: Dict[str, Any]) -> None:
    if not isinstance(value, dict):
        return
    if "example" in value:
        result[prefix] = value["example"]
    examples = value.get("examples")
    if isinstance(examples, dict):
        for name, example in examples.items():
            result[f"{prefix}.{name}"] = example.get("value", example) if isinstance(example, dict) else example


def _parse_endpoint(path: str, method: str, path_item: Dict[str, Any], operation: Any,
                    root: Dict[str, Any]) -> Endpoint:
    _require(isinstance(operation, dict), f"Operation {method.upper()} {path} must be an object")
    operation = _resolve(operation, root)
    summary = _field_text(operation.get("summary"), f"{method.upper()} {path} summary")
    description = _field_text(operation.get("description"), f"{method.upper()} {path} description")
    tags = operation.get("tags", [])
    _require(isinstance(tags, list) and all(isinstance(tag, str) for tag in tags),
             f"{method.upper()} {path} tags must be an array of strings")

    path_parameters = path_item.get("parameters", [])
    operation_parameters = operation.get("parameters", [])
    _require(isinstance(path_parameters, list), f"Path parameters for {path} must be an array")
    _require(isinstance(operation_parameters, list),
             f"Parameters for {method.upper()} {path} must be an array")
    raw_parameters = path_parameters + operation_parameters
    parameter_map: Dict[Tuple[str, str], Parameter] = {}
    examples: Dict[str, Any] = {}
    for index, raw_parameter in enumerate(raw_parameters):
        parameter = _resolve(raw_parameter, root)
        _require(isinstance(parameter, dict), f"Parameter {index} for {method.upper()} {path} must be an object")
        name = _field_text(parameter.get("name"), "Parameter name", required=True)
        location = _field_text(parameter.get("in"), f"Parameter {name} location", required=True)
        _require(location in {"path", "query", "header", "cookie"}, f"Invalid parameter location: {location}")
        _require("schema" in parameter or "content" in parameter,
                 f"Parameter {name} must define schema or content")
        parameter_schema = parameter.get("schema", {"content": parameter.get("content", {})})
        _require(isinstance(parameter_schema, dict), f"Parameter {name} schema must be an object")
        required = parameter.get("required", False)
        _require(isinstance(required, bool), f"Parameter {name} required must be boolean")
        if location == "path":
            _require(required, f"Path parameter {name} must be required")
        parameter_map[(name, location)] = Parameter(
            name=name,
            location=location,
            type=_schema_type(parameter_schema),
            required=required,
            description=_field_text(parameter.get("description"), f"Parameter {name} description"),
            schema=parameter_schema,
        )
        _extract_examples(parameter, f"parameters.{location}.{name}", examples)
        _extract_examples(parameter_schema, f"parameters.{location}.{name}.schema", examples)

    request_body = operation.get("requestBody")
    if request_body is not None:
        request_body = _resolve(request_body, root)
        _require(isinstance(request_body, dict), f"Request body for {method.upper()} {path} must be an object")
        if "required" in request_body:
            _require(isinstance(request_body["required"], bool),
                     f"Request body required for {method.upper()} {path} must be boolean")
        _require("content" in request_body, f"Request body for {method.upper()} {path} must define content")
        request_content = request_body["content"]
        _require(isinstance(request_content, dict),
                 f"Request body content for {method.upper()} {path} must be an object")
        _extract_examples(request_body, "requestBody", examples)
        for media_type, media in request_content.items():
            _require(isinstance(media, dict), f"Request body media {media_type} must be an object")
            _extract_examples(media, f"requestBody.{media_type}", examples)

    raw_responses = operation.get("responses")
    _require(isinstance(raw_responses, dict) and bool(raw_responses),
             f"Operation {method.upper()} {path} must define at least one response")
    responses: Dict[str, Response] = {}
    for status_code, raw_response in raw_responses.items():
        response = _resolve(raw_response, root)
        _require(isinstance(response, dict), f"Response {status_code} for {method.upper()} {path} must be an object")
        response_description = _field_text(response.get("description"),
                                           f"Response {status_code} description", required=True)
        content = response.get("content", {})
        _require(isinstance(content, dict), f"Response {status_code} content must be an object")
        for media_type, media in content.items():
            _require(isinstance(media, dict), f"Response {status_code} media {media_type} must be an object")
        schemas = {media: definition.get("schema") for media, definition in content.items()
                   if isinstance(definition, dict) and "schema" in definition}
        responses[str(status_code)] = Response(
            status_code=str(status_code), description=response_description,
            schema=next(iter(schemas.values())) if len(schemas) == 1 else (schemas or None),
            content=content,
        )
        for media_type, media in content.items():
            _extract_examples(media, f"responses.{status_code}.{media_type}", examples)

    return Endpoint(
        path=path, method=method.upper(), summary=summary, description=description,
        parameters=list(parameter_map.values()), request_body=request_body,
        responses=responses, tags=list(tags), examples=examples,
    )


def extract_endpoints(openapi_dict: Dict[str, Any]) -> List[Endpoint]:
    """Validate and normalize all operations from an OpenAPI document."""
    _require(isinstance(openapi_dict, dict), "OpenAPI document root must be an object")
    version = openapi_dict.get("openapi")
    _require(isinstance(version, str) and re.match(r"^3\.(0|1)(\.|$)", version) is not None,
             f"Unsupported or missing OpenAPI version: {version!r}; expected 3.0 or 3.1")
    info = openapi_dict.get("info")
    _require(isinstance(info, dict), "OpenAPI field 'info' must be an object")
    _field_text(info.get("title"), "info.title", required=True)
    _field_text(info.get("version"), "info.version", required=True)
    description = _field_text(info.get("description"), "info.description")
    paths = openapi_dict.get("paths")
    _require(isinstance(paths, dict), "OpenAPI field 'paths' must be an object")
    endpoints: List[Endpoint] = []
    seen_identities = set()
    for path, original_path_item in paths.items():
        _require(isinstance(path, str) and path.startswith("/"), f"Invalid OpenAPI path: {path!r}")
        path_item = _resolve(original_path_item, openapi_dict)
        _require(isinstance(path_item, dict), f"Path item {path!r} must be an object")
        path_parameters = path_item.get("parameters", [])
        _require(isinstance(path_parameters, list), f"Path parameters for {path} must be an array")
        for method, operation in path_item.items():
            if method.lower() in HTTP_METHODS:
                endpoint = _parse_endpoint(path, method, path_item, operation, openapi_dict)
                identity = (endpoint.path, endpoint.method)
                if identity in seen_identities:
                    raise ValidationError(f"Duplicate operation identity: {endpoint.method} {endpoint.path}")
                seen_identities.add(identity)
                endpoints.append(endpoint)
    return endpoints


def parse_openapi(file_path: str) -> Schema:
    """Read, validate, and normalize an OpenAPI 3.0/3.1 JSON file.

    Raises `OSError` for file access errors and `ValidationError` for invalid
    JSON, schema structure, references, or operation data.
    """
    try:
        with Path(file_path).open("r", encoding="utf-8") as source:
            data = json.load(source)
    except json.JSONDecodeError as error:
        raise ValidationError(f"Invalid JSON in {file_path}: {error}") from error
    except UnicodeDecodeError as error:
        raise ValidationError(f"Schema is not UTF-8 JSON in {file_path}: {error}") from error
    endpoints = extract_endpoints(data)
    info = data["info"]
    description = info.get("description", "")
    return Schema(title=info["title"], version=info["version"], endpoints=endpoints,
                  openapi_version=data["openapi"], description=description)
