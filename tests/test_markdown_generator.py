from docsync.markdown_generator import BEGIN_MARKER, END_MARKER, generate_markdown
from docsync.models import Endpoint, Parameter, ResponseSummary


def test_generate_markdown_wraps_body_in_markers():
    endpoints = [Endpoint(path="/ping", method="GET")]
    output = generate_markdown(endpoints)

    assert output.startswith(BEGIN_MARKER + "\n")
    assert output.rstrip().endswith(END_MARKER)


def test_generate_markdown_includes_endpoint_details():
    endpoint = Endpoint(
        path="/users",
        method="GET",
        summary="List users",
        description="Returns all users",
        parameters=[Parameter(name="limit", location="query", required=False, schema_type="integer")],
        responses=[ResponseSummary(status_code="200", description="OK")],
    )
    output = generate_markdown([endpoint])

    assert "## GET /users" in output
    assert "List users" in output
    assert "Returns all users" in output
    assert "`limit`" in output
    assert "`200`" in output


def test_generate_markdown_empty_endpoints_reports_no_endpoints():
    output = generate_markdown([])
    assert "No endpoints found." in output
    assert output.startswith(BEGIN_MARKER)
    assert output.rstrip().endswith(END_MARKER)


def test_generate_markdown_is_deterministic():
    endpoints = [Endpoint(path="/a", method="GET"), Endpoint(path="/b", method="POST")]
    assert generate_markdown(endpoints) == generate_markdown(endpoints)
