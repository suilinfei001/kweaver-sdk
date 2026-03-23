"""Scenario 3: Agent Pipeline — data → KN → Context Loader → Agent → conversation.

Two modes:
  Default:   use existing KN in the environment (fast, read-only)
  --build:   full lifecycle from CSV import (slow, creates & cleans up everything)

Usage:
  pytest tests/e2e/integration/test_agent_pipeline.py --run-destructive -v -s
  pytest tests/e2e/integration/test_agent_pipeline.py --run-destructive --build -v -s
"""
from __future__ import annotations

import time
from typing import Any

import pytest

from kweaver import KWeaverClient
from kweaver.resources.context_loader import ContextLoaderResource

from tests.e2e.fixtures.config import (
    PREFIX as _PREFIX,
    PK_HINTS as _PK_HINTS,
    KNOWN_OT_NAMES,
    BKN_ADVANCED_CONFIG,
    AGENT_SYSTEM_PROMPT,
)

pytestmark = [pytest.mark.e2e, pytest.mark.destructive]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _discover_existing_kns(client: KWeaverClient) -> list[dict[str, Any]]:
    """Find all usable KNs with known OT names, sorted by relevance."""
    kns = client.knowledge_networks.list()
    candidates = []
    for kn in kns:
        if kn.name.startswith(_PREFIX):
            continue
        try:
            ots = client.object_types.list(kn.id)
        except Exception:
            continue
        indexed = [ot for ot in ots if ot.status and ot.status.doc_count > 0]
        if not indexed:
            continue
        total = sum(ot.status.doc_count for ot in indexed)
        known_count = sum(1 for ot in indexed if ot.name in KNOWN_OT_NAMES)
        if known_count == 0:
            continue  # skip KNs with no recognizable OTs
        candidates.append({
            "kn": kn,
            "ots": indexed,
            "ot_ids": [ot.id for ot in indexed],
            "total_docs": total,
            "known_count": known_count,
        })
    # Sort: known OT count desc, then total docs desc
    return sorted(candidates, key=lambda c: (c["known_count"], c["total_docs"]), reverse=True)


def _elapsed(t0: float) -> str:
    return f"[{time.time() - t0:.0f}s]"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def llm_model(kweaver_client: KWeaverClient) -> dict[str, str]:
    """Discover the first available LLM model."""
    http = kweaver_client._http
    try:
        data = http.get("/api/mf-model-manager/v1/llm/list", params={"page": 1, "size": 100})
    except Exception:
        pytest.skip("model-factory not available")
    models = (data or {}).get("data", [])
    llm = next((m for m in models if m.get("model_type") == "llm"), None)
    if not llm:
        pytest.skip("no LLM model available")
    return {"model_id": llm["model_id"], "model_name": llm["model_name"]}


