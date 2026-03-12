"""Skill: load_kn_context — knowledge network Context Loader."""

from __future__ import annotations

from typing import Any

from kweaver.skills._base import BaseSkill
from kweaver.types import Condition


class LoadKnContextSkill(BaseSkill):
    def _execute(self, **kwargs: Any) -> dict[str, Any]:
        mode: str = kwargs["mode"]

        if mode == "overview":
            return self._overview(kwargs)
        elif mode == "schema":
            return self._schema(kwargs)
        elif mode == "instances":
            return self._instances(kwargs)
        else:
            return {"error": True, "message": f"未知模式: {mode}"}

    # ── overview ────────────────────────────────────────────────────────

    def _overview(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        keyword = kwargs.get("keyword")
        kns = self.client.knowledge_networks.list(name=keyword)
        return {
            "knowledge_networks": [
                {
                    "id": kn.id,
                    "name": kn.name,
                    "object_type_count": kn.statistics.object_types_total if kn.statistics else 0,
                    "relation_type_count": kn.statistics.relation_types_total if kn.statistics else 0,
                }
                for kn in kns
            ]
        }

    # ── schema ──────────────────────────────────────────────────────────

    def _schema(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        kn_id = self._resolve_kn_id(kwargs)
        if kn_id is None:
            return {"error": True, "message": "未找到指定的知识网络"}

        include_properties = kwargs.get("include_properties", True)
        include_samples = kwargs.get("include_samples", False)
        sample_size = kwargs.get("sample_size", 3)

        ot_list = self.client.object_types.list(kn_id)
        rt_list = self.client.relation_types.list(kn_id)

        # Build OT name lookup for relation display
        ot_names = {ot.id: ot.name for ot in ot_list}

        object_types = []
        for ot in ot_list:
            entry: dict[str, Any] = {
                "id": ot.id,
                "name": ot.name,
                "primary_keys": ot.primary_keys,
                "display_key": ot.display_key,
            }
            if include_properties:
                entry["properties"] = [
                    {
                        "name": p.name,
                        "type": p.type,
                        "indexed": p.indexed,
                        "fulltext": p.fulltext,
                        "vector": p.vector,
                    }
                    for p in ot.properties
                ]

            if include_samples:
                try:
                    result = self.client.query.instances(
                        kn_id, ot.id, limit=sample_size
                    )
                    entry["sample_data"] = result.data
                except Exception:
                    entry["sample_data"] = []

            object_types.append(entry)

        relation_types = [
            {
                "id": rt.id,
                "name": rt.name,
                "source": ot_names.get(rt.source_ot_id, rt.source_ot_id),
                "target": ot_names.get(rt.target_ot_id, rt.target_ot_id),
                "mapping_type": rt.mapping_type,
            }
            for rt in rt_list
        ]

        kn = self.client.knowledge_networks.get(kn_id)
        return {
            "kn_id": kn_id,
            "kn_name": kn.name,
            "object_types": object_types,
            "relation_types": relation_types,
        }

    # ── instances ───────────────────────────────────────────────────────

    def _instances(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        kn_id = self._resolve_kn_id(kwargs)
        if kn_id is None:
            return {"error": True, "message": "未找到指定的知识网络"}

        object_type = kwargs.get("object_type", "")
        include_type_info = kwargs.get("include_type_info", True)
        limit = kwargs.get("limit", 20)

        # Resolve object type name to ID
        ot_list = self.client.object_types.list(kn_id)
        target_ot = None
        for ot in ot_list:
            if ot.id == object_type or ot.name == object_type:
                target_ot = ot
                break

        if target_ot is None:
            return {"error": True, "message": f"未找到对象类: {object_type}"}

        condition = None
        if kwargs.get("conditions"):
            condition = Condition(**kwargs["conditions"])

        result = self.client.query.instances(
            kn_id, target_ot.id, condition=condition, limit=limit
        )

        out: dict[str, Any] = {
            "data": result.data,
            "total_count": result.total_count,
            "has_more": (result.total_count or 0) > limit,
        }

        if include_type_info:
            out["object_type_schema"] = {
                "name": target_ot.name,
                "properties": [
                    {"name": p.name, "type": p.type}
                    for p in target_ot.properties
                ],
            }

        return out

    # ── helpers ──────────────────────────────────────────────────────────

    def _resolve_kn_id(self, kwargs: dict[str, Any]) -> str | None:
        kn_id = kwargs.get("kn_id")
        if kn_id:
            return kn_id

        kn_name = kwargs.get("kn_name")
        if kn_name:
            kns = self.client.knowledge_networks.list(name=kn_name)
            if kns:
                return kns[0].id
        return None
