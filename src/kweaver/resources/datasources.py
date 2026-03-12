"""SDK resource: data sources (data-connection service)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kweaver.types import Column, DataSource, Table

if TYPE_CHECKING:
    from kweaver._http import HttpClient

_HTTPS_PROTOCOLS = {"maxcompute", "anyshare7", "opensearch"}


def _connect_protocol(ds_type: str) -> str:
    return "https" if ds_type in _HTTPS_PROTOCOLS else "jdbc"


def _make_bin_data(
    type: str,
    host: str,
    port: int,
    database: str,
    account: str,
    password: str,
    schema: str | None = None,
) -> dict[str, Any]:
    d: dict[str, Any] = {
        "host": host,
        "port": port,
        "database_name": database,
        "connect_protocol": _connect_protocol(type),
        "account": account,
        "password": password,
    }
    if schema is not None:
        d["schema"] = schema
    return d


class DataSourcesResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def test(
        self,
        type: str,
        host: str,
        port: int,
        database: str,
        account: str,
        password: str,
        schema: str | None = None,
    ) -> bool:
        self._http.post(
            "/api/data-connection/v1/datasource/test",
            json={
                "type": type,
                "bin_data": _make_bin_data(type, host, port, database, account, password, schema),
            },
        )
        return True

    def create(
        self,
        name: str,
        type: str,
        host: str,
        port: int,
        database: str,
        account: str,
        password: str,
        schema: str | None = None,
        comment: str | None = None,
    ) -> DataSource:
        body: dict[str, Any] = {
            "name": name,
            "type": type,
            "bin_data": _make_bin_data(type, host, port, database, account, password, schema),
        }
        if comment:
            body["comment"] = comment
        data = self._http.post("/api/data-connection/v1/datasource", json=body)
        return _parse_datasource(data)

    def list(self, *, keyword: str | None = None, type: str | None = None) -> list[DataSource]:
        params: dict[str, Any] = {}
        if keyword:
            params["keyword"] = keyword
        if type:
            params["type"] = type
        data = self._http.get("/api/data-connection/v1/datasource", params=params or None)
        items = data if isinstance(data, list) else (data.get("entries") or data.get("data") or [])
        return [_parse_datasource(d) for d in items]

    def get(self, id: str) -> DataSource:
        data = self._http.get(f"/api/data-connection/v1/datasource/{id}")
        return _parse_datasource(data)

    def delete(self, id: str) -> None:
        self._http.delete(f"/api/data-connection/v1/datasource/{id}")

    def list_tables(
        self,
        id: str,
        *,
        keyword: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Table]:
        params: dict[str, Any] = {}
        if keyword:
            params["keyword"] = keyword
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        data = self._http.get(
            f"/api/data-connection/v1/metadata/data-source/{id}",
            params=params or None,
        )
        items = data if isinstance(data, list) else (data.get("entries") or data.get("data") or [])
        return [
            Table(
                name=t["name"],
                columns=[
                    Column(
                        name=c["name"],
                        type=c.get("type", "varchar"),
                        comment=c.get("comment"),
                    )
                    for c in t.get("columns", t.get("fields", []))
                ],
            )
            for t in items
        ]


def _parse_datasource(d: Any) -> DataSource:
    if isinstance(d, list):
        d = d[0]
    return DataSource(
        id=str(d.get("id", d.get("ds_id", ""))),
        name=d.get("name", ""),
        type=d.get("type", ""),
        comment=d.get("comment"),
    )
