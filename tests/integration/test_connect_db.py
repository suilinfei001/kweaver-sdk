"""Tests for connect_db skill."""

from unittest.mock import MagicMock

from kweaver.skills.connect_db import ConnectDbSkill
from kweaver.types import Column, DataSource, Table


def test_connect_db_full_flow():
    mock_client = MagicMock()
    mock_client.datasources.test.return_value = True
    mock_client.datasources.create.return_value = DataSource(
        id="ds_01", name="erp", type="mysql"
    )
    mock_client.datasources.list_tables.return_value = [
        Table(name="products", columns=[
            Column(name="id", type="integer"),
            Column(name="name", type="varchar"),
        ]),
    ]

    skill = ConnectDbSkill(client=mock_client)
    result = skill.run(
        db_type="mysql", host="10.0.1.100", port=3306,
        database="erp", account="root", password="secret",
    )

    assert result["datasource_id"] == "ds_01"
    assert len(result["tables"]) == 1
    assert result["tables"][0]["name"] == "products"
    mock_client.datasources.test.assert_called_once()
    mock_client.datasources.create.assert_called_once()


def test_connect_db_test_failure():
    from kweaver._errors import ADPError

    mock_client = MagicMock()
    mock_client.datasources.test.side_effect = ADPError(
        "Connection refused", status_code=400
    )

    skill = ConnectDbSkill(client=mock_client)
    result = skill.run(
        db_type="mysql", host="bad-host", port=3306,
        database="erp", account="root", password="secret",
    )
    assert result["error"] is True
    mock_client.datasources.create.assert_not_called()
