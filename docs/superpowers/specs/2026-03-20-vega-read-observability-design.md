# Vega Read Operations & Observability Design

## Overview

Enhance kweaver-sdk (Python + TypeScript) with comprehensive read operations and observability capabilities for the Vega data management platform. All Vega resources are accessed through a `client.vega.*` namespace, and CLI commands live under `kweaver vega *`.

## Target Users

- **Platform operators** — daily health checks, fault diagnosis, capacity monitoring
- **Data engineers/developers** — programmatic data querying, metadata management
- **AI Agents** — tool-based data discovery and querying (via CLI + JSON output)

## Architecture

Vega capabilities are added as an extension within kweaver-sdk, reusing existing Auth, HTTP, and CLI infrastructure. A single `vega_url` configuration points to vega-backend (unified entry point for all Vega services).

```
KWeaverClient
├── agents               (existing)
├── knowledge_networks   (existing)
├── query                (existing)
└── vega                 (new — VegaNamespace)
    ├── catalogs         (CatalogsResource)
    ├── resources        (ResourcesResource)
    ├── connector_types  (ConnectorTypesResource)
    ├── metric_models    (MetricModelsResource)
    ├── event_models     (EventModelsResource)
    ├── trace_models     (TraceModelsResource)
    ├── data_views       (DataViewsResource)
    ├── data_dicts       (DataDictsResource)
    ├── objective_models (ObjectiveModelsResource)
    ├── query            (VegaQueryResource)
    ├── tasks            (TasksResource — unified: discover/metric/event)
    └── health / stats / inspect (methods on VegaNamespace)
```

### VegaNamespace Class

The `vega` attribute on `KWeaverClient` is a `VegaNamespace` instance that owns a **separate `HttpClient`** pointing at `vega_url`. This is necessary because Vega services use a different base URL than the main KWeaver platform.

```python
# Python
class VegaNamespace:
    """Namespace for all Vega resources. Owns its own HttpClient."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http
        self.catalogs = VegaCatalogsResource(http)
        self.resources = VegaResourcesResource(http)
        self.connector_types = VegaConnectorTypesResource(http)
        # 6 model resources via generic base (see Entropy Reduction section)
        self.metric_models = VegaMetricModelsResource(http)
        self.event_models = VegaEventModelsResource(http)
        self.trace_models = VegaTraceModelsResource(http)
        self.data_views = VegaDataViewsResource(http)
        self.data_dicts = VegaDataDictsResource(http)
        self.objective_models = VegaObjectiveModelsResource(http)
        self.query = VegaQueryResource(http)
        self.tasks = VegaTasksResource(http)

    def health(self) -> VegaServerInfo: ...
    def stats(self) -> VegaPlatformStats: ...
    def inspect(self, full: bool = False) -> VegaInspectReport: ...
```

```typescript
// TypeScript — uses VegaContext (parallel to ClientContext)
interface VegaContext {
  base(): { baseUrl: string; accessToken: string; businessDomain: string };
}
```

### Configuration

```python
# Explicit — vega_url is optional, vega features unavailable if not set
client = KWeaverClient(
    base_url="https://kweaver.example.com",
    token="...",
    vega_url="http://vega-backend:13014",
)
# client.vega is available

# Without vega_url — client.vega raises ValueError("vega_url not configured")
client = KWeaverClient(base_url="...", token="...")
client.vega  # → ValueError

# Environment variable
# KWEAVER_VEGA_URL=http://vega-backend:13014

# ~/.kweaver/<platform>/config.json
# { "vega_url": "http://vega-backend:13014" }

# ConfigAuth — reads vega_url from stored config
client = KWeaverClient(auth=ConfigAuth())
```

**Auth model**: Vega uses the same Hydra OAuth tokens as KWeaver. The separate `HttpClient` for vega reuses the same `AuthProvider` instance but with a different `base_url`.

### CLI helper

`make_client()` in CLI is extended to accept `--vega-url` and read `KWEAVER_VEGA_URL`. No separate `make_vega_client()` needed.

## Type Definitions

### Python (Pydantic models in `types.py`)

```python
# ── Vega entity types ────────────────────────────────────────────────

class VegaServerInfo(BaseModel):
    server_name: str
    server_version: str
    language: str
    go_version: str
    go_arch: str

class VegaCatalog(BaseModel):
    id: str
    name: str
    type: str                          # "physical" | "logical"
    connector_type: str                # "mysql" | "opensearch" | ...
    status: str                        # "active" | "disabled"
    health_status: str | None = None   # "healthy" | "degraded" | "unhealthy" | "offline" | "disabled"
    health_check_time: str | None = None
    health_error: str | None = None
    description: str | None = None
    config: dict[str, Any] | None = None

class VegaResource(BaseModel):
    id: str
    name: str
    catalog_id: str
    category: str              # "table" | "index" | "dataset" | "metric" | "topic" | "file" | "fileset" | "api" | "logicview"
    status: str                # "active" | "disabled" | "deprecated" | "stale"
    database: str | None = None
    schema_name: str | None = None
    properties: list[dict[str, Any]] = []
    description: str | None = None

class VegaConnectorType(BaseModel):
    type: str
    name: str
    enabled: bool = True
    description: str | None = None

class VegaMetricModel(BaseModel):
    id: str
    name: str
    group_id: str | None = None
    data_connection_id: str | None = None
    status: str | None = None
    description: str | None = None

class VegaEventModel(BaseModel):
    id: str
    name: str
    status: str | None = None
    level: str | None = None
    description: str | None = None

class VegaTraceModel(BaseModel):
    id: str
    name: str
    status: str | None = None
    description: str | None = None

class VegaDataView(BaseModel):
    id: str
    name: str
    group_id: str | None = None
    status: str | None = None
    description: str | None = None

class VegaDataDict(BaseModel):
    id: str
    name: str
    description: str | None = None

class VegaDataDictItem(BaseModel):
    id: str
    dict_id: str
    key: str
    value: str
    sort_order: int = 0

class VegaObjectiveModel(BaseModel):
    id: str
    name: str
    description: str | None = None

class VegaDiscoverTask(BaseModel):
    id: str
    catalog_id: str
    status: str             # "pending" | "running" | "completed" | "failed"
    progress: float | None = None
    error: str | None = None
    created_at: str | None = None
    completed_at: str | None = None

class VegaMetricTask(BaseModel):
    id: str
    status: str
    plan_time: str | None = None

class VegaSpan(BaseModel):
    span_id: str
    trace_id: str
    parent_span_id: str | None = None
    operation_name: str | None = None
    service_name: str | None = None
    duration_ms: float | None = None
    start_time: str | None = None
    status: str | None = None
    attributes: dict[str, Any] = {}

# ── Vega result types ────────────────────────────────────────────────

class VegaQueryResult(BaseModel):
    entries: list[dict[str, Any]] = []
    total_count: int | None = None

class VegaDslResult(BaseModel):
    """Result from DSL search."""
    hits: list[dict[str, Any]] = []
    total: int = 0
    took_ms: int | None = None
    scroll_id: str | None = None

class VegaPromqlResult(BaseModel):
    status: str = "success"
    result_type: str | None = None   # "matrix" | "vector" | "scalar"
    result: list[dict[str, Any]] = []

class VegaHealthReport(BaseModel):
    catalogs: list[VegaCatalog] = []
    healthy_count: int = 0
    degraded_count: int = 0
    unhealthy_count: int = 0
    offline_count: int = 0

class VegaPlatformStats(BaseModel):
    catalogs_total: int = 0
    resources_by_category: dict[str, int] = {}
    models: dict[str, int] = {}        # {metric: 5, event: 3, trace: 2, ...}
    tasks_summary: dict[str, int] = {}  # {running: 2, pending: 1, ...}

class VegaInspectReport(BaseModel):
    server_info: VegaServerInfo
    catalog_health: VegaHealthReport
    resource_summary: dict[str, int] = {}
    active_tasks: list[VegaDiscoverTask] = []
```

