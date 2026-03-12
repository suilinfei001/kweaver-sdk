"""Skill: query_kn — query a knowledge network."""

from __future__ import annotations

from typing import Any

from kweaver.skills._base import BaseSkill
from kweaver.types import Condition


class QueryKnSkill(BaseSkill):
    def _execute(self, **kwargs: Any) -> dict[str, Any]:
        kn_id: str = kwargs["kn_id"]
        mode: str = kwargs["mode"]

        if mode == "search":
            return self._search(kn_id, kwargs)
        elif mode == "instances":
            return self._instances(kn_id, kwargs)
        elif mode == "subgraph":
            return self._subgraph(kn_id, kwargs)
        else:
            return {"error": True, "message": f"未知查询模式: {mode}"}

    def _search(self, kn_id: str, kwargs: dict[str, Any]) -> dict[str, Any]:
        query: str = kwargs.get("query", "")
        result = self.client.query.semantic_search(kn_id=kn_id, query=query)
        return {
            "data": [c.model_dump() for c in result.concepts],
            "summary": f"找到 {result.hits_total} 个相关概念",
        }

    def _instances(self, kn_id: str, kwargs: dict[str, Any]) -> dict[str, Any]:
        object_type = kwargs.get("object_type", "")
        ot_id = self._resolve_object_type(kn_id, object_type)
        if ot_id is None:
            return {"error": True, "message": f"未找到对象类: {object_type}"}

        condition = None
        if kwargs.get("conditions"):
            condition = Condition(**kwargs["conditions"])

        limit = kwargs.get("limit", 20)
        result = self.client.query.instances(kn_id, ot_id, condition=condition, limit=limit)
        return {
            "data": result.data,
            "summary": f"查询到 {result.total_count or len(result.data)} 条记录",
        }

    def _subgraph(self, kn_id: str, kwargs: dict[str, Any]) -> dict[str, Any]:
        from kweaver.types import PathEdge, PathNode, SubgraphPath

        start_object = kwargs.get("start_object", "")
        start_condition = kwargs.get("start_condition")
        path_names: list[str] = kwargs.get("path", [])

        # Resolve names to IDs
        ot_list = self.client.object_types.list(kn_id)
        rt_list = self.client.relation_types.list(kn_id)
        ot_by_name = {ot.name: ot for ot in ot_list}

        start_ot = ot_by_name.get(start_object)
        if not start_ot:
            return {"error": True, "message": f"未找到起始对象类: {start_object}"}

        nodes = [PathNode(
            id=start_ot.id,
            condition=Condition(**start_condition) if start_condition else None,
        )]
        edges: list[PathEdge] = []

        for name in path_names:
            ot = ot_by_name.get(name)
            if ot:
                nodes.append(PathNode(id=ot.id))

        for rt in rt_list:
            node_ids = {n.id for n in nodes}
            if rt.source_ot_id in node_ids and rt.target_ot_id in node_ids:
                edges.append(PathEdge(id=rt.id, source=rt.source_ot_id, target=rt.target_ot_id))

        sp = SubgraphPath(object_types=nodes, relation_types=edges)
        result = self.client.query.subgraph(kn_id, [sp])
        return {
            "data": result.entries,
            "summary": f"子图查询返回 {len(result.entries)} 条记录",
        }

    def _resolve_object_type(self, kn_id: str, name_or_id: str) -> str | None:
        ot_list = self.client.object_types.list(kn_id)
        for ot in ot_list:
            if ot.id == name_or_id or ot.name == name_or_id:
                return ot.id
        return None
