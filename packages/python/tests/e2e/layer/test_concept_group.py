"""E2E: Concept group read operations."""
import pytest
from kweaver import KWeaverClient

pytestmark = pytest.mark.e2e


def test_concept_group_list(kweaver_client: KWeaverClient, e2e_test_data):
    """SDK: list concept groups."""
    kn = e2e_test_data["kn"]
    cgs = kweaver_client.concept_groups.list(kn.id)
    assert isinstance(cgs, list)


def test_concept_group_get(kweaver_client: KWeaverClient, e2e_test_data):
    """SDK: get concept group by ID."""
    kn = e2e_test_data["kn"]
    cg = e2e_test_data.get("cg")
    if not cg:
        pytest.skip("No concept group available (bootstrap may have failed)")
    result = kweaver_client.concept_groups.get(kn.id, cg.id)
    assert result.id == cg.id
    assert result.name == cg.name