### TypeScript (interfaces)

TypeScript mirrors the same types as interfaces in `types/vega.ts`.

## REST Endpoint Mapping

Every SDK method maps to a concrete HTTP call. Base paths by service:

- **vega-backend**: `/api/vega-backend/v1`
- **mdl-data-model**: `/api/mdl-data-model/v1`
- **mdl-uniquery**: `/api/mdl-uniquery/v1`

Since all requests will route through vega-backend as a unified entry point, the SDK always sends to `vega_url`. Vega-backend will proxy requests to other services internally.

### Catalogs (vega-backend)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `catalogs.list()` | `GET` | `/api/vega-backend/v1/catalogs` |
| `catalogs.get(ids)` | `GET` | `/api/vega-backend/v1/catalogs/{ids}` |
| `catalogs.health_status(ids)` | `GET` | `/api/vega-backend/v1/catalogs/{ids}/health-status` |
| `catalogs.health_report()` | composite | `list()` → `health_status()` for all |
| `catalogs.test_connection(id)` | `POST` | `/api/vega-backend/v1/catalogs/{id}/test-connection` |
| `catalogs.discover(id)` | `POST` | `/api/vega-backend/v1/catalogs/{id}/discover` |
| `catalogs.resources(ids)` | `GET` | `/api/vega-backend/v1/catalogs/{ids}/resources` |

### Resources (vega-backend)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `resources.list()` | `GET` | `/api/vega-backend/v1/resources` |
| `resources.get(ids)` | `GET` | `/api/vega-backend/v1/resources/{ids}` |
| `resources.data(id, body)` | `POST` | `/api/vega-backend/v1/resources/{id}/data` |

### Connector Types (vega-backend)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `connector_types.list()` | `GET` | `/api/vega-backend/v1/connector-types` |
| `connector_types.get(type)` | `GET` | `/api/vega-backend/v1/connector-types/{type}` |

### Discover Tasks (vega-backend)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `tasks.list_discover()` | `GET` | `/api/vega-backend/v1/discover-tasks` |
| `tasks.get_discover(id)` | `GET` | `/api/vega-backend/v1/discover-tasks/{id}` |
| `tasks.wait_discover(id)` | composite | poll `get_discover()` until terminal |

### Query Execute (vega-backend)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `query.execute(body)` | `POST` | `/api/vega-backend/v1/query/execute` |

### Metric Models (mdl-data-model)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `metric_models.list()` | `GET` | `/api/mdl-data-model/v1/metric-models` |
| `metric_models.get(ids)` | `GET` | `/api/mdl-data-model/v1/metric-models/{ids}` |
| `metric_models.fields(ids)` | `GET` | `/api/mdl-data-model/v1/metric-models/{ids}/fields` |
| `metric_models.order_fields(ids)` | `GET` | `/api/mdl-data-model/v1/metric-models/{ids}/order_fields` |

### Metric Tasks (mdl-data-model)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `tasks.get_metric(task_id)` | `GET` | `/api/mdl-data-model/v1/metric-tasks/{task_id}` |

### Event Models (mdl-data-model)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `event_models.list()` | `GET` | `/api/mdl-data-model/v1/event-models` |
| `event_models.get(ids)` | `GET` | `/api/mdl-data-model/v1/event-models/{ids}` |
| `event_models.levels()` | `GET` | `/api/mdl-data-model/v1/event-level` |

### Trace Models (mdl-data-model)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `trace_models.list()` | `GET` | `/api/mdl-data-model/v1/trace-models` |
| `trace_models.get(ids)` | `GET` | `/api/mdl-data-model/v1/trace-models/{ids}` |
| `trace_models.field_info(ids)` | `GET` | `/api/mdl-data-model/v1/trace-models/{ids}/field-info` |

### Data Views (mdl-data-model)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `data_views.list()` | `GET` | `/api/mdl-data-model/v1/data-views` |
| `data_views.get(ids)` | `GET` | `/api/mdl-data-model/v1/data-views/{ids}` |
| `data_views.groups()` | `GET` | `/api/mdl-data-model/v1/data-view-groups` |

