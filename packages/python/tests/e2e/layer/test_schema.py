"""L2: Schema management — object type and relation type CRUD.

Read-only tests use existing data. Write tests are marked destructive.
"""
from __future__ import annotations

import pytest

from kweaver import KWeaverClient

pytestmark = pytest.mark.e2e


def test_object_type_list(kweaver_client: KWeaverClient, kn_with_data):
    """SDK: list object types."""
    kn = kn_with_data["kn"]
    ots = kweaver_client.object_types.list(kn.id)
    assert isinstance(ots, list)
    assert len(ots) > 0


def test_object_type_get(kweaver_client: KWeaverClient, kn_with_data):
    """SDK: get object type by ID."""
    kn = kn_with_data["kn"]
    ot = kn_with_data["ot"]
    result = kweaver_client.object_types.get(kn.id, ot.id)
    assert result.id == ot.id
    assert result.name == ot.name


def test_relation_type_list(kweaver_client: KWeaverClient, kn_with_data):
    """SDK: list relation types."""
    kn = kn_with_data["kn"]
    rts = kweaver_client.relation_types.list(kn.id)
    assert isinstance(rts, list)


def test_relation_type_get(kweaver_client: KWeaverClient, e2e_test_data):
    """SDK: get relation type by ID."""
    kn = e2e_test_data["kn"]
    rt = e2e_test_data.get("rt")
    if not rt:
        pytest.skip("No relation type available (need 2+ tables for RT)")
    result = kweaver_client.relation_types.get(kn.id, rt.id)
    assert result.id == rt.id
    assert result.name == rt.name
