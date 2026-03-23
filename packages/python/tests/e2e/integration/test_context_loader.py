"""Scenario 2: MCP / Context Loader — verify schema discovery and instance query.

Validates: Context Loader kn_search + query_object_instance + REST vs MCP consistency.
"""
from __future__ import annotations

import pytest

from kweaver import KWeaverClient
from kweaver.resources.context_loader import ContextLoaderResource

pytestmark = [pytest.mark.e2e, pytest.mark.destructive]


@pytest.fixture(scope="module")
def cl(kweaver_client: KWeaverClient, lifecycle_env):
    """Context Loader bound to the lifecycle KN."""
    if lifecycle_env["build_status"] != "completed":
        pytest.skip("Build did not complete")
    kn = lifecycle_env["kn"]
    token = kweaver_client._http._auth.auth_headers().get(
        "Authorization", ""
    ).removeprefix("Bearer ").strip()
    base_url = str(kweaver_client._http._client.base_url).rstrip("/")
    return ContextLoaderResource(base_url, token, kn_id=kn.id)


def test_mcp_kn_search_finds_schema(cl, lifecycle_env):
    """MCP kn_search should discover the object type we just built."""
    ot = lifecycle_env["ot"]
    try:
        result = cl.kn_search(ot.name)
    except RuntimeError as e:
        pytest.skip(f"MCP kn_search not available: {e}")
    raw = result.get("raw", "")
    assert raw, f"MCP kn_search returned empty for '{ot.name}'"


def test_mcp_query_instance_returns_data(kweaver_client: KWeaverClient, cl, lifecycle_env):
    """MCP query_object_instance should return data matching REST."""
    kn = lifecycle_env["kn"]
    ot = lifecycle_env["ot"]

    # Get a real instance via REST first
    rest_result = kweaver_client.query.instances(kn.id, ot.id, limit=1)
    if not rest_result.data:
        pytest.skip("No instances available")
    sample = rest_result.data[0]
    identity = sample.get("_instance_identity")
    if not identity:
        pytest.skip("Instance has no _instance_identity")
    pk_field = list(identity.keys())[0]
    pk_value = identity[pk_field]

    # Query same instance via MCP
    mcp_result = cl.query_object_instance(
        ot.id,
        condition={
            "operation": "and",
            "sub_conditions": [
                {"field": pk_field, "operation": "==", "value_from": "const", "value": pk_value},
            ],
        },
        limit=1,
    )
    mcp_raw = mcp_result.get("raw", "")
    assert str(pk_value) in mcp_raw, (
        f"MCP did not return instance {pk_field}={pk_value}"
    )