### Data Dicts (mdl-data-model)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `data_dicts.list()` | `GET` | `/api/mdl-data-model/v1/data-dicts` |
| `data_dicts.get(id)` | `GET` | `/api/mdl-data-model/v1/data-dicts/{id}` |
| `data_dicts.items(id)` | `GET` | `/api/mdl-data-model/v1/data-dicts/{id}/items` |

### Objective Models (mdl-data-model)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `objective_models.list()` | `GET` | `/api/mdl-data-model/v1/objective-models` |
| `objective_models.get(ids)` | `GET` | `/api/mdl-data-model/v1/objective-models/{ids}` |

### DSL Query (mdl-uniquery)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `query.dsl(index, body)` | `POST` | `/api/mdl-uniquery/v1/dsl/{index}/_search` |
| `query.dsl(body)` | `POST` | `/api/mdl-uniquery/v1/dsl/_search` |
| `query.dsl_count(index, body)` | `POST` | `/api/mdl-uniquery/v1/dsl/{index}/_count` |
| `query.dsl_scroll(body)` | `POST` | `/api/mdl-uniquery/v1/dsl/_search/scroll` |

### PromQL Query (mdl-uniquery)

Note: PromQL endpoints require `Content-Type: application/x-www-form-urlencoded`.

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `query.promql(query, start, end, step)` | `POST` | `/api/mdl-uniquery/v1/promql/query_range` |
| `query.promql_instant(query)` | `POST` | `/api/mdl-uniquery/v1/promql/query` |
| `query.promql_series(match)` | `POST` | `/api/mdl-uniquery/v1/promql/series` |

### Metric Model Data Query (mdl-uniquery)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `query.metric_model(ids, body)` | `POST` | `/api/mdl-uniquery/v1/metric-models/{ids}` |
| `query.metric_model_fields(ids)` | `GET` | `/api/mdl-uniquery/v1/metric-models/{ids}/fields` |
| `query.metric_model_labels(ids)` | `GET` | `/api/mdl-uniquery/v1/metric-models/{ids}/labels` |

### Data View Query (mdl-uniquery)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `query.data_view(ids, body)` | `POST` | `/api/mdl-uniquery/v1/data-views/{ids}` |

### Trace Query (mdl-uniquery)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `query.trace(tm_id, trace_id)` | `POST` | `/api/mdl-uniquery/v1/trace-models/{tm_id}/traces/{trace_id}` |
| `trace_models.spans(tm_id, trace_id)` | `POST` | `/api/mdl-uniquery/v1/trace-models/{tm_id}/traces/{trace_id}/spans` |
| `trace_models.span(tm_id, trace_id, span_id)` | `GET` | `/api/mdl-uniquery/v1/trace-models/{tm_id}/traces/{trace_id}/spans/{span_id}` |
| `trace_models.related_logs(tm_id, trace_id, span_id)` | `POST` | `/api/mdl-uniquery/v1/trace-models/{tm_id}/traces/{trace_id}/spans/{span_id}/related-logs` |

### Event Query (mdl-uniquery)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `query.events(body)` | `POST` | `/api/mdl-uniquery/v1/events` |
| `query.event(em_id, event_id)` | `GET` | `/api/mdl-uniquery/v1/event-models/{em_id}/events/{event_id}` |

### Health (vega-backend)

| SDK Method | HTTP | Endpoint |
|-----------|------|----------|
| `health()` | `GET` | `/health` |

## SDK Resource APIs

### Catalogs

```python
client.vega.catalogs.list(status="healthy", limit=20, offset=0)
client.vega.catalogs.get("cat-1")
client.vega.catalogs.health_status(["cat-1", "cat-2"])
client.vega.catalogs.health_report()   # composite: list all → batch health_status → aggregate into VegaHealthReport
client.vega.catalogs.test_connection("cat-1")
client.vega.catalogs.discover("cat-1")
client.vega.catalogs.resources("cat-1", category="table")
```

### Resources

```python
client.vega.resources.list(catalog_id="cat-1", category="table", status="active", limit=20, offset=0)
client.vega.resources.get("res-1")
client.vega.resources.data("res-1", body={...})  # query resource data
```

### Connector Types

```python
client.vega.connector_types.list()
client.vega.connector_types.get("mysql")
```

### Metric Models

```python
client.vega.metric_models.list(limit=20, offset=0)
client.vega.metric_models.get("mm-1")
client.vega.metric_models.fields("mm-1")
client.vega.metric_models.order_fields("mm-1")
```

### Event Models

```python
client.vega.event_models.list(limit=20, offset=0)
client.vega.event_models.get("em-1")
client.vega.event_models.levels()
```

### Trace Models

```python
client.vega.trace_models.list(limit=20, offset=0)
client.vega.trace_models.get("tm-1")
client.vega.trace_models.field_info("tm-1")
client.vega.trace_models.spans("tm-1", "trace-id", body={...})
client.vega.trace_models.span("tm-1", "trace-id", "span-id")
client.vega.trace_models.related_logs("tm-1", "trace-id", "span-id")
```

### Data Views

```python
client.vega.data_views.list(limit=20, offset=0)
client.vega.data_views.get("dv-1")
client.vega.data_views.groups()
```

### Data Dicts

```python
client.vega.data_dicts.list(limit=20, offset=0)
client.vega.data_dicts.get("dd-1")
client.vega.data_dicts.items("dd-1", limit=20, offset=0)
```

### Objective Models

```python
client.vega.objective_models.list(limit=20, offset=0)
client.vega.objective_models.get("om-1")
```

### Query

```python
# DSL (OpenSearch-compatible)
client.vega.query.dsl(index="my-index", body={...})
client.vega.query.dsl(body={...})              # global search, no index
client.vega.query.dsl_count(index="my-index", body={...})
client.vega.query.dsl_scroll(scroll_id="...")

# PromQL
client.vega.query.promql(query="up", start="2026-03-20T00:00:00Z", end="2026-03-20T01:00:00Z", step="15s")
client.vega.query.promql_instant(query="up")
client.vega.query.promql_series(match=["up"])

# Metric model data
client.vega.query.metric_model(ids="mm-1", body={...})
client.vega.query.metric_model_fields(ids="mm-1")
client.vega.query.metric_model_labels(ids="mm-1")

# Data view query
client.vega.query.data_view(ids="dv-1", body={...})

# Trace
client.vega.query.trace(trace_model_id="tm-1", trace_id="abc")

# Events
client.vega.query.events(body={...})
client.vega.query.event(event_model_id="em-1", event_id="evt-1")

# Execute (vega-backend unified query)
client.vega.query.execute(tables=[...], filter_condition={...}, output_fields=[...], sort=[...], offset=0, limit=20)
```

