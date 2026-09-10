"""
OpenAPI 3.1.0 parser: Extract endpoint metadata from FastAPI schemas.

This module implements BLOCKER #1 (Schema Validation): It validates the
OpenAPI structure before parsing to prevent crashes on malformed input.
Validation rules include checking for required fields, valid types, and
detecting schema references ($ref) that require special handling.
"""

from typing import Dict, Any, List, Optional
from docsync.models import Endpoint, Parameter, Response, Schema, ValidationError
from docsync.utils import get_logger, read_json

logger = get_logger(__name__)


class SchemaValidator:
    """Validates OpenAPI 3.1.0 schema structure."""

    @staticmethod
    def validate_openapi_structure(data: Dict[str, Any]) -> List[ValidationError]:
        """
        Validate OpenAPI schema structure and return list of errors found.
        
        Returns:
            List of ValidationError objects. Empty list means schema is valid.
        """
        errors = []

        # Check root-level required fields
        if "openapi" not in data:
            errors.append(ValidationError(
                message="Missing required field: 'openapi'",
                code="MISSING_OPENAPI_VERSION"
            ))
        elif not data["openapi"].startswith("3."):
            errors.append(ValidationError(
                message=f"Unsupported OpenAPI version: {data['openapi']}. Expected 3.x",
                code="UNSUPPORTED_VERSION"
            ))

        if "info" not in data:
            errors.append(ValidationError(
                message="Missing required field: 'info'",
                code="MISSING_INFO"
            ))
        elif not isinstance(data["info"], dict):
            errors.append(ValidationError(
                message="Field 'info' must be an object",
                code="INVALID_INFO_TYPE"
            ))

        # Paths is optional in OpenAPI 3.1.0 (can be empty)
        if "paths" in data and not isinstance(data["paths"], dict):
            errors.append(ValidationError(
                message="Field 'paths' must be an object",
                code="INVALID_PATHS_TYPE"
            ))

        # If there are paths, validate their structure
        if "paths" in data and isinstance(data["paths"], dict):
            for path_key, path_item in data["paths"].items():
                if not isinstance(path_item, dict):
                    errors.append(ValidationError(
                        message=f"Path '{path_key}' must be an object",
                        code="INVALID_PATH_ITEM"
                    ))
                    continue

                # Check for valid HTTP methods
                valid_methods = {"get", "post", "put", "delete", "patch", "options", "head"}
                path_methods = [k.lower() for k in path_item.keys() if k.lower() in valid_methods]
                
                if not path_methods and "parameters" not in path_item:
                    logger.warning(f"Path '{path_key}' has no endpoints or parameters")

        return errors


class OpenAPIParser:
    """Parses OpenAPI 3.1.0 schemas and extracts endpoint metadata."""

    @staticmethod
    def parse(file_path: str) -> Schema:
        """
        Parse OpenAPI schema from JSON file.
        
        Args:
            file_path: Path to openapi.json file
        
        Returns:
            Parsed Schema object with endpoints
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is malformed
            ValidationError: If OpenAPI structure is invalid
        """
        logger.info(f"Parsing OpenAPI schema from {file_path}")
        
        # Load JSON
        try:
            data = read_json(file_path)
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Failed to load schema: {e}")
            raise

        # Validate structure (BLOCKER #1)
        validator = SchemaValidator()
        validation_errors = validator.validate_openapi_structure(data)
        
        if validation_errors:
            error_messages = "\n".join(str(e) for e in validation_errors)
            logger.error(f"Schema validation failed:\n{error_messages}")
            raise ValueError(f"Invalid OpenAPI schema. Errors:\n{error_messages}")

        logger.info("Schema validation passed")

        # Create Schema object
        info = data.get("info", {})
        schema = Schema(
            title=info.get("title", "API Documentation"),
            version=info.get("version", "1.0.0"),
            description=info.get("description", ""),
            base_url=data.get("servers", [{}])[0].get("url", "")
        )

        # Extract endpoints from paths
        paths = data.get("paths", {})
        for path_key, path_item in paths.items():
            if not isinstance(path_item, dict):
                logger.warning(f"Skipping malformed path item: {path_key}")
                continue

            # Extract each HTTP method
            for method_key, operation in path_item.items():
                method_upper = method_key.upper()
                
                # Skip non-operation keys (e.g., 'parameters', 'servers')
                if method_upper not in {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}:
                    continue

                if not isinstance(operation, dict):
                    logger.warning(f"Skipping malformed operation: {method_upper} {path_key}")
                    continue

                try:
                    endpoint = OpenAPIParser._parse_endpoint(method_upper, path_key, operation)
                    schema.endpoints.append(endpoint)
                except Exception as e:
                    logger.warning(f"Failed to parse endpoint {method_upper} {path_key}: {e}")
                    continue

        logger.info(f"Successfully parsed {len(schema.endpoints)} endpoints")
        return schema

    @staticmethod
    def _parse_endpoint(method: str, path: str, operation: Dict[str, Any]) -> Endpoint:
        """
        Parse a single endpoint operation.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path
            operation: Operation object from OpenAPI
        
        Returns:
            Endpoint object
        """
        endpoint = Endpoint(
            method=method,
            path=path,
            summary=operation.get("summary", ""),
            description=operation.get("description", ""),
            tags=operation.get("tags", [])
        )

        # Parse parameters
        parameters = operation.get("parameters", [])
        for param in parameters:
            if not isinstance(param, dict):
                continue
            
            # Check for $ref (schema references) - flag for now
            if "$ref" in param:
                logger.warning(f"Schema reference ($ref) detected in parameter: {param.get('name', 'unknown')}")
            
            try:
                param_obj = Parameter(
                    name=param.get("name", "unknown"),
                    param_type=param.get("in", "query"),
                    required=param.get("required", False),
                    description=param.get("description", ""),
                    schema_type=param.get("schema", {}).get("type", "string")
                )
                endpoint.parameters.append(param_obj)
            except Exception as e:
                logger.warning(f"Failed to parse parameter: {e}")

        # Parse responses
        responses = operation.get("responses", {})
        for status_code, response_obj in responses.items():
            if not isinstance(response_obj, dict):
                continue
            
            if "$ref" in response_obj:
                logger.warning(f"Schema reference ($ref) detected in response {status_code}")
            
            try:
                content = response_obj.get("content", {})
                content_type = list(content.keys())[0] if content else "application/json"
                
                response = Response(
                    status_code=str(status_code),
                    description=response_obj.get("description", ""),
                    content_type=content_type
                )
                endpoint.responses.append(response)
            except Exception as e:
                logger.warning(f"Failed to parse response {status_code}: {e}")

        return endpoint


def parse_openapi(file_path: str) -> Schema:
    """
    Public API: Parse OpenAPI schema from file.
    
    Args:
        file_path: Path to openapi.json
    
    Returns:
        Parsed Schema object
    """
    return OpenAPIParser.parse(file_path)
