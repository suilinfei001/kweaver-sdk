"""Tests for query_kn skill."""

from unittest.mock import MagicMock

from kweaver.skills.query_kn import QueryKnSkill
from kweaver.types import ConceptResult, InstanceResult, ObjectType, SemanticSearchResult


def test_search_mode():
    mock_client = MagicMock()
    mock_client.query.semantic_search.return_value = SemanticSearchResult(
        concepts=[
            ConceptResult(concept_type="object_type", concept_id="ot_01", concept_name="产品"),
        ],
        hits_total=1,
    )

    skill = QueryKnSkill(client=mock_client)
    result = skill.run(kn_id="kn_01", mode="search", query="产品库存")

    assert len(result["data"]) == 1
    assert "1" in result["summary"]


def test_instances_mode():
    mock_client = MagicMock()
    mock_client.object_types.list.return_value = [
        ObjectType(id="ot_01", name="产品", kn_id="kn_01", dataview_id="dv_01",
                   primary_keys=["id"], display_key="name", properties=[]),
    ]
    mock_client.query.instances.return_value = InstanceResult(
        data=[{"id": 1, "name": "轴承A"}], total_count=50,
    )

    skill = QueryKnSkill(client=mock_client)
    result = skill.run(kn_id="kn_01", mode="instances", object_type="产品", limit=10)

    assert len(result["data"]) == 1
    assert "50" in result["summary"]


def test_instances_mode_not_found():
    mock_client = MagicMock()
    mock_client.object_types.list.return_value = []

    skill = QueryKnSkill(client=mock_client)
    result = skill.run(kn_id="kn_01", mode="instances", object_type="不存在")

    assert result["error"] is True


def test_unknown_mode():
    mock_client = MagicMock()
    skill = QueryKnSkill(client=mock_client)
    result = skill.run(kn_id="kn_01", mode="bad")
    assert result["error"] is True
