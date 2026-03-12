"""Tests for dataviews resource."""

import httpx
import pytest

from tests.conftest import RequestCapture, make_client


def test_create_table_mode(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{
            "id": "dv_01", "name": "products", "query_type": "SQL", "fields": [],
        }])

    client = make_client(handler, capture)
    dv = client.dataviews.create(name="products", datasource_id="ds_01", table="products")

    body = capture.last_body()
    assert isinstance(body, list)
    assert body[0]["type"] == "atomic"
    assert body[0]["data_scope"][0]["type"] == "source"
    assert body[0]["data_scope"][0]["config"]["table"] == "products"
    assert dv.id == "dv_01"


def test_create_sql_mode(capture: RequestCapture):
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{
            "id": "dv_02", "name": "custom", "query_type": "SQL", "fields": [],
        }])

    client = make_client(handler, capture)
    client.dataviews.create(
        name="custom", datasource_id="ds_01",
        sql="SELECT id FROM products WHERE status = 'active'",
    )

    body = capture.last_body()
    assert body[0]["type"] == "custom"
    assert body[0]["data_scope"][0]["type"] == "sql"
    assert "SELECT" in body[0]["data_scope"][0]["config"]["sql"]


def test_create_requires_table_or_sql():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    client = make_client(handler)
    with pytest.raises(ValueError, match="Either"):
        client.dataviews.create(name="bad", datasource_id="ds_01")