@pytest.fixture(scope="module")
def pipeline_env(
    kweaver_client: KWeaverClient,
    e2e_env: dict[str, str],
    llm_model: dict[str, str],
    request: pytest.FixtureRequest,
):
    """Pipeline environment: either discover existing KN or build from scratch.

    --build mode: CSV → dataflow → DS → KN → OTs → build → agent → cleanup
    Default mode: discover existing KN → collect ground truth → agent → cleanup agent only
    """
    client = kweaver_client
    build_mode = request.config.getoption("--build")
    tag = str(int(time.time()))[-6:]
    t0 = time.time()
    env: dict[str, Any] = {"build_mode": build_mode}

    # ── Cleanup stale resources ───────────────────────────────────────────
    for kn in client.knowledge_networks.list():
        if kn.name.startswith(_PREFIX):
            try:
                client.knowledge_networks.delete(kn.id)
            except Exception:
                pass
    for ds in client.datasources.list(keyword=_PREFIX):
        try:
            client.datasources.delete(ds.id)
        except Exception:
            pass

    if build_mode:
        # ── BUILD MODE: full lifecycle ────────────────────────────────────

        db_host = e2e_env.get("db_host")
        if not db_host:
            pytest.skip("--build requires db_config (KWEAVER_TEST_DB_HOST)")

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

        # 1. Create datasource
        print(f"\n{_elapsed(t0)} Creating datasource...")
        ds = client.datasources.create(name=f"{_PREFIX}ds_{tag}", **db_cfg)
        env["ds"] = ds
        print(f"{_elapsed(t0)} DS: {ds.id}")

        # 2. Import CSV via dataflow
        print(f"{_elapsed(t0)} Importing CSV data via dataflow...")
        from tests.e2e.fixtures.db import setup_test_tables
        imported = setup_test_tables(client._http, ds.id)
        env["imported_tables"] = imported
        assert imported, "No tables imported"
        print(f"{_elapsed(t0)} Imported {len(imported)} tables")

        # 3. Discover tables
        print(f"{_elapsed(t0)} Waiting for metadata scan...")
        time.sleep(5)
        all_tables = client.datasources.list_tables(ds.id, limit=100, auto_scan=True)
        e2e_tables = {t.name: t for t in all_tables if t.name.startswith("e2e_")}
        assert e2e_tables, "No e2e_ tables found after import"
        print(f"{_elapsed(t0)} Found {len(e2e_tables)} tables")

        # 4. Create KN + OTs
        print(f"{_elapsed(t0)} Creating KN + OTs...")
        kn = client.knowledge_networks.create(name=f"{_PREFIX}kn_{tag}")
        env["kn"] = kn

        ot_ids: list[str] = []
        for table_name, table in e2e_tables.items():
            pk_hint, display_hint = _PK_HINTS.get(table_name, (None, None))
            col_names = [c.name for c in table.columns]
            pk = pk_hint if pk_hint and pk_hint in col_names else next(
                (c for c in col_names if "code" in c or c == "id"), col_names[0])
            display = display_hint if display_hint and display_hint in col_names and display_hint != pk else next(
                (c for c in col_names if "name" in c and c != pk), pk)
            try:
                dv = client.dataviews.create(
                    name=f"{_PREFIX}{table_name}_{tag}",
                    datasource_id=ds.id, table=table_name, columns=table.columns)
                ot = client.object_types.create(
                    kn.id, name=table_name.removeprefix("e2e_"),
                    dataview_id=dv.id, primary_keys=[pk], display_key=display)
                ot_ids.append(ot.id)
            except Exception as exc:
                print(f"  [warn] Skip {table_name}: {exc}")

        env["ot_ids"] = ot_ids
        print(f"{_elapsed(t0)} Created {len(ot_ids)} OTs")
        assert len(ot_ids) >= 3

        # 5. Build
        print(f"{_elapsed(t0)} Building KN...")
        job = client.knowledge_networks.build(kn.id)
        status = job.wait(timeout=600)
        print(f"{_elapsed(t0)} Build: {status.state}")
        assert status.state == "completed", f"Build failed: {status.state_detail}"

    else:
        # ── DEFAULT MODE: discover existing KNs ───────────────────────────
        print(f"\n{_elapsed(t0)} Discovering existing KNs...")
        found_list = _discover_existing_kns(client)
        if not found_list:
            pytest.skip("No existing KN with known data found (use --build to create)")
        # Use top KNs (up to 2)
        env["kn_list"] = found_list[:2]
        env["kn"] = found_list[0]["kn"]  # primary KN for agent
        env["ot_ids"] = []
        for f in found_list[:2]:
            env["ot_ids"].extend(f["ot_ids"])
            print(f"{_elapsed(t0)} KN: {f['kn'].name} ({f['total_docs']} docs, {len(f['ots'])} OTs)")

    # ── Common: collect ground truth from all KNs ─────────────────────────
    print(f"{_elapsed(t0)} Collecting ground truth...")
    from tests.e2e.fixtures.questions import collect_ground_truth, build_questions

    # Merge ground truth from all KNs
    all_gt: dict[str, Any] = {}
    kn_ids_for_gt = []
    if build_mode:
        kn_ids_for_gt = [env["kn"].id]
    else:
        kn_ids_for_gt = [f["kn"].id for f in env.get("kn_list", [{"kn": env["kn"]}])]

    for kn_id in kn_ids_for_gt:
        gt = collect_ground_truth(client, kn_id)
        for k, v in gt.items():
            if k == "ot_map":
                all_gt.setdefault("ot_map", {}).update(v)
            elif k not in all_gt:
                all_gt[k] = v

    env["ground_truth"] = all_gt
    env["questions"] = build_questions(all_gt)
    print(f"{_elapsed(t0)} {len(env['questions'])} questions built")

    # ── Common: create agent ──────────────────────────────────────────────
    print(f"{_elapsed(t0)} Creating agent...")
    ot_ids = env["ot_ids"]
    config: dict[str, Any] = {
        "input": {"fields": [{"name": "user_input", "type": "string", "desc": ""}]},
        "output": {"default_format": "markdown"},
        "system_prompt": AGENT_SYSTEM_PROMPT,
        "llms": [{
            "is_default": True,
            "llm_config": {
                "id": llm_model["model_id"],
                "name": llm_model["model_name"],
                "model_type": "llm",
                "max_tokens": 4096,
            },
        }],
        "data_source": {
            "kg": [
                {"kg_id": kn_info["kn"].id, "fields": kn_info["ot_ids"]}
                for kn_info in env.get("kn_list", [{"kn": env["kn"], "ot_ids": ot_ids}])
            ] if not build_mode else [{"kg_id": env["kn"].id, "fields": ot_ids}],
            "advanced_config": {"kg": BKN_ADVANCED_CONFIG},
        },
    }

    result = client.agents.create(
        name=f"{_PREFIX}agent_{tag}",
        profile="E2E agent pipeline test — auto-deleted",
        key=f"{_PREFIX}agent_{tag}",
        config=config,
    )
    env["agent_id"] = result["id"]
    print(f"{_elapsed(t0)} Agent: {result['id']}")

    try:
        client.agents.publish(env["agent_id"])
        agent = client.agents.get(env["agent_id"])
        env["agent_version"] = agent.version
        print(f"{_elapsed(t0)} Published: v={env['agent_version']}")
    except Exception as exc:
        env["agent_version"] = None
        print(f"{_elapsed(t0)} Publish failed: {exc}")

    print(f"{_elapsed(t0)} Setup complete.")
    yield env

    # ── Cleanup ───────────────────────────────────────────────────────────
    for fn in [
        lambda: client.agents.unpublish(env["agent_id"]),
        lambda: client.agents.delete(env["agent_id"]),
    ]:
        try:
            fn()
        except Exception:
            pass

    if build_mode:
        try:
            client.knowledge_networks.delete(env["kn"].id)
        except Exception:
            pass
        if "ds" in env:
            try:
                client.datasources.delete(env["ds"].id)
            except Exception:
                pass


