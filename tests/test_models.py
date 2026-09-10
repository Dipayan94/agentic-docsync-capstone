"""Test suite for docsync.models

Test coverage:
- Dataclass creation and properties
- String representations
- Enums and types
"""

import pytest
from docsync.models import (
    Parameter, Response, Endpoint, Schema, Change, ChangeType, ValidationError
)


class TestParameter:
    """Tests for Parameter model."""
    
    def test_parameter_creation(self):
        """Test creating a parameter with all fields."""
        param = Parameter(
            name="item_id",
            param_type="path",
            required=True,
            description="Item identifier",
            schema_type="integer"
        )
        assert param.name == "item_id"
        assert param.param_type == "path"
        assert param.required is True
        assert param.description == "Item identifier"
        assert param.schema_type == "integer"
    
    def test_parameter_optional_defaults(self):
        """Test parameter with minimal required fields."""
        # param_type is required (can't use default)
        param = Parameter(name="filter", param_type="query", schema_type="string")
        assert param.name == "filter"
        assert param.required is False
        assert param.description == ""
    
    def test_parameter_str_required(self):
        """Test string representation of required parameter."""
        param = Parameter("id", "query", True, "ID", "integer")
        param_str = str(param)
        assert "[required]" in param_str
        assert "id" in param_str
        assert "integer" in param_str
    
    def test_parameter_str_optional(self):
        """Test string representation of optional parameter."""
        param = Parameter("filter", "query", False, "Filter results", "string")
        param_str = str(param)
        assert "[optional]" in param_str


class TestResponse:
    """Tests for Response model."""
    
    def test_response_creation(self):
        """Test creating a response."""
        resp = Response(
            status_code="200",
            description="Success",
            content_type="application/json"
        )
        assert resp.status_code == "200"
        assert resp.description == "Success"
        assert resp.content_type == "application/json"
    
    def test_response_defaults(self):
        """Test response with minimal fields."""
        resp = Response("404", "Not Found")
        assert resp.status_code == "404"
        assert resp.description == "Not Found"
        assert resp.content_type == "application/json"
    
    def test_response_str(self):
        """Test response string representation."""
        resp = Response("200", "Success")
        assert "200" in str(resp)
        assert "Success" in str(resp)


class TestEndpoint:
    """Tests for Endpoint model."""
    
    def test_endpoint_creation(self):
        """Test creating an endpoint."""
        ep = Endpoint(
            method="GET",
            path="/items/{id}",
            summary="Get item",
            description="Retrieve a single item"
        )
        assert ep.method == "GET"
        assert ep.path == "/items/{id}"
        assert ep.summary == "Get item"
        assert ep.description == "Retrieve a single item"
    
    def test_endpoint_identifier(self):
        """Test endpoint identifier generation."""
        ep = Endpoint("POST", "/items")
        assert ep.identifier() == "post /items"
        
        ep2 = Endpoint("GET", "/items/{id}")
        assert ep2.identifier() == "get /items/{id}"
    
    def test_endpoint_with_parameters(self):
        """Test endpoint with parameters."""
        param = Parameter("id", "path", True)
        ep = Endpoint("GET", "/items/{id}", parameters=[param])
        assert len(ep.parameters) == 1
        assert ep.parameters[0].name == "id"
    
    def test_endpoint_with_multiple_parameters(self):
        """Test endpoint with multiple parameters."""
        params = [
            Parameter("id", "path", True),
            Parameter("filter", "query", False),
            Parameter("limit", "query", False)
        ]
        ep = Endpoint("GET", "/items", parameters=params)
        assert len(ep.parameters) == 3
    
    def test_endpoint_with_responses(self):
        """Test endpoint with responses."""
        resp = Response("200", "OK")
        ep = Endpoint("GET", "/items", responses=[resp])
        assert len(ep.responses) == 1
        assert ep.responses[0].status_code == "200"
    
    def test_endpoint_with_multiple_responses(self):
        """Test endpoint with multiple responses."""
        responses = [
            Response("200", "Success"),
            Response("404", "Not Found"),
            Response("500", "Server Error")
        ]
        ep = Endpoint("GET", "/items", responses=responses)
        assert len(ep.responses) == 3
    
    def test_endpoint_str(self):
        """Test endpoint string representation."""
        ep = Endpoint("GET", "/items", "List items")
        ep_str = str(ep)
        assert "GET" in ep_str
        assert "/items" in ep_str
        assert "List items" in ep_str
    
    def test_endpoint_tags(self):
        """Test endpoint with tags."""
        ep = Endpoint("GET", "/items", tags=["items", "inventory"])
        assert len(ep.tags) == 2
        assert "items" in ep.tags


