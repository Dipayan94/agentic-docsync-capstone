"""OpenAPI schema loading and validation."""

import json
from typing import Any, List, Dict, Optional
from docsync import ValidationError


def load_openapi_schema(path: str) -> dict:
    """
    Load and validate an OpenAPI 3.x schema from a JSON file.
    
    Args:
        path: Path to the OpenAPI JSON file
        
    Returns:
        Parsed schema as a dictionary
        
    Raises:
        ValidationError: If the file cannot be parsed or is not a valid OpenAPI 3.x schema
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in schema file: {e}")
    except FileNotFoundError:
        raise ValidationError(f"Schema file not found: {path}")
    except Exception as e:
        raise ValidationError(f"Error reading schema file: {e}")
    
    # Validate required OpenAPI 3.x structure
    if not isinstance(schema, dict):
        raise ValidationError("Schema must be a JSON object")
    
    if "openapi" not in schema:
        raise ValidationError("Schema missing required 'openapi' field")
    
    openapi_version = schema.get("openapi", "")
    if not isinstance(openapi_version, str) or not openapi_version.startswith("3."):
        raise ValidationError(f"Only OpenAPI 3.x is supported, got version: {openapi_version}")
    
    if "paths" not in schema:
        raise ValidationError("Schema missing required 'paths' field")
    
    if not isinstance(schema["paths"], dict):
        raise ValidationError("'paths' field must be an object")
    
    return schema


class Endpoint:
    """Represents an API endpoint extracted from an OpenAPI schema."""
    
    def __init__(self, method: str, path: str, summary: str = "", 
                 description: str = "", parameters: Optional[list] = None, responses: Optional[dict] = None):
        self.method = method.upper()
        self.path = path
        self.summary = summary
        self.description = description
        self.parameters = parameters or []
        self.responses = responses or {}
    
    def __repr__(self):
        return f"Endpoint({self.method} {self.path})"
    
    def identifier(self) -> str:
        """Return a stable identifier for this endpoint."""
        return f"{self.method} {self.path}"


def extract_endpoints(schema: dict) -> List[Endpoint]:
    """
    Extract endpoint information from an OpenAPI schema.
    
    Args:
        schema: Parsed OpenAPI schema dictionary
        
    Returns:
        List of Endpoint objects, sorted by path then method for deterministic ordering
    """
    endpoints = []
    paths = schema.get("paths", {})
    
    # HTTP methods we care about (lowercase as they appear in OpenAPI)
    http_methods = {"get", "post", "put", "patch", "delete", "options", "head"}
    
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
            
        for method, operation in path_item.items():
            if method.lower() not in http_methods:
                continue
            
            if not isinstance(operation, dict):
                continue
            
            endpoint = Endpoint(
                method=method,
                path=path,
                summary=operation.get("summary", ""),
                description=operation.get("description", ""),
                parameters=operation.get("parameters", []),
                responses=operation.get("responses", {})
            )
            endpoints.append(endpoint)
    
    # Sort for deterministic output: by path first, then by method
    endpoints.sort(key=lambda e: (e.path, e.method))
    
    return endpoints
