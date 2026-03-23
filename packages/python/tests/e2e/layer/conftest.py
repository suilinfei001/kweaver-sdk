"""Shared fixtures for layer tests — data bootstrap + read-only discovery."""
from __future__ import annotations

import time
from typing import Any

import pytest

from kweaver import KWeaverClient
from kweaver.resources.context_loader import ContextLoaderResource


def _discover_existing(client: KWeaverClient) -> dict[str, Any] | None:
    """Try to find an existing KN with indexed data, RT, and CG."""
    kns = client.knowledge_networks.list()
    for kn in kns:
        try:
            ots = client.object_types.list(kn.id)
        except Exception:
            continue
        indexed = [ot for ot in ots if ot.status and ot.status.doc_count > 0 and ot.properties]
        if not indexed:
            continue
        ot = min(indexed, key=lambda x: x.status.doc_count)
        result = client.query.instances(kn.id, ot.id, limit=1)
        if not result.data or not result.data[0].get("_instance_identity"):
            continue

        # Found a usable KN — gather optional RT/CG
        rts = client.relation_types.list(kn.id)
        cgs = client.concept_groups.list(kn.id)
        ot2 = next((o for o in indexed if o.id != ot.id), None)
        return {
            "kn": kn,
            "ot": ot,
            "ot2": ot2,
            "rt": rts[0] if rts else None,
            "cg": cgs[0] if cgs else None,
            "sample": result.data[0],
            "_created": False,
        }
    return None


def _cleanup_stale(client: KWeaverClient, prefix: str) -> None:
    """Delete leftover resources from previous test runs."""
    for kn in client.knowledge_networks.list():
        if kn.name.startswith(prefix):
            try:
                client.knowledge_networks.delete(kn.id)
            except Exception:
                pass
    for ds in client.datasources.list(keyword=prefix):
        try:
            client.datasources.delete(ds.id)
        except Exception:
            pass


def _bootstrap(client: KWeaverClient, db_config: dict[str, Any]) -> dict[str, Any]:
    """Create a complete KN with 2 OTs, RT, CG, and indexed data."""
    tag = str(int(time.time()))[-6:]
    prefix = "e2e_layer_"
    created_ids: dict[str, str] = {}

    _cleanup_stale(client, prefix)

    # 1. Datasource
    ds = client.datasources.create(name=f"{prefix}ds_{tag}", **db_config)
    created_ids["ds"] = ds.id

    # 2. Discover tables — need at least 2 for relation type
    tables = client.datasources.list_tables(ds.id, limit=10)
    assert len(tables) >= 1, "No tables found in test database"

    # 3. Dataviews
    t1 = tables[0]
    dv1 = client.dataviews.create(
        name=f"{prefix}{t1.name}_{tag}",
        datasource_id=ds.id, table=t1.name, columns=t1.columns,
    )

    dv2 = None
    t2 = tables[1] if len(tables) > 1 else None
    if t2:
        dv2 = client.dataviews.create(
            name=f"{prefix}{t2.name}_{tag}",
            datasource_id=ds.id, table=t2.name, columns=t2.columns,
        )

    # 4. Knowledge network
    kn = client.knowledge_networks.create(name=f"{prefix}kn_{tag}")
    created_ids["kn"] = kn.id

    # 5. Object types
    fields1 = [f.name for f in dv1.fields] if dv1.fields else [c.name for c in t1.columns]
    ot1 = client.object_types.create(
        kn.id, name=f"{prefix}{t1.name}_{tag}",
        dataview_id=dv1.id, primary_keys=[fields1[0]],
        display_key=fields1[1] if len(fields1) > 1 else fields1[0],
    )

    ot2 = None
    if dv2 and t2:
        fields2 = [f.name for f in dv2.fields] if dv2.fields else [c.name for c in t2.columns]
        ot2 = client.object_types.create(
            kn.id, name=f"{prefix}{t2.name}_{tag}",
            dataview_id=dv2.id, primary_keys=[fields2[0]],
            display_key=fields2[1] if len(fields2) > 1 else fields2[0],
        )

    # 6. Relation type (between OT1 and OT2 if both exist)
    rt = None
    if ot2:
        try:
            rt = client.relation_types.create(
                kn.id, name=f"{prefix}rt_{tag}",
                source_ot_id=ot1.id, target_ot_id=ot2.id,
                mappings=[(fields1[0], fields2[0])],
            )
        except Exception:
            pass  # relation type creation may fail if fields are incompatible

    # 7. Concept group
    cg = client.concept_groups.create(kn.id, name=f"{prefix}cg_{tag}")
    client.concept_groups.add_members(kn.id, cg.id, object_type_ids=[ot1.id])

    # 8. Build and wait
    job = client.knowledge_networks.build(kn.id)
    status = job.wait(timeout=300)
    assert status.state == "completed", f"Build failed: {status.state_detail}"

    # 9. Get sample instance
    result = client.query.instances(kn.id, ot1.id, limit=1)
    sample = result.data[0] if result.data else {}

    return {
        "kn": kn,
        "ot": ot1,
        "ot2": ot2,
        "rt": rt,
        "cg": cg,
        "sample": sample,
        "_created": True,
        "_ds_id": ds.id,
    }


@pytest.fixture(scope="session")
def e2e_test_data(kweaver_client: KWeaverClient, e2e_env: dict, request: pytest.FixtureRequest):
    """Session-scoped test data: KN with indexed data, OTs, RT, CG.

    1. Fast path: discover existing data (no mutations)
    2. Slow path: bootstrap from scratch using db_config (destructive)
    """
    # Fast path: discover
    data = _discover_existing(kweaver_client)
    if data:
        yield data
        return

    # Slow path: need db_config
    db_host = e2e_env.get("db_host")
    if not db_host:
        pytest.skip("No existing data and no db_config for bootstrap")

    db_cfg = {
        "type": e2e_env["db_type"],
        "host": db_host,
        "port": int(e2e_env["db_port"]),
        "database": e2e_env["db_name"],
        "account": e2e_env["db_user"],
        "password": e2e_env["db_pass"],
    }
    if e2e_env.get("db_schema"):
        db_cfg["schema"] = e2e_env["db_schema"]

    data = _bootstrap(kweaver_client, db_cfg)
    yield data

    # Cleanup bootstrapped resources
    if data.get("_created"):
        for delete_fn in [
            lambda: kweaver_client.knowledge_networks.delete(data["kn"].id),
            lambda: kweaver_client.datasources.delete(data["_ds_id"]),
        ]:
            try:
                delete_fn()
            except Exception:
                pass


@pytest.fixture(scope="module")
def kn_with_data(e2e_test_data):
    """Backward-compatible fixture — delegates to e2e_test_data."""
    return e2e_test_data


@pytest.fixture(scope="module")
def cl_context(kweaver_client: KWeaverClient, e2e_test_data):
    """Context Loader with a KN that has indexed data + sample instance."""
    kn = e2e_test_data["kn"]
    ot = e2e_test_data["ot"]
    sample = e2e_test_data.get("sample", {})
    if not sample.get("_instance_identity"):
        pytest.skip("No instance with _instance_identity available")

    token = kweaver_client._http._auth.auth_headers().get(
        "Authorization", ""
    ).removeprefix("Bearer ").strip()
    base_url = str(kweaver_client._http._client.base_url).rstrip("/")
    cl = ContextLoaderResource(base_url, token, kn_id=kn.id)
    return {"kn": kn, "ot": ot, "cl": cl, "sample": sample}


@pytest.fixture(scope="module")
def vega_client(kweaver_client: KWeaverClient):
    """Vega namespace."""
    return kweaver_client.vega