class TestSchema:
    """Tests for Schema model."""
    
    def test_schema_creation(self):
        """Test creating a schema."""
        schema = Schema(
            title="Pet Store API",
            version="1.0.0",
            description="API for pet store"
        )
        assert schema.title == "Pet Store API"
        assert schema.version == "1.0.0"
        assert schema.description == "API for pet store"
        assert schema.endpoint_count() == 0
    
    def test_schema_defaults(self):
        """Test schema with default values."""
        schema = Schema()
        assert schema.title == "API Documentation"
        assert schema.version == "1.0.0"
        assert schema.description == ""
        assert len(schema.endpoints) == 0
    
    def test_schema_with_endpoints(self):
        """Test schema with endpoints."""
        ep1 = Endpoint("GET", "/items")
        ep2 = Endpoint("POST", "/items")
        schema = Schema(endpoints=[ep1, ep2])
        assert schema.endpoint_count() == 2
    
    def test_schema_endpoints_by_path_single_endpoint(self):
        """Test grouping single endpoint by path."""
        ep = Endpoint("GET", "/items")
        schema = Schema(endpoints=[ep])
        
        grouped = schema.endpoints_by_path()
        assert "/items" in grouped
        assert len(grouped["/items"]) == 1
    
    def test_schema_endpoints_by_path_multiple_methods(self):
        """Test grouping multiple methods on same path."""
        ep1 = Endpoint("GET", "/items")
        ep2 = Endpoint("POST", "/items")
        schema = Schema(endpoints=[ep1, ep2])
        
        grouped = schema.endpoints_by_path()
        assert "/items" in grouped
        assert len(grouped["/items"]) == 2
    
    def test_schema_endpoints_by_path_multiple_paths(self):
        """Test grouping endpoints across multiple paths."""
        ep1 = Endpoint("GET", "/items")
        ep2 = Endpoint("POST", "/items")
        ep3 = Endpoint("GET", "/items/{id}")
        schema = Schema(endpoints=[ep1, ep2, ep3])
        
        grouped = schema.endpoints_by_path()
        assert len(grouped) == 2
        assert "/items" in grouped
        assert "/items/{id}" in grouped
        assert len(grouped["/items"]) == 2
        assert len(grouped["/items/{id}"]) == 1
    
    def test_schema_str(self):
        """Test schema string representation."""
        schema = Schema(title="API", version="2.0", endpoints=[Endpoint("GET", "/")])
        schema_str = str(schema)
        assert "API" in schema_str
        assert "2.0" in schema_str
        assert "1 endpoints" in schema_str


class TestChangeType:
    """Tests for ChangeType enum."""
    
    def test_change_type_new(self):
        """Test NEW change type."""
        assert ChangeType.NEW == "new"
    
    def test_change_type_removed(self):
        """Test REMOVED change type."""
        assert ChangeType.REMOVED == "removed"
    
    def test_change_type_modified(self):
        """Test MODIFIED change type."""
        assert ChangeType.MODIFIED == "modified"


class TestChange:
    """Tests for Change model."""
    
    def test_change_new(self):
        """Test creating a NEW change."""
        ep = Endpoint("GET", "/new-endpoint")
        change = Change(ChangeType.NEW, ep, "New endpoint added")
        assert change.change_type == ChangeType.NEW
        assert change.endpoint == ep
        assert change.details == "New endpoint added"
    
    def test_change_removed(self):
        """Test creating a REMOVED change."""
        ep = Endpoint("DELETE", "/old-endpoint")
        change = Change(ChangeType.REMOVED, ep)
        assert change.change_type == ChangeType.REMOVED
        assert change.endpoint == ep
        assert change.details == ""
    
    def test_change_modified(self):
        """Test creating a MODIFIED change."""
        ep = Endpoint("GET", "/items")
        change = Change(ChangeType.MODIFIED, ep, "Summary changed")
        assert change.change_type == ChangeType.MODIFIED
    
    def test_change_str_new(self):
        """Test string representation of NEW change."""
        ep = Endpoint("GET", "/items")
        change = Change(ChangeType.NEW, ep, "New endpoint")
        change_str = str(change)
        assert "new" in change_str.lower() or "NEW" in change_str
        assert "GET" in change_str
    
    def test_change_str_removed(self):
        """Test string representation of REMOVED change."""
        ep = Endpoint("DELETE", "/items")
        change = Change(ChangeType.REMOVED, ep)
        change_str = str(change)
        assert "removed" in change_str.lower() or "REMOVED" in change_str


class TestValidationError:
    """Tests for ValidationError model."""
    
    def test_validation_error_creation(self):
        """Test creating a validation error."""
        err = ValidationError("Missing field", "MISSING_FIELD")
        assert err.message == "Missing field"
        assert err.code == "MISSING_FIELD"
    
    def test_validation_error_str(self):
        """Test string representation of validation error."""
        err = ValidationError("Invalid type", "INVALID_TYPE")
        err_str = str(err)
        assert "[INVALID_TYPE]" in err_str
        assert "Invalid type" in err_str
    
    def test_validation_error_defaults(self):
        """Test validation error with default code."""
        err = ValidationError("Something wrong")
        assert err.message == "Something wrong"
        # Default code is VALIDATION_ERROR not UNKNOWN
        assert err.code == "VALIDATION_ERROR"
