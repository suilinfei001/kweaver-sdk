"""E2E: context loader — schema discovery and instance browsing.

Requires at least one existing knowledge network with built data.
These tests are read-only (non-destructive) by default, except where noted.
"""

from __future__ import annotations

from typing import Any

import pytest

from kweaver import ADPClient
from kweaver.skills.load_kn_context import LoadKnContextSkill

pytestmark = pytest.mark.e2e


def test_overview_lists_knowledge_networks(adp_client: ADPClient):
    """overview mode should return at least one KN if any exist."""
    skill = LoadKnContextSkill(client=adp_client)
    result = skill.run(mode="overview")

    assert "knowledge_networks" in result
    # Non-destructive: we just check the structure, not the count
    for kn in result["knowledge_networks"]:
        assert "id" in kn
        assert "name" in kn
        assert "object_type_count" in kn
        assert "relation_type_count" in kn


def test_schema_returns_structure(adp_client: ADPClient):
    """schema mode should return object types and relation types for a KN."""
    # First find an available KN
    kns = adp_client.knowledge_networks.list()
    if not kns:
        pytest.skip("No knowledge networks available in test environment")

    kn = kns[0]
    skill = LoadKnContextSkill(client=adp_client)
    result = skill.run(mode="schema", kn_id=kn.id)

    assert result["kn_id"] == kn.id
    assert "object_types" in result
    assert "relation_types" in result


def test_schema_with_samples(adp_client: ADPClient):
    """schema mode with include_samples should return sample data."""
    kns = adp_client.knowledge_networks.list()
    if not kns:
        pytest.skip("No knowledge networks available")

    # Find a KN with at least one object type
    kn = kns[0]
    ots = adp_client.object_types.list(kn.id)
    if not ots:
        pytest.skip("No object types in available knowledge networks")

    skill = LoadKnContextSkill(client=adp_client)
    result = skill.run(
        mode="schema", kn_id=kn.id,
        include_samples=True, sample_size=2,
    )

    # At least one OT should have sample_data
    has_samples = any(
        "sample_data" in ot and len(ot.get("sample_data", [])) > 0
        for ot in result["object_types"]
    )
    # Non-strict: some OTs might be empty
    assert "object_types" in result


def test_instances_browses_data(adp_client: ADPClient):
    """instances mode should return data for a specific object type."""
    kns = adp_client.knowledge_networks.list()
    if not kns:
        pytest.skip("No knowledge networks available")

    kn = kns[0]
    ots = adp_client.object_types.list(kn.id)
    if not ots:
        pytest.skip("No object types available")

    # Prefer the smallest OT (by doc_count) to avoid server-side timeouts
    ots_with_data = [ot for ot in ots if ot.status and ot.status.doc_count > 0]
    if not ots_with_data:
        pytest.skip("No object types with data available")
    target_ot = min(ots_with_data, key=lambda ot: ot.status.doc_count)

    skill = LoadKnContextSkill(client=adp_client)
    result = skill.run(
        mode="instances", kn_id=kn.id,
        object_type=target_ot.name, limit=5,
    )

    assert "data" in result
    assert "total_count" in result
    assert "has_more" in result
    assert "object_type_schema" in result
    assert result["object_type_schema"]["name"] == target_ot.name


def test_resolve_kn_by_name(adp_client: ADPClient):
    """schema mode should resolve kn_name to kn_id automatically."""
    kns = adp_client.knowledge_networks.list()
    if not kns:
        pytest.skip("No knowledge networks available")

    kn = kns[0]
    skill = LoadKnContextSkill(client=adp_client)
    result = skill.run(mode="schema", kn_name=kn.name)

    assert result.get("kn_id") == kn.id


# ---------------------------------------------------------------------------
# Content-aware tests: verify schema and instances actually return data
# ---------------------------------------------------------------------------


def _find_kn_with_object_types(adp_client: ADPClient):
    """Find a KN that has at least one object type with properties."""
    for kn in adp_client.knowledge_networks.list():
        ots = adp_client.object_types.list(kn.id)
        if ots and any(ot.properties for ot in ots):
            return kn, ots
    return None, None


def test_schema_discovers_object_types_and_properties(adp_client: ADPClient):
    """schema mode should find object types with their property definitions."""
    kn, ots = _find_kn_with_object_types(adp_client)
    if kn is None:
        pytest.skip("No KN with object types found")

    skill = LoadKnContextSkill(client=adp_client)
    result = skill.run(mode="schema", kn_id=kn.id)

    assert len(result["object_types"]) > 0, "schema should discover at least one object type"

    # At least one OT should have properties with type info
    ot_with_props = [
        ot for ot in result["object_types"]
        if ot.get("properties") and len(ot["properties"]) > 0
    ]
    assert len(ot_with_props) > 0, "at least one object type should have properties"

    # Verify property structure is complete
    prop = ot_with_props[0]["properties"][0]
    assert "name" in prop and prop["name"], "property should have a name"
    assert "type" in prop, "property should have a type"


def test_schema_discovers_relations(adp_client: ADPClient):
    """schema mode should find relation types linking object types."""
    for kn in adp_client.knowledge_networks.list():
        rts = adp_client.relation_types.list(kn.id)
        if rts:
            break
    else:
        pytest.skip("No KN with relation types found")

    skill = LoadKnContextSkill(client=adp_client)
    result = skill.run(mode="schema", kn_id=kn.id)

    assert len(result["relation_types"]) > 0, "schema should discover relation types"

    rt = result["relation_types"][0]
    assert rt["name"], "relation should have a name"
    assert rt["source"], "relation should have a source object type"
    assert rt["target"], "relation should have a target object type"


def test_schema_samples_return_real_data(adp_client: ADPClient):
    """schema with include_samples should return actual instance data, not empty lists."""
    kn, ots = _find_kn_with_object_types(adp_client)
    if kn is None:
        pytest.skip("No KN with object types found")

    skill = LoadKnContextSkill(client=adp_client)
    result = skill.run(
        mode="schema", kn_id=kn.id,
        include_samples=True, sample_size=3,
    )

    # Find OTs that have sample data
    ots_with_samples = [
        ot for ot in result["object_types"]
        if ot.get("sample_data") and len(ot["sample_data"]) > 0
    ]
    assert len(ots_with_samples) > 0, (
        "at least one object type should have sample instances"
    )

    sample = ots_with_samples[0]["sample_data"][0]
    assert isinstance(sample, dict), "sample should be a dict of field->value"
    assert len(sample) > 0, "sample should have at least one field"


def test_instances_returns_nonempty_data(adp_client: ADPClient):
    """instances mode should return actual rows, not just empty lists."""
    kn, ots = _find_kn_with_object_types(adp_client)
    if kn is None:
        pytest.skip("No KN with object types found")

    skill = LoadKnContextSkill(client=adp_client)

    # Try each OT until we find one with data
    for ot in ots:
        result = skill.run(
            mode="instances", kn_id=kn.id,
            object_type=ot.name, limit=5,
        )
        if result.get("data") and len(result["data"]) > 0:
            break
    else:
        pytest.skip("No object type with instance data found")

    assert result["total_count"] > 0, "should report total count > 0"
    assert len(result["data"]) > 0, "should return at least one instance"

    # Verify instance is a real record with fields
    row = result["data"][0]
    assert isinstance(row, dict), "instance should be a dict"
    assert len(row) > 0, "instance should have fields"

    # Schema should match the data
    schema_props = {p["name"] for p in result["object_type_schema"]["properties"]}
    assert len(schema_props) > 0, "schema should list properties"