### Tasks (unified namespace)

SDK uses a single `tasks` resource with type-prefixed methods, matching the CLI's unified `task` command:

```python
# Discover tasks
client.vega.tasks.list_discover(status="running")
client.vega.tasks.get_discover("task-1")
client.vega.tasks.wait_discover("task-1", timeout=300)  # poll until terminal state

# Metric tasks
client.vega.tasks.get_metric("task-1")

# Event tasks — status update only (no list endpoint)
```

### Health, Stats, Inspect

```python
# Service health
info = client.vega.health()
# → VegaServerInfo(server_name="VEGA Manager", server_version="1.0.0", ...)

# Platform statistics — composite: calls list on catalogs, resources, models, tasks
stats = client.vega.stats()
# → VegaPlatformStats(catalogs_total=6, resources_by_category={table: 42, ...}, ...)

# Aggregated inspection — composite: health + stats + active tasks
# Parallelized internally. Returns partial results if a sub-call fails.
report = client.vega.inspect(full=False)
# → VegaInspectReport(server_info=..., catalog_health=..., ...)
```

## CLI Layer

All commands under `kweaver vega`. Default output is **Markdown**. Use `--format json` for programmatic consumption, `--format yaml` as alternative. All list commands support `--limit` and `--offset` for pagination.

### Metadata

```bash
kweaver vega catalog list [--status healthy|degraded|unhealthy|offline|disabled] [--limit 20]
kweaver vega catalog get <id>
kweaver vega catalog health [<id...>] [--all]
kweaver vega catalog test-connection <id>
kweaver vega catalog discover <id> [--wait]
kweaver vega catalog resources <id> [--category table|index|...]

kweaver vega resource list [--catalog-id X] [--category table] [--status active] [--limit 20]
kweaver vega resource get <id>
kweaver vega resource data <id> -d '<body>'

kweaver vega connector-type list
kweaver vega connector-type get <type>
```

### Data Models

```bash
kweaver vega metric-model list [--limit 20]
kweaver vega metric-model get <id>
kweaver vega metric-model fields <id>

kweaver vega event-model list [--limit 20]
kweaver vega event-model get <id>
kweaver vega event-model levels

kweaver vega trace-model list [--limit 20]
kweaver vega trace-model get <id>
kweaver vega trace-model fields <id>

kweaver vega data-view list [--limit 20]
kweaver vega data-view get <id>
kweaver vega data-view groups

kweaver vega data-dict list [--limit 20]
kweaver vega data-dict get <id>
kweaver vega data-dict items <id>

kweaver vega objective-model list [--limit 20]
kweaver vega objective-model get <id>
```

### Query

```bash
kweaver vega query dsl [<index>] -d '<body>'
kweaver vega query dsl-count [<index>] -d '<body>'
kweaver vega query promql '<expr>' --start X --end Y --step 15s
kweaver vega query promql-instant '<expr>'
kweaver vega query promql-series --match '<selector>'
kweaver vega query metric-model <ids> -d '<body>'
kweaver vega query data-view <ids> -d '<body>'
kweaver vega query trace <trace-model-id> <trace-id>
kweaver vega query events -d '<body>'
kweaver vega query event <event-model-id> <event-id>
kweaver vega query execute -d '<request-body>'
kweaver vega query bench [<index>] -d '<body>' --count 10
```

Note: `query bench` is CLI-only — it's an interactive benchmarking tool (runs N iterations, reports p50/p95/p99), not an SDK-level abstraction.

### Observability — Status

```bash
kweaver vega health
kweaver vega stats
kweaver vega inspect [--full]

kweaver vega task list [--type discover|metric|event] [--status running|pending|completed|failed]
kweaver vega task get <task-id> [--type discover|metric]
```

### Observability — Diagnostics

```bash
kweaver vega trace show <trace-model-id> <trace-id>
kweaver vega trace spans <trace-model-id> <trace-id>
kweaver vega trace span <trace-model-id> <trace-id> <span-id>
kweaver vega trace related-logs <trace-model-id> <trace-id> <span-id>
```

### Output Format

All commands support `--format md|json|yaml` (default: `md`).

`kweaver vega inspect` example output:

```markdown
## Service

- VEGA Manager v1.0.0 (go1.22.0 linux/amd64)

## Catalog Health

| Name       | Type     | Connector | Status   | Last Check          |
|------------|----------|-----------|----------|---------------------|
| prod-mysql | physical | mysql     | healthy  | 2026-03-20 10:30:00 |
| staging-os | physical | opensearch| degraded | 2026-03-20 10:28:12 |

## Resources Summary

| Category | Count |
|----------|-------|
| table    | 42    |
| index    | 15    |
| dataset  | 8     |
| metric   | 3     |
| total    | 68    |

## Active Tasks

- discover cat-1 — running (60%)
- metric-sync mm-3 — pending
```

## Error Handling

Vega-specific errors extend the existing SDK error hierarchy:

```python
class VegaError(KWeaverError):
    """Base for all Vega errors."""

class VegaConnectionError(VegaError):
    """Catalog connection test or health check failure."""
    catalog_id: str
    connector_type: str

class VegaQueryError(VegaError):
    """Query execution failure (DSL, PromQL, etc.)."""
    query_type: str  # "dsl" | "promql" | "execute"

class VegaDiscoverError(VegaError):
    """Resource discovery failure."""
    catalog_id: str
    task_id: str
```

HTTP errors from vega-backend follow the same `rest.HTTPError` pattern with error codes. The SDK maps vega error codes (e.g., `VegaBackend.InvalidRequestHeader.ContentType`) to appropriate Python/TS exceptions.