# ── Tests ─────────────────────────────────────────────────────────────────────


def _make_cl(client: KWeaverClient, kn_id: str) -> ContextLoaderResource:
    """Create a ContextLoaderResource for the given KN."""
    token = client._http._auth.auth_headers().get(
        "Authorization", "").removeprefix("Bearer ").strip()
    base_url = str(client._http._client.base_url).rstrip("/")
    return ContextLoaderResource(base_url, token, kn_id=kn_id)


def _retry(fn, attempts=3, delay=2):
    """Retry a callable up to N times."""
    import time as _time
    last_err = None
    for i in range(attempts):
        try:
            return fn()
        except RuntimeError:
            raise  # don't retry RuntimeError (MCP not available)
        except Exception as e:
            last_err = e
            if i < attempts - 1:
                _time.sleep(delay)
    raise last_err


def _get_kn_ids(env: dict) -> list[str]:
    """Get all KN IDs from the pipeline env."""
    if "kn_list" in env:
        return [f["kn"].id for f in env["kn_list"]]
    return [env["kn"].id]


# ── Test: Data ────────────────────────────────────────────────────────────────


def test_data_indexed(kweaver_client: KWeaverClient, pipeline_env):
    """KNs should have multiple OTs with indexed data."""
    total_ots = 0
    total_docs = 0
    for kn_id in _get_kn_ids(pipeline_env):
        ots = kweaver_client.object_types.list(kn_id)
        indexed = [ot for ot in ots if ot.status and ot.status.doc_count > 0]
        docs = sum(ot.status.doc_count for ot in indexed)
        total_ots += len(indexed)
        total_docs += docs
        kn_name = next((f["kn"].name for f in pipeline_env.get("kn_list", []) if f["kn"].id == kn_id), kn_id)
        print(f"  {kn_name}: {len(indexed)} OTs, {docs} docs")
        for ot in indexed:
            print(f"    {ot.name}: {ot.status.doc_count}")
    assert total_ots >= 3, f"Expected 3+ OTs, got {total_ots}"
    assert total_docs >= 100, f"Expected 100+ docs, got {total_docs}"


