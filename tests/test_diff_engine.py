"""Test suite for docsync.diff_engine

Test coverage for BLOCKER #2 (Endpoint Comparison Algorithm):
- Endpoint comparison (method, path, summary, description, parameters, responses)
- Diff detection (NEW, REMOVED, MODIFIED endpoints)
- Schema caching for efficient diffs
"""

import pytest
import tempfile
from pathlib import Path
from docsync.diff_engine import EndpointComparator, DiffEngine
from docsync.models import Endpoint, Parameter, Response, Schema, ChangeType


class TestEndpointComparator:
    """Tests for endpoint comparison (BLOCKER #2)."""
    
    def test_endpoints_identical(self):
        """Test that identical endpoints are equal."""
        ep1 = Endpoint("GET", "/items", "List", "Get all items")
        ep2 = Endpoint("GET", "/items", "List", "Get all items")
        assert EndpointComparator.endpoints_equal(ep1, ep2) is True
    
    def test_endpoints_different_method(self):
        """Test that different HTTP methods are detected."""
        ep1 = Endpoint("GET", "/items")
        ep2 = Endpoint("POST", "/items")
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_different_path(self):
        """Test that different paths are detected."""
        ep1 = Endpoint("GET", "/items")
        ep2 = Endpoint("GET", "/products")
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_different_summary(self):
        """Test that different summaries are detected."""
        ep1 = Endpoint("GET", "/items", "List items")
        ep2 = Endpoint("GET", "/items", "Get items")
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_different_description(self):
        """Test that different descriptions are detected."""
        ep1 = Endpoint("GET", "/items", description="Return all items")
        ep2 = Endpoint("GET", "/items", description="Get all items modified")
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_different_parameter_count(self):
        """Test that different parameter counts are detected."""
        param1 = Parameter("id", "path", True)
        
        ep1 = Endpoint("GET", "/items", parameters=[param1])
        ep2 = Endpoint("GET", "/items", parameters=[])
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_different_parameter_name(self):
        """Test that different parameter names are detected."""
        param1 = Parameter("id", "path", True)
        param2 = Parameter("item_id", "path", True)
        
        ep1 = Endpoint("GET", "/items", parameters=[param1])
        ep2 = Endpoint("GET", "/items", parameters=[param2])
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_different_parameter_type(self):
        """Test that different parameter types are detected."""
        param1 = Parameter("id", "path", True)
        param2 = Parameter("id", "query", True)
        
        ep1 = Endpoint("GET", "/items", parameters=[param1])
        ep2 = Endpoint("GET", "/items", parameters=[param2])
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_different_parameter_required(self):
        """Test that different parameter 'required' is detected."""
        param1 = Parameter("id", "path", True)
        param2 = Parameter("id", "path", False)
        
        ep1 = Endpoint("GET", "/items", parameters=[param1])
        ep2 = Endpoint("GET", "/items", parameters=[param2])
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_different_parameter_schema_type(self):
        """Test that different schema types are detected."""
        param1 = Parameter("id", "path", True, schema_type="integer")
        param2 = Parameter("id", "path", True, schema_type="string")
        
        ep1 = Endpoint("GET", "/items", parameters=[param1])
        ep2 = Endpoint("GET", "/items", parameters=[param2])
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_parameter_order_matters(self):
        """Test that parameter order affects comparison."""
        param1 = Parameter("id", "path", True)
        param2 = Parameter("filter", "query", False)
        
        ep1 = Endpoint("GET", "/items", parameters=[param1, param2])
        ep2 = Endpoint("GET", "/items", parameters=[param2, param1])
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_different_response_count(self):
        """Test that different response counts are detected."""
        resp1 = Response("200", "OK")
        
        ep1 = Endpoint("GET", "/items", responses=[resp1])
        ep2 = Endpoint("GET", "/items", responses=[])
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_different_response_code(self):
        """Test that different response status codes are detected."""
        resp1 = Response("200", "OK")
        resp2 = Response("201", "Created")
        
        ep1 = Endpoint("GET", "/items", responses=[resp1])
        ep2 = Endpoint("GET", "/items", responses=[resp2])
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_different_response_description(self):
        """Test that different response descriptions are detected."""
        resp1 = Response("200", "Success")
        resp2 = Response("200", "OK")
        
        ep1 = Endpoint("GET", "/items", responses=[resp1])
        ep2 = Endpoint("GET", "/items", responses=[resp2])
        assert EndpointComparator.endpoints_equal(ep1, ep2) is False
    
    def test_endpoints_same_responses_different_order(self):
        """Test that response order doesn't matter (they're sorted)."""
        resp1 = Response("200", "OK")
        resp2 = Response("404", "Not Found")
        
        ep1 = Endpoint("GET", "/items", responses=[resp1, resp2])
        ep2 = Endpoint("GET", "/items", responses=[resp2, resp1])
        # Should be equal because responses are sorted by status code
        assert EndpointComparator.endpoints_equal(ep1, ep2) is True


