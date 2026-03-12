"""Tests for load_kn_context skill."""

from unittest.mock import MagicMock

from kweaver.skills.load_kn_context import LoadKnContextSkill
from kweaver.types import (
    DataProperty,
    InstanceResult,
    KNStatistics,
    KnowledgeNetwork,
    ObjectType,
    RelationType,
)


def test_overview_mode():
    mock_client = MagicMock()
    mock_client.knowledge_networks.list.return_value = [
        KnowledgeNetwork(
            id="kn_01", name="erp_prod",
            statistics=KNStatistics(object_types_total=3, relation_types_total=1),
        ),
        KnowledgeNetwork(
            id="kn_02", name="crm",
            statistics=KNStatistics(object_types_total=5, relation_types_total=4),
        ),
    ]

    skill = LoadKnContextSkill(client=mock_client)
    result = skill.run(mode="overview")

    assert len(result["knowledge_networks"]) == 2
    assert result["knowledge_networks"][0]["object_type_count"] == 3


def test_schema_mode():
    mock_client = MagicMock()
    mock_client.knowledge_networks.get.return_value = KnowledgeNetwork(
        id="kn_01", name="erp_prod",
    )
    mock_client.object_types.list.return_value = [
        ObjectType(
            id="ot_01", name="产品", kn_id="kn_01", dataview_id="dv_01",
            primary_keys=["id"], display_key="name",
            properties=[
                DataProperty(name="id", type="integer", indexed=True),
                DataProperty(name="name", type="varchar", fulltext=True),
            ],
        ),
    ]
    mock_client.relation_types.list.return_value = [
        RelationType(
            id="rt_01", name="产品_库存", kn_id="kn_01",
            source_ot_id="ot_01", target_ot_id="ot_02", mapping_type="direct",
        ),
    ]

    skill = LoadKnContextSkill(client=mock_client)
    result = skill.run(mode="schema", kn_id="kn_01")

    assert len(result["object_types"]) == 1
    assert result["object_types"][0]["properties"][0]["indexed"] is True
    assert len(result["relation_types"]) == 1


def test_schema_with_samples():
    mock_client = MagicMock()
    mock_client.knowledge_networks.get.return_value = KnowledgeNetwork(
        id="kn_01", name="erp_prod",
    )
    mock_client.object_types.list.return_value = [
        ObjectType(
            id="ot_01", name="产品", kn_id="kn_01", dataview_id="dv_01",
            primary_keys=["id"], display_key="name", properties=[],
        ),
    ]
    mock_client.relation_types.list.return_value = []
    mock_client.query.instances.return_value = InstanceResult(
        data=[{"id": 1, "name": "轴承A"}, {"id": 2, "name": "轴承B"}],
        total_count=100,
    )

    skill = LoadKnContextSkill(client=mock_client)
    result = skill.run(mode="schema", kn_id="kn_01", include_samples=True, sample_size=2)

    mock_client.query.instances.assert_called_once()
    assert len(result["object_types"][0]["sample_data"]) == 2


def test_instances_mode():
    mock_client = MagicMock()
    mock_client.object_types.list.return_value = [
        ObjectType(
            id="ot_01", name="库存", kn_id="kn_01", dataview_id="dv_01",
            primary_keys=["seq"], display_key="seq",
            properties=[
                DataProperty(name="seq", type="integer"),
                DataProperty(name="quantity", type="integer"),
            ],
        ),
    ]
    mock_client.query.instances.return_value = InstanceResult(
        data=[{"seq": 1, "quantity": 1200}],
        total_count=1523,
        search_after=[1],
    )

    skill = LoadKnContextSkill(client=mock_client)
    result = skill.run(mode="instances", kn_id="kn_01", object_type="库存", limit=10)

    assert result["total_count"] == 1523
    assert result["has_more"] is True
    assert result["object_type_schema"]["name"] == "库存"


def test_resolve_by_name():
    mock_client = MagicMock()
    mock_client.knowledge_networks.list.return_value = [
        KnowledgeNetwork(id="kn_01", name="erp_prod"),
    ]
    mock_client.knowledge_networks.get.return_value = KnowledgeNetwork(
        id="kn_01", name="erp_prod",
    )
    mock_client.object_types.list.return_value = []
    mock_client.relation_types.list.return_value = []

    skill = LoadKnContextSkill(client=mock_client)
    result = skill.run(mode="schema", kn_name="erp_prod")

    mock_client.knowledge_networks.list.assert_called_once_with(name="erp_prod")
    assert result["kn_id"] == "kn_01"


def test_instances_object_type_not_found():
    mock_client = MagicMock()
    mock_client.object_types.list.return_value = []

    skill = LoadKnContextSkill(client=mock_client)
    result = skill.run(mode="instances", kn_id="kn_01", object_type="不存在")

    assert result["error"] is True
