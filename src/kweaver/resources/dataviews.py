"""SDK resource: data views (mdl-data-model service)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kweaver.types import DataView, ViewField

if TYPE_CHECKING:
    from kweaver._http import HttpClient


class DataViewsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        name: str,
        datasource_id: str,
        *,
        table: str | None = None,
        sql: str | None = None,
        fields: list[dict[str, Any]] | None = None,
    ) -> DataView:
        if table:
            view_type = "atomic"
            scope_type = "source"
            config = {"table": table}
            title = table
        elif sql:
            view_type = "custom"
            scope_type = "sql"
            config = {"sql": sql}
            title = name
        else:
            raise ValueError("Either 'table' or 'sql' must be provided")

        body = [
            {
                "name": name,
                "type": view_type,
                "query_type": "SQL",
                "data_source_id": datasource_id,
                "data_scope": [
                    {
                        "id": "node_0",
                        "title": title,
                        "type": scope_type,
                        "config": config,
                        "input_nodes": [],
                        "output_fields": [],
                    }
                ],
                "fields": fields or [],
            }
        ]
        data = self._http.post("/api/mdl-data-model/v1/data-views", json=body)
        return _parse_dataview(data)

    def list(
        self,
        *,
        datasource_id: str | None = None,
        name: str | None = None,
        type: str | None = None,
    ) -> list[DataView]:
        params: dict[str, Any] = {}
        if datasource_id:
            params["data_source_id"] = datasource_id
        if name:
            params["name"] = name
        if type:
            params["type"] = type
        data = self._http.get("/api/mdl-data-model/v1/data-views", params=params or None)
        items = data if isinstance(data, list) else (data.get("entries") or data.get("data") or [])
        return [_parse_single_dataview(d) for d in items]

    def get(self, id: str) -> DataView:
        data = self._http.get(f"/api/mdl-data-model/v1/data-views/{id}")
        return _parse_single_dataview(data)

    def delete(self, id: str) -> None:
        self._http.delete(f"/api/mdl-data-model/v1/data-views/{id}")


def _parse_dataview(data: Any) -> DataView:
    if isinstance(data, list):
        data = data[0]
    return _parse_single_dataview(data)


def _parse_single_dataview(d: dict[str, Any]) -> DataView:
    return DataView(
        id=str(d.get("id", "")),
        name=d.get("name", ""),
        query_type=d.get("query_type", "SQL"),
        fields=[
            ViewField(
                name=f["name"],
                type=f.get("type", "varchar"),
                display_name=f.get("display_name"),
                comment=f.get("comment"),
            )
            for f in d.get("fields", [])
        ],
    )
