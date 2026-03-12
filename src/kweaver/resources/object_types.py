"""SDK resource: object types (ontology-manager)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kweaver.types import DataProperty, ObjectType, ObjectTypeStatus, Property

if TYPE_CHECKING:
    from kweaver._http import HttpClient

_PREFIX = "/api/ontology-manager/v1"


class ObjectTypesResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        kn_id: str,
        *,
        name: str,
        dataview_id: str,
        primary_keys: list[str] | None = None,
        primary_key: str | None = None,
        display_key: str,
        properties: list[Property] | None = None,
    ) -> ObjectType:
        if primary_keys is None:
            if primary_key is not None:
                primary_keys = [primary_key]
            else:
                raise ValueError("Either 'primary_keys' or 'primary_key' must be provided")

        entry: dict[str, Any] = {
            "name": name,
            "data_source": {"type": "data_view", "id": dataview_id},
            "primary_keys": primary_keys,
            "display_key": display_key,
        }
        if properties is not None:
            entry["data_properties"] = [_property_to_rest(p) for p in properties]
        else:
            entry["data_properties"] = []

        data = self._http.post(
            f"{_PREFIX}/knowledge-networks/{kn_id}/object-types",
            json={"entries": [entry]},
        )
        items = data if isinstance(data, list) else data.get("entries", data.get("data", [data]))
        return _parse_object_type(items[0], kn_id)

    def list(self, kn_id: str) -> list[ObjectType]:
        data = self._http.get(f"{_PREFIX}/knowledge-networks/{kn_id}/object-types")
        items = data if isinstance(data, list) else (data.get("entries") or data.get("data") or [])
        return [_parse_object_type(d, kn_id) for d in items]

    def get(self, kn_id: str, ot_id: str) -> ObjectType:
        data = self._http.get(
            f"{_PREFIX}/knowledge-networks/{kn_id}/object-types/{ot_id}"
        )
        return _parse_object_type(data, kn_id)

    def update(self, kn_id: str, ot_id: str, **kwargs: Any) -> ObjectType:
        data = self._http.put(
            f"{_PREFIX}/knowledge-networks/{kn_id}/object-types/{ot_id}",
            json=kwargs,
        )
        return _parse_object_type(data, kn_id)

    def delete(self, kn_id: str, ot_ids: str | list[str]) -> None:
        if isinstance(ot_ids, list):
            ot_ids = ",".join(ot_ids)
        self._http.delete(
            f"{_PREFIX}/knowledge-networks/{kn_id}/object-types/{ot_ids}"
        )


def _property_to_rest(p: Property) -> dict[str, Any]:
    d: dict[str, Any] = {
        "name": p.name,
        "display_name": p.display_name or p.name,
    }
    if p.type:
        d["type"] = p.type
    d["index_config"] = {
        "keyword_config": {"enabled": p.indexed},
        "fulltext_config": {"enabled": p.fulltext},
        "vector_config": {"enabled": p.vector},
    }
    return d


def _parse_object_type(d: dict[str, Any], kn_id: str) -> ObjectType:
    ds = d.get("data_source", {})
    dataview_id = ds.get("id", "") if isinstance(ds, dict) else ""

    props: list[DataProperty] = []
    for p in d.get("data_properties", d.get("properties", [])):
        ic = p.get("index_config", {})
        props.append(
            DataProperty(
                name=p["name"],
                display_name=p.get("display_name"),
                type=p.get("type", "varchar"),
                comment=p.get("comment"),
                indexed=ic.get("keyword_config", {}).get("enabled", False),
                fulltext=ic.get("fulltext_config", {}).get("enabled", False),
                vector=ic.get("vector_config", {}).get("enabled", False),
            )
        )

    status_data = d.get("status")
    status = ObjectTypeStatus(**status_data) if isinstance(status_data, dict) else None

    return ObjectType(
        id=str(d.get("id", "")),
        name=d.get("name", ""),
        kn_id=kn_id,
        dataview_id=dataview_id,
        primary_keys=d.get("primary_keys", []),
        display_key=d.get("display_key", ""),
        incremental_key=d.get("incremental_key"),
        properties=props,
        status=status,
    )