## Entropy Reduction: Generic Model Resource

Six of the Vega resources (`metric_models`, `event_models`, `trace_models`, `data_views`, `data_dicts`, `objective_models`) share an identical pattern: `list()` + `get()` against the same mdl-data-model service, differing only in path and return type. Instead of 6 separate resource files, we use a **generic `VegaModelResource`** base:

```python
class VegaModelResource(Generic[T]):
    """Generic list/get for mdl-data-model resources."""

    def __init__(self, http: HttpClient, path: str, parse_fn: Callable[[Any], T]) -> None:
        self._http = http
        self._path = path          # e.g. "/api/mdl-data-model/v1/metric-models"
        self._parse = parse_fn

    def list(self, *, limit: int = 20, offset: int = 0, **params) -> list[T]: ...
    def get(self, ids: str) -> T | list[T]: ...
```

Resources with extra methods (e.g., `metric_models.fields()`, `trace_models.field_info()`, `data_dicts.items()`) subclass it and add only the delta:

```python
class VegaMetricModelsResource(VegaModelResource[VegaMetricModel]):
    def __init__(self, http):
        super().__init__(http, "/api/mdl-data-model/v1/metric-models", _parse_metric_model)

    def fields(self, ids: str) -> list[dict]: ...
    def order_fields(self, ids: str) -> list[dict]: ...
```

CLI commands for models similarly use a shared `register_model_commands()` factory, with per-model extras added declaratively.

This reduces:
- SDK resource files: 12 → 7 (catalogs, resources, connector_types, **models**, query, tasks, inspect)
- CLI files: 11 → 7 (catalog, resource, connector_type, **model**, query, task, trace+inspect)
- Unit test files: parameterized over the model registry instead of per-resource
- TypeScript: same pattern, `VegaModelResource<T>` generic class

## Project Structure

### Python

This introduces `resources/vega/` as a **sub-package** — a new pattern in the codebase. This is intentional: Vega has many resource files, and keeping them flat in `resources/` alongside existing KWeaver resources would create namespace confusion. The `vega/` sub-package clearly scopes Vega-specific code.

```
packages/python/src/kweaver/
├── resources/vega/           # NEW sub-package
│   ├── __init__.py           # exports VegaNamespace
│   ├── _base.py              # VegaModelResource generic base class
│   ├── catalogs.py           # CatalogsResource (custom — has health, discover, test_connection)
│   ├── resources.py          # ResourcesResource (custom — has data query)
│   ├── connector_types.py    # ConnectorTypesResource (custom — different service path)
│   ├── models.py             # All 6 model resources via VegaModelResource subclasses
│   ├── query.py              # VegaQueryResource (DSL, PromQL, trace, events, execute)
│   ├── tasks.py              # unified: discover + metric + event tasks
│   └── inspect.py            # health(), stats(), inspect() methods
├── cli/vega/                 # NEW sub-package
│   ├── __init__.py
│   ├── main.py               # `kweaver vega` group entry point
│   ├── catalog.py            # catalog subcommands
│   ├── resource.py           # resource subcommands
│   ├── connector_type.py     # connector-type subcommands
│   ├── model.py              # ALL model subcommands (factory-registered)
│   ├── query.py              # query subcommands
│   ├── task.py               # task subcommands
│   ├── trace.py              # trace diagnostics subcommands
│   └── formatters.py         # md/json/yaml output formatting
├── types.py                  # extended with Vega* types
└── _client.py                # extended with self.vega: VegaNamespace
```

### TypeScript

The existing TS SDK uses `resources/` for resource classes and `api/` for lower-level API functions. Vega follows the same split:

```
packages/typescript/src/
├── resources/vega/           # NEW sub-directory
│   ├── index.ts              # exports VegaNamespace
│   ├── base.ts               # VegaModelResource<T> generic base
│   ├── catalogs.ts
│   ├── resources.ts
│   ├── connector-types.ts
│   ├── models.ts             # all 6 model resources
│   ├── query.ts
│   ├── tasks.ts
│   └── inspect.ts
├── api/vega/                 # NEW — low-level API functions
│   ├── catalogs.ts
│   ├── resources.ts
│   ├── query.ts
│   └── models.ts
├── commands/vega/            # NEW sub-directory
│   ├── index.ts
│   ├── catalog.ts
│   ├── resource.ts
│   ├── connector-type.ts
│   ├── model.ts              # factory-registered model commands
│   ├── query.ts
│   ├── task.ts
│   └── trace.ts
├── types/vega.ts             # Vega type interfaces
└── client.ts                 # extended with vega: VegaNamespace
```

## Capability Matrix

| Domain | Capability | SDK | CLI |
|--------|-----------|-----|-----|
| **Metadata** | Catalog list/get/health/test/discover | `vega.catalogs.*` | `vega catalog *` |
| | Resource list/get/data | `vega.resources.*` | `vega resource *` |
| | Connector-Type list/get | `vega.connector_types.*` | `vega connector-type *` |
| **Models** | Metric-Model list/get/fields | `vega.metric_models.*` | `vega metric-model *` |
| | Event-Model list/get/levels | `vega.event_models.*` | `vega event-model *` |
| | Trace-Model list/get/fields/spans | `vega.trace_models.*` | `vega trace-model *` |
| | Data-View list/get/groups | `vega.data_views.*` | `vega data-view *` |
| | Data-Dict list/get/items | `vega.data_dicts.*` | `vega data-dict *` |
| | Objective-Model list/get | `vega.objective_models.*` | `vega objective-model *` |
| **Query** | DSL search/count/scroll | `vega.query.dsl*()` | `vega query dsl*` |
| | PromQL range/instant/series | `vega.query.promql*()` | `vega query promql*` |
| | Metric model data | `vega.query.metric_model()` | `vega query metric-model` |
| | Data view query | `vega.query.data_view()` | `vega query data-view` |
| | Trace query | `vega.query.trace()` | `vega query trace` |
| | Event query | `vega.query.events()` | `vega query events` |
| | Execute unified query | `vega.query.execute()` | `vega query execute` |
| **Observe-Status** | Catalog health report | `vega.catalogs.health_report()` | `vega catalog health --all` |
| | Discover task wait | `vega.tasks.wait_discover()` | `vega catalog discover --wait` |
| | Task monitoring | `vega.tasks.*()` | `vega task list/get` |
| | Service health | `vega.health()` | `vega health` |
| **Observe-Diag** | Query benchmark | — | `vega query bench` |
| | Trace spans/detail | `vega.trace_models.spans()` | `vega trace show/spans` |
| | Related logs | `vega.trace_models.related_logs()` | `vega trace related-logs` |
| | Platform stats | `vega.stats()` | `vega stats` |
| | Aggregated inspect | `vega.inspect()` | `vega inspect` |
| **Output** | Markdown / JSON / YAML | — | `--format md\|json\|yaml` |

