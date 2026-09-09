"""
OpenAPI parser module.
"""
import json
from pathlib import Path
from typing import List

from docsync.exceptions import ValidationError, DocSyncError
from docsync.models import Endpoint, Parameter, ResponseSummary


def load_openapi_schema(schema_path: str) -> dict:
    """
    Load and validate OpenAPI schema from file.
    
    Args:
        schema_path: Path to OpenAPI JSON file
        
    Returns:
        Parsed OpenAPI schema dict
        
    Raises:
        DocSyncError: If file cannot be read (exit 1)
        ValidationError: If JSON is invalid or schema is malformed (exit 2)
    """
    path = Path(schema_path)
    
    # Check if file exists and is readable
    if not path.exists():
        raise DocSyncError(f"Schema file not found: {schema_path}")
    
    if not path.is_file():
        raise DocSyncError(f"Schema path is not a file: {schema_path}")
    
    # Read and parse JSON
    try:
        with open(path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in schema file: {e}")
    except IOError as e:
        raise DocSyncError(f"Cannot read schema file {schema_path}: {e}")
    
    # Validate basic OpenAPI structure
    if not isinstance(schema, dict):
        raise ValidationError("Schema must be a JSON object")
    
    if "openapi" not in schema:
        raise ValidationError("Missing required field 'openapi' in schema")
    
    if "paths" not in schema:
        raise ValidationError("Missing required field 'paths' in schema")
    
    return schema


def parse_endpoints(schema: dict) -> List[Endpoint]:
    """
    Extract endpoints from OpenAPI schema.
    
    Args:
        schema: Parsed OpenAPI schema
        
    Returns:
        List of Endpoint objects, sorted by path then method
    """
    endpoints = []
    paths = schema.get("paths", {})
    
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
            
        # Iterate over HTTP methods
        http_methods = ["get", "post", "put", "patch", "delete", "options", "head", "trace"]
        for method in http_methods:
            if method not in path_item:
                continue
                
            operation = path_item[method]
            if not isinstance(operation, dict):
                continue
            
            # Extract parameters
            parameters = []
            for param in operation.get("parameters", []):
                if not isinstance(param, dict):
                    continue
                    
                parameters.append(Parameter(
                    name=param.get("name", ""),
                    location=param.get("in"),
                    required=param.get("required", False),
                    schema_type=param.get("schema", {}).get("type") if isinstance(param.get("schema"), dict) else None,
                    description=param.get("description")
                ))
            
            # Extract responses
            responses = []
            for status_code, response in operation.get("responses", {}).items():
                if not isinstance(response, dict):
                    continue
                    
                responses.append(ResponseSummary(
                    status_code=str(status_code),
                    description=response.get("description")
                ))
            
            # Create endpoint
            endpoint = Endpoint(
                path=path,
                method=method.upper(),
                summary=operation.get("summary"),
                description=operation.get("description"),
                parameters=parameters,
                responses=responses
            )
            endpoints.append(endpoint)
    
    # Sort deterministically by path then method
    endpoints.sort()
    
    return endpoints
