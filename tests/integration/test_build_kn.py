"""Tests for build_kn skill."""

from unittest.mock import MagicMock

from kweaver._errors import AuthorizationError
from kweaver.skills.build_kn import BuildKnSkill
from kweaver.types import (
    BuildStatus,
    Column,
    DataView,
    KnowledgeNetwork,
    ObjectType,
    RelationType,
    Table,
)


def _make_mock_client():
    mock = MagicMock()
    mock.datasources.list_tables.return_value = [
        Table(name="products", columns=[
            Column(name="id", type="integer"),
            Column(name="product_name", type="varchar"),
        ]),
        Table(name="inventory", columns=[
            Column(name="seq", type="integer"),
            Column(name="material_code", type="varchar"),
        ]),
    ]
    mock.dataviews.create.side_effect = [
        DataView(id="dv_01", name="products", query_type="SQL", fields=[]),
        DataView(id="dv_02", name="inventory", query_type="SQL", fields=[]),
    ]
    mock.knowledge_networks.create.return_value = KnowledgeNetwork(
        id="kn_01", name="test",
    )
    mock.object_types.create.side_effect = [
        ObjectType(
            id="ot_01", name="products", kn_id="kn_01", dataview_id="dv_01",
            primary_keys=["id"], display_key="product_name", properties=[],
        ),
        ObjectType(
            id="ot_02", name="inventory", kn_id="kn_01", dataview_id="dv_02",
            primary_keys=["seq"], display_key="seq", properties=[],
        ),
    ]
    mock.relation_types.create.return_value = RelationType(
        id="rt_01", name="prod_inv", kn_id="kn_01",
        source_ot_id="ot_01", target_ot_id="ot_02",
    )
    build_job = MagicMock()
    build_job.wait.return_value = BuildStatus(state="completed")
    mock.knowledge_networks.build.return_value = build_job
    return mock


def test_build_kn_full_flow():
    mock_client = _make_mock_client()
    skill = BuildKnSkill(client=mock_client)
    result = skill.run(
        datasource_id="ds_01",
        tables=["products", "inventory"],
        relations=[{
            "name": "prod_inv",
            "from_table": "products",
            "to_table": "inventory",
            "from_field": "id",
            "to_field": "product_id",
        }],
    )

    assert mock_client.dataviews.create.call_count == 2
    assert mock_client.knowledge_networks.create.call_count == 1
    assert mock_client.object_types.create.call_count == 2
    assert mock_client.relation_types.create.call_count == 1
    assert mock_client.knowledge_networks.build.call_count == 1

    # Verify relation uses OT IDs, not table names
    rt_call = mock_client.relation_types.create.call_args
    assert rt_call.kwargs["source_ot_id"] == "ot_01"
    assert rt_call.kwargs["target_ot_id"] == "ot_02"

    assert result["status"] == "completed"
    assert len(result["object_types"]) == 2


def test_build_kn_empty_tables_uses_all():
    mock_client = _make_mock_client()
    skill = BuildKnSkill(client=mock_client)
    result = skill.run(datasource_id="ds_01")

    # Should use all 2 tables
    assert mock_client.dataviews.create.call_count == 2


def test_build_kn_handles_auth_error():
    mock_client = MagicMock()
    mock_client.datasources.list_tables.return_value = [
        Table(name="t1", columns=[Column(name="id", type="integer")]),
    ]
    mock_client.dataviews.create.return_value = DataView(
        id="dv_01", name="t1", query_type="SQL", fields=[],
    )
    mock_client.knowledge_networks.create.side_effect = AuthorizationError(
        "no permission", status_code=403, error_code="FORBIDDEN"
    )

    skill = BuildKnSkill(client=mock_client)
    result = skill.run(datasource_id="ds_01")

    assert result["error"] is True
    assert "无权" in result["message"]
