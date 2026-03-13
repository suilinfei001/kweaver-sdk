"""Skill: build_kn — build a knowledge network from a connected datasource."""

from __future__ import annotations

from typing import Any

from kweaver.skills._base import BaseSkill

# Heuristics for auto-detecting primary key and display key
_PK_CANDIDATES = {"id", "pk", "key"}
_PK_TYPES = {"integer", "unsigned integer", "string", "varchar", "bigint", "int"}
_DISPLAY_HINTS = {"name", "title", "label", "display_name", "description"}


class BuildKnSkill(BaseSkill):
    def _execute(self, **kwargs: Any) -> dict[str, Any]:
        datasource_id: str = kwargs["datasource_id"]
        network_name: str | None = kwargs.get("network_name")
        target_tables: list[str] | None = kwargs.get("tables")
        relations: list[dict[str, str]] = kwargs.get("relations", [])

        # 1. Get available tables
        all_tables = self.client.datasources.list_tables(datasource_id)
        table_map = {t.name: t for t in all_tables}

        if target_tables:
            tables = [table_map[n] for n in target_tables if n in table_map]
        else:
            tables = all_tables

        if not tables:
            return {"error": True, "message": "没有可用的表"}

        # 2. Create data views
        view_map: dict[str, str] = {}  # table_name -> dataview_id
        for t in tables:
            dv = self.client.dataviews.create(
                name=t.name, datasource_id=datasource_id, table=t.name,
                columns=t.columns,
            )
            view_map[t.name] = dv.id

        # 3. Create knowledge network
        kn_name = network_name or f"kn_{datasource_id[:8]}"
        kn = self.client.knowledge_networks.create(name=kn_name)

        # 4. Create object types
        ot_map: dict[str, str] = {}  # table_name -> object_type_id
        ot_results: list[dict[str, Any]] = []

        for t in tables:
            pk = _detect_primary_key(t)
            dk = _detect_display_key(t, pk)
            ot = self.client.object_types.create(
                kn.id,
                name=t.name,
                dataview_id=view_map[t.name],
                primary_keys=[pk],
                display_key=dk,
            )
            ot_map[t.name] = ot.id
            ot_results.append({
                "name": ot.name,
                "id": ot.id,
                "field_count": len(t.columns),
            })

        # 5. Create relation types
        rt_results: list[dict[str, Any]] = []
        for rel in relations:
            from_table = rel["from_table"]
            to_table = rel["to_table"]
            if from_table not in ot_map or to_table not in ot_map:
                continue
            rt = self.client.relation_types.create(
                kn.id,
                name=rel["name"],
                source_ot_id=ot_map[from_table],
                target_ot_id=ot_map[to_table],
                mappings=[(rel["from_field"], rel["to_field"])],
            )
            rt_results.append({
                "name": rt.name,
                "from": from_table,
                "to": to_table,
            })

        # 6. Build and wait
        job = self.client.knowledge_networks.build(kn.id)
        status = job.wait()

        return {
            "kn_id": kn.id,
            "kn_name": kn.name,
            "object_types": ot_results,
            "relation_types": rt_results,
            "status": status.state,
        }


def _detect_primary_key(table: Any) -> str:
    """Heuristic: find the best primary key column."""
    for col in table.columns:
        if col.name.lower() in _PK_CANDIDATES and col.type.lower() in _PK_TYPES:
            return col.name
    # Fallback: first column with a suitable type
    for col in table.columns:
        if col.type.lower() in _PK_TYPES:
            return col.name
    return table.columns[0].name if table.columns else "id"


def _detect_display_key(table: Any, primary_key: str) -> str:
    """Heuristic: find the best display key column."""
    for col in table.columns:
        if any(hint in col.name.lower() for hint in _DISPLAY_HINTS):
            return col.name
    return primary_key