## Testing Plan

Testing follows the existing kweaver-sdk conventions: **unit tests** (mocked HTTP, fast) + **e2e tests** (real Vega instance, the real quality gate). Both Python and TypeScript must have equivalent coverage.

### Test Infrastructure

#### E2E Environment

E2E tests require a running Vega instance. Configuration via environment variables (auto-loaded from `~/.env.secrets`):

```bash
# Required
KWEAVER_VEGA_URL=http://vega-backend:13014

# Reuse existing auth (already in ~/.env.secrets)
KWEAVER_BASE_URL=...
KWEAVER_TOKEN=...
```

**Python**: extend `tests/e2e/conftest.py` to read `KWEAVER_VEGA_URL` into the e2e env registry. Add a `vega_client` fixture (session-scoped) that returns `client.vega`, auto-skipping if `KWEAVER_VEGA_URL` is not set.

**TypeScript**: extend `test/e2e/setup.ts` `getE2eEnv()` to include `vegaUrl` from `KWEAVER_VEGA_URL`.

#### Shared Fixtures (Python)

```python
# tests/e2e/conftest.py — new fixtures

@pytest.fixture(scope="session")
def vega_client(kweaver_client) -> VegaNamespace:
    """Vega namespace, skips if KWEAVER_VEGA_URL not configured."""
    if not hasattr(kweaver_client, "vega") or kweaver_client.vega is None:
        pytest.skip("KWEAVER_VEGA_URL not configured")
    return kweaver_client.vega

@pytest.fixture(scope="module")
def any_catalog(vega_client) -> VegaCatalog:
    """First available catalog, skips if none."""
    cats = vega_client.catalogs.list(limit=1)
    if not cats:
        pytest.skip("No catalogs available")
    return cats[0]

@pytest.fixture(scope="module")
def any_resource(vega_client, any_catalog) -> VegaResource:
    """First available resource in any catalog."""
    resources = vega_client.resources.list(catalog_id=any_catalog.id, limit=1)
    if not resources:
        pytest.skip("No resources available")
    return resources[0]
```

### Unit Tests

Unit tests use mock HTTP transport (existing `make_client` + `RequestCapture` pattern). Every SDK method must have a unit test verifying:
1. Correct HTTP method and endpoint path
2. Query parameters / request body serialization
3. Response parsing into typed Pydantic models

#### Python: `tests/unit/test_vega.py`

A single test file, leveraging parameterization for the 6 generic model resources:

```python
# ── Generic model resources (parameterized) ──────────────────────────

MODEL_RESOURCES = [
    ("metric_models",    "/api/mdl-data-model/v1/metric-models",    VegaMetricModel),
    ("event_models",     "/api/mdl-data-model/v1/event-models",     VegaEventModel),
    ("trace_models",     "/api/mdl-data-model/v1/trace-models",     VegaTraceModel),
    ("data_views",       "/api/mdl-data-model/v1/data-views",       VegaDataView),
    ("data_dicts",       "/api/mdl-data-model/v1/data-dicts",       VegaDataDict),
    ("objective_models", "/api/mdl-data-model/v1/objective-models",  VegaObjectiveModel),
]

@pytest.mark.parametrize("attr,path,model_cls", MODEL_RESOURCES)
def test_model_list(attr, path, model_cls, capture):
    handler = mock_list_response(path)
    client = make_vega_client(handler, capture)
    result = getattr(client.vega, attr).list()
    assert capture.last_request().url.path == path
    assert all(isinstance(r, model_cls) for r in result)

@pytest.mark.parametrize("attr,path,model_cls", MODEL_RESOURCES)
def test_model_get(attr, path, model_cls, capture):
    handler = mock_get_response(path)
    client = make_vega_client(handler, capture)
    result = getattr(client.vega, attr).get("id-1")
    assert f"{path}/id-1" in capture.last_request().url.path

# ── Custom resources (individual tests) ──────────────────────────────

def test_catalog_list(capture): ...
def test_catalog_get(capture): ...
def test_catalog_health_status(capture): ...
def test_catalog_health_report(capture): ...       # verifies composite: list → health_status
def test_catalog_test_connection(capture): ...
def test_catalog_discover(capture): ...
def test_catalog_resources(capture): ...

def test_resource_list(capture): ...
def test_resource_get(capture): ...
def test_resource_data(capture): ...

def test_connector_type_list(capture): ...
def test_connector_type_get(capture): ...

# model-specific extras
def test_metric_model_fields(capture): ...
def test_metric_model_order_fields(capture): ...
def test_trace_model_field_info(capture): ...
def test_data_dict_items(capture): ...
def test_data_view_groups(capture): ...
def test_event_model_levels(capture): ...

# query
def test_query_dsl(capture): ...
def test_query_dsl_count(capture): ...
def test_query_dsl_scroll(capture): ...
def test_query_promql(capture): ...                 # verifies form-encoded content-type
def test_query_promql_instant(capture): ...
def test_query_promql_series(capture): ...
def test_query_metric_model(capture): ...
def test_query_data_view(capture): ...
def test_query_trace(capture): ...
def test_query_events(capture): ...
def test_query_event(capture): ...
def test_query_execute(capture): ...

# tasks
def test_task_list_discover(capture): ...
def test_task_get_discover(capture): ...
def test_task_wait_discover_polls_until_complete(capture): ...
def test_task_get_metric(capture): ...

# health / stats / inspect
def test_health(capture): ...
def test_stats_composite(capture): ...              # verifies multiple internal calls
def test_inspect_composite(capture): ...
def test_inspect_partial_failure(capture): ...      # verifies partial results on sub-call failure
```

