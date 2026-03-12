"""SDK resource: knowledge networks (ontology-manager + agent-retrieval)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kweaver.types import BuildJob, BuildStatus, KNStatistics, KnowledgeNetwork

if TYPE_CHECKING:
    from kweaver._http import HttpClient


class KnowledgeNetworksResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        name: str,
        *,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> KnowledgeNetwork:
        body: dict[str, Any] = {"name": name}
        if description:
            body["description"] = description
        if tags:
            body["tags"] = tags
        data = self._http.post(
            "/api/ontology-manager/v1/knowledge-networks", json=body
        )
        return _parse_kn(data)

    def list(self, *, name: str | None = None) -> list[KnowledgeNetwork]:
        params: dict[str, Any] = {}
        if name:
            params["name"] = name
        data = self._http.get(
            "/api/ontology-manager/v1/knowledge-networks", params=params or None
        )
        items = data if isinstance(data, list) else (data.get("entries") or data.get("data") or [])
        return [_parse_kn(d) for d in items]

    def get(self, id: str) -> KnowledgeNetwork:
        data = self._http.get(f"/api/ontology-manager/v1/knowledge-networks/{id}")
        return _parse_kn(data)

    def update(self, id: str, **kwargs: Any) -> KnowledgeNetwork:
        data = self._http.put(
            f"/api/ontology-manager/v1/knowledge-networks/{id}", json=kwargs
        )
        return _parse_kn(data)

    def delete(self, id: str) -> None:
        self._http.delete(f"/api/ontology-manager/v1/knowledge-networks/{id}")

    def build(self, id: str) -> BuildJob:
        self._http.post(
            "/api/agent-retrieval/in/v1/kn/full_build_ontology",
            json={"kn_id": id},
        )
        job = BuildJob(kn_id=id)
        job.set_poll_fn(lambda: self.build_status(id))
        return job

    def build_status(self, id: str) -> BuildStatus:
        data = self._http.get(
            "/api/agent-retrieval/in/v1/kn/full_ontology_building_status",
            params={"kn_id": id},
        )
        return BuildStatus(
            state=data.get("state", "running"),
            state_detail=data.get("state_detail"),
        )


def _parse_kn(d: Any) -> KnowledgeNetwork:
    if isinstance(d, list):
        d = d[0]
    stats = d.get("statistics")
    return KnowledgeNetwork(
        id=str(d.get("id", d.get("kn_id", ""))),
        name=d.get("name", ""),
        tags=d.get("tags", []),
        comment=d.get("comment") or d.get("description"),
        statistics=KNStatistics(**stats) if stats else None,
    )