# ── Tests: Context Loader ─────────────────────────────────────────────────────


def test_cl_kn_search_schema(kweaver_client: KWeaverClient, pipeline_env):
    """Context Loader kn_search should discover object types in at least one KN."""
    succeeded = 0
    errors = []
    for kn_id in _get_kn_ids(pipeline_env):
        cl = _make_cl(kweaver_client, kn_id)
        ots = kweaver_client.object_types.list(kn_id)
        term = next((ot.name for ot in ots if ot.status and ot.status.doc_count > 0), "物料")
        try:
            result = _retry(lambda: cl.kn_search(term), attempts=3, delay=3)
            raw = result.get("raw", "")
            assert raw, f"Empty kn_search for '{term}'"
            print(f"  kn_search('{term}'): {len(raw)} chars")
            succeeded += 1
        except RuntimeError as e:
            pytest.skip(f"MCP not available: {e}")
        except Exception as e:
            errors.append(f"{kn_id}: {e}")
            print(f"  [warn] kn_search failed for KN {kn_id}: {e}")
    assert succeeded > 0, f"kn_search failed for all KNs: {errors}"


def test_cl_kn_search_only_schema(kweaver_client: KWeaverClient, pipeline_env):
    """kn_search with only_schema=True should return schema without instances."""
    kn_id = _get_kn_ids(pipeline_env)[0]
    cl = _make_cl(kweaver_client, kn_id)
    ots = kweaver_client.object_types.list(kn_id)
    term = next((ot.name for ot in ots if ot.status and ot.status.doc_count > 0), "物料")
    try:
        result = _retry(lambda: cl.kn_search(term, only_schema=True))
    except RuntimeError as e:
        pytest.skip(f"MCP not available: {e}")
    raw = result.get("raw", "")
    assert raw, "only_schema returned empty"
    assert "object_types" in raw, "only_schema should contain object_types"


def test_cl_query_instance_eq(kweaver_client: KWeaverClient, pipeline_env):
    """Context Loader query with == condition should find exact match."""
    gt = pipeline_env["ground_truth"]
    ot_map = gt.get("ot_map", {})

    for kn_id in _get_kn_ids(pipeline_env):
        ots_in_kn = kweaver_client.object_types.list(kn_id)
        for ot in ots_in_kn:
            if not (ot.status and ot.status.doc_count > 0):
                continue
            try:
                result = _retry(lambda: kweaver_client.query.instances(kn_id, ot.id, limit=1))
            except Exception:
                continue
            if not result.data or not result.data[0].get("_instance_identity"):
                continue

            identity = result.data[0]["_instance_identity"]
            pk_field = list(identity.keys())[0]
            pk_value = identity[pk_field]

            cl = _make_cl(kweaver_client, kn_id)
            mcp_result = _retry(lambda: cl.query_object_instance(
                ot.id,
                condition={
                    "operation": "and",
                    "sub_conditions": [
                        {"field": pk_field, "operation": "==", "value_from": "const", "value": pk_value},
                    ],
                },
                limit=1,
            ))
            raw = mcp_result.get("raw", "")
            assert str(pk_value) in raw, f"MCP missing {pk_field}={pk_value} in {ot.name}"
            print(f"  {ot.name}: {pk_field}={pk_value} found via CL")
            return  # one successful match is enough
    pytest.skip("No OT with instance identity found")


def test_cl_query_instance_in(kweaver_client: KWeaverClient, pipeline_env):
    """Context Loader query with 'in' operator should match multiple values."""
    gt = pipeline_env["ground_truth"]
    ot_map = gt.get("ot_map", {})

    for kn_id in _get_kn_ids(pipeline_env):
        ots_in_kn = kweaver_client.object_types.list(kn_id)
        for ot in ots_in_kn:
            if not (ot.status and ot.status.doc_count > 5):
                continue
            try:
                result = _retry(lambda: kweaver_client.query.instances(kn_id, ot.id, limit=3))
            except Exception:
                continue
            samples_with_id = [r for r in result.data if r.get("_instance_identity")]
            if len(samples_with_id) < 2:
                continue

            identity1 = samples_with_id[0]["_instance_identity"]
            identity2 = samples_with_id[1]["_instance_identity"]
            pk_field = list(identity1.keys())[0]
            pk_values = [identity1[pk_field], identity2[pk_field]]

            cl = _make_cl(kweaver_client, kn_id)
            mcp_result = _retry(lambda: cl.query_object_instance(
                ot.id,
                condition={
                    "operation": "and",
                    "sub_conditions": [
                        {"field": pk_field, "operation": "in", "value_from": "const", "value": pk_values},
                    ],
                },
                limit=5,
            ))
            raw = mcp_result.get("raw", "")
            assert str(pk_values[0]) in raw, f"First value {pk_values[0]} not in CL response"
            print(f"  {ot.name}: 'in' query with {pk_values} OK")
            return
    pytest.skip("No OT with enough instances for 'in' query")