class TestDiffEngine:
    """Tests for diff engine (BLOCKER #2)."""
    
    def test_first_sync_all_new(self):
        """Test that first sync marks all endpoints as NEW."""
        ep1 = Endpoint("GET", "/items")
        ep2 = Endpoint("POST", "/items")
        new_schema = Schema(endpoints=[ep1, ep2])
        
        changes = DiffEngine.compute_diff(None, new_schema)
        
        assert len(changes) == 2
        assert all(c.change_type == ChangeType.NEW for c in changes)
    
    def test_no_changes(self):
        """Test that identical schemas produce no changes."""
        ep1 = Endpoint("GET", "/items")
        ep2 = Endpoint("POST", "/items")
        old_schema = Schema(endpoints=[ep1, ep2])
        new_schema = Schema(endpoints=[ep1, ep2])
        
        changes = DiffEngine.compute_diff(old_schema, new_schema)
        assert len(changes) == 0
    
    def test_removed_endpoint(self):
        """Test detection of removed endpoint."""
        ep1 = Endpoint("GET", "/items")
        ep2 = Endpoint("POST", "/items")
        
        old_schema = Schema(endpoints=[ep1, ep2])
        new_schema = Schema(endpoints=[ep1])
        
        changes = DiffEngine.compute_diff(old_schema, new_schema)
        
        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.REMOVED
        assert changes[0].endpoint.method == "POST"
    
    def test_removed_multiple_endpoints(self):
        """Test detection of multiple removed endpoints."""
        ep1 = Endpoint("GET", "/items")
        ep2 = Endpoint("POST", "/items")
        ep3 = Endpoint("DELETE", "/items/{id}")
        
        old_schema = Schema(endpoints=[ep1, ep2, ep3])
        new_schema = Schema(endpoints=[ep1])
        
        changes = DiffEngine.compute_diff(old_schema, new_schema)
        
        removed = [c for c in changes if c.change_type == ChangeType.REMOVED]
        assert len(removed) == 2
    
    def test_new_endpoint(self):
        """Test detection of new endpoint."""
        ep1 = Endpoint("GET", "/items")
        ep2 = Endpoint("DELETE", "/items/{id}")
        
        old_schema = Schema(endpoints=[ep1])
        new_schema = Schema(endpoints=[ep1, ep2])
        
        changes = DiffEngine.compute_diff(old_schema, new_schema)
        
        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.NEW
        assert changes[0].endpoint.method == "DELETE"
    
    def test_new_multiple_endpoints(self):
        """Test detection of multiple new endpoints."""
        ep1 = Endpoint("GET", "/items")
        ep2 = Endpoint("POST", "/items")
        ep3 = Endpoint("GET", "/items/{id}")
        
        old_schema = Schema(endpoints=[ep1])
        new_schema = Schema(endpoints=[ep1, ep2, ep3])
        
        changes = DiffEngine.compute_diff(old_schema, new_schema)
        
        new_changes = [c for c in changes if c.change_type == ChangeType.NEW]
        assert len(new_changes) == 2
    
    def test_modified_endpoint_summary(self):
        """Test detection of endpoint summary modification."""
        ep_old = Endpoint("GET", "/items", "List items")
        ep_new = Endpoint("GET", "/items", "Get all items (modified)")
        
        old_schema = Schema(endpoints=[ep_old])
        new_schema = Schema(endpoints=[ep_new])
        
        changes = DiffEngine.compute_diff(old_schema, new_schema)
        
        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.MODIFIED
    
    def test_modified_endpoint_description(self):
        """Test detection of endpoint description modification."""
        ep_old = Endpoint("GET", "/items", description="Old description")
        ep_new = Endpoint("GET", "/items", description="New description")
        
        old_schema = Schema(endpoints=[ep_old])
        new_schema = Schema(endpoints=[ep_new])
        
        changes = DiffEngine.compute_diff(old_schema, new_schema)
        
        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.MODIFIED
    
    def test_modified_endpoint_parameters_added(self):
        """Test detection when parameter is added."""
        param = Parameter("filter", "query", False)
        ep_old = Endpoint("GET", "/items", parameters=[])
        ep_new = Endpoint("GET", "/items", parameters=[param])
        
        old_schema = Schema(endpoints=[ep_old])
        new_schema = Schema(endpoints=[ep_new])
        
        changes = DiffEngine.compute_diff(old_schema, new_schema)
        
        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.MODIFIED
    
    def test_modified_endpoint_responses_added(self):
        """Test detection when response is added."""
        resp = Response("500", "Server Error")
        ep_old = Endpoint("GET", "/items", responses=[Response("200", "OK")])
        ep_new = Endpoint("GET", "/items", responses=[Response("200", "OK"), resp])
        
        old_schema = Schema(endpoints=[ep_old])
        new_schema = Schema(endpoints=[ep_new])
        
        changes = DiffEngine.compute_diff(old_schema, new_schema)
        
        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.MODIFIED
    
    def test_mixed_changes(self):
        """Test detection of mixed NEW, REMOVED, and MODIFIED."""
        # Old: GET /items, POST /items, DELETE /items/{id}
        # New: GET /items (modified), POST /items (same), PUT /items (new)
        
        ep_get_old = Endpoint("GET", "/items", "List items")
        ep_get_new = Endpoint("GET", "/items", "List all items")
        ep_post = Endpoint("POST", "/items")
        ep_delete = Endpoint("DELETE", "/items/{id}")
        ep_put = Endpoint("PUT", "/items")
        
        old_schema = Schema(endpoints=[ep_get_old, ep_post, ep_delete])
        new_schema = Schema(endpoints=[ep_get_new, ep_post, ep_put])
        
        changes = DiffEngine.compute_diff(old_schema, new_schema)
        
        new_changes = [c for c in changes if c.change_type == ChangeType.NEW]
        removed_changes = [c for c in changes if c.change_type == ChangeType.REMOVED]
        modified_changes = [c for c in changes if c.change_type == ChangeType.MODIFIED]
        
        assert len(new_changes) == 1  # PUT /items
        assert len(removed_changes) == 1  # DELETE /items/{id}
        assert len(modified_changes) == 1  # GET /items
    
    def test_empty_schemas(self):
        """Test diff with both schemas empty."""
        old_schema = Schema(endpoints=[])
        new_schema = Schema(endpoints=[])
        
        changes = DiffEngine.compute_diff(old_schema, new_schema)
        assert len(changes) == 0
    
    def test_old_schema_empty(self):
        """Test diff when old schema is empty (first sync scenario)."""
        ep = Endpoint("GET", "/items")
        new_schema = Schema(endpoints=[ep])
        
        changes = DiffEngine.compute_diff(Schema(endpoints=[]), new_schema)
        
        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.NEW
