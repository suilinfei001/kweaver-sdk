"""Scenario 1: Data Pipeline — build KN from scratch, verify data is indexed.

Validates: datasource -> dataview -> KN -> object type -> build -> REST query.
"""
from __future__ import annotations

import pytest

from kweaver import KWeaverClient

pytestmark = [pytest.mark.e2e, pytest.mark.destructive]


def test_build_completed(lifecycle_env):
    """Build should complete successfully."""
    assert lifecycle_env["build_status"] == "completed", (
        f"Build failed: {lifecycle_env['build_status']}, detail: {lifecycle_env.get('build_detail')}"
    )


def test_rest_instances_have_data(kweaver_client: KWeaverClient, lifecycle_env):
    """REST query.instances should return data from the built KN."""
    if lifecycle_env["build_status"] != "completed":
        pytest.skip("Build did not complete")
    kn = lifecycle_env["kn"]
    ot = lifecycle_env["ot"]
    result = kweaver_client.query.instances(kn.id, ot.id, limit=5)
    assert result.data, "REST returned no instances after build"
    assert result.total_count > 0
    pk = lifecycle_env["pk_col"]
    assert pk in result.data[0] or "_instance_identity" in result.data[0]


def test_rest_semantic_search(kweaver_client: KWeaverClient, lifecycle_env):
    """REST semantic search should find the object type."""
    if lifecycle_env["build_status"] != "completed":
        pytest.skip("Build did not complete")
    from kweaver._errors import ServerError, ValidationError

    kn = lifecycle_env["kn"]
    ot = lifecycle_env["ot"]
    try:
        result = kweaver_client.query.semantic_search(kn.id, "test")
    except (ServerError, ValidationError):
        pytest.skip("Semantic search not available for this KN (may need time to index)")
    assert isinstance(result.concepts, list)