def test_cl_rest_consistency(kweaver_client: KWeaverClient, pipeline_env):
    """REST and Context Loader should return consistent data for the same query."""
    for kn_id in _get_kn_ids(pipeline_env):
        ots = kweaver_client.object_types.list(kn_id)
        for ot in ots:
            if not (ot.status and ot.status.doc_count > 0):
                continue
            try:
                rest = _retry(lambda: kweaver_client.query.instances(kn_id, ot.id, limit=1))
            except Exception:
                continue
            if not rest.data or not rest.data[0].get("_instance_identity"):
                continue

            identity = rest.data[0]["_instance_identity"]
            pk_field = list(identity.keys())[0]
            pk_value = identity[pk_field]
            rest_display = str(rest.data[0].get("_display", ""))

            cl = _make_cl(kweaver_client, kn_id)
            mcp_result = _retry(lambda: cl.query_object_instance(
                ot.id,
                condition={
                    "operation": "and",
                    "sub_conditions": [
                        {"field": pk_field, "operation": "==", "value_from": "const", "value": pk_value},
                    ],
                },
                limit=1,
            ))
            raw = mcp_result.get("raw", "")
            assert str(pk_value) in raw, f"REST/CL mismatch: {pk_field}={pk_value} not in CL"
            if rest_display:
                assert rest_display in raw, f"REST _display='{rest_display}' not in CL"
            print(f"  {ot.name}: REST↔CL consistent for {pk_field}={pk_value}")
            return
    pytest.skip("No OT with instance identity for consistency check")


def test_agent_bound_to_kn(kweaver_client: KWeaverClient, pipeline_env):
    """Agent should be bound to KN(s)."""
    agent = kweaver_client.agents.get(pipeline_env["agent_id"])
    kn_id = pipeline_env["kn"].id
    assert kn_id in agent.kn_ids, f"Agent not bound to {kn_id}, got {agent.kn_ids}"


def test_questions_generated(pipeline_env):
    """Ground truth should produce meaningful questions."""
    qs = pipeline_env["questions"]
    assert len(qs) >= 5, f"Only {len(qs)} questions generated"
    print(f"  {len(qs)} questions:")
    for q in qs:
        print(f"    [{q.id}] {q.question[:70]}")


def test_agent_conversations(kweaver_client: KWeaverClient, pipeline_env):
    """Run all questions against the agent and verify responses."""
    if not pipeline_env.get("agent_version"):
        pytest.skip("Agent not published (backend bug)")

    questions = pipeline_env["questions"]
    results: list[tuple[str, str | None]] = []

    for q in questions:
        try:
            conv = kweaver_client.conversations.create(pipeline_env["agent_id"])
            reply = kweaver_client.conversations.send_message(
                conv.id, content=q.question,
                agent_id=pipeline_env["agent_id"],
                agent_version=pipeline_env["agent_version"],
            )
            assert reply.content and reply.role == "assistant"
            error = q.verify(reply.content)
            results.append((q.id, error))
            tag = "OK" if not error else f"FAIL: {error}"
            print(f"  [{q.id}] {tag}")
            if error:
                print(f"    Q: {q.question[:80]}")
                print(f"    A: {reply.content[:200]}")
        except Exception as exc:
            results.append((q.id, str(exc)))
            print(f"  [{q.id}] ERROR: {exc}")

    passed = sum(1 for _, e in results if e is None)
    total = len(results)
    failed = [(qid, err) for qid, err in results if err]
    print(f"\n  Score: {passed}/{total}")

    min_pass = max(1, total // 2)
    assert passed >= min_pass, f"Only {passed}/{total} passed. Failures: {failed}"
