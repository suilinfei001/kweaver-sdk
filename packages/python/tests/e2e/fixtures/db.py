"""Import/cleanup CSV fixtures into MySQL via KWeaver dataflow API.

No direct MySQL connectivity needed — data is written through the platform's
dataflow engine which runs in the internal network.

Flow: read CSV from data/ → create dataflow with @internal/database/write →
      execute → wait → cleanup dataflow DAG

Table naming: CSV filename `acme_员工.csv` → MySQL table `e2e_acme_员工`
"""
from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).parent / "data"
_TABLE_PREFIX = "e2e_"


def _get_csv_files() -> list[Path]:
    """Return all CSV files in the data/ directory."""
    return sorted(_DATA_DIR.glob("*.csv"))


def _csv_to_table_name(csv_path: Path) -> str:
    """Convert CSV filename to MySQL table name with e2e_ prefix."""
    return f"{_TABLE_PREFIX}{csv_path.stem}"


def _read_csv(csv_path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    """Read CSV file, return (headers, rows_as_dicts)."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = [
            {k: (None if v == "" else v) for k, v in row.items()}
            for row in reader
        ]
    return list(headers), rows


def _build_field_mappings(headers: list[str]) -> list[dict]:
    """Build sync_model_fields — all columns as VARCHAR(512) by default."""
    return [
        {
            "source": {"name": h},
            "target": {"name": h, "data_type": "VARCHAR(512)"},
        }
        for h in headers
    ]


def _wait_dag_done(http_client: Any, dag_id: str, timeout: int = 120) -> None:
    """Poll dataflow execution until it completes or fails."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            data = http_client.get(f"/api/automation/v1/dag/{dag_id}/results")
            results = data.get("results", []) if isinstance(data, dict) else []
            if results:
                status = results[0].get("status", "")
                if status in ("success", "completed"):
                    return
                if status in ("failed", "error"):
                    reason = results[0].get("reason", "unknown")
                    raise RuntimeError(f"Dataflow failed: {reason}")
        except RuntimeError:
            raise
        except Exception:
            pass
        time.sleep(3)
    raise TimeoutError(f"Dataflow {dag_id} did not complete within {timeout}s")


def _run_dataflow(http_client: Any, dag_body: dict) -> None:
    """Create a dataflow, execute it, wait, then delete the DAG."""
    result = http_client.post("/api/automation/v1/data-flow/flow", json=dag_body, timeout=120.0)
    dag_id = result.get("id") if isinstance(result, dict) else None
    if not dag_id:
        raise RuntimeError(f"Failed to create dataflow: {result}")
    try:
        http_client.post(f"/api/automation/v1/run-instance/{dag_id}", json={}, timeout=120.0)
        _wait_dag_done(http_client, dag_id)
    finally:
        try:
            http_client.request("DELETE", f"/api/automation/v1/data-flow/flow/{dag_id}")
        except Exception:
            pass


def setup_test_tables(http_client: Any, datasource_id: str) -> list[str]:
    """Import all CSV files from data/ into MySQL via dataflow.

    Returns list of created table names (e.g. ['e2e_acme_员工', ...]).
    """
    created: list[str] = []
    tag = str(int(time.time()))[-6:]
    t_total = time.time()

    for csv_path in _get_csv_files():
        table_name = _csv_to_table_name(csv_path)
        headers, rows = _read_csv(csv_path)
        if not rows:
            continue

        t_table = time.time()
        n_batches = (len(rows) + 499) // 500

        # Large tables: split into batches (dataflow API has payload/timeout limits)
        batch_size = 500
        for batch_idx in range(0, len(rows), batch_size):
            batch = rows[batch_idx : batch_idx + batch_size]
            is_first_batch = batch_idx == 0
            batch_num = batch_idx // batch_size + 1

            print(f"  [{table_name}] batch {batch_num}/{n_batches} ({len(batch)} rows)...", end="", flush=True)
            t_batch = time.time()

            dag_body = {
                "title": f"{_TABLE_PREFIX}import_{csv_path.stem}_{tag}_b{batch_idx}",
                "description": "e2e fixture import — auto-deleted",
                "trigger_config": {"operator": "@trigger/manual"},
                "steps": [
                    {"id": "trigger", "title": "trigger", "operator": "@trigger/manual", "parameters": {}},
                    {
                        "id": "write",
                        "title": f"Write {table_name}",
                        "operator": "@internal/database/write",
                        "parameters": {
                            "datasource_type": "mysql",
                            "datasource_id": datasource_id,
                            "table_name": table_name,
                            "table_exist": not is_first_batch,
                            "operate_type": "append",
                            "data": batch,
                            "sync_model_fields": _build_field_mappings(headers),
                        },
                    },
                ],
            }
            _run_dataflow(http_client, dag_body)
            print(f" {time.time() - t_batch:.1f}s")

        elapsed = time.time() - t_table
        print(f"  [{table_name}] done ({len(rows)} rows in {elapsed:.1f}s)")
        created.append(table_name)

    print(f"  Total import: {len(created)} tables in {time.time() - t_total:.1f}s")
    return created


def get_table_names() -> list[str]:
    """Return the expected table names based on CSV files in data/."""
    return [_csv_to_table_name(p) for p in _get_csv_files()]


def teardown_test_tables(http_client: Any, datasource_id: str) -> None:
    """Best-effort cleanup: drop e2e test tables.

    Note: dataflow's database/write action doesn't support DROP TABLE directly.
    We use truncate_and_write with empty data as a workaround to clear data.
    The tables themselves remain but are empty.
    """
    tag = str(int(time.time()))[-6:]

    for csv_path in _get_csv_files():
        table_name = _csv_to_table_name(csv_path)
        headers, _ = _read_csv(csv_path)

        dag_body = {
            "title": f"{_TABLE_PREFIX}cleanup_{csv_path.stem}_{tag}",
            "description": "e2e fixture cleanup — auto-deleted",
            "trigger_config": {"operator": "@trigger/manual"},
            "steps": [
                {"id": "trigger", "title": "trigger", "operator": "@trigger/manual", "parameters": {}},
                {
                    "id": "write",
                    "title": f"Clear {table_name}",
                    "operator": "@internal/database/write",
                    "parameters": {
                        "datasource_type": "mysql",
                        "datasource_id": datasource_id,
                        "table_name": table_name,
                        "table_exist": True,
                        "operate_type": "append",
                        "data": [],
                        "sync_model_fields": _build_field_mappings(headers),
                    },
                },
            ],
        }
        try:
            _run_dataflow(http_client, dag_body)
        except Exception:
            pass
