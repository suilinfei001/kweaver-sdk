"""E2E: full flow — connect database → build knowledge network → query.

This is the most comprehensive E2E test: it exercises the complete
lifecycle through the Skill layer.

Destructive: creates and deletes datasources, knowledge networks, etc.
"""

from __future__ import annotations

from typing import Any

import pytest

from kweaver import ADPClient
from kweaver.skills.build_kn import BuildKnSkill
from kweaver.skills.connect_db import ConnectDbSkill
from kweaver.skills.load_kn_context import LoadKnContextSkill
from kweaver.skills.query_kn import QueryKnSkill

pytestmark = [pytest.mark.e2e, pytest.mark.destructive]


def test_skill_full_lifecycle(adp_client: ADPClient, db_config: dict[str, Any]):
    """End-to-end: connect_db → build_kn → load_kn_context → query_kn."""

    # ── Step 1: connect_db ──────────────────────────────────────────────
    connect_skill = ConnectDbSkill(client=adp_client)
    connect_result = connect_skill.run(
        db_type=db_config["type"],
        host=db_config["host"],
        port=db_config["port"],
        database=db_config["database"],
        account=db_config["account"],
        password=db_config["password"],
        schema=db_config.get("schema"),
    )

    assert "error" not in connect_result, f"connect_db failed: {connect_result}"
    assert connect_result["datasource_id"]
    assert len(connect_result["tables"]) > 0, "No tables discovered"

    ds_id = connect_result["datasource_id"]
    first_table = connect_result["tables"][0]["name"]

    try:
        # ── Step 2: build_kn ────────────────────────────────────────────
        build_skill = BuildKnSkill(client=adp_client)
        build_result = build_skill.run(
            datasource_id=ds_id,
            network_name="e2e_full_flow_kn",
            tables=[first_table],
        )

        assert "error" not in build_result, f"build_kn failed: {build_result}"
        assert build_result["kn_id"]
        assert build_result["status"] in ("completed", "failed")
        assert len(build_result["object_types"]) == 1

        kn_id = build_result["kn_id"]

        # ── Step 3: load_kn_context — overview ──────────────────────────
        context_skill = LoadKnContextSkill(client=adp_client)
        overview = context_skill.run(mode="overview")
        assert any(
            kn["id"] == kn_id for kn in overview["knowledge_networks"]
        ), "Built KN not found in overview"

        # ── Step 4: load_kn_context — schema ────────────────────────────
        schema = context_skill.run(mode="schema", kn_id=kn_id, include_samples=True)
        assert schema["kn_id"] == kn_id
        assert len(schema["object_types"]) == 1
        assert schema["object_types"][0]["name"] == first_table

        # ── Step 5: load_kn_context — instances ─────────────────────────
        instances = context_skill.run(
            mode="instances", kn_id=kn_id,
            object_type=first_table, limit=5,
        )
        assert "data" in instances
        assert instances["object_type_schema"]["name"] == first_table

        # ── Step 6: query_kn — semantic search ──────────────────────────
        query_skill = QueryKnSkill(client=adp_client)
        search_result = query_skill.run(
            kn_id=kn_id, mode="search", query=first_table,
        )
        assert "data" in search_result

    finally:
        # Cleanup: delete KN and datasource
        try:
            adp_client.knowledge_networks.delete(kn_id)
        except Exception:
            pass
        try:
            adp_client.datasources.delete(ds_id)
        except Exception:
            pass