#### Python: `tests/unit/test_vega_cli.py`

CLI tests use `CliRunner` (existing pattern). Focus on:
1. Command invocation → SDK method called correctly
2. Output format: `--format md` produces valid Markdown tables, `--format json` produces valid JSON

```python
# Parameterized for model commands
@pytest.mark.parametrize("model_name", ["metric-model", "event-model", "trace-model", "data-view", "data-dict", "objective-model"])
def test_model_list_cli(model_name, cli_runner, mock_vega):
    result = cli_runner.invoke(["vega", model_name, "list"])
    assert result.exit_code == 0

# Format tests
def test_catalog_list_format_json(cli_runner, mock_vega): ...
def test_catalog_list_format_md(cli_runner, mock_vega): ...
def test_inspect_output(cli_runner, mock_vega): ...
```

#### TypeScript: `test/vega.test.ts` and `test/vega-cli.test.ts`

Mirror the Python structure. Uses `withFetch()` mock pattern:

```typescript
// Parameterized model tests
for (const [attr, path] of MODEL_RESOURCES) {
  test(`vega ${attr} list`, async () => {
    await withFetch(mockListHandler(path), async () => {
      const client = new KWeaverClient({ vegaUrl: "http://localhost:13014", ... });
      const result = await client.vega[attr].list();
      assert.ok(Array.isArray(result));
    });
  });
}
```

### E2E Tests

E2E tests validate against a real Vega instance. They are the **real quality gate** — unit tests alone are meaningless for verifying endpoint paths, auth headers, and response parsing.

#### Test Organization

```
tests/e2e/
├── conftest.py                    # extended: vega_client, any_catalog, any_resource fixtures
├── layer/
│   ├── test_vega_metadata.py      # catalog, resource, connector-type read ops
│   ├── test_vega_models.py        # all 6 model types — parameterized
│   ├── test_vega_query.py         # DSL, PromQL, execute, data-view, metric-model queries
│   └── test_vega_observability.py # health, stats, inspect, tasks, trace
└── integration/
    └── test_vega_lifecycle.py     # discover → query → verify (destructive)
```

TypeScript:
```
test/e2e/
├── setup.ts                       # extended: vegaUrl, shouldSkipVega()
├── vega-metadata.test.ts
├── vega-models.test.ts
├── vega-query.test.ts
├── vega-observability.test.ts
└── vega-lifecycle.test.ts
```

#### Layer Tests (read-only, `@pytest.mark.e2e`)

These tests are read-only against existing Vega data. They auto-skip if no data is available.

**`test_vega_metadata.py`**:

```python
@pytest.mark.e2e
class TestVegaCatalogs:
    def test_list(self, vega_client):
        cats = vega_client.catalogs.list()
        assert isinstance(cats, list)
        if cats:
            assert isinstance(cats[0], VegaCatalog)

    def test_get(self, vega_client, any_catalog):
        cat = vega_client.catalogs.get(any_catalog.id)
        assert cat.id == any_catalog.id

    def test_health_status(self, vega_client, any_catalog):
        statuses = vega_client.catalogs.health_status([any_catalog.id])
        assert len(statuses) == 1
        assert statuses[0].health_status in ("healthy", "degraded", "unhealthy", "offline", "disabled")

    def test_health_report(self, vega_client):
        report = vega_client.catalogs.health_report()
        assert isinstance(report, VegaHealthReport)
        assert report.healthy_count + report.degraded_count + report.unhealthy_count + report.offline_count == len(report.catalogs)

    def test_resources(self, vega_client, any_catalog):
        resources = vega_client.catalogs.resources(any_catalog.id)
        assert isinstance(resources, list)

    def test_test_connection(self, vega_client, any_catalog):
        # test_connection is safe (read-only probe)
        result = vega_client.catalogs.test_connection(any_catalog.id)
        assert result is not None

@pytest.mark.e2e
class TestVegaResources:
    def test_list(self, vega_client):
        resources = vega_client.resources.list(limit=5)
        assert isinstance(resources, list)

    def test_get(self, vega_client, any_resource):
        r = vega_client.resources.get(any_resource.id)
        assert r.id == any_resource.id
        assert r.category in ("table", "index", "dataset", "metric", "topic", "file", "fileset", "api", "logicview")

@pytest.mark.e2e
class TestVegaConnectorTypes:
    def test_list(self, vega_client):
        types = vega_client.connector_types.list()
        assert isinstance(types, list)
        assert len(types) > 0  # at least built-in types exist
```

**`test_vega_models.py`** — parameterized over model types:

```python
MODEL_ATTRS = ["metric_models", "event_models", "trace_models", "data_views", "data_dicts", "objective_models"]

@pytest.mark.e2e
@pytest.mark.parametrize("attr", MODEL_ATTRS)
def test_model_list(vega_client, attr):
    result = getattr(vega_client, attr).list(limit=5)
    assert isinstance(result, list)

@pytest.mark.e2e
@pytest.mark.parametrize("attr", MODEL_ATTRS)
def test_model_get(vega_client, attr):
    items = getattr(vega_client, attr).list(limit=1)
    if not items:
        pytest.skip(f"No {attr} available")
    item = getattr(vega_client, attr).get(items[0].id)
    assert item.id == items[0].id

# Model-specific extras
@pytest.mark.e2e
def test_metric_model_fields(vega_client):
    models = vega_client.metric_models.list(limit=1)
    if not models:
        pytest.skip("No metric models")
    fields = vega_client.metric_models.fields(models[0].id)
    assert isinstance(fields, list)

@pytest.mark.e2e
def test_data_dict_items(vega_client):
    dicts = vega_client.data_dicts.list(limit=1)
    if not dicts:
        pytest.skip("No data dicts")
    items = vega_client.data_dicts.items(dicts[0].id)
    assert isinstance(items, list)
```

**`test_vega_query.py`**:

```python
@pytest.mark.e2e
class TestVegaQuery:
    def test_execute(self, vega_client, any_resource):
        """Unified query against a known resource."""
        result = vega_client.query.execute(
            tables=[{"resource_id": any_resource.id}],
            output_fields=["*"],
            limit=5,
        )
        assert isinstance(result, VegaQueryResult)

    def test_dsl_search(self, vega_client):
        """DSL search — requires at least one index resource."""
        result = vega_client.query.dsl(body={"query": {"match_all": {}}, "size": 1})
        assert isinstance(result, VegaDslResult)

    def test_promql_instant(self, vega_client):
        """PromQL instant query — may skip if no Prometheus data source."""
        try:
            result = vega_client.query.promql_instant(query="up")
            assert isinstance(result, VegaPromqlResult)
        except VegaQueryError:
            pytest.skip("No PromQL-compatible data source")
```

**`test_vega_observability.py`**:

```python
@pytest.mark.e2e
class TestVegaHealth:
    def test_health(self, vega_client):
        info = vega_client.health()
        assert isinstance(info, VegaServerInfo)
        assert info.server_name
        assert info.server_version

    def test_stats(self, vega_client):
        stats = vega_client.stats()
        assert isinstance(stats, VegaPlatformStats)
        assert stats.catalogs_total >= 0

    def test_inspect(self, vega_client):
        report = vega_client.inspect()
        assert isinstance(report, VegaInspectReport)
        assert report.server_info.server_name

@pytest.mark.e2e
class TestVegaTasks:
    def test_list_discover(self, vega_client):
        tasks = vega_client.tasks.list_discover()
        assert isinstance(tasks, list)
```

#### Integration Test (destructive, `@pytest.mark.e2e @pytest.mark.destructive`)

Full lifecycle test that creates real data and verifies the read path end-to-end.

**`test_vega_lifecycle.py`**:

```python
@pytest.fixture(scope="module")
def vega_lifecycle(vega_client):
    """
    Lifecycle:
    1. Find a catalog with healthy status
    2. Trigger discover
    3. Wait for discover to complete
    4. Verify resources were discovered
    5. Query resource data
    """
    cats = vega_client.catalogs.list(limit=10)
    healthy = [c for c in cats if c.health_status == "healthy"]
    if not healthy:
        pytest.skip("No healthy catalog for lifecycle test")

    catalog = healthy[0]

    # Trigger discover (destructive — creates a discover task)
    task = vega_client.catalogs.discover(catalog.id)

    # Wait for completion
    final = vega_client.tasks.wait_discover(task.id, timeout=120)

    # List discovered resources
    resources = vega_client.catalogs.resources(catalog.id, limit=50)

    yield {
        "catalog": catalog,
        "task": final,
        "resources": resources,
    }

@pytest.mark.e2e
@pytest.mark.destructive
class TestVegaLifecycle:
    def test_discover_completed(self, vega_lifecycle):
        assert vega_lifecycle["task"].status == "completed"

    def test_resources_discovered(self, vega_lifecycle):
        assert len(vega_lifecycle["resources"]) > 0

    def test_resource_data_query(self, vega_client, vega_lifecycle):
        resources = vega_lifecycle["resources"]
        # Find a table resource to query
        tables = [r for r in resources if r.category == "table"]
        if not tables:
            pytest.skip("No table resources discovered")
        result = vega_client.resources.data(tables[0].id, body={})
        assert result is not None
```

#### CLI E2E Tests

CLI e2e tests verify the full stack: CLI → SDK → HTTP → real Vega:

```python
@pytest.mark.e2e
class TestVegaCLI:
    def test_health(self, cli_runner):
        result = cli_runner.invoke(["vega", "health"])
        assert result.exit_code == 0
        assert "VEGA" in result.output

    def test_catalog_list(self, cli_runner):
        result = cli_runner.invoke(["vega", "catalog", "list"])
        assert result.exit_code == 0

    def test_catalog_list_json(self, cli_runner):
        result = cli_runner.invoke(["vega", "catalog", "list", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_inspect(self, cli_runner):
        result = cli_runner.invoke(["vega", "inspect"])
        assert result.exit_code == 0
        assert "Catalog Health" in result.output

    def test_stats(self, cli_runner):
        result = cli_runner.invoke(["vega", "stats"])
        assert result.exit_code == 0
```

### Test Execution

```bash
# Unit tests (no Vega instance needed)
make test                                    # runs all unit tests (Python + TS)

# E2E — read-only layer (needs running Vega)
KWEAVER_VEGA_URL=http://vega:13014 make test-e2e

# E2E — full lifecycle (needs running Vega + writable catalog)
KWEAVER_VEGA_URL=http://vega:13014 pytest tests/e2e/ --run-destructive

# TypeScript E2E
KWEAVER_VEGA_URL=http://vega:13014 npm run test:e2e
```

### Coverage Targets

| Layer | Target | Notes |
|-------|--------|-------|
| Python unit | 90%+ on vega resources | Parameterized tests cover all model types automatically |
| Python e2e layer | All list/get/health operations | Read-only, safe to run repeatedly |
| Python e2e integration | Discover → query lifecycle | Requires `--run-destructive` |
| TypeScript unit | Parity with Python | Same parameterized patterns |
| TypeScript e2e | Parity with Python | Same scenarios |
| CLI unit | All commands, both md and json format | CliRunner / runCli |
| CLI e2e | health, catalog list, inspect, stats | Smoke tests against real instance |

### Key Testing Principles

1. **E2e is the real quality gate** — unit tests verify wiring, e2e verifies reality. A green unit test with wrong endpoint path is worse than no test.
2. **Parameterize, don't duplicate** — the 6 model resources share one parameterized test set, not 6 copy-pasted test files.
3. **Graceful skip over hard fail** — if a Vega instance has no metric models, skip `test_metric_model_fields`, don't fail.
4. **External endpoints only** — SDK must use `/api/vega-backend/v1/` paths, never `/api/vega-backend/in/v1/` internal paths.
5. **Cleanup after destructive tests** — lifecycle fixtures yield + teardown, timestamped names for isolation.
